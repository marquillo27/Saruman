"""Tests for the CaveBat balance pass: outrunnable, laggy steering, retreat."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from saruman.config import MOVE_SPEED
from saruman.entities.enemy import CaveBat


class _Empty:
    width, height = 100, 20

    def is_solid(self, tx, ty):
        return False


def _chase(bat: CaveBat, target: pygame.Rect, frames: int) -> None:
    for _ in range(frames):
        bat.update(_Empty(), 1 / 60, target)


def test_bat_is_slower_than_the_player():
    assert CaveBat.AGGRO_SPEED < MOVE_SPEED * 0.75


def test_bat_accelerates_gradually():
    bat = CaveBat(100, 100)
    _chase(bat, pygame.Rect(160, 100, 10, 16), 1)
    assert abs(bat._vx) < CaveBat.AGGRO_SPEED * 0.2


def test_bat_retreats_after_touching_player():
    bat = CaveBat(100, 100)
    player = pygame.Rect(80, 100, 10, 16)       # player to the left
    bat.on_player_contact()
    x0, y0 = bat.x, bat.y
    _chase(bat, player, 10)
    assert bat.x > x0 and bat.y < y0            # moving right and up, away


def test_bat_resumes_chase_after_retreat():
    bat = CaveBat(100, 100)
    bat.on_player_contact()
    _chase(bat, pygame.Rect(90, 100, 10, 16), CaveBat.RETREAT_FRAMES)
    _chase(bat, pygame.Rect(bat.x - 60, bat.y, 10, 16), 60)   # player in range again
    assert bat._vx < 0                          # heading back toward the player
