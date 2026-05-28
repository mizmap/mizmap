"""In-memory mission state — units + gRPC connection status.

All mutations run on the asyncio event loop and are synchronous (no awaits
mid-mutation), so no lock is needed.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

from mizmap.airbase import Airbase
from mizmap.bullseye import Bullseye
from mizmap.marks import Mark
from mizmap.navaids import Navaid
from mizmap.routes import GroupRoute
from mizmap.runways import Runway
from mizmap.sidc import sidc_for, threat_km_for

_TWO_PI = 2.0 * math.pi


@dataclass
class GrpcStatus:
    connected: bool = False
    host: str = ""
    last_error: str | None = None
    last_change_at: float = field(default_factory=time.time)

    def update(self, *, connected: bool, host: str, error: str | None = None) -> None:
        self.connected = connected
        self.host = host
        self.last_error = error
        self.last_change_at = time.time()

    def to_message(self) -> dict[str, Any]:
        return {
            "type": "grpc_status",
            "connected": self.connected,
            "host": self.host,
            "error": self.last_error,
        }


@dataclass
class Unit:
    id: int
    name: str
    callsign: str
    type: str
    coalition: int  # DCS Coalition enum: 1=neutral, 2=red, 3=blue
    group_id: int
    group_name: str
    group_category: int  # GroupCategory: 1=airplane, 2=helo, 3=ground, 4=ship, 5=train
    lat: float
    lon: float
    alt: float
    heading: float  # nose direction, radians, normalized to [0, 2π)
    speed: float  # m/s
    track: float = 0.0  # direction of motion, radians, normalized to [0, 2π)
    vs: float = 0.0  # vertical speed, m/s, positive = climb
    player_name: str | None = None  # set iff a player is currently flying/controlling this unit
    last_seen: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        # DCS-gRPC 0.8.1 emits unbounded accumulated yaw — normalize so downstream
        # consumers (frontend symbol rotation, tests, future telemetry HUD) can rely
        # on angles ∈ [0, 2π). Python's % on floats with a positive divisor always
        # returns a non-negative remainder, unlike math.fmod.
        # `heading` is the nose direction (use for HUD / HSI-style readouts).
        # `track` is the direction of motion (use for movement vectors). They
        # differ for aircraft in crosswind, skidding ground vehicles, etc.
        self.heading = self.heading % _TWO_PI
        self.track = self.track % _TWO_PI


def unit_to_dict(u: Unit) -> dict[str, Any]:
    return {
        "id": u.id,
        "name": u.name,
        "callsign": u.callsign,
        "type": u.type,
        "coalition": u.coalition,
        "group": {
            "id": u.group_id,
            "name": u.group_name,
            "category": u.group_category,
        },
        "lat": u.lat,
        "lon": u.lon,
        "alt": u.alt,
        "heading": u.heading,
        "speed": u.speed,
        "track": u.track,
        "vs": u.vs,
        "player_name": u.player_name,
        "sidc": sidc_for(u.coalition, u.group_category, u.type),
        "threat_km": threat_km_for(u.type),
    }


@dataclass
class MissionState:
    grpc: GrpcStatus = field(default_factory=GrpcStatus)
    units: dict[int, Unit] = field(default_factory=dict)
    routes: list[GroupRoute] = field(default_factory=list)
    bullseyes: list[Bullseye] = field(default_factory=list)
    airbases: list[Airbase] = field(default_factory=list)
    runways: list[Runway] = field(default_factory=list)
    navaids: list[Navaid] = field(default_factory=list)
    marks: dict[int, Mark] = field(default_factory=dict)

    def upsert(self, unit: Unit) -> tuple[Unit, bool]:
        """Insert or update. Returns (unit, is_new)."""
        is_new = unit.id not in self.units
        self.units[unit.id] = unit
        return unit, is_new

    def remove(self, unit_id: int) -> Unit | None:
        return self.units.pop(unit_id, None)

    def clear(self) -> int:
        n = len(self.units)
        self.units.clear()
        return n

    def snapshot(self) -> list[Unit]:
        return list(self.units.values())

    def snapshot_message(self) -> dict[str, Any]:
        return {
            "type": "units_snapshot",
            "units": [unit_to_dict(u) for u in self.units.values()],
        }

    def set_routes(self, routes: list[GroupRoute]) -> None:
        self.routes = list(routes)

    def clear_routes(self) -> int:
        n = len(self.routes)
        self.routes.clear()
        return n

    def routes_message(self) -> dict[str, Any]:
        return {
            "type": "mission_routes_snapshot",
            "routes": [r.to_dict() for r in self.routes],
        }

    def set_bullseyes(self, bullseyes: list[Bullseye]) -> None:
        self.bullseyes = list(bullseyes)

    def clear_bullseyes(self) -> int:
        n = len(self.bullseyes)
        self.bullseyes.clear()
        return n

    def bullseyes_message(self) -> dict[str, Any]:
        return {
            "type": "bullseyes_snapshot",
            "bullseyes": [b.to_dict() for b in self.bullseyes],
        }

    def set_airbases(self, airbases: list[Airbase]) -> None:
        self.airbases = list(airbases)

    def clear_airbases(self) -> int:
        n = len(self.airbases)
        self.airbases.clear()
        return n

    def airbases_message(self) -> dict[str, Any]:
        return {
            "type": "airbases_snapshot",
            "airbases": [a.to_dict() for a in self.airbases],
        }

    def set_runways(self, runways: list[Runway]) -> None:
        self.runways = list(runways)

    def clear_runways(self) -> int:
        n = len(self.runways)
        self.runways.clear()
        return n

    def runways_message(self) -> dict[str, Any]:
        return {
            "type": "runways_snapshot",
            "runways": [r.to_dict() for r in self.runways],
        }

    def set_navaids(self, navaids: list[Navaid]) -> None:
        self.navaids = list(navaids)

    def clear_navaids(self) -> int:
        n = len(self.navaids)
        self.navaids.clear()
        return n

    def navaids_message(self) -> dict[str, Any]:
        return {
            "type": "navaids_snapshot",
            "navaids": [n.to_dict() for n in self.navaids],
        }

    def set_marks(self, marks: list[Mark]) -> None:
        self.marks = {m.id: m for m in marks}

    def upsert_mark(self, mark: Mark) -> None:
        self.marks[mark.id] = mark

    def remove_mark(self, mark_id: int) -> Mark | None:
        return self.marks.pop(mark_id, None)

    def clear_marks(self) -> int:
        n = len(self.marks)
        self.marks.clear()
        return n

    def marks_message(self) -> dict[str, Any]:
        return {
            "type": "marks_snapshot",
            "marks": [m.to_dict() for m in self.marks.values()],
        }
