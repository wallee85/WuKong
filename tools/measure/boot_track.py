"""Track the bright red boots in the reference video (colour segmentation).

The boots are the only large, very red, low-in-frame blobs; the red skirt panels
are red too but sit higher and are usually attached to the body mass, so each
frame reports all red components and the analysis picks the lowest ones.

  python boot_track.py <start> <end> <step> [preview_frames...]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

VID = Path(r"D:\Workspace\games\WuKong\docs\refs\video")
OUT = Path(r"D:\Workspace\games\WuKong\docs\renders")


def red_mask(a):
    r, g, b = a[..., 0].astype(np.int16), a[..., 1].astype(np.int16), a[..., 2].astype(np.int16)
    return (r - g > 45) & (r - b > 30) & (r > 105)


def components(m, min_area=120):
    """4-connected labelling, returns list of (area, cx, cy, x0,y0,x1,y1)."""
    seen = np.zeros_like(m, bool)
    out = []
    h, w = m.shape
    idx = np.argwhere(m)
    for y0, x0 in idx:
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        pix = []
        while stack:
            y, x = stack.pop()
            pix.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(pix) < min_area:
            continue
        ys = [p[0] for p in pix]
        xs = [p[1] for p in pix]
        out.append((len(pix), float(np.mean(xs)), float(np.mean(ys)),
                    min(xs), min(ys), max(xs), max(ys)))
    out.sort(key=lambda t: -t[0])
    return out


def main():
    start, end, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    previews = [int(a) for a in sys.argv[4:]]
    print("%5s %-42s %-42s" % ("f", "top-1 red blob (area cx cy bbox)", "top-2 red blob"))
    for n in range(start, end + 1, step):
        p = VID / ("v_%04d.png" % n)
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB")
        a = np.asarray(im)
        m = red_mask(a)
        m[:, :960] = False
        m[:430, :] = False
        m[-42:, :] = False
        comps = components(m)[:2]
        desc = []
        for c in comps:
            desc.append("a%-6d c(%4.0f,%4.0f) y%4d-%4d" % (c[0], c[1], c[2], c[4], c[6]))
        while len(desc) < 2:
            desc.append("-")
        print("%5d %-42s %-42s" % (n, desc[0], desc[1]))
        if n in previews:
            vis = im.copy()
            d = ImageDraw.Draw(vis)
            for c in comps:
                d.rectangle([c[3], c[4], c[5], c[6]], outline=(0, 255, 0), width=2)
                d.ellipse([c[1] - 4, c[2] - 4, c[1] + 4, c[2] + 4], fill=(0, 255, 255))
            vis.save(OUT / ("boot_%04d.png" % n))


if __name__ == "__main__":
    main()
