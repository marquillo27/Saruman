from __future__ import annotations

import random

import pygame

from saruman.config import INTERNAL_H, INTERNAL_W

MODE_RAIN   = "rain"
MODE_SNOW   = "snow"
MODE_EMBERS = "embers"

_MODES = (MODE_RAIN, MODE_SNOW, MODE_EMBERS)


class _Drop:
    __slots__ = ("x", "y", "vx", "vy", "col", "len")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 col: tuple[int, int, int], length: int) -> None:
        self.x   = x
        self.y   = y
        self.vx  = vx
        self.vy  = vy
        self.col = col
        self.len = length


class Weather:
    """Fixed-pool screen-space weather effect. Particles wrap on screen edges."""

    def __init__(self, mode: str, density: int = 40) -> None:
        if mode not in _MODES:
            raise ValueError(f"Unknown weather mode: {mode!r}")
        self.mode    = mode
        self.density = max(0, int(density))
        self._drops: list[_Drop] = [self._make_drop() for _ in range(self.density)]

    # ------------------------------------------------------------------

    def _make_drop(self) -> _Drop:
        x = random.uniform(0, INTERNAL_W)
        y = random.uniform(0, INTERNAL_H)
        if self.mode == MODE_RAIN:
            return _Drop(
                x, y,
                vx     = -0.5,
                vy     = random.uniform(5.0, 7.5),
                col    = (140, 170, 220),
                length = random.randint(3, 5),
            )
        if self.mode == MODE_SNOW:
            return _Drop(
                x, y,
                vx     = random.uniform(-0.3, 0.3),
                vy     = random.uniform(0.6, 1.4),
                col    = (230, 235, 245),
                length = random.choice((1, 2)),
            )
        # embers
        return _Drop(
            x, y,
            vx     = random.uniform(-0.6, 0.6),
            vy     = -random.uniform(0.4, 1.0),
            col    = (240, random.randint(120, 180), 60),
            length = 1,
        )

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        for d in self._drops:
            d.x += d.vx
            d.y += d.vy
            # Wrap on edges so the pool size stays fixed
            if d.x < -8:
                d.x = INTERNAL_W + 4
            elif d.x > INTERNAL_W + 8:
                d.x = -4
            if d.y < -8:
                d.y = INTERNAL_H + 4
            elif d.y > INTERNAL_H + 8:
                d.y = -4

    def draw(self, surface: pygame.Surface) -> None:
        if self.mode == MODE_RAIN:
            for d in self._drops:
                pygame.draw.line(
                    surface, d.col,
                    (int(d.x), int(d.y)),
                    (int(d.x + d.vx * 2), int(d.y + d.len)),
                )
            return
        if self.mode == MODE_SNOW:
            for d in self._drops:
                pygame.draw.rect(surface, d.col, (int(d.x), int(d.y), d.len, d.len))
            return
        # embers
        for d in self._drops:
            pygame.draw.rect(surface, d.col, (int(d.x), int(d.y), 1, 1))
