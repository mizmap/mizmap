"""Coalition bullseyes — navigation reference points set at mission start.

Each coalition (RED, BLUE) typically has a bullseye defined in the .miz; pilots
call out target positions relative to it. DCS-gRPC exposes one via
`CoalitionService.GetBullseye(coalition)` and the position is static for the
mission's lifetime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Bullseye:
    coalition: int  # DCS Coalition enum: 1=neutral, 2=red, 3=blue
    lat: float
    lon: float
    alt: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "coalition": self.coalition,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
        }
