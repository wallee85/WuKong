"""Track the reference run silhouette per frame and derive cycle timing / flight fraction.

  python track_run.py <start> <end> <step> [mask_preview_frame]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

VID = Path(r"D:\Workspace\games\WuKong\docs\refs\video")
OUT = Path(r"D:\Workspace\games\WuKong\docs\renders")


def frames_between(start, end, step):
    return [n for n in range(start, end + 1, step) if (VID / ("v_%04d.png" % n)).exists()]


def char_mask(im):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    v = a.max(axis=2)
    warm = r - g
    gold = (warm > 18) & (r > 90)
    dark = v < 52
    m = gold | dark
    m[:, :960] = False      # keep the right panel
    m[:430, :] = False      # sky + watermark
    m[-42:, :] = False      # UI bar
    # drop isolated specks
    from numpy.lib.stride_tricks import sliding_window_view  # noqa: F401
    return m


def metrics(m):
    ys, xs = np.nonzero(m)
    if len(xs) < 200:
        return None
    return {
        "n": len(xs),
        "x0": int(xs.min()), "x1": int(xs.max()),
        "y0": int(ys.min()), "y1": int(ys.max()),
        "cy": float(ys.mean()), "cx": float(xs.mean()),
        "sx": float(xs.std()),
    }


def main():
    start, end, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    prev = sys.argv[4] if len(sys.argv) > 4 else None
    rows = []
    for n in frames_between(start, end, step):
        im = Image.open(VID / ("v_%04d.png" % n))
        m = char_mask(im)
        d = metrics(m)
        if d is None:
            continue
        rows.append((n, d))
        if prev and str(n) == prev:
            vis = Image.fromarray((m * 255).astype(np.uint8))
            vis.save(OUT / ("mask_%04d.png" % n))
    ys1 = np.array([r[1]["y1"] for r in rows], float)
    y0 = np.array([r[1]["y0"] for r in rows], float)
    cy = np.array([r[1]["cy"] for r in rows], float)
    sx = np.array([r[1]["sx"] for r in rows], float)
    ground = np.percentile(ys1, 90)
    print("frames", rows[0][0], "->", rows[-1][0], "count", len(rows))
    print("ground_y(p90 of lowest point) =", round(ground, 1))
    print("frame  low_y  gap  height  cy     x_std")
    for (n, d), l, t, c, s in zip(rows, ys1, y0, cy, sx):
        print("%5d %6.0f %5.0f %7.0f %6.1f %6.1f" % (n, l, ground - l, l - t, c, s))
    # crude period estimate: autocorrelation of the gap signal
    g = ground - ys1
    g = g - g.mean()
    if g.std() > 1e-6:
        ac = np.correlate(g, g, "full")[len(g) - 1:]
        ac = ac / ac[0]
        best, bestlag = -2, None
        for lag in range(2, len(ac) // 2):
            if ac[lag] > best and ac[lag] > ac[lag - 1] and ac[lag] >= ac[lag + 1]:
                best, bestlag = ac[lag], lag
        print("gap autocorr peak lag =", bestlag, "frames (step", step, ") r =", round(best, 3),
              "-> period_s =", None if bestlag is None else round(bestlag * step / 30.0, 3))


if __name__ == "__main__":
    main()
