from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.audio import get_audio
from saruman.core.state import State
from saruman.save import highscores
from saruman.ui.theme import get_font


class HighScoreState(State):
    draws_below = False

    def __init__(self, game, highlight_rank: int | None = None) -> None:
        self._game      = game
        self._entries   = highscores.load()
        self._highlight = highlight_rank

    def on_enter(self) -> None:
        get_audio().play_music("menu.ogg")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._game.states.pop()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((5, 5, 15))
        cx = INTERNAL_W // 2

        title = get_font(12, bold=True).render("HIGH SCORES", True, COL_GOLD)
        surface.blit(title, title.get_rect(centerx=cx, top=10))

        y = 36
        if not self._entries:
            empty = get_font(8).render("No scores yet!", True, (120, 120, 140))
            surface.blit(empty, empty.get_rect(centerx=cx, top=y))
        else:
            for i, entry in enumerate(self._entries):
                rank = i + 1
                col  = COL_GOLD if rank == self._highlight else COL_WHITE
                line = f"{rank:2d}.  {entry['name']:<8s}  {entry['score']:>6d}"
                surf = get_font(8).render(line, True, col)
                surface.blit(surf, surf.get_rect(centerx=cx, top=y))
                y += 13

        hint = get_font(6).render("Press any key to return", True, (70, 80, 110))
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 5))
