"""Tests for the NightKing final boss (2-phase: summons then frost bolts)."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.entities.enemy import NightKing, Wraith
from saruman.entities.item import Gem
from saruman.entities.projectile import EnemyProjectile


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class _FloorTilemap:
    """Solid everywhere at/below the floor row so the boss stays grounded."""

    width  = 200
    height = 20

    def is_solid(self, tx: int, ty: int) -> bool:
        return ty >= 8


def _player_rect_left_of(boss: NightKing) -> pygame.Rect:
    return pygame.Rect(boss.rect.centerx - 80, boss.rect.y, 12, 16)


# ---------------------------------------------------------------------------
# Phase transition
# ---------------------------------------------------------------------------

def test_starts_in_phase_one_at_full_hp():
    nk = NightKing(0, 0)
    assert nk._hp == nk._MAX_HP
    assert nk.phase == 1


def test_switches_to_phase_two_below_threshold():
    nk = NightKing(0, 0)
    while nk._hp > nk._PHASE2_HP:
        nk.on_shot()
    assert nk.phase == 2
    assert nk.alive


def test_dies_when_hp_depleted():
    nk = NightKing(0, 0)
    killed = False
    for _ in range(nk._MAX_HP):
        killed = nk.on_stomped()
    assert killed
    assert not nk.alive


# ---------------------------------------------------------------------------
# Phase 1 — summons icy wraith minions
# ---------------------------------------------------------------------------

def test_phase_one_summons_wraith():
    nk = NightKing(0, 0)
    tm = _FloorTilemap()
    pr = _player_rect_left_of(nk)
    spawned: list = []
    for _ in range(nk._SPAWN_INTERVAL + 2):
        nk.update(tm, 1.0, pr)
        spawned.extend(nk.take_spawn())
    assert any(isinstance(e, Wraith) for e in spawned)


def test_phase_one_does_not_shoot():
    nk = NightKing(0, 0)
    tm = _FloorTilemap()
    pr = _player_rect_left_of(nk)
    for _ in range(nk._SHOT_INTERVAL * 3):
        nk.update(tm, 1.0, pr)
        assert nk.take_shot() is None


# ---------------------------------------------------------------------------
# Phase 2 — fires frost bolts
# ---------------------------------------------------------------------------

def test_phase_two_shoots_projectile():
    nk = NightKing(0, 0)
    while nk._hp > nk._PHASE2_HP:
        nk.on_shot()
    tm = _FloorTilemap()
    pr = _player_rect_left_of(nk)
    shots: list = []
    for _ in range(nk._SHOT_INTERVAL + 2):
        nk.update(tm, 1.0, pr)
        shot = nk.take_shot()
        if shot is not None:
            shots.append(shot)
    assert shots and all(isinstance(s, EnemyProjectile) for s in shots)


# ---------------------------------------------------------------------------
# Drop + knockback
# ---------------------------------------------------------------------------

def test_drops_gem_on_kill():
    nk = NightKing(0, 0)
    drops = nk.on_kill_drop()
    assert len(drops) == 1
    assert isinstance(drops[0], Gem)


def test_knockback_pushes_right_when_source_left():
    nk = NightKing(100, 0)
    nk.apply_knockback(0.0)
    assert nk.vel_x == 2.5
    assert nk.vel_y == -2.0


def test_knockback_pushes_left_when_source_right():
    nk = NightKing(0, 0)
    nk.apply_knockback(100.0)
    assert nk.vel_x == -2.5


def test_is_tougher_than_goblin_king():
    from saruman.entities.enemy import GoblinKing
    assert NightKing._MAX_HP > GoblinKing._MAX_HP
    assert NightKing.score_value > GoblinKing.score_value


def test_sprite_strip_loads():
    nk = NightKing(0, 0)
    surf = pygame.Surface((96, 96))
    assert nk._blit_strip(surf, 0, 0, "enemy_night_king", 0) is True
