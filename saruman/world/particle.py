from __future__ import annotations

import math
import random

import pygame


class Particle:
    GRAVITY = 0.28

    def __init__(
        self,
        x: float, y: float,
        vel_x: float, vel_y: float,
        color: tuple[int, int, int],
        life: int,
    ) -> None:
        self.x = x
        self.y = y
        self.vel_x  = vel_x
        self.vel_y  = vel_y
        self.color  = color
        self.life   = life
        self.max_life = life
        self.alive  = True

    def update(self) -> None:
        self.vel_y += self.GRAVITY
        self.x += self.vel_x
        self.y += self.vel_y
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frac = self.life / self.max_life
        r, g, b = self.color
        col = (int(r * frac), int(g * frac), int(b * frac))
        radius = max(1, int(2 * frac))
        pygame.draw.circle(surface, col, (sx + 1, sy + 1), radius)


class AmbientParticle(Particle):
    """Atmospheric particle: no gravity, color stays constant, only size fades."""
    GRAVITY = 0.0

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frac   = self.life / self.max_life
        radius = max(1, int(2 * frac))
        pygame.draw.circle(surface, self.color, (sx + 1, sy + 1), radius)


def burst(
    x: float,
    y: float,
    color: tuple[int, int, int],
    count: int = 10,
    speed: float = 2.5,
) -> list[Particle]:
    particles = []
    for i in range(count):
        angle  = (i / count) * math.tau + random.uniform(-0.3, 0.3)
        mag    = speed * (0.4 + random.random() * 0.8)
        vx     = math.cos(angle) * mag
        vy     = math.sin(angle) * mag - 1.0   # slight upward bias
        life   = random.randint(10, 18)
        particles.append(Particle(x, y, vx, vy, color, life))
    return particles
