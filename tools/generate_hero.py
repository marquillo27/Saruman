"""Generate the 24x36 hero (Aldric the Grey) animation strip.

The look follows ComfyUI design candidate 6 (seed 1105: grey wizard, long
wide cloak, white beard, crooked wooden staff). A straight downscale of that
render loses the face, so the sprite is built from parts (cloak, hood, face,
beard, arm, staff, boots) at native resolution and posed per frame. Every
frame gets the same automatic 1 px outline, which keeps the animation
consistent.

Usage:
    python tools/generate_hero.py          # writes assets/sprites/hero_strip.png
    python tools/generate_hero.py --preview out.png   # also an 8x preview sheet
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "assets" / "sprites" / "hero_strip.png"

W, H = 24, 36

# Palette sampled from the ComfyUI render
OUTLINE = (34, 26, 34, 255)
CLOAK   = (186, 178, 180, 255)
CLOAK_M = (156, 147, 152, 255)
CLOAK_D = (118, 110, 118, 255)
HOOD    = (206, 200, 202, 255)
HOOD_D  = (160, 152, 158, 255)
SKIN    = (232, 172, 142, 255)
SKIN_D  = (196, 128, 106, 255)
EYE     = (40, 30, 44, 255)
BEARD   = (244, 242, 240, 255)
BEARD_D = (196, 194, 202, 255)
STAFF   = (150, 104, 70, 255)
STAFF_D = (92, 52, 32, 255)
BOOT    = (81, 40, 28, 255)
MAGIC   = (170, 220, 255, 255)
MAGIC_D = (110, 160, 230, 255)


@dataclass
class Pose:
    bob:    int = 0          # whole body shifted down (breathing / steps)
    lean:   int = 0          # head + shoulders shifted forward
    hem_dx: int = 0          # cloak hem sway (negative = trailing behind)
    hem_dy: int = 0          # cloak hem lifted (jump / fall)
    feet:   tuple = ((7, 0), (12, 0))   # (x, lift) of back and front boot
    staff:  float = 8.0      # staff angle in degrees, 0 = upright, + = tip forward
    hand:   tuple = (16, 18) # hand position holding the staff
    swoosh: bool = False     # magic arc in front (attack strike frame)
    grip:   tuple = (15, 16) # staff length above / below the hand (choke up to swing)


# Frame order in the strip (indices used by Player.draw)
POSES: list[Pose] = [
    # 0-3 idle (breathing)
    Pose(), Pose(), Pose(bob=1, hem_dx=0), Pose(bob=1, hem_dx=-1),
    # 4-9 walk cycle
    Pose(feet=((5, 0), (14, 0)), hem_dx=-1, staff=14),
    Pose(bob=1, feet=((7, 1), (13, 0)), hem_dx=0, staff=10),
    Pose(feet=((9, 0), (11, 2)), hem_dx=1, staff=4),
    Pose(feet=((14, 0), (5, 0)), hem_dx=1, staff=0),
    Pose(bob=1, feet=((13, 0), (7, 1)), hem_dx=0, staff=4),
    Pose(feet=((11, 2), (9, 0)), hem_dx=-1, staff=10),
    # 10 jump (rising): hem trails down/back, boots tucked
    Pose(hem_dx=-2, hem_dy=-1, feet=((6, 3), (12, 4)), staff=20, hand=(16, 16)),
    # 11 fall: cloak billows up, staff raised
    Pose(hem_dx=-1, hem_dy=4, feet=((7, 1), (12, 2)), staff=-12, hand=(16, 15)),
    # 12-14 attack: wind-up, swing, strike with magic arc
    Pose(lean=-1, staff=-55, hand=(14, 14), hem_dx=-1),
    Pose(lean=1, staff=25, hand=(16, 13), hem_dx=0, grip=(11, 12)),
    Pose(lean=2, staff=96, hand=(12, 17), hem_dx=1, feet=((6, 0), (14, 0)), grip=(10, 5)),
    # 15 wall slide: hand on the wall, cloak dragged upward
    Pose(lean=1, hem_dx=-2, hem_dy=3, feet=((9, 1), (14, 3)), staff=-25, hand=(18, 12)),
]


def _poly(d: ImageDraw.ImageDraw, pts, fill) -> None:
    d.polygon([(round(x), round(y)) for x, y in pts], fill=fill)


def _draw_staff(d: ImageDraw.ImageDraw, hand, angle_deg: float, bob: int,
                grip: tuple = (15, 16)) -> None:
    hx, hy = hand[0], hand[1] + bob
    a      = math.radians(angle_deg)
    ux, uy = math.sin(a), -math.cos(a)            # unit vector toward the tip
    top    = (hx + ux * grip[0], hy + uy * grip[0])
    bottom = (hx - ux * grip[1], hy - uy * grip[1])
    d.line([bottom, top], fill=STAFF, width=2)
    d.line([(bottom[0] + 1, bottom[1]), (top[0] + 1, top[1])], fill=STAFF_D, width=1)
    # Crook: short hook bending back from the tip
    px, py = -uy, ux                              # perpendicular (backward side)
    c1 = (top[0] - px * 2 + ux * 1, top[1] - py * 2 + uy * 1)
    c2 = (top[0] - px * 3 - ux * 1, top[1] - py * 3 - uy * 1)
    d.line([top, c1, c2], fill=STAFF, width=2)


def _draw_frame(p: Pose) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    b, l = p.bob, p.lean
    hem_y = 33 - p.hem_dy

    # Boots (behind the cloak hem)
    for fx, lift in p.feet:
        d.rectangle([fx, 33 - lift, fx + 3, 34 - lift], fill=BOOT)

    # Staff behind the body when held back (wind-up), else in front later
    staff_behind = p.staff < -30
    if staff_behind:
        _draw_staff(d, p.hand, p.staff, b, p.grip)

    # Cloak: shoulders -> wide hem, back side darker, a fold line in front
    sh_y = 11 + b
    _poly(d, [(6 + l, sh_y), (15 + l, sh_y), (18 + p.hem_dx, hem_y), (3 + p.hem_dx, hem_y)], CLOAK)
    _poly(d, [(6 + l, sh_y), (9 + l, sh_y), (6 + p.hem_dx, hem_y), (3 + p.hem_dx, hem_y)], CLOAK_M)
    d.line([(12 + l, sh_y + 4), (13 + p.hem_dx, hem_y - 1)], fill=CLOAK_M)
    d.line([(3 + p.hem_dx, hem_y), (18 + p.hem_dx, hem_y)], fill=CLOAK_D)

    # Hood + head
    hx = 7 + l
    hy = 2 + b
    d.ellipse([hx, hy, hx + 8, hy + 10], fill=HOOD)
    d.rectangle([hx, hy + 4, hx + 2, hy + 10], fill=HOOD_D)        # hood back shade
    # Face (front, right side), brow, eye, nose
    d.rectangle([hx + 5, hy + 3, hx + 8, hy + 7], fill=SKIN)
    d.point((hx + 9, hy + 5), fill=SKIN)                              # nose
    d.point((hx + 9, hy + 6), fill=SKIN_D)
    d.line([(hx + 5, hy + 3), (hx + 8, hy + 3)], fill=BEARD)          # white brow
    d.point((hx + 7, hy + 4), fill=EYE)
    d.point((hx + 5, hy + 6), fill=SKIN_D)                            # cheek shade
    # Beard flowing over the chest
    _poly(d, [(hx + 4, hy + 7), (hx + 9, hy + 7), (hx + 8, hy + 13), (hx + 6, hy + 15), (hx + 4, hy + 11)], BEARD)
    d.line([(hx + 5, hy + 9), (hx + 6, hy + 14)], fill=BEARD_D)

    if not staff_behind:
        _draw_staff(d, p.hand, p.staff, b, p.grip)

    # Sleeve from the shoulder to the hand, then the hand over the staff
    sx, sy = 12 + l, 13 + b
    hxx, hyy = p.hand[0], p.hand[1] + b
    d.line([(sx, sy), (hxx, hyy)], fill=CLOAK_M, width=3)
    d.line([(sx, sy - 1), (hxx, hyy - 1)], fill=CLOAK, width=1)
    d.rectangle([hxx - 1, hyy - 1, hxx, hyy], fill=SKIN)

    if p.swoosh:
        # Magic arc sweeping down in front of the staff tip
        cx, cy = hxx + 8, hyy
        for i, rad in enumerate((6, 7)):
            d.arc([cx - rad, cy - rad, cx + rad, cy + rad], 300, 420,
                  fill=MAGIC if i else MAGIC_D)

    return _outline(img)


OUTLINE_MODE = "selout"   # "dark": near-black line, "selout": darkened neighbour colour, "none"


def _outline(img: Image.Image, mode: str | None = None) -> Image.Image:
    """1 px outline around every opaque pixel (4-neighbourhood).

    "selout" (selective outline) tints each outline pixel from the colour it
    borders, so the edge reads as shading instead of a cut-out black line.
    """
    mode = mode or OUTLINE_MODE
    if mode == "none":
        return img
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and src[nx, ny][3] and src[nx, ny] != MAGIC and src[nx, ny] != MAGIC_D:
                    if mode == "selout":
                        r, g, b, _ = src[nx, ny]
                        dst[x, y] = (int(r * 0.42) + 12, int(g * 0.42) + 10, int(b * 0.42) + 16, 255)
                    else:
                        dst[x, y] = OUTLINE
                    break
    return out


def make_strip() -> Image.Image:
    strip = Image.new("RGBA", (W * len(POSES), H), (0, 0, 0, 0))
    for i, pose in enumerate(POSES):
        strip.paste(_draw_frame(pose), (i * W, 0))
    return strip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path, help="also save an 8x preview on a dark background")
    args = ap.parse_args()
    strip = make_strip()
    strip.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(POSES)} frames of {W}x{H})")
    if args.preview:
        bg = Image.new("RGBA", strip.size, (52, 60, 72, 255))
        bg.alpha_composite(strip)
        bg.resize((strip.width * 8, strip.height * 8), Image.NEAREST).save(args.preview)


if __name__ == "__main__":
    main()
