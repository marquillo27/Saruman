from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.state import State
from saruman.ui.theme import get_font

_SECTIONS = [
    ("MOVEMENT", [
        ("Move left / right", "← →  /  A  D"),
        ("Jump",              "Space  /  W  /  Z"),
        ("Double jump",       "Jump again while airborne"),
    ]),
    ("COMBAT", [
        ("Shoot",             "J  /  X"),
        ("Melee swing",       "K  /  C"),
        ("Shield  (hold)",    "L  /  Q"),
    ]),
    ("MENU / SYSTEM", [
        ("Pause",             "Esc"),
        ("Resume",            "Esc  (while paused)"),
        ("Quit to menu",      "Enter  (while paused)"),
    ]),
]

_COL_HEADER = (200, 170, 60)
_COL_LABEL  = (160, 170, 200)
_COL_KEY    = (220, 200, 120)
_COL_SEP    = (50, 55, 80)
_COL_BG     = (5, 5, 15)


class ControlsState(State):
    """Full-screen controls reference — shown from the main menu."""

    draws_below = False

    def __init__(self, game) -> None:
        self._game = game

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._game.states.pop()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(_COL_BG)
        cx = INTERNAL_W // 2

        title = get_font(12, bold=True).render("CONTROLS", True, COL_GOLD)
        surface.blit(title, title.get_rect(centerx=cx, top=8))

        font_h   = get_font(7, bold=True)
        font_lbl = get_font(6)
        font_key = get_font(6, bold=True)

        y = 28
        col_lbl = cx - 80
        col_key = cx + 4

        for section_title, rows in _SECTIONS:
            # Section header
            hdr = font_h.render(section_title, True, _COL_HEADER)
            surface.blit(hdr, (col_lbl, y))
            y += hdr.get_height() + 1
            pygame.draw.line(surface, _COL_SEP, (col_lbl, y), (cx + 90, y))
            y += 3

            for action, keys in rows:
                lbl = font_lbl.render(action, True, _COL_LABEL)
                key = font_key.render(keys,   True, _COL_KEY)
                surface.blit(lbl, (col_lbl, y))
                surface.blit(key, (col_key, y))
                y += 12

            y += 6   # gap between sections

        hint = get_font(6).render("Press any key to go back", True, (70, 80, 110))
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=INTERNAL_H - 5))
