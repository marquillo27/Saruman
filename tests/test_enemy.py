"""Tests for enemy on_stomped/on_shot return values and BossWarg HP."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.entities.enemy import (
    BossWarg, GoblinKing, Goblinkin, MimicChest, ShieldKnight, Slime, SmallSlime,
    SpitterPlant, Wraith,
)
from saruman.entities.projectile import AcidBlob


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    yield
    pygame.quit()


# ---------------------------------------------------------------------------
# Goblinkin
# ---------------------------------------------------------------------------

def test_goblinkin_on_stomped_kills_immediately():
    g = Goblinkin(0, 0)
    result = g.on_stomped()
    assert result is True
    assert not g.alive


def test_goblinkin_on_shot_kills_immediately():
    g = Goblinkin(0, 0)
    result = g.on_shot()
    assert result is True
    assert not g.alive


def test_goblinkin_can_be_stomped():
    assert Goblinkin.can_be_stomped is True


# ---------------------------------------------------------------------------
# Wraith
# ---------------------------------------------------------------------------

def test_wraith_cannot_be_stomped():
    assert Wraith.can_be_stomped is False


def test_wraith_on_shot_kills_immediately():
    w = Wraith(0, 0)
    result = w.on_shot()
    assert result is True
    assert not w.alive


def test_wraith_on_stomped_kills_immediately():
    w = Wraith(0, 0)
    result = w.on_stomped()
    assert result is True
    assert not w.alive


# ---------------------------------------------------------------------------
# BossWarg — multi-hit HP system
# ---------------------------------------------------------------------------

def test_boss_starts_with_full_hp():
    b = BossWarg(0, 0)
    assert b._hp == BossWarg._MAX_HP


def test_boss_max_hp_is_three():
    assert BossWarg._MAX_HP == 3


def test_boss_first_stomp_does_not_kill():
    b = BossWarg(0, 0)
    killed = b.on_stomped()
    assert killed is False
    assert b.alive
    assert b._hp == 2


def test_boss_second_stomp_does_not_kill():
    b = BossWarg(0, 0)
    b.on_stomped()
    killed = b.on_stomped()
    assert killed is False
    assert b.alive
    assert b._hp == 1


def test_boss_third_stomp_kills():
    b = BossWarg(0, 0)
    b.on_stomped()
    b.on_stomped()
    killed = b.on_stomped()
    assert killed is True
    assert not b.alive
    assert b._hp == 0


def test_boss_on_shot_reduces_hp():
    b = BossWarg(0, 0)
    killed = b.on_shot()
    assert killed is False
    assert b._hp == 2


def test_boss_three_shots_kills():
    b = BossWarg(0, 0)
    b.on_shot()
    b.on_shot()
    killed = b.on_shot()
    assert killed is True
    assert not b.alive


def test_boss_mixed_stomp_and_shot():
    b = BossWarg(0, 0)
    b.on_stomped()
    b.on_shot()
    killed = b.on_stomped()
    assert killed is True
    assert not b.alive


def test_boss_can_be_stomped():
    assert BossWarg.can_be_stomped is True


def test_boss_score_value():
    assert BossWarg.score_value == 500


# ---------------------------------------------------------------------------
# ShieldKnight — projectile-immune, stompable
# ---------------------------------------------------------------------------

def test_shieldknight_on_stomped_kills_immediately():
    sk = ShieldKnight(0, 0)
    result = sk.on_stomped()
    assert result is True
    assert not sk.alive


def test_shieldknight_on_shot_does_not_kill():
    sk = ShieldKnight(0, 0)
    result = sk.on_shot()
    assert result is False


def test_shieldknight_survives_projectile_hit():
    sk = ShieldKnight(0, 0)
    sk.on_shot()
    assert sk.alive


def test_shieldknight_can_be_stomped():
    assert ShieldKnight.can_be_stomped is True


def test_shieldknight_score_value():
    assert ShieldKnight.score_value == 150


def test_shieldknight_on_shot_multiple_times_still_alive():
    sk = ShieldKnight(0, 0)
    for _ in range(5):
        sk.on_shot()
    assert sk.alive


# ---------------------------------------------------------------------------
# M11 — hit flash timer defaults and BossWarg recoil defaults
# ---------------------------------------------------------------------------

def test_enemy_class_hit_timer_default():
    from saruman.entities.enemy import Enemy
    assert Enemy._hit_timer == 0


def test_goblinkin_instance_hit_timer_zero():
    assert Goblinkin(0, 0)._hit_timer == 0


def test_wraith_instance_hit_timer_zero():
    assert Wraith(0, 0)._hit_timer == 0


def test_bosswarg_instance_hit_timer_zero():
    assert BossWarg(0, 0)._hit_timer == 0


def test_shieldknight_instance_hit_timer_zero():
    assert ShieldKnight(0, 0)._hit_timer == 0


def test_bosswarg_knockback_frames_default_zero():
    assert BossWarg(0, 0)._knockback_frames == 0


def test_draw_hit_flash_no_op_when_timer_zero():
    """_draw_hit_flash() with _hit_timer=0 must not alter the surface."""
    surf = pygame.Surface((32, 32))
    surf.fill((200, 0, 0))
    g = Goblinkin(0, 0)
    g._draw_hit_flash(surf, 0, 0)
    assert surf.get_at((0, 0)) == (200, 0, 0, 255)


# ---------------------------------------------------------------------------
# M18 — Slime / SmallSlime
# ---------------------------------------------------------------------------

def test_slime_on_stomped_kills():
    s = Slime(0, 0)
    assert s.on_stomped() is True
    assert not s.alive


def test_slime_spawns_two_small_slimes_on_kill():
    s = Slime(100, 80)
    spawns = s.on_kill_spawn()
    assert len(spawns) == 2
    assert all(isinstance(x, SmallSlime) for x in spawns)


def test_small_slime_does_not_spawn_more():
    """SmallSlime is the leaf — killing it spawns nothing."""
    ss = SmallSlime(0, 0)
    assert ss.on_kill_spawn() == []


def test_slime_can_be_stomped():
    assert Slime.can_be_stomped is True


def test_small_slime_score_value():
    assert SmallSlime.score_value == 30


def test_slime_split_children_face_opposite_directions():
    s = Slime(0, 0)
    a, b = s.on_kill_spawn()
    assert a.facing != b.facing


# ---------------------------------------------------------------------------
# M18 — SpitterPlant
# ---------------------------------------------------------------------------

class _NoOpMap:
    @property
    def width(self):  return 100
    @property
    def height(self): return 100

    def is_solid(self, tx, ty): return False


def test_spitter_fires_when_player_in_range():
    sp = SpitterPlant(50, 80)
    # Player is within _DETECT_RANGE
    pr = pygame.Rect(sp.rect.centerx + 50, sp.rect.centery, 10, 16)
    sp.update(_NoOpMap(), 1 / 60, pr)
    shot = sp.take_shot()
    assert isinstance(shot, AcidBlob)


def test_spitter_does_not_fire_out_of_range():
    sp = SpitterPlant(50, 80)
    pr = pygame.Rect(sp.rect.centerx + 500, sp.rect.centery, 10, 16)
    sp.update(_NoOpMap(), 1 / 60, pr)
    assert sp.take_shot() is None


def test_spitter_take_shot_is_consumed():
    """Second consecutive take_shot() returns None even after firing."""
    sp = SpitterPlant(50, 80)
    pr = pygame.Rect(sp.rect.centerx + 30, sp.rect.centery, 10, 16)
    sp.update(_NoOpMap(), 1 / 60, pr)
    sp.take_shot()
    assert sp.take_shot() is None


def test_spitter_can_be_stomped():
    assert SpitterPlant.can_be_stomped is True


# ---------------------------------------------------------------------------
# M18 — AcidBlob
# ---------------------------------------------------------------------------

def test_acid_blob_falls_under_gravity():
    blob = AcidBlob(0.0, 0.0, 1)
    initial_vy = blob.vel_y
    blob.update(_NoOpMap())
    # vel_y must increase (fall faster) after one frame
    assert blob.vel_y > initial_vy


def test_acid_blob_dies_on_solid_tile():
    class _SolidAt:
        @property
        def width(self):  return 100
        @property
        def height(self): return 100

        def is_solid(self, tx, ty): return True

    blob = AcidBlob(0.0, 0.0, 1)
    blob.update(_SolidAt())
    assert not blob.alive


def test_acid_blob_expires_after_lifetime():
    blob = AcidBlob(0.0, 0.0, 1)
    for _ in range(AcidBlob.LIFETIME + 1):
        blob.update(_NoOpMap())
        if not blob.alive:
            break
    assert not blob.alive


# ---------------------------------------------------------------------------
# M18 — MimicChest
# ---------------------------------------------------------------------------

def test_mimic_starts_asleep():
    m = MimicChest(0, 0)
    assert not m._awake


def test_mimic_first_stomp_wakes_but_does_not_kill():
    m = MimicChest(0, 0)
    killed = m.on_stomped()
    assert m._awake
    assert killed is False
    assert m.alive


def test_mimic_dies_after_three_awake_hits():
    m = MimicChest(0, 0)
    m.on_stomped()  # wake
    assert m.on_stomped() is False
    assert m.on_stomped() is False
    killed = m.on_stomped()
    assert killed is True
    assert not m.alive


def test_mimic_stays_asleep_when_player_far():
    m = MimicChest(0, 0)
    pr = pygame.Rect(1000, 1000, 10, 16)
    m.update(_NoOpMap(), 1 / 60, pr)
    assert not m._awake


def test_mimic_wakes_when_player_close():
    m = MimicChest(50, 50)
    pr = pygame.Rect(60, 50, 10, 16)   # within 50 px
    m.update(_NoOpMap(), 1 / 60, pr)
    assert m._awake


def test_mimic_score_value():
    assert MimicChest.score_value == 400


# ---------------------------------------------------------------------------
# on_melee() hook
# ---------------------------------------------------------------------------

def test_on_melee_kills_goblinkin():
    g = Goblinkin(0, 0)
    killed = g.on_melee()
    assert killed is True
    assert not g.alive


def test_on_melee_kills_wraith():
    w = Wraith(0, 0)
    killed = w.on_melee()
    assert killed is True
    assert not w.alive


def test_shieldknight_survives_projectile_but_dies_to_melee():
    k = ShieldKnight(0, 0)
    # Projectile is blocked
    assert k.on_shot() is False
    assert k.alive
    # Melee bypasses shield
    assert k.on_melee() is True
    assert not k.alive


def test_on_melee_default_delegates_to_on_shot():
    """Base implementation of on_melee() calls on_shot() (same result)."""
    g = Goblinkin(0, 0)
    # Both should kill immediately; verify return value matches on_shot behaviour
    g2 = Goblinkin(0, 0)
    assert g.on_melee() == g2.on_shot()


# ---------------------------------------------------------------------------
# on_kill_drop() hook
# ---------------------------------------------------------------------------

def test_on_kill_drop_base_returns_empty():
    g = Goblinkin(0, 0)
    assert g.on_kill_drop() == []


def test_slime_on_kill_drop_returns_empty():
    s = Slime(0, 0)
    assert s.on_kill_drop() == []


def test_mimic_chest_drops_gem_on_kill():
    from saruman.entities.item import Gem
    m = MimicChest(20, 30)
    drops = m.on_kill_drop()
    assert len(drops) == 1
    assert isinstance(drops[0], Gem)


def test_mimic_chest_drop_is_purple_gem():
    from saruman.entities.item import Gem
    m = MimicChest(20, 30)
    drop = m.on_kill_drop()[0]
    assert isinstance(drop, Gem)
    assert drop.color == "purple"


def test_mimic_chest_drop_near_mimic_position():
    from saruman.entities.item import Gem
    m = MimicChest(50, 80)
    drop = m.on_kill_drop()[0]
    # Drop should be near the mimic's position
    assert abs(drop.x - m.x) < 20
    assert abs(drop.y - m.y) < 20


# ---------------------------------------------------------------------------
# GoblinKing — multi-phase final boss
# ---------------------------------------------------------------------------

def test_goblinKing_starts_at_max_hp():
    gk = GoblinKing(0, 0)
    assert gk._hp == GoblinKing._MAX_HP


def test_goblinKing_max_hp_is_five():
    assert GoblinKing._MAX_HP == 5


def test_goblinKing_phase_1_at_full_hp():
    gk = GoblinKing(0, 0)
    assert gk.phase == 1


def test_goblinKing_phase_2_at_or_below_2hp():
    gk = GoblinKing(0, 0)
    gk._hp = 2
    assert gk.phase == 2


def test_goblinKing_phase_2_at_1hp():
    gk = GoblinKing(0, 0)
    gk._hp = 1
    assert gk.phase == 2


def test_goblinKing_on_stomped_reduces_hp():
    gk = GoblinKing(0, 0)
    result = gk.on_stomped()
    assert result is False
    assert gk._hp == 4
    assert gk.alive


def test_goblinKing_on_shot_reduces_hp():
    gk = GoblinKing(0, 0)
    result = gk.on_shot()
    assert result is False
    assert gk._hp == 4


def test_goblinKing_5_hits_kills():
    gk = GoblinKing(0, 0)
    for _ in range(4):
        gk.on_shot()
    killed = gk.on_shot()
    assert killed is True
    assert not gk.alive
    assert gk._hp == 0


def test_goblinKing_drops_red_gem_on_kill():
    from saruman.entities.item import Gem
    gk = GoblinKing(100, 80)
    drops = gk.on_kill_drop()
    assert len(drops) == 1
    assert isinstance(drops[0], Gem)
    assert drops[0].color == "red"


def test_goblinKing_score_value():
    assert GoblinKing.score_value == 1500


def test_goblinKing_can_be_stomped():
    assert GoblinKing.can_be_stomped is True


# ---------------------------------------------------------------------------
# take_spawn() hook
# ---------------------------------------------------------------------------

def test_take_spawn_base_returns_empty_for_goblinkin():
    g = Goblinkin(0, 0)
    assert g.take_spawn() == []


def test_take_spawn_base_returns_empty_for_wraith():
    w = Wraith(0, 0)
    assert w.take_spawn() == []


def test_goblinKing_take_spawn_empty_initially():
    gk = GoblinKing(0, 0)
    assert gk.take_spawn() == []


def test_goblinKing_fires_shot_in_phase2():
    """GoblinKing queues an EnemyProjectile when in phase 2 and shot timer hits 0."""
    from saruman.entities.projectile import EnemyProjectile
    gk = GoblinKing(100, 80)
    gk._hp = 1       # force phase 2
    gk._shot_timer = 0
    pr = pygame.Rect(200, 80, 10, 16)   # player to the right
    gk.update(_NoOpMap(), 1 / 60, pr)
    shot = gk.take_shot()
    assert isinstance(shot, EnemyProjectile)


def test_goblinKing_no_shot_in_phase1():
    """GoblinKing must NOT fire projectiles while in phase 1."""
    gk = GoblinKing(100, 80)
    gk._hp = 5       # phase 1
    gk._shot_timer = 0
    pr = pygame.Rect(200, 80, 10, 16)
    gk.update(_NoOpMap(), 1 / 60, pr)
    shot = gk.take_shot()
    assert shot is None


def test_goblinKing_spawns_goblinkin_in_phase1():
    """GoblinKing queues a Goblinkin minion when in phase 1 and spawn timer hits 0."""
    gk = GoblinKing(100, 80)
    gk._hp = 5       # phase 1
    gk._spawn_timer = 0
    pr = pygame.Rect(200, 80, 10, 16)
    gk.update(_NoOpMap(), 1 / 60, pr)
    spawns = gk.take_spawn()
    assert len(spawns) == 1
    assert isinstance(spawns[0], Goblinkin)
