"""F10 map marks (a.k.a. mark panels).

DCS exposes user-placed and mission-scripted markers on the F10 map. Each
mark has a position, a label, and a visibility scope: visible to everyone,
restricted to one coalition, or restricted to one group. Players see only
those marks whose scope includes them.

DCS-gRPC 0.8.1 surfaces them via:
  - WorldService.GetMarkPanels — one-shot snapshot.
  - MissionService.StreamEvents — MarkAddEvent / MarkChangeEvent /
    MarkRemoveEvent for live updates.

The rust-server emits `0xFFFFFFFF` (UINT32_MAX) in `group_id` when a mark
has no group restriction, instead of leaving the optional field unset.
Normalize that sentinel to None at parse time so downstream code can use
the natural "is None" idiom.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# UINT32_MAX, sentinel for "no group restriction" in MarkPanel.group_id.
# The rust-server always populates the field; we collapse the sentinel here.
_NO_GROUP_SENTINEL = 0xFFFFFFFF


@dataclass
class Mark:
    id: int
    lat: float
    lon: float
    alt: float
    text: str  # label as shown on the F10 map; may be empty
    coalition: int | None  # None = visible to all coalitions; 1=neutral, 2=red, 3=blue
    group_id: int | None  # None = no group restriction
    time: float  # seconds since mission start when the mark was created

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "text": self.text,
            "coalition": self.coalition,
            "group_id": self.group_id,
            "time": self.time,
        }


def mark_from_proto(p: Any) -> Mark:
    """Build a Mark from a `common_pb2.MarkPanel` proto.

    Handles the two quirks of the rust-server's emission:
      - `group_id` is always set; the sentinel UINT32_MAX means "no group".
      - `coalition` is left unset when there's no coalition restriction.
    """
    pos = p.position
    coalition: int | None = int(p.coalition) if p.HasField("coalition") else None
    raw_group = p.group_id if p.HasField("group_id") else None
    group_id: int | None = None if raw_group in (None, _NO_GROUP_SENTINEL) else int(raw_group)
    text = p.text if p.HasField("text") else ""
    return Mark(
        id=int(p.id),
        lat=float(pos.lat),
        lon=float(pos.lon),
        alt=float(pos.alt),
        text=text,
        coalition=coalition,
        group_id=group_id,
        time=float(p.time),
    )


def mark_from_event(ev: Any) -> Mark:
    """Build a Mark from a MarkAddEvent / MarkChangeEvent / MarkRemoveEvent.

    These events use a `visibility` oneof (group_id XOR coalition) instead of
    the two-field layout of MarkPanel. `time` and `alt` aren't on the event,
    so they default to 0.
    """
    pos = ev.position
    which = ev.WhichOneof("visibility")
    coalition: int | None = int(ev.coalition) if which == "coalition" else None
    group_id: int | None = int(ev.group_id) if which == "group_id" else None
    return Mark(
        id=int(ev.id),
        lat=float(pos.lat),
        lon=float(pos.lon),
        alt=float(pos.alt),
        text=ev.text or "",
        coalition=coalition,
        group_id=group_id,
        time=0.0,
    )
