from __future__ import annotations

from typing import Callable

import pygame

from saruman.config import UI_H, UI_W
from saruman.core.state import State


class TransitionState(State):
    """Fade to black, create next state at mid-point, fade in."""

    draws_below = False
    FADE = 25   # frames per half

    def __init__(self, game, factory: Callable[[], State]) -> None:
        self._game    = game
        self._factory = factory
        self._frame   = 0
        self._next: State | None = None
        # Per-pixel alpha: a surface-alpha overlay blitted onto the transparent
        # UI canvas would come out fully opaque and hide the fade-in.
        self._overlay = pygame.Surface((UI_W, UI_H), pygame.SRCALPHA)

    def update(self, dt: float) -> None:
        self._frame += 1
        if self._frame == self.FADE:
            self._next = self._factory()
            self._next.on_enter()
        if self._frame >= self.FADE * 2:
            self._game.states.replace(self._next)

    def render(self, world: pygame.Surface, ui: pygame.Surface) -> None:
        if self._next:
            self._next.render(world, ui)
        self._draw_fade(ui)

    def draw(self, surface: pygame.Surface) -> None:
        if self._next:
            self._next.draw(surface)
        self._draw_fade(surface)

    def _draw_fade(self, surface: pygame.Surface) -> None:
        phase2 = self._frame - self.FADE
        if phase2 < 0:
            alpha = 255                                      # solid black
        else:
            alpha = max(0, 255 - int(255 * phase2 / self.FADE))  # fade in

        self._overlay.fill((0, 0, 0, alpha))
        surface.blit(self._overlay, (0, 0))
