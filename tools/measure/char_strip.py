"""Find the character in the right panel of a reference video frame and build a labelled strip.

The character is saturated (red cloth / gold armor / blue-red pants) against a
desaturated icy background, so a saturation + warm-tone mask finds it.
"""
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

VID = r"D:\Workspace\games\WuKong\docs\refs\video"
OUT = r"D:\Workspace\games\WuKong\docs\renders"


def frame_path(name):
    return "%s\\%s.png" % (VID, name)


def mask_of(im, x0=960):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    sat = (mx - mn)
    warm = r - (g + b) / 2.0
    m = (sat > 55) & ((warm > 12) | (r > 110))
    m[:, :x0] = False          # left panel out
    m[:400, :] = False         # sky / watermark
    m[-40:, :] = False         # bottom UI
    return m


def bbox(m):
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        return None
    # robust bbox: ignore sparse outliers
    x_lo, x_hi = np.percentile(xs, 1), np.percentile(xs, 99.5)
    y_lo, y_hi = np.percentile(ys, 1), np.percentile(ys, 99.5)
    return int(x_lo), int(y_lo), int(x_hi), int(y_hi)


def strip(names, out, scale=2.0, pad=40, step=20, contrast=1.2):
    cells = []
    for n in names:
        im = Image.open(frame_path(n)).convert("RGB")
        m = mask_of(im)
        bb = bbox(m)
        if bb is None:
            print("no bbox", n)
            continue
        x0, y0, x1, y1 = bb
        x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
        x1, y1 = min(im.width, x1 + pad), min(im.height, y1 + pad)
        cells.append((n, im, (x0, y0, x1, y1)))
        print(n, "bbox", bb)
    if not cells:
        return
    maxw = max(c[2][2] - c[2][0] for c in cells)
    maxh = max(c[2][3] - c[2][1] for c in cells)
    cw, ch = int(maxw * scale), int(maxh * scale)
    sh = Image.new("RGB", (cw * len(cells), ch), "black")
    d = ImageDraw.Draw(sh)
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    for i, (n, im, box) in enumerate(cells):
        crop = im.crop(box)
        crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
        crop = ImageEnhance.Contrast(crop).enhance(contrast)
        # bottom-align so the ground line is comparable between cells
        oy = i * cw
        sh.paste(crop, (i * cw, ch - crop.height))
        d.text((i * cw + 4, 2), n[2:], fill=(0, 255, 0), font=font)
        # horizontal reference lines every `step` px of the ORIGINAL scale
        for yy in range(0, crop.height, int(step * scale)):
            col = (255, 0, 0) if (yy // int(step * scale)) % 5 == 0 else (80, 80, 80)
            d.line([(i * cw, ch - crop.height + yy), (i * cw + cw, ch - crop.height + yy)],
                   fill=col, width=1)
    sh.save(out)
    print("wrote", out, sh.size)


if __name__ == "__main__":
    out = sys.argv[1]
    names = sys.argv[2:]
    strip(names, out)
