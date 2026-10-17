from __future__ import annotations

import warnings
from pathlib import Path

import pytmx

from saruman.entities.enemy import (
    BossWarg, CaveBat, Enemy, GoblinKing, Goblinkin, MimicChest, NightKing,
    ShieldKnight, SkeletonArcher, Slime, SpitterPlant, Wraith,
)
from saruman.entities.interactive import Interactive, MovingPlatform, Spike, Spring
from saruman.entities.item import Coin, Gem, Heart, Item, WeaponUpgrade
from saruman.entities.trigger import LevelEndTrigger, Trigger, WarpTrigger
from saruman.world.tilemap import Tilemap

_DEFAULT_SPAWN = (32.0, 152.0)


def load_level(
    path: Path,
) -> tuple[
    Tilemap, tuple[float, float], list[Enemy], list[Item],
    list[Interactive], list[Trigger],
]:
    """Load a TMX level. Returns (Tilemap, spawn_xy, enemies, items, interactives, triggers)."""
    tilemap       = Tilemap(path)
    tmx           = tilemap.tiled_map
    spawn         = _find_spawn(tmx)
    enemies       = _find_enemies(tmx)
    items         = _find_items(tmx)
    interactives  = _find_interactives(tmx)
    triggers      = _find_triggers(tmx)
    return tilemap, spawn, enemies, items, interactives, triggers


def _find_spawn(tmx: pytmx.TiledMap) -> tuple[float, float]:
    for layer in tmx.layers:
        if not isinstance(layer, pytmx.TiledObjectGroup):
            continue
        for obj in layer:
            if getattr(obj, "type", None) == "PlayerSpawn":
                return float(obj.x), float(obj.y)
    warnings.warn(
        f"No PlayerSpawn object found in {getattr(tmx, 'filename', 'map')}; "
        f"using default spawn {_DEFAULT_SPAWN}.",
        stacklevel=2,
    )
    return _DEFAULT_SPAWN


# Hitbox heights the .tmx enemy markers were placed for. Enemies have since
# grown; keep their feet on the same line by spawning taller ones higher.
_MARKER_H: dict[str, int] = {
    "Goblinkin": 14, "Wraith": 16, "BossWarg": 20, "ShieldKnight": 16,
    "SkeletonArcher": 16, "CaveBat": 8, "Slime": 8, "SpitterPlant": 12,
    "MimicChest": 12, "GoblinKing": 24, "NightKing": 26,
}

_ENEMY_CLASSES: dict[str, type[Enemy]] = {
    "Goblinkin": Goblinkin, "Wraith": Wraith, "BossWarg": BossWarg,
    "ShieldKnight": ShieldKnight, "SkeletonArcher": SkeletonArcher,
    "CaveBat": CaveBat, "Slime": Slime, "SpitterPlant": SpitterPlant,
    "MimicChest": MimicChest, "GoblinKing": GoblinKing, "NightKing": NightKing,
}

# Patrolling flyers take the marker width as their patrol range.
_PATROL_DEFAULT = {"Wraith": 64, "CaveBat": 70}


def _find_enemies(tmx: pytmx.TiledMap) -> list[Enemy]:
    enemies: list[Enemy] = []
    for layer in tmx.layers:
        if not isinstance(layer, pytmx.TiledObjectGroup):
            continue
        for obj in layer:
            otype = getattr(obj, "type", None)
            cls   = _ENEMY_CLASSES.get(otype)
            if cls is None:
                continue
            x = float(obj.x)
            y = float(obj.y) + _MARKER_H[otype] - cls.H      # same feet line
            # Centre the (possibly wider) hitbox on the marker's old one.
            x -= (cls.W - _old_w(otype)) / 2
            if otype in _PATROL_DEFAULT:
                patrol_w = float(getattr(obj, "width", 0) or _PATROL_DEFAULT[otype])
                enemies.append(cls(x, y, patrol_w))
            else:
                enemies.append(cls(x, y))
    return enemies


_MARKER_W: dict[str, int] = {
    "Goblinkin": 12, "Wraith": 12, "BossWarg": 24, "ShieldKnight": 12,
    "SkeletonArcher": 12, "CaveBat": 10, "Slime": 10, "SpitterPlant": 12,
    "MimicChest": 14, "GoblinKing": 28, "NightKing": 30,
}


def _old_w(otype: str) -> int:
    return _MARKER_W[otype]


def _find_items(tmx: pytmx.TiledMap) -> list[Item]:
    items: list[Item] = []
    for layer in tmx.layers:
        if not isinstance(layer, pytmx.TiledObjectGroup):
            continue
        for obj in layer:
            otype = getattr(obj, "type", None)
            x, y  = float(obj.x), float(obj.y)
            if otype == "Coin":
                items.append(Coin(x, y))
            elif otype == "Heart":
                items.append(Heart(x, y))
            elif otype == "WeaponUpgrade":
                items.append(WeaponUpgrade(x, y))
            elif otype == "Gem":
                props = getattr(obj, "properties", {}) or {}
                color = str(props.get("color", "blue"))
                items.append(Gem(x, y, color))
    return items


def _find_interactives(tmx: pytmx.TiledMap) -> list[Interactive]:
    interactives: list[Interactive] = []
    for layer in tmx.layers:
        if not isinstance(layer, pytmx.TiledObjectGroup):
            continue
        for obj in layer:
            otype = getattr(obj, "type", None)
            x, y  = float(obj.x), float(obj.y)
            if otype == "Spring":
                interactives.append(Spring(x, y))
            elif otype == "MovingPlatform":
                props    = getattr(obj, "properties", {}) or {}
                axis     = str(props.get("axis", "x"))
                range_px = float(props.get("range", 64) or 64)
                interactives.append(MovingPlatform(x, y, axis, range_px))
            elif otype == "Spike":
                interactives.append(Spike(x, y))
    return interactives


def _find_triggers(tmx: pytmx.TiledMap) -> list[Trigger]:
    triggers: list[Trigger] = []
    for layer in tmx.layers:
        if not isinstance(layer, pytmx.TiledObjectGroup):
            continue
        for obj in layer:
            otype = getattr(obj, "type", None)
            x = float(obj.x)
            y = float(obj.y)
            w = float(getattr(obj, "width",  16) or 16)
            h = float(getattr(obj, "height", 32) or 32)
            props = getattr(obj, "properties", {}) or {}
            if otype == "Warp":
                target = str(props.get("target", ""))
                if target:
                    triggers.append(WarpTrigger(x, y, w, h, target))
            elif otype == "LevelEnd":
                bonus = int(props.get("score_bonus", 0))
                triggers.append(LevelEndTrigger(x, y, w, h, bonus))
    return triggers
