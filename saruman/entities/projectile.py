from __future__ import annotations

import pygame

from saruman.config import TILE_SIZE
from saruman.core.assets import get_sprite

_SPEEDS = (6.0, 9.0)
_COLORS = ((220, 200, 50), (255, 120, 20))
_HEIGHTS = (2, 3)


class Projectile:
    W = 6
    LIFETIME = 120

    def __init__(self, x: float, y: float, facing: int, weapon_level: int = 0) -> None:
        self.x     = x
        self.y     = y
        self.vel_x = _SPEEDS[weapon_level] * facing
        self.alive = True
        self._h    = _HEIGHTS[weapon_level]
        self._col  = _COLORS[weapon_level]
        self._age  = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.W, self._h)

    def update(self, tilemap) -> None:
        self._age += 1
        if self._age >= self.LIFETIME:
            self.alive = False
            return
        self.x += self.vel_x
        tx = int(self.x + self.W // 2) // TILE_SIZE
        ty = int(self.y + self._h // 2) // TILE_SIZE
        if tilemap.is_solid(tx, ty):
            self.alive = False

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("projectile", flip_x=(self.vel_x < 0))
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            pygame.draw.rect(surface, self._col, (sx, sy, self.W, self._h))


class EnemyProjectile:
    """Slow bone-arrow fired by SkeletonArcher. Damages the player on contact."""
    W        = 5
    H        = 2
    LIFETIME = 100
    SPEED    = 3.0
    COLOR    = (200, 195, 165)

    def __init__(self, x: float, y: float, facing: int) -> None:
        self.x     = x
        self.y     = y
        self.vel_x = self.SPEED * facing
        self.vel_y = 0.0
        self.alive = True
        self._age  = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, tilemap) -> None:
        self._age += 1
        if self._age >= self.LIFETIME:
            self.alive = False
            return
        self.x += self.vel_x
        self.y += self.vel_y
        tx = int(self.x + self.W // 2) // TILE_SIZE
        ty = int(self.y + self.H // 2) // TILE_SIZE
        if tilemap.is_solid(tx, ty):
            self.alive = False

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        pygame.draw.rect(surface, self.COLOR, (sx, sy, self.W, self.H))


class AcidBlob(EnemyProjectile):
    """Arcing acid projectile fired by SpitterPlant. Gravity-affected lob."""
    W           = 5
    H           = 5
    LIFETIME    = 180
    SPEED       = 1.6           # horizontal speed (px / frame)
    INIT_VEL_Y  = -3.0          # initial upward velocity
    GRAVITY     = 0.18          # per-frame acceleration
    COLOR       = (130, 200, 60)

    def __init__(self, x: float, y: float, facing: int) -> None:
        super().__init__(x, y, facing)
        self.vel_y = self.INIT_VEL_Y

    def update(self, tilemap) -> None:
        self._age += 1
        if self._age >= self.LIFETIME:
            self.alive = False
            return
        self.vel_y += self.GRAVITY
        self.x += self.vel_x
        self.y += self.vel_y
        tx = int(self.x + self.W // 2) // TILE_SIZE
        ty = int(self.y + self.H // 2) // TILE_SIZE
        if tilemap.is_solid(tx, ty):
            self.alive = False

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        pygame.draw.rect(surface, self.COLOR, (sx, sy, self.W, self.H))
        pygame.draw.rect(surface, (180, 240, 110), (sx + 1, sy + 1, self.W - 2, self.H - 3))
