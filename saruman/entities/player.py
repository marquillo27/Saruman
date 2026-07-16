from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from saruman.config import (
    COYOTE_FRAMES, JUMP_BUFFER_FRAMES, JUMP_VEL, MOVE_SPEED,
    COL_GOLD, COL_DARK_GRAY, HIT_IFRAMES, SHOOT_COOLDOWN, SWING_COOLDOWN, SHIELD_CD,
)
from saruman.core.assets import get_sprite, get_strip_frame
from saruman.core.audio import get_audio
from saruman.core.input import Action, Input
from saruman.entities.entity import Entity
from saruman.physics.collision import move_and_collide

if TYPE_CHECKING:
    from saruman.entities.projectile import Projectile


class Player(Entity):
    W = 10
    H = 16
    _DEATH_FRAMES = 35

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, self.W, self.H)
        self._coyote_timer   = 0
        self._jump_buffer    = 0
        self._jumps_left     = 2
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
            return pygame.Rect(self.rect.right,       self.rect.top + 4, 16, 10)
        return     pygame.Rect(self.rect.left - 16,   self.rect.top + 4, 16, 10)

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
        self._shielding = inp.held(Action.SHIELD) and self._shield_cd <= 0

        # Horizontal movement — halved while shielding
        _spd = MOVE_SPEED * 0.5 if self._shielding else MOVE_SPEED
        if inp.held(Action.MOVE_LEFT):
            self.vel_x = -_spd
            self.facing = -1
        elif inp.held(Action.MOVE_RIGHT):
            self.vel_x = _spd
            self.facing = 1
        else:
            self.vel_x = 0.0

        if not self.on_ground:
            self.apply_gravity()

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
            get_audio().play_sfx("jump.wav")
        elif inp.pressed(Action.JUMP) and not self.on_ground and self._jumps_left > 0:
            self.vel_y       = JUMP_VEL * 0.85
            self._jumps_left -= 1
            get_audio().play_sfx("jump.wav")

        if inp.released(Action.JUMP) and self.vel_y < 0:
            self.vel_y *= 0.5

        _was_on_ground = self.on_ground
        move_and_collide(self, tilemap)
        if not _was_on_ground and self.on_ground:
            get_audio().play_sfx("land.wav")
            self._land_timer = 5
        if self._land_timer > 0:
            self._land_timer -= 1

        if self.vel_x != 0:
            self._anim_tick += 1
        else:
            self._anim_tick = 0

    def draw(self, surface: pygame.Surface, sx: int, sy: int) -> None:
        if self._hit_timer > 0 and (self._hit_timer // 4) % 2 == 1:
            return

        if self._dying:
            spr = get_strip_frame("player", 0, 12, 18, flip_x=(self.facing < 0))
            if spr:
                frac  = self._death_timer / self._DEATH_FRAMES
                angle = (1.0 - frac) * 540.0
                scale = max(0.05, frac)
                spr   = pygame.transform.rotozoom(spr, angle, scale)
                bx    = sx + self.W // 2 - spr.get_width()  // 2
                by    = sy + self.H // 2 - spr.get_height() // 2
                surface.blit(spr, (bx, by))
            return

        # --- Melee attack animation ---
        if self._swing_anim > 0:
            anim_frame = (9 - self._swing_anim) // 3   # 0=raise, 1=extend, 2=follow
            spr = get_strip_frame("player_attack", anim_frame, 12, 18,
                                  flip_x=(self.facing < 0))
            if spr:
                bx = sx - (spr.get_width()  - self.W) // 2
                by = sy - (spr.get_height() - self.H) // 2
                if self.facing < 0:
                    bx = sx - (spr.get_width() - self.W) // 2
                surface.blit(spr, (bx, by))
            else:
                # Fallback: flash gold
                pygame.draw.rect(surface, COL_GOLD, (sx, sy, self.W, self.H))
            return   # skip normal body while mid-swing

        # --- Normal body ---
        if not self.on_ground:
            frame = 5 if self.vel_y > 3 else 4   # F5=falling, F4=jumping/floating
        else:
            frame = (self._anim_tick // 6) % 4   # F0-F3 walk cycle
        spr = get_strip_frame("player", frame, 12, 18, flip_x=(self.facing < 0))
        if spr:
            bx = sx - (spr.get_width()  - self.W) // 2
            by = sy - (spr.get_height() - self.H) // 2
            sw, sh = spr.get_size()
            if not self.on_ground and self.vel_y < -3:
                # Rising — stretch tall, anchor at feet
                spr = pygame.transform.scale(spr, (sw - 1, sh + 2))
                by -= 2
            elif not self.on_ground and self.vel_y > 5:
                # Falling fast — stretch tall, anchor at head
                spr = pygame.transform.scale(spr, (sw - 1, sh + 3))
            elif self._land_timer > 0:
                # Landing squash — wider+shorter, anchor at feet
                frac    = self._land_timer / 5.0
                extra_w = int(3 * frac)
                extra_h = int(2 * frac)
                spr = pygame.transform.scale(spr, (sw + extra_w, sh - extra_h))
                bx -= extra_w // 2
                by += extra_h
            surface.blit(spr, (bx, by))
        else:
            pygame.draw.rect(surface, COL_GOLD, (sx, sy, self.W, self.H))
            eye_x = sx + (6 if self.facing > 0 else 2)
            pygame.draw.rect(surface, COL_DARK_GRAY, (eye_x, sy + 4, 2, 2))

        # --- Shield overlay (drawn on top of body) ---
        if self._shielding:
            self._draw_shield(surface, sx, sy)

        # --- Bonus invulnerability aura (shield power-up) ---
        if self._bonus_invuln > 0:
            self._draw_bonus_aura(surface, sx, sy)

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

        # Shield body — 3 px wide, 12 px tall, centred on the player sprite
        shy = sy + 2
        pygame.draw.rect(surface, col_outer, (shx, shy,     3, 12))
        pygame.draw.rect(surface, col_inner, (shx + 1, shy + 1, 1, 10))
