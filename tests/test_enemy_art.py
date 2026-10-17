"""Tests for the enlarged enemy sprites and their feet-aligned spawning."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.paths import asset_path
from saruman.world import level_loader as LL


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


STRIPS = {
    "Goblinkin": ("enemy_goblinkin", 4), "Wraith": ("enemy_wraith", 4),
    "BossWarg": ("enemy_bosswarg", 4), "ShieldKnight": ("enemy_shieldknight", 2),
    "SkeletonArcher": ("enemy_archer", 2), "CaveBat": ("enemy_bat", 2),
    "Slime": ("enemy_slime", 2), "SpitterPlant": ("enemy_spitter", 2),
    "MimicChest": ("enemy_mimic", 3), "GoblinKing": ("enemy_goblin_king", 3),
    "NightKing": ("enemy_night_king", 3),
}


@pytest.mark.parametrize("name", list(STRIPS))
def test_strip_matches_art_size(name):
    cls = LL._ENEMY_CLASSES[name]
    asset, frames = STRIPS[name]
    img = pygame.image.load(str(asset_path("sprites", asset + "_strip.png")))
    assert img.get_size() == (cls.ART_W * frames, cls.ART_H)


@pytest.mark.parametrize("name", list(STRIPS))
def test_art_covers_hitbox(name):
    cls = LL._ENEMY_CLASSES[name]
    assert cls.ART_W >= cls.W and cls.ART_H >= cls.H


def test_small_slime_strip_matches():
    from saruman.entities.enemy import SmallSlime
    img = pygame.image.load(str(asset_path("sprites", "enemy_small_slime_strip.png")))
    assert img.get_size() == (SmallSlime.ART_W * 2, SmallSlime.ART_H)


def test_spawn_keeps_feet_on_marker_line():
    level = asset_path("maps", "level_01_greenshire_hills.tmx")
    import pytmx
    tmx = pytmx.TiledMap(str(level))
    markers = [o for layer in tmx.layers if isinstance(layer, pytmx.TiledObjectGroup)
               for o in layer if getattr(o, "type", None) == "Goblinkin"]
    enemies = [e for e in LL._find_enemies(tmx) if type(e).__name__ == "Goblinkin"]
    assert markers and len(markers) == len(enemies)
    for m, e in zip(markers, enemies):
        assert e.y + e.h == pytest.approx(m.y + LL._MARKER_H["Goblinkin"])


def test_enemy_draw_with_hit_flash():
    from saruman.entities.enemy import Goblinkin
    g = Goblinkin(10, 10)
    g.start_hit_flash(6)
    g.draw(pygame.Surface((64, 64), pygame.SRCALPHA), 20, 20)
