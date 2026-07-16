from __future__ import annotations

import math

import pygame

from saruman.config import INTERNAL_H, INTERNAL_W

_COLORKEY = (255, 0, 255)


class ParallaxLayer:
    def __init__(self, surface: pygame.Surface, scroll_factor: float) -> None:
        self._surf   = surface
        self._factor = scroll_factor

    def draw(self, target: pygame.Surface, camera_x: float) -> None:
        w      = self._surf.get_width()
        offset = int(camera_x * self._factor) % w
        target.blit(self._surf, (-offset, 0))
        if offset > 0:
            target.blit(self._surf, (w - offset, 0))


def _surf() -> pygame.Surface:
    s = pygame.Surface((INTERNAL_W, INTERNAL_H))
    s.fill(_COLORKEY)
    s.set_colorkey(_COLORKEY)
    return s


# ---------------------------------------------------------------------------
# Biome silhouette factories
# ---------------------------------------------------------------------------

def _greenshire_far() -> pygame.Surface:
    s = _surf()
    col = (45, 90, 55)
    pts = [(0, INTERNAL_H)]
    for x in range(INTERNAL_W + 1):
        y = 130 - int(18 * math.sin(x * 2 * math.pi / INTERNAL_W * 4))
        pts.append((x, y))
    pts.append((INTERNAL_W, INTERNAL_H))
    pygame.draw.polygon(s, col, pts)
    return s


def _greenshire_mid() -> pygame.Surface:
    s = _surf()
    col = (28, 68, 38)
    for tx in range(0, INTERNAL_W, 28):
        pygame.draw.rect(s, col, (tx + 11, 148, 6, 16))
        pygame.draw.circle(s, col, (tx + 14, 141), 11)
    return s


