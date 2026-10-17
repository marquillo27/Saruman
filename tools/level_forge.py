"""Build the M20 campaign levels from hand-designed segments.

Each level is a start segment, a run of middle segments, checkpoint rests
every few segments, and an end segment (or a boss arena). Segments are small
hand-made rooms written with a tiny builder API below; all of them share the
same floor line at both edges, so any order stitches together. The level
recipe (which segments, which enemies, how dense) is seeded, so a rebuild
produces the same maps.

Movement budget the segments are designed against (see saruman/config.py):
single jump ~5 tiles high / ~6 tiles far, double jump ~9 tiles high,
hero needs 2 free tiles of headroom (hitbox 12x28).

Usage:
    python tools/level_forge.py            # rebuild every level in assets/maps
    python tools/level_forge.py level_01_greenshire_hills
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT    = Path(__file__).resolve().parent.parent
MAP_DIR = ROOT / "assets" / "maps"
TS      = 16
H       = 26            # level height in tiles
FLOOR   = H - 4         # first ground row; markers stand on the row above it


# ---------------------------------------------------------------------------
# Segment builder
# ---------------------------------------------------------------------------

@dataclass
class Seg:
    w: int
    grid: list[list[int]] = field(default_factory=list)
    fake: list[list[int]] = field(default_factory=list)
    objs: list[tuple] = field(default_factory=list)     # (role, x, y_px, w, h, props)
    tag: str = ""

    def __post_init__(self) -> None:
        self.grid = [[0] * self.w for _ in range(H)]
        self.fake = [[0] * self.w for _ in range(H)]

    # --- terrain (heights are in tiles above the floor surface) ---
    def ground(self, x0: int = 0, x1: int | None = None) -> "Seg":
        for ty in range(FLOOR, H):
            for tx in range(x0, self.w if x1 is None else x1):
                self.grid[ty][tx] = 1
        return self

    def pit(self, x0: int, x1: int) -> "Seg":
        for ty in range(FLOOR, H):
            for tx in range(x0, x1):
                self.grid[ty][tx] = 0
        return self

    def block(self, x0: int, x1: int, h: int) -> "Seg":
        """Solid mass from the floor up to `h` tiles (a step, pillar or wall)."""
        for ty in range(FLOOR - h, FLOOR):
            for tx in range(x0, x1):
                self.grid[ty][tx] = 1
        return self

    def plat(self, x0: int, x1: int, h: int, thick: int = 1) -> "Seg":
        """Floating platform whose top surface is `h` tiles above the floor."""
        for ty in range(FLOOR - h, FLOOR - h + thick):
            for tx in range(x0, x1):
                self.grid[ty][tx] = 1
        return self

    def ceiling(self, x0: int, x1: int, clearance: int, thick: int = 3) -> "Seg":
        """A rock slab `thick` tiles deep whose underside is `clearance` tiles
        above the floor (tunnels, overhangs)."""
        for ty in range(max(0, FLOOR - clearance - thick), FLOOR - clearance):
            for tx in range(x0, x1):
                self.grid[ty][tx] = 1
        return self

    def fake_wall(self, x0: int, x1: int, h0: int, h1: int) -> "Seg":
        """Looks solid, but the player walks through: hides secrets."""
        for ty in range(FLOOR - h1, FLOOR - h0):
            for tx in range(x0, x1):
                self.grid[ty][tx] = 0
                self.fake[ty][tx] = 1
        return self

    # --- objects; `h` = tiles above floor where the object's feet rest ---
    def put(self, role: str, x: int, h: int = 0, w: int = 16, ht: int = 16, **props) -> "Seg":
        y = (FLOOR - h) * TS - ht
        self.objs.append((role, x * TS, y, w, ht, props))
        return self

    def coins(self, x0: int, x1: int, h: int, step: int = 1) -> "Seg":
        for x in range(x0, x1, step):
            self.put("coin", x, h)
        return self


# ---------------------------------------------------------------------------
# Segment library (every builder returns a fresh Seg)
# ---------------------------------------------------------------------------

def s_start() -> Seg:
    s = Seg(22).ground().plat(8, 13, 3)
    s.coins(9, 12, 4)
    return s.put("spawn", 2)


def s_end() -> Seg:
    s = Seg(20).ground().block(14, 20, 1)
    return s.put("exit", 16, 1, w=16, ht=32).coins(5, 10, 1)


def s_rest() -> Seg:
    s = Seg(14).ground()
    return s.put("checkpoint", 6, 0, w=16, ht=32)


def s_rest_heart() -> Seg:
    s = Seg(16).ground().plat(9, 13, 3)
    return s.put("checkpoint", 4, 0, w=16, ht=32).put("heart", 10, 4)


def s_flat_patrol() -> Seg:
    s = Seg(26).ground().block(10, 14, 1)
    s.coins(10, 14, 2)
    return s.put("grunt", 18).put("grunt", 6)


def s_hills() -> Seg:
    s = Seg(30).ground().block(6, 12, 1).block(8, 12, 2).block(16, 22, 2).block(18, 20, 3)
    s.coins(18, 20, 4).coins(8, 12, 3)
    return s.put("grunt", 14).put("blob", 24)


def s_small_gaps() -> Seg:
    s = Seg(28).ground().pit(7, 10).pit(16, 20)
    s.coins(7, 10, 3).coins(16, 20, 4)
    return s.put("grunt", 12).put("flyer", 18, 5)


def s_stepping_stones() -> Seg:
    s = Seg(34).ground().pit(5, 29)
    s.plat(8, 11, 1).plat(14, 17, 3).plat(20, 23, 2).plat(25, 27, 4)
    s.coins(14, 17, 4).coins(25, 27, 5)
    return s.put("flyer", 17, 6)


def s_stairs() -> Seg:
    s = Seg(32).ground()
    s.block(5, 7, 1).block(7, 9, 2).block(9, 11, 3).block(11, 13, 4).block(13, 25, 5)
    s.block(25, 27, 3).block(27, 29, 1)
    s.coins(16, 24, 6)
    return s.put("heavy", 19, 5).put("ranged", 23, 5)


def s_tower() -> Seg:
    s = Seg(26).ground().block(10, 15, 8)
    s.plat(5, 8, 3).plat(7, 10, 6).plat(15, 18, 5).plat(18, 21, 2)
    s.coins(10, 15, 9).put("heart", 12, 9)
    return s.put("turret", 11, 8).put("grunt", 22)


def s_tunnel() -> Seg:
    s = Seg(34).ground().ceiling(4, 30, 4)
    s.put("spike", 12).put("spike", 13).put("spike", 21).put("spike", 22)
    s.coins(5, 11, 1).coins(15, 20, 1).coins(24, 29, 1)
    return s.put("blob", 17).put("blob", 27)


def s_spring_ledge() -> Seg:
    s = Seg(32).ground().block(14, 24, 7).block(24, 27, 4).block(27, 29, 2)
    s.put("spring", 10).put("spike", 6).put("spike", 7)
    s.coins(15, 23, 8)
    return s.put("grunt", 20, 7).put("blob", 30)


def s_drop_down() -> Seg:
    """Counterpart to s_spring_ledge: starts high, ends low, so the floor
    line at both edges stays the same (raised middle)."""
    s = Seg(26).ground().block(0, 4, 0).block(4, 16, 4).block(16, 20, 2)
    s.coins(5, 15, 5)
    return s.put("ranged", 13, 4).put("grunt", 22)


def s_moving_bridge() -> Seg:
    s = Seg(34).ground().pit(6, 28)
    s.put("mover_x", 7, 2, w=32, ht=8, axis="x", range=232)
    s.plat(16, 18, 6).put("heart", 16, 7)
    s.coins(10, 26, 4, step=3)
    return s.put("flyer", 22, 6)


def s_lift_shaft() -> Seg:
    s = Seg(30).ground().block(16, 23, 9).block(23, 26, 5).block(26, 28, 2)
    s.put("mover_y", 11, 1, w=32, ht=8, axis="y", range=128)
    s.coins(17, 23, 10)
    return s.put("heavy", 19, 9)


def s_two_routes() -> Seg:
    s = Seg(40).ground().pit(15, 25)
    s.plat(6, 10, 4).plat(12, 16, 7).plat(19, 23, 9).plat(26, 30, 7).plat(32, 35, 4)
    s.coins(19, 23, 10).put("gem", 21, 10)
    s.plat(15, 25, 2)                              # lower route over the pit
    s.put("spike", 18, 2).put("spike", 19, 2)
    return s.put("grunt", 21, 2).put("flyer", 28, 9).put("blob", 36)


def s_archer_nest() -> Seg:
    s = Seg(30).ground().block(18, 24, 4).block(16, 18, 2).block(24, 26, 2)
    s.plat(8, 12, 3)
    s.coins(8, 12, 4)
    return s.put("ranged", 20, 4).put("ranged", 22, 4).put("heavy", 12)


def s_turret_alley() -> Seg:
    s = Seg(32).ground().block(8, 10, 2).block(20, 22, 2)
    s.plat(13, 17, 4).plat(25, 29, 4)
    s.coins(13, 17, 5).coins(25, 29, 5)
    return s.put("turret", 8, 2).put("turret", 20, 2).put("grunt", 15).put("grunt", 27)


def s_treasure_room() -> Seg:
    s = Seg(28).ground().ceiling(0, 28, 9).block(4, 6, 2).block(22, 24, 2)
    s.coins(8, 20, 1).put("gem", 14, 1)
    return s.put("mimic", 11).put("mimic", 17).put("flyer", 14, 5)


def s_bat_cave() -> Seg:
    s = Seg(32).ground().ceiling(3, 29, 6)
    s.pit(12, 15).pit(21, 24)
    s.coins(12, 15, 2).coins(21, 24, 2)
    return s.put("flyer", 9, 4).put("flyer", 18, 4).put("flyer", 26, 4).put("blob", 17)


def s_long_pit_double() -> Seg:
    """Long pit broken by one small island; a double jump makes it easy."""
    s = Seg(30).ground().pit(8, 22).plat(13, 17, 0, thick=4)
    s.coins(9, 21, 4, step=2)
    return s.put("flyer", 15, 5)


def s_secret_alcove() -> Seg:
    """A fake wall at the foot of a cliff hides an alcove with a relic."""
    s = Seg(28).ground().block(4, 6, 2).block(10, 22, 5)
    s.fake_wall(10, 14, 0, 3)                       # walk into the cliff at floor level
    s.put("relic", 11)
    s.coins(14, 21, 6)
    return s.put("grunt", 18, 5).put("ranged", 24)


def s_secret_high() -> Seg:
    """The top of a pillar gives way into a hidden pocket with a relic."""
    s = Seg(30).ground().plat(5, 9, 3).plat(9, 12, 6).block(14, 24, 10)
    s.block(24, 26, 6).block(26, 28, 3)
    s.fake_wall(17, 21, 7, 10)                      # false floor on the pillar top
    s.put("relic", 18, 7).coins(14, 17, 11).coins(21, 24, 11)
    return s.put("flyer", 10, 9).put("grunt", 29)


def s_boss_arena() -> Seg:
    s = Seg(44).ground().block(42, 44, 3)
    s.plat(8, 13, 4).plat(31, 36, 4).plat(19, 25, 7)
    s.put("heart", 21, 7).put("checkpoint", 3, 0, w=16, ht=32)
    s.put("boss", 30)
    return s.put("exit", 39, 0, w=16, ht=32)

MIDDLE: dict[str, Callable[[], Seg]] = {
    "flat_patrol": s_flat_patrol, "hills": s_hills, "small_gaps": s_small_gaps,
    "stepping_stones": s_stepping_stones, "stairs": s_stairs, "tower": s_tower,
    "tunnel": s_tunnel, "spring_ledge": s_spring_ledge, "drop_down": s_drop_down,
    "moving_bridge": s_moving_bridge, "lift_shaft": s_lift_shaft,
    "two_routes": s_two_routes, "archer_nest": s_archer_nest,
    "turret_alley": s_turret_alley, "treasure_room": s_treasure_room,
    "bat_cave": s_bat_cave, "long_pit_double": s_long_pit_double,
}
SECRETS: dict[str, Callable[[], Seg]] = {"secret_alcove": s_secret_alcove, "secret_high": s_secret_high}


# ---------------------------------------------------------------------------
# Level recipes
# ---------------------------------------------------------------------------

# Enemy roles per world -> TMX enemy types (random pick per marker).
ROLES = {
    "I":   {"grunt": ["Goblinkin"], "flyer": ["Wraith"], "blob": ["Slime"],
            "turret": ["SpitterPlant"], "ranged": ["SkeletonArcher"],
            "heavy": ["ShieldKnight"], "mimic": ["MimicChest"]},
    "II":  {"grunt": ["Goblinkin"], "flyer": ["CaveBat", "Wraith"], "blob": ["Slime"],
            "turret": ["SpitterPlant"], "ranged": ["SkeletonArcher"],
            "heavy": ["ShieldKnight"], "mimic": ["MimicChest"]},
    "III": {"grunt": ["Goblinkin", "ShieldKnight"], "flyer": ["Wraith", "CaveBat"],
            "blob": ["Slime"], "turret": ["SpitterPlant"], "ranged": ["SkeletonArcher"],
            "heavy": ["ShieldKnight"], "mimic": ["MimicChest"]},
}


@dataclass
class Recipe:
    world: str
    middles: list[str]        # segment names in order ("*" = random pick)
    density: float            # chance each enemy marker is kept
    seed: int
    boss: str | None = None   # boss enemy type; level ends in an arena
    secrets: int = 2          # relic segments mixed in
    warp: str | None = None   # hidden warp target placed in a secret
    extras: list[str] = field(default_factory=list)   # e.g. weapon upgrade
    roles: dict[str, list[str]] = field(default_factory=dict)   # per-level role overrides
    exit_bonus: int = 0       # set from campaign order: later levels pay more
    gems_placed: int = 0


RECIPES: dict[str, Recipe] = {
    # --- World I: Greenwood ---
    "level_01_greenshire_hills": Recipe("I", ["flat_patrol", "hills", "small_gaps", "*", "stepping_stones", "*", "tower", "*", "two_routes", "*"], 0.6, 101,
                                        roles={"heavy": ["Goblinkin"], "ranged": ["Goblinkin"]}),   # tutorial: no knights
    "level_02_wolfwood":         Recipe("I", ["hills", "small_gaps", "*", "tunnel", "*", "stairs", "*", "moving_bridge", "*", "*", "two_routes", "*"], 0.75, 102, warp="level_03_glass_caverns", extras=["upgrade"]),
    "level_03_glass_caverns":    Recipe("I", ["treasure_room", "*", "bat_cave", "*", "treasure_room", "*"], 0.7, 103, secrets=2),
    "level_04_sunken_mines":     Recipe("I", ["tunnel", "*", "lift_shaft", "*", "archer_nest", "*", "*", "spring_ledge", "drop_down", "*", "*", "*"], 0.85, 104, boss="BossWarg", extras=["upgrade"]),
    # --- World II: Scorchlands ---
    "level_11_ashfall_wastes":     Recipe("II", ["flat_patrol", "small_gaps", "*", "stepping_stones", "*", "turret_alley", "two_routes", "*", "long_pit_double", "*", "treasure_room", "*"], 0.8, 111),
    "level_12_cinderwood_remains": Recipe("II", ["tower", "*", "spring_ledge", "drop_down", "*", "bat_cave", "*", "*", "lift_shaft", "*", "*", "*", "*"], 0.85, 112, extras=["upgrade"]),
    "level_05_ash_marshes":        Recipe("II", ["stepping_stones", "*", "moving_bridge", "*", "*", "long_pit_double", "*", "turret_alley", "*", "*", "*", "*", "*"], 0.9, 105),
    "level_10_goblin_kings_throne": Recipe("II", ["archer_nest", "*", "treasure_room", "*", "*", "stairs", "*", "*", "*", "*"], 0.9, 110, boss="GoblinKing"),
    # --- World III: Frozen North ---
    "level_06_pale_tower":       Recipe("III", ["tower", "*", "stairs", "*", "*", "lift_shaft", "*", "*", "*", "*", "*", "*"], 0.85, 106),
    "level_09_skybound_spires":  Recipe("III", ["stepping_stones", "moving_bridge", "tower", "lift_shaft", "long_pit_double", "moving_bridge", "*", "spring_ledge", "drop_down", "lift_shaft", "*", "moving_bridge", "*"], 0.9, 109),
    "level_08_forsaken_bridge":  Recipe("III", ["moving_bridge", "*", "long_pit_double", "treasure_room", "*", "stepping_stones", "spring_ledge", "moving_bridge", "*", "two_routes", "*", "*", "*", "*"], 0.95, 108),
    "level_07_cursed_catacombs": Recipe("III", ["tunnel", "*", "bat_cave", "*", "treasure_room", "*", "*", "tunnel", "*", "*", "*", "*", "*", "*"], 1.0, 107),
    "level_13_emberfall_keep":   Recipe("III", ["archer_nest", "*", "stairs", "*", "*", "turret_alley", "*", "*", "*", "*", "*"], 1.0, 113, boss="NightKing"),
}

REST_EVERY = 3     # checkpoint after every N middle segments

for _i, _r in enumerate(RECIPES.values()):      # dict order = campaign order
    _r.exit_bonus = 500 + 250 * _i


def check_edges(seg: Seg, name: str, left: bool = True, right: bool = True) -> None:
    """Segments stitch together only if both edges are plain floor with
    headroom: ground from FLOOR down, three free tiles above it."""
    cols = ([0] if left else []) + ([seg.w - 1] if right else [])
    for tx in cols:
        ground = all(seg.grid[ty][tx] for ty in range(FLOOR, H))
        air    = not any(seg.grid[ty][tx] for ty in range(FLOOR - 3, FLOOR))
        if not (ground and air):
            raise ValueError(f"segment {name}: column {tx} is not a plain floor edge")


def check_library() -> None:
    for name, fn in {**MIDDLE, **SECRETS}.items():
        check_edges(fn(), name)
    check_edges(s_start(), "start", left=False)
    check_edges(s_rest(), "rest")
    check_edges(s_rest_heart(), "rest_heart")
    check_edges(s_end(), "end", right=False)
    check_edges(s_boss_arena(), "boss_arena", right=False)


def build_level(name: str) -> tuple[list[list[int]], list[list[int]], list[dict]]:
    r   = RECIPES[name]
    rng = random.Random(r.seed)

    names: list[str] = []
    pool = [n for n in MIDDLE if n not in r.middles] or list(MIDDLE)
    for n in r.middles:
        names.append(rng.choice(pool) if n == "*" else n)
    # Secrets go in at spread-out positions
    for i in range(r.secrets):
        pos = (i + 1) * len(names) // (r.secrets + 1) + i
        names.insert(pos, rng.choice(list(SECRETS)))

    segs: list[Seg] = [s_start()]
    for i, n in enumerate(names):
        segs.append((MIDDLE.get(n) or SECRETS[n])())
        if (i + 1) % REST_EVERY == 0 and i + 1 < len(names):
            segs.append(s_rest_heart() if (i + 1) % (REST_EVERY * 2) == 0 else s_rest())
    segs.append(s_boss_arena() if r.boss else s_end())

    width = sum(s.w for s in segs)
    grid = [[0] * width for _ in range(H)]
    fake = [[0] * width for _ in range(H)]
    objs: list[dict] = []
    ox   = 0
    warp_done = r.warp is None
    extras = list(r.extras)
    for seg in segs:
        for ty in range(H):
            grid[ty][ox:ox + seg.w] = seg.grid[ty]
            fake[ty][ox:ox + seg.w] = seg.fake[ty]
        for role, x, y, w, h, props in seg.objs:
            x += ox * TS
            obj = _resolve(role, x, y, w, h, props, r, rng)
            if obj is None:
                continue
            if obj["type"] == "Relic" and not warp_done:
                # The first secret alcove hides the warp to the secret level.
                objs.append({"type": "Warp", "x": x, "y": y - 16, "w": 16, "h": 32,
                             "props": {"target": r.warp}})
                warp_done = True
            if obj["type"] == "Heart" and extras:
                extras.pop()
                obj = {"type": "WeaponUpgrade", "x": x, "y": y, "w": 16, "h": 16, "props": {}}
            objs.append(obj)
        ox += seg.w
    for i, o in enumerate(objs, start=1):
        o["id"] = i
    return grid, fake, objs


_SIMPLE = {"coin": "Coin", "heart": "Heart", "spike": "Spike", "spring": "Spring",
           "checkpoint": "Checkpoint", "relic": "Relic", "spawn": "PlayerSpawn"}
_GEM_COLORS = ["blue", "green", "purple", "red"]


def _resolve(role, x, y, w, h, props, r: Recipe, rng: random.Random) -> dict | None:
    if role in _SIMPLE:
        t = _SIMPLE[role]
        if t == "Spike":
            y += 8                                  # spikes are 8 px tall
            h = 8
        return {"type": t, "x": x, "y": y, "w": w, "h": h, "props": {}}
    if role == "gem":
        color = _GEM_COLORS[r.gems_placed % len(_GEM_COLORS)]
        r.gems_placed += 1
        return {"type": "Gem", "x": x, "y": y, "w": 16, "h": 16, "props": {"color": color}}
    if role == "exit":
        return {"type": "LevelEnd", "x": x, "y": y, "w": w, "h": h,
                "props": {"score_bonus": r.exit_bonus}}
    if role in ("mover_x", "mover_y"):
        return {"type": "MovingPlatform", "x": x, "y": y, "w": w, "h": h,
                "props": {"axis": props["axis"], "range": props["range"]}}
    if role == "boss":
        return {"type": r.boss, "x": x, "y": y, "w": 16, "h": 16, "props": {}}
    if rng.random() > r.density:
        return None
    t = rng.choice(r.roles.get(role) or ROLES[r.world][role])
    return {"type": t, "x": x, "y": y, "w": 16, "h": 16, "props": {}}


# ---------------------------------------------------------------------------
# TMX output
# ---------------------------------------------------------------------------

def _csv(grid: list[list[int]]) -> str:
    return "\n".join(",".join(str(v) for v in row) + "," for row in grid)[:-1]


def _obj_xml(o: dict) -> str:
    tag = (f'  <object id="{o["id"]}" type="{o["type"]}" x="{o["x"]}" y="{o["y"]}"'
           f' width="{o["w"]}" height="{o["h"]}"')
    if not o["props"]:
        return tag + "/>"
    lines = [tag + ">", "   <properties>"]
    for k, v in o["props"].items():
        vtype = "int" if isinstance(v, int) else "string"
        lines.append(f'    <property name="{k}" type="{vtype}" value="{v}"/>')
    lines += ["   </properties>", "  </object>"]
    return "\n".join(lines)


def to_tmx(grid, fake, objs) -> str:
    w = len(grid[0])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal"
     renderorder="right-down" width="{w}" height="{H}"
     tilewidth="{TS}" tileheight="{TS}" infinite="0"
     nextlayerid="4" nextobjectid="{len(objs) + 1}">
 <tileset firstgid="1" name="kenney_platformer" tilewidth="{TS}" tileheight="{TS}"
          tilecount="132" columns="12">
  <image source="../tilesets/tilemap_packed.png" width="192" height="176"/>
 </tileset>
 <layer id="1" name="solid" width="{w}" height="{H}">
  <data encoding="csv">
{_csv(grid)}
  </data>
 </layer>
 <layer id="3" name="fake" width="{w}" height="{H}">
  <data encoding="csv">
{_csv(fake)}
  </data>
 </layer>
 <objectgroup id="2" name="entities">
{chr(10).join(_obj_xml(o) for o in objs)}
 </objectgroup>
</map>
"""


def main(argv: list[str]) -> None:
    check_library()
    names = argv or list(RECIPES)
    for name in names:
        grid, fake, objs = build_level(name)
        (MAP_DIR / f"{name}.tmx").write_text(to_tmx(grid, fake, objs), encoding="utf-8")
        counts: dict[str, int] = {}
        for o in objs:
            counts[o["type"]] = counts.get(o["type"], 0) + 1
        print(f"{name}: {len(grid[0])} x {H} tiles, "
              f"{sum(v for k, v in counts.items() if k not in _SIMPLE.values() and k not in ('Gem', 'MovingPlatform', 'Warp', 'WeaponUpgrade', 'LevelEnd'))} enemies, "
              f"{counts.get('Checkpoint', 0)} checkpoints, {counts.get('Relic', 0)} relics")


if __name__ == "__main__":
    main(sys.argv[1:])
