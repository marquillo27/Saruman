"""Tests for high-score persistence."""
from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from saruman.save import highscores


def _make_entries(scores: list[int]) -> list[dict]:
    return [{"name": f"P{s}", "score": s} for s in scores]


# ---------------------------------------------------------------------------
# is_high_score
# ---------------------------------------------------------------------------

def test_zero_score_never_qualifies():
    assert not highscores.is_high_score(0, [])


def test_qualifies_on_empty_table():
    assert highscores.is_high_score(1, [])


def test_qualifies_when_table_not_full():
    entries = _make_entries([100, 200])
    assert highscores.is_high_score(50, entries)


def test_qualifies_when_beating_lowest():
    entries = _make_entries(list(range(100, 1100, 100)))  # 10 entries: 100..1000
    assert highscores.is_high_score(150, entries)


def test_does_not_qualify_below_lowest():
    entries = _make_entries(list(range(100, 1100, 100)))
    assert not highscores.is_high_score(50, entries)


# ---------------------------------------------------------------------------
# insert
# ---------------------------------------------------------------------------

def test_insert_rank_one():
    entries, rank = highscores.insert("ACE", 9999, [])
    assert rank == 1
    assert entries[0]["name"] == "ACE"
    assert entries[0]["score"] == 9999


def test_insert_sorted_order():
    base = _make_entries([500, 300, 100])
    entries, rank = highscores.insert("NEW", 400, base)
    scores = [e["score"] for e in entries]
    assert scores == sorted(scores, reverse=True)
    assert rank == 2


def test_insert_caps_at_top_scores():
    base = _make_entries(list(range(1000, 11000, 1000)))  # 10 entries
    entries, rank = highscores.insert("BIG", 99999, base)
    from saruman.config import TOP_SCORES
    assert len(entries) <= TOP_SCORES
    assert entries[0]["name"] == "BIG"


def test_insert_blank_name_becomes_placeholder():
    entries, _ = highscores.insert("   ", 100, [])
    assert entries[0]["name"] == "???"


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_round_trip(tmp_path):
    scores_file = tmp_path / "highscores.json"
    with patch("saruman.save.highscores._path", return_value=scores_file):
        original = [{"name": "AAA", "score": 1000}, {"name": "BBB", "score": 500}]
        highscores.save(original)
        loaded = highscores.load()
    assert loaded == original


def test_load_missing_file_returns_empty(tmp_path):
    missing = tmp_path / "no_such_file.json"
    with patch("saruman.save.highscores._path", return_value=missing):
        assert highscores.load() == []


def test_load_corrupt_file_returns_empty(tmp_path):
    corrupt = tmp_path / "bad.json"
    corrupt.write_text("not json!!!", encoding="utf-8")
    with patch("saruman.save.highscores._path", return_value=corrupt):
        assert highscores.load() == []


def test_save_write_error_does_not_crash(tmp_path):
    read_only_dir = tmp_path / "ro"
    read_only_dir.mkdir()
    bad_path = read_only_dir / "scores.json"
    # Make directory read-only so write fails
    import stat
    read_only_dir.chmod(stat.S_IREAD | stat.S_IEXEC)
    try:
        with patch("saruman.save.highscores._path", return_value=bad_path):
            highscores.save([{"name": "X", "score": 1}])  # must not raise
    finally:
        read_only_dir.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
