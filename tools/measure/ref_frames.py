"""Reference-frame helpers: inspect, split panels, upscale with a labelled pixel grid.

Usage:
  python ref_frames.py info
  python ref_frames.py sheet <out.png> [scale]
  python ref_frames.py grid <frame> <panel:left|right> <out.png> [scale]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REFS = Path(r"D:\Workspace\games\WuKong\docs\refs\run3")


def frames():
    return sorted(REFS.glob("c_*.png"))


def info():
    for p in frames():
        im = Image.open(p)
        print(p.name, im.size, im.mode)


def find_divider(im):
    """Return x of the darkest vertical band (the panel divider)."""
    w, h = im.size
    px = im.convert("L").load()
    best, bestx = 1e9, w // 2
    for x in range(w // 3, 2 * w // 3):
        s = 0
        for y in range(0, h, 3):
            s += px[x, y]
        s /= (h // 3)
        if s < best:
            best, bestx = s, x
    return bestx


def split(im):
    x = find_divider(im)
    return im.crop((0, 0, x - 3, im.height)), im.crop((x + 3, 0, im.width, im.height)), x


def sheet(out, scale=3):
    fs = frames()
    im0 = Image.open(fs[0])
    l, r, _ = split(im0)
    cw, ch = l.width * scale, l.height * scale
    cols, rows = 4, 4
    sh = Image.new("RGB", (cols * cw, rows * ch), "black")
    d = ImageDraw.Draw(sh)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    for i, p in enumerate(fs[:cols * rows]):
        im = Image.open(p)
        _, rp, _ = split(im)
        cell = rp.resize((cw, ch), Image.LANCZOS)
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        sh.paste(cell, (x0, y0))
        d.text((x0 + 6, y0 + 4), p.stem, fill=(0, 255, 0), font=font)
    sh.save(out)
    print("wrote", out, sh.size)


def grid(frame, panel, out, scale=5, step=10):
    im = Image.open(REFS / (frame if frame.endswith(".png") else frame + ".png"))
    l, r, dx = split(im)
    src = l if panel == "left" else r
    big = src.resize((src.width * scale, src.height * scale), Image.LANCZOS).convert("RGB")
    d = ImageDraw.Draw(big)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    for x in range(0, src.width, step):
        X = x * scale
        col = (255, 0, 0) if x % 50 == 0 else (90, 90, 90)
        d.line([(X, 0), (X, big.height)], fill=col, width=1)
        if x % 50 == 0:
            d.text((X + 2, 2), str(x), fill=(255, 255, 0), font=font)
    for y in range(0, src.height, step):
        Y = y * scale
        col = (255, 0, 0) if y % 50 == 0 else (90, 90, 90)
        d.line([(0, Y), (big.width, Y)], fill=col, width=1)
        if y % 50 == 0:
            d.text((2, Y + 1), str(y), fill=(255, 255, 0), font=font)
    big.save(out)
    print("wrote", out, big.size, "source-panel", src.size, "divider_x", dx)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"
    if cmd == "info":
        info()
    elif cmd == "sheet":
        sheet(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3)
    elif cmd == "grid":
        grid(sys.argv[2], sys.argv[3], sys.argv[4],
             int(sys.argv[5]) if len(sys.argv) > 5 else 5,
             int(sys.argv[6]) if len(sys.argv) > 6 else 10)
    else:
        raise SystemExit("unknown command " + cmd)
