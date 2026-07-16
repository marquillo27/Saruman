from __future__ import annotations

import math

import pygame

from saruman.config import (
    ARCHER_ANIM_RATE, BAT_ANIM_RATE, BAT_FLOAT_AMP, BOSS_CHARGE_R, BOSS_SPEED,
    BOSSWARG_ANIM_RATE, GOBLIN_ANIM_RATE, GOBLIN_SPEED, GOBLINKING_ANIM_RATE,
    GOBLINKING_SPEED_P1, GOBLINKING_SPEED_P2, MIMIC_ANIM_RATE,
    NIGHTKING_ANIM_RATE, NIGHTKING_SPEED_P1, NIGHTKING_SPEED_P2,
    SHIELDKNIGHT_ANIM_RATE, SLIME_ANIM_RATE, SMALL_SLIME_ANIM_RATE,
    SPITTER_ANIM_RATE, TILE_SIZE, WRAITH_ANIM_RATE, WRAITH_FLOAT_AMP, WRAITH_SPEED,
)
from saruman.core.assets import get_strip_frame
from saruman.entities.entity import Entity
from saruman.entities.projectile import AcidBlob, EnemyProjectile
from saruman.physics.collision import move_and_collide


class Enemy(Entity):
    score_value:    int  = 0
    can_be_stomped: bool = True
    is_boss:        bool = False   # bosses are immune to nuke / fruit transform
    _hit_timer:     int  = 0   # class default kept for `Enemy._hit_timer == 0` test

    def __init__(self, x: float, y: float, w: int, h: int) -> None:
        super().__init__(x, y, w, h)
        self._hit_timer = 0   # instance attribute shadows class default

    def _turn_at_cliff(self, tilemap) -> None:
        """Reverse facing when there's no ground tile ahead of the leading foot.
        No-op while airborne."""
        if not self.on_ground:
            return
        foot_ty  = self.rect.bottom // TILE_SIZE
        ahead_tx = (
            self.rect.right // TILE_SIZE if self.facing > 0
            else (self.rect.left - 1) // TILE_SIZE
        )
        if not tilemap.is_solid(ahead_tx, foot_ty):
            self.facing *= -1

    def _blit_strip(
        self, surface: pygame.Surface, sx: int, sy: int,
        asset: str, frame: int, *, center: bool = False,
    ) -> bool:
        """Blit one strip frame, flipped by facing. Returns False if the sprite is
        missing so the caller can draw its placeholder. `center` aligns oversized
        frames over the hitbox."""
        spr = get_strip_frame(asset, frame, self.w, self.h, flip_x=(self.facing < 0))
        if spr is None:
            return False
        if center:
            sx -= (spr.get_width()  - self.w) // 2
            sy -= (spr.get_height() - self.h) // 2
        surface.blit(spr, (sx, sy))
        return True

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        raise NotImplementedError

    def tick(self) -> None:
        """Decrement per-frame timers. Called by World once per update."""
        if self._hit_timer > 0:
            self._hit_timer -= 1

    def take_shot(self) -> EnemyProjectile | None:
        """Return a pending EnemyProjectile if any, else None. Consumed by World."""
        return None

    def start_hit_flash(self, frames: int = 6) -> None:
        """Begin the hit-flash effect for the given number of frames."""
        self._hit_timer = frames

    def apply_knockback(self, source_x: float) -> None:
        """Override in subclasses that support knockback (e.g. BossWarg)."""

    def on_kill_spawn(self) -> list["Enemy"]:
        """Return enemies to spawn at this one's position when killed (e.g. Slime split)."""
        return []

    def take_spawn(self) -> list["Enemy"]:
        """Return enemies to spawn this frame (e.g. GoblinKing minions). Default: empty."""
        return []

    def on_kill_drop(self) -> list:
        """Return item instances to place at this enemy's position on kill."""
        return []

    def on_stomped(self) -> bool:
        """Return True if the enemy was just killed."""
        self.alive = False
        return True

    def on_shot(self) -> bool:
        """Return True if the enemy was just killed."""
        self.alive = False
        return True

    def on_melee(self) -> bool:
        """Return True if killed by a melee swing. Default: same behaviour as on_shot()."""
        return self.on_shot()

    def _draw_hit_flash(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        if self._hit_timer <= 0:
            return
        if (self._hit_timer // 2) % 2 == 1:
            return
        flash = pygame.Surface((self.w, self.h))
        flash.fill((255, 255, 255))
        flash.set_alpha(180)
        surface.blit(flash, (sx, sy))


class Goblinkin(Enemy):
    W = 12
    H = 14
    score_value = 100

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._anim_tick = 0

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()
        self._turn_at_cliff(tilemap)

        prev_vx    = self.vel_x
        self.vel_x = GOBLIN_SPEED * self.facing
        move_and_collide(self, tilemap)

        if self.vel_x == 0.0 and prev_vx != 0.0:
            self.facing *= -1
        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // GOBLIN_ANIM_RATE) % 4
        if not self._blit_strip(surface, sx, sy, "enemy_goblinkin", frame, center=True):
            pygame.draw.rect(surface, (30, 110, 30), (sx, sy, self.W, self.H))
            eye_x = sx + (8 if self.facing > 0 else 2)
            pygame.draw.rect(surface, (220, 50, 50), (eye_x, sy + 3, 2, 2))
        self._draw_hit_flash(surface, sx, sy)


class Wraith(Enemy):
    W = 12
    H = 16
    score_value    = 200
    can_be_stomped = False

    def __init__(self, x: float, y: float, patrol_w: float = 64.0) -> None:
        super().__init__(x, y, self.W, self.H)
        self._spawn_x   = x
        self._base_y    = y
        self._patrol_w  = patrol_w
        self._time      = 0.0
        self._anim_tick = 0

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self._time += dt
        self.x += WRAITH_SPEED * self.facing

        if self.x > self._spawn_x + self._patrol_w:
            self.facing = -1
        elif self.x < self._spawn_x - self._patrol_w:
            self.facing = 1

        self.y = self._base_y + math.sin(self._time * 2.0) * WRAITH_FLOAT_AMP
        self.on_ground  = False
        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // WRAITH_ANIM_RATE) % 4
        if not self._blit_strip(surface, sx, sy, "enemy_wraith", frame, center=True):
            pygame.draw.rect(surface, (70, 20, 110), (sx, sy, self.W, self.H))
            pygame.draw.rect(surface, (110, 60, 160), (sx + 2, sy + 2, self.W - 4, self.H - 6))
        self._draw_hit_flash(surface, sx, sy)


class BossWarg(Enemy):
    W = 24
    H = 20
    score_value       = 500
    is_boss           = True
    _MAX_HP           = 3
    _KNOCKBACK_VEL_X  = 3.5
    _KNOCKBACK_VEL_Y  = -2.5
    _KNOCKBACK_FRAMES = 10

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._hp               = self._MAX_HP
        self.facing            = -1
        self._anim_tick        = 0
        self._knockback_frames = 0

    def _take_hit(self) -> bool:
        """Reduce HP by 1. Return True if the boss was just killed."""
        self._hp -= 1
        if self._hp <= 0:
            self.alive = False
            return True
        return False

    def on_stomped(self) -> bool:
        return self._take_hit()

    def on_shot(self) -> bool:
        return self._take_hit()

    def apply_knockback(self, source_x: float) -> None:
        dx = self.x - source_x
        self.vel_x = self._KNOCKBACK_VEL_X if dx > 0 else -self._KNOCKBACK_VEL_X
        self.vel_y = self._KNOCKBACK_VEL_Y
        self._knockback_frames = self._KNOCKBACK_FRAMES

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()

        if self._knockback_frames > 0:
            self._knockback_frames -= 1
            move_and_collide(self, tilemap)
            if self.vel_x == 0.0:
                self.facing *= -1
            self._anim_tick += 1
            return

        if player_rect is not None:
            dx = player_rect.centerx - self.rect.centerx
            if abs(dx) <= BOSS_CHARGE_R:
                self.vel_x = BOSS_SPEED * (1 if dx > 0 else -1)
                self.facing = 1 if dx > 0 else -1
            else:
                self._patrol(tilemap)
        else:
            self._patrol(tilemap)

        move_and_collide(self, tilemap)

        # Wall bounce
        if self.vel_x == 0.0:
            self.facing *= -1

        self._anim_tick += 1

    def _patrol(self, tilemap) -> None:
        self._turn_at_cliff(tilemap)
        self.vel_x = GOBLIN_SPEED * self.facing

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // BOSSWARG_ANIM_RATE) % 4
        if not self._blit_strip(surface, sx, sy, "enemy_bosswarg", frame, center=True):
            pygame.draw.rect(surface, (110, 35, 20), (sx, sy + 4, self.W, self.H - 4))
            pygame.draw.rect(surface, (130, 45, 25), (sx + 2, sy, self.W - 4, 10))
            eye_x = sx + (16 if self.facing > 0 else 4)
            pygame.draw.rect(surface, (255, 80, 0), (eye_x, sy + 3, 3, 3))
        # HP pips always rendered above sprite
        for i in range(self._MAX_HP):
            col = (220, 60, 60) if i < self._hp else (60, 30, 30)
            pygame.draw.rect(surface, col, (sx + i * 8, sy - 4, 6, 3))
        self._draw_hit_flash(surface, sx, sy)


class ShieldKnight(Enemy):
    W = 12
    H = 16
    score_value = 150

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._anim_tick = 0

    def on_shot(self) -> bool:
        from saruman.core.audio import get_audio
        get_audio().play_sfx("shield_block.wav")
        return False  # immune to projectiles

    def on_melee(self) -> bool:
        """Melee bypasses the shield — kills immediately."""
        self.alive = False
        return True

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()
        self._turn_at_cliff(tilemap)
        prev_vx    = self.vel_x
        self.vel_x = GOBLIN_SPEED * self.facing
        move_and_collide(self, tilemap)
        if self.vel_x == 0.0 and prev_vx != 0.0:
            self.facing *= -1
        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // SHIELDKNIGHT_ANIM_RATE) % 2
        if not self._blit_strip(surface, sx, sy, "enemy_shieldknight", frame, center=True):
            pygame.draw.rect(surface, (80, 80, 120), (sx, sy, self.W, self.H))
            pygame.draw.rect(surface, (160, 160, 200), (sx, sy, 4, self.H))
        self._draw_hit_flash(surface, sx, sy)


class SkeletonArcher(Enemy):
    W              = 12
    H              = 16
    score_value    = 200
    _DETECT_RANGE  = 120
    _SHOT_INTERVAL = 80

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._anim_tick    = 0
        self._shot_timer   = 0
        self._pending_shot: EnemyProjectile | None = None

    def take_shot(self) -> EnemyProjectile | None:
        shot, self._pending_shot = self._pending_shot, None
        return shot

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()
        self._shot_timer = max(0, self._shot_timer - 1)
        self._pending_shot = None

        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            if abs(dx) <= self._DETECT_RANGE:
                self.facing = 1 if dx > 0 else -1
                self.vel_x  = 0.0
                move_and_collide(self, tilemap)
                if self._shot_timer == 0:
                    self._shot_timer = self._SHOT_INTERVAL
                    px = float(
                        self.rect.right if self.facing > 0
                        else self.rect.left - EnemyProjectile.W
                    )
                    py = float(self.rect.centery - 1)
                    self._pending_shot = EnemyProjectile(px, py, self.facing)
                self._anim_tick += 1
                return

        # Patrol
        self.vel_x = GOBLIN_SPEED * self.facing
        self._turn_at_cliff(tilemap)
        move_and_collide(self, tilemap)
        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // ARCHER_ANIM_RATE) % 2
        if not self._blit_strip(surface, sx, sy, "enemy_archer", frame):
            pygame.draw.rect(surface, (185, 180, 165), (sx, sy, self.W, self.H))
            eye_x = sx + (8 if self.facing > 0 else 2)
            pygame.draw.rect(surface, (40, 10, 10), (eye_x, sy + 4, 2, 2))
        self._draw_hit_flash(surface, sx, sy)


class CaveBat(Enemy):
    W              = 10
    H              = 8
    score_value    = 150
    can_be_stomped = False
    AGGRO_RANGE    = 90
    AGGRO_SPEED    = 2.5
    PATROL_SPEED   = 0.7

    def __init__(self, x: float, y: float, patrol_w: float = 70.0) -> None:
        super().__init__(x, y, self.W, self.H)
        self._spawn_x   = x
        self._base_y    = y
        self._patrol_w  = patrol_w
        self._time      = 0.0
        self._anim_tick = 0
        self._aggro     = False

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self._time += dt
        self.on_ground = False

        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            if abs(dx) <= self.AGGRO_RANGE:
                self._aggro = True
            elif abs(dx) > self.AGGRO_RANGE * 1.5:
                self._aggro = False

        if self._aggro and player_rect:
            dx   = player_rect.centerx - self.rect.centerx
            dy   = player_rect.centery  - self.rect.centery
            dist = max(1.0, (dx ** 2 + dy ** 2) ** 0.5)
            self.x += (dx / dist) * self.AGGRO_SPEED
            self.y += (dy / dist) * self.AGGRO_SPEED
            self.facing = 1 if dx > 0 else -1
        else:
            self.x += self.PATROL_SPEED * self.facing
            if self.x > self._spawn_x + self._patrol_w:
                self.facing = -1
            elif self.x < self._spawn_x - self._patrol_w:
                self.facing = 1
            self.y = self._base_y + math.sin(self._time * 2.5) * BAT_FLOAT_AMP

        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // BAT_ANIM_RATE) % 2
        if not self._blit_strip(surface, sx, sy, "enemy_bat", frame):
            col = (160, 50, 160) if self._aggro else (100, 35, 110)
            pygame.draw.rect(surface, col, (sx, sy, self.W, self.H))
        self._draw_hit_flash(surface, sx, sy)


class Slime(Enemy):
    """Hops along the ground. Splits into two SmallSlime on stomp."""
    W           = 10
    H           = 8
    score_value = 75
    _HOP_PERIOD = 40
    _HOP_VY     = -3.5
    _HOP_VX     = 0.6

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._hop_timer = 0
        self._anim_tick = 0

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()

        if self.on_ground:
            self._hop_timer += 1
            if self._hop_timer >= self._HOP_PERIOD:
                self._hop_timer = 0
                self.vel_y = self._HOP_VY
                self.vel_x = self._HOP_VX * self.facing
            else:
                self.vel_x = 0.0

        prev_vx = self.vel_x
        move_and_collide(self, tilemap)
        if self.vel_x == 0.0 and prev_vx != 0.0:
            self.facing *= -1

        # Edge detection: about-face if landing would put us off a ledge next hop
        self._turn_at_cliff(tilemap)

        self._anim_tick += 1

    def on_kill_spawn(self) -> list[Enemy]:
        sx_left  = self.x - 2
        sx_right = self.x + self.W - SmallSlime.W + 2
        sy       = self.y + self.H - SmallSlime.H
        left  = SmallSlime(sx_left,  sy)
        right = SmallSlime(sx_right, sy)
        left.facing  = -1
        right.facing = 1
        left.vel_y   = -2.5
        right.vel_y  = -2.5
        return [left, right]

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // SLIME_ANIM_RATE) % 2
        if not self._blit_strip(surface, sx, sy, "enemy_slime", frame):
            pygame.draw.rect(surface, (90, 180, 110), (sx, sy + 2, self.W, self.H - 2))
            pygame.draw.rect(surface, (140, 220, 150), (sx + 2, sy, self.W - 4, 3))
        self._draw_hit_flash(surface, sx, sy)


class SmallSlime(Enemy):
    """Tiny slime spawned from a Slime split. Single-stomp kill, no further split."""
    W           = 6
    H           = 5
    score_value = 30
    _HOP_PERIOD = 28
    _HOP_VY     = -2.8
    _HOP_VX     = 0.8

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._hop_timer = 0
        self._anim_tick = 0

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()
        if self.on_ground:
            self._hop_timer += 1
            if self._hop_timer >= self._HOP_PERIOD:
                self._hop_timer = 0
                self.vel_y = self._HOP_VY
                self.vel_x = self._HOP_VX * self.facing
            else:
                self.vel_x = 0.0

        prev_vx = self.vel_x
        move_and_collide(self, tilemap)
        if self.vel_x == 0.0 and prev_vx != 0.0:
            self.facing *= -1
        self._turn_at_cliff(tilemap)
        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // SMALL_SLIME_ANIM_RATE) % 2
        if not self._blit_strip(surface, sx, sy, "enemy_small_slime", frame):
            pygame.draw.rect(surface, (100, 200, 130), (sx, sy + 1, self.W, self.H - 1))
            pygame.draw.rect(surface, (160, 240, 170), (sx + 1, sy, self.W - 2, 2))
        self._draw_hit_flash(surface, sx, sy)


class SpitterPlant(Enemy):
    """Immobile turret. Lobs an arcing AcidBlob toward the player periodically."""
    W              = 12
    H              = 12
    score_value    = 250
    _DETECT_RANGE  = 140
    _SHOT_INTERVAL = 120

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._anim_tick    = 0
        self._shot_timer   = 0
        self._pending_shot: AcidBlob | None = None

    def take_shot(self) -> AcidBlob | None:
        shot, self._pending_shot = self._pending_shot, None
        return shot

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        # Always anchored — no gravity, no movement.
        self.vel_x = 0.0
        self.vel_y = 0.0
        self._shot_timer = max(0, self._shot_timer - 1)
        self._pending_shot = None
        self._anim_tick += 1

        if not player_rect:
            return
        dx = player_rect.centerx - self.rect.centerx
        if abs(dx) > self._DETECT_RANGE:
            return
        self.facing = 1 if dx > 0 else -1

        if self._shot_timer == 0:
            self._shot_timer = self._SHOT_INTERVAL
            px = float(
                self.rect.right if self.facing > 0
                else self.rect.left - AcidBlob.W
            )
            py = float(self.rect.top + 1)
            self._pending_shot = AcidBlob(px, py, self.facing)

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // SPITTER_ANIM_RATE) % 2
        if not self._blit_strip(surface, sx, sy, "enemy_spitter", frame):
            # Pot
            pygame.draw.rect(surface, (90, 60, 40), (sx + 2, sy + 8, self.W - 4, 4))
            # Stem
            pygame.draw.rect(surface, (50, 110, 50), (sx + 5, sy + 4, 2, 5))
            # Bud
            pygame.draw.rect(surface, (140, 50, 130), (sx + 3, sy, self.W - 6, 5))
            pygame.draw.rect(surface, (200, 100, 180), (sx + 4, sy + 1, self.W - 8, 2))
        self._draw_hit_flash(surface, sx, sy)


class MimicChest(Enemy):
    """Disguised chest. Wakes and chases when player approaches."""
    W              = 14
    H              = 12
    score_value    = 400
    _DETECT_RANGE  = 50
    _MAX_HP        = 3
    _CHASE_SPEED   = 1.6
    _JUMP_VEL      = -6.0

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._awake     = False
        self._hp        = self._MAX_HP
        self._anim_tick = 0

    def _take_hit(self) -> bool:
        self._hp -= 1
        if self._hp <= 0:
            self.alive = False
            return True
        return False

    def on_stomped(self) -> bool:
        # First contact wakes the mimic; subsequent stomps damage it
        if not self._awake:
            self._awake = True
            return False
        return self._take_hit()

    def on_shot(self) -> bool:
        if not self._awake:
            self._awake = True
            return False
        return self._take_hit()

    def on_kill_drop(self) -> list:
        from saruman.entities.item import Gem
        return [Gem(self.x + 3, self.y, color="purple")]

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()

        if not self._awake:
            self.vel_x = 0.0
            if player_rect:
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                if dx * dx + dy * dy <= self._DETECT_RANGE * self._DETECT_RANGE:
                    self._awake = True
            move_and_collide(self, tilemap)
            self._anim_tick += 1
            return

        # Awake — chase the player
        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            self.facing = 1 if dx >= 0 else -1
        prev_vx    = self.vel_x
        self.vel_x = self._CHASE_SPEED * self.facing
        move_and_collide(self, tilemap)
        # Jump if blocked by a wall (vel_x got zeroed despite trying to move)
        if self.on_ground and self.vel_x == 0.0 and prev_vx != 0.0:
            self.vel_y = self._JUMP_VEL
        self._anim_tick += 1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:   # type: ignore[override]
        if not self._awake:
            if not self._blit_strip(surface, sx, sy, "enemy_mimic", 0):
                # Sleeping chest disguise
                pygame.draw.rect(surface, (90, 60, 40), (sx, sy + 4, self.W, self.H - 4))
                pygame.draw.rect(surface, (140, 100, 60), (sx, sy + 2, self.W, 4))
                pygame.draw.rect(surface, (210, 170, 80), (sx + self.W // 2 - 1, sy + 5, 2, 3))
        else:
            frame = 1 + (self._anim_tick // MIMIC_ANIM_RATE) % 2
            if not self._blit_strip(surface, sx, sy, "enemy_mimic", frame):
                pygame.draw.rect(surface, (90, 60, 40), (sx, sy + 4, self.W, self.H - 4))
                pygame.draw.rect(surface, (140, 100, 60), (sx, sy + 2, self.W, 4))
                # Teeth
                for i in range(3):
                    pygame.draw.rect(surface, (240, 240, 220),
                                     (sx + 2 + i * 4, sy + 6, 2, 2))
                # Eye
                eye_x = sx + (10 if self.facing > 0 else 2)
                pygame.draw.rect(surface, (255, 60, 60), (eye_x, sy + 1, 2, 2))
            # HP pips
            for i in range(self._MAX_HP):
                col = (220, 60, 60) if i < self._hp else (60, 30, 30)
                pygame.draw.rect(surface, col, (sx + i * 5, sy - 3, 3, 2))
        self._draw_hit_flash(surface, sx, sy)


class GoblinKing(Enemy):
    """Multi-phase final boss. Phase 1: charges + spawns minions. Phase 2: charges faster + shoots."""
    W               = 28
    H               = 24
    score_value     = 1500
    is_boss         = True
    _MAX_HP         = 5
    _PHASE2_HP      = 2
    _SPAWN_INTERVAL = 300   # frames between phase-1 minion spawns
    _SHOT_INTERVAL  = 80    # frames between phase-2 projectile shots

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._hp           = self._MAX_HP
        self._spawn_timer  = 0
        self._shot_timer   = 0
        self._pend_spawns: list[Enemy] = []
        self._pend_shot:   EnemyProjectile | None = None
        self._anim_tick    = 0
        self.facing        = -1

    @property
    def phase(self) -> int:
        return 2 if self._hp <= self._PHASE2_HP else 1

    def _take_hit(self) -> bool:
        self._hp -= 1
        if self._hp <= 0:
            self.alive = False
            return True
        return False

    def on_stomped(self) -> bool:
        return self._take_hit()

    def on_shot(self) -> bool:
        return self._take_hit()

    def on_kill_drop(self) -> list:
        from saruman.entities.item import Gem
        return [Gem(self.x + self.W // 2, self.y, color="red")]

    def take_shot(self) -> EnemyProjectile | None:
        shot, self._pend_shot = self._pend_shot, None
        return shot

    def take_spawn(self) -> list[Enemy]:
        spawns, self._pend_spawns = self._pend_spawns, []
        return spawns

    def apply_knockback(self, source_x: float) -> None:
        dx = self.x - source_x
        self.vel_x = 2.5 if dx > 0 else -2.5
        self.vel_y = -2.0

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()
        self._anim_tick += 1
        if self._spawn_timer > 0: self._spawn_timer -= 1
        if self._shot_timer  > 0: self._shot_timer  -= 1

        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            self.facing = 1 if dx > 0 else -1
            speed = GOBLINKING_SPEED_P2 if self.phase == 2 else GOBLINKING_SPEED_P1
            self.vel_x = speed * self.facing

            if self.phase == 1 and self._spawn_timer == 0:
                self._spawn_timer = self._SPAWN_INTERVAL
                self._pend_spawns.append(
                    Goblinkin(self.x - 12 * self.facing, self.y)
                )

            if self.phase == 2 and self._shot_timer == 0:
                self._shot_timer = self._SHOT_INTERVAL
                px = float(
                    self.rect.right if self.facing > 0
                    else self.rect.left - EnemyProjectile.W
                )
                self._pend_shot = EnemyProjectile(
                    px, float(self.rect.centery - 1), self.facing
                )
        else:
            self.vel_x = 0.0

        move_and_collide(self, tilemap)
        if self.vel_x == 0.0:
            self.facing *= -1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // GOBLINKING_ANIM_RATE) % 3
        if not self._blit_strip(surface, sx, sy, "enemy_goblin_king", frame, center=True):
            # Phase 2: red glow outline
            if self.phase == 2:
                pygame.draw.rect(surface, (200, 30, 10), (sx - 2, sy - 2, self.W + 4, self.H + 4))
            # Body
            pygame.draw.rect(surface, (80, 110, 45), (sx, sy + 4, self.W, self.H - 4))
            # Head
            pygame.draw.rect(surface, (90, 125, 50), (sx + 4, sy, 20, 14))
            # Crown (gold spikes)
            for i in range(3):
                cx_off = sx + 6 + i * 6
                pygame.draw.polygon(surface, (200, 160, 40), [
                    (cx_off, sy - 4), (cx_off + 2, sy), (cx_off + 4, sy - 4)
                ])
            # Eyes
            eye_x = sx + (18 if self.facing > 0 else 6)
            eye_col = (255, 60, 60) if self.phase == 2 else (255, 200, 40)
            pygame.draw.rect(surface, eye_col, (eye_x, sy + 3, 3, 3))
        # HP pips
        for i in range(self._MAX_HP):
            col = (220, 60, 60) if i < self._hp else (60, 30, 30)
            pygame.draw.rect(surface, col, (sx + i * 6, sy - 5, 4, 3))
        self._draw_hit_flash(surface, sx, sy)


class NightKing(Enemy):
    """Final boss of the campaign. Phase 1: stalks + summons icy wraiths.
    Phase 2: charges faster + fires frost bolts. Tougher than GoblinKing."""
    W               = 30
    H               = 26
    score_value     = 2500
    is_boss         = True
    _MAX_HP         = 6
    _PHASE2_HP      = 3
    _SPAWN_INTERVAL = 260   # frames between phase-1 wraith summons
    _SHOT_INTERVAL  = 70    # frames between phase-2 frost bolts

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._hp           = self._MAX_HP
        self._spawn_timer  = 0
        self._shot_timer   = 0
        self._pend_spawns: list[Enemy] = []
        self._pend_shot:   EnemyProjectile | None = None
        self._anim_tick    = 0
        self.facing        = -1

    @property
    def phase(self) -> int:
        return 2 if self._hp <= self._PHASE2_HP else 1

    def _take_hit(self) -> bool:
        self._hp -= 1
        if self._hp <= 0:
            self.alive = False
            return True
        return False

    def on_stomped(self) -> bool:
        return self._take_hit()

    def on_shot(self) -> bool:
        return self._take_hit()

    def on_kill_drop(self) -> list:
        from saruman.entities.item import Gem
        return [Gem(self.x + self.W // 2, self.y, color="blue")]

    def take_shot(self) -> EnemyProjectile | None:
        shot, self._pend_shot = self._pend_shot, None
        return shot

    def take_spawn(self) -> list[Enemy]:
        spawns, self._pend_spawns = self._pend_spawns, []
        return spawns

    def apply_knockback(self, source_x: float) -> None:
        dx = self.x - source_x
        self.vel_x = 2.5 if dx > 0 else -2.5
        self.vel_y = -2.0

    def update(self, tilemap, dt: float, player_rect=None) -> None:
        self.apply_gravity()
        self._anim_tick += 1
        if self._spawn_timer > 0: self._spawn_timer -= 1
        if self._shot_timer  > 0: self._shot_timer  -= 1

        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            self.facing = 1 if dx > 0 else -1
            speed = NIGHTKING_SPEED_P2 if self.phase == 2 else NIGHTKING_SPEED_P1
            self.vel_x = speed * self.facing

            if self.phase == 1 and self._spawn_timer == 0:
                self._spawn_timer = self._SPAWN_INTERVAL
                self._pend_spawns.append(
                    Wraith(self.x - 14 * self.facing, self.y - 6)
                )

            if self.phase == 2 and self._shot_timer == 0:
                self._shot_timer = self._SHOT_INTERVAL
                px = float(
                    self.rect.right if self.facing > 0
                    else self.rect.left - EnemyProjectile.W
                )
                self._pend_shot = EnemyProjectile(
                    px, float(self.rect.centery - 1), self.facing
                )
        else:
            self.vel_x = 0.0

        move_and_collide(self, tilemap)
        if self.vel_x == 0.0:
            self.facing *= -1

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        frame = (self._anim_tick // NIGHTKING_ANIM_RATE) % 3
        if not self._blit_strip(surface, sx, sy, "enemy_night_king", frame, center=True):
            # Phase 2: icy glow outline
            if self.phase == 2:
                pygame.draw.rect(surface, (120, 200, 255), (sx - 2, sy - 2, self.W + 4, self.H + 4))
            # Body (pale blue)
            pygame.draw.rect(surface, (120, 150, 185), (sx, sy + 4, self.W, self.H - 4))
            # Head
            pygame.draw.rect(surface, (150, 180, 210), (sx + 5, sy, 20, 14))
            # Crown (white ice spikes)
            for i in range(3):
                cx_off = sx + 7 + i * 6
                pygame.draw.polygon(surface, (235, 245, 255), [
                    (cx_off, sy - 5), (cx_off + 2, sy), (cx_off + 4, sy - 5)
                ])
            # Eyes
            eye_x = sx + (19 if self.facing > 0 else 6)
            eye_col = (120, 220, 255) if self.phase == 2 else (90, 160, 230)
            pygame.draw.rect(surface, eye_col, (eye_x, sy + 3, 3, 3))
        # HP pips
        for i in range(self._MAX_HP):
            col = (120, 200, 255) if i < self._hp else (30, 40, 60)
            pygame.draw.rect(surface, col, (sx + i * 6, sy - 5, 4, 3))
        self._draw_hit_flash(surface, sx, sy)
