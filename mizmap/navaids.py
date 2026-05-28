"""Navigation aids (NDB / VOR / DME / TACAN / …) from terrain Beacons.lua.

DCS-gRPC exposes no beacon RPC, but every terrain ships a `Beacons.lua` under
`<dcs_install>/Mods/terrains/<Theatre>/`. Crucially each beacon record carries a
`positionGeo = { latitude, longitude }`, so we get lat/lon **directly off disk** —
no Eval, no coordinate conversion. MizMap runs on the same box as DCS, so we read
the file for the loaded theatre (from `WorldService.GetTheatre`) and parse it.

The file isn't pure data — it `dofile`s other scripts, wraps names in `_('…')`
(i18n), and uses `type = BEACON_TYPE_TACAN` symbol constants. So rather than a Lua
interpreter, a tolerant line parser pulls the handful of fields we care about. The
record format (verified on Afghanistan + Caucasus) is regular: each beacon is a
`{ … };` block with one `key = value;` per line and nested tables (`position`,
`positionGeo`) kept on a single line.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# BEACON_TYPE_* symbol → friendly category string sent to the frontend (which
# maps it to a glyph). Unknown symbols fall back to a cleaned-up label.
_TYPE_MAP = {
    "BEACON_TYPE_HOMER": "NDB",
    "BEACON_TYPE_NDB": "NDB",
    "BEACON_TYPE_AIRPORT_HOMER": "NDB",
    "BEACON_TYPE_AIRPORT_HOMER_WITH_MARKER": "NDB",
    "BEACON_TYPE_ILS_FAR_HOMER": "ILS-OM",
    "BEACON_TYPE_ILS_NEAR_HOMER": "ILS-MM",
    "BEACON_TYPE_ILS_LOCALIZER": "ILS-LOC",
    "BEACON_TYPE_ILS_GLIDESLOPE": "ILS-GS",
    "BEACON_TYPE_VOR": "VOR",
    "BEACON_TYPE_VOR_DME": "VOR/DME",
    "BEACON_TYPE_DME": "DME",
    "BEACON_TYPE_TACAN": "TACAN",
    "BEACON_TYPE_VORTAC": "VORTAC",
    "BEACON_TYPE_RSBN": "RSBN",
    "BEACON_TYPE_PRMG": "PRMG",
    "BEACON_TYPE_PRMG_LOCALIZER": "PRMG-LOC",
    "BEACON_TYPE_PRMG_GLIDESLOPE": "PRMG-GS",
    "BEACON_TYPE_BROADCAST_STATION": "Broadcast",
}


def _friendly_type(symbol: str) -> str:
    if symbol in _TYPE_MAP:
        return _TYPE_MAP[symbol]
    # e.g. BEACON_TYPE_SOMETHING_NEW → "Something New"
    return symbol.removeprefix("BEACON_TYPE_").replace("_", " ").title() or "Beacon"


@dataclass
class Navaid:
    name: str
    type: str  # friendly category: NDB, VOR, VOR/DME, DME, TACAN, VORTAC, …
    callsign: str
    lat: float
    lon: float
    freq_hz: float | None  # carrier frequency in Hz (NDB ~ 3e5, VOR ~ 1e8); None if N/A
    channel: int | None  # TACAN/VOR channel; None if N/A
    band: str | None = None  # TACAN X/Y mode (e.g. "X" → channel "75X"); None if N/A

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "callsign": self.callsign,
            "lat": self.lat,
            "lon": self.lon,
            "freq_hz": self.freq_hz,
            "channel": self.channel,
            "band": self.band,
        }


def _tacan_band(freq_hz: float | None, channel: int | None) -> str | None:
    """TACAN/VORTAC X-or-Y band for a channel.

    Beacons.lua stores no explicit mode. When a paired VHF frequency is present
    (VORTAC / VOR-DME, 108–118 MHz) the band is encoded in the 50 kHz step:
    `.x00` → X, `.x50` → Y. Channel-only TACANs (no frequency, common for
    military beacons) default to X — DCS's default mode, matching the in-game
    channel display (e.g. Kandahar = 75X).
    """
    if channel is None:
        return None
    if freq_hz and 108_000_000 <= freq_hz <= 118_000_000:
        return "Y" if round(freq_hz / 1000) % 100 == 50 else "X"
    return "X"


# Field extractors — applied per line inside a beacon record.
_RE_NAME = re.compile(r"""display_name\s*=\s*_?\(?\s*['"](.*?)['"]""")
_RE_TYPE = re.compile(r"type\s*=\s*(BEACON_TYPE_\w+)")
_RE_CALLSIGN = re.compile(r"""callsign\s*=\s*['"]([^'"]*)['"]""")
_RE_FREQ = re.compile(r"frequency\s*=\s*([\d.]+)")
_RE_CHANNEL = re.compile(r"channel\s*=\s*(\d+)")
_RE_GEO = re.compile(r"latitude\s*=\s*(-?[\d.]+).*?longitude\s*=\s*(-?[\d.]+)")


def _parse_field(record: dict[str, Any], line: str) -> None:
    m = _RE_GEO.search(line)
    if m:
        record["lat"] = float(m.group(1))
        record["lon"] = float(m.group(2))
        return
    m = _RE_NAME.search(line)
    if m:
        record["name"] = m.group(1)
        return
    m = _RE_TYPE.search(line)
    if m:
        record["type"] = m.group(1)
        return
    m = _RE_CALLSIGN.search(line)
    if m:
        record["callsign"] = m.group(1)
        return
    m = _RE_FREQ.search(line)
    if m:
        record["freq_hz"] = float(m.group(1))
        return
    m = _RE_CHANNEL.search(line)
    if m:
        record["channel"] = int(m.group(1))


def _record_to_navaid(record: dict[str, Any]) -> Navaid | None:
    if "lat" not in record or "lon" not in record:
        return None  # no geo position → can't place it
    freq_hz = record.get("freq_hz")
    channel = record.get("channel")
    return Navaid(
        name=record.get("name", ""),
        type=_friendly_type(record.get("type", "")),
        callsign=record.get("callsign", ""),
        lat=record["lat"],
        lon=record["lon"],
        freq_hz=freq_hz,
        channel=channel,
        band=_tacan_band(freq_hz, channel),
    )


def parse_beacons_lua(text: str) -> list[Navaid]:
    """Parse a terrain Beacons.lua into Navaids. Tolerant of the surrounding
    `dofile`/`require`/`_()` noise — only the `beacons = { … }` table is read."""
    out: list[Navaid] = []
    in_table = False
    record: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not in_table:
            # The world beacon table: a line like `beacons = {` (not
            # `beaconsTableFormat = 2`, which doesn't end in `{`).
            if line.startswith("beacons") and line.endswith("{"):
                in_table = True
            continue
        if record is None:
            if line == "{":
                record = {}
            elif line in ("}", "};"):
                break  # end of the beacons table
            continue
        # Inside a record.
        if line in ("}", "};"):
            nav = _record_to_navaid(record)
            if nav is not None:
                out.append(nav)
            record = None
            continue
        try:
            _parse_field(record, line)
        except (ValueError, IndexError) as exc:  # malformed value — skip the field
            log.debug("navaids: skipped field %r: %s", line, exc)
    return out


def find_beacons_file(dcs_install_dir: Path | str | None, theatre: str | None) -> Path | None:
    """Locate `Beacons.lua` for `theatre` under the DCS install, or None.

    Tries `Mods/terrains/<theatre>/` then a space/case-insensitive folder match,
    and a case-insensitive `beacons.lua` filename (DCS varies the capitalization).
    """
    if not dcs_install_dir or not theatre:
        return None
    terrains = Path(dcs_install_dir) / "Mods" / "terrains"
    if not terrains.is_dir():
        return None
    folder = terrains / theatre
    if not folder.is_dir():
        norm = theatre.replace(" ", "").lower()
        folder = next(
            (d for d in terrains.iterdir() if d.is_dir() and d.name.replace(" ", "").lower() == norm),
            None,
        )
        if folder is None:
            return None
    return next((f for f in folder.iterdir() if f.is_file() and f.name.lower() == "beacons.lua"), None)


def load_navaids(dcs_install_dir: Path | str | None, theatre: str | None) -> list[Navaid] | None:
    """Find + parse the theatre's Beacons.lua. None if the file can't be located
    (no DCS path / unknown theatre / missing file); `[]` if it parsed to nothing."""
    path = find_beacons_file(dcs_install_dir, theatre)
    if path is None:
        log.info("navaids: no Beacons.lua for theatre=%r under %s", theatre, dcs_install_dir)
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        log.warning("navaids: could not read %s: %s", path, exc)
        return None
    navaids = parse_beacons_lua(text)
    log.info("navaids: parsed %d from %s", len(navaids), path)
    return navaids
