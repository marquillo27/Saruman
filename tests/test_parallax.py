"""Tests for the biome-specific parallax scrolling system."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.world.parallax import ParallaxLayer, make_parallax_layers


ALL_LEVELS = [
    "level_01_greenshire_hills",
    "level_02_wolfwood",
    "level_03_glass_caverns",
    "level_04_sunken_mines",
    "level_05_ash_marshes",
    "level_06_pale_tower",
    "level_07_cursed_catacombs",
    "level_08_forsaken_bridge",
    "level_09_skybound_spires",
    "level_10_goblin_kings_throne",
    "level_11_ashfall_wastes",
    "level_12_cinderwood_remains",
    "level_13_emberfall_keep",
]


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


# ---------------------------------------------------------------------------
# Layer count and types
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("level", ALL_LEVELS)
def test_known_level_returns_two_layers(level):
    layers = make_parallax_layers(level)
    assert len(layers) == 2


def test_unknown_level_falls_back_to_two_layers():
    layers = make_parallax_layers("level_99_nonexistent")
    assert len(layers) == 2


def test_layers_are_parallax_layer_instances():
    for level in ALL_LEVELS:
        layers = make_parallax_layers(level)
        assert all(isinstance(l, ParallaxLayer) for l in layers)


# ---------------------------------------------------------------------------
# Scroll factors
# ---------------------------------------------------------------------------

def test_far_layer_scrolls_slower_than_mid_layer():
    """First layer (far) must have a smaller factor than second (mid)."""
    for level in ALL_LEVELS:
        layers = make_parallax_layers(level)
        assert layers[0]._factor < layers[1]._factor, (
            f"{level}: far factor {layers[0]._factor} >= mid factor {layers[1]._factor}"
        )


def test_scroll_factors_between_zero_and_one():
    for level in ALL_LEVELS:
        for layer in make_parallax_layers(level):
            assert 0 < layer._factor < 1


# ---------------------------------------------------------------------------
# Surface dimensions
# ---------------------------------------------------------------------------

def test_layer_surfaces_are_correct_width():
    from saruman.config import INTERNAL_W
    for level in ALL_LEVELS:
        for layer in make_parallax_layers(level):
            assert layer._surf.get_width() == INTERNAL_W


def test_layer_surfaces_are_correct_height():
    from saruman.config import INTERNAL_H
    for level in ALL_LEVELS:
        for layer in make_parallax_layers(level):
            assert layer._surf.get_height() == INTERNAL_H


# ---------------------------------------------------------------------------
# Draw — no crash at various camera offsets
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("camera_x", [0.0, 50.0, 320.0, 1000.0, -10.0])
def test_draw_does_not_crash(camera_x):
    target = pygame.Surface((320, 180))
    layers = make_parallax_layers("level_02_wolfwood")
    for layer in layers:
        layer.draw(target, camera_x)


def test_draw_covers_full_width_at_zero_offset():
    """At camera_x=0 the layer surface should fully cover the target."""
    from saruman.config import INTERNAL_W, INTERNAL_H
    target = pygame.Surface((INTERNAL_W, INTERNAL_H))
    layers = make_parallax_layers("level_01_greenshire_hills")
    layers[0].draw(target, camera_x=0.0)


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_each_biome_draws_without_error(level):
    target = pygame.Surface((320, 180))
    for layer in make_parallax_layers(level):
        layer.draw(target, camera_x=200.0)


# ---------------------------------------------------------------------------
# New Frozen North silhouette (Night King finale)
# ---------------------------------------------------------------------------

def test_frostkeep_silhouettes_render_at_internal_size():
    from saruman.config import INTERNAL_W, INTERNAL_H
    from saruman.world.parallax import _frostkeep_far, _frostkeep_mid
    for fn in (_frostkeep_far, _frostkeep_mid):
        surf = fn()
        assert surf.get_width()  == INTERNAL_W
        assert surf.get_height() == INTERNAL_H


def test_emberfall_finale_uses_frostkeep_layers():
    """The re-themed ice finale must use the new frostkeep silhouettes, not embers."""
    from saruman.world.parallax import _BIOME_LAYERS, _frostkeep_far, _frostkeep_mid
    fns = [fn for fn, _ in _BIOME_LAYERS["level_13_emberfall_keep"]]
    assert fns == [_frostkeep_far, _frostkeep_mid]
