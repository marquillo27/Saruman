"""Turn raw ComfyUI background renders into game-ready parallax backdrops.

Each raw render (768x448, from comfy_txt2img.py with the PixelArtRedmond LoRA)
is cropped to the 16:9 view, scaled to the 480x270 world canvas, reduced to a
small palette, pushed back a little (dimmer, less saturated) so the playfield
stays readable, and mirrored horizontally so it tiles seamlessly while the
parallax layer scrolls.

Usage:
    python tools/process_backgrounds.py <raw_dir>
    python tools/process_backgrounds.py <raw_dir> --only greenwood_valley

Writes assets/backgrounds/<name>.png (960x270).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT    = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "backgrounds"
VIEW_W, VIEW_H = 480, 270

# backdrop name -> raw render file (prompt seed recorded in the filename)
SOURCES = {
    "greenwood_valley":    "greenwood_2200.png",
    "greenwood_mountains": "greenwood_2201.png",
    "greenwood_dusk":      "greenwood_2202.png",
    "glass_caverns":       "glass_caverns_2300.png",
    "ashfall":             "ashfall_2311.png",
    "cinderwood":          "cinderwood_2320.png",
    "ash_marshes":         "ash_marshes_2331.png",
    "throne":              "throne_2341.png",
    "pale_tower":          "pale_tower_2351.png",
    "skybound":            "skybound_2360.png",
    "bridge":              "bridge_2370.png",
    "catacombs":           "catacombs_2380.png",
    "emberfall":           "emberfall_2390.png",
}


def process(src: Path, colors: int = 32, dim: float = 0.62, saturation: float = 0.6,
            haze: float = 0.3, pixel: int = 2) -> Image.Image:
    img = Image.open(src).convert("RGB")
    # Crop to 16:9 around the vertical centre-bottom (horizon detail sits low).
    w, h   = img.size
    crop_h = round(w * VIEW_H / VIEW_W)
    top    = max(0, h - crop_h)
    img    = img.crop((0, top, w, top + crop_h)).resize((VIEW_W, VIEW_H), Image.LANCZOS)
    img    = ImageEnhance.Color(img).enhance(saturation)
    img    = ImageEnhance.Brightness(img).enhance(dim)
    # Atmospheric haze: blend toward the average sky colour (top strip).
    sky    = img.crop((0, 0, VIEW_W, VIEW_H // 6)).resize((1, 1), Image.BOX)
    img    = Image.blend(img, Image.new("RGB", img.size, sky.getpixel((0, 0))), haze)
    # Chunkier pixels than the playfield read as "far away".
    img    = img.resize((VIEW_W // pixel, VIEW_H // pixel), Image.BOX).resize((VIEW_W, VIEW_H), Image.NEAREST)
    img    = img.quantize(colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    tiled  = Image.new("RGB", (VIEW_W * 2, VIEW_H))
    tiled.paste(img, (0, 0))
    tiled.paste(img.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (VIEW_W, 0))
    return tiled


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir", type=Path)
    ap.add_argument("--only", help="process just this backdrop name")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, fname in SOURCES.items():
        if args.only and name != args.only:
            continue
        src = args.raw_dir / fname
        if not src.exists():
            print(f"skip {name}: {src} missing")
            continue
        process(src).save(OUT_DIR / f"{name}.png", optimize=True)
        print(f"wrote {name}.png")


if __name__ == "__main__":
    main()
