"""Tests for stackable lives (Hearts up to MAX_LIVES) and HUD heart display."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W, MAX_LIVES, PLAYER_LIVES, TILE_SIZE
from saruman.entities.item import Heart
from saruman.ui.hud import HUD
from saruman.world.world import World


class _FlatMap:
    MAP_W = 40
    MAP_H = 12

    @property
    def width(self) -> int:  return self.MAP_W
    @property
    def height(self) -> int: return self.MAP_H
    @property
    def pixel_width(self) -> int:  return self.MAP_W * TILE_SIZE
    @property
    def pixel_height(self) -> int: return self.MAP_H * TILE_SIZE

    def is_solid(self, tx: int, ty: int) -> bool:
        return ty == 11 and 0 <= tx < self.MAP_W

    def draw(self, surface, cx, cy) -> None:
        pass


_SPAWN = (32.0, 144.0)


def _make_world() -> World:
    return World(_FlatMap(), _SPAWN, [], [], [], None)


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def _collect_heart(w: World) -> None:
    w._items = [Heart(w._player.x, w._player.y)]
    w._check_player_items()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_max_lives_above_default():
    assert MAX_LIVES > PLAYER_LIVES
    assert MAX_LIVES == 7


# ---------------------------------------------------------------------------
# Heart stacking
# ---------------------------------------------------------------------------

def test_single_heart_increments_one():
    w = _make_world()
    w._lives = PLAYER_LIVES
    _collect_heart(w)
    assert w.lives == PLAYER_LIVES + 1


def test_hearts_stack_up_to_max():
    w = _make_world()
    w._lives = PLAYER_LIVES
    for _ in range(10):     # more than enough to reach the cap
        _collect_heart(w)
    assert w.lives == MAX_LIVES


def test_heart_capped_at_max():
    w = _make_world()
    w._lives = MAX_LIVES
    _collect_heart(w)
    assert w.lives == MAX_LIVES


def test_heart_does_not_exceed_max_by_one():
    w = _make_world()
    w._lives = MAX_LIVES - 1
    _collect_heart(w)
    assert w.lives == MAX_LIVES
    _collect_heart(w)
    assert w.lives == MAX_LIVES


# ---------------------------------------------------------------------------
# HUD drawing with extended life counts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lives", [0, 1, 3, 5, 7, 99])
def test_hud_draws_any_life_count(lives):
    surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
    HUD().draw(surf, lives, 1234, 0)   # must not raise
