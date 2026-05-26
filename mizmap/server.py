"""FastAPI app — serves the web viewer and the WebSocket hub.

Composes:
  - a static `/` mount for the web viewer
  - REST endpoints for boot config + health
  - a `/ws` endpoint for live updates
  - a background DCS-gRPC client (best-effort, reconnects forever)
"""

from __future__ import annotations

import asyncio
import logging
import math
import webbrowser
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.common.v0 import common_pb2

from mizmap import __version__
from mizmap.config import Settings
from mizmap.grpc_client import DcsGrpcClient
from mizmap.marks import Mark
from mizmap.paths import web_dir
from mizmap.state import MissionState, Unit, unit_to_dict
from mizmap.tiles import TileCache
from mizmap.websocket import WebSocketHub

log = logging.getLogger(__name__)


def _open_browser_safe(url: str) -> None:
    """Best-effort browser launch. Swallow errors so a missing browser
    (e.g. headless CI) never takes the server down."""
    try:
        webbrowser.open(url)
    except Exception as exc:  # noqa: BLE001
        log.warning("could not open browser at %s: %s", url, exc)


def _unit_from_proto(p: common_pb2.Unit) -> Unit:
    group = p.group
    pos = p.position
    vel = p.velocity
    orient = p.orientation
    # Empirically, both Orientation.heading and Velocity.heading from
    # DCS-gRPC 0.8.1 emit values that don't track the actual direction of
    # motion for fast-moving aircraft (verified against position deltas).
    # Velocity.velocity, however, is a true 3D velocity vector in the
    # documented +x=north +z=east frame — atan2(z, x) gives a reliable
    # compass bearing CW from north. Use that for the movement track.
    track = math.atan2(vel.velocity.z, vel.velocity.x)
    return Unit(
        id=p.id,
        name=p.name,
        callsign=p.callsign,
        type=p.type,
        coalition=int(p.coalition),
        group_id=group.id,
        group_name=group.name,
        group_category=int(group.category),
        lat=pos.lat,
        lon=pos.lon,
        alt=pos.alt,
        heading=orient.heading,  # nose direction (Orientation.heading)
        speed=vel.speed,
        track=track,  # derived from velocity vector, not Velocity.heading
        vs=vel.velocity.y,  # +y is up per the proto's documented frame
        player_name=p.player_name if p.HasField("player_name") else None,
    )


