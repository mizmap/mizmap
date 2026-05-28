"""Windows tray icon + uvicorn lifecycle for the frozen MizMap exe.

Architecture:
  - uvicorn runs in a daemon thread (cannot run on the main thread because
    pystray claims it on Windows).
  - pystray.Icon.run() blocks the main thread, draws the tray icon, and
    dispatches menu clicks.
  - "Open viewer" launches the default browser at the bound URL.
  - "Quit MizMap" sets `server.should_exit = True`, then `icon.stop()` returns
    control from `Icon.run()`, and the uvicorn thread drains cleanly when
    the event loop notices the flag.

pystray (and pillow) are runtime deps gated on `sys_platform == "win32"`
in pyproject.toml — this module is only imported when the tray path is
selected, so dev runs on Mac/Linux never need them.
"""

from __future__ import annotations

import logging
import socket
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn

if TYPE_CHECKING:
    from fastapi import FastAPI

    from mizmap.config import Settings

log = logging.getLogger(__name__)

_ICON_PATH = Path(__file__).resolve().parent / "data" / "mizmap.ico"


def _load_icon_image():
    """Load the multi-resolution compass-rose ICO that ships with the package.

    Falls back to a simple programmatic glyph if the file is missing (e.g. in
    a half-bootstrapped dev checkout before `scripts/make_icon.py` ran). The
    frozen exe always bundles the real ICO; the fallback only matters for
    dev edge cases.
    """
    from PIL import Image

    if _ICON_PATH.is_file():
        return Image.open(_ICON_PATH)
    log.warning("tray icon %s missing — using programmatic fallback", _ICON_PATH)
    return _fallback_icon_image()


def _fallback_icon_image():
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGB", (size, size), color=(14, 42, 71))
    ImageDraw.Draw(img).ellipse((4, 4, size - 4, size - 4), outline=(166, 192, 224), width=2)
    return img


_WILDCARD_HOSTS = ("0.0.0.0", "::", "")
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def _viewer_url(settings: "Settings") -> str:
    host = settings.http_host
    display_host = "localhost" if host in _WILDCARD_HOSTS else host
    return f"http://{display_host}:{settings.http_port}/"


def _lan_ip(fallback: str = "127.0.0.1") -> str:
    """Best-effort detect this machine's primary LAN IPv4.

    The UDP-connect trick: a *connected* UDP socket exposes which local
    interface would route to the destination, without sending any packets.
    Picks the route to 8.8.8.8 since that's almost always the default
    gateway, which matches what a tablet on the same network would reach.
    Falls back to loopback if anything fails (e.g. no network).
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return fallback


def _lan_url(settings: "Settings") -> str | None:
    """LAN URL suitable for a tablet to hit, or None if loopback-bound.

    Returns None when http_host is loopback (the server is unreachable from
    the LAN regardless of the host's IP), so callers can hide the affordance.
    """
    if settings.http_host in _LOOPBACK_HOSTS:
        return None
    return f"http://{_lan_ip()}:{settings.http_port}/"


def _copy_to_clipboard(text: str) -> bool:
    """Copy `text` to the Windows clipboard via clip.exe (built in since Vista).

    Avoids new deps and skips spawning a visible cmd window. Returns False on
    failure so the caller can log without raising.
    """
    try:
        subprocess.run(
            ["clip.exe"],
            input=text,
            text=True,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except (OSError, subprocess.CalledProcessError) as exc:
        log.warning("clipboard copy failed: %s", exc)
        return False


def run_with_tray(app: "FastAPI", settings: "Settings") -> None:
    """Run uvicorn in a background thread, the tray icon in the main thread.

    Returns when the user picks "Quit MizMap" from the tray.
    """
    import pystray

    config = uvicorn.Config(
        app,
        host=settings.http_host,
        port=settings.http_port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    def _serve() -> None:
        try:
            server.run()
        except Exception:
            log.exception("uvicorn thread crashed")

    server_thread = threading.Thread(target=_serve, name="mizmap-uvicorn", daemon=True)
    server_thread.start()

    url = _viewer_url(settings)
    lan_url = _lan_url(settings)

    def on_open(icon, item):  # noqa: ARG001
        try:
            webbrowser.open(url)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not open browser at %s: %s", url, exc)

    def on_settings(icon, item):  # noqa: ARG001
        # ?settings=1 makes the viewer auto-open the Settings panel on load.
        try:
            webbrowser.open(f"{url}?settings=1")
        except Exception as exc:  # noqa: BLE001
            log.warning("could not open settings at %s: %s", url, exc)

    def on_copy_lan(icon, item):  # noqa: ARG001
        if lan_url and _copy_to_clipboard(lan_url):
            log.info("tray: copied %s to clipboard", lan_url)

    def on_quit(icon, item):  # noqa: ARG001
        log.info("tray: quit requested")
        server.should_exit = True
        icon.stop()

    # Tooltip prefers the LAN URL — that's what a tablet user needs to type.
    # Falls back to the local URL if we're loopback-bound or LAN detection
    # failed (which surfaces lan_url == None or the loopback-IP fallback).
    title = f"MizMap — {lan_url}" if lan_url else f"MizMap — {url}"
    menu_items = [
        pystray.MenuItem("Open viewer", on_open, default=True),
        pystray.MenuItem("Settings…", on_settings),
    ]
    if lan_url:
        menu_items.append(pystray.MenuItem(f"Copy LAN URL ({lan_url})", on_copy_lan))
    menu_items += [pystray.Menu.SEPARATOR, pystray.MenuItem("Quit MizMap", on_quit)]

    icon = pystray.Icon(
        "MizMap",
        icon=_load_icon_image(),
        title=title,
        menu=pystray.Menu(*menu_items),
    )
    # Open the viewer once on startup. pystray's Icon.run() supports a setup
    # callback that fires after the icon is visible, which is the right place
    # to launch the browser (the server thread has already started, and the
    # tray is visible if the launch is slow).
    def _setup(_icon):
        _icon.visible = True
        on_open(_icon, None)

    icon.run(setup=_setup)
    # Block here until the user clicks Quit. After Icon.run returns, give
    # uvicorn a few seconds to drain.
    server_thread.join(timeout=5.0)
    if server_thread.is_alive():
        log.warning("uvicorn thread did not exit within 5s after Quit")
