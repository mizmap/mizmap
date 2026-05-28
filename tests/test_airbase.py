"""Unit tests for airbases (WorldService.GetAirbases)."""

from __future__ import annotations

import mizmap.proto_gen  # noqa: F401  -- sets sys.path for generated imports
from dcs.common.v0 import common_pb2

from mizmap.airbase import Airbase, airbase_from_proto
from mizmap.sidc import airbase_sidc_for
from mizmap.state import MissionState

# --- airbase_from_proto -----------------------------------------------------

def _proto(**kwargs) -> common_pb2.Airbase:
    base = dict(
        name="Sochi-Adler",
        callsign="Sochi",
        coalition=common_pb2.COALITION_BLUE,
        category=common_pb2.AIRBASE_CATEGORY_AIRDROME,
        display_name="Sochi-Adler",
        position=common_pb2.Position(lat=43.449, lon=39.956, alt=10.0),
    )
    base.update(kwargs)
    return common_pb2.Airbase(**base)


def test_airbase_from_proto_maps_all_fields():
    a = airbase_from_proto(_proto())
    assert a.name == "Sochi-Adler"
    assert a.callsign == "Sochi"
    assert a.display_name == "Sochi-Adler"
    assert a.coalition == int(common_pb2.COALITION_BLUE)
    assert a.category == int(common_pb2.AIRBASE_CATEGORY_AIRDROME)
    assert a.lat == 43.449
    assert a.lon == 39.956
    assert a.alt == 10.0


def test_airbase_from_proto_ignores_carrier_unit_field():
    # Carrier airbases carry a populated `unit`; we deliberately drop it
    # (the carrier is tracked via StreamUnits). Mapping must not choke on it.
    p = _proto(
        category=common_pb2.AIRBASE_CATEGORY_SHIP,
        unit=common_pb2.Unit(id=7, name="CVN", type="CVN_71"),
    )
    a = airbase_from_proto(p)
    assert a.category == int(common_pb2.AIRBASE_CATEGORY_SHIP)


def test_airbase_to_dict_shape_includes_sidc():
    d = airbase_from_proto(_proto()).to_dict()
    assert set(d) == {
        "name", "callsign", "display_name", "coalition",
        "category", "lat", "lon", "alt", "sidc",
    }
    assert len(d["sidc"]) == 15


# --- airbase_sidc_for -------------------------------------------------------

def test_sidc_airdrome_blue_is_friendly_airport():
    # Airdrome → airport function IBA---; BLUE → Friend affiliation.
    assert airbase_sidc_for(common_pb2.COALITION_BLUE, 1) == "SFGPIBA---H----"


def test_sidc_helipad_red_is_hostile_base():
    # Helipad (FARP/FOB) → generic base function IB----; RED → Hostile.
    assert airbase_sidc_for(common_pb2.COALITION_RED, 2) == "SHGPIB----H----"


def test_sidc_neutral_airdrome():
    assert airbase_sidc_for(common_pb2.COALITION_NEUTRAL, 1) == "SNGPIBA---H----"


def test_sidc_ship_falls_back_to_airport_symbol():
    # Ships aren't drawn by the frontend, but the SIDC must still be valid.
    assert airbase_sidc_for(common_pb2.COALITION_BLUE, 3) == "SFGPIBA---H----"


def test_sidc_always_15_chars_with_installation_modifier():
    for category in (1, 2, 3):
        for coalition in (0, 1, 2, 3):
            sidc = airbase_sidc_for(coalition, category)
            assert len(sidc) == 15
            assert sidc[10] == "H"  # installation modifier (position 11)


# --- MissionState -----------------------------------------------------------

def _airbase(name: str = "Sochi", **kwargs) -> Airbase:
    base = dict(
        name=name, callsign=name, display_name=name,
        coalition=3, category=1, lat=43.0, lon=40.0, alt=0.0,
    )
    base.update(kwargs)
    return Airbase(**base)


def test_state_airbases_snapshot_message_shape():
    s = MissionState()
    s.set_airbases([_airbase("A"), _airbase("B", category=2)])
    msg = s.airbases_message()
    assert msg["type"] == "airbases_snapshot"
    assert len(msg["airbases"]) == 2
    assert {a["name"] for a in msg["airbases"]} == {"A", "B"}


def test_state_clear_airbases_returns_count():
    s = MissionState()
    s.set_airbases([_airbase("A"), _airbase("B"), _airbase("C")])
    assert s.clear_airbases() == 3
    assert s.airbases == []
