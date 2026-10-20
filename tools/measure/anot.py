"""Rotoscope helper: crop reference frames, overlay a stick figure, print measured angles.

  python anot.py <spec.json> <out.png> [--no-stick]

spec.json:
{
  "scale": 2.0, "cols": 2,
  "frames": [
    {"f": "v_0250", "box": [x0, y0, x1, y1],
     "pts": {"head": [x, y], "neck": [x, y], "waist": [x, y],
             "knee_r": [x, y], "ankle_r": [x, y], "toe_r": [x, y],
             "knee_l": [x, y], "ankle_l": [x, y], "toe_l": [x, y]}}
  ]
}

Angles are reported in degrees, measured in the image plane:
  lean      torso axis (waist->neck) from vertical, positive = leaning toward +x
  thigh_*   hip->knee from vertical, positive = knee forward (+x)
  knee_*    interior knee flexion (thigh vs shin, 180 = straight)
  shin_*    knee->ankle from vertical, positive = ankle forward (+x)
  foot_*    ankle->toe from horizontal, positive = toe up
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

VID = r"D:\Workspace\games\WuKong\docs\refs\video"


def lift(im):
    a = np.asarray(im).astype(np.float32) / 255.0
    return Image.fromarray(np.clip(np.power(a, 0.78) * 255, 0, 255).astype(np.uint8))


def ang_from_vert(dx, dy):
    """Angle of the vector (dx, dy) in image coords (y down) from the -y axis."""
    return float(np.degrees(np.arctan2(dx, -dy)))


def seg_angle(p, q):
    return ang_from_vert(q[0] - p[0], q[1] - p[1])


def knee_flex(hip, knee, ankle):
    """Interior angle at the knee in degrees (180 = straight)."""
    v1 = np.array(hip, float) - np.array(knee, float)
    v2 = np.array(ankle, float) - np.array(knee, float)
    c = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


def report(spec):
    print("%-8s %-9s %-9s %-9s %-9s %-9s %-9s %-9s %-9s" % (
        "frame", "lean", "thigh_r", "knee_r", "shin_r", "thigh_l", "knee_l", "shin_l", "hip_y"))
    for fr in spec["frames"]:
        p = fr.get("pts") or {}
        need = ("waist", "neck", "knee_r", "ankle_r", "knee_l", "ankle_l")
        if not all(k in p for k in need):
            print("%-8s (incomplete)" % fr["f"])
            continue
        waist, neck = p["waist"], p["neck"]
        row = [fr["f"], "%.1f" % seg_angle(waist, neck)]
        for side in ("r", "l"):
            hip = waist
            k, a = p["knee_" + side], p["ankle_" + side]
            row += ["%.1f" % seg_angle(hip, k),
                    "%.1f" % knee_flex(hip, k, a),
                    "%.1f" % seg_angle(k, a)]
        row.append("%.0f" % waist[1])
        print("%-8s %-9s %-9s %-9s %-9s %-9s %-9s %-9s %-9s" % tuple(row))


def draw_stick(d, p, cx, cy, s, x0, y0):
    def P(k):
        if k not in p:
            return None
        return (cx + (p[k][0] - x0) * s, cy + (p[k][1] - y0) * s)

    links = [("head", "neck", (0, 255, 255)), ("neck", "waist", (255, 255, 0)),
             ("waist", "knee_r", (255, 0, 255)), ("knee_r", "ankle_r", (255, 0, 255)),
             ("ankle_r", "toe_r", (0, 255, 0)),
             ("waist", "knee_l", (0, 160, 255)), ("knee_l", "ankle_l", (0, 160, 255)),
             ("ankle_l", "toe_l", (0, 255, 120))]
    for a, b, col in links:
        A, B = P(a), P(b)
        if A and B:
            d.line([A, B], fill=col, width=2)
    for k, v in p.items():
        Q = P(k)
        d.ellipse([Q[0] - 3, Q[1] - 3, Q[0] + 3, Q[1] + 3], fill=(255, 255, 255))
        d.text((Q[0] + 4, Q[1] - 12), k, fill=(255, 255, 255), font=SMALL)


FONT = None
SMALL = None


def main():
    global FONT, SMALL
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    show_stick = "--no-stick" not in sys.argv
    scale = spec.get("scale", 2.0)
    cols = spec.get("cols", 2)
    FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)
    SMALL = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)
    cw = ch = None
    cells = []
    for fr in spec["frames"]:
        im = Image.open("%s\\%s.png" % (VID, fr["f"])).convert("RGB")
        x0, y0, x1, y1 = fr["box"]
        cells.append((fr, im.crop((x0, y0, x1, y1))))
    cw = max(c[1].width for c in cells)
    ch = max(c[1].height for c in cells)
    cw, ch = int(cw * scale), int(ch * scale)
    rows = (len(cells) + cols - 1) // cols
    M = 36
    canvas = Image.new("RGB", (cw * cols + M, ch * rows + M), (18, 18, 18))
    for i, (fr, crop) in enumerate(cells):
        x0, y0 = fr["box"][0], fr["box"][1]
        cx, cy = M + (i % cols) * cw, M + (i // cols) * ch
        crop = crop.resize((cw, ch), Image.LANCZOS)
        crop = crop.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=1))
        crop = lift(crop)
        crop = ImageEnhance.Contrast(crop).enhance(1.12)
        canvas.paste(crop, (cx, cy))
        d = ImageDraw.Draw(canvas)
        d.rectangle([cx, cy, cx + 54, cy + 16], fill=(0, 0, 0))
        d.text((cx + 3, cy + 1), fr["f"][2:], fill=(80, 255, 80), font=FONT)
        if show_stick:
            draw_stick(d, fr.get("pts") or {}, cx, cy, scale, x0, y0)
        for x in range(0, cw + 1, int(20 * scale)):
            ax = int(round(x0 + x / scale))
            X = cx + x
            lab = round(ax / 20) % 5 == 0
            d.line([(X, cy), (X, cy + ch)], fill=(200, 40, 40) if lab else (95, 95, 95), width=1)
            if lab:
                d.text((X - 9, 2), str(ax), fill=(255, 255, 90), font=FONT)
                d.text((X - 9, M + ch * rows + 3), str(ax), fill=(255, 255, 90), font=FONT)
        for y in range(0, ch + 1, int(20 * scale)):
            ay = int(round(y0 + y / scale))
            Y = cy + y
            lab = round(ay / 20) % 5 == 0
            d.line([(cx, Y), (cx + cw, Y)], fill=(200, 40, 40) if lab else (95, 95, 95), width=1)
            if lab:
                d.text((1, Y - 8), str(ay), fill=(255, 255, 90), font=FONT)
    canvas.save(out)
    print("wrote", out, canvas.size)
    report(spec)


if __name__ == "__main__":
    main()
