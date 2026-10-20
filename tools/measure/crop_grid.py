"""Crop a region of a reference video frame, upscale, and overlay a labelled grid.

  python crop_grid.py <frame> <x0> <y0> <x1> <y1> <out.png> [scale] [step]
"""
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

VID = r"D:\Workspace\games\WuKong\docs\refs\video"


def main():
    frame, x0, y0, x1, y1, out = sys.argv[1:7]
    scale = float(sys.argv[7]) if len(sys.argv) > 7 else 3
    step = int(sys.argv[8]) if len(sys.argv) > 8 else 20
    im = Image.open("%s\\%s.png" % (VID, frame)).convert("RGB")
    src = im.crop((int(x0), int(y0), int(x1), int(y1)))
    big = src.resize((int(src.width * scale), int(src.height * scale)), Image.LANCZOS)
    big = ImageEnhance.Contrast(big).enhance(1.25)
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)
    for x in range(0, src.width, step):
        X = x * scale
        major = x % (step * 5) == 0
        d.line([(X, 0), (X, big.height)], fill=(255, 40, 40) if major else (110, 110, 110), width=1)
        if major:
            d.text((X + 2, 2), str(int(x0) + x), fill=(255, 255, 0), font=font)
    for y in range(0, src.height, step):
        Y = y * scale
        major = y % (step * 5) == 0
        d.line([(0, Y), (big.width, Y)], fill=(255, 40, 40) if major else (110, 110, 110), width=1)
        if major:
            d.text((2, Y + 1), str(int(y0) + y), fill=(255, 255, 0), font=font)
    big.save(out)
    print("wrote", out, big.size)


if __name__ == "__main__":
    main()
