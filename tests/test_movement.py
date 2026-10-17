"""Tests for the M17 movement feel: run acceleration, air control, jump arc."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import GRAVITY, MOVE_SPEED, PLAYER_MAX_FALL, RUN_ACCEL, TILE_SIZE
from saruman.core.input import Action, Input
from saruman.entities.player import Player


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class _FlatMap:
    """Wide map with a floor at row 40 (lots of headroom for jump arcs)."""
    width, height = 200, 42
    pixel_width, pixel_height = 200 * TILE_SIZE, 42 * TILE_SIZE
    FLOOR = 40

    def is_solid(self, tx, ty):
        return ty == self.FLOOR


_MAP = _FlatMap()
_FLOOR_Y = _FlatMap.FLOOR * TILE_SIZE - Player.H


def _grounded() -> Player:
    p = Player(64, _FLOOR_Y)
    p.update(Input(), _MAP)   # settle on the floor
    return p


def _hold(*actions: Action) -> Input:
    inp = Input()
    inp._held.update(actions)
    return inp


def _step(p: Player, inp: Input, frames: int = 1) -> None:
    for _ in range(frames):
        p.update(inp, _MAP)
        inp.clear_frame()


def _jump_height(hold_frames: int) -> float:
    """Peak height in px of a ground jump with jump held for `hold_frames`."""
    p = _grounded()
    inp = _hold(Action.JUMP)
    inp._pressed.add(Action.JUMP)
    start, peak = p.y, p.y
    for f in range(120):
        if f == hold_frames:
            inp._held.discard(Action.JUMP)
        _step(p, inp)
        peak = min(peak, p.y)
        if p.on_ground and f > 2:
            break
    return start - peak


# --- Running -----------------------------------------------------------------

def test_run_accelerates_instead_of_snapping():
    p = _grounded()
    _step(p, _hold(Action.MOVE_RIGHT))
    assert 0 < p.vel_x < MOVE_SPEED


def test_run_reaches_top_speed_within_fifteen_frames():
    p = _grounded()
    _step(p, _hold(Action.MOVE_RIGHT), 15)
    assert p.vel_x == pytest.approx(MOVE_SPEED)


def test_release_brakes_to_stop_with_short_slide():
    p = _grounded()
    _step(p, _hold(Action.MOVE_RIGHT), 15)
    x0 = p.x
    _step(p, Input(), 1)
    assert p.vel_x > 0                       # still sliding one frame later
    _step(p, Input(), 15)
    assert p.vel_x == 0.0
    assert 0 < p.x - x0 < TILE_SIZE          # slide shorter than one tile


def test_turning_around_brakes_harder_than_accelerating():
    p = _grounded()
    _step(p, _hold(Action.MOVE_RIGHT), 15)
    v0 = p.vel_x
    _step(p, _hold(Action.MOVE_LEFT))
    assert v0 - p.vel_x > RUN_ACCEL + 1e-6    # more than a plain accel step
    assert p.facing == -1


def test_air_keeps_momentum_more_than_ground():
    ground = _grounded()
    _step(ground, _hold(Action.MOVE_RIGHT), 15)
    _step(ground, Input())

    air = Player(64, 100)
    air.vel_x = MOVE_SPEED
    _step(air, Input())
    assert air.vel_x > ground.vel_x


def test_knockback_above_top_speed_bleeds_off():
    p = _grounded()
    p.vel_x = -6.0
    _step(p, _hold(Action.MOVE_LEFT))
    assert -6.0 < p.vel_x < -MOVE_SPEED


# --- Jump arc ----------------------------------------------------------------

def test_full_jump_height_close_to_original():
    # Old arc peaked at ~95 px; existing levels are built around that, so the
    # gentler jump stays within a few pixels (double jump covers the rest).
    assert 80 <= _jump_height(hold_frames=60) <= 92


def test_tap_jump_is_much_lower_than_held():
    tap, full = _jump_height(1), _jump_height(60)
    assert tap < full * 0.5
    assert tap >= TILE_SIZE                  # still clears a one-tile bump


def test_fall_is_faster_than_rise():
    p = Player(64, 100)
    p.vel_y = 2.0
    _step(p, Input())
    fall_g = p.vel_y - 2.0
    p2 = Player(64, 100)
    p2.vel_y = -5.0
    _step(p2, _hold(Action.JUMP))
    rise_g = p2.vel_y + 5.0
    assert fall_g > rise_g


def test_fall_speed_is_capped():
    p = Player(64, 0)
    _step(p, Input(), 60)
    assert p.vel_y <= PLAYER_MAX_FALL


def test_spring_launch_not_cut_by_released_jump():
    p = Player(64, 300)
    p.spring_launch(-13.0)
    _step(p, Input())                        # jump not held
    assert p.vel_y == pytest.approx(-13.0 + GRAVITY)


# --- Wall slide / wall jump -------------------------------------------------

class _WallMap(_FlatMap):
    """Floor plus a tall wall column at tile x=10."""
    WALL_X = 10

    def is_solid(self, tx, ty):
        return ty == self.FLOOR or (tx == self.WALL_X and ty < self.FLOOR)


_WALL = _WallMap()


def _against_wall() -> Player:
    """Airborne player touching the wall's left face, falling."""
    p = Player(_WallMap.WALL_X * TILE_SIZE - Player.W, 300)
    p.vel_y = 4.0
    p.update(_hold(Action.MOVE_RIGHT), _WALL)
    return p


def test_wall_slide_caps_fall_speed():
    from saruman.config import WALL_SLIDE_SPEED
    p = _against_wall()
    for _ in range(20):
        p.update(_hold(Action.MOVE_RIGHT), _WALL)
    assert p.wall_sliding
    assert p.vel_y <= WALL_SLIDE_SPEED


def test_no_slide_without_pressing_into_wall():
    p = _against_wall()
    for _ in range(20):
        p.update(Input(), _WALL)
    assert not p.wall_sliding


def test_wall_jump_pushes_away_and_up():
    p = _against_wall()
    inp = _hold(Action.MOVE_RIGHT, Action.JUMP)
    inp._pressed.add(Action.JUMP)
    p.update(inp, _WALL)
    assert p.vel_y < 0
    assert p.vel_x < 0          # away from the wall on the right
    assert p.facing == -1


def test_wall_jump_refreshes_double_jump():
    p = _against_wall()
    p._jumps_left = 0
    inp = _hold(Action.JUMP)
    inp._pressed.add(Action.JUMP)
    p.update(inp, _WALL)
    assert p._jumps_left == 1


def test_wall_jump_locks_steering_briefly():
    p = _against_wall()
    inp = _hold(Action.MOVE_RIGHT, Action.JUMP)
    inp._pressed.add(Action.JUMP)
    p.update(inp, _WALL)
    inp.clear_frame()
    p.update(inp, _WALL)        # still holding toward the wall
    assert p.vel_x < 0
