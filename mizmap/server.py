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
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.common.v0 import common_pb2

from mizmap import __version__
from mizmap.config import (
    Settings,
    configured_value,
    detect_dcs_install_dir,
    env_locked_keys,
    update_config_file,
)
from mizmap.basemaps import DEFAULT_BASEMAP_ID, build_basemaps
from mizmap.grpc_client import DcsGrpcClient
from mizmap.marks import Mark
from mizmap.navaids import load_navaids
from mizmap.paths import web_dir
from mizmap.state import MissionState, Unit, unit_to_dict
from mizmap.tiles import TileCache
from mizmap.websocket import WebSocketHub

log = logging.getLogger(__name__)


class _SettingsUpdate(BaseModel):
    """POST /api/settings body. The panel sends every editable, non-locked
    field as a string; only fields present in the request are acted on."""

    http_host: str | None = None
    http_port: str | None = None
    grpc_host: str | None = None
    grpc_port: str | None = None
    dcs_install_dir: str | None = None


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
            asyncio.create_task(_refresh_airbases())
            asyncio.create_task(_refresh_runways())
            asyncio.create_task(_refresh_navaids())
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

    async def _refresh_airbases(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        airbases = await _refresh_with_retry(grpc_client.fetch_airbases, "airbases")
        if airbases is None:
            return
        state.set_airbases(airbases)
        await hub.broadcast(state.airbases_message())

    async def _refresh_runways(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        runways = await _refresh_with_retry(grpc_client.fetch_runways, "runways")
        if runways is None:
            return
        state.set_runways(runways)
        await hub.broadcast(state.runways_message())

    async def _fetch_navaids() -> list | None:
        # Navaids = theatre (gRPC) + the theatre's on-disk Beacons.lua. Re-read
        # the DCS path from config each time so a Settings change applies live.
        theatre = await grpc_client.fetch_theatre()
        if theatre is None:
            return None  # gRPC not ready yet → retry
        dcs_dir = Settings.from_env().dcs_install_dir
        navaids = load_navaids(dcs_dir, theatre)
        # None (file not found) → definitive empty so we don't retry forever.
        return navaids if navaids is not None else []

    async def _refresh_navaids(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        navaids = await _refresh_with_retry(_fetch_navaids, "navaids")
        if navaids is None:
            return
        state.set_navaids(navaids)
        await hub.broadcast(state.navaids_message())

    async def _refresh_marks(initial_delay: float = 0.0) -> None:
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        marks = await _refresh_with_retry(grpc_client.fetch_marks, "marks")
        if marks is None:
            return
        state.set_marks(marks)
        await hub.broadcast(state.marks_message())

    # Fog-of-war detection is *dynamic* (unlike the static routes/airbases/…
    # which are fetched once per connect), so it's polled on an interval. The
    # loop self-gates: fetch_fog_contacts returns (None, True) with no live
    # channel, so it idles cheaply while disconnected, and we only spend an
    # Eval when at least one browser is actually listening.
    _FOG_POLL_INTERVAL_S = 1.5

    async def _fog_poll_loop() -> None:
        prev_eval_ok = True
        while True:
            try:
                await asyncio.sleep(_FOG_POLL_INTERVAL_S)
                if hub.client_count == 0:
                    continue
                by_coalition, eval_ok = await grpc_client.fetch_fog_contacts()
                if by_coalition is None:
                    if eval_ok:
                        continue  # transient (channel down / paused) — retry
                    # Eval disabled: surface the hint once, then stay quiet
                    # until the flag flips (avoids spamming an empty frame).
                    state.set_fog({}, eval_ok=False)
                    if prev_eval_ok:
                        await hub.broadcast(state.fog_message())
                    prev_eval_ok = False
                    continue
                prev_eval_ok = True
                state.set_fog(by_coalition, eval_ok=True)
                await hub.broadcast(state.fog_message())
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — never let the loop die
                log.warning("fog poll error: %s: %s", type(exc).__name__, exc)

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
        cleared_air = state.clear_airbases()
        cleared_rwy = state.clear_runways()
        cleared_nav = state.clear_navaids()
        cleared_marks = state.clear_marks()
        state.clear_fog()
        if (cleared or cleared_routes or cleared_bull or cleared_air
                or cleared_rwy or cleared_nav or cleared_marks):
            log.info(
                "gRPC dropped — cleared %d units, %d routes, %d bullseyes, "
                "%d airbases, %d runways, %d navaids, %d marks",
                cleared,
                cleared_routes,
                cleared_bull,
                cleared_air,
                cleared_rwy,
                cleared_nav,
                cleared_marks,
            )
        await hub.broadcast({"type": "units_snapshot", "units": []})
        await hub.broadcast({"type": "mission_routes_snapshot", "routes": []})
        await hub.broadcast({"type": "bullseyes_snapshot", "bullseyes": []})
        await hub.broadcast({"type": "airbases_snapshot", "airbases": []})
        await hub.broadcast({"type": "runways_snapshot", "runways": []})
        await hub.broadcast({"type": "navaids_snapshot", "navaids": []})
        await hub.broadcast({"type": "marks_snapshot", "marks": []})
        await hub.broadcast(state.fog_message())

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
        asyncio.create_task(_refresh_airbases(initial_delay=5.0))
        asyncio.create_task(_refresh_runways(initial_delay=5.0))
        asyncio.create_task(_refresh_navaids(initial_delay=5.0))
        asyncio.create_task(_refresh_marks(initial_delay=5.0))

    async def on_mission_end() -> None:
        # Mission unloaded. Clear static data immediately so a stale flight
        # plan doesn't linger across the briefing/load gap. Units are
        # similarly cleared by the StreamUnits gone messages and/or
        # mission_start's fresh snapshot. The gRPC channel stays up.
        cleared_routes = state.clear_routes()
        cleared_bull = state.clear_bullseyes()
        cleared_air = state.clear_airbases()
        cleared_rwy = state.clear_runways()
        cleared_nav = state.clear_navaids()
        cleared_marks = state.clear_marks()
        state.clear_fog()
        log.info(
            "mission ended — cleared %d routes, %d bullseyes, %d airbases, "
            "%d runways, %d navaids, %d marks",
            cleared_routes,
            cleared_bull,
            cleared_air,
            cleared_rwy,
            cleared_nav,
            cleared_marks,
        )
        await hub.broadcast({"type": "mission_routes_snapshot", "routes": []})
        await hub.broadcast({"type": "bullseyes_snapshot", "bullseyes": []})
        await hub.broadcast({"type": "airbases_snapshot", "airbases": []})
        await hub.broadcast({"type": "runways_snapshot", "runways": []})
        await hub.broadcast({"type": "navaids_snapshot", "navaids": []})
        await hub.broadcast({"type": "marks_snapshot", "marks": []})
        await hub.broadcast(state.fog_message())

    async def on_mark_add(mark: Mark) -> None:
        state.upsert_mark(mark)
        await hub.broadcast({"type": "mark_added", "mark": mark.to_dict()})

    async def on_mark_remove(mark_id: int) -> None:
        if state.remove_mark(mark_id) is not None:
            await hub.broadcast({"type": "mark_removed", "id": mark_id})

    basemaps = build_basemaps(settings)
    tile_cache = TileCache(
        basemaps=basemaps,
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
        fog_task = asyncio.create_task(_fog_poll_loop(), name="mizmap-fog-poll")
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
            fog_task.cancel()
            try:
                await fog_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
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
                "airbases": len(state.airbases),
                "runways": len(state.runways),
                "navaids": len(state.navaids),
                "marks": len(state.marks),
                "fog_contacts": sum(len(v) for v in state.fog.values()),
                "fog_eval_ok": state.fog_eval_ok,
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
        # Always serve locally-proxied tile URLs; upstream URLs stay private to
        # the backend (see /tiles route). The frontend renders one selectable
        # basemap at a time, defaulting to `defaultBasemap`.
        return JSONResponse(
            {
                "basemaps": [
                    {
                        "id": b.id,
                        "label": b.label,
                        "url": f"/tiles/{b.id}/{{z}}/{{x}}/{{y}}",
                        "attribution": b.attribution,
                        "maxNativeZoom": b.max_native_zoom,
                    }
                    for b in basemaps
                ],
                "defaultBasemap": DEFAULT_BASEMAP_ID,
            }
        )

    # --- settings (config UX) ----------------------------------------------
    # Editable via the in-app Settings panel. Network keys need a restart to
    # apply (can't rebind a live socket); dcs_install_dir applies on save.
    _NETWORK_KEYS = ("http_host", "http_port", "grpc_host", "grpc_port")
    _EDITABLE_KEYS = (*_NETWORK_KEYS, "dcs_install_dir")

    def _setting_value(s: Settings, key: str) -> object:
        # dcs_install_dir: show only an explicit override so the field stays
        # blank when relying on auto-detect (the detected path is the
        # placeholder); saving blank then keeps auto-detect rather than pinning.
        if key == "dcs_install_dir":
            return str(configured_value(key) or "")
        v = getattr(s, key)
        if v is None:
            return ""
        return str(v) if isinstance(v, Path) else v

    @app.get("/api/settings")
    async def get_settings() -> JSONResponse:
        s = Settings.from_env()  # fresh — reflects the saved file, not startup
        locked = env_locked_keys()
        detected = detect_dcs_install_dir()
        out = {
            key: {
                "value": _setting_value(s, key),
                "env_locked": key in locked,
                "restart_required": key in _NETWORK_KEYS,
            }
            for key in _EDITABLE_KEYS
        }
        return JSONResponse(
            {
                "settings": out,
                "dcs_install_dir_detected": str(detected) if detected else None,
            }
        )

    @app.post("/api/settings")
    async def post_settings(body: _SettingsUpdate) -> JSONResponse:
        provided = body.model_dump(exclude_unset=True)
        locked = env_locked_keys()
        updates: dict[str, object] = {}
        errors: list[str] = []
        for key in _EDITABLE_KEYS:
            if key not in provided:
                continue
            if key in locked:
                errors.append(f"{key} is pinned by an environment variable")
                continue
            raw = provided[key]
            if key in ("http_port", "grpc_port"):
                try:
                    port = int(raw)
                except (TypeError, ValueError):
                    errors.append(f"{key} must be an integer")
                    continue
                if not (1 <= port <= 65535):
                    errors.append(f"{key} must be between 1 and 65535")
                    continue
                updates[key] = port
            elif key in ("http_host", "grpc_host"):
                host = str(raw).strip()
                if not host:
                    errors.append(f"{key} must not be empty")
                    continue
                updates[key] = host
            elif key == "dcs_install_dir":
                path = str(raw).strip()
                if not path:
                    updates[key] = None  # clear → revert to auto-detect
                elif not Path(path).is_dir():
                    errors.append("dcs_install_dir: directory does not exist")
                else:
                    updates[key] = Path(path).as_posix()
        if errors:
            return JSONResponse({"saved": False, "errors": errors}, status_code=400)
        if not updates:
            return JSONResponse({"saved": False, "errors": ["no changes"]}, status_code=400)
        update_config_file(updates)
        restart_required = sorted(
            k for k in updates if k in _NETWORK_KEYS and updates[k] != getattr(settings, k)
        )
        # dcs_install_dir applies live: re-resolve + re-parse Beacons.lua and
        # re-broadcast navaids (no restart). _fetch_navaids reads the path fresh.
        if "dcs_install_dir" in updates:
            asyncio.create_task(_refresh_navaids())
        return JSONResponse({"saved": True, "restart_required": restart_required})

    @app.get("/tiles/{source}/{z}/{x}/{y}")
    async def tile(source: str, z: int, x: int, y: int) -> Response:
        if not tile_cache.has_source(source):
            raise HTTPException(status_code=404, detail="unknown basemap")
        # Cheap sanity bound — Leaflet won't request beyond ~22.
        if not (0 <= z <= 22) or x < 0 or y < 0:
            raise HTTPException(status_code=400, detail="z/x/y out of range")
        try:
            data, status = await tile_cache.fetch(source, z, x, y)
        except httpx.HTTPError as exc:
            log.warning("tile %s/%d/%d/%d upstream fetch failed: %s", source, z, x, y, exc)
            raise HTTPException(status_code=502, detail="upstream tile fetch failed") from exc
        # Browser-side cache lets us avoid even hitting the proxy on subsequent
        # views of the same tile within a session. Tiles are immutable.
        return Response(
            content=data,
            media_type=tile_cache.content_type(source),
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
            await ws.send_json(state.airbases_message())
            await ws.send_json(state.runways_message())
            await ws.send_json(state.navaids_message())
            await ws.send_json(state.marks_message())
            await ws.send_json(state.fog_message())
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
