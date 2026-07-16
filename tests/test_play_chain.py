"""Tests for level progression chain and music map in PlayState."""
from __future__ import annotations

import pytest

from saruman.states.play import PlayState


ALL_STEMS = [
    "level_01_greenshire_hills",
    "level_02_wolfwood",
    "level_03_glass_caverns",
    "level_04_sunken_mines",
    "level_05_ash_marshes",
    "level_06_pale_tower",
    "level_07_cursed_catacombs",
    "level_08_forsaken_bridge",
    "level_09_skybound_spires",
    "level_10_goblin_kings_throne",
    "level_11_ashfall_wastes",
    "level_12_cinderwood_remains",
    "level_13_emberfall_keep",
]

FINAL_STEM   = "level_13_emberfall_keep"
# Levels that reuse music tracks (allowed duplicates)
REUSED_MUSIC_STEMS = {
    "level_07_cursed_catacombs",
    "level_08_forsaken_bridge",
    "level_09_skybound_spires",
    "level_10_goblin_kings_throne",
    "level_11_ashfall_wastes",
    "level_12_cinderwood_remains",
    "level_13_emberfall_keep",
}
INTERMEDIATE = [s for s in ALL_STEMS if s != FINAL_STEM]


# ---------------------------------------------------------------------------
# _NEXT_LEVEL routing
# ---------------------------------------------------------------------------

def test_final_level_not_in_next_level_map():
    """Absent key → win screen, not infinite loop."""
    assert FINAL_STEM not in PlayState._NEXT_LEVEL


def test_all_intermediate_levels_have_a_next():
    for stem in INTERMEDIATE:
        assert stem in PlayState._NEXT_LEVEL, f"{stem} missing from _NEXT_LEVEL"


def test_level_chain_order():
    """World I (Greenwood): greenshire -> wolfwood -> sunken_mines[BossWarg] -> World II."""
    chain = PlayState._NEXT_LEVEL
    assert chain["level_01_greenshire_hills"] == "level_02_wolfwood"
    assert chain["level_02_wolfwood"]         == "level_04_sunken_mines"
    assert chain["level_03_glass_caverns"]    == "level_04_sunken_mines"
    assert chain["level_04_sunken_mines"]     == "level_11_ashfall_wastes"


def test_secret_rejoins_main_chain():
    """Glass Caverns (secret) rejoins main progression at Sunken Mines."""
    assert PlayState._NEXT_LEVEL["level_03_glass_caverns"] == "level_04_sunken_mines"


def test_chain_targets_are_valid_stems():
    for nxt in PlayState._NEXT_LEVEL.values():
        assert nxt in ALL_STEMS, f"Chain target '{nxt}' is not a known level stem"


def test_world_two_scorchlands_order():
    """World II (Scorchlands): ashfall -> cinderwood -> ash_marshes -> throne[GoblinKing]."""
    chain = PlayState._NEXT_LEVEL
    assert chain["level_11_ashfall_wastes"]     == "level_12_cinderwood_remains"
    assert chain["level_12_cinderwood_remains"] == "level_05_ash_marshes"
    assert chain["level_05_ash_marshes"]        == "level_10_goblin_kings_throne"


def test_world_three_frozen_north_order():
    """World III (Frozen North): pale_tower -> skybound -> bridge -> catacombs -> emberfall[NightKing]."""
    chain = PlayState._NEXT_LEVEL
    assert chain["level_10_goblin_kings_throne"] == "level_06_pale_tower"
    assert chain["level_06_pale_tower"]          == "level_09_skybound_spires"
    assert chain["level_09_skybound_spires"]     == "level_08_forsaken_bridge"
    assert chain["level_08_forsaken_bridge"]     == "level_07_cursed_catacombs"
    assert chain["level_07_cursed_catacombs"]    == "level_13_emberfall_keep"


def test_world_bosses_sit_at_world_ends():
    """Each world ends by routing into the next world's first level (or the win screen)."""
    chain = PlayState._NEXT_LEVEL
    # World I boss (sunken_mines) routes into World II (ashfall)
    assert chain["level_04_sunken_mines"] == "level_11_ashfall_wastes"
    # World II boss (throne) routes into World III (pale_tower)
    assert chain["level_10_goblin_kings_throne"] == "level_06_pale_tower"
    # World III boss (emberfall) has no successor -> win
    assert "level_13_emberfall_keep" not in chain


def test_no_chain_cycles():
    """Following _NEXT_LEVEL from any starting point eventually terminates."""
    chain = PlayState._NEXT_LEVEL
    for start in chain:
        visited = set()
        current = start
        while current in chain:
            assert current not in visited, f"Cycle detected from {start}"
            visited.add(current)
            current = chain[current]


# ---------------------------------------------------------------------------
# _LEVEL_MUSIC coverage
# ---------------------------------------------------------------------------

def test_music_map_covers_all_levels():
    for stem in ALL_STEMS:
        assert stem in PlayState._LEVEL_MUSIC, f"{stem} missing from _LEVEL_MUSIC"


def test_music_values_are_wav_files():
    for stem, track in PlayState._LEVEL_MUSIC.items():
        assert track.endswith(".wav"), f"{stem} maps to non-wav: {track}"


def test_each_level_has_distinct_music():
    # Final-stretch levels intentionally reuse atmospheric tracks.
    # All other levels must have unique tracks.
    tracks = [
        t for s, t in PlayState._LEVEL_MUSIC.items()
        if s not in REUSED_MUSIC_STEMS
    ]
    assert len(tracks) == len(set(tracks)), "Two non-final levels share the same music track"


def test_level_07_has_music():
    assert "level_07_cursed_catacombs" in PlayState._LEVEL_MUSIC


def test_level_08_has_music():
    assert "level_08_forsaken_bridge" in PlayState._LEVEL_MUSIC


def test_level_09_has_music():
    assert "level_09_skybound_spires" in PlayState._LEVEL_MUSIC


def test_level_10_has_music():
    assert "level_10_goblin_kings_throne" in PlayState._LEVEL_MUSIC
