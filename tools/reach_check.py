"""Check that every level can be finished: flood-fill over places the hero can
stand, using the real Player physics to try runs and jumps from each one.

Moving platforms are approximated as static one-tile ledges along their whole
path (so a crossing counts if the platform's track can be stood on), springs
launch with their real velocity. Enemies are ignored. This answers "is the
exit / each relic physically reachable", not "is it fun".

Usage:
    python tools/reach_check.py                    # all levels
    python tools/reach_check.py level_01_greenshire_hills --verbose
"""
from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from saruman.config import TILE_SIZE as T  # noqa: E402
from saruman.core.input import Action, Input  # noqa: E402
from saruman.entities.interactive import MovingPlatform, Spring  # noqa: E402
from saruman.entities.item import Relic  # noqa: E402
from saruman.entities.player import Player  # noqa: E402
from saruman.entities.trigger import LevelEndTrigger  # noqa: E402
from saruman.paths import asset_path  # noqa: E402
from saruman.world.level_loader import load_level  # noqa: E402


class _Map:
    """Level tilemap plus moving-platform tracks as extra solid tiles."""

    def __init__(self, tilemap, platforms) -> None:
        self.t = tilemap
        self.width, self.height = tilemap.width, tilemap.height
        self.pixel_width, self.pixel_height = tilemap.pixel_width, tilemap.pixel_height
        self.extra: set[tuple[int, int]] = set()
        for p in platforms:
            r = p.rect
            if p.axis == "x":
                for x in range(r.left, r.right + int(p.range_px), T):
                    self.extra.add((x // T, r.top // T))
            else:
                for y in range(r.top, r.top + int(p.range_px) + 1, T):
                    for x in range(r.left, r.right, T):
                        self.extra.add((x // T, y // T))

    def is_solid(self, tx: int, ty: int) -> bool:
        if ty >= self.height:
            return False                    # pits are open at the bottom here
        return (tx, ty) in self.extra or self.t.is_solid(tx, ty)


ACTIONS = []
for d in (-1, 1, 0):
    for hold in (3, 8, 40):
        for double_at in (None, 10, 20):
            ACTIONS.append(("jump", d, hold, double_at))
for d in (-1, 1):
    ACTIONS.append(("walk", d, 12, None))


def _simulate(start_x: float, start_y: float, action, m: _Map, springs) -> tuple[float, float] | None:
    kind, d, hold, double_at = action
    p = Player(start_x, start_y)
    p.on_ground = True
    p.vel_x = d * 2.4 if kind == "jump" else 0.0      # assume a running start
    inp = Input()
    left_ground = False
    for f in range(150):
        inp._held = set()
        inp._pressed = set()
        if d < 0:
            inp._held.add(Action.MOVE_LEFT)
        elif d > 0:
            inp._held.add(Action.MOVE_RIGHT)
        if kind == "walk" and f >= hold:
            inp._held.clear()
        if kind == "jump":
            if f == 0 or (double_at is not None and f == double_at):
                inp._pressed.add(Action.JUMP)
            if f < hold or (double_at is not None and double_at <= f < double_at + hold):
                inp._held.add(Action.JUMP)
        p.update(inp, m)
        r = p.rect
        for s in springs:
            if p.vel_y > 0 and r.colliderect(s.rect) and r.bottom <= s.rect.top + 6:
                p.spring_launch(Spring.LAUNCH_VEL_Y)
        if p.y > m.pixel_height:
            return None
        if not p.on_ground:
            left_ground = True
        elif (left_ground or kind == "walk") and f > 2 and abs(p.vel_x) < 0.01 + 3:
            if kind == "walk" and f < hold:
                continue
            return p.x, p.y
    return (p.x, p.y) if p.on_ground else None


def check(stem: str, verbose: bool = False) -> dict:
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1))
    tm, spawn, enemies, items, inter, trig = load_level(asset_path("maps", stem + ".tmx"))
    m = _Map(tm, [i for i in inter if isinstance(i, MovingPlatform)])
    springs = [i for i in inter if isinstance(i, Spring)]
    goal = next(t.rect for t in trig if isinstance(t, LevelEndTrigger))
    relics = [i.rect for i in items if isinstance(i, Relic)]

    start = (spawn[0], spawn[1] + 16 - Player.H)
    seen: set[tuple[int, int]] = set()
    frontier = [start]
    reached_goal = False
    got = [False] * len(relics)
    max_x = 0.0
    t0 = time.time()
    while frontier:
        x, y = frontier.pop()
        key = (int(x) // 8, int(y + Player.H) // T)
        if key in seen:
            continue
        seen.add(key)
        max_x = max(max_x, x)
        body = pygame.Rect(int(x), int(y), Player.W, Player.H)
        if body.inflate(0, 4096).colliderect(goal) and body.bottom > goal.top - 64:
            reached_goal = True
        for i, rr in enumerate(relics):
            if body.inflate(16, 16).colliderect(rr):
                got[i] = True
        for a in ACTIONS:
            res = _simulate(x, y, a, m, springs)
            if res is not None:
                frontier.append(res)
    result = {"level": stem, "exit": reached_goal, "relics": f"{sum(got)}/{len(got)}",
              "max_x_tiles": int(max_x // T), "width": tm.width, "states": len(seen),
              "secs": round(time.time() - t0, 1)}
    if verbose:
        print(result)
    return result


def main(argv: list[str]) -> int:
    stems = argv or sorted(p[:-4] for p in os.listdir(os.path.join(ROOT, "assets", "maps"))
                           if p.endswith(".tmx"))
    bad = 0
    for stem in stems:
        r = check(stem)
        ok = r["exit"] and r["relics"].split("/")[0] == r["relics"].split("/")[1]
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {stem}: exit={r['exit']} relics={r['relics']} "
              f"reached {r['max_x_tiles']}/{r['width']} tiles ({r['states']} spots, {r['secs']}s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith("--")]))
