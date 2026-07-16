"""
Generate assets/maps/level_08_forsaken_bridge.tmx
Run from project root:  uv run python tools/generate_level_08.py

Map spec:
  150 × 12 tiles (2400 × 192 px)
  Horizontal traversal across a broken stone bridge with frequent gaps.
  Showcases SpitterPlant, Slime, MimicChest, MovingPlatform, Spring,
  plus SkeletonArcher and CaveBat for variety.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_08_forsaken_bridge.tmx")

W = 150
H = 12

TS = 16


def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]
    # Full ground row 11
    for x in range(W):
        grid[11][x] = 1
    # Pit gaps — wide ones span moving-platform crossings
    pits = [(18, 22), (32, 38), (50, 54), (68, 75), (90, 94),
            (108, 114), (124, 128), (140, 144)]
    for px0, px1 in pits:
        for x in range(px0, px1):
            grid[11][x] = 0
    # Elevated stone platforms
    platforms = [
        (6,   12, 8),
        (24,  30, 7),
        (42,  48, 8),
        (58,  66, 7),
        (78,  86, 8),
        (96,  104, 7),
        (118, 122, 8),
        (132, 138, 7),
    ]
    for px0, px1, row in platforms:
        for x in range(px0, px1):
            grid[row][x] = 3
    return grid


def _px(tx: int) -> int:
    return tx * TS


def _py(ty: int) -> int:
    return ty * TS


def _objects() -> list[dict]:
    objs: list[dict] = []
    oid = 1

    def _add(otype: str, x: int, y: int, w: int = 16, h: int = 16,
             props: dict | None = None) -> None:
        nonlocal oid
        objs.append({"id": oid, "type": otype,
                     "x": x, "y": y, "w": w, "h": h,
                     "props": props or {}})
        oid += 1

    _add("PlayerSpawn", _px(1), _py(10), 16, 16)

    # Early patrol pair
    _add("Goblinkin", _px(4),  _py(10), 12, 14)
    _add("Goblinkin", _px(28), _py(10), 12, 14)

    # Skeleton archers at choke points
    _add("SkeletonArcher", _px(14),  _py(10), 12, 16)
    _add("SkeletonArcher", _px(56),  _py(10), 12, 16)
    _add("SkeletonArcher", _px(98),  _py(7),  12, 16)
    _add("SkeletonArcher", _px(120), _py(10), 12, 16)
    _add("SkeletonArcher", _px(146), _py(10), 12, 16)

    # Bats — lurk over chasms
    _add("CaveBat", _px(20),  _py(5), 64, 8)
    _add("CaveBat", _px(34),  _py(4), 80, 8)
    _add("CaveBat", _px(52),  _py(5), 64, 8)
    _add("CaveBat", _px(70),  _py(3), 80, 8)
    _add("CaveBat", _px(108), _py(4), 80, 8)
    _add("CaveBat", _px(140), _py(5), 64, 8)

    # Slimes scattered along the path
    _add("Slime", _px(40),  _py(10), 10, 8)
    _add("Slime", _px(82),  _py(7),  10, 8)
    _add("Slime", _px(132), _py(10), 10, 8)

    # SpitterPlants — turret hazards forcing player to dash through
    _add("SpitterPlant", _px(46),  _py(10), 12, 12)
    _add("SpitterPlant", _px(88),  _py(10), 12, 12)
    _add("SpitterPlant", _px(116), _py(10), 12, 12)
    _add("SpitterPlant", _px(138), _py(7),  12, 12)

    # Mimics — disguised as gems on a platform; surprises
    _add("MimicChest", _px(62),  _py(7) - 12, 14, 12)
    _add("MimicChest", _px(102), _py(7) - 12, 14, 12)

    # MovingPlatforms — horizontal carriers over wide chasms
    _add("MovingPlatform", _px(34) + 4, _py(8),  32, 8,
         props={"axis": "x", "range": 56})
    _add("MovingPlatform", _px(70) + 4, _py(8),  32, 8,
         props={"axis": "x", "range": 72})
    _add("MovingPlatform", _px(108) + 4, _py(8), 32, 8,
         props={"axis": "x", "range": 72})

    # Springs — vertical boost shortcuts
    _add("Spring", _px(10),  _py(10) + 10, 12, 6)
    _add("Spring", _px(126), _py(10) + 10, 12, 6)

    # Coins
    coin_positions = [
        (_px(7),   _py(7)),
        (_px(26),  _py(6)),
        (_px(44),  _py(7)),
        (_px(60),  _py(6)),
        (_px(80),  _py(7)),
        (_px(85),  _py(7)),
        (_px(100), _py(6)),
        (_px(120), _py(7)),
        (_px(135), _py(6)),
        (_px(146), _py(10)),
        (_px(147), _py(10)),
        (_px(148), _py(10)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Gems — high-value rewards
    _add("Gem", _px(60), _py(6), 8, 8, props={"color": "red"})
    _add("Gem", _px(100), _py(6), 8, 8, props={"color": "green"})

    # Heart
    _add("Heart", _px(72), _py(10), 9, 9)

    # Spikes — forcing careful navigation near chasms
    _add("Spike", _px(35), _py(11), 16, 8)   # first chasm approach
    _add("Spike", _px(72), _py(11), 16, 8)   # center gap
    _add("Spike", _px(115), _py(11), 16, 8)  # near MimicChest zone
    _add("Spike", _px(141), _py(11), 16, 8)  # final approach

    # Level end — full-height column so the player can't jump past it
    _add("LevelEnd", _px(148), 0, 16, H * TS,
         props={"score_bonus": 8000})

    return objs


def main() -> None:
    grid = _build_grid()
    objs = _objects()
    tmx  = build_tmx(grid, objs, W, H, TS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(tmx)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
