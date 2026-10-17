"""Tests for biome terrain skins rendered from the collision grid."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import TILE_SIZE as T
from saruman.world.terrain import LEVEL_SKIN, SKINS, render_terrain, skin_for


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


# 4 wide x 3 tall: floating 2-tile platform on row 0, floor on row 2
GRID = [
    [False, True,  True,  False],
    [False, False, False, False],
    [True,  True,  True,  True],
]


def test_every_level_has_a_known_skin():
    for name in LEVEL_SKIN.values():
        assert name in SKINS


def test_unknown_level_falls_back():
    assert skin_for("level_99_nope") is SKINS["greenwood"]


@pytest.mark.parametrize("skin", list(SKINS))
def test_render_size_matches_grid(skin):
    surf = render_terrain(GRID, SKINS[skin])
    assert surf.get_size() == (4 * T, 3 * T)


def test_air_cells_stay_transparent():
    surf = render_terrain(GRID, SKINS["greenwood"])
    assert surf.get_at((T // 2, T + T // 2)).a == 0     # empty row in the middle


def test_exposed_top_gets_the_cap_colour():
    skin = SKINS["greenwood"]
    surf = render_terrain(GRID, skin)
    top_row = {tuple(surf.get_at((x, 2 * T + 1)))[:3] for x in range(4 * T)}
    assert skin.cap[1] in top_row                          # highlight line of the cap


def test_rendering_is_deterministic():
    a = render_terrain(GRID, SKINS["scorch"])
    b = render_terrain(GRID, SKINS["scorch"])
    assert pygame.image.tobytes(a, "RGBA") == pygame.image.tobytes(b, "RGBA")


def test_frozen_overhang_grows_icicles():
    skin = SKINS["frozen"]
    surf = render_terrain(GRID, skin)
    below = [tuple(surf.get_at((x, T)))[:3] for x in range(T, 3 * T)]
    assert skin.drips in below
