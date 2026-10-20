"""Character-centred crops laid out in a grid with an absolute-coordinate grid.

  python body_grid.py <out.png> <scale> <cols> <frame> [frame ...]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

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


def main():
    out, scale, cols = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
    names = sys.argv[4:]
    ims, boxes = [], []
    for n in names:
        im = Image.open("%s\\%s.png" % (VID, n)).convert("RGB")
        bb = body_bbox(mask_of(im))
        if bb is None:
            print("skip", n)
            continue
        print(n, "body bbox", bb, "w", bb[2] - bb[0], "h", bb[3] - bb[1])
        ims.append((n, im))
        boxes.append(bb)
    pad = 25
    xs0 = min(b[0] for b in boxes) - pad
    ys0 = min(b[1] for b in boxes) - pad
    xs1 = max(b[2] for b in boxes) + pad
    ys1 = max(b[3] for b in boxes) + pad
    cw, ch = int((xs1 - xs0) * scale), int((ys1 - ys0) * scale)
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cw * cols, ch * rows), "black")
    d = ImageDraw.Draw(sh)
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
    step = int(10 * scale) or 1
    for i, (n, im) in enumerate(ims):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        crop = im.crop((xs0, ys0, xs1, ys1)).resize((cw, ch), Image.LANCZOS)
        crop = ImageEnhance.Contrast(crop).enhance(1.28)
        sh.paste(crop, (cx, cy))
        d.rectangle([cx, cy, cx + 58, cy + 16], fill=(0, 0, 0))
        d.text((cx + 3, cy + 1), n[2:], fill=(0, 255, 0), font=font)
        for x in range(0, cw, step):
            major = (x // step) % 5 == 0
            d.line([(cx + x, cy), (cx + x, cy + ch)], fill=(255, 30, 30) if major else (70, 70, 70), width=1)
            if major:
                d.text((cx + x + 1, cy + ch - 15), str(int(xs0 + x / scale)), fill=(255, 255, 0), font=font)
        for y in range(0, ch, step):
            major = (y // step) % 5 == 0
            d.line([(cx, cy + y), (cx + cw, cy + y)], fill=(255, 30, 30) if major else (70, 70, 70), width=1)
            if major:
                d.text((cx + 1, cy + y + 1), str(int(ys0 + y / scale)), fill=(255, 255, 0), font=font)
    sh.save(out)
    print("wrote", out, sh.size, "crop", (xs0, ys0, xs1, ys1))


if __name__ == "__main__":
    main()
