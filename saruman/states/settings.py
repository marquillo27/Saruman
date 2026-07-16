from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.audio import get_audio
from saruman.core.state import State
from saruman.save import settings as _cfg
from saruman.ui.theme import get_font

_ROWS = ["MUSIC VOLUME", "SFX VOLUME", "FULLSCREEN", "CLEAR HIGH SCORES"]


class SettingsState(State):
    draws_below = False

    def __init__(self, game) -> None:
        self._game          = game
        self._cursor        = 0
        self._s             = _cfg.get()   # live reference — mutations persist
        self._confirm_clear = False

    def on_exit(self) -> None:
        _cfg.save()

    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self._cursor = (self._cursor - 1) % len(_ROWS)
            self._confirm_clear = False
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._cursor = (self._cursor + 1) % len(_ROWS)
            self._confirm_clear = False
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self._adjust(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(+1)
        elif event.key == pygame.K_ESCAPE:
            self._confirm_clear = False
            self._game.states.pop()
        elif event.key in (pygame.K_RETURN, pygame.K_z):
            if self._cursor == len(_ROWS) - 1:   # CLEAR HIGH SCORES row
                if self._confirm_clear:
                    from saruman.save import highscores
                    highscores.clear()
                    self._confirm_clear = False
                else:
                    self._confirm_clear = True
            else:
                self._game.states.pop()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((5, 5, 15))
        cx = INTERNAL_W // 2

        title = get_font(12, bold=True).render("SETTINGS", True, COL_GOLD)
        surface.blit(title, title.get_rect(centerx=cx, top=12))

        y0 = 50
        for i, label in enumerate(_ROWS):
            col  = COL_GOLD if i == self._cursor else COL_WHITE
            val  = self._fmt(i)
            line = f"{label}   {val}"
            surf = get_font(8).render(line, True, col)
            r    = surf.get_rect(centerx=cx, top=y0 + i * 22)
            surface.blit(surf, r)
            if i == self._cursor and i < len(_ROWS) - 1:
                arr = get_font(8).render("< >", True, COL_GOLD)
                surface.blit(arr, arr.get_rect(centerx=cx, top=r.bottom + 2))

        hint = get_font(6).render("Left/Right to change   ESC/Enter to save", True, (70, 80, 110))
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 5))

    # ------------------------------------------------------------------

    def _fmt(self, row: int) -> str:
        if row == 0: return str(self._s["music_volume"])
        if row == 1: return str(self._s["sfx_volume"])
        if row == 2: return "ON" if self._s["fullscreen"] else "OFF"
        return "CONFIRM?" if self._confirm_clear else "ENTER"

    def _adjust(self, delta: int) -> None:
        if self._cursor == 0:
            v = max(0, min(10, self._s["music_volume"] + delta))
            self._s["music_volume"] = v
            get_audio().set_music_volume(v)
        elif self._cursor == 1:
            v = max(0, min(10, self._s["sfx_volume"] + delta))
            self._s["sfx_volume"] = v
            get_audio().set_sfx_volume(v)
        elif self._cursor == 2:
            self._s["fullscreen"] = not self._s["fullscreen"]
            self._game.set_fullscreen(self._s["fullscreen"])
