"""Unit tests for F10 map marks."""

from __future__ import annotations

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.common.v0 import common_pb2
from dcs.mission.v0 import mission_pb2

from mizmap.marks import Mark, mark_from_event, mark_from_proto
from mizmap.state import MissionState


# --- mark_from_proto (snapshot via WorldService.GetMarkPanels) -------------

def _panel(**kwargs) -> common_pb2.MarkPanel:
    base = dict(
        id=1,
        time=10.0,
        position=common_pb2.Position(lat=43.0, lon=40.0, alt=0.0),
        text="hi",
    )
    base.update(kwargs)
    return common_pb2.MarkPanel(**base)


def test_mark_panel_no_restrictions_yields_both_none():
    # Mimics rust-server's "no group, no coalition" emission: group_id
    # explicitly set to UINT32_MAX, coalition unset.
    p = _panel(group_id=0xFFFFFFFF)
    m = mark_from_proto(p)
    assert m.coalition is None
    assert m.group_id is None
    assert m.text == "hi"
    assert m.id == 1


def test_mark_panel_coalition_only():
    p = _panel(coalition=common_pb2.COALITION_BLUE, group_id=0xFFFFFFFF)
    m = mark_from_proto(p)
    assert m.coalition == int(common_pb2.COALITION_BLUE)
    assert m.group_id is None


def test_mark_panel_group_only():
    p = _panel(group_id=201)
    m = mark_from_proto(p)
    assert m.coalition is None
    assert m.group_id == 201


def test_mark_panel_empty_text_is_preserved():
    # Player-added marks observed in the wild with text="" (label cleared
    # but the mark still exists on the F10 map).
    p = _panel(group_id=0xFFFFFFFF, text="")
    m = mark_from_proto(p)
    assert m.text == ""


def test_mark_to_dict_roundtrip_shape():
    p = _panel(group_id=0xFFFFFFFF)
    d = mark_from_proto(p).to_dict()
    assert set(d) == {"id", "lat", "lon", "alt", "text", "coalition", "group_id", "time"}


# --- mark_from_event (StreamEvents) ---------------------------------------

def test_mark_event_visibility_oneof_group():
    ev = mission_pb2.StreamEventsResponse.MarkAddEvent(
        id=42,
        group_id=201,
        position=common_pb2.Position(lat=1.0, lon=2.0, alt=3.0),
        text="ELINT",
    )
    m = mark_from_event(ev)
    assert m.id == 42
    assert m.group_id == 201
    assert m.coalition is None


def test_mark_event_visibility_oneof_coalition():
    ev = mission_pb2.StreamEventsResponse.MarkAddEvent(
        id=42,
        coalition=common_pb2.COALITION_RED,
        position=common_pb2.Position(lat=1.0, lon=2.0, alt=3.0),
        text="bandit",
    )
    m = mark_from_event(ev)
    assert m.group_id is None
    assert m.coalition == int(common_pb2.COALITION_RED)


# --- MissionState upsert / remove ----------------------------------------

def _mark(uid: int = 1, **kwargs) -> Mark:
    base = dict(
        id=uid, lat=43.0, lon=40.0, alt=0.0, text=f"m{uid}",
        coalition=None, group_id=None, time=0.0,
    )
    base.update(kwargs)
    return Mark(**base)


def test_state_marks_snapshot_message_shape():
    s = MissionState()
    s.set_marks([_mark(1), _mark(2, coalition=2)])
    msg = s.marks_message()
    assert msg["type"] == "marks_snapshot"
    assert len(msg["marks"]) == 2
    ids = {m["id"] for m in msg["marks"]}
    assert ids == {1, 2}


def test_state_upsert_and_remove_mark():
    s = MissionState()
    s.upsert_mark(_mark(1, text="first"))
    assert s.marks[1].text == "first"
    s.upsert_mark(_mark(1, text="updated"))
    assert s.marks[1].text == "updated"
    removed = s.remove_mark(1)
    assert removed is not None
    assert 1 not in s.marks
    assert s.remove_mark(1) is None  # idempotent


def test_state_clear_marks_returns_count():
    s = MissionState()
    s.set_marks([_mark(1), _mark(2), _mark(3)])
    assert s.clear_marks() == 3
    assert s.marks == {}
