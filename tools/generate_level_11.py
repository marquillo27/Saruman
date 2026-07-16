"""
Generate assets/maps/level_11_ashfall_wastes.tmx
Run from project root:  uv run python tools/generate_level_11.py

Map spec:
  150 × 12 tiles (2400 × 192 px)
  Act 3 opener. Open wind-scoured ash plain — long horizontal traversal with
  shallow drifts and exposed ridges. Wind hazards: SpitterPlants and CaveBats
  harry the player across open ground. Rewards include the previously-unused
  blue & green gems.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_11_ashfall_wastes.tmx")

W = 150
H = 12

TS = 16


def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]
    # Full ground row 11
    for x in range(W):
        grid[11][x] = 1
    # Shallow ash sinkholes
    pits = [(26, 30), (44, 48), (66, 71), (88, 92), (110, 115), (132, 136)]
    for px0, px1 in pits:
        for x in range(px0, px1):
            grid[11][x] = 0
    # Low ash ridges (row 10 humps) — uneven footing
    ridges = [(10, 18), (52, 60), (96, 104), (120, 128)]
    for rx0, rx1 in ridges:
        for x in range(rx0, rx1):
            grid[10][x] = 1
    # Floating ash-stone platforms
    platforms = [
        (8,   14, 8),
        (28,  34, 7),
        (46,  52, 8),
        (68,  74, 7),
        (90,  96, 8),
        (112, 118, 7),
        (134, 140, 8),
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

    # Early goblin patrols on open ground
    _add("Goblinkin", _px(5),  _py(10), 12, 14)
    _add("Goblinkin", _px(38), _py(10), 12, 14)
    _add("Goblinkin", _px(78), _py(10), 12, 14)

    # SpitterPlants — wind turrets dotting the plain
    _add("SpitterPlant", _px(20),  _py(10), 12, 12)
    _add("SpitterPlant", _px(56),  _py(9),  12, 12)
    _add("SpitterPlant", _px(100), _py(9),  12, 12)
    _add("SpitterPlant", _px(126), _py(10), 12, 12)

    # CaveBats — gusting across the open sky
    _add("CaveBat", _px(28),  _py(4), 80, 8)
    _add("CaveBat", _px(64),  _py(3), 80, 8)
    _add("CaveBat", _px(108), _py(4), 80, 8)
    _add("CaveBat", _px(132), _py(5), 64, 8)

    # SkeletonArchers on ridges
    _add("SkeletonArcher", _px(54),  _py(9),  12, 16)
    _add("SkeletonArcher", _px(98),  _py(9),  12, 16)

    # Slimes in the sinkholes
    _add("Slime", _px(46),  _py(10), 10, 8)
    _add("Slime", _px(112), _py(10), 10, 8)

    # MimicChest — lurking on a platform
    _add("MimicChest", _px(70), _py(7) - 12, 14, 12)

    # MovingPlatforms over the wider sinkholes
    _add("MovingPlatform", _px(66) + 4, _py(8), 32, 8,
         props={"axis": "x", "range": 56})
    _add("MovingPlatform", _px(110) + 4, _py(8), 32, 8,
         props={"axis": "y", "range": 40})

    # Springs — boosts up to high platforms
    _add("Spring", _px(40), _py(10) + 10, 12, 6)
    _add("Spring", _px(122), _py(10) + 10, 12, 6)

    # Coins
    coin_positions = [
        (_px(9),   _py(7)),
        (_px(30),  _py(6)),
        (_px(48),  _py(7)),
        (_px(70),  _py(6)),
        (_px(92),  _py(7)),
        (_px(114), _py(6)),
        (_px(136), _py(7)),
        (_px(147), _py(10)),
        (_px(148), _py(10)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Gems — finally use the unused blue & green sprites as Act 3 rewards
    _add("Gem", _px(30), _py(6), 8, 8, props={"color": "blue"})
    _add("Gem", _px(92), _py(7), 8, 8, props={"color": "green"})

    # Heart
    _add("Heart", _px(114), _py(6), 9, 9)

    # Spikes — drift-edge hazards
    _add("Spike", _px(30), _py(11), 16, 8)
    _add("Spike", _px(71), _py(11), 16, 8)
    _add("Spike", _px(115), _py(11), 16, 8)

    # Level end — full-height column
    _add("LevelEnd", _px(148), 0, 16, H * TS,
         props={"score_bonus": 9000})

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
