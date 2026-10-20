"""Crop the character out of the reference video (clean side view on a grey backdrop)
and build a labelled, upscaled sheet.

  python ref3_sheet.py <out.png> [cols] [height]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = Path(r"D:\Workspace\games\WuKong\docs\refs\video3")


def frames():
    fs = sorted(SRC.glob("v_*.png"), key=lambda p: int(p.stem.split("_")[1]))
    return [p for p in fs if p.stat().st_size > 1000]


def content_box(a):
    """The video content area (non-black border)."""
    g = a.mean(axis=2)
    m = g > 30
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max(), ys.max()


def char_mask(a):
    """Character = dark clothing or red accents, inside the content area."""
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    dark = g < 70
    red = (r - g) > 25
    m = dark | red
    x0, y0, x1, y1 = content_box(a)
    m[:y0, :] = False
    m[y1:, :] = False
    m[:, :x0] = False
    m[:, x1:] = False
    return m


def main():
    out = sys.argv[1]
    cols = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    H = int(sys.argv[3]) if len(sys.argv) > 3 else 360
    fs = frames()
    crops = []
    for p in fs:
        im = Image.open(p).convert("RGB")
        a = np.asarray(im)
        m = char_mask(a)
        ys, xs = np.nonzero(m)
        if len(xs) < 50:
            continue
        pad = 12
        box = (max(0, xs.min() - pad), max(0, ys.min() - pad),
               min(im.width, xs.max() + pad), min(im.height, ys.max() + pad))
        crops.append((p.stem[2:], im.crop(box), (xs.min(), ys.min(), xs.max(), ys.max())))
    if not crops:
        raise SystemExit("no character found")
    W = max(c.width for _, c, _ in crops)
    Hc = max(c.height for _, c, _ in crops)
    scale = H / Hc
    cw, ch = int(W * scale), H
    rows = (len(crops) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols + 8 * cols, (ch + 22) * rows), (18, 18, 20))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)
    for i, (name, im, bb) in enumerate(crops):
        t = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        x = (i % cols) * (cw + 8) + 4
        y = (i // cols) * (ch + 22) + 18
        sheet.paste(t, (x, y))
        d.text((x, y - 16), "f%s  h=%d" % (name, bb[3] - bb[1]), fill=(140, 255, 150), font=font)
    sheet.save(out)
    print("wrote", out, sheet.size, "frames", len(crops))
    for name, im, bb in crops:
        print("  f%s bbox %s  w=%d h=%d" % (name, bb, bb[2] - bb[0], bb[3] - bb[1]))


if __name__ == "__main__":
    main()
