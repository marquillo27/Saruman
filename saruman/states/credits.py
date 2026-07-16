from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.audio import get_audio
from saruman.core.state import State
from saruman.ui.theme import get_font

_LINES: list[tuple[str, str]] = [
    ("PROJECT SARUMAN",                      "title"),
    ("",                                     "gap"),
    ("A pygame-ce adventure",                "body"),
    ("",                                     "gap"),
    ("Created by Marquillo",                 "body"),
    ("",                                     "gap"),
    ("Levels",                               "header"),
    ("Greenshire Hills  •  Wolfwood",   "body"),
    ("Glass Caverns  •  Sunken Mines",  "body"),
    ("Ash Marshes  •  Pale Tower",      "body"),
    ("",                                     "gap"),
    ("Music & SFX: procedurally generated",  "body"),
    ("Art: procedurally generated",          "body"),
    ("",                                     "gap"),
    ("Built with pygame-ce",                 "body"),
    ("",                                     "gap"),
    ("Thanks for playing!",                  "title"),
]

_SCROLL_SPEED = 0.6    # px/frame (36 px/s at 60 fps)
_TOTAL_FRAMES = 720    # 12 seconds before auto-advance
_SKIP_KEYS    = {pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE}


class CreditsState(State):
    draws_below = False

    def __init__(self, game, score: int) -> None:
        self._game   = game
        self._score  = score
        self._frame  = 0
        self._done   = False
        self._scroll = float(INTERNAL_H)

        # Pre-render each line as (surface | None, line_height)
        self._rendered: list[tuple[pygame.Surface | None, int]] = []
        for text, kind in _LINES:
            if kind == "gap" or not text:
                self._rendered.append((None, 10))
            elif kind == "title":
                surf = get_font(12, bold=True).render(text, True, COL_GOLD)
                self._rendered.append((surf, 20))
            elif kind == "header":
                surf = get_font(8, bold=True).render(text, True, (180, 200, 255))
                self._rendered.append((surf, 14))
            else:
                surf = get_font(7).render(text, True, COL_WHITE)
                self._rendered.append((surf, 12))

        self._total_h = sum(h for _, h in self._rendered)
        self._hint    = get_font(6).render("ENTER / SPACE to skip", True, (90, 95, 125))

    def on_enter(self) -> None:
        get_audio().stop_music()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in _SKIP_KEYS:
            self._advance()

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._scroll -= _SCROLL_SPEED
        self._frame  += 1
        if self._frame >= _TOTAL_FRAMES or self._scroll + self._total_h < 0:
            self._advance()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((5, 5, 15))
        cx = INTERNAL_W // 2
        y  = int(self._scroll)
        for surf, h in self._rendered:
            if surf is not None and -h < y < INTERNAL_H:
                surface.blit(surf, surf.get_rect(centerx=cx, top=y))
            y += h

        if self._frame < _TOTAL_FRAMES - 60:
            surface.blit(
                self._hint,
                self._hint.get_rect(centerx=cx, bottom=INTERNAL_H - 4),
            )

    def _advance(self) -> None:
        if self._done:
            return
        self._done = True
        from saruman.states.gameover import GameOverState
        self._game.states.replace(GameOverState(self._game, self._score, won=True))
