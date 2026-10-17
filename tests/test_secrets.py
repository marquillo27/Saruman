"""Tests for M20 hidden relics, fake walls and boss-locked exits."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.input import Input
from saruman.entities.item import Relic
from saruman.entities.trigger import LevelEndTrigger
from saruman.paths import asset_path
from saruman.world.level_loader import load_level
from saruman.world.world import World

ALL = [
    "level_01_greenshire_hills", "level_02_wolfwood", "level_03_glass_caverns",
    "level_04_sunken_mines", "level_11_ashfall_wastes", "level_12_cinderwood_remains",
    "level_05_ash_marshes", "level_10_goblin_kings_throne", "level_06_pale_tower",
    "level_09_skybound_spires", "level_08_forsaken_bridge", "level_07_cursed_catacombs",
    "level_13_emberfall_keep",
]


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def _world(stem: str) -> World:
    tm, spawn, enemies, items, inter, trig = load_level(asset_path("maps", stem + ".tmx"))
    return World(tm, spawn, enemies, items, trig, level_name=stem, interactives=inter)


@pytest.mark.parametrize("stem", ALL)
def test_every_level_hides_two_relics(stem):
    w = _world(stem)
    assert w.relics == (0, 2)


@pytest.mark.parametrize("stem", ALL)
def test_levels_are_long(stem):
    tm, *_ = load_level(asset_path("maps", stem + ".tmx"))
    assert tm.width >= 300


def test_fake_walls_are_walkable_but_marked():
    tm, *_ = load_level(asset_path("maps", "level_01_greenshire_hills.tmx"))
    cells = [(tx, ty) for ty in range(tm.height) for tx in range(tm.width) if tm.is_fake(tx, ty)]
    assert cells
    assert not any(tm.is_solid(tx, ty) for tx, ty in cells)


def test_relic_pickup_counts_and_scores():
    w = _world("level_01_greenshire_hills")
    relic = next(i for i in w._items if isinstance(i, Relic))
    w.player.x = relic.x
    w.player.y = relic.y + relic.H - w.player.H       # standing on the relic's floor
    w.update(Input(), 1 / 60)
    assert w.relics[0] == 1
    assert w.score >= Relic.score_value


def test_fake_wall_overlay_draws_and_reveals():
    w = _world("level_01_greenshire_hills")
    s = pygame.Surface((INTERNAL_W, INTERNAL_H))
    w._tilemap.draw_fake(s, 0, 0, reveal=False)
    w._tilemap.draw_fake(s, 0, 0, reveal=True)
    assert w._tilemap._fake_overlay is not None


def test_boss_level_exit_locked_until_boss_dies():
    w = _world("level_04_sunken_mines")
    exit_t = next(t for t in w._triggers if isinstance(t, LevelEndTrigger))
    w.player.x, w.player.y = exit_t.rect.x, exit_t.rect.y
    w.update(Input(), 1 / 60)
    assert not w.is_level_complete
    for e in w._enemies:
        if e.is_boss:
            e.alive = False
    w.player.x, w.player.y = exit_t.rect.x, exit_t.rect.y
    w.update(Input(), 1 / 60)
    assert w.is_level_complete


def test_wolfwood_hides_warp_to_glass_caverns():
    from saruman.entities.trigger import WarpTrigger
    *_, trig = load_level(asset_path("maps", "level_02_wolfwood.tmx"))
    assert any(isinstance(t, WarpTrigger) and t.target_level == "level_03_glass_caverns"
               for t in trig)
