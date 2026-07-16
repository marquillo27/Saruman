"""Tests for AABB tile collision."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import TILE_SIZE
from saruman.entities.entity import Entity
from saruman.physics.collision import move_and_collide


# ---------------------------------------------------------------------------
# Minimal tilemap stub
# ---------------------------------------------------------------------------

class _StubTilemap:
    """Single solid platform at tile row 10 (y=160..175) across all columns."""

    SOLID_ROW = 10
    MAP_W     = 40
    MAP_H     = 12

    @property
    def width(self)  -> int: return self.MAP_W
    @property
    def height(self) -> int: return self.MAP_H
    @property
    def pixel_width(self)  -> int: return self.MAP_W * TILE_SIZE
    @property
    def pixel_height(self) -> int: return self.MAP_H * TILE_SIZE

    def is_solid(self, tx: int, ty: int) -> bool:
        if tx < 0 or tx >= self.MAP_W or ty < 0 or ty >= self.MAP_H:
            return False
        return ty == self.SOLID_ROW


@pytest.fixture
def tilemap():
    pygame.init()
    yield _StubTilemap()
    pygame.quit()


def _entity(x: float, y: float, w: int = 10, h: int = 16) -> Entity:
    return Entity(x, y, w, h)


# Platform top = SOLID_ROW * TILE_SIZE = 160
PLATFORM_TOP = _StubTilemap.SOLID_ROW * TILE_SIZE   # 160


# ---------------------------------------------------------------------------
# Landing on ground
# ---------------------------------------------------------------------------

def test_land_on_platform(tilemap):
    e = _entity(64, 140)
    e.vel_y = 5.0
    move_and_collide(e, tilemap)
    assert e.on_ground
    assert e.y + e.h == PLATFORM_TOP


def test_land_snaps_to_tile_top_not_offby_one(tilemap):
    # entity bottom one pixel above tile top (143+16=159, tile top=160)
    e = _entity(64, 143)
    e.vel_y = 5.0
    move_and_collide(e, tilemap)
    assert e.on_ground
    assert e.y + e.h == PLATFORM_TOP


def test_exact_boundary_still_on_ground(tilemap):
    """Entity resting exactly on platform top should stay on_ground."""
    e = _entity(64, PLATFORM_TOP - 16)  # bottom == 160 exactly
    e.vel_y = 0.0
    e.on_ground = True
    move_and_collide(e, tilemap)
    assert e.on_ground


# ---------------------------------------------------------------------------
# Ceiling bonk
# ---------------------------------------------------------------------------

def test_ceiling_bonk_stops_upward_vel(tilemap):
    """Moving up into a solid tile should zero vel_y and push entity down."""
    # Place entity one tile above SOLID_ROW (row 9) with upward velocity
    # There's no ceiling in our stub, so let's use a two-row solid stub.
    class _CeilMap(_StubTilemap):
        def is_solid(self, tx, ty):
            return ty in (5, 10) and 0 <= tx < self.MAP_W

    cmap = _CeilMap()
    # Entity starts below ceiling row 5 (tile bottom=96), moves up into it
    e = _entity(64, 100)
    e.vel_y = -8.0
    move_and_collide(e, cmap)
    assert e.vel_y >= 0  # upward velocity killed or reversed
    assert not e.on_ground


# ---------------------------------------------------------------------------
# Wall slide
# ---------------------------------------------------------------------------

def test_wall_stops_horizontal_vel(tilemap):
    """Moving right into a vertical wall column should zero vel_x."""
    class _WallMap(_StubTilemap):
        def is_solid(self, tx, ty):
            if ty == 10:
                return True  # ground
            if tx == 5 and 0 <= ty < self.MAP_H:
                return True  # wall column
            return False

    wmap = _WallMap()
    e = _entity(68, 140)  # just left of wall column tx=5 (x=80)
    e.vel_x = 5.0
    move_and_collide(e, wmap)
    assert e.vel_x == 0.0
    assert e.x + e.w <= 5 * TILE_SIZE


# ---------------------------------------------------------------------------
# No tunneling at max fall speed
# ---------------------------------------------------------------------------

def test_no_tunneling_at_max_fall_speed(tilemap):
    """Even at MAX_FALL_SPEED the entity must not pass through the platform."""
    from saruman.config import MAX_FALL_SPEED
    # entity bottom at 159 (one px above tile top=160), moving at max speed
    e = _entity(64, 143)
    e.vel_y = MAX_FALL_SPEED  # worst-case fall
    move_and_collide(e, tilemap)
    assert e.on_ground
    assert e.y + e.h <= PLATFORM_TOP


# ---------------------------------------------------------------------------
# Air movement
# ---------------------------------------------------------------------------

def test_no_ground_flag_in_air(tilemap):
    e = _entity(64, 50)  # well above platform
    e.vel_y = 2.0
    move_and_collide(e, tilemap)
    assert not e.on_ground
