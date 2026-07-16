from __future__ import annotations

import pygame

from saruman.paths import asset_path

_cache: dict[tuple, pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _cache:
        ttf = asset_path("fonts", "kenney_pixel.ttf")
        if ttf.exists():
            _cache[key] = pygame.font.Font(str(ttf), size)
        else:
            _cache[key] = pygame.font.SysFont("consolas,monospace", size, bold=bold)
    return _cache[key]
