"""Unit tests for MissionState and SIDC mapper."""

from __future__ import annotations

import math

import pytest

from mizmap.sidc import (
    COALITION_BLUE,
    COALITION_NEUTRAL,
    COALITION_RED,
    GROUP_CATEGORY_AIRPLANE,
    GROUP_CATEGORY_GROUND,
    GROUP_CATEGORY_HELICOPTER,
    GROUP_CATEGORY_SHIP,
    sidc_for,
)
from mizmap.state import MissionState, Unit, unit_to_dict


def make_unit(uid: int = 1, **kwargs) -> Unit:
    base = dict(
        id=uid,
        name=f"unit-{uid}",
        callsign=f"CALL-{uid}",
        type="FA-18C_hornet",
        coalition=COALITION_BLUE,
        group_id=10,
        group_name="GroupA",
        group_category=GROUP_CATEGORY_AIRPLANE,
        lat=43.0,
        lon=40.0,
        alt=1000.0,
        heading=0.0,
        speed=200.0,
        track=0.0,
        vs=0.0,
    )
    base.update(kwargs)
    return Unit(**base)


def test_sidc_affiliation_blue_airplane():
    sidc = sidc_for(COALITION_BLUE, GROUP_CATEGORY_AIRPLANE)
    assert sidc.startswith("SFAP"), sidc
    assert len(sidc) == 15


def test_sidc_affiliation_red_ground():
    sidc = sidc_for(COALITION_RED, GROUP_CATEGORY_GROUND)
    assert sidc.startswith("SHGP"), sidc


def test_sidc_neutral_ship():
    sidc = sidc_for(COALITION_NEUTRAL, GROUP_CATEGORY_SHIP)
    assert sidc.startswith("SNSP"), sidc


def test_sidc_unknown_coalition_becomes_unknown():
    sidc = sidc_for(coalition=999, group_category=GROUP_CATEGORY_AIRPLANE)
    assert sidc.startswith("SUAP"), sidc


def test_sidc_helicopter_air_dimension():
    sidc = sidc_for(COALITION_BLUE, GROUP_CATEGORY_HELICOPTER)
    # Air dimension (3rd char), helicopter function code MH
    assert sidc[2] == "A"
    assert "MH" in sidc[4:10]


def test_mission_state_upsert_returns_is_new():
    s = MissionState()
    _, is_new = s.upsert(make_unit(1))
    assert is_new is True
    _, is_new2 = s.upsert(make_unit(1, callsign="CHANGED"))
    assert is_new2 is False
    assert s.units[1].callsign == "CHANGED"


def test_mission_state_remove():
    s = MissionState()
    s.upsert(make_unit(1))
    s.upsert(make_unit(2))
    removed = s.remove(1)
    assert removed is not None and removed.id == 1
    assert 1 not in s.units
    assert 2 in s.units
    # idempotent
    assert s.remove(1) is None


def test_mission_state_clear():
    s = MissionState()
    s.upsert(make_unit(1))
    s.upsert(make_unit(2))
    assert s.clear() == 2
    assert s.units == {}


def test_mission_state_snapshot_message_shape():
    s = MissionState()
    s.upsert(make_unit(1, coalition=COALITION_BLUE, group_category=GROUP_CATEGORY_AIRPLANE))
    msg = s.snapshot_message()
    assert msg["type"] == "units_snapshot"
    assert len(msg["units"]) == 1
    u = msg["units"][0]
    assert u["id"] == 1
    assert u["sidc"].startswith("SFAP")
    assert u["group"]["category"] == GROUP_CATEGORY_AIRPLANE


def test_unit_to_dict_includes_sidc():
    # Use a type NOT in typedb so the coarse coalition×category mapping kicks in.
    u = make_unit(
        type="UnknownGroundUnit",
        coalition=COALITION_RED,
        group_category=GROUP_CATEGORY_GROUND,
    )
    d = unit_to_dict(u)
    assert d["sidc"].startswith("SHGP"), d["sidc"]
    assert d["coalition"] == COALITION_RED
    assert d["group"]["category"] == GROUP_CATEGORY_GROUND


