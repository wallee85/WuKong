"""Split the three-view sheet and measure each figure."""

import os

import numpy as np
from PIL import Image

MAX_IMG = 255

SRC = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\refs\ref_sheet_v2.png"
OUT_DIR = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\refs"


def foreground_mask(img: Image.Image, tol: int = 22) -> np.ndarray:
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    bg = np.median(rgb[:40, :40].reshape(-1, 3), axis=0)
    return (np.abs(rgb - bg).max(axis=2) > tol)


def column_runs(mask: np.ndarray, min_width: int = 40, min_pixels: int = 20):
    counts = mask.sum(axis=0)
    active = counts > min_pixels
    runs = []
    start = None
    for x, on in enumerate(active):
        if on and start is None:
            start = x
        elif not on and start is not None:
            if x - start >= min_width:
                runs.append((start, x))
            start = None
    if start is not None and len(active) - start >= min_width:
        runs.append((start, len(active)))
    return runs


def main() -> None:
    img = Image.open(SRC)
    mask = foreground_mask(img)
    runs = column_runs(mask)
    print("runs:", runs)

    for index, (x0, x1) in enumerate(runs, start=1):
        sub = mask[:, x0:x1]
        rows = np.where(sub.any(axis=1))[0]
        y0, y1 = int(rows.min()), int(rows.max())
        height = y1 - y0
        width = x1 - x0
        crop = img.crop((x0, y0, x1, y1))
        name = {1: "ref_front.png", 2: "ref_side.png", 3: "ref_back.png"}.get(
            index, f"view_{index}.png"
        )
        crop.save(os.path.join(OUT_DIR, name))
        print(
            f"{name}: bbox=({x0},{y0})-({x1},{y1}) "
            f"h={height}px w={width}px aspect={width / height:.3f} "
            f"crop={crop.size}"
        )


if __name__ == "__main__":
    main()
