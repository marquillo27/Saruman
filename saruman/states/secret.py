from __future__ import annotations

import math
from typing import Callable

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.state import State
from saruman.ui.theme import get_font
from saruman.world.particle import Particle, burst


class SecretState(State):
    """'SECRET FOUND!' gag screen shown before warping to a secret level."""

    draws_below = False
    DURATION = 120  # 2s @ 60fps

    def __init__(self, game, factory: Callable[[], State]) -> None:
        self._game     = game
        self._factory  = factory
        self._frame    = 0
        self._particles: list[Particle] = []

    def update(self, dt: float) -> None:
        self._frame += 1

        if self._frame % 10 == 0:
            self._particles.extend(
                burst(INTERNAL_W // 2, INTERNAL_H // 2, COL_GOLD, count=8, speed=2.5)
            )

        for p in self._particles:
            p.update()
        self._particles = [p for p in self._particles if p.alive]

        if self._frame >= self.DURATION:
            from saruman.states.transition import TransitionState
            self._game.states.replace(TransitionState(self._game, self._factory))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))

        for p in self._particles:
            p.draw(surface, int(p.x), int(p.y))

        pulse = 0.75 + 0.25 * math.sin(self._frame * 0.15)
        r = int(COL_GOLD[0] * pulse)
        g = int(COL_GOLD[1] * pulse)
        b = int(COL_GOLD[2] * pulse)

        big  = get_font(14, bold=True).render("SECRET FOUND!", True, (r, g, b))
        hint = get_font(6).render("A hidden path has been revealed...", True, COL_WHITE)

        cx = INTERNAL_W // 2
        cy = INTERNAL_H // 2
        surface.blit(big,  big.get_rect(centerx=cx, centery=cy - 8))
        surface.blit(hint, hint.get_rect(centerx=cx, centery=cy + 12))
