"""
Generate assets/maps/level_12_cinderwood_remains.tmx
Run from project root:  uv run python tools/generate_level_12.py

Map spec:
  120 × 18 tiles (1920 × 288 px) — vertical climb through a burnt-out dead forest.
  Charred trunks form stepping columns; the player ascends through smouldering
  remains. Mixed-axis MovingPlatforms and Springs aid the climb. Rewards include
  the blue & green gems.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_12_cinderwood_remains.tmx")

W = 120
H = 18

TS = 16


def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]
    # Bottom solid ground — scorched earth floor
    for x in range(W):
        grid[17][x] = 1
    # Charred trunk columns rising as stepping spires
    trunk_cols = [
        ( 8, 12, 14),
        (22, 26, 11),
        (36, 40,  9),
        (50, 54,  7),
        (64, 68,  5),
        (78, 82,  7),
        (92, 96,  5),
        (104, 110, 3),  # canopy summit
    ]
    for x0, x1, top in trunk_cols:
        for x in range(x0, x1):
            for y in range(top, 17):
                grid[y][x] = 3
    # Burnt branch ledges (platforms)
    ledges = [
        (14, 20, 9),
        (30, 36, 7),
        (44, 50, 11),
        (58, 64, 5),
        (72, 78, 9),
        (86, 92, 7),
        (98, 104, 5),
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

    # Player starts at the bottom-left of the burnt grove
    _add("PlayerSpawn", _px(2), _py(16), 16, 16)

    # Goblinkins scavenging the lower forest floor
    _add("Goblinkin", _px(9),  _py(13), 12, 14)
    _add("Goblinkin", _px(24), _py(10), 12, 14)
    _add("Goblinkin", _px(38), _py( 8), 12, 14)

    # ShieldKnight blocking a mid ledge
    _add("ShieldKnight", _px(46), _py(10), 14, 16)

    # Wraiths drifting between dead trunks (no-stomp threats)
    _add("Wraith", _px(30), _py( 6), 12, 16)
    _add("Wraith", _px(88), _py( 6), 12, 16)

    # SpitterPlants — charred turret stumps
    _add("SpitterPlant", _px(16), _py( 8), 12, 12)
    _add("SpitterPlant", _px(60), _py( 4), 12, 12)
    _add("SpitterPlant", _px(100), _py(4), 12, 12)

    # CaveBats — startled from the canopy
    _add("CaveBat", _px(20), _py( 9), 80, 8)
    _add("CaveBat", _px(40), _py( 7), 96, 8)
    _add("CaveBat", _px(66), _py( 4), 80, 8)
    _add("CaveBat", _px(94), _py( 5), 64, 8)

    # Slimes oozing from rotten logs
    _add("Slime", _px(34), _py(6), 10, 8)
    _add("Slime", _px(76), _py(8), 10, 8)

    # MimicChest — a "treasure" stump
    _add("MimicChest", _px(62), _py(5) - 12, 14, 12)

    # MovingPlatforms — chained climb across the burnt gaps
    _add("MovingPlatform", _px(16) + 4, _py(14), 32, 8,
         props={"axis": "x", "range": 56})
    _add("MovingPlatform", _px(30) + 4, _py(12), 32, 8,
         props={"axis": "y", "range": 48})
    _add("MovingPlatform", _px(54) + 4, _py( 9), 32, 8,
         props={"axis": "x", "range": 56})
    _add("MovingPlatform", _px(80) + 4, _py( 7), 32, 8,
         props={"axis": "y", "range": 48})

    # Springs — vertical boosts up the trunks
    _add("Spring", _px(11), _py(13) + 10, 12, 6)
    _add("Spring", _px(53), _py( 6) + 10, 12, 6)
    _add("Spring", _px(95), _py( 4) + 10, 12, 6)

    # Coins — scattered up the climb
    coin_positions = [
        (_px(12), _py(15)),
        (_px(26), _py(10)),
        (_px(40), _py( 8)),
        (_px(48), _py( 4)),
        (_px(60), _py( 4)),
        (_px(66), _py( 8)),
        (_px(74), _py( 4)),
        (_px(88), _py( 6)),
        (_px(100), _py(4)),
        (_px(106), _py(2)),
        (_px(108), _py(2)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Gems — climbing rewards (blue & green reused)
    _add("Gem", _px(58), _py(4), 8, 8, props={"color": "blue"})
    _add("Gem", _px(100), _py(4), 8, 8, props={"color": "green"})

    # Heart — mid-climb mercy
    _add("Heart", _px(44), _py(10), 9, 9)

    # WeaponUpgrade — reward for braving the climb
    _add("WeaponUpgrade", _px(72), _py(8), 10, 12)

    # Spikes — punishing bad landings at trunk bases
    _add("Spike", _px(7),  _py(17), 16, 8)
    _add("Spike", _px(35), _py(17), 16, 8)
    _add("Spike", _px(63), _py(17), 16, 8)

    # Level end — wide stripe across the canopy summit
    _add("LevelEnd", _px(102), 0, 14 * TS, 3 * TS,
         props={"score_bonus": 11000})

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
