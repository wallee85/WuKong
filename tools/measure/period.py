"""Estimate the reference run's cycle period from frame-to-frame similarity.

The camera follows the runner, so a frame repeats when the pose repeats. We take a
fixed window over the character in each panel, block-average it down, mean-centre
and unit-normalise it, then look for the lag with the highest correlation.

  python period.py <start> <end> <step> [panel:left|right]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

VID = Path(r"D:\Workspace\games\WuKong\docs\refs\video")
WINDOWS = {"left": (200, 380, 940, 1030), "right": (1050, 380, 1850, 1030)}


def vec(n, panel):
    x0, y0, x1, y1 = WINDOWS[panel]
    a = np.asarray(Image.open(VID / ("v_%04d.png" % n)).convert("L"), dtype=np.float32)
    a = a[y0:y1, x0:x1]
    h, w = a.shape
    a = a[: h // 8 * 8, : w // 8 * 8].reshape(h // 8, 8, w // 8, 8).mean(axis=(1, 3))
    v = a.ravel()
    v = v - v.mean()
    n_ = np.linalg.norm(v)
    return v / (n_ + 1e-9)


def main():
    start, end, step = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    panel = sys.argv[4] if len(sys.argv) > 4 else "left"
    nums = [n for n in range(start, end + 1, step) if (VID / ("v_%04d.png" % n)).exists()]
    vs = [vec(n, panel) for n in nums]
    T = len(nums)
    print("frames", nums[0], "->", nums[-1], "n", T, "step", step, "panel", panel)
    print("lag_frames  lag_s   mean_corr   n_pairs")
    best = (-2, None)
    for lag in range(2, T // 2 + 1):
        cs = [float(np.dot(vs[i], vs[i + lag])) for i in range(T - lag)]
        m = float(np.mean(cs))
        print("%10d %7.2f %11.4f %8d" % (lag, lag * step / 30.0, m, len(cs)))
        if m > best[0]:
            best = (m, lag)
    print("BEST lag=%d frames (%.3f s) corr=%.4f" % (best[1], best[1] * step / 30.0, best[0]))
    # sub-lag: also report the lag with the highest single-pair correlation
    i, lag = max(((i, l) for i in range(T) for l in range(3, T - i)),
                 key=lambda p: float(np.dot(vs[p[0]], vs[p[0] + p[1]])))
    print("PEAK single pair f%d vs f%d  lag=%d  corr=%.4f" % (
        nums[i], nums[i + lag], lag, float(np.dot(vs[i], vs[i + lag]))))


if __name__ == "__main__":
    main()
