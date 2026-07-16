"""Tests for the Weather overlay system."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.world.weather import MODE_EMBERS, MODE_RAIN, MODE_SNOW, Weather


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", [MODE_RAIN, MODE_SNOW, MODE_EMBERS])
def test_each_mode_constructs(mode):
    w = Weather(mode, density=10)
    assert w.mode == mode
    assert w.density == 10


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        Weather("blizzard", density=10)


def test_zero_density_is_valid():
    w = Weather(MODE_RAIN, density=0)
    assert w.density == 0


def test_negative_density_clamps_to_zero():
    w = Weather(MODE_SNOW, density=-5)
    assert w.density == 0


# ---------------------------------------------------------------------------
# Pool size invariants — density never grows
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", [MODE_RAIN, MODE_SNOW, MODE_EMBERS])
def test_pool_size_stays_constant_after_updates(mode):
    w = Weather(mode, density=20)
    initial = len(w._drops)
    for _ in range(120):
        w.update(1 / 60)
    assert len(w._drops) == initial


# ---------------------------------------------------------------------------
# Wrap-around: particles never escape forever
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", [MODE_RAIN, MODE_SNOW, MODE_EMBERS])
def test_drops_stay_within_extended_bounds(mode):
    w = Weather(mode, density=30)
    for _ in range(300):
        w.update(1 / 60)
    for d in w._drops:
        assert -8 <= d.x <= INTERNAL_W + 8
        assert -8 <= d.y <= INTERNAL_H + 8


# ---------------------------------------------------------------------------
# Drawing — must not crash for any mode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", [MODE_RAIN, MODE_SNOW, MODE_EMBERS])
def test_draw_does_not_crash(mode):
    target = pygame.Surface((INTERNAL_W, INTERNAL_H))
    w = Weather(mode, density=15)
    w.draw(target)


def test_zero_density_draw_does_not_crash():
    target = pygame.Surface((INTERNAL_W, INTERNAL_H))
    w = Weather(MODE_SNOW, density=0)
    w.draw(target)
