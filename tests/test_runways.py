"""Unit tests for runway parsing (Airbase:getRunways via Eval)."""

from __future__ import annotations

import json
import math

from mizmap.runways import Runway, parse_runways_json
from mizmap.state import MissionState


def _payload(entries) -> str:
    return json.dumps(entries)


def _entry(**kw) -> dict:
    base = dict(
        airbase_name="Herat", name=18, course=0.0, length=2700, width=60,
        lat=34.2, lon=62.2,
    )
    base.update(kw)
    return base


# --- course sign + normalization -------------------------------------------

def test_course_is_negated_and_normalized():
    # Real DCS gives a +0.5183 rad course for a 330° runway (Farah); negating
    # is what makes it a compass bearing. radians(30) negated → 330°.
    rws = parse_runways_json(_payload([_entry(course=math.radians(30))]))
    assert len(rws) == 1
    assert math.isclose(rws[0].course, math.radians(330), abs_tol=1e-9)


def test_negative_raw_course_negates_to_positive():
    # The mock emits course=-radians(60); negated → 60°.
    rws = parse_runways_json(_payload([_entry(course=-math.radians(60))]))
    assert math.isclose(rws[0].course, math.radians(60), abs_tol=1e-9)


def test_course_always_in_unit_circle():
    for deg in (0, 60, 180, 330, 359):
        rws = parse_runways_json(_payload([_entry(course=math.radians(deg))]))
        assert 0.0 <= rws[0].course < 2 * math.pi


# --- Name normalization -----------------------------------------------------

def test_int_name_zero_padded():
    assert parse_runways_json(_payload([_entry(name=6)]))[0].name == "06"
    assert parse_runways_json(_payload([_entry(name=18)]))[0].name == "18"
    assert parse_runways_json(_payload([_entry(name=33)]))[0].name == "33"


def test_float_name_normalized():
    assert parse_runways_json(_payload([_entry(name=33.0)]))[0].name == "33"


def test_string_name_passthrough():
    assert parse_runways_json(_payload([_entry(name="06L")]))[0].name == "06L"


# --- field mapping + to_dict ------------------------------------------------

def test_field_mapping_and_to_dict_shape():
    rws = parse_runways_json(_payload([_entry(length=2718, width=60, lat=34.21, lon=62.23)]))
    rw = rws[0]
    assert rw.airbase_name == "Herat"
    assert rw.length_m == 2718.0
    assert rw.width_m == 60.0
    assert rw.lat == 34.21 and rw.lon == 62.23
    d = rw.to_dict()
    assert set(d) == {"airbase_name", "name", "lat", "lon", "course", "length_m", "width_m"}


# --- tolerant parsing -------------------------------------------------------

def test_entry_missing_latlon_skipped():
    payload = json.dumps([{"airbase_name": "X", "name": 1, "course": 0.0}])  # no lat/lon
    assert parse_runways_json(payload) == []


def test_non_dict_entries_skipped():
    payload = json.dumps([_entry(), "garbage", 42, None])
    assert len(parse_runways_json(payload)) == 1


def test_non_list_payload_yields_empty():
    assert parse_runways_json(json.dumps({"not": "a list"})) == []


def test_non_json_payload_yields_empty():
    assert parse_runways_json("not json at all") == []
    assert parse_runways_json("") == []


# --- MissionState -----------------------------------------------------------

def test_state_runways_snapshot_message_shape():
    s = MissionState()
    s.set_runways([
        Runway("Herat", "18", 34.2, 62.2, 0.0, 2700, 60),
        Runway("Farah", "33", 32.3, 62.1, 1.0, 2100, 45),
    ])
    msg = s.runways_message()
    assert msg["type"] == "runways_snapshot"
    assert len(msg["runways"]) == 2
    assert {r["airbase_name"] for r in msg["runways"]} == {"Herat", "Farah"}


def test_state_clear_runways_returns_count():
    s = MissionState()
    s.set_runways([Runway("A", "18", 1, 2, 0.0, 100, 10), Runway("B", "36", 3, 4, 0.0, 200, 20)])
    assert s.clear_runways() == 2
    assert s.runways == []
