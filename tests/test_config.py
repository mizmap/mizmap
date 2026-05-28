"""Tests for mizmap.config — env var resolution + frozen-aware defaults."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mizmap.config import (
    Settings,
    detect_dcs_install_dir,
    ensure_config_file,
    env_locked_keys,
    update_config_file,
)


_MIZMAP_ENV_VARS = (
    "MIZMAP_HTTP_HOST", "MIZMAP_HTTP_PORT", "MIZMAP_GRPC_HOST", "MIZMAP_GRPC_PORT",
    "MIZMAP_TILE_URL", "MIZMAP_TILE_ATTRIBUTION", "MIZMAP_TILE_CACHE_DIR",
    "MIZMAP_DCS_INSTALL_DIR",
)


def test_defaults_from_env_dev(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    # Isolate from any real config.toml in the dev cwd.
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(tmp_path / "none.toml"))
    s = Settings.from_env()
    assert s.http_host == "0.0.0.0"
    assert s.http_port == 8766
    assert s.grpc_host == "127.0.0.1"
    assert s.grpc_port == 50051
    # Dev default resolves to <cwd>/cache/tiles
    assert s.tile_cache_dir == (Path.cwd() / "cache" / "tiles").resolve()


def test_env_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("MIZMAP_HTTP_PORT", "9000")
    monkeypatch.setenv("MIZMAP_GRPC_HOST", "10.0.0.5")
    monkeypatch.setenv("MIZMAP_TILE_CACHE_DIR", str(tmp_path))
    s = Settings.from_env()
    assert s.http_port == 9000
    assert s.grpc_host == "10.0.0.5"
    assert s.tile_cache_dir == tmp_path.resolve()


def test_frozen_default_tile_cache_in_localappdata(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv("MIZMAP_TILE_CACHE_DIR", raising=False)
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(tmp_path / "none.toml"))
    s = Settings.from_env()
    assert s.tile_cache_dir == (tmp_path / "MizMap" / "tiles").resolve()


def test_config_file_values_apply_when_set(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    cfg = tmp_path / "mizmap.toml"
    cfg.write_text(
        'http_port = 9100\n'
        'grpc_host = "192.168.1.10"\n'
        'tile_url = "https://example.com/{z}/{x}/{y}.png"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    s = Settings.from_env()
    assert s.http_port == 9100
    assert s.grpc_host == "192.168.1.10"
    assert s.tile_url == "https://example.com/{z}/{x}/{y}.png"


def test_env_var_overrides_config_file(monkeypatch, tmp_path):
    cfg = tmp_path / "mizmap.toml"
    cfg.write_text('http_port = 9100\n', encoding="utf-8")
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    monkeypatch.setenv("MIZMAP_HTTP_PORT", "9999")
    s = Settings.from_env()
    assert s.http_port == 9999


def test_malformed_config_file_falls_back_to_defaults(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    cfg = tmp_path / "mizmap.toml"
    cfg.write_text("this is = not = valid toml\n", encoding="utf-8")
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    s = Settings.from_env()
    # Defaults kick in.
    assert s.http_port == 8766


def test_ensure_config_file_no_op_in_dev(monkeypatch, tmp_path):
    # Not frozen → no file written even if user_config_dir is writable.
    monkeypatch.setattr("mizmap.config.is_frozen", lambda: False)
    assert ensure_config_file() is None


def test_ensure_config_file_writes_template_on_first_run(monkeypatch, tmp_path):
    monkeypatch.setattr("mizmap.config.is_frozen", lambda: True)
    monkeypatch.setattr("mizmap.config.user_config_dir", lambda: tmp_path)
    written = ensure_config_file()
    assert written == tmp_path / "config.toml"
    assert written.is_file()
    body = written.read_text(encoding="utf-8")
    assert "http_port" in body
    assert body.startswith("# MizMap configuration")


def test_ensure_config_file_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr("mizmap.config.is_frozen", lambda: True)
    monkeypatch.setattr("mizmap.config.user_config_dir", lambda: tmp_path)
    first = ensure_config_file()
    second = ensure_config_file()
    assert first is not None
    assert second is None  # second call sees existing file


# --- dcs_install_dir resolution --------------------------------------------

def test_dcs_install_dir_from_file(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    cfg = tmp_path / "c.toml"
    cfg.write_text(f'dcs_install_dir = "{tmp_path.as_posix()}"\n', encoding="utf-8")
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    s = Settings.from_env()
    assert s.dcs_install_dir == tmp_path


def test_dcs_install_dir_env_overrides_file(monkeypatch, tmp_path):
    cfg = tmp_path / "c.toml"
    cfg.write_text('dcs_install_dir = "C:/from-file"\n', encoding="utf-8")
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    monkeypatch.setenv("MIZMAP_DCS_INSTALL_DIR", str(tmp_path))
    s = Settings.from_env()
    assert s.dcs_install_dir == tmp_path


def test_dcs_install_dir_falls_back_to_autodetect(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(tmp_path / "none.toml"))
    monkeypatch.setattr("mizmap.config.detect_dcs_install_dir", lambda: tmp_path)
    s = Settings.from_env()
    assert s.dcs_install_dir == tmp_path


# --- env_locked_keys -------------------------------------------------------

def test_env_locked_keys_reports_set_vars(monkeypatch):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    assert "http_port" not in env_locked_keys()
    monkeypatch.setenv("MIZMAP_HTTP_PORT", "9000")
    locked = env_locked_keys()
    assert "http_port" in locked
    assert "grpc_host" not in locked


# --- update_config_file ----------------------------------------------------

def test_update_config_file_roundtrip(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    cfg = tmp_path / "c.toml"
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    update_config_file({"http_port": 9001, "dcs_install_dir": "C:/DCS"})
    s = Settings.from_env()
    assert s.http_port == 9001
    assert s.dcs_install_dir == Path("C:/DCS")
    # None clears a key → reverts to default/auto.
    monkeypatch.setattr("mizmap.config.detect_dcs_install_dir", lambda: None)
    update_config_file({"dcs_install_dir": None})
    s2 = Settings.from_env()
    assert s2.http_port == 9001  # untouched key preserved
    assert s2.dcs_install_dir is None


def test_update_config_file_preserves_unrelated_keys(monkeypatch, tmp_path):
    for key in _MIZMAP_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    cfg = tmp_path / "c.toml"
    cfg.write_text('tile_url = "https://example.com/{z}/{x}/{y}.png"\n', encoding="utf-8")
    monkeypatch.setenv("MIZMAP_CONFIG_FILE", str(cfg))
    update_config_file({"http_port": 9100})
    s = Settings.from_env()
    assert s.http_port == 9100
    assert s.tile_url == "https://example.com/{z}/{x}/{y}.png"


def test_detect_dcs_install_dir_returns_path_or_none():
    # Smoke: never raises; returns a Path or None on any platform.
    result = detect_dcs_install_dir()
    assert result is None or isinstance(result, Path)
