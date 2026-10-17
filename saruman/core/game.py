from __future__ import annotations

import os
import random
import sys

import numpy as np
import pygame

from saruman.config import (
    FPS, INTERNAL_H, INTERNAL_W, TITLE, UI_H, UI_W, WINDOW_H, WINDOW_W,
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


STEP          = 1.0 / FPS   # fixed simulation step (seconds)
MAX_STEPS     = 5           # cap catch-up steps per frame (avoids a death spiral)
_STEP_EPSILON = 0.001       # absorbs Clock.tick()'s whole-millisecond rounding


def fixed_steps(acc: float, frame_dt: float) -> tuple[int, float]:
    """Add one frame's elapsed time to the accumulator and return how many fixed
    simulation steps to run plus the leftover time. A long stall (dragging the
    window, a breakpoint) runs at most MAX_STEPS and drops the rest, so the game
    slows down briefly instead of fast-forwarding."""
    acc  += min(frame_dt, STEP * MAX_STEPS)
    steps = 0
    while acc >= STEP - _STEP_EPSILON and steps < MAX_STEPS:
        acc   -= STEP
        steps += 1
    return steps, acc


def _make_scanlines(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    for y in range(0, h, 2):
        pygame.draw.line(surf, (0, 0, 0, 35), (0, y), (w - 1, y))
    return surf


def _prepare_display() -> None:
    """Call before pygame.init(): centre the window, and on Windows opt out of
    DPI virtualisation so 125 %/150 % desktop scaling doesn't blur the game or
    shrink fullscreen into a corner of the screen."""
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor aware
        except (AttributeError, OSError):
            pass


class Game:
    # SCALED: SDL scales the 960x540 frame to the window/screen, keeps the
    # aspect ratio and centres it (letterboxing if needed).
    _WINDOWED   = pygame.SCALED | pygame.RESIZABLE
    _FULLSCREEN = pygame.SCALED | pygame.FULLSCREEN

    def __init__(self) -> None:
        _prepare_display()
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._fullscreen = False
        self._window = pygame.display.set_mode((WINDOW_W, WINDOW_H), self._WINDOWED)
        pygame.display.set_caption(TITLE)
        self._canvas    = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self._ui        = pygame.Surface((UI_W, UI_H), pygame.SRCALPHA)
        self._scaled    = pygame.Surface((WINDOW_W, WINDOW_H))
        self._ui_scaled = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
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
            self.set_fullscreen(True)

    @property
    def states(self) -> StateStack:
        return self._states

    def quit(self) -> None:
        self._running = False

    def shake(self, frames: int = 10) -> None:
        self._shake = max(self._shake, frames)

    def set_fullscreen(self, flag: bool) -> None:
        if flag == self._fullscreen:
            return
        self._fullscreen = flag
        flags = self._FULLSCREEN if flag else self._WINDOWED
        self._window = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)

    def toggle_fullscreen(self) -> None:
        """F11 / Alt+Enter: switch and remember the choice."""
        from saruman.save import settings as _cfg
        s = _cfg.get()
        s["fullscreen"] = not self._fullscreen
        self.set_fullscreen(s["fullscreen"])
        _cfg.save()

    def run(self) -> None:
        from saruman.states.menu import MenuState
        self._states.push(MenuState(self))

        acc   = 0.0
        frame = 0
        while self._running and not self._states.is_empty():
            steps, acc = fixed_steps(acc, self._clock.tick(FPS) / 1000.0)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN and (
                    event.key == pygame.K_F11
                    or (event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT)
                ):
                    self.toggle_fullscreen()
                else:
                    self._states.handle_event(event)

            # Simulation always advances in whole 1/60 s steps, so movement,
            # jumps and frame-counted timers behave the same at any frame rate.
            for _ in range(steps):
                self._states.update(STEP)
                if self._shake > 0:
                    self._shake -= 1
                if self._states.is_empty():
                    break

            self._canvas.fill((0, 0, 0))
            self._ui.fill((0, 0, 0, 0))
            self._states.draw(self._canvas, self._ui)

            pygame.transform.scale(self._canvas, (WINDOW_W, WINDOW_H), self._scaled)
            pygame.transform.scale(self._ui, (WINDOW_W, WINDOW_H), self._ui_scaled)
            self._scaled.blit(self._ui_scaled, (0, 0))
            self._scaled.blit(self._vignette,  (0, 0))
            self._scaled.blit(self._scanlines, (0, 0))

            if self._shake > 0:
                ox = random.randint(-3, 3) * 2
                oy = random.randint(-2, 2) * 2
                self._window.fill((0, 0, 0))
                self._window.blit(self._scaled, (ox, oy))
            else:
                self._window.blit(self._scaled, (0, 0))

            pygame.display.flip()
            frame += 1
            if frame % FPS == 0:    # once a second; set_caption is slow on Windows
                pygame.display.set_caption(f"{TITLE}  |  {self._clock.get_fps():.0f} fps")

        pygame.quit()
