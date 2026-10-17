from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from saruman.config import (
    AIR_ACCEL, AIR_DECEL, AIR_TURN, APEX_GRAVITY_MULT, APEX_HANG_SPEED,
    COYOTE_FRAMES, GRAVITY, GRAVITY_FALL, JUMP_BUFFER_FRAMES, JUMP_CUT_GRAVITY_MULT,
    JUMP_VEL, MOVE_SPEED, PLAYER_MAX_FALL, RUN_ACCEL, RUN_DECEL, RUN_TURN,
    TILE_SIZE, WALL_COYOTE, WALL_JUMP_LOCK, WALL_JUMP_PUSH, WALL_JUMP_VEL_Y,
    WALL_SLIDE_SPEED,
    COL_GOLD, COL_DARK_GRAY, HIT_IFRAMES, SHOOT_COOLDOWN, SWING_COOLDOWN, SHIELD_CD,
)
from saruman.core.assets import get_sprite, get_strip_frame
from saruman.core.audio import get_audio
from saruman.core.input import Action, Input
from saruman.entities.entity import Entity
from saruman.physics.collision import move_and_collide

if TYPE_CHECKING:
    from saruman.entities.projectile import Projectile


# Frame indices in assets/sprites/hero_strip.png (see tools/generate_hero.py)
_HERO_W, _HERO_H = 24, 36
_F_IDLE, _F_WALK, _F_JUMP, _F_FALL, _F_ATTACK, _F_WALL = 0, 4, 10, 11, 12, 15
_HERO_CENTER_X   = 11       # body centre column inside a right-facing frame
_HERO_FEET_Y     = 34       # last boot row inside a frame


