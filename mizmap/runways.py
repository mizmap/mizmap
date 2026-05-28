"""Airbase runways.

DCS-gRPC 0.8.1 doesn't expose runways via any standard RPC, so — like routes —
we use `CustomService.Eval` (gated behind `evalEnabled = true`) to walk
`world.getAirbases()`, call `Airbase:getRunways()` on each, and convert each
runway's world-space center to lat/lon via the in-engine `coord.LOtoLL`.

The raw `getRunways()` entry, confirmed against a live Afghanistan mission, is:
`{ course = <radians>, Name = <int designator>, position = {x,y,z}, length, width }`.

Two quirks handled at parse time:
  - `course` is negated. DCS returns a value whose sign is inverted relative to a
    compass bearing (the Hoggit wiki's "multiply by -1"); verified empirically by
    matching the negated heading to each runway's `Name` designator (e.g. Farah
    `33` → 330°, Maymana `32` → 322°). We store the corrected true bearing,
    normalized to [0, 2π).
  - `Name` comes back as an integer designator (18, 6, 33). We normalize to a
    zero-padded 2-char string ("18", "06", "33"); a non-numeric Name (e.g. "06L")
    passes through trimmed.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

_TWO_PI = 2.0 * math.pi


@dataclass
class Runway:
    airbase_name: str
    name: str  # runway designator, e.g. "18"; may be "" if DCS gave nothing
    lat: float
    lon: float
    course: float  # true bearing, radians, normalized to [0, 2π), sign-corrected
    length_m: float
    width_m: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "airbase_name": self.airbase_name,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "course": self.course,
            "length_m": self.length_m,
            "width_m": self.width_m,
        }


# Walk every airbase's runways, converting each runway center xyz → lat/lon
# in-engine. `coord.LOtoLL(vec3)` returns (lat, lon, alt); a runway's `position`
# is already a Vec3 {x, y(alt), z}. FARPs/ships return no runways (the inner loop
# just doesn't run). `Name` is emitted as-is (an integer); Python normalizes it.
RUNWAYS_LUA_SNIPPET = r"""
local out = {}
if not world or not world.getAirbases then
  return out
end
for _, ab in pairs(world.getAirbases()) do
  local rws = ab:getRunways()
  if rws then
    for _, rw in ipairs(rws) do
      if rw.position then
        local lat, lon = coord.LOtoLL(rw.position)
        out[#out + 1] = {
          airbase_name = ab:getName(),
          name = rw.Name,
          course = rw.course or 0,
          length = rw.length or 0,
          width = rw.width or 0,
          lat = lat,
          lon = lon,
        }
      end
    end
  end
end
return out
"""


def _normalize_name(raw: Any) -> str:
    """DCS `Name` is an int designator (18); render as a 2-digit string ("18").

    A string designator (e.g. "06L") is trimmed and returned as-is.
    """
    if isinstance(raw, bool):  # guard: bool is an int subclass
        return ""
    if isinstance(raw, (int, float)):
        return f"{int(round(raw)):02d}"
    if isinstance(raw, str):
        return raw.strip()
    return ""


def parse_runways_json(payload: str) -> list[Runway]:
    """Parse the JSON returned by the runways Eval into typed Runways.

    Tolerant: a single malformed entry is skipped with a warning rather than
    tanking the whole snapshot.
    """
    try:
        raw = json.loads(payload) if payload else []
    except json.JSONDecodeError as exc:
        log.warning("runways Eval returned non-JSON payload (%s): %r", exc, payload[:120])
        return []
    if not isinstance(raw, list):
        log.warning("runways Eval returned non-list: %r", type(raw).__name__)
        return []
    out: list[Runway] = []
    for entry in raw:
        if not isinstance(entry, dict) or "lat" not in entry or "lon" not in entry:
            continue
        try:
            # Negate the raw course and normalize into [0, 2π). Python's % on a
            # positive divisor always yields a non-negative remainder.
            course = (-float(entry.get("course", 0.0))) % _TWO_PI
            out.append(
                Runway(
                    airbase_name=str(entry.get("airbase_name", "")),
                    name=_normalize_name(entry.get("name")),
                    lat=float(entry["lat"]),
                    lon=float(entry["lon"]),
                    course=course,
                    length_m=float(entry.get("length", 0.0)),
                    width_m=float(entry.get("width", 0.0)),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("skipping unparseable runway entry: %s", exc)
    return out
