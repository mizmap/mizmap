"""Per-DCS-type lookup table for refined SIDC symbology + SAM/AAA threat rings.

The YAML at `mizmap/data/units.yaml` is the authoritative source. This module
loads it once at import time, validates the schema strictly (bad entry → load
fails), and exposes `lookup(unit_type)` for the rest of the package.

Lookup is **case-insensitive**: DCS itself is inconsistent about capitalisation
(e.g. `ZiL-131 APA-80` with lowercase i, but `ZIL-131 KUNG` with uppercase),
and no real DCS unit type would intentionally differ from another only in
case. To enforce that assumption, the loader raises if two YAML keys fold to
the same lowercase form.

If the YAML file is missing entirely (e.g. running tests against an
incomplete checkout), the module logs a warning and falls back to an empty
table — `sidc_for(...)` then degrades to the coarse coalition×category
mapping that predated this phase.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent / "data" / "units.yaml"

# Valid characters per MIL-STD-2525C SIDC positions (subset we use).
_VALID_DIMENSIONS = frozenset("AGSFPUX")


@dataclass(frozen=True)
class TypeEntry:
    sidc: str  # 7 chars: 1 dim + 6 function. Validated at load time.
    threat_km: float | None = None


def _validate_entry(unit_type: str, raw: dict) -> TypeEntry:
    if not isinstance(raw, dict):
        raise ValueError(f"{unit_type!r}: entry must be a mapping, got {type(raw).__name__}")
    extra = set(raw) - {"sidc", "threat_km"}
    if extra:
        raise ValueError(f"{unit_type!r}: unknown fields {sorted(extra)}")
    sidc = raw.get("sidc")
    if not isinstance(sidc, str) or len(sidc) != 7:
        raise ValueError(f"{unit_type!r}: sidc must be a 7-char string, got {sidc!r}")
    if sidc[0] not in _VALID_DIMENSIONS:
        raise ValueError(
            f"{unit_type!r}: sidc dimension {sidc[0]!r} must be one of {sorted(_VALID_DIMENSIONS)}"
        )
    threat = raw.get("threat_km")
    if threat is not None:
        if not isinstance(threat, (int, float)) or threat <= 0:
            raise ValueError(f"{unit_type!r}: threat_km must be a positive number, got {threat!r}")
        threat = float(threat)
    return TypeEntry(sidc=sidc, threat_km=threat)


def _load(path: Path) -> dict[str, TypeEntry]:
    if not path.is_file():
        log.warning("typedb: %s not found — falling back to coarse mapping", path)
        return {}
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    units = raw.get("units", {})
    if not isinstance(units, dict):
        raise ValueError(f"{path}: 'units' must be a mapping, got {type(units).__name__}")
    out: dict[str, TypeEntry] = {}
    seen_originals: dict[str, str] = {}  # lower -> first original key seen
    for unit_type, entry in units.items():
        if not isinstance(unit_type, str):
            raise ValueError(f"unit type key must be a string, got {unit_type!r}")
        key = unit_type.lower()
        if key in seen_originals:
            raise ValueError(
                f"unit type key collision under case-insensitive match: "
                f"{seen_originals[key]!r} and {unit_type!r} both fold to {key!r}"
            )
        seen_originals[key] = unit_type
        out[key] = _validate_entry(unit_type, entry)
    log.info(
        "typedb: loaded %d entries (%d with threat_km)",
        len(out),
        sum(1 for e in out.values() if e.threat_km is not None),
    )
    return out


# Loaded once at import. Reload by restarting the process or calling _load()
# directly from a REPL.
_DB: dict[str, TypeEntry] = _load(_DATA_PATH)


def lookup(unit_type: str | None) -> TypeEntry | None:
    """Return the typedb entry for `unit_type`, or None if not present.

    Tolerant of None input so callers don't have to guard. Matching is
    case-insensitive — see module docstring.
    """
    if not unit_type:
        return None
    return _DB.get(unit_type.lower())


def size() -> int:
    """Number of entries currently loaded — convenience for diagnostics."""
    return len(_DB)
