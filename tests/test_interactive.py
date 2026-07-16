"""Tests for Spring and MovingPlatform interactive entities."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.entities.interactive import MovingPlatform, Spike, Spring
from saruman.entities.player import Player
from saruman.physics.collision import platform_carry


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


# ---------------------------------------------------------------------------
# Spring
# ---------------------------------------------------------------------------

def test_spring_starts_inactive():
    s = Spring(100.0, 100.0)
    assert s._activation == 0
    assert s.alive


def test_spring_triggered_sets_activation():
    s = Spring(0.0, 0.0)
    s.trigger()
    assert s._activation > 0


def test_spring_activation_decays_each_update():
    s = Spring(0.0, 0.0)
    s.trigger()
    a0 = s._activation
    s.update(1 / 60)
    assert s._activation == a0 - 1


def test_spring_no_overlap_when_player_above_rising():
    """Player must be falling (vel_y > 0) to engage the spring."""
    s = Spring(50.0, 100.0)
    p = Player(50.0, 90.0)
    p.vel_y = -5.0   # going up — not landing
    assert not s.player_overlap_from_above(p)


def test_spring_overlap_detected_when_falling_into_top():
    s = Spring(50.0, 100.0)   # rect (50, 100, 12, 6)
    p = Player(50.0, 85.0)    # bottom = 101 → overlaps spring top by 1px
    p.vel_y = 4.0
    assert s.player_overlap_from_above(p)


def test_spring_no_overlap_when_far_below():
    s = Spring(50.0, 100.0)
    p = Player(50.0, 200.0)   # well below
    p.vel_y = 2.0
    assert not s.player_overlap_from_above(p)


def test_player_spring_launch_sets_velocity():
    p = Player(0.0, 0.0)
    p.vel_y = 3.0     # falling
    p._jumps_left = 0
    p.spring_launch(-13.0)
    assert p.vel_y == -13.0
    assert p._jumps_left == 1


# ---------------------------------------------------------------------------
# MovingPlatform
# ---------------------------------------------------------------------------

def test_moving_platform_starts_at_spawn():
    plat = MovingPlatform(100.0, 100.0, axis="x", range_px=64.0)
    assert plat.x == 100.0 and plat.y == 100.0


def test_horizontal_platform_drift_within_range():
    plat = MovingPlatform(100.0, 100.0, axis="x", range_px=64.0)
    seen_x = set()
    for _ in range(plat.PERIOD):
        plat.update(1 / 60)
        seen_x.add(int(plat.x))
    assert 100 in seen_x
    assert max(seen_x) <= 100 + 64
    assert min(seen_x) >= 100   # cosine LERP goes 0..1..0, so never below spawn


def test_horizontal_platform_returns_to_spawn():
    plat = MovingPlatform(50.0, 50.0, axis="x", range_px=80.0)
    for _ in range(plat.PERIOD):
        plat.update(1 / 60)
    # After one full PERIOD, the cosine returns to phase 0
    assert abs(plat.x - 50.0) < 1.0


def test_vertical_platform_moves_on_y():
    plat = MovingPlatform(0.0, 100.0, axis="y", range_px=48.0)
    initial_y = plat.y
    plat.update(1 / 60)
    plat.update(1 / 60)
    plat.update(1 / 60)
    assert plat.y != initial_y
    assert plat.x == 0.0   # x stays put


def test_platform_records_previous_position():
    plat = MovingPlatform(0.0, 0.0, axis="x", range_px=32.0)
    plat.update(1 / 60)
    p1 = plat.x
    plat.update(1 / 60)
    assert plat.prev_x == p1


def test_platform_delta_matches_position_change():
    plat = MovingPlatform(0.0, 0.0, axis="x", range_px=32.0)
    plat.update(1 / 60)
    plat.update(1 / 60)
    assert abs(plat.delta_x - (plat.x - plat.prev_x)) < 0.001


# ---------------------------------------------------------------------------
# platform_carry
# ---------------------------------------------------------------------------

def test_carry_snaps_player_to_platform_top():
    plat = MovingPlatform(0.0, 100.0, axis="x", range_px=64.0)
    p    = Player(8.0, 86.0)   # bottom = 102, within (99, 104) window
    p.vel_y = 2.0
    platform_carry(p, [plat])
    assert p.on_ground
    assert p.vel_y == 0.0
    # Player bottom should now align with platform top
    assert abs((p.y + p.H) - plat.rect.top) < 2


def test_carry_skips_when_player_below_platform():
    plat = MovingPlatform(0.0, 100.0, axis="x", range_px=64.0)
    p    = Player(8.0, 150.0)
    p.vel_y = 2.0
    on_ground_before = p.on_ground
    platform_carry(p, [plat])
    # Player is below; carry should not engage
    assert p.on_ground == on_ground_before


def test_carry_skips_when_player_jumping_upward():
    plat = MovingPlatform(0.0, 100.0, axis="x", range_px=64.0)
    p    = Player(8.0, 84.0)
    p.vel_y = -5.0   # jumping up
    platform_carry(p, [plat])
    # Going up — must not be snapped
    assert p.vel_y == -5.0


# ---------------------------------------------------------------------------
# Spike
# ---------------------------------------------------------------------------

def test_spike_alive_always_true():
    s = Spike(50.0, 100.0)
    assert s.alive is True


def test_spike_rect_correct_dimensions():
    s = Spike(50.0, 100.0)
    r = s.rect
    assert r.width  == Spike.W
    assert r.height == Spike.H
    assert r.left   == 50
    assert r.top    == 100


def test_spike_update_is_noop():
    """update() must not raise and must not change position."""
    s = Spike(50.0, 100.0)
    s.update(1 / 60)
    assert s.x == 50.0
    assert s.y == 100.0


def test_spike_alive_after_update():
    s = Spike(50.0, 100.0)
    s.update(1 / 60)
    assert s.alive is True


def test_spike_draw_does_not_raise():
    """draw() with a fallback surface must not crash."""
    s   = Spike(0.0, 0.0)
    srf = pygame.Surface((320, 180))
    s.draw(srf, 0, 0)   # should not raise
