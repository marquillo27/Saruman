from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.state import State
from saruman.ui.theme import get_font

_ITEMS = ["RESUME", "SETTINGS", "CONTROLS", "QUIT TO MENU"]
_RESUME, _SETTINGS, _CONTROLS, _QUIT = range(len(_ITEMS))


class PauseState(State):
    """Pause menu drawn on top of the frozen play scene."""

    draws_below = True

    def __init__(self, game) -> None:
        self._game    = game
        self._cursor  = _RESUME     # always open on RESUME: a stray confirm is harmless
        self._overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._game.states.pop()                 # resume Play
        elif event.key in (pygame.K_UP, pygame.K_w):
            self._cursor = (self._cursor - 1) % len(_ITEMS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._cursor = (self._cursor + 1) % len(_ITEMS)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_z):
            self._confirm()

    def _confirm(self) -> None:
        if self._cursor == _RESUME:
            self._game.states.pop()
        elif self._cursor == _SETTINGS:
            from saruman.states.settings import SettingsState
            self._game.states.push(SettingsState(self._game))
        elif self._cursor == _CONTROLS:
            from saruman.states.controls import ControlsState
            self._game.states.push(ControlsState(self._game))
        else:
            # pop Pause then Play; MenuState.on_enter() fires automatically
            self._game.states.pop()
            self._game.states.pop()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._overlay, (0, 0))
        cx = INTERNAL_W // 2

        title = get_font(12, bold=True).render("PAUSED", True, COL_GOLD)
        surface.blit(title, title.get_rect(centerx=cx, top=40))

        font = get_font(8, bold=True)
        y0   = 76
        for i, label in enumerate(_ITEMS):
            col  = COL_GOLD if i == self._cursor else COL_WHITE
            surf = font.render(label, True, col)
            r    = surf.get_rect(centerx=cx, top=y0 + i * 16)
            surface.blit(surf, r)
            if i == self._cursor:
                arrow = font.render(">", True, COL_GOLD)
                surface.blit(arrow, (r.left - 12, r.top))

        hint = get_font(6).render("Arrows/WASD   Enter   Esc resume", True, (110, 120, 150))
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 6))
