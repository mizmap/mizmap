"""Mock DCS-gRPC server for Mac-side development.

Implements just enough of `MissionService.StreamUnits` to let the real MizMap
client connect, see "connected", and (in Phase 1) receive unit updates.

Scenario: 4 units in the DCS Caucasus theater, moving on simple courses.
Run with:  `python -m mizmap.dev.mock_server`
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from dataclasses import dataclass

import grpc

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.common.v0 import common_pb2
from dcs.custom.v0 import custom_pb2, custom_pb2_grpc
from dcs.mission.v0 import mission_pb2, mission_pb2_grpc
from dcs.world.v0 import world_pb2, world_pb2_grpc

log = logging.getLogger(__name__)

# Earth radius for the (tiny) flat-earth course integration we do for the mock.
_EARTH_R_M = 6_371_000.0


@dataclass
class MockUnit:
    id: int
    name: str
    callsign: str
    type: str
    coalition: int
    group_id: int
    group_name: str
    group_category: int
    lat: float
    lon: float
    alt: float
    heading_rad: float
    speed_mps: float
    player_name: str | None = None

    def advance(self, dt: float) -> None:
        # Local-tangent-plane integration is fine at our scale.
        dx = self.speed_mps * dt * math.sin(self.heading_rad)
        dy = self.speed_mps * dt * math.cos(self.heading_rad)
        dlat = dy / _EARTH_R_M
        dlon = dx / (_EARTH_R_M * math.cos(math.radians(self.lat)))
        self.lat += math.degrees(dlat)
        self.lon += math.degrees(dlon)

    def to_proto(self) -> common_pb2.Unit:
        kwargs = dict(
            id=self.id,
            name=self.name,
            callsign=self.callsign,
            coalition=self.coalition,
            type=self.type,
            position=common_pb2.Position(lat=self.lat, lon=self.lon, alt=self.alt),
            orientation=common_pb2.Orientation(heading=self.heading_rad),
            velocity=common_pb2.Velocity(
                heading=self.heading_rad, speed=self.speed_mps
            ),
            group=common_pb2.Group(
                id=self.group_id,
                name=self.group_name,
                coalition=self.coalition,
                category=self.group_category,
            ),
            number_in_group=1,
        )
        if self.player_name is not None:
            kwargs["player_name"] = self.player_name
        return common_pb2.Unit(**kwargs)


def _build_scenario() -> list[MockUnit]:
    return [
        MockUnit(
            id=1,
            name="Hornet-1-1",
            callsign="ENFIELD11",
            type="FA-18C_hornet",
            coalition=common_pb2.COALITION_BLUE,
            group_id=10,
            group_name="Enfield",
            group_category=common_pb2.GROUP_CATEGORY_AIRPLANE,
            lat=43.05,
            lon=39.79,  # near Sukhumi
            alt=3000.0,
            heading_rad=math.radians(90),
            speed_mps=200.0,
            # Marked as a player so own-ship features (auto-center, recenter
            # button, nav-mode follow, telemetry HUD's own-ship row) are
            # exercisable against the mock without a real DCS connection.
            player_name="TestPilot",
        ),
        MockUnit(
            id=2,
            name="Hornet-1-2",
            callsign="ENFIELD12",
            type="FA-18C_hornet",
            coalition=common_pb2.COALITION_BLUE,
            group_id=10,
            group_name="Enfield",
            group_category=common_pb2.GROUP_CATEGORY_AIRPLANE,
            lat=43.04,
            lon=39.77,
            alt=3000.0,
            heading_rad=math.radians(90),
            speed_mps=200.0,
        ),
        MockUnit(
            id=3,
            name="SA-10-Site",
            callsign="SA10",
            type="S-300PS 40B6M tr",
            coalition=common_pb2.COALITION_RED,
            group_id=20,
            group_name="Sochi SAM",
            group_category=common_pb2.GROUP_CATEGORY_GROUND,
            lat=43.585,
            lon=39.723,  # near Sochi
            alt=10.0,
            heading_rad=0.0,
            speed_mps=0.0,
        ),
        MockUnit(
            id=4,
            name="Cruiser-1",
            callsign="VINSON",
            type="CV_1143_5",
            coalition=common_pb2.COALITION_BLUE,
            group_id=30,
            group_name="Vinson",
            group_category=common_pb2.GROUP_CATEGORY_SHIP,
            lat=43.20,
            lon=39.40,
            alt=0.0,
            heading_rad=math.radians(45),
            speed_mps=10.0,
        ),
    ]


class MockMissionService(mission_pb2_grpc.MissionServiceServicer):
    def __init__(self) -> None:
        self._units = _build_scenario()
        self._t0 = time.monotonic()
        self._last_tick = self._t0

    def _tick(self) -> None:
        now = time.monotonic()
        dt = now - self._last_tick
        self._last_tick = now
        for u in self._units:
            u.advance(dt)

    async def StreamUnits(
        self,
        request: mission_pb2.StreamUnitsRequest,
        context: grpc.aio.ServicerContext,
    ):
        # poll_rate is in seconds-between-frames (DCS-gRPC semantics).
        period = max(0.1, float(request.poll_rate or 1))
        log.info("StreamUnits client connected (period=%.2fs)", period)
        try:
            while True:
                self._tick()
                t = time.monotonic() - self._t0
                for u in self._units:
                    yield mission_pb2.StreamUnitsResponse(time=t, unit=u.to_proto())
                await asyncio.sleep(period)
        except asyncio.CancelledError:
            log.info("StreamUnits client disconnected")
            raise

    async def StreamEvents(
        self,
        request: mission_pb2.StreamEventsRequest,
        context: grpc.aio.ServicerContext,
    ):
        # Emit a synthetic mark add/remove cycle so the live-events path is
        # exercisable against the mock. Adds a "Dynamic Mark" every 20s and
        # removes it 10s later, alternating between two positions. The real
        # DCS-gRPC StreamEvents emits many other event kinds; the consumer
        # ignores everything except mission_start/_end and the mark events,
        # so the minimal subset here is sufficient.
        log.info("StreamEvents client connected")
        dynamic_id = 9_000_001
        positions = [
            (43.10, 39.85, "Dynamic Mark A"),
            (43.30, 39.60, "Dynamic Mark B"),
        ]
        i = 0
        try:
            while True:
                await asyncio.sleep(20.0)
                lat, lon, text = positions[i % len(positions)]
                i += 1
                yield mission_pb2.StreamEventsResponse(
                    time=time.monotonic() - self._t0,
                    mark_add=mission_pb2.StreamEventsResponse.MarkAddEvent(
                        id=dynamic_id,
                        coalition=common_pb2.COALITION_BLUE,
                        position=common_pb2.Position(lat=lat, lon=lon, alt=0.0),
                        text=text,
                    ),
                )
                await asyncio.sleep(10.0)
                yield mission_pb2.StreamEventsResponse(
                    time=time.monotonic() - self._t0,
                    mark_remove=mission_pb2.StreamEventsResponse.MarkRemoveEvent(
                        id=dynamic_id,
                        coalition=common_pb2.COALITION_BLUE,
                        position=common_pb2.Position(lat=lat, lon=lon, alt=0.0),
                        text=text,
                    ),
                )
        except asyncio.CancelledError:
            log.info("StreamEvents client disconnected")
            raise


class MockWorldService(world_pb2_grpc.WorldServiceServicer):
    """Just enough to satisfy `WorldService.GetMarkPanels` + `GetAirbases`."""

    # A handful of Caucasus airbases near the unit scenario: two airfields, a
    # FARP, and a carrier. The carrier (SHIP) is deliberately co-located with
    # the moving cruiser unit so the frontend's skip-ships dedup is exercisable.
    _AIRBASES = [
        common_pb2.Airbase(
            name="Sochi-Adler",
            callsign="Sochi",
            coalition=common_pb2.COALITION_BLUE,
            position=common_pb2.Position(lat=43.449, lon=39.956, alt=10.0),
            category=common_pb2.AIRBASE_CATEGORY_AIRDROME,
            display_name="Sochi-Adler",
        ),
        common_pb2.Airbase(
            name="Gudauta",
            callsign="Gudauta",
            coalition=common_pb2.COALITION_RED,
            position=common_pb2.Position(lat=43.105, lon=40.583, alt=20.0),
            category=common_pb2.AIRBASE_CATEGORY_AIRDROME,
            display_name="Gudauta",
        ),
        common_pb2.Airbase(
            name="FARP London",
            callsign="London",
            coalition=common_pb2.COALITION_BLUE,
            position=common_pb2.Position(lat=43.30, lon=39.85, alt=15.0),
            category=common_pb2.AIRBASE_CATEGORY_HELIPAD,
            display_name="FARP London",
        ),
        common_pb2.Airbase(
            name="CVN-71 Roosevelt",
            callsign="Roosevelt",
            coalition=common_pb2.COALITION_BLUE,
            position=common_pb2.Position(lat=43.20, lon=39.40, alt=0.0),
            category=common_pb2.AIRBASE_CATEGORY_SHIP,
            display_name="CVN-71 Roosevelt",
        ),
    ]

    def __init__(self) -> None:
        # Two static marks: one campaign-style (visible to all), one
        # coalition-restricted. The dynamic third mark is added/removed
        # by StreamEvents and isn't included here.
        self._marks = [
            common_pb2.MarkPanel(
                id=1,
                time=0.0,
                # No coalition set → visible to all (the rust-server's
                # asymmetry: coalition is left unset when no restriction,
                # but group_id always uses the UINT32_MAX sentinel).
                group_id=0xFFFFFFFF,
                text="BULLSEYE-Y",
                position=common_pb2.Position(lat=42.95, lon=39.65, alt=0.0),
            ),
            common_pb2.MarkPanel(
                id=2,
                time=0.0,
                coalition=common_pb2.COALITION_BLUE,
                group_id=0xFFFFFFFF,
                text="TANKER STA  BRAVO",
                position=common_pb2.Position(lat=43.45, lon=39.50, alt=0.0),
            ),
        ]

    async def GetMarkPanels(
        self,
        request: world_pb2.GetMarkPanelsRequest,
        context: grpc.aio.ServicerContext,
    ) -> world_pb2.GetMarkPanelsResponse:
        return world_pb2.GetMarkPanelsResponse(mark_panels=self._marks)

    async def GetAirbases(
        self,
        request: world_pb2.GetAirbasesRequest,
        context: grpc.aio.ServicerContext,
    ) -> world_pb2.GetAirbasesResponse:
        # Real server filters by request.coalition; the mock returns all.
        return world_pb2.GetAirbasesResponse(airbases=self._AIRBASES)

    async def GetTheatre(
        self,
        request: world_pb2.GetTheatreRequest,
        context: grpc.aio.ServicerContext,
    ) -> world_pb2.GetTheatreResponse:
        # The mock scenario is in the Caucasus. On a box with DCS installed, the
        # Navaids layer then parses the real Caucasus Beacons.lua; elsewhere
        # (no DCS) navaids just stay empty.
        return world_pb2.GetTheatreResponse(theatre="Caucasus")


class MockCustomService(custom_pb2_grpc.CustomServiceServicer):
    """Minimal Eval — serves canned runway JSON for the getRunways snippet.

    The real client uses `CustomService.Eval` for routes, elevation AND runways.
    Only runways are mocked here (so the layer renders without real DCS); every
    other Eval returns an empty JSON list, leaving routes/elevation empty exactly
    as before this servicer existed. `course` is pre-negated to mirror the real
    DCS sign convention (`parse_runways_json` negates again), so the rendered
    headings come out as commented.
    """

    # course = -radians(desired_heading); parse negates → desired heading.
    _RUNWAYS_JSON = json.dumps(
        [
            {
                "airbase_name": "Sochi-Adler", "name": 6, "course": -math.radians(60),
                "length": 2500, "width": 45, "lat": 43.449, "lon": 39.956,
            },
            {
                "airbase_name": "Gudauta", "name": 33, "course": -math.radians(330),
                "length": 2000, "width": 40, "lat": 43.105, "lon": 40.583,
            },
        ]
    )

    async def Eval(
        self,
        request: custom_pb2.EvalRequest,
        context: grpc.aio.ServicerContext,
    ) -> custom_pb2.EvalResponse:
        if "getRunways" in (request.lua or ""):
            return custom_pb2.EvalResponse(json=self._RUNWAYS_JSON)
        # Routes / elevation aren't mocked — empty list keeps them blank.
        return custom_pb2.EvalResponse(json="[]")


async def _serve(host: str, port: int) -> None:
    server = grpc.aio.server()
    mission_pb2_grpc.add_MissionServiceServicer_to_server(MockMissionService(), server)
    world_pb2_grpc.add_WorldServiceServicer_to_server(MockWorldService(), server)
    custom_pb2_grpc.add_CustomServiceServicer_to_server(MockCustomService(), server)
    bind = f"{host}:{port}"
    server.add_insecure_port(bind)
    await server.start()
    log.info("mock DCS-gRPC server listening on %s", bind)
    await server.wait_for_termination()


def main() -> None:
    import os

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    host = os.environ.get("MIZMAP_MOCK_HOST", "127.0.0.1")
    port = int(os.environ.get("MIZMAP_MOCK_PORT", "50051"))
    try:
        asyncio.run(_serve(host, port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
