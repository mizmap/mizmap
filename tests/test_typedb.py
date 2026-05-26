"""Tests for mizmap.typedb — schema validation + lookup."""

from __future__ import annotations

from pathlib import Path

import pytest

from mizmap.typedb import _load, _validate_entry, lookup, size


def test_typedb_loaded_with_real_entries():
    # The shipped units.yaml should have at least a few dozen entries.
    assert size() >= 30


def test_known_air_lookup_matches_yaml():
    # F/A-18 Hornet — strike fighter, no threat ring.
    entry = lookup("FA-18C_hornet")
    assert entry is not None
    assert entry.sidc == "AMFA---"
    assert entry.threat_km is None


def test_known_sam_lookup_has_threat():
    # S-300PS TEL — SAM long-range, ~75 km. Equipment-family code EWMAL is
    # what milsymbol actually recognises (UCDSA falls back to a "?" glyph).
    entry = lookup("S-300PS 40B6M tr")
    assert entry is not None
    assert entry.sidc == "GEWMAL-"
    assert entry.threat_km == 75


def test_unknown_type_returns_none():
    assert lookup("ThisUnitDoesNotExist") is None
    assert lookup(None) is None
    assert lookup("") is None


def test_validate_entry_accepts_minimal():
    e = _validate_entry("X", {"sidc": "GUCAAM-"})
    assert e.sidc == "GUCAAM-"
    assert e.threat_km is None


def test_validate_entry_accepts_full():
    e = _validate_entry("X", {"sidc": "GUCDSA-", "threat_km": 75})
    assert e.threat_km == 75.0


def test_validate_entry_rejects_short_sidc():
    with pytest.raises(ValueError, match="7-char"):
        _validate_entry("X", {"sidc": "GUC"})


def test_validate_entry_rejects_bad_dimension():
    with pytest.raises(ValueError, match="dimension"):
        _validate_entry("X", {"sidc": "ZEWMAL-"})  # Z is not a valid dimension


def test_validate_entry_rejects_unknown_field():
    with pytest.raises(ValueError, match="unknown fields"):
        _validate_entry("X", {"sidc": "GUCAAM-", "category": "tank"})


def test_validate_entry_rejects_negative_threat():
    with pytest.raises(ValueError, match="positive"):
        _validate_entry("X", {"sidc": "GUCDSA-", "threat_km": -5})


def test_load_returns_empty_on_missing_file(tmp_path):
    missing = tmp_path / "nope.yaml"
    out = _load(missing)
    assert out == {}


def test_load_rejects_bad_top_level(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- just a list", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level YAML must be a mapping"):
        _load(bad)


def test_lookup_is_case_insensitive():
    # ZiL-131 APA-80 is stored with a lowercase i in units.yaml; DCS reports
    # it that way. Looking it up with any other casing must still find it.
    canonical = lookup("ZiL-131 APA-80")
    assert canonical is not None
    assert lookup("ZIL-131 APA-80") == canonical
    assert lookup("zil-131 apa-80") == canonical
    assert lookup("zIl-131 ApA-80") == canonical


def test_load_rejects_case_insensitive_key_collision(tmp_path):
    bad = tmp_path / "collide.yaml"
    bad.write_text(
        "units:\n"
        "  \"Foo Bar\": { sidc: \"GUCAAM-\" }\n"
        "  \"foo bar\": { sidc: \"GUCAAM-\" }\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="case-insensitive"):
        _load(bad)
