"""Prepare square, clean-background inputs for Hunyuan3D.

The source crops still carry the paper texture of the concept sheet; it is
keyed out by distance from the paper colour so the canvas is plain white.
"""

import os

import numpy as np
from PIL import Image

REFS = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\refs"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\hunyuan"
CANVAS = 2048
FIGURE_H = 1800
FEET_Y = 1948

os.makedirs(OUT, exist_ok=True)

SOURCES = {
    "front.png": "ref_front.png",
    "right.png": "ref_side.png",
    "back.png": "ref_back.png",
    "tpose_front.png": "ref_tpose_crop.png",
}

for out_name, src_name in SOURCES.items():
    src = Image.open(os.path.join(REFS, src_name)).convert("RGB")
    rgb = np.asarray(src).astype(np.float32)
    paper = np.median(rgb[:20, :20].reshape(-1, 3), axis=0)
    diff = np.abs(rgb - paper).max(axis=2)
    alpha = np.clip((diff - 14.0) / 26.0, 0.0, 1.0)

    rgba = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
    fg = Image.fromarray(rgba, "RGBA")

    scale = FIGURE_H / src.height
    resized = fg.resize((round(src.width * scale), FIGURE_H), Image.LANCZOS)

    canvas = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    x = (CANVAS - resized.width) // 2
    canvas.paste(resized, (x, FEET_Y - FIGURE_H), resized)

    path = os.path.join(OUT, out_name)
    canvas.save(path)
    print(out_name, canvas.size, "figure", resized.size)
