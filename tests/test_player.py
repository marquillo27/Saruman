"""Tests for Player double-jump mechanic."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import JUMP_VEL, TILE_SIZE, SHIELD_CD, MOVE_SPEED
from saruman.core.input import Action, Input
from saruman.entities.player import Player


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class _FlatMap:
    MAP_W = 40
    MAP_H = 12

    @property
    def width(self):  return self.MAP_W
    @property
    def height(self): return self.MAP_H
    @property
    def pixel_width(self):  return self.MAP_W * TILE_SIZE
    @property
    def pixel_height(self): return self.MAP_H * TILE_SIZE

    def is_solid(self, tx, ty):
        return ty == 11 and 0 <= tx < self.MAP_W

    def draw(self, surface, cx, cy): pass


_MAP = _FlatMap()


def _inp_with(*actions: Action) -> Input:
    inp = Input()
    for a in actions:
        inp._pressed.add(a)
    return inp


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_player_starts_with_two_jumps_left():
    p = Player(32, 144)
    assert p._jumps_left == 2


# ---------------------------------------------------------------------------
# Double jump velocity and counter
# ---------------------------------------------------------------------------

def test_double_jump_decrements_jumps_left():
    p = Player(32, 0)
    p.on_ground = False
    p._coyote_timer = 0
    p._jumps_left = 1
    p.update(_inp_with(Action.JUMP), _MAP)
    assert p._jumps_left == 0


def test_double_jump_velocity_is_less_than_normal_jump():
    """Mid-air jump sets vel_y to JUMP_VEL * 0.85 (overwrite, not accumulate)."""
    p = Player(32, 0)
    p.on_ground = False
    p._coyote_timer = 0
    p._jumps_left = 1
    p.update(_inp_with(Action.JUMP), _MAP)
    assert abs(p.vel_y - JUMP_VEL * 0.85) < 0.01


def test_double_jump_gives_lower_arc_than_normal():
    assert JUMP_VEL * 0.85 > JUMP_VEL  # both negative; 0.85× is closer to zero


def test_third_jump_ignored_when_exhausted():
    """No jump when _jumps_left is 0 — vel_y stays positive (falling)."""
    p = Player(32, 0)
    p.on_ground = False
    p._coyote_timer = 0
    p._jumps_left = 0
    p.vel_y = 5.0  # already falling
    p.update(_inp_with(Action.JUMP), _MAP)
    # gravity is applied but jump is not; vel_y must be > JUMP_VEL * 0.85
    assert p.vel_y > JUMP_VEL * 0.85


def test_double_jump_not_possible_when_already_used_twice():
    p = Player(32, 0)
    p.on_ground = False
    p._coyote_timer = 0
    p._jumps_left = 0
    vel_before = p.vel_y
    p.update(_inp_with(Action.JUMP), _MAP)
    # vel_y only changes from gravity, not a jump assignment
    assert p.vel_y != JUMP_VEL * 0.85


# ---------------------------------------------------------------------------
# Ground jump uses first jump slot
# ---------------------------------------------------------------------------

def test_ground_jump_sets_jumps_left_to_one():
    """Normal jump from ground consumes one slot, leaving _jumps_left == 1."""
    p = Player(32, 160)  # standing height on FlatMap ground
    p.on_ground = True
    p._jumps_left = 2
    p.update(_inp_with(Action.JUMP), _MAP)
    assert p._jumps_left == 1


# ---------------------------------------------------------------------------
# Landing resets jump counter
# ---------------------------------------------------------------------------

def test_jumps_reset_when_on_ground_at_update_start():
    """If on_ground is True at the top of update(), _jumps_left becomes 2."""
    p = Player(32, 160)
    p.on_ground = True
    p._jumps_left = 0
    p.update(Input(), _MAP)
    assert p._jumps_left == 2


def test_jumps_remain_zero_while_airborne():
    """Exhausted jumps are not restored mid-air."""
    p = Player(32, 0)
    p.on_ground = False
    p._coyote_timer = 0
    p._jumps_left = 0
    p.update(Input(), _MAP)
    assert p._jumps_left == 0


# ---------------------------------------------------------------------------
# Melee swing
# ---------------------------------------------------------------------------

def test_swing_cooldown_starts_zero():
    p = Player(32, 144)
    assert p._swing_cooldown == 0


def test_swing_active_starts_zero():
    p = Player(32, 144)
    assert p._swing_active == 0


def test_try_swing_returns_true_first_call():
    p = Player(32, 144)
    assert p.try_swing() is True


def test_try_swing_returns_false_during_cooldown():
    p = Player(32, 144)
    p.try_swing()
    assert p.try_swing() is False


def test_swing_cooldown_set_after_swing():
    from saruman.config import SWING_COOLDOWN
    p = Player(32, 144)
    p.try_swing()
    assert p._swing_cooldown == SWING_COOLDOWN


def test_swing_active_set_to_2_after_swing():
    p = Player(32, 144)
    p.try_swing()
    assert p._swing_active == 2


def test_swing_rect_none_when_inactive():
    p = Player(32, 144)
    assert p.swing_rect is None


def test_swing_rect_facing_right_is_in_front():
    p = Player(32, 144)
    p.facing = 1
    p.try_swing()
    sr = p.swing_rect
    assert sr is not None
    assert sr.left == p.rect.right


def test_swing_rect_facing_left_is_in_front():
    p = Player(32, 144)
    p.facing = -1
    p.try_swing()
    sr = p.swing_rect
    assert sr is not None
    assert sr.right == p.rect.left


def test_swing_active_decrements_each_update():
    p = Player(32, 160)
    p.on_ground = True
    p.try_swing()
    assert p._swing_active == 2
    p.update(Input(), _MAP)
    assert p._swing_active == 1


def test_swing_rect_none_after_2_updates():
    p = Player(32, 160)
    p.on_ground = True
    p.try_swing()
    p.update(Input(), _MAP)
    p.update(Input(), _MAP)
    assert p.swing_rect is None


def test_swing_cooldown_decrements_each_update():
    from saruman.config import SWING_COOLDOWN
    p = Player(32, 160)
    p.on_ground = True
    p.try_swing()
    p.update(Input(), _MAP)
    assert p._swing_cooldown == SWING_COOLDOWN - 1


# ---------------------------------------------------------------------------
# Shield / parry
# ---------------------------------------------------------------------------

def test_shielding_starts_false():
    p = Player(32, 144)
    assert p._shielding is False


def _inp_held(*actions: Action) -> Input:
    """Input with actions in the _held (continuous) set — for shield / move tests."""
    inp = Input()
    for a in actions:
        inp._held.add(a)
        inp._pressed.add(a)
    return inp


def test_shielding_true_when_shield_held_and_no_cooldown():
    p = Player(32, 160)
    p.on_ground = True
    p._shield_cd = 0
    inp = _inp_held(Action.SHIELD)
    p.update(inp, _MAP)
    assert p.shielding is True


def test_shielding_false_during_cooldown():
    p = Player(32, 160)
    p.on_ground = True
    p._shield_cd = SHIELD_CD   # active cooldown
    inp = _inp_held(Action.SHIELD)
    p.update(inp, _MAP)
    assert p.shielding is False


def test_parry_hit_sets_shield_cd():
    p = Player(32, 144)
    p.parry_hit()
    assert p._shield_cd == SHIELD_CD


def test_shield_cd_decrements_each_update():
    p = Player(32, 160)
    p.on_ground = True
    p._shield_cd = 10
    p.update(Input(), _MAP)
    assert p._shield_cd == 9


def test_speed_reduced_while_shielding():
    """Player moves at half speed while shielding."""
    p = Player(32, 160)
    p.on_ground = True
    p._shield_cd = 0
    inp = _inp_held(Action.SHIELD, Action.MOVE_RIGHT)
    p.update(inp, _MAP)
    assert abs(p.vel_x - MOVE_SPEED * 0.5) < 0.01


def test_speed_normal_when_not_shielding():
    p = Player(32, 160)
    p.on_ground = True
    inp = _inp_held(Action.MOVE_RIGHT)
    p.update(inp, _MAP)
    assert abs(p.vel_x - MOVE_SPEED) < 0.01
