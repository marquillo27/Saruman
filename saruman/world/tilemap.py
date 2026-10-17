from __future__ import annotations

from pathlib import Path

import pygame
import pytmx

from saruman.config import INTERNAL_H, INTERNAL_W, TILE_SIZE
from saruman.world.terrain import render_terrain, skin_for


class Tilemap:
    def __init__(self, tmx_path: Path) -> None:
        self._map: pytmx.TiledMap = pytmx.load_pygame(str(tmx_path), pixelalpha=True)
        self._width  = self._map.width
        self._height = self._map.height
        self._solid_idx = next(
            i for i, l in enumerate(self._map.layers)
            if l.name == "solid" and isinstance(l, pytmx.TiledTileLayer)
        )
        self._solid_grid = self._build_solid_grid()
        self._fake_grid  = self._build_fake_grid()
        self._fake_overlay: pygame.Surface | None = None
        # Painted lazily on first draw (needs pygame display for convert_alpha).
        self._skin    = skin_for(tmx_path.stem)
        self._terrain: pygame.Surface | None = None

    def _build_solid_grid(self) -> list[list[bool]]:
        return [
            [self._map.get_tile_gid(tx, ty, self._solid_idx) != 0
             for tx in range(self._width)]
            for ty in range(self._height)
        ]

    def _build_fake_grid(self) -> list[list[bool]]:
        """Cells of the optional "fake" layer: drawn like ground, walkable."""
        idx = next((i for i, l in enumerate(self._map.layers)
                    if l.name == "fake" and isinstance(l, pytmx.TiledTileLayer)), None)
        if idx is None:
            return [[False] * self._width for _ in range(self._height)]
        return [[self._map.get_tile_gid(tx, ty, idx) != 0 for tx in range(self._width)]
                for ty in range(self._height)]

    def is_fake(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= self._width or ty >= self._height:
            return False
        return self._fake_grid[ty][tx]

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def pixel_width(self) -> int:
        return self._width * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self._height * TILE_SIZE

    @property
    def tiled_map(self) -> pytmx.TiledMap:
        return self._map

    def is_solid(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= self._width or ty >= self._height:
            return True  # out-of-bounds = wall
        return self._solid_grid[ty][tx]

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        """Blit the pre-painted biome terrain under the camera."""
        if self._terrain is None:
            self._paint()
        surface.blit(self._terrain, (-int(camera_x), -int(camera_y)))

    def draw_fake(self, surface: pygame.Surface, camera_x: float, camera_y: float,
                  reveal: bool) -> None:
        """Draw fake walls over the actors; see-through while the player is inside."""
        if self._terrain is None:
            self._paint()
        if self._fake_overlay is None:
            return
        self._fake_overlay.set_alpha(90 if reveal else 255)
        surface.blit(self._fake_overlay, (-int(camera_x), -int(camera_y)))

    def _paint(self) -> None:
        """Paint solid and fake cells together so fake walls match the ground,
        then split the fake cells off into their own overlay."""
        merged = [[s or f for s, f in zip(srow, frow)]
                  for srow, frow in zip(self._solid_grid, self._fake_grid)]
        full = render_terrain(merged, self._skin)
        if any(any(row) for row in self._fake_grid):
            overlay = pygame.Surface(full.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 0))
            for ty, row in enumerate(self._fake_grid):
                for tx, fake in enumerate(row):
                    if fake:
                        cell = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        overlay.blit(full, cell, cell)
                        full.fill((0, 0, 0, 0), cell)
            self._fake_overlay = overlay
        self._terrain = full
        if pygame.display.get_surface():
            self._terrain = self._terrain.convert_alpha()
            if self._fake_overlay is not None:
                self._fake_overlay = self._fake_overlay.convert_alpha()

    def draw_tmx_tiles(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        """Original renderer using the .tmx tileset images (kept for tools)."""
        left   = max(0, int(camera_x) // TILE_SIZE)
        right  = min(self._width,  int(camera_x + INTERNAL_W) // TILE_SIZE + 2)
        top    = max(0, int(camera_y) // TILE_SIZE)
        bottom = min(self._height, int(camera_y + INTERNAL_H) // TILE_SIZE + 2)

        for ty in range(top, bottom):
            for tx in range(left, right):
                if not self._solid_grid[ty][tx]:
                    continue
                img = self._map.get_tile_image(tx, ty, self._solid_idx)
                if img:
                    sx = tx * TILE_SIZE - int(camera_x)
                    sy = ty * TILE_SIZE - int(camera_y)
                    surface.blit(img, (sx, sy))
