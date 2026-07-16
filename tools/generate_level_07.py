"""
Generate assets/maps/level_07_cursed_catacombs.tmx
Run from project root:  uv run python tools/generate_level_07.py

Map spec:
  140 × 12 tiles (2240 × 192 px)
  Tile size: 16 × 16
  Ground solid at row 11 (bottom row, tile id = 1)
  Elevated platforms at rows 7–8 (tile id = 3)
  Several pit gaps to challenge traversal (bats lurk over pits)
  Entities: 5× SkeletonArcher, 6× CaveBat, 2× Goblinkin, 3× Slime,
            1× SpitterPlant, 1× Spring, 12× Coin, 1× Gem, 1× Heart, 1× LevelEnd
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_07_cursed_catacombs.tmx")

W = 140   # map width  in tiles
H = 12    # map height in tiles

TS = 16   # tile size px


# ---------------------------------------------------------------------------
# Build tile grid (row-major, row 0 = top)
# ---------------------------------------------------------------------------

def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]

    # Full ground row at row 11
    for x in range(W):
        grid[11][x] = 1

    # Pit gaps
    pits = [(15, 17), (32, 34), (50, 52), (68, 70), (82, 84),
            (98, 100), (114, 117), (128, 130)]
    for px0, px1 in pits:
        for x in range(px0, px1):
            grid[11][x] = 0

    # Elevated platforms
    platforms = [
        (5,   10,  8),
        (20,  26,  7),
        (38,  44,  8),
        (55,  61,  7),
        (72,  78,  8),
        (88,  94,  7),
        (104, 110, 8),
        (120, 126, 7),
    ]
    for px0, px1, row in platforms:
        for x in range(px0, px1):
            grid[row][x] = 3

    return grid


# ---------------------------------------------------------------------------
# Build object list
# ---------------------------------------------------------------------------

def _px(tx: int) -> int:
    """Tile col → pixel x (left edge)."""
    return tx * TS


def _py(ty: int) -> int:
    """Tile row → pixel y (top edge)."""
    return ty * TS


def _objects() -> list[dict]:
    """Return list of object dicts with keys: id, type, x, y, w, h, props."""
    objs: list[dict] = []
    oid = 1

    def _add(otype: str, x: int, y: int, w: int = 16, h: int = 16,
             props: dict | None = None) -> None:
        nonlocal oid
        objs.append({"id": oid, "type": otype,
                     "x": x, "y": y, "w": w, "h": h,
                     "props": props or {}})
        oid += 1

    # Player spawn — left end, standing on ground
    _add("PlayerSpawn", _px(1), _py(10), 16, 16)

    # Goblinkins — early patrol guards
    _add("Goblinkin", _px(3),   _py(10), 12, 14)
    _add("Goblinkin", _px(25),  _py(10), 12, 14)

    # SkeletonArchers — ranged guards at strategic choke points
    _add("SkeletonArcher", _px(12),  _py(10), 12, 16)
    _add("SkeletonArcher", _px(46),  _py(7),  12, 16)
    _add("SkeletonArcher", _px(75),  _py(10), 12, 16)
    _add("SkeletonArcher", _px(106), _py(7),  12, 16)
    _add("SkeletonArcher", _px(125), _py(10), 12, 16)

    # CaveBats — lurk over pit gaps
    _add("CaveBat", _px(15),  _py(5), 64, 8)
    _add("CaveBat", _px(32),  _py(4), 64, 8)
    _add("CaveBat", _px(50),  _py(5), 64, 8)
    _add("CaveBat", _px(68),  _py(4), 48, 8)
    _add("CaveBat", _px(98),  _py(5), 64, 8)
    _add("CaveBat", _px(114), _py(4), 48, 8)

    # Slimes — splitting hop enemies
    _add("Slime", _px(35),  _py(10), 10, 8)
    _add("Slime", _px(63),  _py(10), 10, 8)
    _add("Slime", _px(118), _py(10), 10, 8)

    # SpitterPlant — immobile turret at a mid-level chokepoint
    _add("SpitterPlant", _px(91), _py(10), 12, 12)

    # Spring — vertical shortcut over the last big pit
    _add("Spring", _px(127), _py(10) + 10, 12, 6)

    # Coins scattered across the level
    coin_positions = [
        (_px(6),   _py(7)),
        (_px(22),  _py(6)),
        (_px(40),  _py(7)),
        (_px(57),  _py(6)),
        (_px(73),  _py(7)),
        (_px(85),  _py(10)),
        (_px(90),  _py(7)),
        (_px(105), _py(7)),
        (_px(122), _py(6)),
        (_px(133), _py(10)),
        (_px(136), _py(10)),
        (_px(138), _py(10)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Gem — high-value reward up high
    _add("Gem", _px(90), _py(6), 8, 8, props={"color": "purple"})

    # Heart — reward after the mid-level gauntlet
    _add("Heart", _px(56), _py(10), 9, 9)

    # Spikes — narrow passage hazards
    _add("Spike", _px(18), _py(11), 16, 8)   # before the first archer
    _add("Spike", _px(52), _py(11), 16, 8)   # near slime cluster
    _add("Spike", _px(95), _py(11), 16, 8)   # SpitterPlant zone

    # Level end — full-height column so the player can't jump past it
    _add("LevelEnd", _px(138), 0, 16, H * TS,
         props={"score_bonus": 6000})

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
