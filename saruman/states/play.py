from __future__ import annotations

from pathlib import Path

import pygame

from saruman.config import INTERNAL_H, INTERNAL_W
from saruman.core.audio import get_audio
from saruman.core.input import Input
from saruman.core.state import State
from saruman.paths import asset_path
from saruman.ui.hud import HUD
from saruman.world.level_loader import load_level
from saruman.world.world import World


_BIOME_GRADE = {
    "level_01_greenshire_hills": (10, 30,  5, 20),
    "level_02_wolfwood":         ( 0,  5, 20, 25),
    "level_03_glass_caverns":    ( 0, 20, 25, 22),
    "level_04_sunken_mines":     (10, 28,  8, 20),   # World I: green forest grotto (re-themed)
    "level_05_ash_marshes":      (28,  8,  2, 22),   # World II: magma tint (re-themed)
    "level_06_pale_tower":       ( 5, 10, 20, 18),
    "level_07_cursed_catacombs": ( 8, 18, 32, 22),   # World III: icy-blue tint (re-themed to ice)
    "level_08_forsaken_bridge":     ( 8, 18, 30, 20),   # World III: icy-blue tint (re-themed to ice)
    "level_09_skybound_spires":     (10, 15, 25, 15),   # cool sky tint
    "level_10_goblin_kings_throne": (25,  5,  0, 22),   # hot red tint
    "level_11_ashfall_wastes":      (15, 12, 18, 24),   # desaturated ashen tint
    "level_12_cinderwood_remains":  (28, 12,  6, 22),   # charred warm-brown tint
    "level_13_emberfall_keep":      ( 8, 18, 32, 22),   # World III: icy-blue tint (re-themed)
}


