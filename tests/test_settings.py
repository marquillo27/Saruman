"""Tests for settings persistence."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from saruman.save import settings as cfg


# Reset the in-memory cache before each test so tests don't bleed into each other
@pytest.fixture(autouse=True)
def reset_cache():
    cfg._current = None
    yield
    cfg._current = None


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

def test_defaults_on_missing_file(tmp_path):
    missing = tmp_path / "no_file.json"
    with patch("saruman.save.settings._path", return_value=missing):
        s = cfg.load()
    assert s["music_volume"] == cfg._DEFAULTS["music_volume"]
    assert s["sfx_volume"]   == cfg._DEFAULTS["sfx_volume"]
    assert s["fullscreen"]   == cfg._DEFAULTS["fullscreen"]


def test_corrupt_file_returns_defaults(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json!!!", encoding="utf-8")
    with patch("saruman.save.settings._path", return_value=bad):
        s = cfg.load()
    assert s == cfg._DEFAULTS


def test_partial_file_merges_with_defaults(tmp_path):
    import json
    partial = tmp_path / "partial.json"
    partial.write_text(json.dumps({"music_volume": 3}), encoding="utf-8")
    with patch("saruman.save.settings._path", return_value=partial):
        s = cfg.load()
    assert s["music_volume"] == 3                    # from file
    assert s["sfx_volume"]   == cfg._DEFAULTS["sfx_volume"]  # default


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

def test_save_load_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    with patch("saruman.save.settings._path", return_value=path):
        cfg._current = {"music_volume": 7, "sfx_volume": 4, "fullscreen": True}
        cfg.save()
        cfg._current = None          # bust cache
        s = cfg.load()
    assert s["music_volume"] == 7
    assert s["sfx_volume"]   == 4
    assert s["fullscreen"]   is True


def test_save_write_error_does_not_crash(tmp_path):
    import stat
    ro_dir = tmp_path / "ro"
    ro_dir.mkdir()
    ro_dir.chmod(stat.S_IREAD | stat.S_IEXEC)
    bad_path = ro_dir / "settings.json"
    try:
        with patch("saruman.save.settings._path", return_value=bad_path):
            cfg._current = dict(cfg._DEFAULTS)
            cfg.save()   # must not raise
    finally:
        ro_dir.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)


# ---------------------------------------------------------------------------
# Singleton cache
# ---------------------------------------------------------------------------

def test_get_returns_same_object(tmp_path):
    missing = tmp_path / "none.json"
    with patch("saruman.save.settings._path", return_value=missing):
        s1 = cfg.get()
        s2 = cfg.get()
    assert s1 is s2


def test_get_mutations_are_visible_on_next_call(tmp_path):
    missing = tmp_path / "none.json"
    with patch("saruman.save.settings._path", return_value=missing):
        s = cfg.get()
        s["music_volume"] = 0
        assert cfg.get()["music_volume"] == 0
