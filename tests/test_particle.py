"""Tests for the particle system."""
from __future__ import annotations

import math

import pytest

from saruman.world.particle import Particle, burst


# ---------------------------------------------------------------------------
# Particle lifecycle
# ---------------------------------------------------------------------------

def test_particle_alive_at_start():
    p = Particle(0, 0, 1.0, 0.0, (255, 0, 0), life=10)
    assert p.alive


def test_particle_dies_when_life_exhausted():
    p = Particle(0, 0, 0.0, 0.0, (255, 0, 0), life=3)
    for _ in range(3):
        p.update()
    assert not p.alive


def test_particle_still_alive_before_last_tick():
    p = Particle(0, 0, 0.0, 0.0, (255, 0, 0), life=3)
    p.update()
    p.update()
    assert p.alive  # one tick remaining


def test_particle_x_advances_by_vel_x():
    p = Particle(10.0, 0.0, 3.0, 0.0, (255, 255, 0), life=20)
    p.update()
    assert p.x == pytest.approx(13.0)


def test_particle_y_advances_by_vel_y_plus_gravity():
    p = Particle(0.0, 0.0, 0.0, 0.0, (255, 255, 0), life=20)
    p.update()
    # vel_y becomes GRAVITY after first tick, then y += that
    assert p.y == pytest.approx(Particle.GRAVITY)


def test_gravity_accelerates_particle():
    p = Particle(0, 0, 0.0, 0.0, (255, 255, 0), life=20)
    p.update()
    vy1 = p.vel_y
    p.update()
    vy2 = p.vel_y
    assert vy2 > vy1


def test_max_life_unchanged_after_updates():
    p = Particle(0, 0, 0.0, 0.0, (255, 255, 0), life=15)
    for _ in range(5):
        p.update()
    assert p.max_life == 15


# ---------------------------------------------------------------------------
# burst() factory
# ---------------------------------------------------------------------------

def test_burst_returns_correct_count():
    parts = burst(100, 80, (255, 200, 0), count=12)
    assert len(parts) == 12


def test_burst_all_alive():
    parts = burst(0, 0, (255, 0, 0), count=8)
    assert all(p.alive for p in parts)


def test_burst_all_start_at_origin():
    cx, cy = 50.0, 75.0
    parts = burst(cx, cy, (255, 255, 0), count=6)
    for p in parts:
        assert p.x == pytest.approx(cx)
        assert p.y == pytest.approx(cy)


def test_burst_velocities_are_varied():
    parts = burst(0, 0, (255, 255, 0), count=10, speed=3.0)
    vx_vals = [p.vel_x for p in parts]
    # Not all identical (radial spread)
    assert len(set(round(v, 4) for v in vx_vals)) > 1


def test_burst_custom_count():
    assert len(burst(0, 0, (0, 0, 255), count=1))  == 1
    assert len(burst(0, 0, (0, 0, 255), count=20)) == 20
