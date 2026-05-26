"""DCS unit → MIL-STD-2525C SIDC (Symbol Identification Code).

Two-stage mapping:
  1. If `mizmap/data/units.yaml` (via mizmap.typedb) has an entry for the DCS type
     string, use its 7-char `sidc` (dim + 6-char function) as the type-specific
     override. The runtime affiliation (from coalition) and status are still
     applied.
  2. Otherwise fall back to a coarse (coalition, group_category) mapping —
     this is the Phase 1 baseline and still covers everything the typedb
     doesn't.

SIDC format (15 chars, 2525C):
  pos 0 : coding scheme    (S = warfighting)
  pos 1 : affiliation      (F=friend, H=hostile, N=neutral, U=unknown)
  pos 2 : battle dimension (A=air, G=ground, S=sea-surface)
  pos 3 : status           (P=present)
  pos 4-9 : function ID    (6 chars)
  pos 10-14: modifiers / padding (use '-')

Reference: milsymbol consumes this format directly.
"""

from __future__ import annotations

from mizmap.typedb import lookup as _typedb_lookup

# DCS Coalition enum values (from common.proto)
COALITION_ALL = 0
COALITION_NEUTRAL = 1
COALITION_RED = 2
COALITION_BLUE = 3

# DCS GroupCategory enum values (from common.proto)
GROUP_CATEGORY_UNSPECIFIED = 0
GROUP_CATEGORY_AIRPLANE = 1
GROUP_CATEGORY_HELICOPTER = 2
GROUP_CATEGORY_GROUND = 3
GROUP_CATEGORY_SHIP = 4
GROUP_CATEGORY_TRAIN = 5


def _affiliation(coalition: int) -> str:
    if coalition == COALITION_BLUE:
        return "F"
    if coalition == COALITION_RED:
        return "H"
    if coalition == COALITION_NEUTRAL:
        return "N"
    return "U"


def _dimension_and_function(category: int) -> tuple[str, str]:
    """Return (battle_dimension, 6-char function id)."""
    if category == GROUP_CATEGORY_AIRPLANE:
        # Air → fixed-wing military fighter (generic for now).
        return "A", "MF----"
    if category == GROUP_CATEGORY_HELICOPTER:
        # Air → rotary-wing.
        return "A", "MH----"
    if category == GROUP_CATEGORY_GROUND:
        # Ground → equipment / combat unit (generic).
        return "G", "U-----"
    if category == GROUP_CATEGORY_SHIP:
        # Sea surface → combatant (generic).
        return "S", "C-----"
    if category == GROUP_CATEGORY_TRAIN:
        # Ground → equipment.
        return "G", "E-----"
    # Unknown category → generic ground.
    return "G", "------"


def sidc_for(coalition: int, group_category: int, unit_type: str | None = None) -> str:
    """Compute a 15-character MIL-STD-2525C SIDC.

    When `unit_type` matches a `mizmap/data/units.yaml` entry, its 7-char `sidc`
    overrides the dimension + function code. Affiliation always comes from the
    coalition; status is always Present.
    """
    affiliation = _affiliation(coalition)
    override = _typedb_lookup(unit_type)
    if override is not None:
        dimension = override.sidc[0]
        function = override.sidc[1:]
    else:
        dimension, function = _dimension_and_function(group_category)
    status = "P"  # Present
    # 15 chars total: S + F + A + P + 6 fn + 5 modifier
    sidc = f"S{affiliation}{dimension}{status}{function}-----"
    assert len(sidc) == 15, f"SIDC must be 15 chars, got {len(sidc)}: {sidc!r}"
    return sidc


def threat_km_for(unit_type: str | None) -> float | None:
    """Return the typedb-declared max engagement range in km, or None."""
    entry = _typedb_lookup(unit_type)
    return entry.threat_km if entry is not None else None
