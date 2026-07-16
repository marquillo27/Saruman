"""Tests for the random bonus power-ups: shield, nuke, fruit-transform."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import BONUS_FRUIT_FRAMES, BONUS_SHIELD_FRAMES, TILE_SIZE
from saruman.core.input import Input
from saruman.entities.enemy import Goblinkin, NightKing
from saruman.entities.item import FruitPickup, NukePickup, ShieldPickup
from saruman.world.world import World


class _FlatMap:
    MAP_W = 60
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


def _make_world(enemies=None, items=None) -> World:
    return World(_FlatMap(), _SPAWN, enemies or [], items or [], [], None)


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def inp() -> Input:
    return Input()


# ---------------------------------------------------------------------------
# Shield bonus — timed invulnerability
# ---------------------------------------------------------------------------

def test_grant_invuln_makes_player_invincible():
    w = _make_world()
    w._player.grant_invuln(BONUS_SHIELD_FRAMES)
    assert w._player.invincible is True


def test_shield_blocks_normal_damage():
    w = _make_world()
    before = w.lives
    w._player.grant_invuln(BONUS_SHIELD_FRAMES)
    w._apply_damage()
    assert w.lives == before


def test_void_fall_bypasses_shield():
    w = _make_world()
    before = w.lives
    w._player.grant_invuln(BONUS_SHIELD_FRAMES)
    w._apply_damage(ignore_shield=True)
    assert w.lives == before - 1


def test_void_fall_still_respects_hit_iframes():
    """ignore_shield bypasses the bonus shield but NOT the brief post-hit i-frames."""
    w = _make_world()
    w._player._hit_timer = 60
    before = w.lives
    w._apply_damage(ignore_shield=True)
    assert w.lives == before


def test_bonus_invuln_decrements_each_update(inp):
    w = _make_world()
    w._player.grant_invuln(30)
    w.update(inp, 1 / 60)
    assert w._player._bonus_invuln == 29


# ---------------------------------------------------------------------------
# Nuke bonus — clears non-boss enemies, spares bosses
# ---------------------------------------------------------------------------

def test_nuke_kills_all_nonboss():
    g1, g2 = Goblinkin(150.0, 150.0), Goblinkin(180.0, 150.0)
    w = _make_world(enemies=[g1, g2])
    w._detonate_nuke()
    assert not g1.alive and not g2.alive


def test_nuke_spares_boss():
    boss = NightKing(300.0, 144.0)
    grunt = Goblinkin(150.0, 150.0)
    w = _make_world(enemies=[boss, grunt])
    w._detonate_nuke()
    assert boss.alive
    assert not grunt.alive


def test_nuke_awards_score():
    g = Goblinkin(150.0, 150.0)
    w = _make_world(enemies=[g])
    w._detonate_nuke()
    assert w.score == Goblinkin.score_value


def test_nuke_sets_flash_signal():
    w = _make_world(enemies=[Goblinkin(150.0, 150.0)])
    w._detonate_nuke()
    assert w.nuke_flash is True


def test_nuke_dead_enemies_filtered_next_update(inp):
    g = Goblinkin(150.0, 150.0)
    w = _make_world(enemies=[g])
    w._detonate_nuke()
    w.update(inp, 1 / 60)
    assert g not in w._enemies


# ---------------------------------------------------------------------------
# Fruit bonus — enemies harmless + edible, bosses unaffected
# ---------------------------------------------------------------------------

def test_fruit_contact_eats_nonboss_without_damage():
    g = Goblinkin(32.0, 145.0)
    w = _make_world(enemies=[g])
    w._fruit_timer = BONUS_FRUIT_FRAMES
    w._player.x, w._player.y, w._player.vel_y = 32.0, 145.0, 0.0
    before = w.lives
    w._check_player_enemy()
    assert not g.alive
    assert w.lives == before
    assert w.score == Goblinkin.score_value


def test_fruit_mode_boss_still_damages_player():
    boss = NightKing(32.0, 145.0)
    w = _make_world(enemies=[boss])
    w._fruit_timer = BONUS_FRUIT_FRAMES
    w._player.x, w._player.y, w._player.vel_y = 32.0, 145.0, 0.0
    w._player._hit_timer = 0
    before = w.lives
    w._check_player_enemy()
    assert boss.alive
    assert w.lives == before - 1


def test_fruit_timer_decrements_each_update(inp):
    w = _make_world()
    w._fruit_timer = 10
    w.update(inp, 1 / 60)
    assert w._fruit_timer == 9


def test_normal_enemy_damages_when_fruit_inactive():
    g = Goblinkin(32.0, 145.0)
    w = _make_world(enemies=[g])
    w._fruit_timer = 0
    w._player.x, w._player.y, w._player.vel_y = 32.0, 145.0, 0.0
    w._player._hit_timer = 0
    before = w.lives
    w._check_player_enemy()
    assert w.lives == before - 1


# ---------------------------------------------------------------------------
# Random spawn scheduling
# ---------------------------------------------------------------------------

def test_bonus_timer_initialized_positive():
    w = _make_world()
    assert w._bonus_timer > 0


def test_bonus_timer_decrements_each_update(inp):
    w = _make_world()
    start = w._bonus_timer
    w.update(inp, 1 / 60)
    assert w._bonus_timer == start - 1


def test_bonus_spawns_when_timer_elapses(inp):
    w = _make_world()
    w._bonus_timer = 1
    before = len(w._items)
    w.update(inp, 1 / 60)
    assert len(w._items) == before + 1
    assert w._bonus_timer > 0   # rescheduled


def test_spawned_bonus_is_a_bonus_type(inp):
    w = _make_world()
    w._bonus_timer = 1
    w.update(inp, 1 / 60)
    assert any(isinstance(i, (ShieldPickup, NukePickup, FruitPickup)) for i in w._items)


# ---------------------------------------------------------------------------
# Pickup dispatch
# ---------------------------------------------------------------------------

def test_shield_pickup_grants_invuln():
    w = _make_world(items=[ShieldPickup(_SPAWN[0], _SPAWN[1])])
    w._check_player_items()
    assert w._player.invincible


def test_nuke_pickup_detonates():
    g = Goblinkin(150.0, 150.0)
    w = _make_world(enemies=[g], items=[NukePickup(_SPAWN[0], _SPAWN[1])])
    w._check_player_items()
    assert not g.alive


def test_fruit_pickup_sets_timer():
    w = _make_world(items=[FruitPickup(_SPAWN[0], _SPAWN[1])])
    w._check_player_items()
    assert w._fruit_timer == BONUS_FRUIT_FRAMES


def test_bonus_pickups_consumed():
    w = _make_world(items=[ShieldPickup(_SPAWN[0], _SPAWN[1])])
    w._check_player_items()
    assert all(not i.alive for i in w._items)


# ---------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["item_shield", "item_nuke", "item_fruit"])
def test_bonus_sprites_load(name):
    from saruman.core.assets import get_sprite
    assert get_sprite(name) is not None
