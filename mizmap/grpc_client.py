"""Async DCS-gRPC client.

Connects to a DCS-gRPC server, subscribes to `MissionService.StreamUnits`, and
dispatches updates through callbacks. Reconnects forever with exponential
backoff.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

import grpc

import json

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.coalition.v0 import coalition_pb2, coalition_pb2_grpc
from dcs.common.v0 import common_pb2
from dcs.custom.v0 import custom_pb2, custom_pb2_grpc
from dcs.mission.v0 import mission_pb2, mission_pb2_grpc
from dcs.world.v0 import world_pb2, world_pb2_grpc

from mizmap.bullseye import Bullseye
from mizmap.marks import Mark, mark_from_event, mark_from_proto
from mizmap.routes import LUA_SNIPPET, GroupRoute, parse_eval_json

log = logging.getLogger(__name__)

StatusCallback = Callable[[bool, str | None], Awaitable[None]]
UnitCallback = Callable[[common_pb2.Unit], Awaitable[None]]
UnitGoneCallback = Callable[[int], Awaitable[None]]
DisconnectCallback = Callable[[], Awaitable[None]]
MissionEventCallback = Callable[[], Awaitable[None]]
MarkCallback = Callable[[Mark], Awaitable[None]]
MarkRemoveCallback = Callable[[int], Awaitable[None]]


class DcsGrpcClient:
    """Maintains a long-lived connection to DCS-gRPC.

    On each (re)connect:
      - calls `on_status(True, None)`
      - subscribes to StreamUnits AND StreamEvents in parallel
      - dispatches unit frames to `on_unit` / `on_unit_gone`
      - dispatches mission_start events to `on_mission_start`, mission_end
        events to `on_mission_end`

    On disconnect:
      - calls `on_status(False, error)`
      - calls `on_disconnect()` so the host can clear stale state.
    """

    def __init__(
        self,
        host: str,
        port: int,
        *,
        on_status: StatusCallback,
        on_unit: UnitCallback,
        on_unit_gone: UnitGoneCallback,
        on_disconnect: DisconnectCallback,
        on_mission_start: MissionEventCallback,
        on_mission_end: MissionEventCallback,
        on_mark_add: MarkCallback,
        on_mark_remove: MarkRemoveCallback,
        backoff_min: float = 1.0,
        backoff_max: float = 15.0,
    ) -> None:
        self._target = f"{host}:{port}"
        self._on_status = on_status
        self._on_unit = on_unit
        self._on_unit_gone = on_unit_gone
        self._on_disconnect = on_disconnect
        self._on_mission_start = on_mission_start
        self._on_mission_end = on_mission_end
        self._on_mark_add = on_mark_add
        self._on_mark_remove = on_mark_remove
        self._backoff_min = backoff_min
        self._backoff_max = backoff_max
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._was_connected = False
        # Held for fetch_* methods (Eval, GetBullseye, GetMagneticDeclination);
        # cleared on disconnect.
        self._channel: grpc.aio.Channel | None = None

    @property
    def target(self) -> str:
        return self._target

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name="mizmap-grpc-client")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass

    async def _run(self) -> None:
        backoff = self._backoff_min
        while not self._stop.is_set():
            try:
                async with grpc.aio.insecure_channel(self._target) as channel:
                    await asyncio.wait_for(channel.channel_ready(), timeout=3.0)
                    self._channel = channel
                    await self._on_status(True, None)
                    self._was_connected = True
                    backoff = self._backoff_min
                    log.info("connected to DCS-gRPC at %s", self._target)
                    # StreamUnits is the load-bearing stream — if it fails, the
                    # channel is dead and we need to reconnect. StreamEvents is
                    # additive — if it returns UNIMPLEMENTED (e.g. against the
                    # mock) we want unit streaming to keep going regardless.
                    # asyncio.gather propagates the first exception; the events
                    # task swallows its own errors so only a real channel-level
                    # failure trips the gather.
                    await asyncio.gather(
                        self._consume_units(channel),
                        self._consume_events(channel),
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — surface and retry
                msg = f"{type(exc).__name__}: {exc}"
                log.debug("gRPC connection failed: %s", msg)
                await self._on_status(False, msg)
                if self._was_connected:
                    self._was_connected = False
                    await self._on_disconnect()
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, self._backoff_max)
            finally:
                self._channel = None
        # Final disconnect notification if we were connected.
        if self._was_connected:
            await self._on_disconnect()

    async def fetch_routes(self, timeout: float = 5.0) -> list[GroupRoute] | None:
        """Pull every group's planned route via CustomService.Eval.

        Returns `None` on RPC failure (timeout, Eval disabled, channel down,
        etc.) so callers can retry; returns `[]` on a successful call with no
        routes defined in the mission. Eval is gated behind `evalEnabled =
        true` in `Saved Games/DCS/Config/dcs-grpc.lua`; without it the
        rust-server replies with FAILED_PRECONDITION and we log + return None.
        """
        channel = self._channel
        if channel is None:
            log.debug("fetch_routes called with no live channel")
            return None
        try:
            stub = custom_pb2_grpc.CustomServiceStub(channel)
            resp = await asyncio.wait_for(
                stub.Eval(custom_pb2.EvalRequest(lua=LUA_SNIPPET)),
                timeout=timeout,
            )
        except grpc.aio.AioRpcError as exc:
            log.warning("Eval(routes) failed: %s — %s", exc.code(), exc.details())
            return None
        except Exception as exc:  # noqa: BLE001
            log.warning("fetch_routes error: %s: %s", type(exc).__name__, exc)
            return None
        routes = parse_eval_json(resp.json)
        log.info("fetched %d group routes", len(routes))
        return routes

    async def fetch_bullseyes(self, timeout: float = 3.0) -> list[Bullseye] | None:
        """Pull RED + BLUE bullseyes via CoalitionService.GetBullseye.

        Per-coalition best-effort: a mission may define one and not the other,
        in which case the missing call raises NOT_FOUND and we skip it.
        Returns `None` only if BOTH calls were transient failures (timeout,
        channel down). A NOT_FOUND on either side counts as a definitive
        response — that coalition just has no bullseye defined.
        """
        channel = self._channel
        if channel is None:
            return None
        stub = coalition_pb2_grpc.CoalitionServiceStub(channel)
        out: list[Bullseye] = []
        any_responded = False
        for coalition in (common_pb2.COALITION_BLUE, common_pb2.COALITION_RED):
            try:
                resp = await asyncio.wait_for(
                    stub.GetBullseye(coalition_pb2.GetBullseyeRequest(coalition=coalition)),
                    timeout=timeout,
                )
            except grpc.aio.AioRpcError as exc:
                if exc.code() == grpc.StatusCode.NOT_FOUND:
                    # Definitive "no bullseye for this coalition" — not a
                    # transient failure.
                    any_responded = True
                log.debug("GetBullseye(%s) failed: %s", coalition, exc.code())
                continue
            except Exception as exc:  # noqa: BLE001
                log.warning("GetBullseye(%s) error: %s", coalition, exc)
                continue
            any_responded = True
            pos = resp.position
            out.append(
                Bullseye(coalition=int(coalition), lat=pos.lat, lon=pos.lon, alt=pos.alt)
            )
        if not any_responded:
            log.info("bullseyes: all attempts failed (transient — retry candidate)")
            return None
        log.info("fetched %d bullseyes", len(out))
        return out

    async def fetch_marks(self, timeout: float = 3.0) -> list[Mark] | None:
        """Pull all F10 map marks via WorldService.GetMarkPanels.

        No Eval dependency. Returns `None` on transient failure (channel down,
        timeout) so callers can retry, `[]` on a successful call with no marks.
        Visibility scoping (coalition/group) is preserved on each Mark; filtering
        happens on the frontend against the local own-ship.
        """
        channel = self._channel
        if channel is None:
            return None
        try:
            stub = world_pb2_grpc.WorldServiceStub(channel)
            resp = await asyncio.wait_for(
                stub.GetMarkPanels(world_pb2.GetMarkPanelsRequest()),
                timeout=timeout,
            )
        except grpc.aio.AioRpcError as exc:
            log.warning("GetMarkPanels failed: %s — %s", exc.code(), exc.details())
            return None
        except Exception as exc:  # noqa: BLE001
            log.warning("fetch_marks error: %s: %s", type(exc).__name__, exc)
            return None
        marks = [mark_from_proto(p) for p in resp.mark_panels]
        log.info("fetched %d marks", len(marks))
        return marks

    async def fetch_elevation(self, lat: float, lon: float, timeout: float = 3.0) -> float | None:
        """Return terrain elevation (m MSL) at a lat/lon, or None on failure.

        Uses DCS-gRPC Eval to call coord.LLtoLO + land.getHeight in-engine. The
        result matches what DCS itself uses for that point. Requires
        `evalEnabled = true` in `Saved Games/DCS/Config/dcs-grpc.lua`.
        """
        channel = self._channel
        if channel is None:
            return None
        # Inline the lat/lon — Eval takes a Lua string, no parameter binding.
        # DCS quirks: coord.LLtoLO(lat, lon, alt) returns a Vec3 {x, y, z} where
        # y is altitude and z is the second horizontal axis. land.getHeight takes
        # a Vec2 {x, y} where y is z from the Vec3. So we map vec3.z → arg.y.
        lua = (
            "local p = coord.LLtoLO(%.10f, %.10f, 0); "
            "return land.getHeight({ x = p.x, y = p.z })"
        ) % (lat, lon)
        try:
            stub = custom_pb2_grpc.CustomServiceStub(channel)
            resp = await asyncio.wait_for(
                stub.Eval(custom_pb2.EvalRequest(lua=lua)),
                timeout=timeout,
            )
        except grpc.aio.AioRpcError as exc:
            log.warning("Eval(elevation) failed: %s — %s", exc.code(), exc.details())
            return None
        except Exception as exc:  # noqa: BLE001
            log.warning("fetch_elevation error: %s: %s", type(exc).__name__, exc)
            return None
        try:
            value = json.loads(resp.json)
        except json.JSONDecodeError:
            log.warning("elevation Eval returned non-JSON: %r", resp.json[:120])
            return None
        if not isinstance(value, (int, float)):
            return None
        return float(value)

    async def fetch_declination(
        self, lat: float, lon: float, alt: float = 0.0, timeout: float = 3.0
    ) -> float | None:
        """Return the magnetic declination (degrees) at a lat/lon/alt, or None.

        Direct `CustomService.GetMagneticDeclination` RPC — no Eval involved,
        no `evalEnabled` config dependency. DCS-gRPC computes via the IGRF
        model. Sign convention per the proto: positive = easterly declination
        (magnetic north is east of true north), negative = westerly.
        `True North + declination = Magnetic North`, so to convert a true
        bearing to magnetic: `bearing_M = bearing_T - declination`.
        """
        channel = self._channel
        if channel is None:
            return None
        try:
            stub = custom_pb2_grpc.CustomServiceStub(channel)
            resp = await asyncio.wait_for(
                stub.GetMagneticDeclination(
                    custom_pb2.GetMagneticDeclinationRequest(lat=lat, lon=lon, alt=alt)
                ),
                timeout=timeout,
            )
        except grpc.aio.AioRpcError as exc:
            log.warning("GetMagneticDeclination failed: %s — %s", exc.code(), exc.details())
            return None
        except Exception as exc:  # noqa: BLE001
            log.warning("fetch_declination error: %s: %s", type(exc).__name__, exc)
            return None
        return float(resp.declination)

    async def _consume_units(self, channel: grpc.aio.Channel) -> None:
        """Stream units and dispatch each frame. Returns on disconnect."""
        stub = mission_pb2_grpc.MissionServiceStub(channel)
        req = mission_pb2.StreamUnitsRequest(poll_rate=1, max_backoff=3)
        async for response in stub.StreamUnits(req):
            if self._stop.is_set():
                return
            which = response.WhichOneof("update")
            if which == "unit":
                await self._on_unit(response.unit)
            elif which == "gone":
                await self._on_unit_gone(response.gone.id)

    async def _consume_events(self, channel: grpc.aio.Channel) -> None:
        """Subscribe to mission events; dispatch mission_start/_end.

        Resilient: a stream that returns `UNIMPLEMENTED` (e.g. the dev mock
        doesn't expose this RPC) just logs once and exits cleanly so the unit
        stream keeps running. Any other RPC error after first event is
        propagated to the caller via the outer reconnect loop, since it
        usually means the channel itself is dying.
        """
        stub = mission_pb2_grpc.MissionServiceStub(channel)
        req = mission_pb2.StreamEventsRequest()
        try:
            async for response in stub.StreamEvents(req):
                if self._stop.is_set():
                    return
                which = response.WhichOneof("event")
                if which == "mission_start":
                    log.info("mission_start event received")
                    await self._on_mission_start()
                elif which == "mission_end":
                    log.info("mission_end event received")
                    await self._on_mission_end()
                elif which == "mark_add":
                    await self._on_mark_add(mark_from_event(response.mark_add))
                elif which == "mark_change":
                    # Treat change as an upsert — same shape as add.
                    await self._on_mark_add(mark_from_event(response.mark_change))
                elif which == "mark_remove":
                    await self._on_mark_remove(int(response.mark_remove.id))
                # All other event kinds intentionally ignored.
        except grpc.aio.AioRpcError as exc:
            if exc.code() == grpc.StatusCode.UNIMPLEMENTED:
                log.warning(
                    "StreamEvents unavailable (UNIMPLEMENTED) — "
                    "mission-change auto-refresh disabled for this connection"
                )
                return
            raise
