from __future__ import annotations

import math

import pygame

from saruman.core.assets import get_sprite, get_strip_frame


class Interactive:
    """Base class for environment objects the player can interact with."""
    W: int = 16
    H: int = 16

    def __init__(self, x: float, y: float) -> None:
        self.x      = x
        self.y      = y
        self.alive  = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, dt: float) -> None:
        raise NotImplementedError

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        raise NotImplementedError


class Spring(Interactive):
    """Bounce pad. Touching from above launches the player upward and refreshes air jump."""
    W            = 12
    H            = 6
    LAUNCH_VEL_Y = -13.0
    _ANIM_FRAMES = 8

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self._activation = 0   # counts down while compressed/releasing

    def trigger(self) -> None:
        self._activation = self._ANIM_FRAMES

    def update(self, dt: float) -> None:
        if self._activation > 0:
            self._activation -= 1

    def player_overlap_from_above(self, player) -> bool:
        """Return True if the player is falling and overlaps the spring's top face."""
        if player.vel_y <= 0:
            return False
        pr = player.rect
        if not pr.colliderect(self.rect):
            return False
        # Foot must be near the top of the spring (within 6 px)
        return pr.bottom <= self.rect.top + 6

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = 1 if self._activation > 0 else 0
        spr = get_strip_frame("spring", frame, self.W, self.H)
        if spr:
            surface.blit(spr, (sx, sy))
            return
        # Fallback: compressed when active, extended when idle
        if self._activation > 0:
            pygame.draw.rect(surface, (180, 180, 60), (sx, sy + 3, self.W, 3))
            pygame.draw.rect(surface, (110, 110, 30), (sx, sy + 1, self.W, 2))
        else:
            pygame.draw.rect(surface, (180, 180, 60), (sx, sy + 4, self.W, 2))
            pygame.draw.rect(surface, (110, 110, 30), (sx + 1, sy, self.W - 2, 4))


class MovingPlatform(Interactive):
    """Solid one-way platform that moves between two endpoints on a cosine LERP."""
    W           = 32
    H           = 8
    PERIOD      = 180   # frames for a full back-and-forth cycle

    def __init__(
        self, x: float, y: float, axis: str = "x", range_px: float = 64.0,
    ) -> None:
        super().__init__(x, y)
        self.axis     = axis if axis in ("x", "y") else "x"
        self.range_px = float(range_px)
        self._spawn_x = x
        self._spawn_y = y
        self._tick    = 0
        # Previous frame position — World uses delta to carry the player
        self.prev_x   = x
        self.prev_y   = y

    @property
    def delta_x(self) -> float:
        return self.x - self.prev_x

    @property
    def delta_y(self) -> float:
        return self.y - self.prev_y

    def update(self, dt: float) -> None:
        self.prev_x = self.x
        self.prev_y = self.y
        self._tick += 1
        # 0..1..0 cosine LERP across PERIOD frames
        phase = (1.0 - math.cos(2.0 * math.pi * (self._tick / self.PERIOD))) * 0.5
        offset = phase * self.range_px
        if self.axis == "x":
            self.x = self._spawn_x + offset
        else:
            self.y = self._spawn_y + offset

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_strip_frame("platform", 0, self.W, self.H)
        if spr:
            surface.blit(spr, (sx, sy))
            return
        # Stone slab fallback
        pygame.draw.rect(surface, (110, 100, 90), (sx, sy, self.W, self.H))
        pygame.draw.rect(surface, (160, 150, 130), (sx, sy, self.W, 2))
        for bx in range(sx + 4, sx + self.W, 6):
            pygame.draw.rect(surface, (80, 70, 60), (bx, sy + 3, 1, self.H - 4))


class Spike(Interactive):
    """Static floor hazard. Damages the player on any overlap."""
    W = 16
    H = 8

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)

    def update(self, dt: float) -> None:
        pass   # static — never moves or despawns

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        spr = get_sprite("spike")
        if spr:
            surface.blit(spr, (sx, sy))
            return
        # Fallback: three steel-gray upward triangles
        for i in range(3):
            bx = sx + 1 + i * 5
            pygame.draw.polygon(
                surface, (122, 128, 128),
                [(bx, sy + self.H - 1), (bx + 4, sy + self.H - 1), (bx + 2, sy)],
            )
            pygame.draw.polygon(
                surface, (58, 64, 64),
                [(bx, sy + self.H - 1), (bx + 4, sy + self.H - 1), (bx + 2, sy)],
                1,
            )
