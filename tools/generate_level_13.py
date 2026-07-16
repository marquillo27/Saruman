"""
Generate assets/maps/level_13_emberfall_keep.tmx
Run from project root:  uv run python tools/generate_level_13.py

Map spec:
  96 × 12 tiles (1536 × 192 px) — the Act 3 finale: a ruined, burning keep.
  Entry breach (tx 0–17): rubble platforms, Goblinkin + ShieldKnight gatekeepers.
  Collapsed great hall (tx 18–95): open arena with three raised ramparts where
  TWO BossWargs make their last stand (a rematch of the Sunken Mines / Pale Tower
  encounter, harder configuration). Spike-lined back wall. No new boss class —
  the finale recombines existing threats. Absent from _NEXT_LEVEL → win screen.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from tmx_builder import build_tmx

OUT = os.path.join(ROOT, "assets", "maps", "level_13_emberfall_keep.tmx")

W = 96
H = 12
TS = 16


def _build_grid() -> list[list[int]]:
    grid = [[0] * W for _ in range(H)]

    # Full solid ground (row 11)
    for x in range(W):
        grid[11][x] = 1

    # Solid ceiling row 0 — collapsed great hall
    for x in range(W):
        grid[0][x] = 1

    # Left border wall (breach entry)
    for y in range(1, 11):
        grid[y][0] = 1

    # Entry breach rubble platforms (tx 5–10 and tx 13–17)
    for x in range(5, 11):
        grid[8][x] = 1
    for x in range(13, 18):
        grid[6][x] = 1

    # Great-hall ramparts for tactical boss play
    # Rampart A: tx 26–34, row 8
    for x in range(26, 35):
        grid[8][x] = 1
    # Rampart B: tx 45–54, row 7  (central high ground)
    for x in range(45, 55):
        grid[7][x] = 1
    # Rampart C: tx 64–72, row 8
    for x in range(64, 73):
        grid[8][x] = 1

    # Crumbled dais behind the bosses (tx 80–94, rows 9–10)
    for x in range(80, 95):
        for y in range(9, 11):
            grid[y][x] = 3

    # Right border wall
    for y in range(1, 11):
        grid[y][95] = 1

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

    # Player breaches from the left
    _add("PlayerSpawn", _px(2), _py(10), 16, 16)

    # Breach guards
    _add("Goblinkin",    _px(5),  _py(7),  12, 14)
    _add("Goblinkin",    _px(14), _py(5),  12, 14)
    _add("SkeletonArcher", _px(9), _py(10), 12, 16)

    # Gatekeeper — shielded, blocks the hall entrance
    _add("ShieldKnight", _px(20), _py(10), 12, 16)

    # The two BossWargs — finale rematch, flanking the hall
    _add("BossWarg", _px(40), _py(9), 24, 20)
    _add("BossWarg", _px(70), _py(9), 24, 20)

    # Supporting threats during the boss fight
    _add("ShieldKnight", _px(58), _py(10), 12, 16)
    _add("SpitterPlant", _px(30), _py( 7), 12, 12)
    _add("SpitterPlant", _px(68), _py( 7), 12, 12)
    _add("Wraith", _px(50), _py(6), 12, 16)

    # Spikes lining the back wall to punish cornering
    _add("Spike", _px(90), _py(11), 16, 8)
    _add("Spike", _px(91), _py(11), 16, 8)
    _add("Spike", _px(92), _py(11), 16, 8)
    # Mid-arena hazard between the bosses
    _add("Spike", _px(54), _py(11), 16, 8)

    # Springs — tactical repositioning under boss pressure
    _add("Spring", _px(36), _py(10) + 10, 12, 6)
    _add("Spring", _px(76), _py(10) + 10, 12, 6)

    # Hearts — two mercy pickups for the gauntlet
    _add("Heart", _px(24), _py(10), 9, 9)
    _add("Heart", _px(62), _py(10), 9, 9)

    # Coins across the ramparts
    coin_positions = [
        (_px(6),  _py(7)),
        (_px(8),  _py(7)),
        (_px(15), _py(5)),
        (_px(28), _py(7)),
        (_px(32), _py(7)),
        (_px(48), _py(6)),
        (_px(51), _py(6)),
        (_px(66), _py(7)),
        (_px(70), _py(7)),
        (_px(85), _py(8)),
    ]
    for cx, cy in coin_positions:
        _add("Coin", cx, cy, 8, 8)

    # Gems — final rewards (blue & green reused; high-value purple on the dais)
    _add("Gem", _px(48), _py(6), 8, 8, props={"color": "blue"})
    _add("Gem", _px(66), _py(7), 8, 8, props={"color": "green"})
    _add("Gem", _px(86), _py(8), 8, 8, props={"color": "purple"})

    # WeaponUpgrade — last-ditch firepower before the bosses
    _add("WeaponUpgrade", _px(22), _py(10), 10, 12)

    # Level end — tall column at the back, reachable once the keep is cleared.
    # level_13 is absent from _NEXT_LEVEL → crossing it triggers the win screen.
    _add("LevelEnd", _px(88), 0, 6 * TS, H * TS,
         props={"score_bonus": 20000})

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
