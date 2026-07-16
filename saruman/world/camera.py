from __future__ import annotations

import pygame

from saruman.config import INTERNAL_H, INTERNAL_W


class Camera:
    LERP = 8.0  # camera catch-up speed in units/second

    def __init__(self, level_pixel_w: int, level_pixel_h: int) -> None:
        self.x = 0.0
        self.y = 0.0
        self._max_x = float(max(0, level_pixel_w - INTERNAL_W))
        self._max_y = float(max(0, level_pixel_h - INTERNAL_H))

    def follow(self, target: pygame.Rect, dt: float) -> None:
        tx = target.centerx - INTERNAL_W // 2
        ty = target.centery - INTERNAL_H // 2
        f  = min(1.0, self.LERP * dt)
        self.x += (tx - self.x) * f
        self.y += (ty - self.y) * f
        self.x = max(0.0, min(self.x, self._max_x))
        self.y = max(0.0, min(self.y, self._max_y))

    def world_to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        return int(wx - self.x), int(wy - self.y)
