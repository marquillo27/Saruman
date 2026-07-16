from __future__ import annotations

import random

import pygame

from saruman.config import (
    BONUS_FRUIT_FRAMES, BONUS_SHIELD_FRAMES, BONUS_SPAWN_MAX, BONUS_SPAWN_MIN,
    COL_SKY_BOT, COL_SKY_TOP, INTERNAL_H, INTERNAL_W,
    MAX_LIVES, PLAYER_LIVES, STOMP_BOUNCE,
)
from saruman.core.assets import get_sprite
from saruman.core.audio import get_audio
from saruman.core.input import Action, Input
from saruman.entities.enemy import Enemy
from saruman.entities.interactive import Interactive, MovingPlatform, Spike, Spring
from saruman.entities.item import (
    Coin, FruitPickup, Gem, Heart, Item, NukePickup, ShieldPickup, WeaponUpgrade,
)
from saruman.entities.player import Player
from saruman.entities.projectile import EnemyProjectile, Projectile
from saruman.entities.trigger import LevelEndTrigger, Trigger, WarpTrigger
from saruman.physics.collision import platform_carry
from saruman.world.camera import Camera
from saruman.world.parallax import make_parallax_layers
from saruman.world.particle import AmbientParticle, Particle, burst
from saruman.world.tilemap import Tilemap
from saruman.world.weather import Weather

_COL_STOMP    = (255, 220,  60)   # yellow burst on stomp kill
_COL_HURT     = (255,  80,  80)   # red burst on enemy non-lethal hit
_COL_PLAYER_H = (220,  80,  80)   # red burst on player damage

_BIOME_SKY = {
    "level_01_greenshire_hills":   ((22, 35, 70),  (55, 90, 60)),
    "level_02_wolfwood":           (( 8, 10, 22),  (20, 24, 45)),
    "level_03_glass_caverns":      (( 8, 14, 22),  (18, 38, 48)),
    "level_04_sunken_mines":       ((14, 30, 40),  (34, 64, 46)),   # World I: green forest grotto
    "level_05_ash_marshes":        ((34, 12, 10),  (82, 30, 16)),   # World II: magma marsh (re-themed to fire)
    "level_06_pale_tower":         ((22, 28, 48),  (65, 72, 90)),
    "level_07_cursed_catacombs":   ((20, 30, 48),  (60, 80,110)),   # World III: frozen crypt (re-themed to ice)
    "level_08_forsaken_bridge":    ((28, 44, 70),  (110,150,195)),  # World III: icy chasm bridge (re-themed to ice)
    "level_09_skybound_spires":    ((60, 80,130),  (140,160,200)),  # pale sky
    "level_10_goblin_kings_throne": ((30, 14,  8),  (70, 30, 15)),  # hellish red
    "level_11_ashfall_wastes":      ((34, 28, 36),  (78, 64, 70)),   # ashen grey-violet
    "level_12_cinderwood_remains":  ((26, 18, 18),  (58, 38, 34)),   # smouldering brown-grey
    "level_13_emberfall_keep":      ((26, 40, 66),  (120,160,205)),  # World III: frozen keep (re-themed to ice)
}

_BIOME_AMBIENT = {
    "level_01_greenshire_hills":  ((200, 220,  80), "up",    8),
    "level_02_wolfwood":          ((130, 150, 220), "up",   10),
    "level_03_glass_caverns":     (( 60, 220, 200), "rand",  6),
    "level_04_sunken_mines":      ((150, 200, 110), "up",    9),   # green spores (re-themed)
    "level_05_ash_marshes":       ((255, 110,  30), "up",    8),   # magma embers (re-themed)
    "level_06_pale_tower":        ((220, 228, 242), "down",  7),
    "level_07_cursed_catacombs":  ((200, 220, 245), "down",  9),   # frost motes (re-themed to ice)
    "level_08_forsaken_bridge":   ((215, 232, 250), "down",  7),   # frost motes (re-themed to ice)
    "level_09_skybound_spires":   ((220, 230, 240), "down", 14),   # soft snow
    "level_10_goblin_kings_throne": ((255, 80, 30), "up",    8),   # fire embers up
    "level_11_ashfall_wastes":      ((190, 180, 175), "down", 6),  # falling grey ash
    "level_12_cinderwood_remains":  ((220, 110,  40), "up",   7),  # rising cinders
    "level_13_emberfall_keep":      ((220, 235, 255), "down", 6),  # frost motes (re-themed to ice)
}

