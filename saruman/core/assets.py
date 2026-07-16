from __future__ import annotations

import pygame

from saruman.paths import asset_path

_sprites: dict[str, pygame.Surface | None] = {}
_flipped: dict[str, pygame.Surface | None] = {}
_strips:  dict[str, pygame.Surface | None] = {}
_strip_frames: dict[tuple, pygame.Surface | None] = {}


def get_sprite(name: str, flip_x: bool = False) -> pygame.Surface | None:
    """Lazy-load assets/sprites/<name>.png; None on missing file.
    Both orientations are cached so flip is only computed once."""
    if flip_x:
        if name not in _flipped:
            base = get_sprite(name, False)
            _flipped[name] = pygame.transform.flip(base, True, False) if base else None
        return _flipped[name]
    if name not in _sprites:
        try:
            path = asset_path("sprites", name + ".png")
            _sprites[name] = pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            _sprites[name] = None
    return _sprites[name]


def get_strip_frame(
    name: str, frame: int, w: int, h: int, flip_x: bool = False
) -> pygame.Surface | None:
    """Load one frame from assets/sprites/<name>_strip.png.
    Falls back to get_sprite(name, flip_x) if strip file is absent."""
    key = (name, frame, flip_x)
    if key not in _strip_frames:
        strip_name = name + "_strip"
        if strip_name not in _strips:
            try:
                path = asset_path("sprites", strip_name + ".png")
                _strips[strip_name] = pygame.image.load(str(path)).convert_alpha()
            except (FileNotFoundError, pygame.error):
                _strips[strip_name] = None
        strip = _strips[strip_name]
        if strip is None:
            _strip_frames[key] = get_sprite(name, flip_x)
        else:
            frame_surf = strip.subsurface((frame * w, 0, w, h)).copy()
            _strip_frames[key] = (
                pygame.transform.flip(frame_surf, True, False) if flip_x
                else frame_surf
            )
    return _strip_frames[key]