# --- heading normalization (DCS-gRPC 0.8.1 emits unbounded accumulated yaw) ---

@pytest.mark.parametrize(
    "raw,expected",
    [
        (0.0, 0.0),
        (math.pi, math.pi),
        # Real-world samples from the 2026-05-25 Windows smoke test
        (76.24, 76.24 % (2 * math.pi)),
        (187.85, 187.85 % (2 * math.pi)),
        # Negative input should still land in [0, 2π)
        (-0.5, (2 * math.pi) - 0.5),
        # 2π exactly wraps to 0
        (2 * math.pi, 0.0),
    ],
)
def test_unit_normalizes_heading(raw, expected):
    u = make_unit(heading=raw)
    assert u.heading == pytest.approx(expected, abs=1e-9)
    assert 0.0 <= u.heading < 2 * math.pi


def test_unit_normalizes_track_same_as_heading():
    # track has the same DCS-gRPC quirk (unbounded accumulated angle) and
    # uses the same normalization in __post_init__.
    u = make_unit(track=187.85)
    assert u.track == pytest.approx(187.85 % (2 * math.pi), abs=1e-9)
    assert 0.0 <= u.track < 2 * math.pi


def test_unit_to_dict_carries_track():
    u = make_unit(track=1.234)
    d = unit_to_dict(u)
    assert d["track"] == pytest.approx(1.234, abs=1e-9)


# --- player_name pass-through (telemetry HUD relies on this surviving) ---

@pytest.mark.parametrize("name", [None, "", "Maverick"])
def test_unit_to_dict_carries_player_name(name):
    u = make_unit(player_name=name)
    d = unit_to_dict(u)
    assert d["player_name"] == name


# --- typedb-driven SIDC refinement + threat_km ---

def test_sidc_refined_from_typedb_for_known_type():
    sidc = sidc_for(
        coalition=COALITION_RED,
        group_category=GROUP_CATEGORY_GROUND,
        unit_type="S-300PS 40B6M tr",
    )
    # SHGPEWMAL------ : hostile, ground, present, EWMAL (equipment / SAM
    # launcher / long-range) + 5 dashes
    assert sidc == "SHGPEWMAL------"


def test_sidc_falls_back_to_coarse_for_unknown_type():
    sidc = sidc_for(
        coalition=COALITION_BLUE,
        group_category=GROUP_CATEGORY_AIRPLANE,
        unit_type="SomeFutureJet",
    )
    # Coarse: SFAPMF--------- (blue, air, fighter generic)
    assert sidc.startswith("SFAP")
    assert "MF" in sidc[4:10]


def test_unit_to_dict_carries_threat_km_for_sam():
    u = make_unit(type="S-300PS 40B6M tr", coalition=COALITION_RED,
                  group_category=GROUP_CATEGORY_GROUND)
    d = unit_to_dict(u)
    assert d["threat_km"] == 75
    assert d["sidc"] == "SHGPEWMAL------"


def test_unit_to_dict_threat_km_none_when_no_entry():
    u = make_unit(type="FA-18C_hornet")
    d = unit_to_dict(u)
    assert d["threat_km"] is None
    # F/A-18 also gets a refined SIDC even without threat_km
    assert d["sidc"] == "SFAPMFA--------"


# --- bullseyes ---

def test_bullseyes_message_shape():
    from mizmap.bullseye import Bullseye

    s = MissionState()
    s.set_bullseyes(
        [
            Bullseye(coalition=COALITION_BLUE, lat=34.0, lon=62.0, alt=1500.0),
            Bullseye(coalition=COALITION_RED, lat=35.5, lon=63.5, alt=2200.0),
        ]
    )
    msg = s.bullseyes_message()
    assert msg["type"] == "bullseyes_snapshot"
    assert len(msg["bullseyes"]) == 2
    assert msg["bullseyes"][0]["coalition"] == COALITION_BLUE
    assert msg["bullseyes"][0]["lat"] == 34.0
    assert s.clear_bullseyes() == 2
    assert s.bullseyes == []
