from __future__ import annotations

import math

import pygame

from saruman.config import (
    COL_GOLD, COL_SKY_BOT, COL_SKY_TOP, COL_WHITE,
    INTERNAL_H, INTERNAL_W,
)
from saruman.core.audio import get_audio
from saruman.core.state import State
from saruman.paths import asset_path
from saruman.ui.theme import get_font
from saruman.world.parallax import _PAINTED_FACTORS, ParallaxLayer, load_backdrop

_ITEMS = ["START GAME", "HIGH SCORES", "SETTINGS", "CONTROLS", "QUIT"]

# Aldric walks in from the left edge; the view follows him a little and
# settles when he stops, so the backdrop layers show their depth once.
_WALK_TIME  = 2.4         # seconds from the edge to his spot
_WALK_FROM  = -30         # world px, off screen to the left
_WALK_FPS   = 8
_WALK_FRAME = 4           # first walk frame in hero_strip.png (6 frames)
_PAN        = 80.0        # world px the view travels while he walks

# Aldric stands on the foreground hill at the lower left, looking at the tower.
_HERO_FRAME_W, _HERO_FRAME_H = 24, 36
_HERO_X       = 48        # world px, sprite centre at zero sway
_HERO_SCALE   = 2         # backdrop pixels are 2x2 too, so the hero matches them
_HERO_FRAMES  = 4         # idle frames at the start of hero_strip.png
_HERO_FPS     = 60 / 14   # same idle cadence as in play

# Title and menu sit on a dark panel on the right, clear of the tower.
_PANEL      = pygame.Rect(168, 10, 146, 160)
_PANEL_CX   = _PANEL.centerx
_COL_PANEL  = (8, 10, 22, 165)
_COL_BORDER = (212, 161, 85, 70)


class MenuState(State):
    draws_below = False

    def __init__(self, game) -> None:
        self._game   = game
        self._cursor = 0
        self._tick   = 0.0
        layers       = load_backdrop("title")
        self._layers = ([ParallaxLayer(s, f) for s, f in zip(layers, _PAINTED_FACTORS)]
                        if layers else [ParallaxLayer(self._make_sky(), 0.0)])
        self._hero   = self._load_hero()
        self._panel  = self._make_panel()

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

    def render(self, world: pygame.Surface, ui: pygame.Surface) -> None:
        self.draw_backdrop(world)
        self.draw(ui)

    def draw_backdrop(self, surface: pygame.Surface) -> None:
        camera_x = -_PAN * (1 - self._ease(self._walk_progress()))
        for layer in self._layers:
            layer.draw(surface, camera_x)
        self._draw_hero(surface, camera_x)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._panel, _PANEL)
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

    def _draw_hero(self, surface: pygame.Surface, camera_x: float) -> None:
        if self._hero is None or len(self._layers) < 2:
            return
        # Ride the nearest layer and stand on whatever it shows under the hero.
        ground = self._layers[-1]
        p      = self._walk_progress()
        x      = round(_WALK_FROM + (_HERO_X - _WALK_FROM) * p - camera_x * ground._factor)
        feet   = self._ground_y(ground, camera_x, x)
        if p < 1:
            frame = _WALK_FRAME + int(self._tick * _WALK_FPS) % 6
        else:
            frame = int((self._tick - _WALK_TIME) * _HERO_FPS) % _HERO_FRAMES
        w, h   = _HERO_FRAME_W * _HERO_SCALE, _HERO_FRAME_H * _HERO_SCALE
        area   = pygame.Rect(frame * w, 0, w, h)
        # Feet stand a little into the hill so the slope doesn't leave them floating.
        surface.blit(self._hero, (x - w // 2, feet - h + 2 * _HERO_SCALE), area)

    def _walk_progress(self) -> float:
        return min(self._tick / _WALK_TIME, 1.0)

    @staticmethod
    def _ease(t: float) -> float:
        """Ease-out: the view slows down as Aldric arrives."""
        return 1 - (1 - t) ** 2

    @staticmethod
    def _ground_y(layer: ParallaxLayer, camera_x: float, screen_x: int) -> int:
        """Topmost opaque row of a layer at a screen column, in screen coordinates."""
        surf = layer._surf
        w, h = surf.get_size()
        col  = (screen_x + int(camera_x * layer._factor)) % w
        top  = INTERNAL_H - h
        for y in range(h):
            if surf.get_at((col, y)).a:
                return top + y
        return INTERNAL_H - 1

    def _draw_title(self, surface: pygame.Surface) -> None:
        pulse = 0.5 + 0.5 * math.sin(self._tick * 2.0)
        r = int(COL_GOLD[0] + (255 - COL_GOLD[0]) * pulse * 0.35)
        g = int(COL_GOLD[1] + (255 - COL_GOLD[1]) * pulse * 0.35)
        b = int(COL_GOLD[2] + (255 - COL_GOLD[2]) * pulse * 0.35)

        font   = get_font(16, bold=True)
        sub    = get_font(7).render("Aldric the Grey  vs  The Pale Hand", True, (150, 160, 195))
        byline = get_font(6).render("Created by Marquillo", True, (100, 110, 145))

        cx = _PANEL_CX
        for i, word in enumerate(("PROJECT", "SARUMAN")):
            top = 18 + i * (font.get_height() + 1)
            shadow = font.render(word, True, (20, 14, 8))
            text   = font.render(word, True, (r, g, b))
            rect   = text.get_rect(centerx=cx, top=top)
            surface.blit(shadow, rect.move(1, 1))
            surface.blit(text, rect)
        surface.blit(sub,    sub.get_rect(centerx=cx, top=56))
        surface.blit(byline, byline.get_rect(centerx=cx, top=67))

    def _draw_menu(self, surface: pygame.Surface) -> None:
        font = get_font(8, bold=True)
        cx   = _PANEL_CX
        y0   = 86

        for i, label in enumerate(_ITEMS):
            col  = COL_GOLD if i == self._cursor else COL_WHITE
            surf = font.render(label, True, col)
            r    = surf.get_rect(centerx=cx, top=y0 + i * 14)
            surface.blit(surf, r)
            if i == self._cursor:
                arrow = font.render(">", True, COL_GOLD)
                surface.blit(arrow, (r.left - 12, r.top))

        hint = get_font(6).render("Arrows/WASD   Space/Z   Enter", True, (100, 110, 145))
        surface.blit(hint, hint.get_rect(centerx=cx, bottom=_PANEL.bottom - 5))

    # ------------------------------------------------------------------

    @staticmethod
    def _make_panel() -> pygame.Surface:
        panel = pygame.Surface(_PANEL.size, pygame.SRCALPHA)
        rect  = panel.get_rect()
        pygame.draw.rect(panel, _COL_PANEL, rect, border_radius=4)
        pygame.draw.rect(panel, _COL_BORDER, rect, width=1, border_radius=4)
        return panel

    @staticmethod
    def _load_hero() -> pygame.Surface | None:
        path = asset_path("sprites", "hero_strip.png")
        if not path.exists():
            return None
        surf = pygame.image.load(str(path))
        surf = pygame.transform.scale_by(surf, _HERO_SCALE)
        return surf.convert_alpha() if pygame.display.get_surface() else surf

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