class PlayState(State):
    _DMG_FLASH_FRAMES = 9

    def __init__(
        self,
        game,
        level_path: Path | None = None,
        carry: dict | None = None,
    ) -> None:
        self._game  = game
        self._input = Input()
        self._hud   = HUD()

        if level_path is None:
            level_path = asset_path("maps", "level_01_greenshire_hills.tmx")
        self._level_path = level_path

        tilemap, spawn, enemies, items, interactives, triggers = load_level(level_path)
        self._world = World(
            tilemap, spawn, enemies, items, triggers, carry,
            level_name=level_path.stem,
            interactives=interactives,
        )

        self._red_flash   = 0
        self._dmg_overlay = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self._dmg_overlay.fill((200, 30, 30))

        gr, gg, gb, ga = _BIOME_GRADE.get(level_path.stem, (0, 0, 0, 0))
        self._grade_overlay = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self._grade_overlay.fill((gr, gg, gb))
        self._grade_overlay.set_alpha(ga)

    # ------------------------------------------------------------------

    _LEVEL_MUSIC = {
        "level_01_greenshire_hills": "greenshire.wav",
        "level_02_wolfwood":         "wolfwood.wav",
        "level_03_glass_caverns":    "caverns.wav",
        "level_04_sunken_mines":     "mines.wav",
        "level_05_ash_marshes":      "marshes.wav",
        "level_06_pale_tower":       "tower.wav",
        "level_07_cursed_catacombs": "tower.wav",     # reuse atmospheric track
        "level_08_forsaken_bridge":     "tower.wav",       # World III: cold atmospheric reuse
        "level_09_skybound_spires":     "greenshire.wav",  # reuse uplifting track
        "level_10_goblin_kings_throne": "tower.wav",       # ominous final boss
        "level_11_ashfall_wastes":      "marshes.wav",     # bleak desolate track
        "level_12_cinderwood_remains":  "wolfwood.wav",    # dead-forest reuse
        "level_13_emberfall_keep":      "tower.wav",       # final-boss reprise
    }

    # Campaign restructured into 3 worlds (3 + 4 + 5), each ending in a boss.
    #   World I  — Greenwood  (green):  greenshire → wolfwood → sunken_mines[BossWarg]
    #   World II — Scorchlands (fire):  ashfall → cinderwood → ash_marshes → throne[GoblinKing]
    #   World III— Frozen North (ice):  pale_tower → skybound → bridge → catacombs → emberfall[NightKing]
    # Secret: glass_caverns (warp) rejoins the main chain at sunken_mines.
    _NEXT_LEVEL = {
        # --- World I: Greenwood ---
        "level_01_greenshire_hills":    "level_02_wolfwood",
        "level_02_wolfwood":            "level_04_sunken_mines",
        "level_03_glass_caverns":       "level_04_sunken_mines",   # secret rejoins World I
        "level_04_sunken_mines":        "level_11_ashfall_wastes",  # World I boss → World II
        # --- World II: Scorchlands ---
        "level_11_ashfall_wastes":      "level_12_cinderwood_remains",
        "level_12_cinderwood_remains":  "level_05_ash_marshes",
        "level_05_ash_marshes":         "level_10_goblin_kings_throne",  # World II boss
        "level_10_goblin_kings_throne": "level_06_pale_tower",      # World II boss → World III
        # --- World III: Frozen North ---
        "level_06_pale_tower":          "level_09_skybound_spires",
        "level_09_skybound_spires":     "level_08_forsaken_bridge",
        "level_08_forsaken_bridge":     "level_07_cursed_catacombs",
        "level_07_cursed_catacombs":    "level_13_emberfall_keep",  # World III boss (NightKing)
        # level_13_emberfall_keep absent → triggers win screen (campaign finale)
    }

    def on_enter(self) -> None:
        track = self._LEVEL_MUSIC.get(self._level_path.stem)
        if track:
            get_audio().play_music(track)
        else:
            get_audio().stop_music()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from saruman.states.pause import PauseState
            self._game.states.push(PauseState(self._game))
            return
        self._input.handle_event(event)

    def update(self, dt: float) -> None:
        self._world.update(self._input, dt)

        if self._world.damage_flash:
            self._game.shake(10)
            self._red_flash = self._DMG_FLASH_FRAMES

        if self._world.nuke_flash:
            self._game.shake(14)

        if self._red_flash > 0:
            self._red_flash -= 1

        if self._world.is_game_over:
            from saruman.states.gameover import GameOverState
            self._game.states.replace(GameOverState(self._game, self._world.score))
            return

        if self._world.warp_target:
            self._start_warp(self._world.warp_target)
            return

        if self._world.is_level_complete:
            self._start_level_complete()

    def draw(self, surface: pygame.Surface) -> None:
        self._world.draw(surface)
        surface.blit(self._grade_overlay, (0, 0))

        if self._red_flash > 0:
            self._dmg_overlay.set_alpha(self._red_flash * 18)
            surface.blit(self._dmg_overlay, (0, 0))

        self._hud.draw(
            surface,
            self._world.lives,
            self._world.score,
            self._world.player.weapon_level,
        )

    # ------------------------------------------------------------------

    def _start_warp(self, target_level: str) -> None:
        from saruman.states.secret import SecretState
        carry       = self._world.carry_state()
        target_path = asset_path("maps", f"{target_level}.tmx")

        def factory():
            return PlayState(self._game, target_path, carry)

        self._game.states.replace(SecretState(self._game, factory))

    def _start_level_complete(self) -> None:
        from saruman.states.transition import TransitionState
        from saruman.states.worldcard import WORLDS, WorldCardState

        score = self._world.score
        nxt   = self._NEXT_LEVEL.get(self._level_path.stem)

        if nxt:
            carry       = self._world.carry_state()
            target_path = asset_path("maps", f"{nxt}.tmx")

            def play_factory():
                return PlayState(self._game, target_path, carry)

            if nxt in WORLDS:
                def factory():
                    return WorldCardState(self._game, nxt, play_factory)
            else:
                factory = play_factory
        else:
            def factory():
                from saruman.states.credits import CreditsState
                return CreditsState(self._game, score)

        self._game.states.replace(TransitionState(self._game, factory))
