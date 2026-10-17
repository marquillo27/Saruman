"""Generate the enemy animation strips in the hero's style.

Like tools/generate_hero.py, each enemy is built from simple parts at native
resolution, posed per frame and finished with the same soft selective
outline (outline pixels are a darkened copy of the colour they border).
Sprites face right; the game mirrors them. Frame counts match what
saruman/entities/enemy.py animates.

Usage:
    python tools/generate_enemies.py                 # writes assets/sprites/enemy_*_strip.png
    python tools/generate_enemies.py --preview out.png
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "assets" / "sprites"

Px = tuple[int, int, int, int]


def c(r: int, g: int, b: int, a: int = 255) -> Px:
    return (r, g, b, a)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def selout(img: Image.Image, skip: set | None = None) -> Image.Image:
    """Soft 1 px outline: each outline pixel is a darkened copy of the colour
    it borders (same recipe as the hero)."""
    w, h = img.size
    src, out = img.load(), img.copy()
    dst = out.load()
    skip = skip or set()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] and src[nx, ny] not in skip:
                    r, g, b, _ = src[nx, ny]
                    dst[x, y] = (int(r * 0.42) + 12, int(g * 0.42) + 10, int(b * 0.42) + 16, 255)
                    break
    return out


def strip(frames: list[Image.Image]) -> Image.Image:
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


def canvas(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def legs(d, xs, top, bottom, col, foot, lifts=(0, 0), width=2):
    for x, lift in zip(xs, lifts):
        d.rectangle([x, top, x + width - 1, bottom - lift], fill=col)
        d.rectangle([x, bottom - lift - 1, x + width, bottom - lift], fill=foot)


# --------------------------------------------------------------------------
# Goblinkin 20x24 — 4 walk frames
# --------------------------------------------------------------------------

GOB_SKIN, GOB_SKIN_D, GOB_SKIN_L = c(104, 156, 72), c(70, 112, 52), c(150, 196, 104)
GOB_EYE, LEATHER, LEATHER_D = c(230, 50, 40), c(116, 76, 46), c(80, 50, 32)
STEEL, STEEL_D, STEEL_L = c(170, 176, 190), c(110, 116, 132), c(222, 228, 236)


def goblin_frame(i: int) -> Image.Image:
    img, d = canvas(20, 24)
    bob = (0, 1, 0, 1)[i]
    step = ((0, 2), (1, 1), (2, 0), (1, 1))[i]
    legs(d, (6, 10), 19, 23, GOB_SKIN_D, LEATHER_D, step)
    # tunic
    d.rectangle([5, 12 + bob, 13, 19], fill=LEATHER)
    d.rectangle([5, 12 + bob, 6, 19], fill=LEATHER_D)
    d.line([(5, 17), (13, 17)], fill=LEATHER_D)
    # head
    hy = 2 + bob
    d.ellipse([4, hy, 14, hy + 10], fill=GOB_SKIN)
    d.polygon([(4, hy + 4), (0, hy + 2), (4, hy + 7)], fill=GOB_SKIN_D)      # back ear
    d.polygon([(13, hy + 3), (18, hy + 1), (14, hy + 6)], fill=GOB_SKIN)     # front ear
    d.line([(6, hy + 1), (11, hy + 1)], fill=GOB_SKIN_L)
    d.point((15, hy + 6), fill=GOB_SKIN)                                       # nose
    d.rectangle([11, hy + 4, 12, hy + 5], fill=GOB_EYE)
    d.line([(11, hy + 8), (14, hy + 8)], fill=GOB_SKIN_D)                    # grin
    d.point((12, hy + 9), fill=STEEL_L)                                        # tooth
    # arm + dagger
    d.line([(11, 14 + bob), (15, 15 + bob)], fill=GOB_SKIN, width=2)
    d.line([(15, 16 + bob), (19, 12 + bob)], fill=STEEL)
    d.point((15, 15 + bob), fill=LEATHER_D)
    return selout(img)


# --------------------------------------------------------------------------
# Wraith 20x28 — 4 floating frames
# --------------------------------------------------------------------------

WR, WR_D, WR_L, WR_EYE = c(100, 82, 156), c(64, 50, 108), c(150, 132, 206), c(160, 245, 255)


def wraith_frame(i: int) -> Image.Image:
    img, d = canvas(20, 28)
    bob = (0, 1, 2, 1)[i]
    wave = (0, 1, 0, -1)[i]
    top = 2 + bob
    # robe body tapering into a ragged hem
    d.polygon([(6, top + 4), (14, top + 4), (17, 22 + bob), (3, 22 + bob)], fill=WR)
    d.polygon([(6, top + 4), (9, top + 4), (5, 22 + bob), (3, 22 + bob)], fill=WR_D)
    for k, x in enumerate(range(3, 18, 3)):
        tip = 26 + bob + ((k + wave) % 2) * 1
        d.polygon([(x, 21 + bob), (x + 3, 21 + bob), (x + 1, tip)], fill=WR if k % 2 else WR_D)
    # hood
    d.ellipse([5, top, 15, top + 11], fill=WR)
    d.ellipse([8, top + 3, 15, top + 10], fill=c(26, 18, 40))                 # dark face hole
    d.rectangle([11, top + 6, 12, top + 6], fill=WR_EYE)
    d.point((14, top + 6), fill=WR_EYE)
    d.line([(6, top + 1), (11, top)], fill=WR_L)
    # reaching claw arm
    d.line([(11, top + 13), (17, top + 11 + wave)], fill=WR_L, width=2)
    d.line([(17, top + 11 + wave), (19, top + 9 + wave)], fill=c(220, 220, 240))
    return selout(img)


# --------------------------------------------------------------------------
# ShieldKnight 24x32 — 2 walk frames
# --------------------------------------------------------------------------

PLUME, SHIELD, SHIELD_D, GOLD = c(190, 46, 46), c(62, 84, 156), c(40, 56, 110), c(224, 182, 70)


def knight_frame(i: int) -> Image.Image:
    img, d = canvas(24, 32)
    step = ((0, 2), (2, 0))[i]
    legs(d, (7, 11), 24, 31, STEEL_D, c(60, 62, 72), step, width=3)
    # torso
    d.rectangle([6, 13, 15, 24], fill=STEEL)
    d.rectangle([6, 13, 8, 24], fill=STEEL_D)
    d.line([(9, 15), (14, 15)], fill=STEEL_L)
    d.rectangle([6, 22, 15, 23], fill=LEATHER)                                 # belt
    # helmet with visor slit + plume
    d.rectangle([6, 3, 15, 13], fill=STEEL)
    d.rectangle([6, 3, 8, 13], fill=STEEL_D)
    d.line([(10, 8), (15, 8)], fill=c(20, 20, 28))
    d.line([(7, 3), (14, 3)], fill=STEEL_L)
    d.polygon([(7, 3), (4, 0), (12, 1), (10, 3)], fill=PLUME)
    # big kite shield in front
    sx = 15 + (1 if i else 0)
    d.polygon([(sx, 11), (sx + 7, 11), (sx + 7, 22), (sx + 3, 28), (sx, 22)], fill=SHIELD)
    d.polygon([(sx, 11), (sx + 2, 11), (sx + 2, 24), (sx, 22)], fill=SHIELD_D)
    d.line([(sx, 11), (sx + 7, 11)], fill=GOLD)
    d.line([(sx + 4, 14), (sx + 4, 23)], fill=GOLD)                            # emblem cross
    d.line([(sx + 2, 17), (sx + 6, 17)], fill=GOLD)
    return selout(img)


# --------------------------------------------------------------------------
# SkeletonArcher 22x32 — 0 idle, 1 drawing the bow
# --------------------------------------------------------------------------

BONE, BONE_D, BONE_L, BOW = c(228, 222, 202), c(176, 168, 146), c(250, 248, 236), c(134, 86, 48)


def archer_frame(i: int) -> Image.Image:
    img, d = canvas(22, 32)
    legs(d, (8, 11), 22, 31, BONE_D, c(90, 84, 72), (0, 0), width=2)
    d.line([(8, 21), (13, 21)], fill=BONE)                                     # pelvis
    # spine + ribs
    d.line([(10, 11), (10, 21)], fill=BONE_D, width=2)
    for y in (13, 15, 17):
        d.line([(7, y), (13, y)], fill=BONE)
    # skull
    d.ellipse([6, 2, 15, 11], fill=BONE)
    d.line([(7, 3), (12, 2)], fill=BONE_L)
    d.rectangle([11, 5, 12, 7], fill=c(30, 22, 26))
    d.point((12, 6), fill=c(230, 50, 50))
    d.rectangle([10, 9, 14, 10], fill=BONE_D)                                  # jaw
    d.point((11, 10), fill=BONE_L); d.point((13, 10), fill=BONE_L)
    if i == 0:
        # bow held low
        d.arc([12, 12, 20, 30], 280, 80, fill=BOW, width=2)
        d.line([(17, 13), (17, 29)], fill=c(220, 220, 220))
        d.line([(10, 14), (15, 20)], fill=BONE, width=1)
    else:
        # drawing: bow raised, string pulled back with an arrow
        d.arc([14, 6, 22, 26], 280, 80, fill=BOW, width=2)
        d.line([(19, 7), (11, 16), (19, 25)], fill=c(220, 220, 220))
        d.line([(11, 16), (21, 16)], fill=c(150, 110, 70))
        d.point((21, 16), fill=STEEL_L)
        d.line([(10, 14), (11, 16)], fill=BONE)
        d.line([(12, 14), (19, 16)], fill=BONE)
    return selout(img)


# --------------------------------------------------------------------------
# CaveBat 24x14 — 2 flap frames
# --------------------------------------------------------------------------

BAT, BAT_D, BAT_W, BAT_EYE = c(76, 46, 96), c(48, 28, 64), c(104, 66, 128), c(240, 70, 70)


def bat_frame(i: int) -> Image.Image:
    img, d = canvas(24, 14)
    if i == 0:   # wings up
        d.polygon([(10, 7), (2, 0), (0, 4), (3, 6), (6, 5), (9, 9)], fill=BAT_W)
        d.polygon([(14, 7), (22, 0), (24, 4), (21, 6), (18, 5), (15, 9)], fill=BAT_W)
        d.line([(10, 7), (2, 0)], fill=BAT_D); d.line([(14, 7), (22, 0)], fill=BAT_D)
    else:        # wings down
        d.polygon([(10, 7), (1, 9), (2, 13), (5, 11), (7, 12), (9, 9)], fill=BAT_W)
        d.polygon([(14, 7), (23, 9), (22, 13), (19, 11), (17, 12), (15, 9)], fill=BAT_W)
        d.line([(10, 7), (1, 9)], fill=BAT_D); d.line([(14, 7), (23, 9)], fill=BAT_D)
    d.ellipse([9, 4, 15, 11], fill=BAT)
    d.polygon([(10, 5), (10, 1), (12, 4)], fill=BAT)                           # ears
    d.polygon([(14, 5), (14, 1), (12, 4)], fill=BAT)
    d.point((11, 7), fill=BAT_EYE); d.point((13, 7), fill=BAT_EYE)
    d.point((11, 10), fill=BONE_L); d.point((13, 10), fill=BONE_L)              # fangs
    return selout(img)


# --------------------------------------------------------------------------
# Slime 20x14 / SmallSlime 12x9 — 2 squish frames
# --------------------------------------------------------------------------

SL, SL_D, SL_L = c(96, 204, 112), c(56, 146, 80), c(186, 246, 190)


def _slime(w: int, h: int, i: int, eye: bool = True) -> Image.Image:
    img, d = canvas(w, h)
    if i == 0:
        box = [1, 2, w - 2, h - 1]
    else:
        box = [0, 4, w - 1, h - 1]
    d.ellipse(box, fill=SL)
    d.rectangle([box[0], h - 3, box[2], h - 1], fill=SL_D)
    d.ellipse([box[0] + 2, box[1] + 1, box[0] + 4 + w // 6, box[1] + 3], fill=SL_L)
    if eye:
        ey = box[1] + (box[3] - box[1]) // 2
        d.rectangle([w // 2 + 1, ey, w // 2 + 2, ey + 1], fill=c(30, 40, 30))
        d.rectangle([w // 2 + 4, ey, w // 2 + 5, ey + 1], fill=c(30, 40, 30))
    return selout(img)


def slime_frame(i: int) -> Image.Image:
    return _slime(20, 14, i)


def small_slime_frame(i: int) -> Image.Image:
    img, d = canvas(12, 9)
    box = [1, 1, 10, 8] if i == 0 else [0, 3, 11, 8]
    d.ellipse(box, fill=SL)
    d.rectangle([box[0], 7, box[2], 8], fill=SL_D)
    d.point((box[0] + 2, box[1] + 1), fill=SL_L)
    d.point((7, box[1] + 2), fill=c(30, 40, 30)); d.point((9, box[1] + 2), fill=c(30, 40, 30))
    return selout(img)


# --------------------------------------------------------------------------
# SpitterPlant 20x24 — 0 idle, 1 spitting
# --------------------------------------------------------------------------

POT, POT_D, POT_L = c(170, 96, 56), c(120, 64, 38), c(206, 132, 82)
STEM, STEM_D = c(70, 150, 70), c(44, 104, 50)
PETAL, PETAL_D, MAW = c(200, 64, 156), c(140, 36, 110), c(250, 214, 80)


def spitter_frame(i: int) -> Image.Image:
    img, d = canvas(20, 24)
    # pot
    d.polygon([(4, 16), (16, 16), (14, 23), (6, 23)], fill=POT)
    d.rectangle([3, 15, 17, 17], fill=POT_L)
    d.polygon([(4, 18), (7, 18), (8, 23), (6, 23)], fill=POT_D)
    # stem + leaves
    d.line([(10, 15), (10, 9)], fill=STEM, width=2)
    d.polygon([(10, 13), (4, 10), (6, 14)], fill=STEM_D)
    d.polygon([(11, 12), (16, 9), (15, 13)], fill=STEM)
    # head (faces right); open mouth when spitting
    d.ellipse([5, 1, 15, 10], fill=PETAL)
    d.ellipse([5, 1, 9, 10], fill=PETAL_D)
    if i == 0:
        d.line([(12, 6), (16, 6)], fill=PETAL_D)
        d.point((11, 3), fill=c(30, 20, 30))
    else:
        d.polygon([(11, 5), (19, 2), (19, 9), (11, 7)], fill=MAW)
        d.line([(12, 5), (18, 3)], fill=BONE_L)
        d.point((10, 3), fill=c(30, 20, 30))
    return selout(img)


# --------------------------------------------------------------------------
# MimicChest 22x22 — 0 closed, 1 ajar, 2 chomp
# --------------------------------------------------------------------------

WOOD, WOOD_D, WOOD_L, IRON = c(146, 94, 52), c(100, 62, 34), c(186, 128, 74), c(96, 98, 110)


def mimic_frame(i: int) -> Image.Image:
    img, d = canvas(22, 22)
    o = 4   # headroom so the opening lid stays inside the frame
    lid_lift = (0, 3, 6)[i]
    # base
    d.rectangle([1, 9 + o, 20, 17 + o], fill=WOOD)
    d.rectangle([1, 9 + o, 3, 17 + o], fill=WOOD_D)
    for x in (6, 15):
        d.rectangle([x, 9 + o, x + 1, 17 + o], fill=IRON)
    if i:
        # mouth interior, teeth, tongue, eyes
        d.rectangle([2, 9 + o - lid_lift, 19, 9 + o], fill=c(70, 20, 30))
        for x in range(3, 19, 3):
            d.polygon([(x, 9 + o), (x + 2, 9 + o), (x + 1, 7 + o)], fill=BONE_L)
            d.polygon([(x, 9 + o - lid_lift), (x + 2, 9 + o - lid_lift), (x + 1, 11 + o - lid_lift)], fill=BONE_L)
        d.rectangle([10, 9 + o - lid_lift // 2, 16, 9 + o], fill=c(220, 70, 90))
    # lid (rises with lid_lift)
    ly = 9 + o - lid_lift
    d.rectangle([1, ly - 6, 20, ly - 1], fill=WOOD)
    d.line([(1, ly - 6), (20, ly - 6)], fill=WOOD_L)
    d.rectangle([1, ly - 6, 3, ly - 1], fill=WOOD_D)
    for x in (6, 15):
        d.rectangle([x, ly - 6, x + 1, ly - 1], fill=IRON)
    if i:
        d.point((13, ly - 4), fill=c(250, 230, 60)); d.point((17, ly - 4), fill=c(250, 230, 60))
    else:
        d.rectangle([10, ly - 2, 12, ly + 1], fill=GOLD)                       # lock
    return selout(img)


# --------------------------------------------------------------------------
# BossWarg 48x32 — 4 run frames
# --------------------------------------------------------------------------

FUR, FUR_D, FUR_L = c(96, 86, 80), c(62, 54, 52), c(140, 128, 118)


def warg_frame(i: int) -> Image.Image:
    img, d = canvas(48, 32)
    bob = (0, 1, 0, 1)[i]
    # legs: (x_top, swing) pairs for back and front pairs
    swings = ((-3, 3), (0, 0), (3, -3), (0, 0))[i]
    for x, s in ((10, swings[0]), (14, -swings[0]), (31, swings[1]), (35, -swings[1])):
        d.line([(x, 20 + bob), (x + s, 30)], fill=FUR_D, width=3)
        d.rectangle([x + s - 1, 29, x + s + 2, 31], fill=c(40, 34, 34))
    # body
    d.ellipse([6, 9 + bob, 40, 25 + bob], fill=FUR)
    d.ellipse([6, 15 + bob, 36, 25 + bob], fill=FUR_D)
    # mane spikes
    for k, x in enumerate(range(12, 34, 4)):
        d.polygon([(x, 11 + bob), (x + 2, 5 + bob - (k % 2)), (x + 4, 11 + bob)], fill=FUR_D)
    # tail
    d.polygon([(8, 14 + bob), (0, 8 + bob), (2, 16 + bob)], fill=FUR)
    # head
    hx = 34
    d.ellipse([hx, 6 + bob, hx + 11, 18 + bob], fill=FUR)
    d.polygon([(hx + 8, 10 + bob), (hx + 14, 13 + bob), (hx + 8, 17 + bob)], fill=FUR)   # snout
    d.polygon([(hx + 2, 7 + bob), (hx + 3, 1 + bob), (hx + 6, 7 + bob)], fill=FUR_D)     # ear
    d.rectangle([hx + 7, 10 + bob, hx + 8, 11 + bob], fill=c(240, 50, 40))
    d.line([(hx + 9, 16 + bob), (hx + 13, 15 + bob)], fill=c(40, 24, 24))
    d.point((hx + 10, 17 + bob), fill=BONE_L); d.point((hx + 12, 16 + bob), fill=BONE_L)
    d.line([(14, 11 + bob), (30, 10 + bob)], fill=FUR_L)
    return selout(img)


# --------------------------------------------------------------------------
# GoblinKing 40x40 / NightKing 44x44 — 3 frames each
# --------------------------------------------------------------------------

CAPE, CAPE_D = c(116, 40, 126), c(78, 24, 88)


def goblin_king_frame(i: int) -> Image.Image:
    img, d = canvas(40, 40)
    bob = (0, 1, 2)[i]
    legs(d, (13, 20), 30, 39, GOB_SKIN_D, LEATHER_D, ((0, 2), (1, 1), (2, 0))[i], width=4)
    d.polygon([(8, 14 + bob), (28, 14 + bob), (31, 34), (5, 34)], fill=CAPE)        # cape
    d.polygon([(8, 14 + bob), (13, 14 + bob), (9, 34), (5, 34)], fill=CAPE_D)
    d.ellipse([10, 13 + bob, 28, 33], fill=GOB_SKIN)                                 # belly
    d.rectangle([10, 27, 28, 29], fill=LEATHER)
    d.rectangle([17, 27, 20, 29], fill=GOLD)
    hy = 2 + bob
    d.ellipse([10, hy, 28, hy + 15], fill=GOB_SKIN)
    d.polygon([(10, hy + 6), (3, hy + 3), (10, hy + 10)], fill=GOB_SKIN_D)
    d.polygon([(27, hy + 5), (36, hy + 2), (28, hy + 9)], fill=GOB_SKIN)
    d.rectangle([22, hy + 6, 24, hy + 7], fill=GOB_EYE)
    d.line([(20, hy + 11), (27, hy + 11)], fill=GOB_SKIN_D)
    d.point((22, hy + 12), fill=BONE_L); d.point((25, hy + 12), fill=BONE_L)
    for k, x in enumerate((12, 16, 20, 24)):                                        # crown
        d.polygon([(x, hy + 1), (x + 2, hy - 2 - (k % 2)), (x + 4, hy + 1)], fill=GOLD)
    d.rectangle([12, hy, 27, hy + 2], fill=GOLD)
    # spiked club, raised higher each frame
    ang = (0, 4, 8)[i]
    d.line([(27, 20 + bob), (35, 12 - ang + bob)], fill=WOOD, width=3)
    d.ellipse([32, 6 - ang + bob, 39, 14 - ang + bob], fill=WOOD_D)
    d.point((38, 9 - ang + bob), fill=STEEL_L); d.point((33, 7 - ang + bob), fill=STEEL_L)
    return selout(img)


ICE_SKIN, ICE_SKIN_D, ICE_EYE = c(156, 194, 230), c(108, 146, 190), c(140, 236, 255)
ARMOR, ARMOR_D, ARMOR_L = c(52, 62, 96), c(34, 40, 66), c(90, 104, 148)
ICE, ICE_L = c(190, 230, 255), c(240, 252, 255)


def night_king_frame(i: int) -> Image.Image:
    img, d = canvas(44, 44)
    bob = (0, 1, 2)[i]
    legs(d, (16, 23), 33, 43, ARMOR_D, c(24, 26, 40), ((0, 2), (1, 1), (2, 0))[i], width=4)
    d.polygon([(10, 14 + bob), (32, 14 + bob), (36, 38), (5, 38)], fill=c(30, 44, 86))  # cape
    d.polygon([(10, 14 + bob), (15, 14 + bob), (10, 38), (5, 38)], fill=c(20, 28, 58))
    d.rectangle([13, 15 + bob, 30, 34], fill=ARMOR)
    d.rectangle([13, 15 + bob, 16, 34], fill=ARMOR_D)
    d.line([(18, 18 + bob), (29, 18 + bob)], fill=ARMOR_L)
    d.line([(21, 22 + bob), (21, 32)], fill=ARMOR_L)
    hy = 2 + bob
    d.ellipse([14, hy + 2, 30, hy + 16], fill=ICE_SKIN)
    d.rectangle([14, hy + 8, 17, hy + 15], fill=ICE_SKIN_D)
    d.rectangle([24, hy + 8, 26, hy + 9], fill=ICE_EYE)
    d.point((28, hy + 8), fill=ICE_EYE)
    d.line([(23, hy + 13), (28, hy + 13)], fill=ICE_SKIN_D)
    for k, x in enumerate(range(14, 31, 4)):                                         # ice crown
        d.polygon([(x, hy + 4), (x + 2, hy - 2 - (k % 2) * 2), (x + 3, hy + 4)], fill=ICE)
        d.point((x + 2, hy), fill=ICE_L)
    # ice sword, glow edge; swings forward over the frames
    tip = ((40, 6), (42, 12), (43, 20))[i]
    d.line([(29, 24 + bob), tip], fill=ICE, width=3)
    d.line([(30, 23 + bob), tip], fill=ICE_L, width=1)
    d.rectangle([27, 23 + bob, 31, 26 + bob], fill=ARMOR_L)                           # hilt
    return selout(img, skip={ICE_L})


# --------------------------------------------------------------------------

# strip name -> (frame builder, frame count)
ENEMIES: dict[str, tuple[Callable[[int], Image.Image], int]] = {
    "enemy_goblinkin_strip":    (goblin_frame, 4),
    "enemy_wraith_strip":       (wraith_frame, 4),
    "enemy_shieldknight_strip": (knight_frame, 2),
    "enemy_archer_strip":       (archer_frame, 2),
    "enemy_bat_strip":          (bat_frame, 2),
    "enemy_slime_strip":        (slime_frame, 2),
    "enemy_small_slime_strip":  (small_slime_frame, 2),
    "enemy_spitter_strip":      (spitter_frame, 2),
    "enemy_mimic_strip":        (mimic_frame, 3),
    "enemy_bosswarg_strip":     (warg_frame, 4),
    "enemy_goblin_king_strip":  (goblin_king_frame, 3),
    "enemy_night_king_strip":   (night_king_frame, 3),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path, help="also save a 6x preview sheet of every strip")
    args = ap.parse_args()
    built = {}
    for name, (fn, n) in ENEMIES.items():
        s = strip([fn(i) for i in range(n)])
        s.save(SPRITES / f"{name}.png")
        built[name] = s
        print(f"wrote {name}.png {s.size}")
    if args.preview:
        scale, pad = 6, 6
        wmax = max(s.width for s in built.values())
        htot = sum(s.height + pad for s in built.values())
        sheet = Image.new("RGBA", (wmax * scale + 2 * pad, htot * scale + pad), (52, 60, 72, 255))
        y = pad
        for s in built.values():
            sheet.alpha_composite(s.resize((s.width * scale, s.height * scale), Image.NEAREST), (pad, y))
            y += (s.height + pad) * scale
        sheet.save(args.preview)


if __name__ == "__main__":
    main()