def create_app(settings: Settings, *, open_browser: bool = False) -> FastAPI:
    hub = WebSocketHub()
    state = MissionState()

    async def push_grpc_status(connected: bool, error: str | None) -> None:
        target = f"{settings.grpc_host}:{settings.grpc_port}"
        state.grpc.update(connected=connected, host=target, error=error)
        await hub.broadcast(state.grpc.to_message())
        if connected:
            # Routes + bullseyes are static for the mission's lifetime — fetch
            # once per connect, broadcast snapshots, then stay quiet until the
            # next mission_start event or reconnect. Scheduled rather than
            # awaited so slow RPC calls don't stall the gRPC client's status
            # flow. Connect often races a still-loading mission Lua, so the
            # internal retry-once is what actually rescues this path.
            asyncio.create_task(_refresh_routes())
            asyncio.create_task(_refresh_bullseyes())
            asyncio.create_task(_refresh_marks())

    # DCS Lua can take 20–40 s to fully bootstrap a freshly-loaded mission;
    # the Eval used by fetch_routes is heavier than GetBullseye and recovers
    # slower. Generous retry budget covers that range without slowing down
    # the steady-state case (when the first attempt succeeds, no waits fire).
    # Five attempts total: the first one immediately, then each subsequent
    # one after the corresponding wait.
    _RETRY_WAITS_S = (5, 10, 15, 20)

    async def _refresh_with_retry(fetch, label):
        result = await fetch()
        for wait_s in _RETRY_WAITS_S:
            if result is not None:
                return result
            await asyncio.sleep(wait_s)
            result = await fetch()
        if result is None:
            log.warning(
                "%s refresh: gave up after %d attempts (state left empty)",
                label,
                len(_RETRY_WAITS_S) + 1,
            )
        return result

    async def _refresh_routes(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        routes = await _refresh_with_retry(grpc_client.fetch_routes, "routes")
        if routes is None:
            return
        state.set_routes(routes)
        await hub.broadcast(state.routes_message())

    async def _refresh_bullseyes(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        bullseyes = await _refresh_with_retry(grpc_client.fetch_bullseyes, "bullseyes")
        if bullseyes is None:
            return
        state.set_bullseyes(bullseyes)
        await hub.broadcast(state.bullseyes_message())

    async def _refresh_marks(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        marks = await _refresh_with_retry(grpc_client.fetch_marks, "marks")
        if marks is None:
            return
        state.set_marks(marks)
        await hub.broadcast(state.marks_message())

    async def on_unit(p: common_pb2.Unit) -> None:
        unit = _unit_from_proto(p)
        state.upsert(unit)
        await hub.broadcast({"type": "unit_update", "unit": unit_to_dict(unit)})

    async def on_unit_gone(unit_id: int) -> None:
        if state.remove(unit_id) is not None:
            await hub.broadcast({"type": "unit_gone", "id": unit_id})

    async def on_disconnect() -> None:
        cleared = state.clear()
        cleared_routes = state.clear_routes()
        cleared_bull = state.clear_bullseyes()
        cleared_marks = state.clear_marks()
        if cleared or cleared_routes or cleared_bull or cleared_marks:
            log.info(
                "gRPC dropped — cleared %d units, %d routes, %d bullseyes, %d marks",
                cleared,
                cleared_routes,
                cleared_bull,
                cleared_marks,
            )
        await hub.broadcast({"type": "units_snapshot", "units": []})
        await hub.broadcast({"type": "mission_routes_snapshot", "routes": []})
        await hub.broadcast({"type": "bullseyes_snapshot", "bullseyes": []})
        await hub.broadcast({"type": "marks_snapshot", "marks": []})

    async def on_mission_start() -> None:
        # New mission booted (or current mission restarted). Static data —
        # routes, bullseyes — needs to be re-pulled. Marks too: any
        # mission-scripted markers come back with the new mission, and any
        # player-added marks from the prior session are gone. Units take
        # care of themselves via StreamUnits. Leading 5s delay lets DCS Lua
        # finish bootstrapping; the refresh helpers' internal retry-once
        # catches the slower cases.
        asyncio.create_task(_refresh_routes(initial_delay=5.0))
        asyncio.create_task(_refresh_bullseyes(initial_delay=5.0))
        asyncio.create_task(_refresh_marks(initial_delay=5.0))

    async def on_mission_end() -> None:
        # Mission unloaded. Clear static data immediately so a stale flight
        # plan doesn't linger across the briefing/load gap. Units are
        # similarly cleared by the StreamUnits gone messages and/or
        # mission_start's fresh snapshot. The gRPC channel stays up.
        cleared_routes = state.clear_routes()
        cleared_bull = state.clear_bullseyes()
        cleared_marks = state.clear_marks()
        log.info(
            "mission ended — cleared %d routes, %d bullseyes, %d marks",
            cleared_routes,
            cleared_bull,
            cleared_marks,
        )
        await hub.broadcast({"type": "mission_routes_snapshot", "routes": []})
        await hub.broadcast({"type": "bullseyes_snapshot", "bullseyes": []})
        await hub.broadcast({"type": "marks_snapshot", "marks": []})

    async def on_mark_add(mark: Mark) -> None:
        state.upsert_mark(mark)
        await hub.broadcast({"type": "mark_added", "mark": mark.to_dict()})

    async def on_mark_remove(mark_id: int) -> None:
        if state.remove_mark(mark_id) is not None:
            await hub.broadcast({"type": "mark_removed", "id": mark_id})

    tile_cache = TileCache(
        upstream_url_template=settings.tile_url,
        cache_dir=settings.tile_cache_dir,
    )

    grpc_client = DcsGrpcClient(
        host=settings.grpc_host,
        port=settings.grpc_port,
        on_status=push_grpc_status,
        on_unit=on_unit,
        on_unit_gone=on_unit_gone,
        on_disconnect=on_disconnect,
        on_mission_start=on_mission_start,
        on_mission_end=on_mission_end,
        on_mark_add=on_mark_add,
        on_mark_remove=on_mark_remove,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        grpc_client.start()
        if open_browser:
            # Fire-and-forget: uvicorn has already bound the port by the time
            # the lifespan startup runs, so the browser hit lands on a live
            # server. webbrowser.open is synchronous + can block briefly on
            # Windows shell-out, so push it to a thread.
            host = settings.http_host
            display_host = "localhost" if host in ("0.0.0.0", "::", "") else host
            url = f"http://{display_host}:{settings.http_port}/"
            asyncio.create_task(asyncio.to_thread(_open_browser_safe, url))
        try:
            yield
        finally:
            await grpc_client.stop()
            await tile_cache.aclose()

    app = FastAPI(title="MizMap", version=__version__, lifespan=lifespan)

    @app.get("/api/health")
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "version": __version__,
                "grpc": state.grpc.to_message(),
                "units": len(state.units),
                "routes": len(state.routes),
                "bullseyes": len(state.bullseyes),
                "marks": len(state.marks),
            }
        )

    @app.get("/api/elevation")
    async def elevation(lat: float, lon: float) -> JSONResponse:
        # Range-check so a bad URL can't drive a confused Eval string.
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            return JSONResponse(
                {"elev_m": None, "error": "lat/lon out of range"}, status_code=400
            )
        elev = await grpc_client.fetch_elevation(lat, lon)
        return JSONResponse({"elev_m": elev})

    @app.get("/api/declination")
    async def declination(lat: float, lon: float, alt: float = 0.0) -> JSONResponse:
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            return JSONResponse(
                {"declination_deg": None, "error": "lat/lon out of range"}, status_code=400
            )
        dec = await grpc_client.fetch_declination(lat, lon, alt)
        return JSONResponse({"declination_deg": dec})

    @app.get("/api/config")
    async def public_config() -> JSONResponse:
        # Always serve the locally-proxied tile URL; the upstream URL stays
        # private to the backend (see /tiles route).
        return JSONResponse(
            {
                "tileUrl": "/tiles/{z}/{x}/{y}.png",
                "tileAttribution": settings.tile_attribution,
            }
        )

    @app.get("/tiles/{z}/{x}/{y}.png")
    async def tile(z: int, x: int, y: int) -> Response:
        # Cheap sanity bound — Leaflet/OpenTopoMap won't request beyond ~22.
        if not (0 <= z <= 22) or x < 0 or y < 0:
            raise HTTPException(status_code=400, detail="z/x/y out of range")
        try:
            data, status = await tile_cache.fetch(z, x, y)
        except httpx.HTTPError as exc:
            log.warning("tile %d/%d/%d upstream fetch failed: %s", z, x, y, exc)
            raise HTTPException(status_code=502, detail="upstream tile fetch failed") from exc
        # Browser-side cache lets us avoid even hitting the proxy on subsequent
        # views of the same tile within a session. Tiles are immutable.
        return Response(
            content=data,
            media_type="image/png",
            headers={
                "X-Tile-Cache": status,
                "Cache-Control": "public, max-age=86400",
            },
        )

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await hub.connect(ws)
        try:
            await ws.send_json({"type": "hello", "version": __version__})
            await ws.send_json(state.grpc.to_message())
            await ws.send_json(state.snapshot_message())
            await ws.send_json(state.routes_message())
            await ws.send_json(state.bullseyes_message())
            await ws.send_json(state.marks_message())
            while True:
                try:
                    await ws.receive_text()
                except WebSocketDisconnect:
                    break
        finally:
            await hub.disconnect(ws)

    web = web_dir()
    if web.is_dir():
        app.mount("/", StaticFiles(directory=web, html=True), name="web")
    else:
        log.warning("web directory not found at %s — UI will 404", web)

    return app


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run(*, open_browser: bool = False) -> None:
    """Run uvicorn in the foreground (no tray). Used in dev + --no-tray mode."""
    import uvicorn

    settings = Settings.from_env()
    _configure_logging()
    uvicorn.run(
        create_app(settings, open_browser=open_browser),
        host=settings.http_host,
        port=settings.http_port,
        log_level="info",
    )


def run_with_tray() -> None:
    """Run uvicorn in a background thread with a tray icon on the main thread.

    Windows-only path. The tray opens the browser on startup and provides a
    Quit affordance for the background server.
    """
    from mizmap.tray import run_with_tray as _tray_run

    settings = Settings.from_env()
    _configure_logging()
    # Browser-open is handled by the tray (once on startup + on menu click),
    # so we don't ask the app to also open it.
    app = create_app(settings, open_browser=False)
    _tray_run(app, settings)
