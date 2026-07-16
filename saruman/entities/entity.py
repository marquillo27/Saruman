from __future__ import annotations

import pygame

from saruman.config import GRAVITY, MAX_FALL_SPEED


class Entity:
    def __init__(self, x: float, y: float, w: int, h: int) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vel_x  = 0.0
        self.vel_y  = 0.0
        self.on_ground = False
        self.alive  = True
        self.facing = 1  # 1 = right, -1 = left

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def apply_gravity(self) -> None:
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
