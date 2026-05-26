"""PyInstaller entry point.

When mizmap.exe is double-clicked with no args, run `mizmap serve` directly so the
non-technical user gets the tray + browser auto-open UX without typing
anything. When called with args, delegate to the typer CLI so power users
still have `mizmap version`, `mizmap clear-cache`, etc.
"""

from __future__ import annotations

import os
import sys


def _ensure_std_streams() -> None:
    """Give downstream code real stdout/stderr objects to talk to.

    PyInstaller's no-console bundle (`console=False`) leaves sys.stdout and
    sys.stderr as `None` when the process has no parent console — exactly
    the Start-menu / Explorer launch path. That breaks anything that calls
    `.isatty()` or `.write()` on those streams, including:
      - uvicorn's DefaultFormatter (crashes in `__init__` → kills startup)
      - click/typer's echo (silently swallows + may raise on some paths)
      - any third-party `print(...)` for diagnostics

    Redirecting to os.devnull is the standard PyInstaller workaround:
    everything gets to write somewhere harmless, and visible user output
    routes through the tray icon + MessageBox paths regardless.
    """
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def main() -> None:
    _ensure_std_streams()
    from mizmap.cli import app

    if len(sys.argv) == 1:
        # Double-click default: just `mizmap serve`. --tray/--browser default to
        # on because is_frozen() is True in this bundle.
        app(["serve"])
    else:
        app()


if __name__ == "__main__":
    main()
