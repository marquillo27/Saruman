"""
One-time script — generates pixel-art entity sprites as PNGs using Pillow.
Run from project root:  uv run python tools/generate_sprites.py
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "assets", "sprites")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# Palette (all RGBA)
# ---------------------------------------------------------------------------

# player (Aldric)
P_CLOAK_TOP  = (65, 58, 90, 255)
P_CLOAK_BOT  = (32, 28, 50, 255)
P_CLOAK_LITE = (82, 74, 112, 255)
P_CLOAK_FOOT = (40, 35, 58, 255)
P_FACE       = (220, 185, 145, 255)
P_GOLD       = (212, 161, 85, 255)
P_STAFF_TOP  = (125, 98, 62, 255)
P_STAFF_BOT  = (72, 56, 34, 255)
P_EYE        = (28, 18, 22, 255)
P_BOOT       = (28, 22, 40, 255)
P_HOOD       = (45, 38, 65, 255)
P_SPR_W      = 12   # player sprite width  (collision box is 10)
P_SPR_H      = 18   # player sprite height (collision box is 16)

# goblinkin
G_HEAD_TOP   = (112, 158, 74, 255)
G_HEAD_BOT   = (78, 112, 52, 255)
G_BODY_TOP   = (100, 142, 65, 255)
G_BODY_BOT   = (68, 98, 44, 255)
G_VEST_TOP   = (62, 84, 44, 255)
G_VEST_BOT   = (40, 55, 26, 255)
G_EYE_WHITE  = (218, 212, 198, 255)
G_EYE_RED    = (215, 52, 52, 255)
G_FEET_TOP   = (58, 85, 36, 255)
G_FEET_BOT   = (38, 56, 22, 255)

# bosswarg
B_FUR_TOP    = (128, 48, 42, 255)
B_FUR_BOT    = (76, 24, 20, 255)
B_FUR_LITE   = (148, 64, 58, 255)
B_BELLY_TOP  = (158, 118, 92, 255)
B_BELLY_BOT  = (118, 84, 62, 255)
B_EYE        = (238, 148, 30, 255)
B_TEETH      = (244, 240, 224, 255)
B_PAW_TOP    = (85, 32, 28, 255)
B_PAW_BOT    = (48, 16, 14, 255)

# shieldknight
SK_ARMOR_TOP = (88, 94, 135, 255)
SK_ARMOR_BOT = (52, 56, 92, 255)
SK_TRIM      = (138, 144, 188, 255)
SK_SHLD_TOP  = (168, 172, 210, 255)
SK_SHLD_BOT  = (88, 94, 138, 255)
SK_VISOR     = (20, 20, 38, 255)
SK_EMBLEM    = (218, 166, 88, 255)

# skeleton archer
SA_BONE      = (210, 205, 188, 255)
SA_BONE_DRK  = (158, 152, 135, 255)
SA_HOOD      = (80,  72,  60, 255)
SA_EYE       = (200,  40,  20, 255)
SA_BOW       = (130, 100,  58, 255)
SA_STRING    = (210, 205, 188, 255)

# cave bat
CB_BODY      = (90,  30, 100, 255)
CB_WING      = (60,  20,  75, 255)
CB_WING_LT   = (115, 50, 130, 255)
CB_EYE       = (220, 180,  30, 255)

# items
COIN_RIM     = (138, 96, 26, 255)
COIN_FACE    = (220, 168, 86, 255)
COIN_SHINE   = (250, 212, 122, 255)
COIN_EDGE    = (88, 60, 14, 255)
HEART_DARK   = (148, 24, 32, 255)
HEART_RED    = (218, 54, 64, 255)
HEART_PINK   = (244, 108, 112, 255)
BOW_BROWN    = (138, 90, 48, 255)
STRING_CYAN  = (100, 208, 224, 255)
ARROW_BLUE   = (68, 120, 205, 255)
PROJ_LITE    = (246, 246, 255, 255)
PROJ_MID     = (168, 164, 180, 255)
PROJ_DARK    = (98, 96, 110, 255)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _save(img: Image.Image, name: str) -> None:
    path = os.path.join(OUT, f"{name}.png")
    img.save(path)
    print(f"  wrote {path}")


def _hstack(*frames: Image.Image) -> Image.Image:
    w, h = frames[0].size
    strip = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f, (i * w, 0))
    return strip


def _vgrad(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
           top: tuple, bot: tuple) -> None:
    """Vertical gradient fill in pixel-rect [x0,x1) × [y0,y1)."""
    span = max(y1 - y0 - 1, 1)
    for y in range(y0, y1):
        t = (y - y0) / span
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        draw.line([(x0, y), (x1 - 1, y)], fill=(r, g, b, 255))


def _darken_edge(img: Image.Image, factor: float = 0.65) -> Image.Image:
    """Darken the outermost ring of opaque pixels — gives a subtle outline."""
    arr = np.array(img, dtype=np.float32)
    alpha = arr[:, :, 3]
    solid = alpha > 30          # shape (H, W)
    edge = np.zeros_like(solid, dtype=bool)
    edge[1:, :]  |= solid[1:, :]  & ~solid[:-1, :]   # transparent above
    edge[:-1, :] |= solid[:-1, :] & ~solid[1:, :]    # transparent below
    edge[:, 1:]  |= solid[:, 1:]  & ~solid[:, :-1]   # transparent left
    edge[:, :-1] |= solid[:, :-1] & ~solid[:, 1:]    # transparent right
    arr[edge, :3] = np.clip(arr[edge, :3] * factor, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------
# Player (Aldric) — 12×18 side profile, 6-frame strip (72×18)
#
# Facing RIGHT by default; sprite flipped horizontally when facing left.
# Right side of canvas = front of character.
# Drawing order (painter's algorithm, back → front):
#   rear leg → cloak body → cloak hem → front leg → head → front arm → staff
# ---------------------------------------------------------------------------

def _player_profile(
    draw: ImageDraw.ImageDraw,
    front_leg_x: int = 5,   # x col of front (right) leg
    rear_leg_x:  int = 2,   # x col of rear  (left)  leg
    staff_dx:    int = 0,   # staff lean at top: -1=back, 0=straight, +1=fwd
    body_rise:   int = 0,   # body bobs up this many px (passing frame)
    leg_dy:      int = 0,   # extra leg y shift: negative=pulled up (jump)
) -> None:
    r = body_rise

    # 1. REAR LEG — drawn first so cloak covers its upper portion
    rlx = max(0, min(7, rear_leg_x))
    leg_top = 14 + leg_dy
    _vgrad(draw, rlx, leg_top, rlx + 2, 18, P_CLOAK_BOT, P_BOOT)

    # 2. CLOAK SHOULDERS + BODY
    _vgrad(draw, 2,  6 - r, 10,  8 - r, P_CLOAK_TOP,  P_CLOAK_TOP)   # shoulders
    _vgrad(draw, 2,  8 - r, 10, 14 - r, P_CLOAK_TOP,  P_CLOAK_BOT)   # body taper
    _vgrad(draw, 1,  6 - r,  2, 14 - r, P_CLOAK_LITE, P_CLOAK_TOP)   # left-edge highlight
    # Belt
    draw.line([(1, 11 - r), (8, 11 - r)], fill=P_GOLD)

    # 3. CLOAK HEM — covers top of rear leg, front leg goes on top of this
    draw.polygon(
        [(1, 13 - r), (9, 13 - r), (7, 15 - r), (1, 15 - r)],
        fill=P_CLOAK_BOT,
    )

    # 4. FRONT LEG — in front of cloak hem
    flx = max(1, min(9, front_leg_x))
    _vgrad(draw, flx, leg_top, flx + 2, 18, P_CLOAK_FOOT, P_BOOT)

    # 5. HEAD — profile facing right
    # Hood (dark, covers most of head; face visible on right side only)
    draw.ellipse([(4, 0 - r), (10, 5 - r)], fill=P_CLOAK_TOP)
    # Face skin (right half of head, revealed in profile)
    draw.rectangle([(7, 1 - r), (10, 4 - r)], fill=P_FACE)
    # Nose bump
    draw.point([(11, 3 - r)], fill=P_FACE)
    # Re-apply hood over left portion (so only right side shows skin)
    draw.rectangle([(4, 1 - r), (7, 4 - r)], fill=P_HOOD)
    # Eye
    draw.point([(9, 2 - r)], fill=P_EYE)
    # Neck
    draw.rectangle([(6, 5 - r), (8, 6 - r)], fill=P_FACE)

    # 6. FRONT ARM (holding staff, rightmost body columns)
    _vgrad(draw, 9, 7 - r, 11, 13 - r, P_CLOAK_TOP, P_CLOAK_BOT)

    # 7. STAFF — runs full height at col 10-11, leans at top half
    tip_x = max(0, min(11, 10 + staff_dx))
    draw.point([(tip_x, 0)], fill=P_GOLD)   # gold tip
    for sy in range(1, 17):
        t  = sy / 16
        cr = int(P_STAFF_TOP[0] + (P_STAFF_BOT[0] - P_STAFF_TOP[0]) * t)
        cg = int(P_STAFF_TOP[1] + (P_STAFF_BOT[1] - P_STAFF_TOP[1]) * t)
        cb = int(P_STAFF_TOP[2] + (P_STAFF_BOT[2] - P_STAFF_TOP[2]) * t)
        sx = max(0, min(11, tip_x if sy <= 7 else 10))
        draw.point([(sx, sy)], fill=(cr, cg, cb, 255))


def make_player() -> Image.Image:
    img, draw = _new(P_SPR_W, P_SPR_H)
    _player_profile(draw)
    return _darken_edge(img)


def make_player_strip() -> Image.Image:
    """72×18: 6-frame strip — idle + 3-frame walk + jump + fall."""
    def _f(fl, rl, sdx=0, rise=0, ldy=0):
        img, d = _new(P_SPR_W, P_SPR_H)
        _player_profile(d, front_leg_x=fl, rear_leg_x=rl,
                        staff_dx=sdx, body_rise=rise, leg_dy=ldy)
        return _darken_edge(img)

    return _hstack(
        _f(5, 2),               # F0 idle
        _f(7, 1, sdx=-1),       # F1 stride A — front leg forward, staff leans back
        _f(4, 4, rise=1),       # F2 passing  — legs together, body bobs up 1px
        _f(2, 6, sdx=1),        # F3 stride B — front leg back, rear swings through
        _f(5, 2, sdx=-1, ldy=-2),  # F4 jump  — legs pulled up
        _f(6, 2, sdx=1,  ldy=1),   # F5 fall  — legs extending down
    )


# ---------------------------------------------------------------------------
# Goblinkin — 12×14, 4-frame walk strip (48×14)
# ---------------------------------------------------------------------------

def _goblinkin_body(draw: ImageDraw.ImageDraw, head_dy: int = 0,
                    foot_l_shift: int = 0, foot_r_shift: int = 0) -> None:
    """Draw goblinkin body parts. head_dy: 0=normal, -1=head up (ground contact)."""
    # Head — rounded ellipse
    hy = head_dy
    draw.ellipse([(2, hy), (10, hy + 4)], fill=None)
    _vgrad(draw, 2, hy, 10, hy + 4, G_HEAD_TOP, G_HEAD_BOT)
    # Eyes — white sclera + red pupils
    draw.rectangle([(4, hy + 1), (6, hy + 2)], fill=G_EYE_WHITE)
    draw.rectangle([(7, hy + 1), (9, hy + 2)], fill=G_EYE_WHITE)
    draw.point([(5, hy + 2)], fill=G_EYE_RED)
    draw.point([(8, hy + 2)], fill=G_EYE_RED)
    # Body
    _vgrad(draw, 1, 4, 11, 11, G_BODY_TOP, G_BODY_BOT)
    # Vest overlay (darker patch on torso)
    _vgrad(draw, 3, 5, 9, 10, G_VEST_TOP, G_VEST_BOT)
    # Feet
    lx = max(0, 2 + foot_l_shift)
    _vgrad(draw, lx, 11, lx + 4, 14, G_FEET_TOP, G_FEET_BOT)
    rx = max(0, 6 + foot_r_shift)
    _vgrad(draw, rx, 11, rx + 4, 14, G_FEET_TOP, G_FEET_BOT)


def make_goblinkin() -> Image.Image:
    img, draw = _new(12, 14)
    _goblinkin_body(draw)
    return _darken_edge(img)


def make_goblinkin_strip() -> Image.Image:
    """48×14: 4-frame walk cycle."""
    frames = []
    # F0 neutral
    img, draw = _new(12, 14); _goblinkin_body(draw)
    frames.append(_darken_edge(img))
    # F1 ground contact left — head 1px lower (impact), right foot forward
    img, draw = _new(12, 14); _goblinkin_body(draw, head_dy=1, foot_l_shift=-1, foot_r_shift=1)
    frames.append(_darken_edge(img))
    # F2 midstep
    img, draw = _new(12, 14); _goblinkin_body(draw)
    frames.append(_darken_edge(img))
    # F3 ground contact right — head 1px lower, left foot forward
    img, draw = _new(12, 14); _goblinkin_body(draw, head_dy=1, foot_l_shift=1, foot_r_shift=-1)
    frames.append(_darken_edge(img))
    return _hstack(*frames)


# ---------------------------------------------------------------------------
# Wraith — 12×16, 4-frame float strip (48×16) — alpha-gradient ghost body
# ---------------------------------------------------------------------------

def _make_wraith_frame(phase: float) -> Image.Image:
    """Per-pixel alpha gradient wraith. phase in [0, 2π) controls ripple."""
    arr = np.zeros((16, 12, 4), dtype=np.uint8)
    cx = 5.5
    for y in range(16):
        for x in range(12):
            # Horizontal alpha: solid at center, transparent at edges
            edge_a = max(0.0, 1.0 - abs(x - cx) / 4.5)
            # Vertical: fully solid body rows 2-10, fade bottom
            if y < 2:
                vert_a = y / 2.0            # fade in at top
            elif y < 11:
                vert_a = 1.0
            else:
                vert_a = max(0.0, (14 - y) / 3.0)  # wispy tail
            # Ripple based on phase
            ripple = 1.0 + math.sin(y * 0.65 + phase) * 0.14
            a = int(195 * edge_a * vert_a * ripple)
            a = max(0, min(255, a))
            # Color: dark purple hood top, mid purple body
            if y < 4:
                col = (80, 48, 120)
            elif y < 12:
                col = (112, 72, 165)
            else:
                col = (90, 55, 140)
            arr[y, x] = (*col, a)
    # Glowing white eyes at row 3, cols 4 and 7
    arr[3, 4] = (255, 255, 255, 232)
    arr[3, 7] = (255, 255, 255, 232)
    # Slight glow halo around eyes (dim white)
    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
        for ex, ey in [(4,3),(7,3)]:
            ny, nx = ey+dy, ex+dx
            if 0 <= ny < 16 and 0 <= nx < 12:
                old_a = arr[ny, nx, 3]
                arr[ny, nx] = (180, 160, 220, min(255, old_a + 60))
    return Image.fromarray(arr, "RGBA")


def make_wraith() -> Image.Image:
    return _make_wraith_frame(0.0)


def make_wraith_strip() -> Image.Image:
    """48×16: 4-frame float animation."""
    frames = [_make_wraith_frame(i * math.pi / 2) for i in range(4)]
    return _hstack(*frames)


# ---------------------------------------------------------------------------
# BossWarg — 24×20, 4-frame gallop strip (96×20)
# ---------------------------------------------------------------------------

def _bosswarg_body(draw: ImageDraw.ImageDraw, body_lift: int = 0,
                   front_paw_x: int = 2, rear_paw_x: int = 16) -> None:
    """Draw BossWarg. body_lift=1 lifts body 1px (floating phase)."""
    by = body_lift  # body Y offset
    # Main fur body
    _vgrad(draw, 2, 3 - by, 22, 17 - by, B_FUR_TOP, B_FUR_BOT)
    # Fur texture: dithered light stripe
    for y in range(3 - by, 17 - by, 2):
        for x in range(4, 20, 3):
            draw.point([(x, y)], fill=B_FUR_LITE)
    # Underbelly
    _vgrad(draw, 5, 12 - by, 19, 17 - by, B_BELLY_TOP, B_BELLY_BOT)
    # Head
    _vgrad(draw, 1, 0, 11, 8, B_FUR_TOP, B_FUR_BOT)
    # Snout polygon
    snout_pts = [(1, 5), (7, 5), (7, 9), (3, 9)]
    draw.polygon(snout_pts, fill=B_BELLY_BOT)
    _vgrad(draw, 1, 5, 7, 10, B_BELLY_TOP, B_BELLY_BOT)
    # Eyes
    draw.rectangle([(3, 2), (4, 3)], fill=B_EYE)
    draw.rectangle([(7, 2), (8, 3)], fill=B_EYE)
    # Teeth row
    for x in range(1, 7, 2):
        draw.point([(x, 8)], fill=B_TEETH)
    # Tail stub
    _vgrad(draw, 22, 4 - by, 24, 10 - by, B_FUR_TOP, B_FUR_BOT)
    # Front paw
    fp = front_paw_x
    _vgrad(draw, fp, 17, fp + 4, 20, B_PAW_TOP, B_PAW_BOT)
    draw.ellipse([(fp, 18), (fp + 3, 20)], fill=B_PAW_BOT)
    # Rear paw
    rp = rear_paw_x
    _vgrad(draw, rp, 17, rp + 4, 20, B_PAW_TOP, B_PAW_BOT)
    draw.ellipse([(rp, 18), (rp + 3, 20)], fill=B_PAW_BOT)


def make_bosswarg() -> Image.Image:
    img, draw = _new(24, 20)
    _bosswarg_body(draw)
    return _darken_edge(img)


def make_bosswarg_strip() -> Image.Image:
    """96×20: 4-frame gallop — power stroke / float alternation."""
    frames = []
    # F0: power stroke — front paw forward, rear paw back
    img, draw = _new(24, 20); _bosswarg_body(draw, front_paw_x=4, rear_paw_x=14)
    frames.append(_darken_edge(img))
    # F1: float — paws level, body 1px higher
    img, draw = _new(24, 20); _bosswarg_body(draw, body_lift=1, front_paw_x=2, rear_paw_x=16)
    frames.append(_darken_edge(img))
    # F2: power stroke reversed — front paw back, rear paw forward
    img, draw = _new(24, 20); _bosswarg_body(draw, front_paw_x=2, rear_paw_x=18)
    frames.append(_darken_edge(img))
    # F3: float again
    img, draw = _new(24, 20); _bosswarg_body(draw, body_lift=1, front_paw_x=2, rear_paw_x=16)
    frames.append(_darken_edge(img))
    return _hstack(*frames)


# ---------------------------------------------------------------------------
# ShieldKnight — 12×16, 2-frame walk strip (24×16)
# ---------------------------------------------------------------------------

def _shieldknight_body(draw: ImageDraw.ImageDraw,
                       shield_dx: int = 0, foot_swap: bool = False) -> None:
    # Armor body
    _vgrad(draw, 3, 3, 11, 16, SK_ARMOR_TOP, SK_ARMOR_BOT)
    # Left edge armor highlight
    draw.line([(3, 3), (3, 15)], fill=(*SK_ARMOR_TOP[:3], 255))
    # Helmet
    _vgrad(draw, 2, 0, 10, 5, SK_ARMOR_TOP, SK_ARMOR_BOT)
    # Helmet trim
    draw.rectangle([(2, 0), (9, 0)], fill=SK_TRIM)
    draw.line([(2, 0), (2, 4)], fill=SK_TRIM)
    draw.line([(9, 0), (9, 4)], fill=SK_TRIM)
    # Visor slit
    draw.rectangle([(3, 2), (8, 3)], fill=SK_VISOR)
    # Shield — vertical gradient with metallic look
    sx = shield_dx
    for y in range(4, 13):
        t = (y - 4) / 8
        r = int(SK_SHLD_TOP[0] + (SK_SHLD_BOT[0] - SK_SHLD_TOP[0]) * t)
        g = int(SK_SHLD_TOP[1] + (SK_SHLD_BOT[1] - SK_SHLD_TOP[1]) * t)
        b = int(SK_SHLD_TOP[2] + (SK_SHLD_BOT[2] - SK_SHLD_TOP[2]) * t)
        draw.line([(sx, y), (sx + 2, y)], fill=(r, g, b, 255))
    draw.line([(sx, 4),  (sx + 2, 4)],  fill=SK_TRIM)
    draw.line([(sx, 12), (sx + 2, 12)], fill=SK_TRIM)
    draw.point([(sx + 1, 8)], fill=SK_EMBLEM)
    # Feet
    if not foot_swap:
        draw.rectangle([(3, 13), (6, 15)], fill=SK_ARMOR_BOT)
        draw.rectangle([(7, 14), (10, 15)], fill=SK_ARMOR_BOT)
    else:
        draw.rectangle([(3, 14), (6, 15)], fill=SK_ARMOR_BOT)
        draw.rectangle([(7, 13), (10, 15)], fill=SK_ARMOR_BOT)


def make_shieldknight() -> Image.Image:
    img, draw = _new(12, 16)
    _shieldknight_body(draw)
    return _darken_edge(img)


def make_shieldknight_strip() -> Image.Image:
    """24×16: 2-frame walk."""
    f0_img, f0d = _new(12, 16); _shieldknight_body(f0d)
    f1_img, f1d = _new(12, 16); _shieldknight_body(f1d, shield_dx=1, foot_swap=True)
    return _hstack(_darken_edge(f0_img), _darken_edge(f1_img))


# ---------------------------------------------------------------------------
# SkeletonArcher — 12×16, 2-frame strip (24×16)
# Frame 0 = idle/patrol.  Frame 1 = drawing bow (arm slightly forward).
# Facing RIGHT; engine flips for left.
# ---------------------------------------------------------------------------

def _archer_frame(arm_fwd: bool = False) -> Image.Image:
    img, d = _new(12, 16)

    # Bone-white body (ribcage silhouette)
    _vgrad(d, 3, 4, 9, 12, SA_BONE, SA_BONE_DRK)
    # Rib lines (thin dark horizontals)
    for ry in (5, 7, 9):
        d.line([(4, ry), (8, ry)], fill=SA_BONE_DRK)

    # Hood/skull
    _vgrad(d, 3, 0, 9, 5, SA_HOOD, SA_BONE_DRK)
    # Eye sockets
    d.point([(4, 2)], fill=SA_EYE)
    d.point([(7, 2)], fill=SA_EYE)

    # Bony legs
    d.line([(4, 12), (4, 15)], fill=SA_BONE_DRK)
    d.line([(7, 12), (7, 15)], fill=SA_BONE_DRK)
    # Feet
    d.line([(3, 15), (5, 15)], fill=SA_BONE_DRK)
    d.line([(6, 15), (8, 15)], fill=SA_BONE_DRK)

    # Bow — right side (front arm)
    bx = 9 if not arm_fwd else 10
    d.arc([(bx - 2, 3), (bx + 2, 13)], start=270, end=90, fill=SA_BOW, width=1)
    d.line([(bx - 1, 3), (bx - 1, 13)], fill=SA_STRING)

    return _darken_edge(img)


def make_archer_strip() -> Image.Image:
    """24×16: 2-frame strip — idle + draw."""
    return _hstack(_archer_frame(False), _archer_frame(True))


# ---------------------------------------------------------------------------
# CaveBat — 10×8, 2-frame strip (20×8)
# Frame 0 = wings spread.  Frame 1 = wings half-folded.
# ---------------------------------------------------------------------------

def _bat_frame(fold: bool = False) -> Image.Image:
    img, d = _new(10, 8)

    # Body (center)
    _vgrad(d, 4, 1, 7, 7, CB_BODY, CB_WING)

    # Eyes
    d.point([(4, 2)], fill=CB_EYE)
    d.point([(6, 2)], fill=CB_EYE)

    if not fold:
        # Spread wings
        # Left wing
        d.polygon([(4, 3), (0, 1), (0, 6), (3, 5)], fill=CB_WING)
        d.line([(0, 1), (3, 5)], fill=CB_WING_LT)
        # Right wing
        d.polygon([(6, 3), (10, 1), (10, 6), (7, 5)], fill=CB_WING)
        d.line([(10, 1), (7, 5)], fill=CB_WING_LT)
    else:
        # Half-folded wings (closer to body)
        d.polygon([(4, 3), (1, 2), (1, 6), (3, 5)], fill=CB_WING)
        d.polygon([(6, 3), (9, 2), (9, 6), (7, 5)], fill=CB_WING)

    return _darken_edge(img)


def make_bat_strip() -> Image.Image:
    """20×8: 2-frame strip — wings spread + half-folded."""
    return _hstack(_bat_frame(False), _bat_frame(True))


# ---------------------------------------------------------------------------
# Slime — 10×8, 2-frame hop strip (20×8)
# ---------------------------------------------------------------------------

SL_DARK  = ( 60, 130,  70, 255)
SL_BODY  = ( 90, 180, 110, 255)
SL_LITE  = (140, 220, 150, 255)
SL_EYE   = ( 20,  40,  20, 255)


def _slime_frame(squash: int) -> Image.Image:
    """squash: 0 = full height, 1 = compressed."""
    img, draw = _new(10, 8)
    top = squash
    # Outer rim
    draw.ellipse([(0, top + 1), (9, 7)], fill=SL_DARK)
    # Body
    draw.ellipse([(1, top + 2), (8, 6)], fill=SL_BODY)
    # Highlight strip
    draw.line([(2, top + 2), (4, top + 2)], fill=SL_LITE)
    # Eyes
    draw.point([(3, top + 3)], fill=SL_EYE)
    draw.point([(6, top + 3)], fill=SL_EYE)
    return _darken_edge(img)


def make_slime_strip() -> Image.Image:
    return _hstack(_slime_frame(0), _slime_frame(2))


# ---------------------------------------------------------------------------
# SmallSlime — 6×5, 2-frame strip (12×5)
# ---------------------------------------------------------------------------

def _small_slime_frame(squash: int) -> Image.Image:
    img, draw = _new(6, 5)
    top = squash
    draw.ellipse([(0, top), (5, 4)], fill=SL_DARK)
    draw.ellipse([(1, top + 1), (4, 3)], fill=SL_LITE)
    draw.point([(2, top + 1)], fill=SL_EYE)
    draw.point([(3, top + 1)], fill=SL_EYE)
    return _darken_edge(img)


def make_small_slime_strip() -> Image.Image:
    return _hstack(_small_slime_frame(0), _small_slime_frame(1))


# ---------------------------------------------------------------------------
# SpitterPlant — 12×12, 2-frame strip (24×12)
# ---------------------------------------------------------------------------

SP_POT_TOP  = (110,  70,  45, 255)
SP_POT_BOT  = ( 75,  45,  28, 255)
SP_STEM     = ( 40, 105,  55, 255)
SP_BUD_DRK  = (140,  40, 130, 255)
SP_BUD_LITE = (210, 105, 180, 255)


def _spitter_frame(open_mouth: bool) -> Image.Image:
    img, draw = _new(12, 12)
    # Pot
    _vgrad(draw, 2, 8, 10, 12, SP_POT_TOP, SP_POT_BOT)
    draw.rectangle([(1, 7), (10, 8)], fill=SP_POT_TOP)
    # Stem
    draw.rectangle([(5, 4), (6, 8)], fill=SP_STEM)
    # Leaves
    draw.point([(3, 6)], fill=SP_STEM)
    draw.point([(8, 6)], fill=SP_STEM)
    # Bud (open or closed)
    if open_mouth:
        # Mouth open — show inner color
        draw.ellipse([(2, 0), (9, 5)], fill=SP_BUD_DRK)
        draw.ellipse([(3, 1), (8, 4)], fill=(240, 240, 100, 255))
        draw.point([(5, 2)], fill=(40, 0, 0, 255))
        draw.point([(6, 2)], fill=(40, 0, 0, 255))
    else:
        draw.ellipse([(2, 0), (9, 5)], fill=SP_BUD_DRK)
        draw.ellipse([(3, 1), (8, 4)], fill=SP_BUD_LITE)
        draw.point([(5, 2)], fill=SP_BUD_DRK)
    return _darken_edge(img)


def make_spitter_strip() -> Image.Image:
    return _hstack(_spitter_frame(False), _spitter_frame(True))


# ---------------------------------------------------------------------------
# MimicChest — 14×12, 3-frame strip (42×12): sleeping + 2× awake
# ---------------------------------------------------------------------------

MC_WOOD_DRK = ( 75,  48,  30, 255)
MC_WOOD     = (115,  76,  46, 255)
MC_WOOD_LT  = (160, 110,  64, 255)
MC_BAND     = (210, 170,  80, 255)
MC_EYE      = (255,  70,  70, 255)
MC_TOOTH    = (240, 240, 220, 255)


def _mimic_sleep() -> Image.Image:
    img, draw = _new(14, 12)
    # Chest body
    _vgrad(draw, 0, 5, 14, 12, MC_WOOD, MC_WOOD_DRK)
    # Lid
    draw.rectangle([(0, 3), (13, 6)], fill=MC_WOOD_LT)
    # Bands
    draw.line([(0, 7),  (13, 7)],  fill=MC_BAND)
    draw.line([(0, 10), (13, 10)], fill=MC_BAND)
    # Lock
    draw.rectangle([(6, 5), (7, 8)], fill=MC_BAND)
    draw.point([(6, 6)], fill=MC_WOOD_DRK)
    return _darken_edge(img)


def _mimic_awake(open_jaw: bool) -> Image.Image:
    img, draw = _new(14, 12)
    # Body (lower)
    _vgrad(draw, 0, 6, 14, 12, MC_WOOD, MC_WOOD_DRK)
    # Upper jaw lifted away
    top = 0 if open_jaw else 2
    draw.rectangle([(0, top), (13, top + 3)], fill=MC_WOOD_LT)
    draw.line([(0, top + 3), (13, top + 3)], fill=MC_BAND)
    # Teeth
    if open_jaw:
        for tx in (1, 4, 7, 10):
            draw.rectangle([(tx, top + 3), (tx + 1, top + 4)], fill=MC_TOOTH)
            draw.rectangle([(tx, 5), (tx + 1, 6)], fill=MC_TOOTH)
    else:
        for tx in (2, 6, 10):
            draw.rectangle([(tx, top + 3), (tx + 1, top + 4)], fill=MC_TOOTH)
    # Eyes
    draw.point([(3, 7)], fill=MC_EYE)
    draw.point([(10, 7)], fill=MC_EYE)
    return _darken_edge(img)


def make_mimic_strip() -> Image.Image:
    return _hstack(_mimic_sleep(), _mimic_awake(False), _mimic_awake(True))


# ---------------------------------------------------------------------------
# Gem — 8×8, single-frame "strip" per color
# ---------------------------------------------------------------------------

GEM_COLORS = {
    "blue":   ((30,  90, 200, 255), (130, 200, 255, 255)),
    "red":    ((180, 40,  60, 255), (255, 140, 160, 255)),
    "green":  ((30, 160,  80, 255), (140, 240, 170, 255)),
    "purple": ((110, 50, 180, 255), (210, 160, 255, 255)),
}


def _gem_frame(dark: tuple, light: tuple) -> Image.Image:
    img, draw = _new(8, 8)
    # Faceted diamond
    draw.polygon([(4, 0), (7, 4), (4, 7), (0, 4)], fill=dark)
    draw.polygon([(4, 2), (6, 4), (4, 6), (2, 4)], fill=light)
    # Top sparkle
    draw.point([(3, 1)], fill=(255, 255, 255, 255))
    return img


def make_gem_strip(color: str) -> Image.Image:
    dark, light = GEM_COLORS[color]
    # Single-frame strip so get_strip_frame still finds it
    return _gem_frame(dark, light)


# ---------------------------------------------------------------------------
# Spring — 12×6, 2-frame strip (24×6): extended + compressed
# ---------------------------------------------------------------------------

SPR_DARK = ( 80,  80,  30, 255)
SPR_BODY = (160, 160,  60, 255)
SPR_LITE = (220, 220, 110, 255)
SPR_BASE = ( 60,  50,  20, 255)


def _spring_frame(compressed: bool) -> Image.Image:
    img, draw = _new(12, 6)
    # Base plate
    draw.rectangle([(0, 4), (11, 5)], fill=SPR_BASE)
    if compressed:
        # Squashed spring
        draw.rectangle([(1, 3), (10, 4)], fill=SPR_DARK)
        draw.rectangle([(2, 2), (9, 3)], fill=SPR_BODY)
    else:
        # Extended spring + cap
        draw.rectangle([(2, 1), (9, 4)], fill=SPR_DARK)
        draw.rectangle([(3, 2), (8, 3)], fill=SPR_LITE)
        draw.rectangle([(1, 0), (10, 1)], fill=SPR_BODY)
    return _darken_edge(img)


def make_spring_strip() -> Image.Image:
    return _hstack(_spring_frame(False), _spring_frame(True))


# ---------------------------------------------------------------------------
# Platform — 32×8, single-frame strip
# ---------------------------------------------------------------------------

PL_DARK = ( 60,  50,  42, 255)
PL_BODY = (110, 100,  90, 255)
PL_LITE = (170, 160, 140, 255)


def _platform_frame() -> Image.Image:
    img, draw = _new(32, 8)
    _vgrad(draw, 0, 1, 32, 8, PL_BODY, PL_DARK)
    draw.rectangle([(0, 0), (31, 1)], fill=PL_LITE)
    # Mortar joints
    for bx in range(6, 32, 8):
        draw.line([(bx, 2), (bx, 6)], fill=PL_DARK)
    return _darken_edge(img)


def make_platform_strip() -> Image.Image:
    return _platform_frame()


# ---------------------------------------------------------------------------
# Coin — 8×8, 4-frame spin strip (32×8)
# ---------------------------------------------------------------------------

def _coin_frame(bbox_x0: int, bbox_x1: int,
                face_col: tuple, shine_col: tuple | None) -> Image.Image:
    img, draw = _new(8, 8)
    # Outer rim
    draw.ellipse([(bbox_x0 - 1, 0), (bbox_x1 + 1, 7)], fill=COIN_RIM)
    # Face
    draw.ellipse([(bbox_x0, 1), (bbox_x1, 6)], fill=face_col)
    # Shine
    if shine_col and bbox_x1 - bbox_x0 >= 2:
        draw.point([(bbox_x0 + 1, 2)], fill=shine_col)
    return _darken_edge(img)


def make_coin() -> Image.Image:
    return _coin_frame(1, 6, COIN_FACE, COIN_SHINE)


def make_coin_strip() -> Image.Image:
    """32×8: 4-frame spin — full → tilt → edge → tilt back."""
    f0 = _coin_frame(1, 6, COIN_FACE,  COIN_SHINE)   # full face
    f1 = _coin_frame(2, 5, COIN_FACE,  COIN_SHINE)   # slight tilt
    # Edge-on: just a thin rect
    f2, d2 = _new(8, 8)
    d2.rectangle([(3, 1), (4, 6)], fill=COIN_EDGE)
    f2 = _darken_edge(f2)
    f3 = _coin_frame(2, 5, COIN_SHINE, None)           # bright returning side
    return _hstack(f0, f1, f2, f3)


# ---------------------------------------------------------------------------
# Heart — 9×9
# ---------------------------------------------------------------------------

def make_heart() -> Image.Image:
    img, draw = _new(9, 9)
    # Heart silhouette using pixel list (classic heart shape)
    pixels = [
        (1,0),(2,0),(5,0),(6,0),(7,0),
        (0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),
        (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2),
        (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),(7,3),(8,3),
        (1,4),(2,4),(3,4),(4,4),(5,4),(6,4),(7,4),
        (2,5),(3,5),(4,5),(5,5),(6,5),
        (3,6),(4,6),(5,6),
        (4,7),
    ]
    # Draw dark base first, then lighter on top
    for x, y in pixels:
        # gradient: darker at bottom
        t = y / 7
        r = int(HEART_RED[0] + (HEART_DARK[0] - HEART_RED[0]) * t)
        g = int(HEART_RED[1] + (HEART_DARK[1] - HEART_RED[1]) * t)
        b = int(HEART_RED[2] + (HEART_DARK[2] - HEART_RED[2]) * t)
        draw.point([(x, y)], fill=(r, g, b, 255))
    # Pink highlights on bumps
    draw.point([(1, 1)], fill=HEART_PINK)
    draw.point([(6, 1)], fill=HEART_PINK)
    return _darken_edge(img)


# ---------------------------------------------------------------------------
# Weapon pickup — 10×10 (bow + arrow)
# ---------------------------------------------------------------------------

def make_weapon() -> Image.Image:
    img, draw = _new(10, 10)
    # Bow arc — left side curve using arc
    draw.arc([(0, 1), (4, 8)], start=270, end=90, fill=BOW_BROWN, width=1)
    # Bowstring — straight line right of bow
    draw.line([(2, 1), (2, 8)], fill=STRING_CYAN)
    # Arrow shaft
    draw.line([(2, 4), (9, 4)], fill=BOW_BROWN)
    # Arrowhead
    draw.line([(7, 2), (9, 4)], fill=ARROW_BLUE)
    draw.line([(7, 6), (9, 4)], fill=ARROW_BLUE)
    # Arrow fletching (back end)
    draw.line([(2, 3), (0, 2)], fill=BOW_BROWN)
    draw.line([(2, 5), (0, 6)], fill=BOW_BROWN)
    return img


# ---------------------------------------------------------------------------
# Bonus pickups — shield (10×10), nuke (12×12), fruit (10×10)
# ---------------------------------------------------------------------------

def make_shield() -> Image.Image:
    """Blue heater shield with a cross emblem — the 10 s invulnerability bonus."""
    img, draw = _new(10, 10)
    top, bot = (90, 160, 245), (35, 80, 170)
    # Shield body: filled heater shape via vertical gradient inside a polygon mask
    outline = [(5, 0), (9, 1), (9, 5), (5, 9), (1, 5), (1, 1)]
    draw.polygon(outline, fill=bot)
    # Lighter inner sheen
    draw.polygon([(5, 1), (8, 2), (8, 5), (5, 8), (2, 5), (2, 2)], fill=top)
    # Cross emblem
    draw.line([(5, 2), (5, 7)], fill=(235, 245, 255))
    draw.line([(3, 4), (7, 4)], fill=(235, 245, 255))
    return _darken_edge(img)


def make_nuke() -> Image.Image:
    """Dark bomb sphere with a lit fuse — the screen-clearing nuke bonus."""
    img, draw = _new(12, 12)
    # Bomb body
    draw.ellipse([(1, 3), (9, 11)], fill=(34, 34, 44))
    draw.ellipse([(1, 3), (9, 11)], outline=(95, 95, 120))
    # Shine highlight
    draw.point([(3, 5)], fill=(150, 150, 175))
    draw.point([(4, 5)], fill=(120, 120, 150))
    # Fuse cap + fuse
    draw.rectangle([(5, 1), (6, 3)], fill=(120, 95, 55))
    draw.line([(6, 1), (9, 0)], fill=(150, 110, 60))
    # Spark
    draw.point([(9, 0)], fill=(255, 210, 80))
    draw.point([(10, 1)], fill=(255, 150, 40))
    return _darken_edge(img)


def make_fruit() -> Image.Image:
    """A bright apple — used both as a pickup and as the enemy-fruit overlay."""
    img, draw = _new(10, 10)
    # Apple body
    draw.ellipse([(1, 3), (8, 9)], fill=(205, 45, 55))
    draw.ellipse([(1, 3), (8, 9)], outline=(150, 25, 35))
    # Glossy highlight
    draw.ellipse([(3, 4), (5, 6)], fill=(255, 150, 150))
    # Stem + leaf
    draw.line([(5, 1), (5, 3)], fill=(110, 70, 30))
    draw.polygon([(6, 1), (9, 0), (7, 3)], fill=(70, 175, 75))
    return _darken_edge(img)


# ---------------------------------------------------------------------------
# Projectile — 6×3
# ---------------------------------------------------------------------------

def make_projectile() -> Image.Image:
    img, draw = _new(6, 3)
    # Gradient bolt: bright tip → dark tail
    for x in range(6):
        t = 1.0 - x / 5
        r = int(PROJ_DARK[0] + (PROJ_LITE[0] - PROJ_DARK[0]) * t)
        g = int(PROJ_DARK[1] + (PROJ_LITE[1] - PROJ_DARK[1]) * t)
        b = int(PROJ_DARK[2] + (PROJ_LITE[2] - PROJ_DARK[2]) * t)
        draw.line([(x, 0), (x, 2)], fill=(r, g, b, 255))
    # Extra bright tip pixel
    draw.point([(5, 1)], fill=PROJ_LITE)
    return _darken_edge(img)


# ---------------------------------------------------------------------------
# Player attack strip — 36×18 (3 frames: raise / extend / follow-through)
# ---------------------------------------------------------------------------

# sword palette
SWORD_BLADE  = (200, 210, 220, 255)   # steel-grey blade
SWORD_EDGE   = (240, 248, 255, 255)   # bright edge highlight
SWORD_GUARD  = (180, 140, 60, 255)    # gold guard
SWORD_GRIP   = (90, 60, 38, 255)      # brown grip


def _player_attack_frame(frame: int) -> Image.Image:
    """Draw one attack frame (0=raise, 1=extend/strike, 2=follow-through)."""
    img, draw = _new(P_SPR_W, P_SPR_H)

    # Shared body: idle stance
    _player_profile(draw, front_leg_x=5, rear_leg_x=2, staff_dx=0)

    if frame == 0:
        # Sword raised — vertical above head (cols 9-10, rows 0-6)
        draw.rectangle([(9, 0), (10, 6)], fill=SWORD_BLADE)
        draw.point([(10, 0)], fill=SWORD_EDGE)
        draw.rectangle([(8, 6), (11, 7)], fill=SWORD_GUARD)
        draw.rectangle([(9, 7), (10, 9)], fill=SWORD_GRIP)
    elif frame == 1:
        # Sword horizontal — extended forward (rows 6-7, cols 11 overflows to canvas edge)
        draw.rectangle([(9, 6), (11, 7)], fill=SWORD_BLADE)
        draw.point([(11, 6)], fill=SWORD_EDGE)
        draw.rectangle([(8, 7), (9, 9)], fill=SWORD_GUARD)
        draw.rectangle([(7, 7), (9, 8)], fill=SWORD_GRIP)
    else:
        # Sword angled down — follow-through (rows 8-11, cols 8-10)
        draw.line([(10, 8), (8, 11)], fill=SWORD_BLADE, width=2)
        draw.rectangle([(9, 7), (10, 8)], fill=SWORD_GUARD)
        draw.rectangle([(8, 7), (9, 8)], fill=SWORD_GRIP)

    return _darken_edge(img)


def make_player_attack_strip() -> Image.Image:
    """36×18: 3-frame melee swing strip."""
    return _hstack(
        _player_attack_frame(0),
        _player_attack_frame(1),
        _player_attack_frame(2),
    )


# ---------------------------------------------------------------------------
# GoblinKing — 28×24, 3-frame strip (84×24): idle / charge / rage
# ---------------------------------------------------------------------------

GK_BODY_DRK = ( 55,  78,  30, 255)
GK_BODY     = ( 80, 110,  45, 255)
GK_BODY_LT  = (100, 140,  55, 255)
GK_CROWN    = (200, 160,  40, 255)
GK_ARMOR    = ( 70,  55,  90, 255)
GK_EYE_N    = (255, 200,  40, 255)   # phase-1 eye
GK_EYE_R    = (255,  50,  50, 255)   # phase-2 rage eye
GK_SASH     = (180,  40,  40, 255)


def _goblin_king_frame(frame: int) -> Image.Image:
    """frame 0=idle, 1=charging (lunge), 2=rage (red eyes, darker body)."""
    img, draw = _new(28, 24)

    rage = (frame == 2)
    lunge = (frame == 1)

    body_col = (GK_BODY_DRK if rage else GK_BODY)
    body_lt  = ((65, 90, 35, 255) if rage else GK_BODY_LT)

    # Legs
    lx_l, lx_r = (4, 18) if lunge else (6, 16)
    _vgrad(draw, lx_l, 18, lx_l + 5, 24, GK_BODY, GK_BODY_DRK)
    _vgrad(draw, lx_r, 18, lx_r + 5, 24, GK_BODY, GK_BODY_DRK)
    # Feet
    draw.rectangle([(lx_l - 1, 22), (lx_l + 5, 23)], fill=GK_BODY_DRK)
    draw.rectangle([(lx_r - 1, 22), (lx_r + 5, 23)], fill=GK_BODY_DRK)

    # Body / torso
    body_y = 8 if not lunge else 9
    _vgrad(draw, 4, body_y, 24, 20, body_col, GK_BODY_DRK)
    # Shoulder armor plates
    draw.rectangle([(2, body_y), (8, body_y + 4)], fill=GK_ARMOR)
    draw.rectangle([(20, body_y), (26, body_y + 4)], fill=GK_ARMOR)
    # Sash across torso
    draw.line([(4, 14), (23, 14)], fill=GK_SASH)

    # Head
    head_y = 2 if not lunge else 3
    _vgrad(draw, 8, head_y, 20, head_y + 8, body_lt, body_col)
    # Jaw (lower protrusion for goblin look)
    draw.rectangle([(9, head_y + 6), (19, head_y + 10)], fill=body_col)
    # Teeth
    for tx in (10, 13, 16):
        draw.rectangle([(tx, head_y + 8), (tx + 1, head_y + 9)], fill=(240, 240, 220, 255))

    # Eyes
    eye_col = GK_EYE_R if rage else GK_EYE_N
    draw.rectangle([(10, head_y + 2), (12, head_y + 4)], fill=eye_col)
    draw.rectangle([(16, head_y + 2), (18, head_y + 4)], fill=eye_col)
    if rage:
        # Glow halo around eyes
        for ex, ey in [(11, head_y + 2), (17, head_y + 2)]:
            draw.ellipse([(ex - 2, ey - 1), (ex + 2, ey + 3)], outline=(255, 100, 50, 120))

    # Crown — 3 spikes
    crown_y = head_y - 4
    for i in range(3):
        cx = 10 + i * 4
        draw.polygon(
            [(cx, head_y), (cx + 2, crown_y), (cx + 4, head_y)],
            fill=GK_CROWN,
        )
    # Crown band
    draw.rectangle([(8, head_y), (20, head_y + 2)], fill=GK_CROWN)

    # Arms
    arm_ext = 2 if lunge else 0
    # Left arm
    draw.rectangle([(0, body_y + 2), (4 + arm_ext, body_y + 6)], fill=body_col)
    draw.rectangle([(0, body_y + 6), (3 + arm_ext, body_y + 9)], fill=GK_BODY_DRK)
    # Right arm
    draw.rectangle([(24 - arm_ext, body_y + 2), (28, body_y + 6)], fill=body_col)
    draw.rectangle([(25 - arm_ext, body_y + 6), (28, body_y + 9)], fill=GK_BODY_DRK)

    return _darken_edge(img)


def make_goblin_king_strip() -> Image.Image:
    """84×24: 3-frame strip — idle + charge + rage."""
    return _hstack(
        _goblin_king_frame(0),
        _goblin_king_frame(1),
        _goblin_king_frame(2),
    )


# ---------------------------------------------------------------------------
# Night King — final boss (icy palette), 30×26, 3 frames
# ---------------------------------------------------------------------------

NK_BODY_DRK = ( 50,  72, 110, 255)
NK_BODY     = ( 90, 125, 165, 255)
NK_BODY_LT  = (140, 175, 205, 255)
NK_CROWN    = (235, 245, 255, 255)   # white ice crown
NK_ARMOR    = ( 70,  95, 140, 255)
NK_EYE_N    = ( 90, 160, 230, 255)   # phase-1 eye
NK_EYE_R    = (140, 230, 255, 255)   # phase-2 frost eye
NK_CAPE     = ( 40,  60,  95, 255)


def _night_king_frame(frame: int) -> Image.Image:
    """frame 0=idle, 1=charging (lunge), 2=frost-rage (bright eyes, icy aura)."""
    img, draw = _new(30, 26)

    rage  = (frame == 2)
    lunge = (frame == 1)

    body_col = NK_BODY
    body_lt  = (NK_BODY_LT if not rage else (175, 210, 235, 255))

    # Frost aura when raging
    if rage:
        for ox, oy in [(2, 6), (27, 6), (4, 22), (25, 22)]:
            draw.ellipse([(ox - 1, oy - 1), (ox + 1, oy + 1)], fill=(170, 225, 255, 160))

    # Legs
    lx_l, lx_r = (5, 19) if lunge else (7, 17)
    _vgrad(draw, lx_l, 20, lx_l + 5, 26, NK_BODY, NK_BODY_DRK)
    _vgrad(draw, lx_r, 20, lx_r + 5, 26, NK_BODY, NK_BODY_DRK)
    # Feet
    draw.rectangle([(lx_l - 1, 24), (lx_l + 5, 25)], fill=NK_BODY_DRK)
    draw.rectangle([(lx_r - 1, 24), (lx_r + 5, 25)], fill=NK_BODY_DRK)

    # Cape behind torso
    draw.polygon([(4, 9), (26, 9), (24, 22), (6, 22)], fill=NK_CAPE)

    # Body / torso
    body_y = 9 if not lunge else 10
    _vgrad(draw, 5, body_y, 25, 21, body_col, NK_BODY_DRK)
    # Shoulder armor plates
    draw.rectangle([(3, body_y), (9, body_y + 4)], fill=NK_ARMOR)
    draw.rectangle([(21, body_y), (27, body_y + 4)], fill=NK_ARMOR)

    # Head
    head_y = 2 if not lunge else 3
    _vgrad(draw, 9, head_y, 21, head_y + 8, body_lt, body_col)

    # Eyes
    eye_col = NK_EYE_R if rage else NK_EYE_N
    draw.rectangle([(11, head_y + 2), (13, head_y + 4)], fill=eye_col)
    draw.rectangle([(17, head_y + 2), (19, head_y + 4)], fill=eye_col)
    if rage:
        for ex, ey in [(12, head_y + 2), (18, head_y + 2)]:
            draw.ellipse([(ex - 2, ey - 1), (ex + 2, ey + 3)], outline=(170, 235, 255, 140))

    # Crown — 3 ice spikes
    crown_y = head_y - 4
    for i in range(3):
        cx = 11 + i * 4
        draw.polygon(
            [(cx, head_y), (cx + 2, crown_y), (cx + 4, head_y)],
            fill=NK_CROWN,
        )
    # Crown band
    draw.rectangle([(9, head_y), (21, head_y + 2)], fill=NK_CROWN)

    # Arms
    arm_ext = 2 if lunge else 0
    draw.rectangle([(1, body_y + 2), (5 + arm_ext, body_y + 6)], fill=body_col)
    draw.rectangle([(1, body_y + 6), (4 + arm_ext, body_y + 9)], fill=NK_BODY_DRK)
    draw.rectangle([(25 - arm_ext, body_y + 2), (29, body_y + 6)], fill=body_col)
    draw.rectangle([(26 - arm_ext, body_y + 6), (29, body_y + 9)], fill=NK_BODY_DRK)

    return _darken_edge(img)


def make_night_king_strip() -> Image.Image:
    """90×26: 3-frame strip — idle + charge + frost-rage."""
    return _hstack(
        _night_king_frame(0),
        _night_king_frame(1),
        _night_king_frame(2),
    )


# ---------------------------------------------------------------------------
# Spike hazard — 16×8 single-frame (3 upward triangles)
# ---------------------------------------------------------------------------

SPIKE_STEEL  = (122, 128, 128, 255)
SPIKE_DARK   = (58,  64,  64,  255)
SPIKE_SHINE  = (180, 188, 190, 255)


def make_spike() -> Image.Image:
    """16×8 spike strip: three upward steel triangles."""
    img, draw = _new(16, 8)
    # Three triangles, each 5px wide with 1px gap
    for i in range(3):
        bx = 1 + i * 5
        tip_x = bx + 2
        # Filled triangle
        draw.polygon(
            [(bx, 7), (bx + 4, 7), (tip_x, 0)],
            fill=SPIKE_STEEL,
        )
        # Dark outline
        draw.polygon(
            [(bx, 7), (bx + 4, 7), (tip_x, 0)],
            outline=SPIKE_DARK,
        )
        # Bright edge highlight on left face
        draw.line([(bx, 7), (tip_x, 0)], fill=SPIKE_SHINE)
    return _darken_edge(img)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Writing sprites to {OUT}/")

    singles = [
        ("player",             make_player),
        ("enemy_goblinkin",    make_goblinkin),
        ("enemy_wraith",       make_wraith),
        ("enemy_bosswarg",     make_bosswarg),
        ("enemy_shieldknight", make_shieldknight),
        ("item_coin",          make_coin),
        ("item_heart",         make_heart),
        ("item_weapon",        make_weapon),
        ("item_shield",        make_shield),
        ("item_nuke",          make_nuke),
        ("item_fruit",         make_fruit),
        ("projectile",         make_projectile),
        ("spike",              make_spike),
    ]

    strips = [
        ("player_strip",             make_player_strip),
        ("enemy_goblinkin_strip",    make_goblinkin_strip),
        ("enemy_wraith_strip",       make_wraith_strip),
        ("enemy_bosswarg_strip",     make_bosswarg_strip),
        ("enemy_shieldknight_strip", make_shieldknight_strip),
        ("enemy_archer_strip",       make_archer_strip),
        ("enemy_bat_strip",          make_bat_strip),
        ("enemy_slime_strip",        make_slime_strip),
        ("enemy_small_slime_strip",  make_small_slime_strip),
        ("enemy_spitter_strip",      make_spitter_strip),
        ("enemy_mimic_strip",        make_mimic_strip),
        ("enemy_goblin_king_strip",  make_goblin_king_strip),
        ("enemy_night_king_strip",   make_night_king_strip),
        ("item_coin_strip",          make_coin_strip),
        ("item_gem_blue_strip",      lambda: make_gem_strip("blue")),
        ("item_gem_red_strip",       lambda: make_gem_strip("red")),
        ("item_gem_green_strip",     lambda: make_gem_strip("green")),
        ("item_gem_purple_strip",    lambda: make_gem_strip("purple")),
        ("spring_strip",             make_spring_strip),
        ("platform_strip",           make_platform_strip),
        ("player_attack_strip",      make_player_attack_strip),
    ]

    for name, fn in singles:
        _save(fn(), name)

    print("Writing strips:")
    for name, fn in strips:
        _save(fn(), name)

    print(f"Done — {len(singles)} sprites + {len(strips)} strips written.")


if __name__ == "__main__":
    main()
