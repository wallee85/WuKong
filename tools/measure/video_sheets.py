"""Contact sheets for the extracted reference video frames."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

VID = Path(r"D:\Workspace\games\WuKong\docs\refs\video")
OUT = Path(r"D:\Workspace\games\WuKong\docs\renders")


def main(per_sheet=40, cols=8, w=320):
    fs = sorted(VID.glob("v_*.png"), key=lambda p: int(p.stem.split("_")[1]))
    fs = [p for p in fs if p.stat().st_size > 1000]
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    n = 0
    for start in range(0, len(fs), per_sheet):
        chunk = fs[start:start + per_sheet]
        h = int(w * 9 / 16)
        rows = (len(chunk) + cols - 1) // cols
        sh = Image.new("RGB", (cols * w, rows * h), "black")
        d = ImageDraw.Draw(sh)
        for i, p in enumerate(chunk):
            im = Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS)
            x0, y0 = (i % cols) * w, (i // cols) * h
            sh.paste(im, (x0, y0))
            d.rectangle([x0, y0, x0 + 62, y0 + 20], fill=(0, 0, 0))
            d.text((x0 + 3, y0 + 1), p.stem[2:].lstrip("0") or "0", fill=(0, 255, 0), font=font)
        out = OUT / ("video_sheet_%02d.png" % n)
        sh.save(out)
        print(out, sh.size, chunk[0].stem, "->", chunk[-1].stem)
        n += 1


if __name__ == "__main__":
    main()
