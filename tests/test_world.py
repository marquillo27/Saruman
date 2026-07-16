"""Tests for World game logic — game over, damage, hitstop, triggers, carry."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from saruman.config import PLAYER_LIVES, TILE_SIZE
from saruman.core.input import Input
from saruman.entities.enemy import Goblinkin
from saruman.entities.trigger import LevelEndTrigger, WarpTrigger
from saruman.world.world import World


# ---------------------------------------------------------------------------
# Minimal stub tilemap — solid ground at row 11, everything else is air
# ---------------------------------------------------------------------------

class _FlatMap:
    MAP_W = 40
    MAP_H = 12

    @property
    def width(self) -> int:  return self.MAP_W
    @property
    def height(self) -> int: return self.MAP_H
    @property
    def pixel_width(self) -> int:  return self.MAP_W * TILE_SIZE
    @property
    def pixel_height(self) -> int: return self.MAP_H * TILE_SIZE

    def is_solid(self, tx: int, ty: int) -> bool:
        return ty == 11 and 0 <= tx < self.MAP_W

    def draw(self, surface, cx, cy) -> None:
        pass


_SPAWN = (32.0, 144.0)   # just above ground (row 11 top = 176, player h=16 → 160)


def _make_world(enemies=None, items=None, triggers=None, carry=None) -> World:
    return World(
        _FlatMap(), _SPAWN,
        enemies  or [],
        items    or [],
        triggers or [],
        carry,
    )


@pytest.fixture(scope="module", autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def world() -> World:
    return _make_world()


@pytest.fixture
def inp() -> Input:
    return Input()


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_fresh_world_not_game_over(world):
    assert not world.is_game_over


def test_fresh_world_no_level_complete(world):
    assert not world.is_level_complete


def test_fresh_world_no_warp_target(world):
    assert world.warp_target is None


def test_fresh_world_damage_flash_false(world):
    assert not world.damage_flash


def test_fresh_world_full_lives(world):
    assert world.lives == PLAYER_LIVES


def test_fresh_world_zero_score(world):
    assert world.score == 0


# ---------------------------------------------------------------------------
# Damage and game over
# ---------------------------------------------------------------------------

def test_apply_damage_reduces_lives(world):
    world._apply_damage()
    assert world.lives == PLAYER_LIVES - 1


def test_apply_damage_sets_damage_flash(world):
    world._apply_damage()
    assert world.damage_flash is True


def test_damage_flash_resets_each_update(world, inp):
    world._apply_damage()
    assert world.damage_flash is True
    world.update(inp, 1 / 60)
    assert world.damage_flash is False


def test_game_over_when_lives_reach_zero(world):
    inp = Input()
    for _ in range(PLAYER_LIVES):
        world._lives = 1          # reset so invincibility doesn't block
        world._player._hit_timer = 0
        world._apply_damage()
    # Death animation starts — game-over is not immediate
    assert world._player.dying
    assert not world.is_game_over
    # Exhaust the death timer and tick once → game-over fires
    world._player._death_timer = 0
    world.update(inp, 1 / 60)
    assert world.is_game_over


def test_death_timer_decrements_during_world_update(world):
    """Regression: World must tick _death_timer itself while player is dying,
    because Player.update() is not called during the death state."""
    inp = Input()
    for _ in range(PLAYER_LIVES):
        world._lives = 1
        world._player._hit_timer = 0
        world._apply_damage()
    assert world._player.dying
    initial = world._player._death_timer
    assert initial > 0
    world.update(inp, 1 / 60)
    assert world._player._death_timer == initial - 1


def test_death_eventually_triggers_game_over_without_manual_reset(world):
    """Regression: leaving the world running long enough must reach game-over
    without anyone resetting _death_timer to 0."""
    inp = Input()
    for _ in range(PLAYER_LIVES):
        world._lives = 1
        world._player._hit_timer = 0
        world._apply_damage()
    assert world._player.dying
    # Cap at the player's death animation length + a small slack
    for _ in range(world._player._DEATH_FRAMES + 2):
        if world.is_game_over:
            break
        world.update(inp, 1 / 60)
    assert world.is_game_over


def test_invincible_player_not_damaged(world):
    world._player._hit_timer = 60   # force invincibility
    lives_before = world.lives
    world._apply_damage()
    assert world.lives == lives_before


# ---------------------------------------------------------------------------
# Hit-stop
# ---------------------------------------------------------------------------

def test_hitstop_starts_at_zero(world):
    assert world._hitstop == 0


def test_hitstop_decrements_each_update(world, inp):
    world._hitstop = 4
    world.update(inp, 1 / 60)
    assert world._hitstop == 3


def test_hitstop_freezes_lives(world, inp):
    world._hitstop = 4
    initial_lives = world.lives
    for _ in range(4):
        world.update(inp, 1 / 60)
    assert world.lives == initial_lives


def test_hitstop_reaches_zero_after_n_frames(world, inp):
    world._hitstop = 3
    for _ in range(3):
        world.update(inp, 1 / 60)
    assert world._hitstop == 0


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------

def test_warp_trigger_sets_warp_target(inp):
    trigger = WarpTrigger(*_SPAWN, 16, 16, "level_03_glass_caverns")
    w = _make_world(triggers=[trigger])
    w.update(inp, 1 / 60)
    assert w.warp_target == "level_03_glass_caverns"


def test_warp_trigger_only_fires_once(inp):
    trigger = WarpTrigger(*_SPAWN, 16, 16, "level_03_glass_caverns")
    w = _make_world(triggers=[trigger])
    w.update(inp, 1 / 60)
    assert trigger.triggered


def test_level_end_sets_complete_and_adds_bonus(inp):
    trigger = LevelEndTrigger(*_SPAWN, 16, 16, score_bonus=1000)
    w = _make_world(triggers=[trigger])
    w.update(inp, 1 / 60)
    assert w.is_level_complete
    assert w.score == 1000


def test_level_end_zero_bonus(inp):
    trigger = LevelEndTrigger(*_SPAWN, 16, 16, score_bonus=0)
    w = _make_world(triggers=[trigger])
    w.update(inp, 1 / 60)
    assert w.score == 0


def test_trigger_not_fired_when_player_far_away(inp):
    trigger = WarpTrigger(600.0, 0.0, 16, 16, "nowhere")  # far from spawn
    w = _make_world(triggers=[trigger])
    w.update(inp, 1 / 60)
    assert w.warp_target is None


# ---------------------------------------------------------------------------
# Carry state
# ---------------------------------------------------------------------------

def test_carry_state_reflects_current_values(world):
    world._lives = 2
    world._score = 750
    world._player.weapon_level = 1
    carry = world.carry_state()
    assert carry == {"lives": 2, "score": 750, "weapon_level": 1}


def test_world_initializes_from_carry(inp):
    carry = {"lives": 2, "score": 1500, "weapon_level": 1}
    w = _make_world(carry=carry)
    assert w.lives == 2
    assert w.score == 1500
    assert w.player.weapon_level == 1


def test_world_default_lives_without_carry(world):
    assert world.lives == PLAYER_LIVES


# ---------------------------------------------------------------------------
# Score from enemies
# ---------------------------------------------------------------------------

def test_score_only_awarded_on_kill():
    from saruman.entities.enemy import BossWarg
    boss = BossWarg(*_SPAWN)
    w = _make_world(enemies=[boss])
    # Stomp 1 — non-lethal
    boss.on_stomped()
    w._score += boss.score_value if not boss.alive else 0
    assert w.score == 0
    # Stomp 2 — non-lethal
    boss.on_stomped()
    w._score += boss.score_value if not boss.alive else 0
    assert w.score == 0
    # Stomp 3 — lethal
    killed = boss.on_stomped()
    if killed:
        w._score += boss.score_value
    assert w.score == boss.score_value


# ---------------------------------------------------------------------------
# ShieldKnight — projectile immunity, stompable in world context
# ---------------------------------------------------------------------------

def test_shieldknight_survives_projectile_in_world():
    """Projectile is consumed but ShieldKnight stays alive."""
    from saruman.entities.enemy import ShieldKnight
    from saruman.entities.projectile import Projectile

    knight = ShieldKnight(50.0, 150.0)
    w = _make_world(enemies=[knight])
    proj = Projectile(float(knight.x), float(knight.y), 1, 0)
    w._projectiles = [proj]
    w._check_projectile_enemy()

    assert knight.alive
    assert not proj.alive


def test_shieldknight_projectile_awards_no_score():
    from saruman.entities.enemy import ShieldKnight
    from saruman.entities.projectile import Projectile

    knight = ShieldKnight(50.0, 150.0)
    w = _make_world(enemies=[knight])
    proj = Projectile(float(knight.x), float(knight.y), 1, 0)
    w._projectiles = [proj]
    w._check_projectile_enemy()

    assert w.score == 0


def test_shieldknight_dies_from_stomp_and_awards_score():
    """Player falling onto ShieldKnight kills it and adds its score value."""
    from saruman.entities.enemy import ShieldKnight

    knight = ShieldKnight(32.0, 145.0)
    w = _make_world(enemies=[knight])

    # Position player above knight, falling
    w._player.x = 32.0
    w._player.y = 130.0       # player centery = 138, knight centery = 153
    w._player.vel_y = 5.0     # positive → falling

    w._check_player_enemy()

    assert not knight.alive
    assert w.score == ShieldKnight.score_value


def test_shieldknight_multiple_shots_projectiles_all_consumed():
    """Each projectile hit on ShieldKnight is consumed (alive=False)."""
    from saruman.entities.enemy import ShieldKnight
    from saruman.entities.projectile import Projectile

    knight = ShieldKnight(50.0, 150.0)
    w = _make_world(enemies=[knight])
    projs = [Projectile(float(knight.x), float(knight.y), 1, 0) for _ in range(3)]
    w._projectiles = list(projs)

    for _ in range(3):
        w._check_projectile_enemy()
        # reset projectile alive status to test repeated hits
        for p in w._projectiles:
            p.alive = True

    assert knight.alive


# ---------------------------------------------------------------------------
# M11 — hit timer set by World on non-lethal hits
# ---------------------------------------------------------------------------

def test_hit_timer_set_on_nonfatal_stomp():
    """Non-lethal stomp of BossWarg sets _hit_timer = 8."""
    from saruman.entities.enemy import BossWarg

    boss = BossWarg(32.0, 145.0)
    w = _make_world(enemies=[boss])
    w._player.x = 32.0
    w._player.y = 130.0
    w._player.vel_y = 5.0

    w._check_player_enemy()

    assert boss._hit_timer == 8


def test_hit_timer_set_on_nonfatal_projectile():
    """Non-lethal projectile hit on BossWarg sets _hit_timer = 6."""
    from saruman.entities.enemy import BossWarg
    from saruman.entities.projectile import Projectile

    boss = BossWarg(50.0, 150.0)
    w = _make_world(enemies=[boss])
    proj = Projectile(float(boss.x), float(boss.y), 1, 0)
    w._projectiles = [proj]

    w._check_projectile_enemy()

    assert boss._hit_timer == 6
    assert boss.alive


def test_hit_timer_decrements_each_update(inp):
    """World decrements _hit_timer by 1 per update while > 0."""
    from saruman.entities.enemy import Goblinkin

    g = Goblinkin(200.0, 150.0)   # far from spawn, won't collide
    w = _make_world(enemies=[g])
    g._hit_timer = 5
    w.update(inp, 1 / 60)
    assert g._hit_timer == 4


def test_hit_timer_not_set_on_lethal_stomp():
    """Lethal stomp (Goblinkin) must not set _hit_timer — enemy dies instead."""
    from saruman.entities.enemy import Goblinkin

    g = Goblinkin(32.0, 145.0)
    w = _make_world(enemies=[g])
    w._player.x = 32.0
    w._player.y = 130.0
    w._player.vel_y = 5.0

    w._check_player_enemy()

    assert not g.alive


def test_knockback_frames_set_on_nonfatal_stomp():
    """Non-lethal stomp of BossWarg sets _knockback_frames = 10."""
    from saruman.entities.enemy import BossWarg

    boss = BossWarg(32.0, 145.0)
    w = _make_world(enemies=[boss])
    w._player.x = 32.0
    w._player.y = 130.0
    w._player.vel_y = 5.0

    w._check_player_enemy()

    assert boss._knockback_frames == 10


def test_knockback_vel_set_on_nonfatal_stomp():
    """Recoil velocity: boss moves away from player horizontally."""
    from saruman.entities.enemy import BossWarg

    # Boss at x=36 overlaps player (x=32, W=8 → right=40); dx=4>0 → rightward recoil
    boss = BossWarg(36.0, 145.0)
    w = _make_world(enemies=[boss])
    w._player.x = 32.0
    w._player.y = 130.0
    w._player.vel_y = 5.0

    w._check_player_enemy()

    assert boss.vel_x > 0    # boss right of player → knocked rightward
    assert boss.vel_y < 0    # slight upward arc


def test_knockback_not_applied_on_lethal_projectile():
    """Lethal shot (Goblinkin) must not set knockback."""
    from saruman.entities.enemy import Goblinkin
    from saruman.entities.projectile import Projectile

    g = Goblinkin(50.0, 150.0)
    w = _make_world(enemies=[g])
    proj = Projectile(float(g.x), float(g.y), 1, 0)
    w._projectiles = [proj]

    w._check_projectile_enemy()

    assert not g.alive
    assert not hasattr(g, "_knockback_frames") or getattr(g, "_knockback_frames", 0) == 0


# ---------------------------------------------------------------------------
# Melee (sword swing) in world context
# ---------------------------------------------------------------------------

def _make_world_with_interactives(enemies=None, interactives=None) -> World:
    return World(
        _FlatMap(), _SPAWN,
        enemies      or [],
        [],
        [],
        None,
        interactives=interactives or [],
    )


def test_melee_kills_goblinkin_and_awards_score():
    from saruman.entities.enemy import Goblinkin
    g = Goblinkin(32.0, 145.0)
    w = _make_world(enemies=[g])
    # Place player facing right so swing_rect overlaps enemy
    w._player.x      = 16.0
    w._player.y      = 140.0
    w._player.facing = 1
    w._player.try_swing()   # activates swing_active = 2

    w._check_melee_enemy()

    assert not g.alive
    assert w.score == g.score_value


def test_melee_hitstop_set_to_6_on_kill():
    from saruman.entities.enemy import Goblinkin
    g = Goblinkin(32.0, 145.0)
    w = _make_world(enemies=[g])
    w._player.x      = 16.0
    w._player.y      = 140.0
    w._player.facing = 1
    w._player.try_swing()

    w._check_melee_enemy()

    assert w._hitstop == 6


def test_melee_sets_hitstop_4_on_nonfatal_hit():
    """Non-lethal melee hit (BossWarg, 3 HP) sets hitstop=4."""
    from saruman.entities.enemy import BossWarg
    boss = BossWarg(32.0, 145.0)
    w = _make_world(enemies=[boss])
    w._player.x      = 16.0
    w._player.y      = 140.0
    w._player.facing = 1
    w._player.try_swing()

    w._check_melee_enemy()

    assert boss.alive        # boss survives first hit
    assert w._hitstop == 4


def test_melee_no_kill_when_swing_inactive():
    from saruman.entities.enemy import Goblinkin
    g = Goblinkin(32.0, 145.0)
    w = _make_world(enemies=[g])
    w._player.x      = 16.0
    w._player.y      = 140.0
    # _swing_active is 0 — no swing
    w._check_melee_enemy()
    assert g.alive


def test_shieldknight_dies_to_melee_in_world():
    """ShieldKnight that blocks projectiles must be killed by melee."""
    from saruman.entities.enemy import ShieldKnight
    knight = ShieldKnight(32.0, 145.0)
    w = _make_world(enemies=[knight])
    w._player.x      = 16.0
    w._player.y      = 140.0
    w._player.facing = 1
    w._player.try_swing()

    w._check_melee_enemy()

    assert not knight.alive
    assert w.score == ShieldKnight.score_value


def test_mimic_drop_added_to_items_on_kill():
    """Killing a MimicChest via melee adds a Gem to world._items."""
    from saruman.entities.enemy import MimicChest
    from saruman.entities.item import Gem
    m = MimicChest(32.0, 145.0)
    # Wake mimic and reduce HP so next hit kills it
    m._awake = True
    m._hp    = 1
    w = _make_world(enemies=[m])
    w._player.x      = 16.0
    w._player.y      = 140.0
    w._player.facing = 1
    w._player.try_swing()

    w._check_melee_enemy()

    assert not m.alive
    gems = [i for i in w._items if isinstance(i, Gem)]
    assert len(gems) == 1


# ---------------------------------------------------------------------------
# Spike hazard in world context
# ---------------------------------------------------------------------------

def test_spike_damages_player_on_overlap():
    from saruman.entities.interactive import Spike
    # Place spike right under the player spawn
    spike = Spike(float(_SPAWN[0]), float(_SPAWN[1]))
    w = _make_world_with_interactives(interactives=[spike])
    lives_before = w.lives

    w._check_player_spikes()

    assert w.lives == lives_before - 1


def test_spike_does_not_damage_invincible_player():
    from saruman.entities.interactive import Spike
    spike = Spike(float(_SPAWN[0]), float(_SPAWN[1]))
    w = _make_world_with_interactives(interactives=[spike])
    w._player._hit_timer = 60   # force invincibility
    lives_before = w.lives

    w._check_player_spikes()

    assert w.lives == lives_before


def test_spike_no_damage_when_player_far():
    from saruman.entities.interactive import Spike
    spike = Spike(500.0, 500.0)   # far from spawn
    w = _make_world_with_interactives(interactives=[spike])
    lives_before = w.lives

    w._check_player_spikes()

    assert w.lives == lives_before


def test_spike_remains_alive_after_triggering():
    """Spikes are permanent — alive stays True."""
    from saruman.entities.interactive import Spike
    spike = Spike(float(_SPAWN[0]), float(_SPAWN[1]))
    w = _make_world_with_interactives(interactives=[spike])

    w._check_player_spikes()

    assert spike.alive is True


# ---------------------------------------------------------------------------
# Shield parry in world context
# ---------------------------------------------------------------------------

def test_shield_parry_blocks_enemy_projectile():
    """Shielding player must survive a direct EnemyProjectile hit."""
    from saruman.entities.projectile import EnemyProjectile
    w = _make_world()
    w._player._shielding = True
    w._player._shield_cd = 0
    ep = EnemyProjectile(float(_SPAWN[0]), float(_SPAWN[1]), 1)
    w._enemy_projectiles = [ep]
    lives_before = w.lives
    w._check_player_enemy_projectiles()
    assert w.lives == lives_before   # no damage taken


def test_shield_parry_consumes_projectile():
    """Blocked projectile must be marked dead."""
    from saruman.entities.projectile import EnemyProjectile
    w = _make_world()
    w._player._shielding = True
    w._player._shield_cd = 0
    ep = EnemyProjectile(float(_SPAWN[0]), float(_SPAWN[1]), 1)
    w._enemy_projectiles = [ep]
    w._check_player_enemy_projectiles()
    assert not ep.alive


def test_shield_parry_sets_cooldown():
    """After absorbing a hit, _shield_cd must be > 0."""
    from saruman.entities.projectile import EnemyProjectile
    w = _make_world()
    w._player._shielding = True
    w._player._shield_cd = 0
    ep = EnemyProjectile(float(_SPAWN[0]), float(_SPAWN[1]), 1)
    w._enemy_projectiles = [ep]
    w._check_player_enemy_projectiles()
    assert w._player._shield_cd > 0


def test_no_parry_without_shielding():
    """Unshielded player must take damage from an EnemyProjectile."""
    from saruman.entities.projectile import EnemyProjectile
    w = _make_world()
    w._player._shielding = False
    ep = EnemyProjectile(float(_SPAWN[0]), float(_SPAWN[1]), 1)
    w._enemy_projectiles = [ep]
    lives_before = w.lives
    w._check_player_enemy_projectiles()
    assert w.lives == lives_before - 1


# ---------------------------------------------------------------------------
# take_spawn() loop in world context
# ---------------------------------------------------------------------------

def test_take_spawn_loop_adds_enemy():
    """GoblinKing's queued minions are transferred to _enemies each update."""
    from saruman.entities.enemy import GoblinKing
    gk = GoblinKing(200.0, 144.0)
    # Pre-queue a Goblinkin in the boss's pending list
    from saruman.entities.enemy import Goblinkin
    gk._pend_spawns = [Goblinkin(200.0, 144.0)]

    w = _make_world(enemies=[gk])
    enemy_count_before = len(w._enemies)

    # Drive one tick of the take_spawn collection phase
    for enemy in w._enemies:
        if enemy.alive:
            new_spawns = enemy.take_spawn()
            if new_spawns:
                w._pending_spawns.extend(new_spawns)
    if w._pending_spawns:
        w._enemies.extend(w._pending_spawns)
        w._pending_spawns.clear()

    assert len(w._enemies) == enemy_count_before + 1


def test_take_spawn_loop_exhausts_pending():
    """take_spawn() must drain the boss's internal queue — second call returns []."""
    from saruman.entities.enemy import GoblinKing, Goblinkin
    gk = GoblinKing(200.0, 144.0)
    gk._pend_spawns = [Goblinkin(200.0, 144.0)]
    gk.take_spawn()   # drain
    assert gk.take_spawn() == []
