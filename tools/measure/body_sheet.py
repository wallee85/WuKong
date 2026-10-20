"""Body-centred reference crops with a labelled absolute-coordinate grid.

  python body_sheet.py <out.png> <scale> <cols> <mode> <frame> [frame ...]
    mode plain : clean crops, frame number badge
    mode grid   : 20 px grid, labelled margins in absolute frame pixels
Out name may contain %F, replaced by the first frame name.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

VID = r"D:\Workspace\games\WuKong\docs\refs\video"


def mask_of(im, x0=960):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    warm = r - (g + b) / 2.0
    m = ((mx - mn) > 55) & ((warm > 12) | (r > 110))
    m[:, :x0] = False
    m[:400, :] = False
    m[-40:, :] = False
    return m


def body_bbox(m, dense=8):
    cols = m.sum(axis=0)
    rows = m.sum(axis=1)
    vc = np.nonzero(cols >= dense)[0]
    vr = np.nonzero(rows >= dense)[0]
    if len(vc) == 0 or len(vr) == 0:
        return None
    return int(vc[0]), int(vr[0]), int(vc[-1]), int(vr[-1])


def lift(im):
    """Lift shadows so the dark cloth/boots read against the bright ground."""
    a = np.asarray(im).astype(np.float32) / 255.0
    a = np.power(a, 0.75)
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


def main():
    out, scale, cols, mode = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    names = sys.argv[5:]
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)
    items = []
    for n in names:
        im = Image.open("%s\\%s.png" % (VID, n)).convert("RGB")
        bb = body_bbox(mask_of(im))
        print(n, bb)
        items.append((n, im, bb))
    pad = 30
    xs0 = min(i[2][0] for i in items) - pad
    xs1 = max(i[2][2] for i in items) + pad
    ys0 = min(i[2][1] for i in items) - pad - 15
    ys1 = max(i[2][3] for i in items) + pad + 10
    cw, ch = int((xs1 - xs0) * scale), int((ys1 - ys0) * scale)
    rows = (len(items) + cols - 1) // cols
    M = 36 if mode == "grid" else 0
    canvas = Image.new("RGB", (cw * cols + M, ch * rows + M), (18, 18, 18))
    for i, (n, im, bb) in enumerate(items):
        cx, cy = M + (i % cols) * cw, M + (i // cols) * ch
        crop = im.crop((xs0, ys0, xs1, ys1)).resize((cw, ch), Image.LANCZOS)
        crop = crop.filter(ImageFilter.UnsharpMask(radius=2, percent=170, threshold=1))
        crop = lift(crop)
        crop = ImageEnhance.Contrast(crop).enhance(1.15)
        canvas.paste(crop, (cx, cy))
        d = ImageDraw.Draw(canvas)
        d.rectangle([cx, cy, cx + 52, cy + 16], fill=(0, 0, 0))
        d.text((cx + 3, cy + 1), n[2:], fill=(80, 255, 80), font=font)
        if mode != "grid":
            continue
        step = 20
        for x in range(0, cw + 1, int(step * scale)):
            ax = int(round(xs0 + x / scale))
            X = cx + x
            lab = round(ax / 20) % 5 == 0
            d.line([(X, cy), (X, cy + ch)], fill=(255, 45, 45) if lab else (100, 100, 100), width=1)
            if lab:
                d.text((X - 10, 2), str(ax), fill=(255, 255, 90), font=font)
                d.text((X - 10, M + ch * rows + 4), str(ax), fill=(255, 255, 90), font=font)
        for y in range(0, ch + 1, int(step * scale)):
            ay = int(round(ys0 + y / scale))
            Y = cy + y
            lab = round(ay / 20) % 5 == 0
            d.line([(cx, Y), (cx + cw, Y)], fill=(255, 45, 45) if lab else (100, 100, 100), width=1)
            if lab:
                d.text((1, Y - 8), str(ay), fill=(255, 255, 90), font=font)
    canvas.save(out.replace("%F", items[0][0]))
    print("wrote", out.replace("%F", items[0][0]), canvas.size, "crop", (xs0, ys0, xs1, ys1))


if __name__ == "__main__":
    main()
