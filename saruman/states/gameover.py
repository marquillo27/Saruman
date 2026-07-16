from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_RED, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.audio import get_audio
from saruman.core.state import State
from saruman.save import highscores
from saruman.ui.theme import get_font


class GameOverState(State):
    draws_below = False
    _MAX_NAME   = 8

    def __init__(self, game, score: int, won: bool = False) -> None:
        self._game    = game
        self._score   = score
        self._won     = won
        self._entries = highscores.load()
        self._qualify = highscores.is_high_score(score, self._entries)
        self._name    = ""
        self._blink   = 0
        self._done    = False

    def on_enter(self) -> None:
        get_audio().stop_music()
        if self._won:
            get_audio().play_sfx("level_complete.wav")

    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._done:
            return

        if not self._qualify:
            if event.type == pygame.KEYDOWN:
                self._finish(save=False)
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            self._finish(save=True)
        elif event.key == pygame.K_BACKSPACE:
            self._name = self._name[:-1]
        elif len(self._name) < self._MAX_NAME:
            ch = event.unicode
            if ch.isprintable() and ch.strip():
                self._name += ch.upper()

    def update(self, dt: float) -> None:
        self._blink = (self._blink + 1) % 60

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((5, 5, 15))
        cx = INTERNAL_W // 2

        # Header
        header = "LEVEL COMPLETE!" if self._won else "GAME OVER"
        hcol   = COL_GOLD if self._won else COL_RED
        go = get_font(14, bold=True).render(header, True, hcol)
        surface.blit(go, go.get_rect(centerx=cx, top=28))

        # Score
        sc = get_font(9).render(f"SCORE  {self._score:06d}", True, COL_WHITE)
        surface.blit(sc, sc.get_rect(centerx=cx, top=62))

        if self._qualify:
            msg = get_font(7).render("NEW HIGH SCORE!  Enter your name:", True, COL_GOLD)
            surface.blit(msg, msg.get_rect(centerx=cx, top=86))

            cursor    = "_" if self._blink < 30 else " "
            nm_surf   = get_font(10, bold=True).render(self._name + cursor, True, COL_GOLD)
            surface.blit(nm_surf, nm_surf.get_rect(centerx=cx, top=100))

            hint = get_font(6).render("ENTER to confirm  BACKSPACE to delete", True, (90, 95, 125))
            surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 5))
        else:
            hint = get_font(7).render("Press any key", True, (90, 95, 125))
            surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 5))

    # ------------------------------------------------------------------

    def _finish(self, *, save: bool) -> None:
        self._done = True
        rank = None
        if save:
            name = self._name.strip() or "???"
            self._entries, rank = highscores.insert(name, self._score, self._entries)
            highscores.save(self._entries)

        from saruman.states.highscore import HighScoreState
        self._game.states.replace(HighScoreState(self._game, rank))
