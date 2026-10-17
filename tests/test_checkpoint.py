"""Tests for checkpoints and pit-fall respawn."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import PLAYER_LIVES, TILE_SIZE
from saruman.core.input import Input
from saruman.entities.interactive import Checkpoint
from saruman.world.world import World


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class _PitMap:
    """Floor everywhere except a pit at tiles 20-24."""
    width, height = 60, 12
    pixel_width, pixel_height = 60 * TILE_SIZE, 12 * TILE_SIZE

    def is_solid(self, tx, ty):
        return ty == 11 and not (20 <= tx <= 24)

    def draw(self, surface, cx, cy):
        pass


def _world(interactives=()) -> World:
    return World(_PitMap(), (32.0, 160.0), [], [], [], interactives=list(interactives))


def _fall(w: World) -> None:
    w.player.x, w.player.y = 22 * TILE_SIZE, w._tilemap.pixel_height + 40
    w.update(Input(), 1 / 60)


def test_pit_costs_exactly_one_life():
    w = _world()
    _fall(w)
    assert w.lives == PLAYER_LIVES - 1
    for _ in range(120):                       # no further drain afterwards
        w.update(Input(), 1 / 60)
    assert w.lives == PLAYER_LIVES - 1


def test_pit_respawns_at_level_start_without_checkpoint():
    w = _world()
    _fall(w)
    assert w.player.rect.bottom == 176         # spawn marker feet line
    assert w.player.x < 64


def test_touching_checkpoint_lights_it_and_moves_respawn():
    cp = Checkpoint(40 * TILE_SIZE, 176 - Checkpoint.H)
    w = _world([cp])
    w.player.x, w.player.y = cp.x, cp.y
    w.update(Input(), 1 / 60)
    assert cp.lit
    _fall(w)
    assert abs(w.player.rect.centerx - cp.rect.centerx) <= 1
    assert w.player.rect.bottom == cp.rect.bottom


def test_respawn_gives_invulnerability():
    w = _world()
    _fall(w)
    assert w.player.hit_invincible


def test_last_life_pit_is_game_over():
    w = _world()
    w._lives = 1
    _fall(w)
    for _ in range(60):
        w.update(Input(), 1 / 60)
    assert w.is_game_over


def test_checkpoint_draws_lit_and_unlit():
    cp = Checkpoint(0, 0)
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    cp.draw(s, 20, 20)
    cp.light()
    cp.update(1 / 60)
    cp.draw(s, 20, 20)
    assert not cp.light()                      # only lights once
