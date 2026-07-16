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


def _find_enemies(tmx: pytmx.TiledMap) -> list[Enemy]:
    enemies: list[Enemy] = []
    for layer in tmx.layers:
        if not isinstance(layer, pytmx.TiledObjectGroup):
            continue
        for obj in layer:
            otype = getattr(obj, "type", None)
            if otype == "Goblinkin":
                enemies.append(Goblinkin(float(obj.x), float(obj.y)))
            elif otype == "Wraith":
                patrol_w = float(getattr(obj, "width", 64) or 64)
                enemies.append(Wraith(float(obj.x), float(obj.y), patrol_w))
            elif otype == "BossWarg":
                enemies.append(BossWarg(float(obj.x), float(obj.y)))
            elif otype == "ShieldKnight":
                enemies.append(ShieldKnight(float(obj.x), float(obj.y)))
            elif otype == "SkeletonArcher":
                enemies.append(SkeletonArcher(float(obj.x), float(obj.y)))
            elif otype == "CaveBat":
                patrol_w = float(getattr(obj, "width", 70) or 70)
                enemies.append(CaveBat(float(obj.x), float(obj.y), patrol_w))
            elif otype == "Slime":
                enemies.append(Slime(float(obj.x), float(obj.y)))
            elif otype == "SpitterPlant":
                enemies.append(SpitterPlant(float(obj.x), float(obj.y)))
            elif otype == "MimicChest":
                enemies.append(MimicChest(float(obj.x), float(obj.y)))
            elif otype == "GoblinKing":
                enemies.append(GoblinKing(float(obj.x), float(obj.y)))
            elif otype == "NightKing":
                enemies.append(NightKing(float(obj.x), float(obj.y)))
    return enemies


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
