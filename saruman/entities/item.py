from __future__ import annotations

import math

import pygame

from saruman.core.assets import get_sprite, get_strip_frame


class Item:
    W: int = 8
    H: int = 8
    score_value: int = 0

    def __init__(self, x: float, y: float) -> None:
        self.x     = x
        self.y     = y
        self.alive = True
        self._time = 0.0

    @property
    def rect(self) -> pygame.Rect:
        oy = math.sin(self._time * 3.0) * 2.0
        return pygame.Rect(int(self.x), int(self.y + oy), self.W, self.H)

    def update(self, dt: float) -> None:
        self._time += dt

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        raise NotImplementedError


class Coin(Item):
    W = 8
    H = 8
    score_value = 100

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = int(self._time * 6) % 4
        spr = get_strip_frame("item_coin", frame, self.W, self.H)
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            pygame.draw.rect(surface, (212, 161, 85), (sx + 1, sy, 6, 8))
            pygame.draw.rect(surface, (240, 200, 120), (sx + 2, sy + 1, 4, 6))


class Heart(Item):
    W = 9
    H = 9

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("item_heart")
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            col = (210, 50, 50)
            pygame.draw.rect(surface, col, (sx + 1, sy,     3, 2))
            pygame.draw.rect(surface, col, (sx + 5, sy,     3, 2))
            pygame.draw.rect(surface, col, (sx,     sy + 2, 8, 3))
            pygame.draw.rect(surface, col, (sx + 1, sy + 5, 6, 2))
            pygame.draw.rect(surface, col, (sx + 2, sy + 7, 4, 1))


class WeaponUpgrade(Item):
    W = 10
    H = 10

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("item_weapon")
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            pygame.draw.rect(surface, (20, 180, 180), (sx + 3, sy,     4, 3))
            pygame.draw.rect(surface, (20, 180, 180), (sx,     sy + 3, 10, 4))
            pygame.draw.rect(surface, (20, 180, 180), (sx + 3, sy + 7, 4, 3))
            pygame.draw.rect(surface, (120, 240, 240), (sx + 3, sy + 3, 4, 4))


class ShieldPickup(Item):
    """Bonus: grants ~10 s of invulnerability."""
    W = 10
    H = 10

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("item_shield")
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            col, lite = (60, 120, 220), (150, 200, 255)
            pygame.draw.polygon(surface, col, [
                (sx + 5, sy), (sx + 9, sy + 2),
                (sx + 9, sy + 6), (sx + 5, sy + 9), (sx + 1, sy + 6), (sx + 1, sy + 2),
            ])
            pygame.draw.line(surface, lite, (sx + 5, sy + 2), (sx + 5, sy + 7), 1)
            pygame.draw.line(surface, lite, (sx + 3, sy + 4), (sx + 7, sy + 4), 1)


class NukePickup(Item):
    """Bonus: wipes all non-boss enemies on screen."""
    W = 12
    H = 12

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("item_nuke")
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            pygame.draw.circle(surface, (30, 30, 38), (sx + 6, sy + 7), 5)
            pygame.draw.circle(surface, (90, 90, 110), (sx + 6, sy + 7), 5, 1)
            pygame.draw.rect(surface, (140, 110, 60), (sx + 5, sy + 1, 2, 2))
            pygame.draw.rect(surface, (255, 180, 60), (sx + 6, sy, 1, 1))


class FruitPickup(Item):
    """Bonus: turns all non-boss enemies into harmless fruit for ~10 s."""
    W = 10
    H = 10

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("item_fruit")
        if spr:
            surface.blit(spr, (sx, sy))
        else:
            pygame.draw.circle(surface, (210, 50, 60), (sx + 5, sy + 6), 4)
            pygame.draw.rect(surface, (110, 70, 30), (sx + 5, sy + 1, 1, 3))
            pygame.draw.polygon(surface, (60, 170, 70),
                                [(sx + 6, sy + 1), (sx + 9, sy), (sx + 7, sy + 3)])


_GEM_PALETTE = {
    "blue":   ((40, 110, 220), (130, 200, 255)),
    "red":    ((200,  50,  70), (255, 140, 160)),
    "green":  ((40, 180,  90), (140, 240, 170)),
    "purple": ((130,  60, 200), (210, 160, 255)),
}


class Gem(Item):
    """High-value collectible — five times a coin."""
    W           = 8
    H           = 8
    score_value = 500

    def __init__(self, x: float, y: float, color: str = "blue") -> None:
        super().__init__(x, y)
        self.color = color if color in _GEM_PALETTE else "blue"

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_strip_frame(f"item_gem_{self.color}", 0, self.W, self.H)
        if spr:
            surface.blit(spr, (sx, sy))
            return
        dark, light = _GEM_PALETTE[self.color]
        # Faceted diamond shape
        pygame.draw.polygon(surface, dark, [
            (sx + self.W // 2, sy),
            (sx + self.W - 1, sy + self.H // 2),
            (sx + self.W // 2, sy + self.H - 1),
            (sx, sy + self.H // 2),
        ])
        pygame.draw.polygon(surface, light, [
            (sx + self.W // 2, sy + 2),
            (sx + self.W // 2 + 2, sy + self.H // 2),
            (sx + self.W // 2, sy + self.H - 3),
            (sx + self.W // 2 - 2, sy + self.H // 2),
        ])
