"""Estimate a depth map for each raw ComfyUI background render.

process_backgrounds.py uses these maps to cut a painted backdrop into parallax
layers (sky, far land, near land). The model is Depth Anything V2 Small
(ONNX export from onnx-community/depth-anything-v2-small, Apache-2.0). It needs
onnxruntime, which the game itself does not depend on, so run this with the
ComfyUI embedded Python:

    <ComfyUI>/python_embeded/python.exe -I tools/depth_maps.py <model.onnx> <raw_dir>

Writes <raw_dir>/<render>_depth.png next to each render (8-bit, white = near).
Only renders listed in process_backgrounds.SOURCES are processed.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
_STD  = np.array([0.229, 0.224, 0.225], np.float32)


def _source_files() -> list[str]:
    """Raw render filenames from process_backgrounds.SOURCES, read without importing it
    (this script runs outside the project's environment)."""
    tree = ast.parse((Path(__file__).parent / "process_backgrounds.py").read_text(encoding="utf-8"))
    for node in tree.body:
        target = node.target if isinstance(node, ast.AnnAssign) else getattr(node, "targets", [None])[0]
        if getattr(target, "id", "") == "SOURCES":
            return sorted({v[0] if isinstance(v, tuple) else v
                           for v in ast.literal_eval(node.value).values()})
    raise RuntimeError("SOURCES not found in process_backgrounds.py")


def estimate(sess: ort.InferenceSession, img: Image.Image) -> Image.Image:
    w, h = img.size
    # The model needs sides that are multiples of its 14 px patch size.
    x = np.asarray(img.resize((14 * round(w / 14), 14 * round(h / 14)), Image.BICUBIC), np.float32) / 255
    x = ((x - _MEAN) / _STD).transpose(2, 0, 1)[None].astype(np.float32)
    d = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]
    d = (d - d.min()) / (d.max() - d.min() + 1e-6)
    return Image.fromarray((d * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", type=Path)
    ap.add_argument("raw_dir", type=Path)
    args = ap.parse_args()
    sess = ort.InferenceSession(str(args.model), providers=["CPUExecutionProvider"])
    for fname in _source_files():
        src = args.raw_dir / fname
        if not src.exists():
            print(f"skip {fname}: missing")
            continue
        out = src.with_name(f"{src.stem}_depth.png")
        estimate(sess, Image.open(src).convert("RGB")).save(out)
        print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
