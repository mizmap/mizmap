"""Unit tests for navaid parsing (terrain Beacons.lua)."""

from __future__ import annotations

from mizmap.navaids import (
    Navaid,
    find_beacons_file,
    load_navaids,
    parse_beacons_lua,
)
from mizmap.state import MissionState

# Mimics the real Beacons.lua: dofile/require/_() noise, BEACON_TYPE_* symbols,
# single-line nested tables, and a record with no positionGeo (must be skipped).
SNIPPET = """
dofile('Scripts/Database/wsTypes.lua')
local disableNauticalBeacons = true
local gettext = require("i_18n")
local _ = gettext.translate

beaconsTableFormat = 2
beacons = {
\t{
\t\tdisplay_name = _('Gilgit');
\t\tbeaconId = 'world_0';
\t\ttype = BEACON_TYPE_HOMER;
\t\tcallsign = 'GT';
\t\tfrequency = 324000.000000;
\t\tposition = { 275356.375000, 1501.198279, 724554.375000 };
\t\tdirection = 0.000000;
\t\tpositionGeo = { latitude = 35.920161, longitude = 74.335056 };
\t\tsceneObjects = {'t:198565888'};
\t};
\t{
\t\tdisplay_name = _('Dushanbe');
\t\ttype = BEACON_TYPE_VOR_DME;
\t\tcallsign = 'DNB';
\t\tfrequency = 113600000.000000;
\t\tchannel = 83;
\t\tpositionGeo = { latitude = 38.541666, longitude = 68.810835 };
\t};
\t{
\t\tdisplay_name = _('Mystery');
\t\ttype = BEACON_TYPE_SOMETHING_NEW;
\t\tcallsign = 'MYS';
\t\tpositionGeo = { latitude = 30.0, longitude = 60.0 };
\t};
\t{
\t\tdisplay_name = _('NoGeo');
\t\ttype = BEACON_TYPE_TACAN;
\t\tcallsign = 'XXX';
\t\tchannel = 76;
\t\tposition = { -498489.0, 1380.0, -503357.0 };
\t};
}
"""


def test_parse_skips_records_without_geo():
    navs = parse_beacons_lua(SNIPPET)
    # Gilgit, Dushanbe, Mystery have positionGeo; NoGeo does not.
    assert len(navs) == 3
    assert "XXX" not in {n.callsign for n in navs}


def test_parse_fields_and_type_mapping():
    by_cs = {n.callsign: n for n in parse_beacons_lua(SNIPPET)}
    gt = by_cs["GT"]
    assert gt.type == "NDB"  # BEACON_TYPE_HOMER
    assert gt.name == "Gilgit"
    assert gt.freq_hz == 324000.0
    assert gt.channel is None
    assert gt.band is None  # no channel → no band
    assert (round(gt.lat, 6), round(gt.lon, 6)) == (35.920161, 74.335056)

    dnb = by_cs["DNB"]
    assert dnb.type == "VOR/DME"
    assert dnb.channel == 83
    assert dnb.band == "X"  # 113.60 MHz → .x00 → X
    assert dnb.freq_hz == 113600000.0


def _one_record(*field_lines: str) -> str:
    body = "".join(f"\t\t{ln}\n" for ln in field_lines)
    return f"beacons = {{\n\t{{\n{body}\t}};\n}}\n"


def test_tacan_band_defaults_to_x_without_frequency():
    # Channel-only military TACAN (no paired VHF freq), e.g. Kandahar 75X.
    txt = _one_record(
        "display_name = _('Kandahar');",
        "type = BEACON_TYPE_TACAN;",
        "callsign = 'KAF';",
        "channel = 75;",
        "positionGeo = { latitude = 31.5, longitude = 65.8 };",
    )
    n = parse_beacons_lua(txt)[0]
    assert (n.channel, n.band) == (75, "X")


def test_tacan_band_derived_y_from_paired_frequency():
    # 116.25 MHz → .x50 step → Y band.
    txt = _one_record(
        "display_name = _('Yband');",
        "type = BEACON_TYPE_VORTAC;",
        "callsign = 'YBN';",
        "frequency = 116250000.000000;",
        "channel = 109;",
        "positionGeo = { latitude = 31.0, longitude = 61.0 };",
    )
    n = parse_beacons_lua(txt)[0]
    assert n.band == "Y"


def test_unknown_type_falls_back_to_readable_label():
    mys = {n.callsign: n for n in parse_beacons_lua(SNIPPET)}["MYS"]
    assert mys.type == "Something New"


def test_to_dict_shape():
    d = parse_beacons_lua(SNIPPET)[0].to_dict()
    assert set(d) == {"name", "type", "callsign", "lat", "lon", "freq_hz", "channel", "band"}


def test_parse_empty_or_garbage():
    assert parse_beacons_lua("") == []
    assert parse_beacons_lua("nothing to see here") == []


# --- find_beacons_file / load_navaids --------------------------------------

def _make_terrain(tmp_path, folder: str, filename: str = "Beacons.lua") -> "object":
    d = tmp_path / "Mods" / "terrains" / folder
    d.mkdir(parents=True)
    (d / filename).write_text(SNIPPET, encoding="utf-8")
    return d / filename


def test_find_beacons_file_exact(tmp_path):
    expected = _make_terrain(tmp_path, "Caucasus")
    assert find_beacons_file(tmp_path, "Caucasus") == expected


def test_find_beacons_file_space_and_case_insensitive(tmp_path):
    expected = _make_terrain(tmp_path, "MarianaIslands", filename="beacons.lua")
    assert find_beacons_file(tmp_path, "Mariana Islands") == expected


def test_find_beacons_file_missing(tmp_path):
    _make_terrain(tmp_path, "Caucasus")
    assert find_beacons_file(tmp_path, "Nevada") is None
    assert find_beacons_file(None, "Caucasus") is None
    assert find_beacons_file(tmp_path / "nope", "Caucasus") is None


def test_load_navaids(tmp_path):
    _make_terrain(tmp_path, "Caucasus")
    navs = load_navaids(tmp_path, "Caucasus")
    assert navs is not None
    assert len(navs) == 3
    # Missing file → None (caller distinguishes from an empty parse).
    assert load_navaids(tmp_path, "Syria") is None


# --- MissionState ----------------------------------------------------------

def test_state_navaids_message_and_clear():
    s = MissionState()
    s.set_navaids([
        Navaid("Gilgit", "NDB", "GT", 35.9, 74.3, 324000.0, None),
        Navaid("Dushanbe", "VOR/DME", "DNB", 38.5, 68.8, 113600000.0, 83),
    ])
    msg = s.navaids_message()
    assert msg["type"] == "navaids_snapshot"
    assert len(msg["navaids"]) == 2
    assert s.clear_navaids() == 2
    assert s.navaids == []
