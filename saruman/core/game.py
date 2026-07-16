from __future__ import annotations

import random

import numpy as np
import pygame

from saruman.config import (
    FPS, INTERNAL_H, INTERNAL_W, TITLE, WINDOW_H, WINDOW_W,
)
from saruman.core.state import StateStack


def _make_vignette(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    X, Y = np.mgrid[0:w, 0:h].astype(np.float32)
    cx, cy = w / 2.0, h / 2.0
    dist = ((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2
    alpha = np.clip(dist * 160, 0, 180).astype(np.uint8)
    arr = pygame.surfarray.pixels_alpha(surf)
    arr[:, :] = alpha
    del arr
    return surf


def _make_scanlines(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    for y in range(0, h, 2):
        pygame.draw.line(surf, (0, 0, 0, 35), (0, y), (w - 1, y))
    return surf


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption(TITLE)
        self._canvas    = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self._scaled    = pygame.Surface((WINDOW_W, WINDOW_H))
        self._clock     = pygame.time.Clock()
        self._states    = StateStack()
        self._running   = True
        self._shake     = 0
        self._vignette  = _make_vignette(WINDOW_W, WINDOW_H)
        self._scanlines = _make_scanlines(WINDOW_W, WINDOW_H)

        # Apply saved settings
        from saruman.save import settings as _cfg
        s = _cfg.get()
        from saruman.core.audio import get_audio
        audio = get_audio()
        audio.set_music_volume(s["music_volume"])
        audio.set_sfx_volume(s["sfx_volume"])
        if s["fullscreen"]:
            self._window = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.FULLSCREEN)

    @property
    def states(self) -> StateStack:
        return self._states

    def quit(self) -> None:
        self._running = False

    def shake(self, frames: int = 10) -> None:
        self._shake = max(self._shake, frames)

    def set_fullscreen(self, flag: bool) -> None:
        flags = pygame.FULLSCREEN if flag else 0
        self._window = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)

    def run(self) -> None:
        from saruman.states.menu import MenuState
        self._states.push(MenuState(self))

        while self._running and not self._states.is_empty():
            dt = min(self._clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                else:
                    self._states.handle_event(event)

            self._states.update(dt)
            self._canvas.fill((0, 0, 0))
            self._states.draw(self._canvas)

            pygame.transform.scale(self._canvas, (WINDOW_W, WINDOW_H), self._scaled)
            self._scaled.blit(self._vignette,  (0, 0))
            self._scaled.blit(self._scanlines, (0, 0))

            if self._shake > 0:
                ox = random.randint(-3, 3) * 2
                oy = random.randint(-2, 2) * 2
                self._shake -= 1
                self._window.fill((0, 0, 0))
                self._window.blit(self._scaled, (ox, oy))
            else:
                self._window.blit(self._scaled, (0, 0))

            pygame.display.flip()
            pygame.display.set_caption(f"{TITLE}  |  {self._clock.get_fps():.0f} fps")

        pygame.quit()
