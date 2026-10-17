"""Tests for level exits: unjumpable hit zone and the visible beacon."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.entities.trigger import LevelEndTrigger, WarpTrigger


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_exit_zone_extends_above_the_map():
    t = LevelEndTrigger(100, 144, 16, 32)
    high_jump = pygame.Rect(102, -60, 10, 16)    # player above the top of the map
    assert not high_jump.colliderect(t.rect)
    assert high_jump.colliderect(t.hit_rect)


def test_exit_zone_does_not_extend_below():
    t = LevelEndTrigger(100, 144, 16, 32)
    assert t.hit_rect.bottom == t.rect.bottom


def test_warp_zone_unchanged():
    t = WarpTrigger(100, 144, 16, 32, "level_03_glass_caverns")
    assert t.hit_rect == t.rect


def test_world_fires_exit_when_jumping_over_it():
    from saruman.paths import asset_path
    from saruman.world.level_loader import load_level
    from saruman.world.world import World
    from saruman.core.input import Input

    tm, spawn, enemies, items, inter, triggers = load_level(
        asset_path("maps", "level_01_greenshire_hills.tmx"))
    w = World(tm, spawn, [], [], triggers, level_name="level_01_greenshire_hills")
    exit_rect = next(t for t in triggers if isinstance(t, LevelEndTrigger)).rect
    w.player.x, w.player.y = exit_rect.x + 2, -40.0
    w.update(Input(), 1 / 60)
    assert w.is_level_complete


def test_beacon_draws_without_error():
    from saruman.paths import asset_path
    from saruman.world.level_loader import load_level
    from saruman.world.world import World

    tm, spawn, enemies, items, inter, triggers = load_level(
        asset_path("maps", "level_01_greenshire_hills.tmx"))
    w = World(tm, spawn, [], [], triggers, level_name="level_01_greenshire_hills")
    w._draw_exit_beacons(pygame.Surface((INTERNAL_W, INTERNAL_H)))
