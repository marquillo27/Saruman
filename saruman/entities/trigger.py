from __future__ import annotations

import pygame


class Trigger:
    def __init__(self, x: float, y: float, w: float, h: float) -> None:
        self.rect      = pygame.Rect(int(x), int(y), int(w), int(h))
        self.triggered = False


class WarpTrigger(Trigger):
    def __init__(self, x: float, y: float, w: float, h: float, target_level: str) -> None:
        super().__init__(x, y, w, h)
        self.target_level = target_level  # e.g. "level_03_glass_caverns"


class LevelEndTrigger(Trigger):
    def __init__(self, x: float, y: float, w: float, h: float, score_bonus: int = 0) -> None:
        super().__init__(x, y, w, h)
        self.score_bonus = score_bonus
