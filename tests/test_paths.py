"""Tests for mizmap.paths — frozen detection + path resolution.

We can't actually run a frozen exe inside the test process, so the
frozen-mode branches are exercised by monkeypatching `sys.frozen` and
`sys._MEIPASS`. The dev-mode branches are exercised directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mizmap import paths


def test_is_frozen_false_in_dev():
    assert paths.is_frozen() is False


def test_web_dir_resolves_to_source_tree_in_dev():
    # The source tree has web/ alongside mizmap/.
    web = paths.web_dir()
    assert web.is_dir(), f"expected web dir to exist at {web}"
    assert (web / "index.html").is_file()


def test_user_cache_dir_is_cwd_in_dev():
    assert paths.user_cache_dir() == Path.cwd()


def test_user_config_dir_is_cwd_in_dev():
    assert paths.user_config_dir() == Path.cwd()


def test_default_tile_cache_dir_is_relative_in_dev():
    # Dev default is a relative path so it lives in the repo's cache/ dir.
    assert paths.default_tile_cache_dir() == Path("cache") / "tiles"


def test_user_cache_dir_routes_to_localappdata_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert paths.user_cache_dir() == tmp_path / "MizMap"


def test_user_config_dir_routes_to_appdata_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert paths.user_config_dir() == tmp_path / "MizMap"


def test_default_tile_cache_dir_routes_to_localappdata_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert paths.default_tile_cache_dir() == tmp_path / "MizMap" / "tiles"


def test_frozen_without_localappdata_falls_back_to_cwd(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    assert paths.user_cache_dir() == Path.cwd()


def test_web_dir_prefers_bundle_when_frozen(monkeypatch, tmp_path):
    # Simulate a PyInstaller bundle layout: <_MEIPASS>/web/index.html exists.
    bundle = tmp_path / "bundle"
    (bundle / "web").mkdir(parents=True)
    (bundle / "web" / "index.html").write_text("<!doctype html>")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    assert paths.web_dir() == bundle / "web"