def _wolfwood_far() -> pygame.Surface:
    s = _surf()
    col = (22, 28, 52)
    period = 55
    for i in range(-1, INTERNAL_W // period + 3):
        bx     = i * period
        peak_y = 55 + (i % 5) * 10
        pygame.draw.polygon(s, col, [
            (bx - 24, 108), (bx, peak_y), (bx + 24, 108),
        ])
    return s


def _wolfwood_mid() -> pygame.Surface:
    s = _surf()
    col = (16, 36, 20)
    period = 30
    for i in range(-1, INTERNAL_W // period + 3):
        bx = i * period
        pygame.draw.rect(s, col, (bx - 2, 126, 4, 16))
        pygame.draw.polygon(s, col, [
            (bx - 8, 126), (bx, 108), (bx + 8, 126),
        ])
    return s


def _mines_far() -> pygame.Surface:
    s = _surf()
    col = (25, 22, 30)
    pygame.draw.rect(s, col, (0, 0, INTERNAL_W, 30))
    for tx in range(0, INTERNAL_W, 22):
        h = 20 + (tx % 4) * 8
        pygame.draw.polygon(s, col, [(tx, 30), (tx + 11, 30 + h), (tx + 22, 30)])
    return s


def _mines_mid() -> pygame.Surface:
    s = _surf()
    col = (35, 30, 40)
    for tx in range(0, INTERNAL_W, 16):
        h = 12 + (tx % 3) * 6
        pygame.draw.polygon(s, col, [
            (tx, INTERNAL_H), (tx + 8, INTERNAL_H - h), (tx + 16, INTERNAL_H),
        ])
    return s


def _marshes_far() -> pygame.Surface:
    s = _surf()
    col = (28, 24, 32)
    for tx in range(0, INTERNAL_W, 36):
        h = 30 + (tx % 5) * 8
        pygame.draw.rect(s, col, (tx + 14, INTERNAL_H - h, 8, h))
        pygame.draw.line(s, col, (tx + 18, INTERNAL_H - h + 10), (tx + 30, INTERNAL_H - h), 2)
        pygame.draw.line(s, col, (tx + 18, INTERNAL_H - h + 10), (tx + 4,  INTERNAL_H - h - 4), 2)
    return s


def _marshes_mid() -> pygame.Surface:
    s = _surf()
    col = (20, 18, 25)
    for tx in range(0, INTERNAL_W, 48):
        pygame.draw.line(s, col, (tx,      20), (tx + 32, 40), 2)
        pygame.draw.line(s, col, (tx + 8,  10), (tx + 40, 30), 2)
        pygame.draw.line(s, col, (tx + 16, 28), (tx + 24, 16), 1)
        pygame.draw.line(s, col, (tx + 28, 36), (tx + 20, 22), 1)
    return s


def _tower_far() -> pygame.Surface:
    s = _surf()
    col = (30, 28, 45)
    for tx in range(0, INTERNAL_W, 80):
        pygame.draw.rect(s, col, (tx + 30, 60, 20, 80))
        for bx in range(tx + 30, tx + 50, 6):
            pygame.draw.rect(s, col, (bx, 54, 4, 8))
        pygame.draw.rect(s, col, (tx + 8, 80, 14, 60))
        for bx in range(tx + 8, tx + 22, 6):
            pygame.draw.rect(s, col, (bx, 74, 4, 8))
    return s


def _tower_mid() -> pygame.Surface:
    s = _surf()
    col = (40, 38, 55)
    for tx in range(0, INTERNAL_W, 64):
        pygame.draw.rect(s, col, (tx, 120, 48, INTERNAL_H - 120))
        for bx in range(tx, tx + 48, 8):
            pygame.draw.rect(s, col, (bx, 112, 6, 10))
    return s


def _catacombs_far() -> pygame.Surface:
    """Distant arched pillars — dark stone silhouettes."""
    s = _surf()
    col = (20, 16, 28)
    # Draw periodic arch + pillar shapes
    for tx in range(0, INTERNAL_W, 48):
        # Pillar pair
        pygame.draw.rect(s, col, (tx,      80, 8, INTERNAL_H - 80))
        pygame.draw.rect(s, col, (tx + 38, 80, 8, INTERNAL_H - 80))
        # Arch keystone
        pygame.draw.rect(s, col, (tx + 4,  72, 36, 10))
        pygame.draw.rect(s, col, (tx + 10, 66, 24, 8))
        pygame.draw.rect(s, col, (tx + 16, 62, 12, 6))
    return s


def _catacombs_mid() -> pygame.Surface:
    """Closer crumbling stone blocks along the floor and ceiling."""
    s = _surf()
    col = (30, 24, 38)
    # Floor rubble blocks
    for tx in range(0, INTERNAL_W, 28):
        h = 8 + (tx % 3) * 4
        pygame.draw.rect(s, col, (tx, INTERNAL_H - h, 26, h))
    # Ceiling stalactites
    for tx in range(0, INTERNAL_W, 22):
        h = 6 + (tx % 4) * 3
        pygame.draw.rect(s, col, (tx + 6, 0, 10, h))
    return s


def _bridge_far() -> pygame.Surface:
    """Far broken arches across a desert canyon — warm rust silhouettes."""
    s = _surf()
    col = (60, 38, 36)
    # Distant cliff tops
    for tx in range(0, INTERNAL_W, 38):
        h = 28 + (tx % 5) * 6
        pygame.draw.rect(s, col, (tx, INTERNAL_H - 80, 38, h))
    # Broken bridge arches further back
    arch_col = (75, 48, 42)
    for tx in range(0, INTERNAL_W, 70):
        bx = tx + 6
        pygame.draw.rect(s, arch_col, (bx,      90, 6, 38))
        pygame.draw.rect(s, arch_col, (bx + 38, 90, 6, 38))
        pygame.draw.rect(s, arch_col, (bx + 2,  86, 42, 6))
    return s


def _bridge_mid() -> pygame.Surface:
    """Mid-distance ropes, planks, and ruined pillars."""
    s = _surf()
    col = (90, 60, 50)
    rope = (110, 78, 55)
    for tx in range(0, INTERNAL_W, 32):
        # Snapped pillar
        pygame.draw.rect(s, col, (tx + 8, 120, 8, INTERNAL_H - 120))
        pygame.draw.rect(s, col, (tx + 6, 116, 12, 6))
        # Sagging rope between pillars
        for px in range(tx + 16, tx + 32):
            sag = int(2 * math.sin((px - tx) * math.pi / 16))
            pygame.draw.rect(s, rope, (px, 118 + sag, 1, 1))
    return s


def _spires_far() -> pygame.Surface:
    """Far distant snow-capped peaks against pale sky."""
    s = _surf()
    rock = (70, 90, 130)
    snow = (210, 220, 240)
    for tx in range(0, INTERNAL_W, 56):
        base_y = INTERNAL_H - 20
        peak_y = 40 + (tx % 4) * 6
        pygame.draw.polygon(s, rock, [
            (tx - 8, base_y), (tx + 28, peak_y), (tx + 64, base_y),
        ])
        # Snow cap
        pygame.draw.polygon(s, snow, [
            (tx + 18, peak_y + 12),
            (tx + 28, peak_y),
            (tx + 38, peak_y + 12),
        ])
    return s


def _spires_mid() -> pygame.Surface:
    """Mid cloud bands drifting across the sky."""
    s = _surf()
    cloud = (200, 215, 235)
    for tx in range(0, INTERNAL_W, 64):
        y = 40 + (tx % 3) * 18
        pygame.draw.rect(s, cloud, (tx,      y,     46, 6))
        pygame.draw.rect(s, cloud, (tx + 6,  y - 3, 32, 4))
        pygame.draw.rect(s, cloud, (tx + 4,  y + 6, 38, 4))
    # Closer spires near bottom
    spire = (60, 78, 110)
    for tx in range(0, INTERNAL_W, 80):
        pygame.draw.polygon(s, spire, [
            (tx + 6, INTERNAL_H), (tx + 22, 110), (tx + 38, INTERNAL_H),
        ])
    return s


def _throne_far() -> pygame.Surface:
    """Far crumbling gothic columns with lava glow — dark reds and oranges."""
    s = _surf()
    col_stone = (60, 28, 18)
    col_lava   = (180, 60, 10)
    # Gothic pillars with crumbled tops
    for tx in range(0, INTERNAL_W, 60):
        h = 70 + (tx % 4) * 12
        pygame.draw.rect(s, col_stone, (tx + 22, INTERNAL_H - h, 16, h))
        # Crumble notches at top
        pygame.draw.rect(s, col_stone, (tx + 18, INTERNAL_H - h, 8, 8))
        pygame.draw.rect(s, col_stone, (tx + 30, INTERNAL_H - h - 4, 8, 8))
        # Arch span
        pygame.draw.rect(s, col_stone, (tx + 10, INTERNAL_H - h + 4, 40, 6))
    # Lava glow along the bottom third
    for y in range(INTERNAL_H - 50, INTERNAL_H):
        intensity = int(60 * (y - (INTERNAL_H - 50)) / 50)
        pygame.draw.line(s, (intensity, intensity // 3, 0),
                         (0, y), (INTERNAL_W, y))
    # Lava pools — bright orange blobs
    for tx in range(0, INTERNAL_W, 44):
        pygame.draw.ellipse(s, col_lava, (tx + 8, INTERNAL_H - 14, 28, 8))
    return s


def _throne_mid() -> pygame.Surface:
    """Mid-distance torch sconces with flickering smoke wisps."""
    s = _surf()
    col_wall  = (80, 38, 22)
    col_torch = (220, 110, 30)
    col_smoke = (160, 80, 40)
    # Stone wall slabs
    for tx in range(0, INTERNAL_W, 20):
        pygame.draw.rect(s, col_wall, (tx, 100, 18, INTERNAL_H - 100))
        # Mortar joints
        for ty in range(100, INTERNAL_H, 12):
            pygame.draw.line(s, (50, 22, 12), (tx, ty), (tx + 18, ty))
    # Torch sconces
    for tx in range(10, INTERNAL_W, 40):
        # Bracket
        pygame.draw.rect(s, (100, 50, 20), (tx, 95, 4, 10))
        # Flame
        pygame.draw.rect(s, col_torch, (tx - 2, 88, 8, 8))
        pygame.draw.rect(s, (255, 200, 80), (tx, 90, 4, 4))
        # Smoke wisps above
        for i in range(3):
            wy = 86 - i * 4
            pygame.draw.rect(s, col_smoke, (tx + (i % 2), wy, 2, 3))
    return s


def _ashfall_far() -> pygame.Surface:
    """Far rolling ash dunes under a pale, dust-choked sky — muted grey-violet."""
    s = _surf()
    col = (52, 46, 56)
    pts = [(0, INTERNAL_H)]
    for x in range(INTERNAL_W + 1):
        y = 120 - int(10 * math.sin(x * 2 * math.pi / INTERNAL_W * 3)) \
                - int(5 * math.sin(x * 2 * math.pi / INTERNAL_W * 7))
        pts.append((x, y))
    pts.append((INTERNAL_W, INTERNAL_H))
    pygame.draw.polygon(s, col, pts)
    # Faint distant ash plumes
    plume = (64, 56, 66)
    for tx in range(0, INTERNAL_W, 70):
        pygame.draw.ellipse(s, plume, (tx + 20, 70, 30, 16))
    return s


def _ashfall_mid() -> pygame.Surface:
    """Mid-distance dead skeletal trees and ash drifts."""
    s = _surf()
    col  = (38, 32, 40)
    bark = (46, 40, 48)
    for tx in range(0, INTERNAL_W, 46):
        # Ash drift mound
        pygame.draw.ellipse(s, col, (tx, INTERNAL_H - 16, 40, 24))
        # Bare dead tree
        trunk_x = tx + 26
        pygame.draw.rect(s, bark, (trunk_x, 116, 4, INTERNAL_H - 116))
        pygame.draw.line(s, bark, (trunk_x + 2, 124), (trunk_x + 12, 112), 2)
        pygame.draw.line(s, bark, (trunk_x + 2, 130), (trunk_x - 8, 120), 2)
        pygame.draw.line(s, bark, (trunk_x + 2, 118), (trunk_x + 8, 106), 1)
    return s


def _cinderwood_far() -> pygame.Surface:
    """Far stand of dead burnt trees against a smoke-hazed sky — dark browns."""
    s = _surf()
    col   = (34, 24, 22)
    smoke = (44, 32, 30)
    # Hazy smoke band across the upper sky
    pygame.draw.rect(s, smoke, (0, 30, INTERNAL_W, 26))
    # Row of bare charred trunks
    for tx in range(0, INTERNAL_W, 34):
        h = 70 + (tx % 4) * 10
        trunk_x = tx + 14
        pygame.draw.rect(s, col, (trunk_x, INTERNAL_H - h, 6, h))
        # A couple of broken limbs
        pygame.draw.line(s, col, (trunk_x + 3, INTERNAL_H - h + 14),
                         (trunk_x + 16, INTERNAL_H - h + 2), 2)
        pygame.draw.line(s, col, (trunk_x + 3, INTERNAL_H - h + 24),
                         (trunk_x - 10, INTERNAL_H - h + 12), 2)
    return s


def _cinderwood_mid() -> pygame.Surface:
    """Mid-distance charred stumps with faint ember glow at their roots."""
    s = _surf()
    col   = (24, 16, 16)
    ember = (150, 56, 20)
    for tx in range(0, INTERNAL_W, 40):
        # Broken stump
        pygame.draw.rect(s, col, (tx + 12, INTERNAL_H - 40, 12, 40))
        pygame.draw.polygon(s, col, [
            (tx + 12, INTERNAL_H - 40), (tx + 18, INTERNAL_H - 52),
            (tx + 24, INTERNAL_H - 40),
        ])
        # Ember glow pooled at the base
        pygame.draw.ellipse(s, ember, (tx + 10, INTERNAL_H - 8, 18, 6))
    return s


def _emberfall_far() -> pygame.Surface:
    """Far burning fortress ramparts against a fire-lit sky — deep reds + glow."""
    s = _surf()
    col_stone = (50, 22, 18)
    glow      = (150, 50, 14)
    # Fire-glow band along the horizon
    for y in range(70, 120):
        intensity = int(70 * (y - 70) / 50)
        pygame.draw.line(s, (intensity, intensity // 4, 0),
                         (0, y), (INTERNAL_W, y))
    # Broken battlements
    for tx in range(0, INTERNAL_W, 50):
        h = 64 + (tx % 4) * 10
        pygame.draw.rect(s, col_stone, (tx + 14, INTERNAL_H - h, 22, h))
        # Crenellations
        for bx in range(tx + 14, tx + 36, 8):
            pygame.draw.rect(s, col_stone, (bx, INTERNAL_H - h - 6, 5, 8))
    # Distant flame plumes
    for tx in range(0, INTERNAL_W, 80):
        pygame.draw.ellipse(s, glow, (tx + 30, 96, 18, 26))
    return s


def _emberfall_mid() -> pygame.Surface:
    """Mid collapsed walls with torch fires and rising smoke."""
    s = _surf()
    col_wall  = (66, 30, 22)
    col_fire  = (230, 120, 30)
    col_smoke = (70, 40, 36)
    for tx in range(0, INTERNAL_W, 24):
        # Ruined wall block of varying height
        h = 40 + (tx % 3) * 18
        pygame.draw.rect(s, col_wall, (tx, INTERNAL_H - h, 20, h))
        # Mortar joints
        for ty in range(INTERNAL_H - h, INTERNAL_H, 12):
            pygame.draw.line(s, (40, 18, 14), (tx, ty), (tx + 20, ty))
    # Torch fires perched on the walls
    for tx in range(12, INTERNAL_W, 48):
        pygame.draw.rect(s, col_fire, (tx, INTERNAL_H - 70, 8, 10))
        pygame.draw.rect(s, (255, 200, 90), (tx + 2, INTERNAL_H - 68, 4, 5))
        # Smoke wisps
        for i in range(3):
            wy = INTERNAL_H - 74 - i * 5
            pygame.draw.rect(s, col_smoke, (tx + 2 + (i % 2), wy, 3, 4))
    return s


def _frostkeep_far() -> pygame.Surface:
    """Far frozen fortress ramparts under a cold aurora glow — icy blues."""
    s = _surf()
    col_stone = (52, 70, 100)
    glow      = (120, 170, 215)
    # Cold aurora glow band along the horizon
    for y in range(70, 120):
        intensity = int(55 * (y - 70) / 50)
        pygame.draw.line(s, (intensity // 3, intensity // 2, intensity),
                         (0, y), (INTERNAL_W, y))
    # Frozen battlements
    for tx in range(0, INTERNAL_W, 50):
        h = 64 + (tx % 4) * 10
        pygame.draw.rect(s, col_stone, (tx + 14, INTERNAL_H - h, 22, h))
        # Crenellations
        for bx in range(tx + 14, tx + 36, 8):
            pygame.draw.rect(s, col_stone, (bx, INTERNAL_H - h - 6, 5, 8))
        # Ice cap on the rampart top
        pygame.draw.rect(s, (200, 225, 245), (tx + 14, INTERNAL_H - h - 8, 22, 3))
    # Distant frost plumes
    for tx in range(0, INTERNAL_W, 80):
        pygame.draw.ellipse(s, glow, (tx + 30, 96, 18, 26))
    return s


def _frostkeep_mid() -> pygame.Surface:
    """Mid frozen walls hung with icicles and cold blue brazier flames."""
    s = _surf()
    col_wall = (40, 56, 82)
    col_ice  = (180, 215, 240)
    col_fire = (120, 200, 240)
    for tx in range(0, INTERNAL_W, 24):
        # Ice-rimed wall block of varying height
        h = 40 + (tx % 3) * 18
        pygame.draw.rect(s, col_wall, (tx, INTERNAL_H - h, 20, h))
        # Mortar joints
        for ty in range(INTERNAL_H - h, INTERNAL_H, 12):
            pygame.draw.line(s, (28, 40, 60), (tx, ty), (tx + 20, ty))
        # Icicles hanging from the top edge
        for ix in range(tx + 3, tx + 20, 6):
            pygame.draw.polygon(s, col_ice, [
                (ix, INTERNAL_H - h), (ix + 2, INTERNAL_H - h),
                (ix + 1, INTERNAL_H - h + 6),
            ])
    # Cold blue braziers perched on the walls
    for tx in range(12, INTERNAL_W, 48):
        pygame.draw.rect(s, col_fire, (tx, INTERNAL_H - 70, 8, 10))
        pygame.draw.rect(s, (210, 240, 255), (tx + 2, INTERNAL_H - 68, 4, 5))
        # Frost wisps
        for i in range(3):
            wy = INTERNAL_H - 74 - i * 5
            pygame.draw.rect(s, (90, 130, 170), (tx + 2 + (i % 2), wy, 3, 4))
    return s


# ---------------------------------------------------------------------------
# Biome → layer mapping
# ---------------------------------------------------------------------------

_BIOME_LAYERS: dict[str, list[tuple]] = {
    "level_01_greenshire_hills": [(_greenshire_far, 0.15), (_greenshire_mid, 0.35)],
    "level_02_wolfwood":         [(_wolfwood_far,   0.15), (_wolfwood_mid,   0.35)],
    "level_03_glass_caverns":    [(_mines_far,      0.10), (_mines_mid,      0.30)],
    "level_04_sunken_mines":     [(_greenshire_far, 0.15), (_greenshire_mid, 0.35)],  # World I: green grotto (re-themed)
    "level_05_ash_marshes":      [(_throne_far,     0.13), (_throne_mid,     0.32)],  # World II: magma marsh (re-themed)
    "level_06_pale_tower":       [(_tower_far,      0.15), (_tower_mid,      0.35)],
    "level_07_cursed_catacombs": [(_catacombs_far,  0.10), (_catacombs_mid,  0.25)],
    "level_08_forsaken_bridge":     [(_bridge_far,  0.12), (_bridge_mid,  0.30)],  # World III: frozen broken bridge (icy grade)
    "level_09_skybound_spires":     [(_spires_far,  0.08), (_spires_mid,  0.22)],
    "level_10_goblin_kings_throne": [(_throne_far,  0.10), (_throne_mid,  0.28)],
    "level_11_ashfall_wastes":      [(_ashfall_far, 0.12), (_ashfall_mid, 0.30)],
    "level_12_cinderwood_remains":  [(_cinderwood_far, 0.13), (_cinderwood_mid, 0.32)],
    "level_13_emberfall_keep":      [(_frostkeep_far,  0.10), (_frostkeep_mid,  0.28)],  # World III: frozen keep (re-themed)
}


def make_parallax_layers(level_name: str) -> list[ParallaxLayer]:
    entries = _BIOME_LAYERS.get(level_name, _BIOME_LAYERS["level_02_wolfwood"])
    return [ParallaxLayer(fn(), factor) for fn, factor in entries]
