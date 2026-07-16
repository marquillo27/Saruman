"""
Generate assets/maps/level_10_goblin_kings_throne.tmx
Run from project root:  uv run python tools/generate_level_10.py

Map spec:
  80 × 12 tiles (1280 × 192 px) — wide, horizontal boss arena.
  Entry corridor (tx 0–19): elevated platforms, Goblinkin guards.
  Throne chamber (tx 20–79): open floor, 3 raised platforms for tactical play.
  GoblinKing centred at tx=50.  Spikes at back wall.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_10_goblin_kings_throne.tmx")

W = 80
H = 12
TS = 16


def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]

    # Full solid ground (row 11)
    for x in range(W):
        grid[11][x] = 1

    # Solid ceiling row 0 — ominous throne room
    for x in range(W):
        grid[0][x] = 1

    # Entry corridor walls (left border)
    for y in range(1, 11):
        grid[y][0] = 1

    # Elevated entry platforms (tx 6–11 and tx 14–19)
    for x in range(6, 12):
        grid[8][x] = 1
    for x in range(14, 20):
        grid[6][x] = 1

    # Throne chamber raised platforms for tactical play
    # Platform A: tx 25–32, row 8
    for x in range(25, 33):
        grid[8][x] = 1
    # Platform B: tx 40–47, row 7
    for x in range(40, 48):
        grid[7][x] = 1
    # Platform C: tx 55–62, row 8
    for x in range(55, 63):
        grid[8][x] = 1

    # Throne dais — raised section behind the boss (tx 68–78, rows 9–10)
    for x in range(68, 79):
        for y in range(9, 11):
            grid[y][x] = 3

    # Right border wall
    for y in range(1, 11):
        grid[y][79] = 1

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

    # Player spawns at the left of the entry corridor
    _add("PlayerSpawn", _px(2), _py(10), 16, 16)

    # Entry guards
    _add("Goblinkin",    _px(6),  _py(7),  12, 14)
    _add("Goblinkin",    _px(14), _py(5),  12, 14)

    # Gatekeeper — must be meleed (blocks ranged with shield)
    _add("ShieldKnight", _px(18), _py(10), 12, 16)

    # GoblinKing — centred in throne chamber
    _add("GoblinKing",   _px(50), _py(10), 28, 24)

    # Spikes at the back wall to punish cornering
    _add("Spike", _px(75), _py(11), 16, 8)
    _add("Spike", _px(76), _py(11), 16, 8)
    _add("Spike", _px(77), _py(11), 16, 8)

    # Spring — tactical escape option mid-arena
    _add("Spring", _px(38), _py(10) + 10, 12, 6)

    # Heart — mid-arena mercy pickup
    _add("Heart", _px(30), _py(10), 9, 9)

    # Coins scattered across raised platforms
    coin_positions = [
        (_px(7),  _py(7)),
        (_px(9),  _py(7)),
        (_px(15), _py(5)),
        (_px(17), _py(5)),
        (_px(26), _py(7)),
        (_px(28), _py(7)),
        (_px(41), _py(6)),
        (_px(44), _py(6)),
        (_px(56), _py(7)),
        (_px(59), _py(7)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Red Gem — reward behind boss (near throne dais)
    _add("Gem", _px(65), _py(8), 8, 8, props={"color": "red"})

    # Level end — tall column at back wall, unreachable until boss is cleared
    _add("LevelEnd", _px(72), 0, 6 * TS, H * TS,
         props={"score_bonus": 15000})

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
