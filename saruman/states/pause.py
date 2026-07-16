from __future__ import annotations

import pygame

from saruman.config import COL_GOLD, COL_WHITE, INTERNAL_H, INTERNAL_W
from saruman.core.state import State
from saruman.ui.theme import get_font

_CONTROLS = [
    ("MOVE",        "← → / A D"),
    ("JUMP",        "Space / W / Z"),
    ("DOUBLE JUMP", "Jump again mid-air"),
    ("SHOOT",       "J / X"),
    ("MELEE SWING", "K / C"),
    ("SHIELD",      "L / Q  (hold)"),
    ("PAUSE",       "Esc"),
]

_COL_LABEL = (160, 170, 200)
_COL_KEY   = (220, 200, 120)
_COL_SEP   = (50, 55, 80)


class PauseState(State):
    """Overlay drawn on top of the frozen play scene."""

    draws_below = True

    def __init__(self, game) -> None:
        self._game = game
        self._overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._game.states.pop()                 # resume Play
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
            # quit to menu: pop Pause then Play; MenuState.on_enter() fires automatically
            self._game.states.pop()
            self._game.states.pop()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._overlay, (0, 0))

        cx = INTERNAL_W // 2

        # Title
        paused = get_font(12, bold=True).render("PAUSED", True, COL_GOLD)
        surface.blit(paused, paused.get_rect(centerx=cx, top=10))

        # Controls table
        font_label = get_font(6)
        font_key   = get_font(6, bold=True)
        row_h      = 14
        table_top  = 32
        col_label_x = cx - 72
        col_key_x   = cx + 4

        header = font_label.render("CONTROLS", True, _COL_LABEL)
        surface.blit(header, header.get_rect(centerx=cx, top=table_top))

        # Separator line under header
        sep_y = table_top + header.get_height() + 2
        pygame.draw.line(surface, _COL_SEP, (cx - 76, sep_y), (cx + 76, sep_y))

        for i, (action, keys) in enumerate(_CONTROLS):
            y = sep_y + 4 + i * row_h
            lbl = font_label.render(action, True, _COL_LABEL)
            key = font_key.render(keys,   True, _COL_KEY)
            surface.blit(lbl, (col_label_x, y))
            surface.blit(key, (col_key_x,   y))

        # Bottom separator + actions
        bot_sep_y = sep_y + 4 + len(_CONTROLS) * row_h + 2
        pygame.draw.line(surface, _COL_SEP, (cx - 76, bot_sep_y), (cx + 76, bot_sep_y))

        hint = get_font(6).render("ESC  resume    ENTER  quit to menu", True, (110, 120, 150))
        surface.blit(hint, hint.get_rect(centerx=cx, top=bot_sep_y + 4))
