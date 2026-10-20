"""Segment the reference character by temporal-median background subtraction.

The search camera follows the runner, so a per-pixel temporal median over the
whole segment approximates the background; the runner - present in a given pixel
only briefly - stands out. Writes mask previews and a per-frame metric table.

  python seg_run.py <start> <end> <step> [preview_frames...]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

VID = Path(r"D:\Workspace\games\WuKong\docs\refs\video")
OUT = Path(r"D:\Workspace\games\WuKong\docs\renders")


def load(n):
    return np.asarray(Image.open(VID / ("v_%04d.png" % n)).convert("RGB")).astype(np.float32)


def main():
    start, end, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    previews = [int(a) for a in sys.argv[4:]]
    nums = [n for n in range(start, end + 1, step) if (VID / ("v_%04d.png" % n)).exists()]
    stack = np.stack([load(n) for n in nums])          # (T, H, W, 3)
    bg = np.median(stack, axis=0)
    Image.fromarray(bg.astype(np.uint8)).save(OUT / "seg_bg.png")
    thr = 26.0
    rows = []
    for i, n in enumerate(nums):
        d = np.abs(stack[i] - bg).max(axis=2)
        m = d > thr
        m[:430, :] = False
        m[-42:, :] = False
        # right panel only (side-ish view)
        half = 960
        ml = m.copy(); ml[:, half:] = False
        mr = m.copy(); mr[:, :half] = False
        ys, xs = np.nonzero(ml)
        yl, xl = np.nonzero(mr)
        rec = {"f": n}
        if len(xs) > 400:
            rec.update({"Ln": len(xs), "Lx0": xs.min(), "Lx1": xs.max(), "Ly0": ys.min(),
                        "Ly1": ys.max(), "Lcx": xs.mean(), "Lcy": ys.mean()})
        if len(xl) > 400:
            rec.update({"Rn": len(xl), "Rx0": xl.min(), "Rx1": xl.max(), "Ry0": yl.min(),
                        "Ry1": yl.max(), "Rcx": xl.mean(), "Rcy": yl.mean()})
        rows.append(rec)
        if n in previews:
            vis = np.zeros((*m.shape, 3), np.uint8)
            vis[m] = (255, 255, 255)
            Image.fromarray(vis).save(OUT / ("seg_%04d.png" % n))
    keys = ["f", "Ln", "Lx0", "Lx1", "Ly0", "Ly1", "Lcy", "Rn", "Rx0", "Rx1", "Ry0", "Ry1", "Rcy"]
    print(" ".join("%6s" % k for k in keys))
    for r in rows:
        print(" ".join("%6.0f" % r.get(k, -1) for k in keys))
    print("PREVIEWS", previews, "NUM_FRAMES", len(nums))


if __name__ == "__main__":
    main()
