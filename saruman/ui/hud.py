from __future__ import annotations

import pygame

from saruman.config import (
    COL_GOLD, COL_RED, COL_WHITE, UI_W, MAX_LIVES,
)
from saruman.core.assets import get_sprite
from saruman.ui.theme import get_font

_HUD_H = 14


class HUD:
    def __init__(self) -> None:
        self._bg = pygame.Surface((UI_W, _HUD_H), pygame.SRCALPHA)
        self._bg.fill((8, 8, 18, 210))

    def draw(
        self,
        surface: pygame.Surface,
        lives: int,
        score: int,
        weapon_level: int,
        relics: tuple[int, int] | None = None,
    ) -> None:
        surface.blit(self._bg, (0, 0))
        # Gold divider at bottom of HUD bar
        pygame.draw.line(surface, (100, 78, 35), (0, _HUD_H - 1), (UI_W - 1, _HUD_H - 1))

        # Hearts — one per current life, up to MAX_LIVES
        heart_spr = get_sprite("item_heart")
        shown = max(0, min(lives, MAX_LIVES))
        for i in range(shown):
            if heart_spr:
                surface.blit(heart_spr, (3 + i * 13, 2))
            else:
                self._draw_heart(surface, 3 + i * 13, 3, COL_RED)

        # Score (6 digits, centred)
        font   = get_font(8, bold=True)
        s_surf = font.render(f"{score:06d}", True, COL_WHITE)
        surface.blit(s_surf, s_surf.get_rect(centerx=UI_W // 2, top=3))

        # Weapon label
        label  = "BOW " if weapon_level == 0 else "FIRE"
        col    = COL_GOLD if weapon_level == 0 else (255, 110, 20)
        w_surf = font.render(label, True, col)
        w_rect = w_surf.get_rect(right=UI_W - 2, top=3)
        surface.blit(w_surf, w_rect)

        # Hidden relics found in this level, e.g. "1/2" with a tiny chalice
        if relics and relics[1]:
            found, total = relics
            r_col  = COL_GOLD if found == total else (190, 180, 150)
            r_surf = font.render(f"{found}/{total}", True, r_col)
            r_rect = r_surf.get_rect(right=w_rect.left - 10, top=3)
            surface.blit(r_surf, r_rect)
            ix, iy = r_rect.left - 8, 3
            pygame.draw.rect(surface, (150, 104, 36), (ix, iy, 6, 4))
            pygame.draw.rect(surface, (226, 178, 62), (ix + 1, iy, 4, 3))
            pygame.draw.rect(surface, (150, 104, 36), (ix + 2, iy + 4, 2, 2))
            pygame.draw.rect(surface, (226, 178, 62), (ix + 1, iy + 6, 4, 1))

    @staticmethod
    def _draw_heart(surface: pygame.Surface, x: int, y: int, col: tuple) -> None:
        # Tiny 9x8 heart made of rects
        pygame.draw.rect(surface, col, (x + 1, y,     3, 2))
        pygame.draw.rect(surface, col, (x + 5, y,     3, 2))
        pygame.draw.rect(surface, col, (x,     y + 2, 8, 3))
        pygame.draw.rect(surface, col, (x + 1, y + 5, 6, 2))
        pygame.draw.rect(surface, col, (x + 2, y + 7, 4, 1))
        pygame.draw.rect(surface, col, (x + 3, y + 8, 2, 1))
