"""Unit tests for fog-of-war detection parsing (getDetectedTargets via Eval)."""

from __future__ import annotations

import json

from mizmap.fog import FogContact, parse_fog_json
from mizmap.state import MissionState


def _payload(by_coalition) -> str:
    return json.dumps({"by_coalition": by_coalition})


def _contact(**kw) -> dict:
    base = dict(id=1, visible=True, type_known=True, distance_known=True)
    base.update(kw)
    return base


# --- happy path -------------------------------------------------------------

def test_parses_per_coalition_contacts():
    out = parse_fog_json(
        _payload(
            {
                "1": [],
                "2": [_contact(id=1, type_known=False, distance_known=False)],
                "3": [_contact(id=3)],
            }
        )
    )
    assert set(out) == {1, 2, 3}
    assert out[1] == []
    assert len(out[2]) == 1
    c = out[2][0]
    assert isinstance(c, FogContact)
    assert (c.id, c.visible, c.type_known, c.distance_known) == (1, True, False, False)
    assert out[3][0].id == 3


def test_flags_default_false_when_absent():
    # Lua may omit a false flag; the parser must default it, not crash.
    out = parse_fog_json(_payload({"2": [{"id": 7}]}))
    c = out[2][0]
    assert (c.visible, c.type_known, c.distance_known) == (False, False, False)


def test_to_dict_round_trips_shape():
    c = FogContact(id=5, visible=True, type_known=False, distance_known=True)
    assert c.to_dict() == {
        "id": 5,
        "visible": True,
        "type_known": False,
        "distance_known": True,
    }


# --- tolerance / degenerate payloads ----------------------------------------

def test_empty_string_is_empty():
    assert parse_fog_json("") == {}


def test_empty_table_serialised_as_list_is_tolerated():
    # An all-empty Lua result can serialise as `[]` rather than an object.
    assert parse_fog_json("[]") == {}


def test_missing_by_coalition_key_is_empty():
    assert parse_fog_json("{}") == {}


def test_non_json_is_empty():
    assert parse_fog_json("not json at all") == {}


def test_by_coalition_as_list_is_tolerated():
    # by_coalition itself empty-serialising as a list → no contacts, no crash.
    assert parse_fog_json(json.dumps({"by_coalition": []})) == {}


def test_malformed_contacts_skipped_not_fatal():
    out = parse_fog_json(
        _payload({"2": [{"nope": 1}, _contact(id=9), "garbage", 42]})
    )
    # Only the well-formed contact survives.
    assert [c.id for c in out[2]] == [9]


def test_non_numeric_coalition_key_skipped():
    out = parse_fog_json(_payload({"blue": [_contact(id=1)], "3": [_contact(id=2)]}))
    assert set(out) == {3}


def test_non_list_coalition_value_skipped():
    out = parse_fog_json(_payload({"2": {"id": 1}, "3": [_contact(id=2)]}))
    assert set(out) == {3}


# --- state integration ------------------------------------------------------

def test_state_set_and_message():
    ms = MissionState()
    assert ms.fog_message() == {"type": "fog_snapshot", "eval_ok": True, "by_coalition": {}}
    ms.set_fog({2: [FogContact(id=1, visible=True, type_known=True, distance_known=False)]})
    msg = ms.fog_message()
    assert msg["type"] == "fog_snapshot"
    assert msg["eval_ok"] is True
    assert msg["by_coalition"] == {
        "2": [{"id": 1, "visible": True, "type_known": True, "distance_known": False}]
    }


def test_state_eval_disabled_flag():
    ms = MissionState()
    ms.set_fog({}, eval_ok=False)
    assert ms.fog_message()["eval_ok"] is False
    # clear_fog resets the flag back to the optimistic default.
    ms.clear_fog()
    assert ms.fog_message()["eval_ok"] is True


def test_clear_fog_returns_count():
    ms = MissionState()
    ms.set_fog({2: [FogContact(1, True, True, True)], 3: []})
    assert ms.clear_fog() == 2
    assert ms.fog == {}
