"""Turn raw ComfyUI background renders into game-ready parallax backdrops.

Each raw render (768x448, from comfy_txt2img.py with the PixelArtRedmond LoRA)
is cropped to the 16:9 view, scaled to the 480x270 world canvas, reduced to a
small palette, pushed back a little (dimmer, less saturated) so the playfield
stays readable, and mirrored horizontally so it tiles seamlessly while the
parallax layer scrolls.

Backdrops with depth cuts are also split into parallax layers using the depth
map written next to the render by tools/depth_maps.py: layer 0 is the whole
scene (sky), layer k keeps only what is nearer than cuts[k-1]. Wherever a
nearer layer covers a farther one, the farther one is filled in by smearing
its own neighbouring pixels sideways, so nothing is duplicated when the
layers drift apart.

Usage:
    python tools/process_backgrounds.py <raw_dir>
    python tools/process_backgrounds.py <raw_dir> --only greenwood_valley

Writes assets/backgrounds/<name>.png (960x270) and, for layered backdrops,
<name>_1.png, <name>_2.png ... (960x270, transparent where farther away).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "backgrounds"
VIEW_W, VIEW_H = 480, 270
PIXEL = 2   # backdrop pixels are 2x2 world pixels (chunkier reads as far away)

# backdrop name -> (raw render file with its seed in the name, depth cuts).
# Each cut is a depth threshold (0 = farthest, 1 = nearest) that starts a new,
# faster layer. No cuts = one flat layer (enclosed scenes have no clear sky).
SOURCES: dict[str, tuple[str, tuple[float, ...]]] = {
    "greenwood_valley":    ("greenwood_2200.png",     (0.15, 0.6)),
    "greenwood_mountains": ("greenwood_2201.png",     (0.15, 0.6)),
    "greenwood_dusk":      ("greenwood_2202.png",     (0.15, 0.6)),
    "glass_caverns":       ("glass_caverns_2300.png", ()),
    "ashfall":             ("ashfall_2413.png",       (0.15, 0.6)),
    "cinderwood":          ("cinderwood_2320.png",    (0.15, 0.6)),
    "ash_marshes":         ("ash_marshes_2331.png",   (0.15, 0.6)),
    "throne":              ("throne_2341.png",        (0.15, 0.6)),
    "pale_tower":          ("pale_tower_2351.png",    (0.15, 0.6)),
    "skybound":            ("skybound_2360.png",      (0.15, 0.6)),
    "bridge":              ("bridge_2370.png",        (0.15, 0.6)),
    "catacombs":           ("catacombs_2380.png",     ()),
    "emberfall":           ("emberfall_2390.png",     (0.15, 0.6)),
    "title":               ("title_4101.png",         (0.3, 0.75)),   # main menu
}


def _crop_view(img: Image.Image, resample: int) -> Image.Image:
    """Crop to 16:9 at the bottom (horizon detail sits low) and scale to the view."""
    w, h   = img.size
    crop_h = round(w * VIEW_H / VIEW_W)
    top    = max(0, h - crop_h)
    return img.crop((0, top, w, top + crop_h)).resize((VIEW_W, VIEW_H), resample)


# Backdrops that are not pushed back behind a playfield get a lighter touch.
LOOK: dict[str, dict[str, float]] = {
    "title": {"dim": 0.85, "saturation": 0.8, "haze": 0.12},
}


def process(src: Path, colors: int = 32, dim: float = 0.62, saturation: float = 0.6,
            haze: float = 0.3) -> Image.Image:
    """The flat 480x270 backdrop, already reduced to PIXEL-sized blocks and the palette."""
    img = _crop_view(Image.open(src).convert("RGB"), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(saturation)
    img = ImageEnhance.Brightness(img).enhance(dim)
    # Atmospheric haze: blend toward the average sky colour (top strip).
    sky = img.crop((0, 0, VIEW_W, VIEW_H // 6)).resize((1, 1), Image.BOX)
    img = Image.blend(img, Image.new("RGB", img.size, sky.getpixel((0, 0))), haze)
    img = img.resize((VIEW_W // PIXEL, VIEW_H // PIXEL), Image.BOX).resize((VIEW_W, VIEW_H), Image.NEAREST)
    return img.quantize(colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")


def _clean(mask: np.ndarray) -> np.ndarray:
    """Drop isolated specks and pinholes (3x3 majority vote)."""
    p = np.pad(mask, 1, mode="edge").astype(np.int8)
    votes = sum(p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    return votes >= 5


def _grow(mask: np.ndarray, diagonal: bool = False) -> np.ndarray:
    """Dilate a mask by one pixel (4-neighbourhood, or 8 with diagonal=True)."""
    out = mask.copy()
    out[1:]     |= mask[:-1]
    out[:-1]    |= mask[1:]
    out[:, 1:]  |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    if diagonal:
        out[1:, 1:]   |= mask[:-1, :-1]
        out[1:, :-1]  |= mask[:-1, 1:]
        out[:-1, 1:]  |= mask[1:, :-1]
        out[:-1, :-1] |= mask[1:, 1:]
    return out


def _fill_hidden(rgb: np.ndarray, own: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    """Paint the hidden pixels of a layer in flat horizontal bands: each row gets the
    average of its own visible pixels (rows with none repeat the band above),
    snapped to the backdrop's palette. Reads as distant haze when uncovered,
    where copying neighbours would smear streaks and ghost outlines."""
    out = rgb.copy()
    palette = np.unique(rgb.reshape(-1, 3), axis=0).astype(np.int32)
    band = rgb[0].mean(axis=0)
    for y in range(own.shape[0]):
        if own[y].any():
            band = rgb[y, own[y]].mean(axis=0)
        if hidden[y].any():
            out[y, hidden[y]] = palette[np.argmin(((palette - band) ** 2).sum(axis=1))]
    return out


def split_layers(img: Image.Image, depth: Image.Image, cuts: tuple[float, ...]) -> list[Image.Image]:
    """Cut the flat backdrop into len(cuts)+1 view-sized layers, far to near."""
    gw, gh = VIEW_W // PIXEL, VIEW_H // PIXEL
    rgb = np.asarray(img.resize((gw, gh), Image.NEAREST)).copy()
    d   = np.asarray(_crop_view(depth.convert("L"), Image.BILINEAR).resize((gw, gh), Image.BOX)) / 255.0
    # in_layer[k]: pixel belongs to layer k or nearer. Grown by one pixel so the
    # dark outline at a silhouette's edge travels with it instead of staying
    # behind on the farther layer.
    in_layer = [np.ones((gh, gw), bool)] + [_grow(_clean(d >= c), diagonal=True) for c in cuts]
    for k in range(len(in_layer) - 1, 0, -1):
        in_layer[k][-1] = True                           # every layer reaches the bottom edge
        in_layer[k - 1] |= in_layer[k]
    # The blurry depth map leaves a one-pixel sliver of a nearer silhouette's
    # edge on the layer behind it; hand such slivers to the nearer layer.
    for k in range(len(in_layer) - 1, 1, -1):
        own = in_layer[k - 1] & ~in_layer[k]
        in_layer[k] |= own & _grow(~own) & _grow(in_layer[k])
    layers = []
    for k in range(len(in_layer)):
        nearer = in_layer[k + 1] if k + 1 < len(in_layer) else np.zeros_like(in_layer[k])
        own    = in_layer[k] & ~nearer
        filled = _fill_hidden(rgb, own, nearer)
        # A land layer only exists below its own top edge; above that (e.g. a
        # tower rising out of the near layer) it stays see-through, so the
        # sky shows there once the layers drift apart.
        # Thin slivers of own pixels hugging a nearer silhouette don't count.
        body   = ~_grow(~own)
        shape  = own | (nearer & np.logical_or.accumulate(body, axis=0)) if k else in_layer[k]
        alpha  = np.where(shape, 255, 0).astype(np.uint8)
        layer  = Image.fromarray(np.dstack([filled, alpha]), "RGBA")
        layers.append(layer.resize((VIEW_W, VIEW_H), Image.NEAREST))
    return layers


def tile(img: Image.Image) -> Image.Image:
    """Mirror horizontally so the strip wraps seamlessly."""
    tiled = Image.new(img.mode, (VIEW_W * 2, VIEW_H))
    tiled.paste(img, (0, 0))
    tiled.paste(img.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (VIEW_W, 0))
    return tiled


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir", type=Path)
    ap.add_argument("--only", help="process just this backdrop name")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (fname, cuts) in SOURCES.items():
        if args.only and name != args.only:
            continue
        src = args.raw_dir / fname
        if not src.exists():
            print(f"skip {name}: {src} missing")
            continue
        flat = process(src, **LOOK.get(name, {}))
        for old in OUT_DIR.glob(f"{name}_[0-9].png"):
            old.unlink()
        depth = src.with_name(f"{src.stem}_depth.png")
        if not cuts:
            tile(flat).save(OUT_DIR / f"{name}.png", optimize=True)
            print(f"wrote {name}.png")
            continue
        if not depth.exists():
            raise SystemExit(f"{name}: {depth.name} missing, run tools/depth_maps.py first")
        layers = split_layers(flat, Image.open(depth), cuts)
        tile(layers[0].convert("RGB")).save(OUT_DIR / f"{name}.png", optimize=True)
        for k, layer in enumerate(layers[1:], start=1):
            tile(layer).save(OUT_DIR / f"{name}_{k}.png", optimize=True)
        print(f"wrote {name}.png + {len(layers) - 1} layer(s)")


if __name__ == "__main__":
    main()
