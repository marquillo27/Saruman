"""Tests for the consolidated Enemy base helpers and knockback.

Covers the refactored shared logic: `_turn_at_cliff` (patrol consolidation),
`_blit_strip` (draw-fallback consolidation), and the `apply_knockback`
overrides on the bosses.
"""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import TILE_SIZE
from saruman.entities.enemy import BossWarg, GoblinKing, Goblinkin


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class _FakeTilemap:
    """is_solid() returns True only for the explicitly-listed (tx, ty) tiles."""

    def __init__(self, solid: set[tuple[int, int]]) -> None:
        self._solid = solid

    def is_solid(self, tx: int, ty: int) -> bool:
        return (tx, ty) in self._solid


def _grounded_goblin(tx: int, ty: int) -> Goblinkin:
    g = Goblinkin(tx * TILE_SIZE, ty * TILE_SIZE)
    g.on_ground = True
    return g


# ---------------------------------------------------------------------------
# _turn_at_cliff
# ---------------------------------------------------------------------------

def test_turn_at_cliff_reverses_when_no_ground_ahead():
    g = _grounded_goblin(5, 5)
    g.facing = 1
    foot_ty = g.rect.bottom // TILE_SIZE
    # No solid tiles anywhere ahead → should flip.
    tm = _FakeTilemap(set())
    g._turn_at_cliff(tm)
    assert g.facing == -1
    assert foot_ty == g.rect.bottom // TILE_SIZE  # sanity: unchanged position


def test_turn_at_cliff_keeps_facing_over_solid_ground():
    g = _grounded_goblin(5, 5)
    g.facing = 1
    foot_ty  = g.rect.bottom // TILE_SIZE
    ahead_tx = g.rect.right // TILE_SIZE
    tm = _FakeTilemap({(ahead_tx, foot_ty)})
    g._turn_at_cliff(tm)
    assert g.facing == 1


def test_turn_at_cliff_checks_left_tile_when_facing_left():
    g = _grounded_goblin(5, 5)
    g.facing = -1
    foot_ty  = g.rect.bottom // TILE_SIZE
    ahead_tx = (g.rect.left - 1) // TILE_SIZE
    tm = _FakeTilemap({(ahead_tx, foot_ty)})
    g._turn_at_cliff(tm)
    assert g.facing == -1  # ground present on the left → keep heading left


def test_turn_at_cliff_noop_while_airborne():
    g = _grounded_goblin(5, 5)
    g.on_ground = False
    g.facing = 1
    tm = _FakeTilemap(set())  # nothing solid, but airborne → must not flip
    g._turn_at_cliff(tm)
    assert g.facing == 1


# ---------------------------------------------------------------------------
# _blit_strip — fallback contract
# ---------------------------------------------------------------------------

def test_blit_strip_returns_false_for_missing_asset():
    g = Goblinkin(0, 0)
    surf = pygame.Surface((64, 64))
    assert g._blit_strip(surf, 0, 0, "definitely_missing_asset_xyz", 0) is False


def test_blit_strip_returns_true_for_real_asset():
    g = Goblinkin(0, 0)
    surf = pygame.Surface((64, 64))
    # enemy_goblinkin_strip.png ships in assets/sprites.
    assert g._blit_strip(surf, 0, 0, "enemy_goblinkin", 0) is True


# ---------------------------------------------------------------------------
# apply_knockback — BossWarg
# ---------------------------------------------------------------------------

def test_base_apply_knockback_is_noop():
    g = Goblinkin(100, 0)
    g.apply_knockback(0.0)
    assert g.vel_x == 0.0
    assert g.vel_y == 0.0


def test_bosswarg_knockback_pushes_away_from_source_on_right():
    b = BossWarg(100, 0)
    b.apply_knockback(0.0)            # source to the left of boss
    assert b.vel_x == BossWarg._KNOCKBACK_VEL_X   # pushed right (positive)
    assert b.vel_y == BossWarg._KNOCKBACK_VEL_Y
    assert b._knockback_frames == BossWarg._KNOCKBACK_FRAMES


def test_bosswarg_knockback_pushes_away_from_source_on_left():
    b = BossWarg(0, 0)
    b.apply_knockback(100.0)          # source to the right of boss
    assert b.vel_x == -BossWarg._KNOCKBACK_VEL_X  # pushed left (negative)


# ---------------------------------------------------------------------------
# apply_knockback — GoblinKing
# ---------------------------------------------------------------------------

def test_goblinking_knockback_pushes_right_when_source_left():
    gk = GoblinKing(100, 0)
    gk.apply_knockback(0.0)
    assert gk.vel_x == 2.5
    assert gk.vel_y == -2.0


def test_goblinking_knockback_pushes_left_when_source_right():
    gk = GoblinKing(0, 0)
    gk.apply_knockback(100.0)
    assert gk.vel_x == -2.5
