"""Mission group routes (planned flight plans / waypoints).

DCS-gRPC 0.8.1 does not expose group routes directly. We use
`CustomService.Eval` (gated behind `evalEnabled = true` in
`Saved Games/DCS/Config/dcs-grpc.lua`) to walk the live `env.mission` table and
return each group's route with coordinates already converted to lat/lon via the
in-engine `coord.LOtoLL` helper. That avoids both an in-Python `.miz` Lua parser
and a hand-maintained per-theater Transverse Mercator projection table.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class RoutePoint:
    lat: float
    lon: float
    alt: float
    type: str  # e.g. "Turning Point", "TakeOff", "Land" — the raw .miz string
    action: str  # e.g. "Turning Point", "Fly Over Point" — the raw .miz string
    speed: float  # m/s (DCS stores this in m/s already)
    eta: float  # seconds from mission start
    name: str = ""  # optional waypoint name from the .miz; empty for most missions

    def to_dict(self) -> dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "type": self.type,
            "action": self.action,
            "speed": self.speed,
            "eta": self.eta,
            "name": self.name,
        }


@dataclass
class GroupRoute:
    group_id: int
    group_name: str
    coalition: int  # DCS Coalition enum: 1=neutral, 2=red, 3=blue
    category: int  # GroupCategory: 1=airplane, 2=helo, 3=ground, 4=ship, 5=train
    points: list[RoutePoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "coalition": self.coalition,
            "category": self.category,
            "points": [p.to_dict() for p in self.points],
        }


# Walk env.mission.coalition[*].country[*].{plane,helicopter,vehicle,ship,train}[*].group[*]
# and return route points with xy→lat/lon conversion done in-engine. Keys in
# env.mission.coalition are "blue" / "red" / "neutrals" (DCS lowercase plurals).
# In a Vec3 for coord.LOtoLL, x=N-S, y=alt, z=E-W; in a .miz route point,
# `x`/`y` are the 2D map coords and `alt` is altitude — note the y/z swap.
LUA_SNIPPET = r"""
local result = {}
if not env or not env.mission or not env.mission.coalition then
  return result
end
local coalitions = { neutrals = 1, red = 2, blue = 3 }
local categories = { plane = 1, helicopter = 2, vehicle = 3, ship = 4, train = 5 }
for coal_key, coal_enum in pairs(coalitions) do
  local coal_data = env.mission.coalition[coal_key]
  if coal_data and coal_data.country then
    for _, country in pairs(coal_data.country) do
      for cat_key, cat_enum in pairs(categories) do
        local cat_data = country[cat_key]
        if cat_data and cat_data.group then
          for _, group in pairs(cat_data.group) do
            local pts = {}
            if group.route and group.route.points then
              for _, pt in ipairs(group.route.points) do
                local lat, lon, alt = coord.LOtoLL({ x = pt.x, y = pt.alt or 0, z = pt.y })
                pts[#pts + 1] = {
                  lat = lat,
                  lon = lon,
                  alt = alt,
                  type = pt.type or "",
                  action = pt.action or "",
                  speed = pt.speed or 0,
                  eta = pt.ETA or 0,
                  name = pt.name or "",
                }
              end
            end
            result[#result + 1] = {
              group_id = group.groupId,
              group_name = group.name,
              coalition = coal_enum,
              category = cat_enum,
              points = pts,
            }
          end
        end
      end
    end
  end
end
return result
"""


def parse_eval_json(payload: str) -> list[GroupRoute]:
    """Parse the JSON string returned by CustomService.Eval into typed routes.

    Tolerant of missing/extra fields: anything unparseable is skipped with a
    warning, so a single malformed group never tanks the whole snapshot.
    """
    try:
        raw = json.loads(payload) if payload else []
    except json.JSONDecodeError as exc:
        log.warning("routes Eval returned non-JSON payload (%s): %r", exc, payload[:120])
        return []
    if not isinstance(raw, list):
        log.warning("routes Eval returned non-list: %r", type(raw).__name__)
        return []
    out: list[GroupRoute] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        try:
            pts = [
                RoutePoint(
                    lat=float(p["lat"]),
                    lon=float(p["lon"]),
                    alt=float(p.get("alt", 0.0)),
                    type=str(p.get("type", "")),
                    action=str(p.get("action", "")),
                    speed=float(p.get("speed", 0.0)),
                    eta=float(p.get("eta", 0.0)),
                    name=str(p.get("name", "")),
                )
                for p in entry.get("points", [])
                if isinstance(p, dict) and "lat" in p and "lon" in p
            ]
            out.append(
                GroupRoute(
                    group_id=int(entry.get("group_id", 0)),
                    group_name=str(entry.get("group_name", "")),
                    coalition=int(entry.get("coalition", 0)),
                    category=int(entry.get("category", 0)),
                    points=pts,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            log.warning("skipping unparseable route entry: %s", exc)
    return out
