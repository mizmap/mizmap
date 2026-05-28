"""Airbases — airfields, FARPs/FOBs, and ships from WorldService.GetAirbases.

DCS-gRPC's `WorldService.GetAirbases` returns every airbase in the loaded
theatre: airdromes (airfields/airports), helipads (FARPs, FOBs, oil rigs), and
ships (carriers/LHAs). Position, name, callsign and coalition come straight off
the proto — no Eval required, unlike routes.

The set is static for the mission apart from `coalition`, which flips if a field
is captured. We treat it with the same re-snapshot-on-(re)connect lifecycle as
routes and bullseyes rather than chasing capture events (rare in single-player).

`category` is the raw DCS `AirbaseCategory` enum: 1=airdrome, 2=helipad, 3=ship.
The frontend skips ships — carriers already render as live units via StreamUnits,
so drawing them again as airbases would double-symbol them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mizmap.sidc import airbase_sidc_for

# DCS AirbaseCategory enum (common.proto)
AIRBASE_CATEGORY_AIRDROME = 1
AIRBASE_CATEGORY_HELIPAD = 2
AIRBASE_CATEGORY_SHIP = 3


@dataclass
class Airbase:
    name: str
    callsign: str
    display_name: str
    coalition: int  # DCS Coalition enum: 1=neutral, 2=red, 3=blue
    category: int  # AirbaseCategory: 1=airdrome, 2=helipad, 3=ship
    lat: float
    lon: float
    alt: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "callsign": self.callsign,
            "display_name": self.display_name,
            "coalition": self.coalition,
            "category": self.category,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "sidc": airbase_sidc_for(self.coalition, self.category),
        }


def airbase_from_proto(p: Any) -> Airbase:
    """Build an Airbase from a `common_pb2.Airbase` proto.

    The optional `unit` field (set for carrier airbases) is intentionally
    ignored — the carrier is already tracked via StreamUnits.
    """
    pos = p.position
    return Airbase(
        name=p.name,
        callsign=p.callsign,
        display_name=p.display_name,
        coalition=int(p.coalition),
        category=int(p.category),
        lat=float(pos.lat),
        lon=float(pos.lon),
        alt=float(pos.alt),
    )
