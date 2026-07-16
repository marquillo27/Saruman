from __future__ import annotations

import math
import random

import pygame

from saruman.config import (
    COL_GOLD, COL_SKY_BOT, COL_SKY_TOP, COL_WHITE,
    INTERNAL_H, INTERNAL_W,
)
from saruman.core.audio import get_audio
from saruman.core.state import State
from saruman.ui.theme import get_font

_ITEMS = ["START GAME", "HIGH SCORES", "SETTINGS", "CONTROLS", "QUIT"]


class MenuState(State):
    draws_below = False

    def __init__(self, game) -> None:
        self._game   = game
        self._cursor = 0
        self._bg     = self._make_sky()
        self._stars  = self._make_stars()
        self._tick   = 0.0

    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        get_audio().play_music("menu.ogg")

    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self._cursor = (self._cursor - 1) % len(_ITEMS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._cursor = (self._cursor + 1) % len(_ITEMS)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            self._confirm()

    def update(self, dt: float) -> None:
        self._tick += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._bg, (0, 0))
        self._draw_stars(surface)
        self._draw_mountains(surface)
        self._draw_title(surface)
        self._draw_menu(surface)

    # ------------------------------------------------------------------

    def _confirm(self) -> None:
        if self._cursor == 0:
            from saruman.states.play import PlayState
            from saruman.states.worldcard import WorldCardState
            game = self._game
            self._game.states.push(
                WorldCardState(game, "level_01_greenshire_hills",
                               lambda: PlayState(game))
            )
        elif self._cursor == 1:
            from saruman.states.highscore import HighScoreState
            self._game.states.push(HighScoreState(self._game))
        elif self._cursor == 2:
            from saruman.states.settings import SettingsState
            self._game.states.push(SettingsState(self._game))
        elif self._cursor == 3:
            from saruman.states.controls import ControlsState
            self._game.states.push(ControlsState(self._game))
        else:
            self._game.quit()

    # ------------------------------------------------------------------

    def _draw_title(self, surface: pygame.Surface) -> None:
        pulse = 0.5 + 0.5 * math.sin(self._tick * 2.0)
        r = int(COL_GOLD[0] + (255 - COL_GOLD[0]) * pulse * 0.35)
        g = int(COL_GOLD[1] + (255 - COL_GOLD[1]) * pulse * 0.35)
        b = int(COL_GOLD[2] + (255 - COL_GOLD[2]) * pulse * 0.35)

        t1 = get_font(16, bold=True).render("PROJECT", True, (r, g, b))
        t2 = get_font(16, bold=True).render("SARUMAN", True, (r, g, b))
        sub    = get_font(7).render("Aldric the Grey  vs  The Pale Hand", True, (110, 120, 155))
        byline = get_font(6).render("Created by Marquillo", True, (80, 90, 120))

        cx = INTERNAL_W // 2
        surface.blit(t1, t1.get_rect(centerx=cx, top=22))
        surface.blit(t2, t2.get_rect(centerx=cx, top=22 + t1.get_height() + 1))
        surface.blit(sub,    sub.get_rect(centerx=cx, top=60))
        surface.blit(byline, byline.get_rect(centerx=cx, top=72))

    def _draw_menu(self, surface: pygame.Surface) -> None:
        font = get_font(8, bold=True)
        cx   = INTERNAL_W // 2
        y0   = 90

        for i, label in enumerate(_ITEMS):
            col  = COL_GOLD if i == self._cursor else COL_WHITE
            surf = font.render(label, True, col)
            r    = surf.get_rect(centerx=cx, top=y0 + i * 16)
            surface.blit(surf, r)
            if i == self._cursor:
                arrow = font.render(">", True, COL_GOLD)
                surface.blit(arrow, (r.left - 12, r.top))

        hint = get_font(6).render("Arrows/WASD   Space/Z   Enter", True, (70, 80, 110))
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 4))

    def _draw_stars(self, surface: pygame.Surface) -> None:
        for x, y, phase in self._stars:
            bright = int(110 + 100 * math.sin(self._tick * 1.4 + phase))
            pygame.draw.rect(surface, (bright, bright, min(255, bright + 30)), (x, y, 1, 1))

    def _draw_mountains(self, surface: pygame.Surface) -> None:
        period = 55
        count  = INTERNAL_W // period + 3
        offset = 0
        for i in range(-1, count):
            bx     = i * period - offset
            peak_y = 55 + (i % 5) * 10
            pygame.draw.polygon(surface, (18, 22, 46), [
                (bx - 24, 120), (bx, peak_y), (bx + 24, 120),
            ])

    # ------------------------------------------------------------------

    @staticmethod
    def _make_sky() -> pygame.Surface:
        surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
        for y in range(INTERNAL_H):
            t = y / INTERNAL_H
            r = int(COL_SKY_TOP[0] + (COL_SKY_BOT[0] - COL_SKY_TOP[0]) * t)
            g = int(COL_SKY_TOP[1] + (COL_SKY_BOT[1] - COL_SKY_TOP[1]) * t)
            b = int(COL_SKY_TOP[2] + (COL_SKY_BOT[2] - COL_SKY_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (INTERNAL_W, y))
        return surf

    @staticmethod
    def _make_stars() -> list[tuple[int, int, float]]:
        rng = random.Random(42)
        return [
            (rng.randint(0, INTERNAL_W - 1), rng.randint(2, INTERNAL_H // 2 - 10), rng.random() * math.tau)
            for _ in range(60)
        ]