_BIOME_WEATHER: dict[str, tuple[str, int] | None] = {
    "level_02_wolfwood":          ("rain",   30),   # light rain
    "level_05_ash_marshes":       ("embers", 55),   # World II: magma firefall (re-themed)
    "level_06_pale_tower":        ("snow",   45),
    "level_07_cursed_catacombs":  ("snow",   40),   # World III: frozen crypt (re-themed to ice)
    "level_08_forsaken_bridge":   ("snow",   45),   # World III: icy chasm bridge (re-themed to ice)
    "level_09_skybound_spires":   ("snow",   55),
    "level_10_goblin_kings_throne": ("embers", 50),
    "level_11_ashfall_wastes":      ("snow",   40),   # reuse snow as drifting ash
    "level_12_cinderwood_remains":  ("embers", 45),   # smoke and cinders
    "level_13_emberfall_keep":      ("snow",   55),   # World III: blizzard finale (re-themed to ice)
}


class World:
    _ENEMY_DEATH_FRAMES = 12

    def __init__(
        self,
        tilemap:      Tilemap,
        player_spawn: tuple[float, float],
        enemies:      list[Enemy],
        items:        list[Item],
        triggers:     list[Trigger],
        carry:        dict | None = None,
        level_name:   str = "",
        interactives: list[Interactive] | None = None,
    ) -> None:
        self._tilemap      = tilemap
        self._player       = Player(*player_spawn)
        self._camera       = Camera(tilemap.pixel_width, tilemap.pixel_height)
        self._enemies      = list(enemies)
        self._items        = list(items)
        self._interactives = list(interactives or [])
        self._triggers     = list(triggers)
        self._projectiles:       list[Projectile]            = []
        self._enemy_projectiles: list[EnemyProjectile]       = []
        self._particles:         list[Particle]              = []
        self._pending_spawns:    list[Enemy]                  = []

        if carry:
            self._lives               = carry.get("lives", PLAYER_LIVES)
            self._score               = carry.get("score", 0)
            self._player.weapon_level = carry.get("weapon_level", 0)
        else:
            self._lives = PLAYER_LIVES
            self._score = 0

        self._game_over           = False
        self._level_complete      = False
        self._warp_target: str | None = None
        self._damage_flash        = False
        self._nuke_flash          = False   # one-frame signal for PlayState screen shake
        self._hitstop             = 0
        self._fruit_timer         = 0       # >0 while enemies are harmless fruit
        self._bonus_timer         = random.randint(BONUS_SPAWN_MIN, BONUS_SPAWN_MAX)
        self._player_dying        = False
        self._player_was_grounded = True
        self._ambient_tick        = 0
        self._dying_enemies: list[tuple[Enemy, int, int]] = []
        self._ambient_cfg         = _BIOME_AMBIENT.get(level_name)
        sky_top, sky_bot          = _BIOME_SKY.get(level_name, (COL_SKY_TOP, COL_SKY_BOT))
        self._bg                  = self._make_sky(sky_top, sky_bot)
        self._parallax            = make_parallax_layers(level_name)
        weather_cfg               = _BIOME_WEATHER.get(level_name)
        self._weather: Weather | None = (
            Weather(weather_cfg[0], weather_cfg[1]) if weather_cfg else None
        )

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def player(self) -> Player:
        return self._player

    @property
    def lives(self) -> int:
        return self._lives

    @property
    def score(self) -> int:
        return self._score

    @property
    def is_game_over(self) -> bool:
        return self._game_over

    @property
    def is_level_complete(self) -> bool:
        return self._level_complete

    @property
    def warp_target(self) -> str | None:
        return self._warp_target

    @property
    def damage_flash(self) -> bool:
        return self._damage_flash

    @property
    def nuke_flash(self) -> bool:
        return self._nuke_flash

    def carry_state(self) -> dict[str, int]:
        return {
            "lives":        self._lives,
            "score":        self._score,
            "weapon_level": self._player.weapon_level,
        }

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, inp: Input, dt: float) -> None:
        self._damage_flash = False
        self._nuke_flash   = False

        # Tick the death animation; fire game-over only after it finishes.
        # Player.update() isn't called while dying, so decrement the timer here.
        if self._player_dying:
            if self._player._death_timer > 0:
                self._player._death_timer -= 1
            if self._player._death_timer <= 0:
                self._game_over    = True
                self._player_dying = False
            return

        if self._game_over or self._level_complete or self._warp_target:
            return

        if self._hitstop > 0:
            self._hitstop -= 1
            return          # freeze simulation; input preserved for next frame

        # Interactives tick first so MovingPlatform has fresh prev/curr positions
        for inter in self._interactives:
            inter.update(dt)

        self._player.update(inp, self._tilemap)
        self._player.x = max(
            0.0,
            min(self._player.x, self._tilemap.pixel_width - self._player.W)
        )

        # Moving platforms: carry the player if standing on one
        platforms = [i for i in self._interactives if isinstance(i, MovingPlatform)]
        if platforms:
            platform_carry(self._player, platforms)

        # Springs: launch player on top-overlap
        self._check_player_springs()

        if inp.pressed(Action.SHOOT):
            proj = self._player.try_shoot()
            if proj:
                self._projectiles.append(proj)

        if inp.pressed(Action.SWING):
            self._player.try_swing()

        for enemy in self._enemies:
            if enemy.alive:
                enemy.tick()
                enemy.update(self._tilemap, dt, self._player.rect)

        for proj in self._projectiles:
            if proj.alive:
                proj.update(self._tilemap)

        # Collect enemy shots fired this frame
        for enemy in self._enemies:
            if enemy.alive:
                shot = enemy.take_shot()
                if shot:
                    self._enemy_projectiles.append(shot)

        # Collect enemy-spawned minions (e.g. GoblinKing)
        for enemy in self._enemies:
            if enemy.alive:
                new_spawns = enemy.take_spawn()
                if new_spawns:
                    self._pending_spawns.extend(new_spawns)

        for ep in self._enemy_projectiles:
            if ep.alive:
                ep.update(self._tilemap)

        for item in self._items:
            item.update(dt)

        for particle in self._particles:
            particle.update()

        # Timed bonus state
        if self._fruit_timer > 0:
            self._fruit_timer -= 1
        self._bonus_timer -= 1
        if self._bonus_timer <= 0:
            self._spawn_bonus()
            self._bonus_timer = random.randint(BONUS_SPAWN_MIN, BONUS_SPAWN_MAX)

        self._check_player_spikes()
        self._check_player_enemy()
        self._check_projectile_enemy()
        self._check_melee_enemy()
        self._check_player_enemy_projectiles()
        self._check_player_items()
        self._check_player_triggers()

        # Merge any spawn-on-death children (e.g. Slime → 2× SmallSlime)
        if self._pending_spawns:
            self._enemies.extend(self._pending_spawns)
            self._pending_spawns.clear()

        self._enemies             = [e for e in self._enemies             if e.alive]
        self._projectiles         = [p for p in self._projectiles         if p.alive]
        self._enemy_projectiles   = [ep for ep in self._enemy_projectiles if ep.alive]
        self._items               = [i for i in self._items               if i.alive]
        self._interactives        = [i for i in self._interactives        if i.alive]
        self._particles           = [p for p in self._particles           if p.alive]
        self._dying_enemies = [
            (e, t - 1, mt) for e, t, mt in self._dying_enemies if t > 0
        ]

        if self._weather is not None:
            self._weather.update(dt)

        if self._player.y > self._tilemap.pixel_height + 32:
            self._apply_damage(ignore_shield=True)

        if not self._player_was_grounded and self._player.on_ground:
            cx = self._player.x + self._player.W / 2
            cy = self._player.y + self._player.H
            self._particles += burst(cx, cy, (160, 145, 120), count=6, speed=1.4)
        self._player_was_grounded = self._player.on_ground

        self._spawn_ambient()
        self._camera.follow(self._player.rect, dt)
        inp.clear_frame()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._bg, (0, 0))
        self._draw_parallax(surface)
        self._tilemap.draw(surface, self._camera.x, self._camera.y)

        for inter in self._interactives:
            r = inter.rect
            sx, sy = self._camera.world_to_screen(r.x, r.y)
            if -32 < sx < INTERNAL_W + 32:
                inter.draw(surface, sx, sy)

        for item in self._items:
            r = item.rect
            sx, sy = self._camera.world_to_screen(r.x, r.y)
            if -16 < sx < INTERNAL_W + 16:
                item.draw(surface, sx, sy)

        for enemy, timer, max_timer in self._dying_enemies:
            sx, sy = self._camera.world_to_screen(enemy.x, enemy.y)
            if -32 < sx < INTERNAL_W + 32:
                frac  = timer / max_timer
                new_w = int(enemy.w * (1.0 + (1.0 - frac) * 0.6))
                new_h = max(1, int(enemy.h * frac))
                rx    = sx + enemy.w // 2 - new_w // 2
                ry    = sy + enemy.h - new_h
                pygame.draw.rect(surface, (180, 80, 30), (rx, ry, new_w, new_h))

        fruit_spr = get_sprite("item_fruit") if self._fruit_timer > 0 else None
        for enemy in self._enemies:
            sx, sy = self._camera.world_to_screen(enemy.x, enemy.y)
            if not (-32 < sx < INTERNAL_W + 32):
                continue
            if self._fruit_timer > 0 and not enemy.is_boss:
                if fruit_spr:
                    fx = sx + (enemy.w - fruit_spr.get_width()) // 2
                    fy = sy + (enemy.h - fruit_spr.get_height()) // 2
                    surface.blit(fruit_spr, (fx, fy))
                else:
                    pygame.draw.circle(surface, (210, 50, 60),
                                       (sx + enemy.w // 2, sy + enemy.h // 2), 4)
            else:
                enemy.draw(surface, sx, sy)

        for proj in self._projectiles:
            sx, sy = self._camera.world_to_screen(proj.x, proj.y)
            if 0 <= sx <= INTERNAL_W:
                proj.draw(surface, sx, sy)

        for ep in self._enemy_projectiles:
            sx, sy = self._camera.world_to_screen(ep.x, ep.y)
            if 0 <= sx <= INTERNAL_W:
                ep.draw(surface, sx, sy)

        px, py = self._camera.world_to_screen(self._player.x, self._player.y)
        self._player.draw(surface, px, py)

        for particle in self._particles:
            sx, sy = self._camera.world_to_screen(int(particle.x), int(particle.y))
            if -4 < sx < INTERNAL_W + 4:
                particle.draw(surface, sx, sy)

        if self._weather is not None:
            self._weather.draw(surface)

    # ------------------------------------------------------------------
    # Collision helpers
    # ------------------------------------------------------------------

    def _kill_enemy(self, enemy: Enemy) -> None:
        """Mark enemy dead, queue on-kill spawns and item drops, register death animation."""
        enemy.alive = False
        spawns = enemy.on_kill_spawn()
        if spawns:
            self._pending_spawns.extend(spawns)
        drops = enemy.on_kill_drop()
        if drops:
            self._items.extend(drops)
        self._dying_enemies.append(
            (enemy, self._ENEMY_DEATH_FRAMES, self._ENEMY_DEATH_FRAMES)
        )

    def _check_player_enemy(self) -> None:
        pr = self._player.rect
        for enemy in self._enemies:
            if not enemy.alive or not pr.colliderect(enemy.rect):
                continue
            # Fruit bonus: non-boss enemies are harmless and edible on contact.
            if self._fruit_timer > 0 and not enemy.is_boss:
                self._vaporize_enemy(enemy)
                get_audio().play_sfx("coin.wav")
                continue
            if self._player.vel_y > 0 and pr.centery < enemy.rect.centery:
                if enemy.can_be_stomped:
                    killed = enemy.on_stomped()
                    self._hitstop = 4
                    cx = enemy.x + enemy.w / 2
                    cy = enemy.y + enemy.h / 2
                    if killed:
                        self._score += enemy.score_value
                        self._particles += burst(cx, cy, _COL_STOMP, count=12, speed=2.8)
                        get_audio().play_sfx("enemy_death.wav")
                        self._kill_enemy(enemy)
                    else:
                        self._particles += burst(cx, cy, _COL_HURT, count=6, speed=1.8)
                        get_audio().play_sfx("stomp.wav")
                        enemy.start_hit_flash(8)
                        enemy.apply_knockback(self._player.x)
                    self._player.vel_y = STOMP_BOUNCE
                else:
                    self._apply_damage()
            else:
                self._apply_damage()

    def _check_projectile_enemy(self) -> None:
        for proj in self._projectiles:
            if not proj.alive:
                continue
            for enemy in self._enemies:
                if enemy.alive and proj.rect.colliderect(enemy.rect):
                    killed = enemy.on_shot()
                    if killed:
                        self._score += enemy.score_value
                        cx = enemy.x + enemy.w / 2
                        cy = enemy.y + enemy.h / 2
                        self._particles += burst(cx, cy, _COL_STOMP, count=10, speed=2.2)
                        get_audio().play_sfx("enemy_death.wav")
                        self._kill_enemy(enemy)
                    else:
                        enemy.start_hit_flash(6)
                        enemy.apply_knockback(self._player.x)
                    proj.alive = False
                    break

    def _check_player_enemy_projectiles(self) -> None:
        pr = self._player.rect
        for ep in self._enemy_projectiles:
            if ep.alive and pr.colliderect(ep.rect):
                ep.alive = False
                if self._player.shielding:
                    self._player.parry_hit()
                    get_audio().play_sfx("shield_block.wav")
                else:
                    self._apply_damage()
                break   # one hit per frame

    def _check_player_items(self) -> None:
        pr = self._player.rect
        for item in self._items:
            if not item.alive or not pr.colliderect(item.rect):
                continue
            if isinstance(item, Coin):
                self._score += item.score_value
                get_audio().play_sfx("coin.wav")
            elif isinstance(item, Heart):
                self._lives = min(self._lives + 1, MAX_LIVES)
                get_audio().play_sfx("coin.wav")
            elif isinstance(item, WeaponUpgrade):
                self._player.weapon_level = min(self._player.weapon_level + 1, 1)
            elif isinstance(item, Gem):
                self._score += item.score_value
                get_audio().play_sfx("coin.wav")
            elif isinstance(item, ShieldPickup):
                self._player.grant_invuln(BONUS_SHIELD_FRAMES)
                get_audio().play_sfx("shield_block.wav")
            elif isinstance(item, NukePickup):
                self._detonate_nuke()
            elif isinstance(item, FruitPickup):
                self._fruit_timer = BONUS_FRUIT_FRAMES
                get_audio().play_sfx("coin.wav")
            item.alive = False

    def _check_player_springs(self) -> None:
        """Activate Spring entities the player landed on this frame."""
        for inter in self._interactives:
            if isinstance(inter, Spring) and inter.player_overlap_from_above(self._player):
                inter.trigger()
                self._player.spring_launch(Spring.LAUNCH_VEL_Y)
                get_audio().play_sfx("jump.wav")

    def _check_player_spikes(self) -> None:
        """Damage the player if they touch any Spike (runs outside hitstop guard)."""
        pr = self._player.rect
        for inter in self._interactives:
            if isinstance(inter, Spike) and pr.colliderect(inter.rect):
                self._apply_damage()
                return   # one damage event per frame maximum

    def _check_melee_enemy(self) -> None:
        """Resolve player sword-swing vs. enemy collisions."""
        sr = self._player.swing_rect
        if sr is None:
            return
        for enemy in list(self._enemies):
            if not enemy.alive or not sr.colliderect(enemy.rect):
                continue
            killed = enemy.on_melee()
            cx = enemy.x + enemy.w / 2
            cy = enemy.y + enemy.h / 2
            if killed:
                self._score   += enemy.score_value
                self._hitstop  = 6
                self._particles += burst(cx, cy, (220, 220, 80), count=14, speed=3.0)
                get_audio().play_sfx("enemy_death.wav")
                self._kill_enemy(enemy)
            else:
                enemy.start_hit_flash(6)
                enemy.apply_knockback(self._player.x)
                self._hitstop = 4
            break   # one enemy contact per swing frame

    def _check_player_triggers(self) -> None:
        pr = self._player.rect
        for trigger in self._triggers:
            if trigger.triggered or not pr.colliderect(trigger.rect):
                continue
            trigger.triggered = True
            if isinstance(trigger, WarpTrigger):
                self._warp_target = trigger.target_level
            elif isinstance(trigger, LevelEndTrigger):
                self._score += trigger.score_bonus
                self._level_complete = True

    def _apply_damage(self, ignore_shield: bool = False) -> None:
        # `ignore_shield` (e.g. falling out of the world) bypasses the 10 s bonus
        # shield but still respects the brief post-hit i-frames, so a single fall
        # can't drain every life at once.
        blocked = self._player.hit_invincible if ignore_shield else self._player.invincible
        if blocked:
            return
        self._player.take_damage()
        self._lives -= 1
        self._damage_flash = True
        get_audio().play_sfx("hit.wav")
        cx = self._player.x + self._player.W / 2
        cy = self._player.y + self._player.H / 2
        self._particles += burst(cx, cy, _COL_PLAYER_H, count=8, speed=2.0)
        if self._lives <= 0:
            self._player.trigger_death()
            self._player_dying = True

    # ------------------------------------------------------------------
    # Bonus power-ups
    # ------------------------------------------------------------------

    def _spawn_bonus(self) -> None:
        """Drop one random bonus pickup just ahead of the player."""
        cls    = random.choice((ShieldPickup, NukePickup, FruitPickup))
        facing = self._player.facing or 1
        bx     = self._player.x + 60 * facing
        bx     = max(8.0, min(bx, self._tilemap.pixel_width - 16.0))
        by     = max(8.0, self._player.y - 4.0)
        self._items.append(cls(bx, by))

    def _vaporize_enemy(self, enemy: Enemy) -> None:
        """Instantly destroy a non-boss enemy for score, with death animation but
        no on-kill spawns/drops (used by the nuke and by fruit-eating)."""
        enemy.alive   = False
        self._score  += enemy.score_value
        cx = enemy.x + enemy.w / 2
        cy = enemy.y + enemy.h / 2
        self._particles += burst(cx, cy, _COL_STOMP, count=10, speed=2.4)
        self._dying_enemies.append(
            (enemy, self._ENEMY_DEATH_FRAMES, self._ENEMY_DEATH_FRAMES)
        )

    def _detonate_nuke(self) -> None:
        """Wipe every living non-boss enemy on the level. Bosses are immune."""
        self._nuke_flash = True
        get_audio().play_sfx("enemy_death.wav")
        for enemy in self._enemies:
            if enemy.alive and not enemy.is_boss:
                self._vaporize_enemy(enemy)

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------

    def _make_sky(self, top=COL_SKY_TOP, bot=COL_SKY_BOT) -> pygame.Surface:
        surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
        for y in range(INTERNAL_H):
            t = y / INTERNAL_H
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (INTERNAL_W, y))
        return surf

    def _spawn_ambient(self) -> None:
        if not self._ambient_cfg:
            return
        col, direction, interval = self._ambient_cfg
        self._ambient_tick += 1
        if self._ambient_tick < interval:
            return
        self._ambient_tick = 0

        x = self._camera.x + random.randint(0, INTERNAL_W)
        y = self._camera.y + random.randint(10, INTERNAL_H - 10)

        if direction == "up":
            vx = random.uniform(-0.3, 0.3)
            vy = -random.uniform(0.2, 0.5)
        elif direction == "down":
            vx = random.uniform(-0.2, 0.2)
            vy =  random.uniform(0.2, 0.6)
        else:   # "side" or "rand"
            vx = random.uniform(-0.4, 0.4)
            vy = random.uniform(-0.2, 0.2)

        life = random.randint(25, 50)
        self._particles.append(AmbientParticle(x, y, vx, vy, col, life))

    def _draw_parallax(self, surface: pygame.Surface) -> None:
        for layer in self._parallax:
            layer.draw(surface, self._camera.x)
