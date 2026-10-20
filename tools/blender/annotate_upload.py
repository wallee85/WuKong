"""Annotate the Hunyuan3D multi-view dialog screenshot."""

from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\jianxin\.dsh\attachments\v1\objects\0b\0bf2fbb50cab075dca41515687d1b4cd12df896b28497c1d60664a516c35ea01"
OUT = r"C:\Users\jianxin\Documents\deepseek-harness\default-workspace\wukong\hunyuan\upload_guide.png"

shot = Image.open(SRC).convert("RGB")
W, H = shot.size
BAND = 172
img = Image.new("RGB", (W, H + BAND), (250, 249, 246))
img.paste(shot, (0, 0))
d = ImageDraw.Draw(img, "RGBA")

font_badge = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 18)
font_legend = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 19)
font_title = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 21)

GREEN = (34, 160, 107, 255)
GRAY = (150, 155, 160, 255)
INK = (31, 35, 40, 255)
MUTED = (110, 115, 120, 255)

slots = {
    "top": (482, 84, 580, 174),
    "left45": (316, 236, 414, 326),
    "front": (482, 236, 580, 326),
    "right45": (636, 236, 734, 326),
    "left": (316, 386, 414, 476),
    "right": (636, 386, 734, 476),
    "back": (482, 530, 580, 620),
    "bottom": (482, 686, 580, 776),
}

targets = {"front": "1", "left": "2", "back": "3"}

for key, box in slots.items():
    if key in targets:
        d.rounded_rectangle(box, radius=10, outline=GREEN, width=4)
        cx, cy = box[0] + 6, box[1] + 6
        d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=GREEN)
        d.text((cx, cy), targets[key], font=font_badge, fill="white", anchor="mm")
    else:
        d.line([(box[0] + 26, box[1] + 26), (box[2] - 26, box[3] - 26)], fill=GRAY, width=3)
        d.line([(box[0] + 26, box[3] - 26), (box[2] - 26, box[1] + 26)], fill=GRAY, width=3)

# circle the 500k face-count button
d.rounded_rectangle([176, 414, 236, 452], radius=8, outline=GREEN, width=3)

d.text((24, H + 12), "只传这三张，其余留空（最少 2 张）", font=font_title, fill=INK)

legend = [
    ("1", "正图 ← front.png", "必填"),
    ("2", "左图 ← side.png", "角色左侧，鼻子朝左"),
    ("3", "背图 ← back.png", ""),
    ("4", "模型面数 ← 500k", "1.5m/1m 太重，50k 太粗"),
]
y = H + 48
for num, text, note in legend:
    d.ellipse([26, y + 2, 50, y + 26], fill=GREEN)
    d.text((38, y + 14), num, font=font_badge, fill="white", anchor="mm")
    d.text((60, y + 1), text, font=font_legend, fill=INK)
    if note:
        d.text((300, y + 1), f"（{note}）", font=font_legend, fill=MUTED)
    y += 28

img.save(OUT)
print("saved", OUT, img.size)