class Player(Entity):
    W = 12
    H = 28
    _DEATH_FRAMES = 35

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._coyote_timer   = 0
        self._jump_buffer    = 0
        self._jumps_left     = 2
        self._jump_cuttable  = True   # False after a spring: its launch is fixed
        self._wall_dir       = 0      # -1 / 1 while touching a wall in the air
        self._wall_coyote    = 0      # frames left to wall-jump after leaving it
        self._wall_jump_dir  = 0      # side of the wall last touched
        self._wall_lock      = 0      # frames of locked air steering
        self._wall_sliding   = False
        self._hit_timer      = 0
        self._shoot_cooldown = 0
        self._swing_cooldown = 0
        self._swing_active   = 0   # frames the melee hitbox remains live
        self._swing_anim     = 0   # frames of attack animation remaining (9 → 0)
        self._shielding      = False
        self._shield_cd      = 0   # countdown after absorbing a hit
        self._bonus_invuln   = 0   # bonus power-up invulnerability (frames)
        self.weapon_level    = 0
        self._anim_tick      = 0
        self._idle_tick      = 0
        self._land_timer     = 0
        self._dying          = False
        self._death_timer    = 0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def invincible(self) -> bool:
        return self._hit_timer > 0 or self._bonus_invuln > 0

    @property
    def hit_invincible(self) -> bool:
        """True only during the brief post-hit i-frames (ignores bonus shield)."""
        return self._hit_timer > 0

    @property
    def shielded_bonus(self) -> bool:
        return self._bonus_invuln > 0

    def grant_respawn_iframes(self) -> None:
        """Blinking post-hit invulnerability after reappearing at a checkpoint."""
        self._hit_timer = HIT_IFRAMES

    def grant_invuln(self, frames: int) -> None:
        """Grant a timed invulnerability bonus (the shield power-up)."""
        self._bonus_invuln = max(self._bonus_invuln, frames)

    @property
    def dying(self) -> bool:
        return self._dying

    @property
    def shielding(self) -> bool:
        return self._shielding

    def trigger_death(self) -> None:
        self._dying       = True
        self._death_timer = self._DEATH_FRAMES

    def take_damage(self) -> None:
        if self._hit_timer > 0:
            return
        self._hit_timer = HIT_IFRAMES
        self.vel_y = -3.0
        self.vel_x = -self.facing * 2.0

    def parry_hit(self) -> None:
        """Absorb a projectile with the shield — start cooldown."""
        self._shield_cd = SHIELD_CD

    def spring_launch(self, vel_y: float) -> None:
        """Force a strong upward velocity (from a Spring) and refresh the air-jump."""
        self.vel_y       = vel_y
        self._jumps_left = 1
        self._jump_buffer = 0
        self._jump_cuttable = False

    def try_swing(self) -> bool:
        """Attempt a melee swing. Returns True if the swing started."""
        if self._swing_cooldown > 0:
            return False
        self._swing_cooldown = SWING_COOLDOWN
        self._swing_active   = 2   # hitbox is live for 2 frames
        self._swing_anim     = 9   # 3 animation frames × 3 ticks each
        get_audio().play_sfx("swing.wav")
        return True

    @property
    def swing_rect(self) -> "pygame.Rect | None":
        """Active melee hitbox in front of the player, or None if not swinging."""
        if self._swing_active <= 0:
            return None
        if self.facing > 0:
            return pygame.Rect(self.rect.right,       self.rect.top + 8, 20, 14)
        return     pygame.Rect(self.rect.left - 20,   self.rect.top + 8, 20, 14)

    def try_shoot(self) -> "projectile.Projectile | None":
        if self._shoot_cooldown > 0:
            return None
        self._shoot_cooldown = SHOOT_COOLDOWN
        from saruman.entities.projectile import Projectile
        px = float(self.rect.right if self.facing > 0 else self.rect.left - Projectile.W)
        py = float(self.rect.centery - 1)
        get_audio().play_sfx("shoot.wav")
        return Projectile(px, py, self.facing, self.weapon_level)

    def update(self, inp: Input, tilemap) -> None:
        if self._dying:
            if self._death_timer > 0:
                self._death_timer -= 1
            return          # freeze all movement/input during death

        if self._hit_timer      > 0: self._hit_timer      -= 1
        if self._bonus_invuln   > 0: self._bonus_invuln   -= 1
        if self._shoot_cooldown > 0: self._shoot_cooldown -= 1
        if self._swing_cooldown > 0: self._swing_cooldown -= 1
        if self._swing_active   > 0: self._swing_active   -= 1
        if self._swing_anim     > 0: self._swing_anim     -= 1
        if self._shield_cd      > 0: self._shield_cd      -= 1
        if self._wall_lock      > 0: self._wall_lock      -= 1
        self._shielding = inp.held(Action.SHIELD) and self._shield_cd <= 0

        # Horizontal movement — accelerate toward the target speed (halved while
        # shielding) instead of snapping to it, so running has weight.
        direction = 0
        if inp.held(Action.MOVE_LEFT):
            direction = -1
        elif inp.held(Action.MOVE_RIGHT):
            direction = 1
        if direction:
            self.facing = direction
        top_speed = MOVE_SPEED * 0.5 if self._shielding else MOVE_SPEED
        if self._wall_lock == 0:
            self._steer(direction * top_speed)

        if not self.on_ground:
            self._apply_jump_gravity(inp.held(Action.JUMP))

        # Wall slide: falling while pressing into a wall caps the fall speed.
        self._wall_sliding = (
            self._wall_dir != 0 and direction == self._wall_dir and self.vel_y > 0
        )
        if self._wall_sliding:
            self.vel_y = min(self.vel_y, WALL_SLIDE_SPEED)

        # Coyote time
        if self.on_ground:
            self._coyote_timer = COYOTE_FRAMES
            self._jumps_left   = 2
        elif self._coyote_timer > 0:
            self._coyote_timer -= 1

        # Jump buffer
        if inp.pressed(Action.JUMP):
            self._jump_buffer = JUMP_BUFFER_FRAMES
        elif self._jump_buffer > 0:
            self._jump_buffer -= 1

        if self._jump_buffer > 0 and self._coyote_timer > 0:
            self.vel_y         = JUMP_VEL
            self._coyote_timer = 0
            self._jump_buffer  = 0
            self._jumps_left   = 1
            self._jump_cuttable = True
            get_audio().play_sfx("jump.wav")
        elif inp.pressed(Action.JUMP) and not self.on_ground and self._wall_coyote > 0:
            self._wall_jump()
        elif inp.pressed(Action.JUMP) and not self.on_ground and self._jumps_left > 0:
            self.vel_y       = JUMP_VEL * 0.85
            self._jumps_left -= 1
            self._jump_cuttable = True
            get_audio().play_sfx("jump.wav")

        _was_on_ground = self.on_ground
        move_and_collide(self, tilemap)
        self._update_wall_contact(tilemap)
        if not _was_on_ground and self.on_ground:
            get_audio().play_sfx("land.wav")
            self._land_timer = 5
        if self._land_timer > 0:
            self._land_timer -= 1

        if self.vel_x != 0:
            self._anim_tick += 1
        else:
            self._anim_tick = 0
        self._idle_tick += 1

    @property
    def wall_sliding(self) -> bool:
        return self._wall_sliding

    def _wall_jump(self) -> None:
        """Kick off the last-touched wall, refreshing the double jump."""
        away = -self._wall_jump_dir
        self.vel_y          = WALL_JUMP_VEL_Y
        self.vel_x          = away * WALL_JUMP_PUSH
        self.facing         = away
        self._wall_lock     = WALL_JUMP_LOCK
        self._wall_coyote   = 0
        self._jumps_left    = 1
        self._jump_buffer   = 0
        self._jump_cuttable = True
        get_audio().play_sfx("jump.wav")

    def _update_wall_contact(self, tilemap) -> None:
        """Record which side (if any) is pressed against a solid tile while
        airborne. Probes 1 px beside the body, skipping the corners so floor
        and ceiling tiles don't count as walls."""
        self._wall_dir = 0
        if not self.on_ground:
            r = self.rect
            for side, px in ((-1, r.left - 1), (1, r.right)):
                tx = px // TILE_SIZE
                for py in (r.top + 3, r.centery, r.bottom - 3):
                    if tilemap.is_solid(tx, py // TILE_SIZE):
                        self._wall_dir = side
                        break
                if self._wall_dir:
                    break
        if self._wall_dir:
            self._wall_coyote   = WALL_COYOTE
            self._wall_jump_dir = self._wall_dir
        elif self._wall_coyote > 0:
            self._wall_coyote -= 1
        if self.on_ground:
            self._wall_coyote = 0

    def _steer(self, target: float) -> None:
        """Move vel_x toward `target` by the ground/air accel, decel or turn rate."""
        ground = self.on_ground
        if target == 0.0:
            rate = RUN_DECEL if ground else AIR_DECEL
        elif self.vel_x * target < 0:
            rate = RUN_TURN if ground else AIR_TURN
        elif abs(self.vel_x) > abs(target):
            # Above top speed (knockback, shield slowdown): bleed off gently.
            rate = RUN_DECEL if ground else AIR_DECEL
        else:
            rate = RUN_ACCEL if ground else AIR_ACCEL
        if self.vel_x < target:
            self.vel_x = min(self.vel_x + rate, target)
        else:
            self.vel_x = max(self.vel_x - rate, target)

    def _apply_jump_gravity(self, jump_held: bool) -> None:
        """Gravity shaped for a readable arc: lighter at the apex while jump is
        held, heavier after an early release and on the way down."""
        if self.vel_y < 0 and not jump_held and self._jump_cuttable:
            g = GRAVITY * JUMP_CUT_GRAVITY_MULT
        elif abs(self.vel_y) < APEX_HANG_SPEED and jump_held:
            g = GRAVITY * APEX_GRAVITY_MULT
        elif self.vel_y >= 0:
            g = GRAVITY_FALL
        else:
            g = GRAVITY
        self.vel_y = min(self.vel_y + g, PLAYER_MAX_FALL)

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        if self._hit_timer > 0 and (self._hit_timer // 4) % 2 == 1:
            return

        if self._dying:
            spr = self._hero_frame(_F_IDLE)
            if spr:
                frac  = self._death_timer / self._DEATH_FRAMES
                angle = (1.0 - frac) * 540.0
                scale = max(0.05, frac)
                spr   = pygame.transform.rotozoom(spr, angle, scale)
                bx    = sx + self.W // 2 - spr.get_width()  // 2
                by    = sy + self.H // 2 - spr.get_height() // 2
                surface.blit(spr, (bx, by))
            return

        spr = self._hero_frame(self._frame_index())
        if spr:
            # Feet on the hitbox bottom, body centred on the hitbox.
            cx = _HERO_CENTER_X if self.facing > 0 else _HERO_W - 1 - _HERO_CENTER_X
            bx = sx + self.W // 2 - cx
            by = sy + self.H - 1 - _HERO_FEET_Y
            surface.blit(spr, (bx, by))
        else:
            pygame.draw.rect(surface, COL_GOLD, (sx, sy, self.W, self.H))
            eye_x = sx + (8 if self.facing > 0 else 2)
            pygame.draw.rect(surface, COL_DARK_GRAY, (eye_x, sy + 4, 2, 2))

        if self._swing_anim and self._swing_anim <= 3:
            self._draw_slash(surface, sx, sy)

        # --- Shield overlay (drawn on top of body) ---
        if self._shielding:
            self._draw_shield(surface, sx, sy)

        # --- Bonus invulnerability aura (shield power-up) ---
        if self._bonus_invuln > 0:
            self._draw_bonus_aura(surface, sx, sy)

    def _hero_frame(self, index: int) -> "pygame.Surface | None":
        return get_strip_frame("hero", index, _HERO_W, _HERO_H, flip_x=(self.facing < 0))

    def _frame_index(self) -> int:
        """Pick the hero strip frame for the current state."""
        if self._swing_anim > 0:
            return _F_ATTACK + min(2, (9 - self._swing_anim) // 3)   # wind-up, swing, strike
        if self._wall_sliding:
            return _F_WALL
        if not self.on_ground:
            return _F_FALL if self.vel_y > 1.0 else _F_JUMP
        if abs(self.vel_x) > 0.3:
            return _F_WALK + (self._anim_tick // 5) % 6
        return _F_IDLE + (self._idle_tick // 14) % 4

    def _draw_slash(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        """Pale-blue magic arc in front of the staff on the strike frames."""
        r   = self.swing_rect
        if r is None:
            r = pygame.Rect(0, 0, 20, 14)
        w, h = 22, 22
        arc  = pygame.Surface((w, h), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, w, h)
        start, end = (-1.2, 1.2) if self.facing > 0 else (1.94, 4.34)
        pygame.draw.arc(arc, (110, 160, 230, 200), rect, start, end, 3)
        pygame.draw.arc(arc, (200, 235, 255, 255), rect.inflate(-4, -4), start, end, 1)
        ax = sx + self.W - 4 if self.facing > 0 else sx - w + 4
        surface.blit(arc, (ax, sy + 4))

    def _draw_bonus_aura(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        """Pulsing protective ring shown while the shield power-up is active."""
        pulse  = abs((self._bonus_invuln % 30) - 15)        # 0..15 triangle
        bright = 150 + pulse * 6                            # 150..240
        cx     = sx + self.W // 2
        cy     = sy + self.H // 2
        radius = max(self.W, self.H) // 2 + 3
        ring   = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(ring, (120, 190, 255, min(255, bright)),
                           (radius + 1, radius + 1), radius, 1)
        surface.blit(ring, (cx - radius - 1, cy - radius - 1))

    def _draw_shield(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        """Draw a small shield bar in front of the player while blocking."""
        # Pulsing brightness tied to _shield_cd (dims as cooldown ticks up after a hit)
        bright = max(80, 220 - self._shield_cd * 3)
        col_outer = (40,  bright // 2, bright)
        col_inner = (120, min(255, bright + 40), 255)

        if self.facing > 0:
            shx = sx + self.W + 1
        else:
            shx = sx - 4

        # Shield body — 3 px wide, 18 px tall, in front of the chest
        shy = sy + 6
        pygame.draw.rect(surface, col_outer, (shx, shy,     3, 18))
        pygame.draw.rect(surface, col_inner, (shx + 1, shy + 1, 1, 16))
