from __future__ import annotations

from typing import Callable

import pygame

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.state import State
from saruman.ui.theme import get_font

# Stem of each world's FIRST level → (subtitle, title, accent, background).
# Shown as a brief intro card when the player enters a new world.
WORLDS: dict[str, tuple[str, str, tuple, tuple]] = {
    "level_01_greenshire_hills": ("SVET I",   "GREENWOOD",    (120, 210, 120), (10, 26, 14)),
    "level_11_ashfall_wastes":   ("SVET II",  "SCORCHLANDS",  (255, 140,  50), (28, 10,  6)),
    "level_06_pale_tower":       ("SVET III", "FROZEN NORTH", (150, 210, 255), (10, 22, 38)),
}


class WorldCardState(State):
    """Brief full-screen title card announcing a new world, then hands off
    to the level via the supplied factory."""

    draws_below = False
    HOLD        = 110   # frames held at full opacity (~1.8s at 60fps)
    FADE        = 18    # fade-in / fade-out frames
    _SKIP_KEYS  = {pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE}

    def __init__(self, game, stem: str, factory: Callable[[], State]) -> None:
        self._game    = game
        self._factory = factory
        self._frame   = 0
        self._done    = False

        sub, title, accent, self._bg = WORLDS[stem]
        self._sub_surf   = get_font(9,  bold=True).render(sub,   True, (235, 235, 245))
        self._title_surf = get_font(16, bold=True).render(title, True, accent)
        self._rule_col   = accent
        self._overlay    = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self._overlay.fill((0, 0, 0))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in self._SKIP_KEYS:
            self._advance()

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._frame += 1
        if self._frame >= self.FADE * 2 + self.HOLD:
            self._advance()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self._bg)
        cx, cy = INTERNAL_W // 2, INTERNAL_H // 2

        surface.blit(self._sub_surf,   self._sub_surf.get_rect(centerx=cx, bottom=cy - 8))
        surface.blit(self._title_surf, self._title_surf.get_rect(centerx=cx, top=cy - 2))
        # Accent rule under the title
        rule_w = self._title_surf.get_width() + 12
        pygame.draw.line(
            surface, self._rule_col,
            (cx - rule_w // 2, cy + 22), (cx + rule_w // 2, cy + 22), 1,
        )

        # Fade in then out via a black overlay
        if self._frame < self.FADE:
            alpha = 255 - int(255 * self._frame / self.FADE)
        elif self._frame >= self.FADE + self.HOLD:
            out = self._frame - (self.FADE + self.HOLD)
            alpha = min(255, int(255 * out / self.FADE))
        else:
            alpha = 0
        if alpha > 0:
            self._overlay.set_alpha(alpha)
            surface.blit(self._overlay, (0, 0))

    def _advance(self) -> None:
        if self._done:
            return
        self._done = True
        nxt = self._factory()
        self._game.states.replace(nxt)
