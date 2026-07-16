"""
Generate assets/maps/level_09_skybound_spires.tmx
Run from project root:  uv run python tools/generate_level_09.py

Map spec:
  120 × 18 tiles (1920 × 288 px) — first level with vertical scrolling.
  Vertical climb featuring MovingPlatforms (mixed axes), Springs, and aerial enemies.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_09_skybound_spires.tmx")

W = 120
H = 18

TS = 16


def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]
    # Bottom solid ground for traversal start
    for x in range(W):
        grid[17][x] = 1
    # Stepping spires — tall stone columns rising at intervals
    spire_cols = [
        ( 6, 14, 16),   # x range 6..13, top row 14 (4 tiles tall)
        (20, 26, 12),
        (34, 40, 10),
        (48, 54,  8),
        (62, 68,  6),
        (76, 82,  4),   # high spire
        (88, 94,  6),
        (100, 106, 4),
        (110, 118, 2),  # final summit
    ]
    for x0, x1, top in spire_cols:
        for x in range(x0, x1):
            for y in range(top, 17):
                grid[y][x] = 3
    # A few mid-air ledges
    ledges = [
        (16, 22, 8),
        (42, 48, 6),
        (58, 64, 12),
        (84, 90, 10),
        (96, 102, 8),
    ]
    for x0, x1, row in ledges:
        for x in range(x0, x1):
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

    # Player starts at the bottom-left
    _add("PlayerSpawn", _px(2), _py(16), 16, 16)

    # Goblinkins guarding the lower path
    _add("Goblinkin", _px(8),  _py(13), 12, 14)
    _add("Goblinkin", _px(22), _py(11), 12, 14)
    _add("Goblinkin", _px(36), _py( 9), 12, 14)

    # Slimes on stepping platforms
    _add("Slime", _px(44), _py(5),  10, 8)
    _add("Slime", _px(64), _py(5),  10, 8)
    _add("Slime", _px(86), _py(9),  10, 8)
    _add("Slime", _px(98), _py(7),  10, 8)

    # SpitterPlants — turret hazards on ledges
    _add("SpitterPlant", _px(18), _py( 7), 12, 12)
    _add("SpitterPlant", _px(60), _py(11), 12, 12)
    _add("SpitterPlant", _px(96), _py( 7), 12, 12)

    # CaveBats — between spires, swooping
    _add("CaveBat", _px(14), _py(10), 80, 8)
    _add("CaveBat", _px(30), _py( 8), 80, 8)
    _add("CaveBat", _px(50), _py( 6), 96, 8)
    _add("CaveBat", _px(72), _py( 4), 80, 8)
    _add("CaveBat", _px(88), _py( 6), 64, 8)
    _add("CaveBat", _px(104), _py(4), 80, 8)

    # MovingPlatforms — chained climb across the gaps
    _add("MovingPlatform", _px(14) + 4, _py(15), 32, 8,
         props={"axis": "x", "range": 64})
    _add("MovingPlatform", _px(28) + 4, _py(13), 32, 8,
         props={"axis": "y", "range": 48})
    _add("MovingPlatform", _px(40) + 4, _py(11), 32, 8,
         props={"axis": "x", "range": 64})
    _add("MovingPlatform", _px(54) + 4, _py( 9), 32, 8,
         props={"axis": "y", "range": 48})
    _add("MovingPlatform", _px(68) + 4, _py( 7), 32, 8,
         props={"axis": "x", "range": 64})
    _add("MovingPlatform", _px(94) + 4, _py( 5), 32, 8,
         props={"axis": "y", "range": 48})

    # Springs — quick vertical boost at key spots
    _add("Spring", _px(7),  _py(13) + 10, 12, 6)
    _add("Spring", _px(35), _py( 9) + 10, 12, 6)
    _add("Spring", _px(63), _py( 5) + 10, 12, 6)
    _add("Spring", _px(89), _py( 5) + 10, 12, 6)
    _add("Spring", _px(112), _py(1) + 10, 12, 6)

    # Coins — scattered along the climbing path
    coin_positions = [
        (_px(10), _py(15)),
        (_px(24), _py(11)),
        (_px(38), _py( 9)),
        (_px(45), _py( 5)),
        (_px(52), _py( 7)),
        (_px(60), _py(11)),
        (_px(65), _py( 5)),
        (_px(74), _py( 3)),
        (_px(80), _py( 3)),
        (_px(86), _py( 9)),
        (_px(92), _py( 5)),
        (_px(99), _py( 7)),
        (_px(104), _py(3)),
        (_px(112), _py(1)),
        (_px(116), _py(1)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Gems — climbing rewards
    _add("Gem", _px(60), _py(11), 8, 8, props={"color": "blue"})
    _add("Gem", _px(80), _py( 3), 8, 8, props={"color": "green"})
    _add("Gem", _px(114), _py( 1), 8, 8, props={"color": "purple"})

    # Heart — mid-climb mercy
    _add("Heart", _px(58), _py(11), 9, 9)

    # Spikes — at the base of spire columns to punish bad landings
    _add("Spike", _px(5),  _py(17), 16, 8)
    _add("Spike", _px(19), _py(17), 16, 8)
    _add("Spike", _px(48), _py(17), 16, 8)

    # Level end — wide horizontal stripe across the summit so the climber
    # can't miss it regardless of which spire they land on.
    _add("LevelEnd", _px(108), 0, 12 * TS, 3 * TS,
         props={"score_bonus": 10000})

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
