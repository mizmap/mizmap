"""Top-level CLI for MizMap."""

from __future__ import annotations

import sys

import typer

from mizmap import __version__
from mizmap.config import Settings, ensure_config_file
from mizmap.paths import is_frozen


def _report_result(text: str, *, is_error: bool = False) -> None:
    """Surface a one-shot CLI result to the user.

    In dev (console attached) prints normally. In the frozen no-console exe,
    `sys.stdout`/`sys.stderr` may be `None` and any prints go nowhere visible —
    so we also pop a MessageBox so a Start-menu-triggered action (like
    Clear MizMap tile cache) actually shows feedback.
    """
    stream = sys.stderr if is_error else sys.stdout
    if stream is not None:
        try:
            typer.echo(text, err=is_error)
        except OSError:
            pass
    if is_frozen() and sys.platform == "win32":
        import ctypes

        MB_ICONINFORMATION = 0x40
        MB_ICONERROR = 0x10
        flags = MB_ICONERROR if is_error else MB_ICONINFORMATION
        ctypes.windll.user32.MessageBoxW(0, text, "MizMap", flags)

app = typer.Typer(
    name="mizmap",
    help="MizMap — live moving-map viewer for DCS World.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def version() -> None:
    """Print the MizMap version."""
    typer.echo(__version__)


@app.command()
def serve(
    browser: bool = typer.Option(
        None,
        "--browser/--no-browser",
        help="Open the viewer in the default web browser at startup. "
        "Defaults to on when running as the installed Windows app, off in dev.",
    ),
    tray: bool = typer.Option(
        None,
        "--tray/--no-tray",
        help="Run with a system-tray icon (Open viewer / Quit MizMap menu). "
        "Defaults to on when running as the installed Windows app, off in dev.",
    ),
) -> None:
    """Start the MizMap server (HTTP + WebSocket viewer, gRPC client to DCS)."""
    from mizmap.server import run, run_with_tray

    template_path = ensure_config_file()
    if template_path is not None:
        typer.echo(f"Wrote default config template to {template_path}")
    settings = Settings.from_env()
    frozen = is_frozen()
    if tray is None:
        tray = frozen
    if browser is None:
        browser = frozen
    typer.echo(
        f"MizMap v{__version__} — listening on http://{settings.http_host}:{settings.http_port} "
        f"(gRPC target: {settings.grpc_host}:{settings.grpc_port})"
    )
    if tray:
        run_with_tray()
    else:
        run(open_browser=browser)


@app.command(name="clear-cache")
def clear_cache() -> None:
    """Wipe the local tile cache. Useful when you've changed MIZMAP_TILE_URL."""
    from mizmap.tiles import clear_cache as _clear

    settings = Settings.from_env()
    try:
        files, bytes_freed = _clear(settings.tile_cache_dir)
    except OSError as exc:
        _report_result(
            f"Failed to clear tile cache at {settings.tile_cache_dir}:\n{exc}",
            is_error=True,
        )
        raise typer.Exit(code=1) from exc
    mib = bytes_freed / (1024 * 1024)
    _report_result(
        f"Cleared {files} tile(s), freed {mib:.1f} MiB from {settings.tile_cache_dir}"
    )


if __name__ == "__main__":
    app()
