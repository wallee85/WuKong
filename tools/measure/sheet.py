"""Compose render sheets (and reference/render comparisons) from PNG frames.

  python sheet.py <out.png> <cols> <cell_width> <files...>
"""
import sys

from PIL import Image, ImageDraw, ImageFont


def main():
    out, cols, cellw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    files = sys.argv[4:]
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    ims = [Image.open(f).convert("RGBA") for f in files]
    ratio = cellw / ims[0].width
    cellh = int(ims[0].height * ratio)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGBA", (cellw * cols, cellh * rows), (28, 28, 30, 255))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        t = im.resize((cellw, cellh), Image.LANCZOS)
        x, y = (i % cols) * cellw, (i // cols) * cellh
        sheet.alpha_composite(t, (x, y))
        d.rectangle([x, y, x + cellw - 1, y + cellh - 1], outline=(70, 70, 70))
        name = files[i].replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
        d.rectangle([x, y, x + 9 * len(name) + 8, y + 20], fill=(0, 0, 0))
        d.text((x + 4, y + 1), name, fill=(120, 255, 120), font=font)
    sheet.convert("RGB").save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
