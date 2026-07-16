"""Tests for TMX level loader — every documented object type and all levels."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest
import pygame

from saruman.entities.enemy import (
    BossWarg, CaveBat, GoblinKing, Goblinkin, MimicChest, NightKing,
    ShieldKnight, SkeletonArcher, Slime, SpitterPlant, Wraith,
)
from saruman.entities.interactive import MovingPlatform, Spring
from saruman.entities.item import Coin, Gem, Heart, WeaponUpgrade
from saruman.entities.trigger import LevelEndTrigger
from saruman.paths import asset_path
from saruman.world.level_loader import load_level


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture(scope="module")
def level():
    return load_level(asset_path("maps", "level_02_wolfwood.tmx"))


@pytest.fixture(scope="module")
def greenshire():
    return load_level(asset_path("maps", "level_01_greenshire_hills.tmx"))


@pytest.fixture(scope="module")
def mines():
    return load_level(asset_path("maps", "level_04_sunken_mines.tmx"))


@pytest.fixture(scope="module")
def tower():
    return load_level(asset_path("maps", "level_06_pale_tower.tmx"))


# ---------------------------------------------------------------------------
# Tilemap (wolfwood reference level)
# ---------------------------------------------------------------------------

def test_tilemap_has_positive_dimensions(level):
    tilemap, *_ = level
    assert tilemap.pixel_width  > 0
    assert tilemap.pixel_height > 0


def test_solid_ground_row(level):
    tilemap, *_ = level
    from saruman.config import TILE_SIZE
    ground_row = 11
    map_w = tilemap.pixel_width // TILE_SIZE
    solid_cols = [tilemap.is_solid(tx, ground_row) for tx in range(map_w)]
    assert all(solid_cols), "Ground row must be entirely solid"


# ---------------------------------------------------------------------------
# Player spawn (wolfwood)
# ---------------------------------------------------------------------------

def test_player_spawn_is_tuple_of_floats(level):
    _, spawn, *_ = level
    assert isinstance(spawn, tuple) and len(spawn) == 2
    assert all(isinstance(v, float) for v in spawn)


def test_player_spawn_inside_level(level):
    tilemap, spawn, *_ = level
    x, y = spawn
    assert 0 <= x < tilemap.pixel_width
    assert 0 <= y < tilemap.pixel_height


# ---------------------------------------------------------------------------
# Enemies (wolfwood)
# ---------------------------------------------------------------------------

def test_goblinkin_present(level):
    _, _, enemies, *_ = level
    assert any(isinstance(e, Goblinkin) for e in enemies)


def test_wraith_present(level):
    _, _, enemies, *_ = level
    assert any(isinstance(e, Wraith) for e in enemies)


def test_wolfwood_has_no_boss_warg(level):
    """Wolfwood is now an early World I level — its mid-level BossWarg was removed."""
    _, _, enemies, *_ = level
    assert not any(isinstance(e, BossWarg) for e in enemies)


def test_all_enemies_alive_on_load(level):
    _, _, enemies, *_ = level
    assert all(e.alive for e in enemies)


def test_wraith_has_patrol_width(level):
    _, _, enemies, *_ = level
    for w in (e for e in enemies if isinstance(e, Wraith)):
        assert w._patrol_w > 0


# ---------------------------------------------------------------------------
# Items (wolfwood)
# ---------------------------------------------------------------------------

def test_coins_present(level):
    _, _, _, items, *_ = level
    assert any(isinstance(i, Coin) for i in items)


def test_heart_present(level):
    _, _, _, items, *_ = level
    assert any(isinstance(i, Heart) for i in items)


def test_weapon_upgrade_present(level):
    _, _, _, items, *_ = level
    assert any(isinstance(i, WeaponUpgrade) for i in items)


def test_all_items_alive_on_load(level):
    _, _, _, items, *_ = level
    assert all(i.alive for i in items)


# ---------------------------------------------------------------------------
# Level 01 — Greenshire Hills (tutorial)
# ---------------------------------------------------------------------------

def test_greenshire_loads_with_positive_dimensions(greenshire):
    tilemap, *_ = greenshire
    assert tilemap.pixel_width > 0 and tilemap.pixel_height > 0


def test_greenshire_has_no_shieldknight(greenshire):
    """Tutorial level must not contain ShieldKnights."""
    _, _, enemies, *_ = greenshire
    assert not any(isinstance(e, ShieldKnight) for e in enemies)


def test_greenshire_has_goblinkins(greenshire):
    _, _, enemies, *_ = greenshire
    goblins = [e for e in enemies if isinstance(e, Goblinkin)]
    assert len(goblins) >= 1


def test_greenshire_has_coins(greenshire):
    _, _, _, items, *_ = greenshire
    assert any(isinstance(i, Coin) for i in items)


def test_greenshire_has_level_end_trigger(greenshire):
    *_, triggers = greenshire
    assert any(isinstance(t, LevelEndTrigger) for t in triggers)


def test_greenshire_spawn_inside_level(greenshire):
    tilemap, spawn, *_ = greenshire
    x, y = spawn
    assert 0 <= x < tilemap.pixel_width
    assert 0 <= y < tilemap.pixel_height


# ---------------------------------------------------------------------------
# Level 04 — Sunken Mines (first ShieldKnight encounter)
# ---------------------------------------------------------------------------

def test_mines_has_shieldknight(mines):
    _, _, enemies, *_ = mines
    assert any(isinstance(e, ShieldKnight) for e in mines[2])


def test_mines_has_boss_warg(mines):
    _, _, enemies, *_ = mines
    assert any(isinstance(e, BossWarg) for e in enemies)


def test_mines_has_solid_ceiling(mines):
    """Sunken Mines has a solid ceiling tile row at row 0."""
    from saruman.config import TILE_SIZE
    tilemap, *_ = mines
    map_w = tilemap.pixel_width // TILE_SIZE
    ceiling_cols = [tilemap.is_solid(tx, 0) for tx in range(map_w)]
    assert all(ceiling_cols), "Sunken Mines must have a solid ceiling at row 0"


def test_mines_has_level_end_trigger(mines):
    *_, triggers = mines
    assert any(isinstance(t, LevelEndTrigger) for t in triggers)


# ---------------------------------------------------------------------------
# Level 06 — Pale Tower (final, dual boss)
# ---------------------------------------------------------------------------

def test_tower_has_no_boss_warg(tower):
    """Pale Tower is now a normal World III level — its mid-level BossWargs were removed."""
    _, _, enemies, *_ = tower
    assert not any(isinstance(e, BossWarg) for e in enemies)


def test_tower_has_shieldknights(tower):
    _, _, enemies, *_ = tower
    knights = [e for e in enemies if isinstance(e, ShieldKnight)]
    assert len(knights) >= 1


def test_tower_has_level_end_trigger(tower):
    *_, triggers = tower
    assert any(isinstance(t, LevelEndTrigger) for t in triggers)


def test_tower_level_end_bonus_is_highest(tower, level, mines):
    """Pale Tower bonus must exceed Wolfwood and Mines bonuses."""
    def first_bonus(triggers):
        for t in triggers:
            if isinstance(t, LevelEndTrigger):
                return t.score_bonus
        return 0

    tower_bonus  = first_bonus(tower[-1])
    ww_bonus     = first_bonus(level[-1])
    mines_bonus  = first_bonus(mines[-1])
    assert tower_bonus > ww_bonus
    assert tower_bonus > mines_bonus


# ---------------------------------------------------------------------------
# All levels — smoke test (load without error)
# ---------------------------------------------------------------------------

ALL_LEVEL_FILES = [
    "level_01_greenshire_hills.tmx",
    "level_02_wolfwood.tmx",
    "level_03_glass_caverns.tmx",
    "level_04_sunken_mines.tmx",
    "level_05_ash_marshes.tmx",
    "level_06_pale_tower.tmx",
    "level_07_cursed_catacombs.tmx",
    "level_08_forsaken_bridge.tmx",
    "level_09_skybound_spires.tmx",
    "level_10_goblin_kings_throne.tmx",
    "level_11_ashfall_wastes.tmx",
    "level_12_cinderwood_remains.tmx",
    "level_13_emberfall_keep.tmx",
]


@pytest.mark.parametrize("filename", ALL_LEVEL_FILES)
def test_all_levels_load_without_error(filename):
    tilemap, spawn, enemies, items, interactives, triggers = load_level(
        asset_path("maps", filename)
    )
    assert tilemap.pixel_width > 0
    assert all(e.alive for e in enemies)
    assert all(i.alive for i in items)
    assert all(i.alive for i in interactives)


# ---------------------------------------------------------------------------
# M18 — new enemy / interactive / item types load correctly
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def catacombs():
    return load_level(asset_path("maps", "level_07_cursed_catacombs.tmx"))


@pytest.fixture(scope="module")
def bridge():
    return load_level(asset_path("maps", "level_08_forsaken_bridge.tmx"))


@pytest.fixture(scope="module")
def spires():
    return load_level(asset_path("maps", "level_09_skybound_spires.tmx"))


def test_catacombs_has_archers(catacombs):
    _, _, enemies, *_ = catacombs
    assert any(isinstance(e, SkeletonArcher) for e in enemies)


def test_catacombs_has_bats(catacombs):
    _, _, enemies, *_ = catacombs
    assert any(isinstance(e, CaveBat) for e in enemies)


def test_catacombs_has_slimes(catacombs):
    _, _, enemies, *_ = catacombs
    assert any(isinstance(e, Slime) for e in enemies)


def test_catacombs_has_spitter(catacombs):
    _, _, enemies, *_ = catacombs
    assert any(isinstance(e, SpitterPlant) for e in enemies)


def test_bridge_has_mimic_chest(bridge):
    _, _, enemies, *_ = bridge
    assert any(isinstance(e, MimicChest) for e in enemies)


def test_bridge_has_moving_platforms(bridge):
    *_, interactives, _ = bridge
    assert any(isinstance(i, MovingPlatform) for i in interactives)


def test_bridge_has_springs(bridge):
    *_, interactives, _ = bridge
    assert any(isinstance(i, Spring) for i in interactives)


def test_bridge_has_gems(bridge):
    _, _, _, items, _, _ = bridge
    assert any(isinstance(i, Gem) for i in items)


def test_spires_is_taller_than_screen(spires):
    """Level 09 must be tall enough to require vertical camera scrolling."""
    tilemap, *_ = spires
    from saruman.config import INTERNAL_H
    assert tilemap.pixel_height > INTERNAL_H


def test_spires_has_many_moving_platforms(spires):
    *_, interactives, _ = spires
    platforms = [i for i in interactives if isinstance(i, MovingPlatform)]
    assert len(platforms) >= 5


# ---------------------------------------------------------------------------
# Level 10 — Goblin King's Throne (boss arena)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def throne():
    return load_level(asset_path("maps", "level_10_goblin_kings_throne.tmx"))


def test_level_10_loads(throne):
    tilemap, *_ = throne
    assert tilemap.pixel_width > 0
    assert tilemap.pixel_height > 0


def test_level_10_has_goblinKing(throne):
    _, _, enemies, *_ = throne
    assert any(isinstance(e, GoblinKing) for e in enemies)


def test_level_10_has_levelend(throne):
    *_, triggers = throne
    assert any(isinstance(t, LevelEndTrigger) for t in triggers)


def test_level_10_has_shieldknight_gatekeeper(throne):
    _, _, enemies, *_ = throne
    assert any(isinstance(e, ShieldKnight) for e in enemies)


def test_level_10_has_goblinkin_guards(throne):
    _, _, enemies, *_ = throne
    goblins = [e for e in enemies if isinstance(e, Goblinkin)]
    assert len(goblins) >= 2


def test_level_10_goblinKing_alive_on_load(throne):
    _, _, enemies, *_ = throne
    king = next(e for e in enemies if isinstance(e, GoblinKing))
    assert king.alive
    assert king._hp == GoblinKing._MAX_HP


# ---------------------------------------------------------------------------
# M14 Act 3 — new ashen biomes (levels 11–13) and the Emberfall Keep finale
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ashfall():
    return load_level(asset_path("maps", "level_11_ashfall_wastes.tmx"))


@pytest.fixture(scope="module")
def cinderwood():
    return load_level(asset_path("maps", "level_12_cinderwood_remains.tmx"))


@pytest.fixture(scope="module")
def emberfall():
    return load_level(asset_path("maps", "level_13_emberfall_keep.tmx"))


def test_ashfall_uses_unused_gem_colors(ashfall):
    """Act 3 finally spawns the previously-unused blue & green gems."""
    _, _, _, items, _, _ = ashfall
    colors = {i.color for i in items if isinstance(i, Gem)}
    assert "blue" in colors and "green" in colors


def test_cinderwood_is_vertical(cinderwood):
    tilemap, *_ = cinderwood
    from saruman.config import INTERNAL_H
    assert tilemap.pixel_height > INTERNAL_H


def test_emberfall_finale_has_night_king(emberfall):
    """The campaign finale is the new Night King boss — exactly one, no BossWargs."""
    _, _, enemies, *_ = emberfall
    kings = [e for e in enemies if isinstance(e, NightKing)]
    assert len(kings) == 1
    assert not any(isinstance(e, BossWarg) for e in enemies)


def test_emberfall_finale_has_level_end(emberfall):
    *_, triggers = emberfall
    assert any(isinstance(t, LevelEndTrigger) for t in triggers)


def test_emberfall_bonus_exceeds_throne(emberfall, throne):
    """Finale must reward more than the (now mid-game) Goblin King's Throne."""
    def first_bonus(triggers):
        for t in triggers:
            if isinstance(t, LevelEndTrigger):
                return t.score_bonus
        return 0
    assert first_bonus(emberfall[-1]) > first_bonus(throne[-1])
