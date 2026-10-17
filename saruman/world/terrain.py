"""Biome terrain skins: solid tiles rendered from the collision grid.

Each level's solid tiles are painted once, at load time, into a single
surface. Every tile looks at its neighbours: an exposed top gets the biome's
surface cap (grass, ash crust, snow...), exposed sides get a rim, an exposed
underside gets a shadow (or icicles), and tiles further from the surface get
darker so thick ground reads as depth. Per-tile details are seeded from the
tile position, so a level always looks the same.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from saruman.config import TILE_SIZE

T = TILE_SIZE
Color = tuple[int, int, int]


@dataclass(frozen=True)
class Skin:
    fill:     tuple[Color, Color, Color]   # base, light speck, dark speck
    deep:     Color                        # colour the fill darkens toward
    outline:  Color
    cap:      tuple[Color, Color, Color]   # top colour, highlight, underside
    cap_h:    int                          # cap thickness in px
    accent:   Color | None = None          # sparse glowing bits (embers, crystals)
    bricks:   bool = False                 # draw mortar lines (masonry)
    drips:    Color | None = None          # icicles / hanging moss under overhangs


SKINS: dict[str, Skin] = {
    "greenwood": Skin(
        fill=((112, 78, 52), (138, 100, 66), (84, 57, 40)), deep=(40, 28, 24),
        outline=(30, 22, 18),
        cap=((92, 168, 70), (150, 210, 96), (52, 108, 48)), cap_h=4,
        drips=(52, 108, 48)),
    "cavern": Skin(
        fill=((70, 52, 96), (96, 74, 128), (50, 36, 72)), deep=(22, 16, 36),
        outline=(16, 12, 28),
        cap=((60, 170, 160), (140, 240, 220), (36, 104, 110)), cap_h=3,
        accent=(120, 250, 230)),
    "scorch": Skin(
        fill=((62, 54, 56), (84, 74, 74), (42, 36, 40)), deep=(22, 16, 18),
        outline=(16, 12, 14),
        cap=((150, 140, 132), (196, 186, 176), (98, 88, 84)), cap_h=3,
        accent=(255, 128, 40)),
    "frozen": Skin(
        fill=((92, 110, 138), (118, 138, 168), (68, 84, 110)), deep=(30, 38, 58),
        outline=(22, 28, 44),
        cap=((226, 236, 248), (255, 255, 255), (170, 196, 226)), cap_h=5,
        bricks=True, drips=(200, 228, 250)),
}

# Which skin each level uses (by .tmx stem); unknown levels fall back to greenwood.
LEVEL_SKIN: dict[str, str] = {
    "level_01_greenshire_hills":    "greenwood",
    "level_02_wolfwood":            "greenwood",
    "level_03_glass_caverns":       "cavern",
    "level_04_sunken_mines":        "greenwood",
    "level_11_ashfall_wastes":      "scorch",
    "level_12_cinderwood_remains":  "scorch",
    "level_05_ash_marshes":         "scorch",
    "level_10_goblin_kings_throne": "scorch",
    "level_06_pale_tower":          "frozen",
    "level_09_skybound_spires":     "frozen",
    "level_08_forsaken_bridge":     "frozen",
    "level_07_cursed_catacombs":    "frozen",
    "level_13_emberfall_keep":      "frozen",
}

_DEPTH_STEPS = 4   # tiles below the surface until the fill is fully "deep"


def skin_for(level_name: str) -> Skin:
    return SKINS[LEVEL_SKIN.get(level_name, "greenwood")]


def _mix(a: Color, b: Color, t: float) -> Color:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def render_terrain(grid: list[list[bool]], skin: Skin) -> pygame.Surface:
    """Paint every solid cell of `grid` (rows of bools) with `skin`."""
    h, w = len(grid), len(grid[0]) if grid else 0
    surf = pygame.Surface((w * T, h * T), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    def solid(tx: int, ty: int) -> bool:
        if tx < 0 or tx >= w:
            return True           # level edges continue the ground
        if ty < 0 or ty >= h:
            return ty >= h        # below the map is solid, above is open air
        return grid[ty][tx]

    for ty in range(h):
        for tx in range(w):
            if grid[ty][tx]:
                _paint_tile(surf, tx, ty, skin, solid)
    # Second pass: drips hang into the air cell below an overhang.
    if skin.drips:
        for ty in range(h):
            for tx in range(w):
                if grid[ty][tx] and not solid(tx, ty + 1):
                    _paint_drips(surf, tx, ty, skin)
    return surf


def _paint_tile(surf: pygame.Surface, tx: int, ty: int, skin: Skin, solid) -> None:
    rng = random.Random(tx * 7919 + ty * 104729)
    x0, y0 = tx * T, ty * T

    # Depth: distance to the nearest open cell above (capped).
    depth = 0
    while depth < _DEPTH_STEPS and solid(tx, ty - depth - 1):
        depth += 1
    shade = depth / _DEPTH_STEPS * 0.75
    base, light, dark = (_mix(c, skin.deep, shade) for c in skin.fill)

    surf.fill(base, (x0, y0, T, T))
    for _ in range(5):                                   # specks
        sx, sy = rng.randrange(T - 2), rng.randrange(T - 2)
        surf.fill(rng.choice((light, dark)), (x0 + sx, y0 + sy, rng.choice((1, 2)), 1))
    if rng.random() < 0.18:                              # a pebble
        px, py = rng.randrange(2, T - 5), rng.randrange(6, T - 4)
        surf.fill(dark, (x0 + px, y0 + py + 1, 4, 2))
        surf.fill(light, (x0 + px + 1, y0 + py, 2, 1))
    if skin.bricks:
        mortar = _mix(base, skin.outline, 0.5)
        for row in (0, 8):
            surf.fill(mortar, (x0, y0 + row, T, 1))
        off = 4 if ty % 2 else 12
        surf.fill(mortar, (x0 + off, y0, 1, 8))
        surf.fill(mortar, (x0 + (off + 8) % T, y0 + 8, 1, 8))
    if skin.accent and depth >= 1 and rng.random() < 0.12:
        ax, ay = rng.randrange(2, T - 3), rng.randrange(3, T - 3)
        surf.fill(skin.accent, (x0 + ax, y0 + ay, 1, 2))
        surf.fill(_mix(skin.accent, base, 0.5), (x0 + ax + 1, y0 + ay + 1, 1, 1))

    open_l, open_r = not solid(tx - 1, ty), not solid(tx + 1, ty)
    open_t, open_b = not solid(tx, ty - 1), not solid(tx, ty + 1)

    # Rims on exposed sides: dark outline plus a 1 px highlight inside.
    if open_l:
        surf.fill(skin.outline, (x0, y0, 1, T))
        surf.fill(light, (x0 + 1, y0, 1, T))
    if open_r:
        surf.fill(skin.outline, (x0 + T - 1, y0, 1, T))
        surf.fill(dark, (x0 + T - 2, y0, 1, T))
    if open_b:
        surf.fill(dark, (x0, y0 + T - 3, T, 2))
        surf.fill(skin.outline, (x0, y0 + T - 1, T, 1))

    if open_t:
        _paint_cap(surf, x0, y0, skin, rng, open_l, open_r)


def _paint_cap(surf, x0: int, y0: int, skin: Skin, rng: random.Random,
               open_l: bool, open_r: bool) -> None:
    top, hi, under = skin.cap
    ch = skin.cap_h
    surf.fill(skin.outline, (x0, y0, T, 1))
    surf.fill(top, (x0, y0 + 1, T, ch))
    surf.fill(hi, (x0, y0 + 1, T, 1))
    # Ragged lower edge of the cap hanging over the fill.
    for x in range(T):
        drop = rng.choice((0, 0, 1, 1, 2))
        surf.fill(under, (x0 + x, y0 + 1 + ch, 1, drop + 1))
    # Little tufts / sparkles on top.
    for _ in range(2):
        bx = rng.randrange(1, T - 2)
        surf.fill(hi, (x0 + bx, y0 + 2, 1, 1))
    if open_l:
        surf.fill(skin.outline, (x0, y0, 1, ch + 2))
    if open_r:
        surf.fill(skin.outline, (x0 + T - 1, y0, 1, ch + 2))


def _paint_drips(surf, tx: int, ty: int, skin: Skin) -> None:
    rng = random.Random(tx * 31337 + ty * 7)
    x0, y_below = tx * T, (ty + 1) * T
    if y_below >= surf.get_height():
        return
    for _ in range(2):
        if rng.random() < 0.6:
            dx = rng.randrange(2, T - 2)
            length = rng.randrange(2, 6)
            surf.fill(skin.drips, (x0 + dx, y_below, 1, length))
            surf.fill(skin.drips, (x0 + dx - 1, y_below, 3, 1))
