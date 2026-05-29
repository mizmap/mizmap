"""Fog-of-war detection picture (sensor-based visibility per coalition).

DCS's F10 "Fog of War" map mode shows a coalition its own units always, plus
enemy/neutral units only where that coalition's sensors have *detected* them.
DCS exposes no single "coalition fog-of-war contact set" RPC; the building
block is the per-unit-controller `Controller.getDetectedTargets()`
(https://wiki.hoggitworld.com/view/DCS_func_getDetectedTargets). We reconstruct
each coalition's picture by unioning that call across every unit on the
coalition, server-side in one `CustomService.Eval` — same escape hatch (and
same `evalEnabled = true` gate) as `mizmap/routes.py`.

Per detected target DCS reports three booleans — `visible` (currently sensed),
`type` (classification known), `distance` (range known) — but NOT which sensor
produced the contact (the detection-method enum is an *input* filter, not part
of the return), so we don't try to surface sensor type. The frontend joins each
contact `id` against the live `StreamUnits` units it already holds (so we only
ship the detected ids + flags, not positions) and applies the actual
show/degrade/ghost rendering, with the viewpoint coalition chosen client-side.

Coalition numbering note: the DCS *runtime* `coalition.side` enum is
0=neutral / 1=red / 2=blue, but the rest of MizMap (StreamUnits, SIDC, routes)
uses the gRPC `Coalition` enum 1=neutral / 2=red / 3=blue. The Lua maps
`coalition.side` → the gRPC enum (+1) so the observer keys here line up with
each unit's `coalition` field everywhere else.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class FogContact:
    """One detected target, as known to a coalition's sensors (unioned)."""

    id: int  # DCS runtime object id — joins against a StreamUnits unit id
    visible: bool  # currently sensed (vs. inferred/stale within the engine)
    type_known: bool  # classification resolved (else render as unknown-type)
    distance_known: bool  # range resolved (else position is uncertain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "visible": self.visible,
            "type_known": self.type_known,
            "distance_known": self.distance_known,
        }


# Walk each coalition's units, union getDetectedTargets() into a per-observer
# set of detected target ids + OR'd knowledge flags, and return
# { by_coalition = { "1"|"2"|"3" = [ {id, visible, type_known, distance_known}, ... ] } }.
# Defensive throughout: pcall around every engine call so a single odd
# unit/contact can't blank the whole snapshot, and string keys so the result
# always serialises as a JSON object (not an array) even when a side is empty.
FOG_LUA_SNIPPET = r"""
local result = { by_coalition = {} }
-- coalition.side (runtime) -> MizMap/gRPC Coalition enum (+1).
local sides = { [0] = 1, [1] = 2, [2] = 3 }
for side, miz_coal in pairs(sides) do
  local detected = {}
  local ok_groups, groups = pcall(coalition.getGroups, side)
  if ok_groups and groups then
    for _, grp in pairs(groups) do
      local ok_units, units = pcall(function() return grp:getUnits() end)
      if ok_units and units then
        for _, unit in pairs(units) do
          local ok_ctrl, ctrl = pcall(function() return unit:getController() end)
          if ok_ctrl and ctrl then
            local ok_tgts, tgts = pcall(function() return ctrl:getDetectedTargets() end)
            if ok_tgts and tgts then
              for _, t in pairs(tgts) do
                local obj = t.object
                if obj then
                  local ok_id, id = pcall(function() return obj:getID() end)
                  id = tonumber(id)
                  if ok_id and id then
                    local rec = detected[id]
                    if not rec then
                      rec = { visible = false, type_known = false, distance_known = false }
                      detected[id] = rec
                    end
                    if t.visible == true then rec.visible = true end
                    if t.type == true then rec.type_known = true end
                    if t.distance == true then rec.distance_known = true end
                  end
                end
              end
            end
          end
        end
      end
    end
  end
  local arr = {}
  for id, rec in pairs(detected) do
    arr[#arr + 1] = {
      id = id,
      visible = rec.visible,
      type_known = rec.type_known,
      distance_known = rec.distance_known,
    }
  end
  result.by_coalition[tostring(miz_coal)] = arr
end
return result
"""


def parse_fog_json(payload: str) -> dict[int, list[FogContact]]:
    """Parse the Eval JSON into {observer_coalition: [FogContact, ...]}.

    Tolerant of missing/extra fields and of an empty `by_coalition` table
    serialising as a JSON list rather than an object: anything unparseable is
    skipped with a warning, so one malformed contact never tanks the snapshot.
    """
    try:
        raw = json.loads(payload) if payload else {}
    except json.JSONDecodeError as exc:
        log.warning("fog Eval returned non-JSON payload (%s): %r", exc, payload[:120])
        return {}
    if not isinstance(raw, dict):
        # An all-empty Lua result can serialise as `[]`; treat as "no contacts".
        return {}
    by_coalition = raw.get("by_coalition")
    if not isinstance(by_coalition, dict):
        return {}
    out: dict[int, list[FogContact]] = {}
    for coal_key, contacts in by_coalition.items():
        try:
            coalition = int(coal_key)
        except (TypeError, ValueError):
            continue
        if not isinstance(contacts, list):
            continue
        parsed: list[FogContact] = []
        for c in contacts:
            if not isinstance(c, dict) or "id" not in c:
                continue
            try:
                parsed.append(
                    FogContact(
                        id=int(c["id"]),
                        visible=bool(c.get("visible", False)),
                        type_known=bool(c.get("type_known", False)),
                        distance_known=bool(c.get("distance_known", False)),
                    )
                )
            except (TypeError, ValueError) as exc:
                log.warning("skipping unparseable fog contact: %s", exc)
        out[coalition] = parsed
    return out
