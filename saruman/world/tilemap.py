from __future__ import annotations

from pathlib import Path

import pygame
import pytmx

from saruman.config import INTERNAL_H, INTERNAL_W, TILE_SIZE


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

    def _build_solid_grid(self) -> list[list[bool]]:
        return [
            [self._map.get_tile_gid(tx, ty, self._solid_idx) != 0
             for tx in range(self._width)]
            for ty in range(self._height)
        ]

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
