#!/usr/bin/env python3
"""蜜小π首发片 v3 — keyword-synced campus film."""
from __future__ import annotations

import argparse
import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path("/workspace/mixiaopi/v3")
CLIPS = ROOT / "clips"
STILLS = ROOT / "stills"
OLD = ROOT / "old_campus"
WORK = ROOT / "work"
PNG = WORK / "png"
GEN = WORK / "gen"
SHOTS = WORK / "shots"
SEGS = WORK / "segs"
ASS = WORK / "ass"
ART = ROOT / "artifacts"
FONT_PATH = Path("/workspace/src/assets/fonts/NotoSansSC-Regular.ttf")
FONTS = FONT_PATH.parent
W, H, FPS = 1920, 1080, 30
HEAD, TAIL, TARGET = 3.0, 2.0, 182.0
VOICE = "zh-CN-XiaoxiaoNeural"

# Crop burned-in lower-thirds that fight our narration. Keep the picture.
CROP_BOTTOM = {
    "course_03.mp4", "course_09.mp4", "course_10.mp4", "course_11.mp4",
    "course_12.mp4", "course_14.mp4", "course_15.mp4", "plant.mp4", "soil.mp4",
}
CROP_TOP = {"exhibit_1.mp4", "exhibit_2.mp4", "exhibit_3.mp4"}


def run(cmd, label):
    print(f"\n== {label} ==", flush=True)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print(p.stderr.decode("utf-8", "replace")[-4000:])
        raise SystemExit(f"failed: {label}")


def probe(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def snap(sec: float) -> float:
    return max(1 / FPS, round(sec * FPS) / FPS)


def font(size):
    return ImageFont.truetype(str(FONT_PATH), size)


def find_anchor(words, anchor: str):
    spans, chars = [], []
    for w in words:
        for ch in w["text"]:
            if ch.isspace():
                continue
            spans.append(w["start"])
            chars.append(ch)
    hay = "".join(chars)
    key = "".join(ch for ch in anchor if not ch.isspace())
    i = hay.find(key)
    return None if i < 0 else spans[i]


def cutout(src: Path, dst: Path):
    rgb = np.asarray(Image.open(src).convert("RGB")).astype(np.int16)
    mn, mx = rgb.min(2), rgb.max(2)
    white = (mn >= 248) & ((mx - mn) <= 10)
    lab, n = ndimage.label(white, structure=np.ones((3, 3), np.int8))
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    edge = edge[edge > 0]
    bg = np.isin(lab, edge) if len(edge) else np.zeros(white.shape, bool)
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    fg = alpha > 20
    lab2, n2 = ndimage.label(fg, structure=np.ones((3, 3), np.int8))
    if n2:
        sizes = ndimage.sum(fg, lab2, index=range(1, n2 + 1))
        main = int(np.argmax(sizes)) + 1
        alpha[lab2 != main] = 0
    sh = np.zeros_like(alpha, np.float32)
    sh[14:, :] = alpha[:-14, :]
    sh = ndimage.gaussian_filter(sh, 7)
    shadow = np.zeros((*alpha.shape, 4), np.uint8)
    shadow[:, :, 3] = np.clip(sh * 0.4, 0, 120).astype(np.uint8)
    color = np.zeros((*alpha.shape, 4), np.uint8)
    color[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    color[:, :, 3] = alpha
    base = Image.fromarray(shadow, "RGBA")
    base.alpha_composite(Image.fromarray(color, "RGBA"))
    bb = base.getchannel("A").getbbox()
    out = base.crop((max(0, bb[0] - 12), max(0, bb[1] - 12), min(base.width, bb[2] + 12), min(base.height, bb[3] + 12)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print("cutout", out.size)


def text_center(d, text, fnt, y, fill, width, stroke=0):
    b = fnt.getbbox(text)
    x = (width - (b[2] - b[0])) / 2 - b[0]
    yy = y - b[1]
    if stroke:
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx * dx + dy * dy <= stroke * stroke:
                    d.text((x + dx, yy + dy), text, font=fnt, fill=(20, 16, 8, 180))
    d.text((x, yy), text, font=fnt, fill=fill)


def _grad(c0, c1):
    img = np.zeros((H, W, 3), np.uint8)
    t = np.linspace(0, 1, H)[:, None, None]
    img[:] = (np.array(c0) * (1 - t) + np.array(c1) * t).astype(np.uint8)
    return Image.fromarray(img, "RGB").convert("RGBA")


def render_gen(kind: str, dur: float, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = max(8, int(round(dur * 15)))
    frames = []
    rng = np.random.default_rng(3)
    stars = None
    if kind == "stars":
        stars = rng.random((420, 3))
        stars[:, 0] *= W
        stars[:, 1] *= H
    for i in range(n):
        u = i / max(1, n - 1)
        if kind == "map":
            im = _grad((18, 92, 158), (126, 206, 230))
            d = ImageDraw.Draw(im)
            # island
            d.ellipse((620, 340, 1280, 820), fill=(232, 196, 96, 255), outline=(40, 30, 10, 255), width=6)
            d.ellipse((760, 430, 1100, 700), fill=(90, 150, 72, 255))
            d.ellipse((980, 500, 1180, 680), fill=(70, 130, 78, 255))
            # west-coast dot
            pin_y = int(560 + 40 * np.sin(u * 3))
            d.ellipse((690, pin_y, 740, pin_y + 50), fill=(200, 50, 40, 255), outline=(20, 10, 10, 255), width=4)
            text_center(d, "厦门岛 · 西海岸", font(64), 150, (255, 255, 255, 255), W, 2)
            text_center(d, "东渡二小在这里", font(36), 230, (255, 236, 190, 255), W)
        elif kind == "trees":
            im = _grad((186, 224, 255), (232, 244, 220))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 760, W, H), fill=(122, 78, 42, 255))
            d.rounded_rectangle((460, 800, 1460, 900), radius=20, fill=(90, 56, 30, 255))
            text_center(d, "自然教育 · 自主发展", font(40), 828, (255, 228, 170, 255), W)
            for cx, canopy, label in ((620, (70, 140, 60), "全学科阅读"), (1240, (46, 110, 70), "思维生长")):
                d.rectangle((cx - 18, 560, cx + 18, 800), fill=(92, 58, 32, 255))
                d.ellipse((cx - 150, 300, cx + 150, 640), fill=canopy + (255,), outline=(20, 40, 20, 255), width=6)
                text_center(d, label, font(42), 250, (255, 255, 255, 255), W, 2) if False else None
                b = font(40).getbbox(label)
                d.text((cx - (b[2] - b[0]) / 2, 200), label, font=font(40), fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(20, 30, 20, 255))
            text_center(d, "两颗大树", font(54), 90, (30, 50, 40, 255), W)
        elif kind == "triptych":
            im = _grad((255, 246, 220), (220, 236, 210))
            d = ImageDraw.Draw(im)
            labels = ["一粒沙", "一片叶子", "一只凤蝶"]
            for k, lab in enumerate(labels):
                x0 = 120 + k * 600
                d.rounded_rectangle((x0, 220, x0 + 500, 780), radius=28, fill=(255, 255, 255, 255), outline=(40, 30, 20, 255), width=6)
                if k == 0:
                    rng2 = np.random.default_rng(9)
                    for _ in range(40):
                        x = int(x0 + 80 + rng2.random() * 340)
                        y = int(360 + rng2.random() * 280)
                        d.ellipse((x, y, x + 18, y + 14), fill=(196, 164, 96, 255))
                elif k == 1:
                    d.polygon([(x0 + 250, 340), (x0 + 120, 620), (x0 + 380, 620)], fill=(56, 150, 70, 255), outline=(20, 50, 20, 255))
                    d.line((x0 + 250, 430, x0 + 250, 700), fill=(30, 90, 40, 255), width=8)
                else:
                    d.ellipse((x0 + 80, 430, x0 + 250, 620), fill=(230, 120, 40, 255), outline=(40, 20, 10, 255), width=5)
                    d.ellipse((x0 + 250, 430, x0 + 420, 620), fill=(240, 160, 50, 255), outline=(40, 20, 10, 255), width=5)
                    d.ellipse((x0 + 210, 500, x0 + 290, 580), fill=(40, 30, 20, 255))
                text_center(d, lab, font(40), 820, (40, 30, 20, 255), W) if False else d.text((x0 + 140, 800), lab, font=font(36), fill=(40, 30, 20, 255))
            text_center(d, "拼成一整个生态", font(48), 120, (40, 50, 30, 255), W)
        elif kind == "stars":
            im = _grad((6, 10, 28), (18, 24, 60))
            d = ImageDraw.Draw(im)
            for x, y, b in stars:
                r = 1 + int(b * 3)
                col = int(180 + b * 75)
                d.ellipse((x, y, x + r, y + r), fill=(col, col, 255, 255))
            # pi constellation
            pts = [(860, 220), (1060, 220), (860, 380), (1060, 420), (960, 520)]
            d.line(pts[:2], fill=(255, 230, 160, 255), width=2)
            d.line([pts[0], pts[2]], fill=(255, 230, 160, 255), width=2)
            d.line([pts[1], pts[3]], fill=(255, 230, 160, 255), width=2)
            d.line([pts[2], pts[4], pts[3]], fill=(255, 230, 160, 255), width=2)
            if u > 0.25:
                text_center(d, "银河π", font(92), 640, (255, 255, 255, 255), W, 3)
                text_center(d, "从脚下的泥土，抬向星空", font(36), 760, (220, 220, 255, 255), W)
        elif kind == "mailbox":
            im = _grad((255, 244, 214), (210, 228, 196))
            d = ImageDraw.Draw(im)
            text_center(d, "CC 馆长信箱", font(60), 90, (50, 36, 20, 255), W, 2)
            text_center(d, "问题卡投递", font(34), 170, (120, 80, 30, 255), W)
            # wooden box — not a cyan locker
            d.rounded_rectangle((700, 280, 1220, 860), radius=18, fill=(150, 96, 48, 255), outline=(50, 28, 12, 255), width=8)
            d.rectangle((760, 340, 1160, 430), fill=(40, 24, 12, 255))
            d.ellipse((910, 620, 1010, 720), fill=(212, 168, 70, 255), outline=(50, 28, 12, 255), width=5)
            # card flies into the slot over the first 55%
            p = min(1.0, u / 0.55)
            cx = int(180 + p * 620)
            cy = int(520 - p * 160)
            if p < 0.98:
                d.rounded_rectangle((cx, cy, cx + 280, cy + 180), radius=14, fill=(255, 255, 255, 255), outline=(30, 30, 30, 255), width=5)
                d.text((cx + 110, cy + 40), "？", font=font(72), fill=(180, 40, 40, 255))
            text_center(d, "认真提问，值得被馆藏", font(36), 960, (50, 40, 20, 255), W)
        elif kind == "piroll":
            im = _grad((10, 16, 36), (24, 18, 48))
            d = ImageDraw.Draw(im)
            digits = "3.141592653589793238462643383279"
            shift = int(u * 700)
            d.text((180 - shift, 430), "π = " + digits + digits, font=font(64), fill=(255, 220, 140, 255))
            text_center(d, "无限不循环", font(52), 250, (255, 255, 255, 255), W, 2)
        else:
            im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        frames.append(im.convert("RGB"))
    # write via pipe
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "15", "-i", "-",
        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for fr in frames:
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        print(err[-2000:])
        raise SystemExit(f"gen failed {kind}")
    print(f"gen {kind} {dur:.2f}s")


def render_cards():
    PNG.mkdir(parents=True, exist_ok=True)
    gold = (226, 182, 86, 255)
    white = (255, 255, 255, 255)
    # open
    im = Image.new("RGBA", (1180, 380), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, 1173, 373), radius=28, fill=(8, 18, 36, 170))
    d.rectangle((50, 26, 1130, 32), fill=gold)
    text_center(d, "蜜小π", font(96), 70, white, 1180, 2)
    text_center(d, "学校 IP 形象首发", font(34), 200, (230, 240, 250, 255), 1180)
    text_center(d, "厦门市东渡第二小学", font(32), 270, gold, 1180)
    im.save(PNG / "card_open.png")
    im = Image.new("RGBA", (1360, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, 1353, 413), radius=28, fill=(8, 18, 36, 180))
    d.rectangle((48, 28, 1310, 34), fill=gold)
    text_center(d, "从自然π到银河π · 读世界 · 长思维", font(46), 70, white, 1360, 2)
    text_center(d, "让生命自然生长 · 让爱传递", font(32), 170, (230, 240, 250, 255), 1360)
    text_center(d, "厦门市东渡第二小学 & 自然π·校园生态探秘博物馆", font(28), 250, gold, 1360)
    im.save(PNG / "card_end.png")
    arr = np.zeros((260, W, 4), np.uint8)
    ramp = (np.linspace(0, 1, 260) ** 1.3)[:, None]
    arr[:, :, 3] = (ramp * 160).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(PNG / "lower.png")


# Each window starts when its anchor is spoken. parts split that window.
# kind: video (clips/ or old_campus/), still, gen
SEGMENTS = [
    {
        "title": "开场",
        "side": "right", "h": 420,
        "windows": [
            {"anchor": None, "label": "厦门岛西海岸", "parts": [{"kind": "gen", "name": "map", "max": 2.6}, {"kind": "video", "src": "playground1.mp4", "where": "old"}]},
            {"anchor": "蜜小π", "label": "蜜小π", "parts": [{"kind": "video", "src": "enter.mp4", "where": "old", "ss": 0.4}]},
            {"anchor": "东渡第二小学", "label": "厦门市东渡第二小学", "parts": [{"kind": "video", "src": "gate1.mp4", "where": "old", "ss": 0.2}]},
            {"anchor": "我们学校", "label": "学校的 π", "parts": [{"kind": "video", "src": "overview_04.mp4", "where": "clips"}]},
        ],
    },
    {
        "title": "理念",
        "side": "left", "h": 400,
        "windows": [
            {"anchor": None, "label": "育人的土壤", "parts": [{"kind": "still", "src": "garden_1.jpg"}]},
            {"anchor": "自然教育", "label": "自然教育 · 自主发展", "parts": [{"kind": "video", "src": "clip_extra.mp4", "where": "old"}]},
            {"anchor": "两颗大树", "label": "两颗大树", "parts": [
                {"kind": "gen", "name": "trees", "max": 5.0},
                {"kind": "video", "src": "overview_09.mp4", "where": "clips"},
            ]},
            {"anchor": "读世界", "label": "读世界", "parts": [{"kind": "video", "src": "overview_08.mp4", "where": "clips"}, {"kind": "still", "src": "library_2.jpg"}]},
            {"anchor": "驻足", "label": "每一处可以驻足", "parts": [{"kind": "still", "src": "sunny_1.jpg"}]},
        ],
    },
    {
        "title": "自然π",
        "side": "right", "h": 400,
        "windows": [
            {"anchor": None, "label": "2024", "parts": [{"kind": "video", "src": "course_08.mp4", "where": "clips"}]},
            {"anchor": "自然π", "label": "自然π", "parts": [{"kind": "video", "src": "course_01.mp4", "where": "clips"}, {"kind": "video", "src": "course_02.mp4", "where": "clips"}]},
            {"anchor": "三四年级", "label": "三、四年级", "parts": [{"kind": "video", "src": "course_06.mp4", "where": "clips"}]},
            {"anchor": "养苔藓", "label": "养苔藓", "parts": [{"kind": "video", "src": "moss.mp4", "where": "clips", "ss": 0.3}]},
            {"anchor": "观察校园", "label": "观察植物与昆虫", "parts": [{"kind": "video", "src": "course_07.mp4", "where": "clips"}, {"kind": "video", "src": "plant.mp4", "where": "clips", "ss": 0.4}]},
            {"anchor": "小生态", "label": "校园小生态", "parts": [{"kind": "video", "src": "soil.mp4", "where": "clips", "ss": 0.3}]},
            {"anchor": "设计旅馆", "label": "昆虫旅馆", "parts": [{"kind": "video", "src": "course_15.mp4", "where": "clips"}]},
            {"anchor": "一粒沙", "label": "沙 · 叶 · 凤蝶", "parts": [
                {"kind": "gen", "name": "triptych", "max": 3.2},
                {"kind": "video", "src": "course_03.mp4", "where": "clips"},
            ]},
        ],
    },
    {
        "title": "银河π",
        "side": "right", "h": 400, "extra": 2.4,
        "windows": [
            {"anchor": None, "label": "2026 · 银河π", "parts": [{"kind": "still", "src": "cls_exhibit_1.jpg", "bias": 0.62}]},
            {"anchor": "科技馆", "label": "厦门科技馆展教中心", "parts": [{"kind": "video", "src": "exhibit_1.mp4", "where": "clips", "ss": 0.2}]},
            {"anchor": "做中学", "label": "做中学", "parts": [{"kind": "still", "src": "workshop_1.jpg"}, {"kind": "still", "src": "cls5_1.jpg"}]},
            {"anchor": "泥土", "label": "脚下的泥土", "parts": [{"kind": "still", "src": "cls_soil_1.jpg"}]},
            {"anchor": "星空", "label": "银河π", "parts": [{"kind": "gen", "name": "stars", "max": 6.0}]},
        ],
    },
    {
        "title": "落地转场",
        "side": "right", "h": 400,
        "windows": [
            {"anchor": None, "label": "课程在生长", "parts": [{"kind": "video", "src": "overview_04.mp4", "where": "clips"}, {"kind": "still", "src": "rainbow_1.jpg"}]},
            {"anchor": "生态探秘博物馆", "label": "生态探秘博物馆", "parts": [{"kind": "video", "src": "pi_01.mp4", "where": "clips", "ss": 0.4}]},
            {"anchor": "跟我看看", "label": "跟我看看东二", "parts": [{"kind": "video", "src": "enter.mp4", "where": "old", "ss": 1.0}]},
        ],
    },
    {
        "title": "马年形象墙",
        "side": "left", "h": 320,
        "windows": [
            {"anchor": None, "label": "马年形象墙", "parts": [{"kind": "video", "src": "horse_1.mp4", "where": "clips"}]},
            {"anchor": "1100", "label": "1100 个孩子", "parts": [{"kind": "video", "src": "horse_4.mp4", "where": "clips", "ss": 0.4}]},
        ],
    },
    {
        "title": "π空间等",
        "side": "right", "h": 380,
        "windows": [
            {"anchor": None, "label": "π空间", "parts": [{"kind": "video", "src": "pi_04.mp4", "where": "clips", "ss": 0.3}, {"kind": "video", "src": "pi_08.mp4", "where": "clips", "ss": 0.3}]},
            {"anchor": "图书馆", "label": "图书馆 · 探微书馆", "parts": [{"kind": "still", "src": "library_1.jpg"}, {"kind": "video", "src": "overview_09.mp4", "where": "clips"}]},
            {"anchor": "奇点工坊", "label": "奇点工坊", "parts": [{"kind": "still", "src": "workshop_2.jpg"}, {"kind": "still", "src": "workshop_1.jpg"}]},
            {"anchor": "馆长信箱", "label": "CC 馆长信箱", "parts": [{"kind": "gen", "name": "mailbox", "max": 8.0}]},
        ],
    },
    {
        "title": "三园",
        "side": "left", "h": 380,
        "windows": [
            {"anchor": None, "label": "自然而然共建花园", "parts": [
                {"kind": "still", "src": "cls_garden_1.jpg"},
                {"kind": "still", "src": "garden_1.jpg", "graphics": "meter"},
            ]},
            {"anchor": "半野观察园", "label": "半野观察园", "parts": [{"kind": "still", "src": "banye_1.jpg"}, {"kind": "still", "src": "banye_2.jpg"}]},
            {"anchor": "有序栖境", "label": "有序栖境", "parts": [{"kind": "still", "src": "habitat_1.jpg", "graphics": "layers"}, {"kind": "still", "src": "habitat_2.jpg"}]},
        ],
    },
    {
        "title": "操场",
        "side": "right", "h": 380,
        "windows": [
            {"anchor": None, "label": "操场", "parts": [{"kind": "video", "src": "playground1.mp4", "where": "old", "ss": 0.3}]},
            {"anchor": "绿语花园", "label": "绿语花园", "parts": [{"kind": "still", "src": "sunny_2.jpg"}, {"kind": "still", "src": "sunny_3.jpg"}]},
        ],
    },
    {
        "title": "教室",
        "side": "left", "h": 360,
        "windows": [
            {"anchor": None, "label": "美术教室", "parts": [{"kind": "still", "src": "art_1.jpg"}]},
            {"anchor": "自然笔记", "label": "自然笔记", "parts": [{"kind": "still", "src": "art_2.jpg"}, {"kind": "video", "src": "course_03.mp4", "where": "clips"}]},
            {"anchor": "科学教室", "label": "科学教室", "parts": [{"kind": "still", "src": "science_2.jpg"}]},
            {"anchor": "猜想", "label": "猜想被验证", "parts": [{"kind": "still", "src": "cls6_1.jpg"}]},
        ],
    },
    {
        "title": "结尾",
        "side": "right", "h": 400,
        "windows": [
            {"anchor": None, "label": "自然π → 银河π", "parts": [{"kind": "video", "src": "course_01.mp4", "where": "clips"}, {"kind": "still", "src": "cls_exhibit_1.jpg", "bias": 0.6}]},
            {"anchor": "一间教室", "label": "从教室到校园", "parts": [{"kind": "still", "src": "cls5_1.jpg"}, {"kind": "video", "src": "overview_01.mp4", "where": "clips"}]},
            {"anchor": "读世界", "label": "读世界 · 长思维", "parts": [{"kind": "video", "src": "overview_09.mp4", "where": "clips"}]},
            {"anchor": "无限不循环", "label": "π", "parts": [
                {"kind": "gen", "name": "piroll", "max": 3.6},
                {"kind": "still", "src": "school_gate.jpg", "where": "old"},
            ]},
            {"anchor": "让生命自然生长", "label": "", "parts": [{"kind": "still", "src": "school_gate.jpg", "where": "old", "endcard": True}]},
        ],
    },
]


def resolve(part):
    if part["kind"] == "gen":
        return GEN / f"{part['name']}.mp4"
    src = part["src"]
    where = part.get("where")
    if part["kind"] == "still":
        if where == "old":
            return OLD / src
        return STILLS / src
    if part["kind"] == "video":
        return (OLD if where == "old" else CLIPS) / src
    return GEN / f"{part['name']}.mp4"


def window_times(words, windows, seg_dur):
    times = []
    for i, w in enumerate(windows):
        if i == 0 or not w.get("anchor"):
            t = 0.0 if i == 0 else None
        else:
            t = find_anchor(words, w["anchor"])
        if t is None:
            t = seg_dur * i / len(windows)
        times.append(t)
    # monotonic, keep sync: don't push a hit later than 0.15s, allow earlier clamp
    fixed = [max(0.0, times[0])]
    for i in range(1, len(times)):
        fixed.append(min(seg_dur - 0.35, max(fixed[-1] + 0.45, times[i])))
    fixed[0] = 0.0
    if fixed[-1] >= seg_dur - 0.3:
        fixed[-1] = max(fixed[-2] + 0.45 if len(fixed) > 1 else 0, seg_dur - 1.0)
    return fixed


def expand(windows, times, seg_dur):
    shots = []
    for i, w in enumerate(windows):
        end = times[i + 1] if i + 1 < len(times) else seg_dur
        dur = max(0.4, end - times[i])
        parts = w["parts"]
        # honor max on gen parts
        lengths = []
        remain = dur
        flex = []
        for j, p in enumerate(parts):
            if p.get("max") and len(parts) > 1:
                take = min(p["max"], max(0.8, dur * 0.62))
                lengths.append(take)
                remain -= take
            else:
                lengths.append(None)
                flex.append(j)
        if remain < 0.35 * max(1, len(flex)):
            # scale gen max down
            scale = dur / (sum(x for x in lengths if x) or dur)
            lengths = [None if x is None else max(0.6, x * scale) for x in lengths]
            remain = dur - sum(x for x in lengths if x)
        if flex:
            share = max(0.35, remain / len(flex))
            for j in flex:
                lengths[j] = share
        s = sum(lengths) or 1
        lengths = [x * dur / s for x in lengths]
        t = times[i]
        for p, ln in zip(parts, lengths):
            ln = snap(ln)
            item = dict(p)
            item.update(t0=t, dur=ln, label=w.get("label", ""), graphics=p.get("graphics") or w.get("graphics"))
            shots.append(item)
            t += ln
    # fix sum
    if shots:
        drift = seg_dur - (shots[-1]["t0"] + shots[-1]["dur"])
        shots[-1]["dur"] = snap(shots[-1]["dur"] + drift)
    return shots


def shot_filter(item):
    dur = item["dur"]
    kind = item["kind"]
    graphics = item.get("graphics")
    extra = ""
    if graphics == "meter":
        extra = ",drawbox=x=760:y=300:w=400:h=400:color=white@0.9:t=6"
    elif graphics == "layers":
        extra = (
            ",drawbox=x=160:y=300:w=1500:h=4:color=white@0.85:t=fill"
            ",drawbox=x=160:y=520:w=1500:h=4:color=white@0.85:t=fill"
            ",drawbox=x=160:y=760:w=1500:h=4:color=white@0.85:t=fill"
        )
    if kind == "video":
        path = resolve(item)
        src_dur = probe(path)
        ss = item.get("ss", 0.15)
        avail = max(0.4, src_dur - ss - 0.08)
        use = min(avail, dur)
        slow = dur / use if use < dur - 0.05 else 1.0
        if slow > 1.75:
            slow = 1.75
            use = min(avail, dur / slow)
        top = 0.10 if path.name in CROP_TOP else 0.0
        bot = 0.15 if path.name in CROP_BOTTOM else 0.0
        crop = ""
        if top or bot:
            crop = f"crop=iw:ih*{1 - top - bot:.3f}:0:ih*{top:.3f},"
        return (
            f"trim=start={ss:.3f}:end={ss + use + 0.06:.3f},setpts=PTS-STARTPTS,setpts=PTS*{slow:.4f},"
            f"{crop}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
            f"fps={FPS},setsar=1,format=yuv420p{extra},trim=duration={dur:.3f},setpts=PTS-STARTPTS"
        )
    if kind == "still":
        bias = item.get("bias", 0.45)
        return (
            f"scale=2300:-2:flags=lanczos,"
            f"crop={W}:{H}:x='(in_w-{W})*(0.42+0.08*t/{max(dur,0.2):.3f})':y='(in_h-{H})*{bias:.2f}',"
            f"fps={FPS},setsar=1,format=yuv420p{extra},trim=duration={dur:.3f},setpts=PTS-STARTPTS"
        )
    # gen already 1920x1080
    return (
        f"scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p{extra},"
        f"trim=duration={dur:.3f},setpts=PTS-STARTPTS"
    )


def render_shot(item, path: Path):
    src = resolve(item)
    dur = item["dur"]
    if item["kind"] == "gen":
        # render gen at least this long
        if not src.exists() or probe(src) + 0.05 < dur:
            render_gen(item["name"], max(dur, 1.2), src)
        cmd_in = ["-i", str(src)]
    elif item["kind"] == "still":
        cmd_in = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.2:.3f}", "-i", str(src)]
    else:
        cmd_in = ["-i", str(src)]
    path.parent.mkdir(parents=True, exist_ok=True)
    run(
        ["ffmpeg", "-y", "-v", "error", *cmd_in, "-vf", shot_filter(item), "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-fps_mode", "cfr", "-an", str(path)],
        path.name,
    )


def cues(words, text, limit=16):
    stream = []
    for w in words:
        for ch in w["text"]:
            if not ch.isspace():
                stream.append((ch, w["start"], w["end"]))
    punct = set("，。；、：！？…—《》「」『』“”\"'")
    out, buf, st, en, si = [], "", None, None, 0
    for ch in text:
        if ch.isspace() or ch in punct:
            if buf and ch in punct:
                out.append([st, en, buf])
                buf, st, en = "", None, None
            continue
        if si >= len(stream):
            break
        if stream[si][0] != ch:
            found = next((k for k in range(si, min(si + 6, len(stream))) if stream[k][0] == ch), None)
            if found is None:
                continue
            si = found
        _, cs, ce = stream[si]
        si += 1
        if buf and len(buf) >= limit:
            out.append([st, en, buf])
            buf, st = "", None
        if st is None:
            st = cs
        buf += ch
        en = ce
    if buf:
        out.append([st, en, buf])
    return out


def ass_time(t):
    t = max(0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narr,Noto Sans SC,46,&H00FFFFFF,&H000000FF,&H00141010,&H64000000,0,0,0,0,100,100,0,0,1,3,0.6,2,40,40,30,1
Style: Place,Noto Sans SC,58,&H00FFFFFF,&H000000FF,&H00141018,&H00000000,0,0,0,0,100,100,1,0,1,4,0,7,48,48,36,1
Style: Layer,Noto Sans SC,32,&H00E8F4FF,&H000000FF,&H00141018,&H00000000,0,0,0,0,100,100,1,0,1,2,0,7,48,48,28,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def write_ass(path: Path, shots, words, text, side, endcard_from=None):
    lines = [ASS_HEAD]
    sx = 780 if side == "right" else 1140
    for st, en, tx in cues(words, text):
        if en <= st:
            continue
        lines.append(f"Dialogue: 0,{ass_time(st)},{ass_time(min(en + 0.12, st + 6))},Narr,,0,0,0,,{{\\an2\\pos({sx},1016)}}{tx}\n")
    for s in shots:
        if not s.get("label"):
            continue
        fs = 52 if len(s["label"]) < 10 else 42
        lines.append(
            f"Dialogue: 1,{ass_time(s['t0'])},{ass_time(s['t0'] + s['dur'])},Place,,0,0,0,,{{\\an7\\pos(56,48)\\fs{fs}\\fad(120,120)}}{s['label']}\n"
        )
        if s.get("graphics") == "layers":
            lines.append(f"Dialogue: 2,{ass_time(s['t0'])},{ass_time(s['t0'] + s['dur'])},Layer,,0,0,0,,{{\\an7\\pos(180,250)}}乔木\n")
            lines.append(f"Dialogue: 2,{ass_time(s['t0'])},{ass_time(s['t0'] + s['dur'])},Layer,,0,0,0,,{{\\an7\\pos(180,470)}}灌木\n")
            lines.append(f"Dialogue: 2,{ass_time(s['t0'])},{ass_time(s['t0'] + s['dur'])},Layer,,0,0,0,,{{\\an7\\pos(180,710)}}地被\n")
        if s.get("graphics") == "meter":
            lines.append(f"Dialogue: 2,{ass_time(s['t0'])},{ass_time(s['t0'] + s['dur'])},Layer,,0,0,0,,{{\\an5\\pos(960,270)}}1㎡\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8-sig")


def composite(bg: Path, ass: Path, out: Path, dur: float, side: str, ch: int, endcard: bool):
    x = "W-w-20+8*sin(t*1.3)" if side == "right" else "24+8*sin(t*1.3)"
    y = "H-h-78+6*sin(t*2)"
    inputs = ["-i", str(bg), "-framerate", "30", "-loop", "1", "-i", str(PNG / "lower.png"),
              "-framerate", "30", "-loop", "1", "-i", str(PNG / "official.png")]
    idx_card = None
    if endcard:
        inputs += ["-framerate", "30", "-loop", "1", "-i", str(PNG / "card_end.png")]
        idx_card = 3
    fc = (
        f"[0:v]fps={FPS},trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p[v0];"
        f"[1:v]format=rgba,scale={W}:260[lt];"
        f"[v0][lt]overlay=0:H-h:format=auto[v1];"
        f"[v1]subtitles={ass}:fontsdir={FONTS}[v2];"
        f"[2:v]scale=-1:{ch}:flags=lanczos,format=rgba[ch];"
        f"[v2][ch]overlay=x='{x}':y='{y}':format=auto:shortest=1[v3]"
    )
    last = "v3"
    if endcard:
        # card for the whole segment; this segment is only the closing gate
        fc += f";[{idx_card}:v]format=rgba,fade=t=in:st=0.15:d=0.35:alpha=1[card];[v3][card]overlay=x=(W-w)/2-80:y=90:format=auto:shortest=1[v4]"
        last = "v4"
    fc += f";[{last}]format=yuv420p[vout]"
    run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vout]",
         "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr", "-video_track_timescale", "30000", "-an", str(out)],
        out.name,
    )


def load_wav(path):
    with wave.open(str(path), "rb") as w:
        n, ch = w.getnframes(), w.getnchannels()
        raw = w.readframes(n)
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, ch) / 32768.0


def save_wav(path, data, sr=44100):
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def silence(sec):
    return np.zeros((max(0, int(round(sec * 44100))), 2), np.float32)


def write_bgm(path, seconds, sr=44100):
    n = int(round(seconds * sr))
    y = np.zeros(n, np.float32)

    def note(freq, t0, dur, amp, decay):
        i0 = int(t0 * sr)
        if i0 >= n or freq <= 0:
            return
        i1 = min(n, i0 + int(dur * sr))
        tt = np.arange(i1 - i0) / sr
        env = np.exp(-tt * decay) * (1 - np.exp(-tt * 6))
        fade = min(len(tt) // 4, int(0.4 * sr)) or 1
        env[-fade:] *= np.linspace(1, 0, fade)
        wave_ = np.sin(2 * np.pi * freq * tt) + 0.28 * np.sin(4 * np.pi * freq * tt)
        y[i0:i1] += (amp * wave_ * env).astype(np.float32)

    prog = [(0, [130.81, 196.0, 261.63, 329.63]), (8, [110.0, 164.81, 220.0, 329.63]),
            (16, [87.31, 174.61, 220.0, 349.23]), (24, [98.0, 146.83, 196.0, 293.66])]
    t = 0.0
    while t < seconds:
        for off, freqs in prog:
            for f in freqs:
                note(f, t + off, 8.2, 0.04, 0.22)
            note(freqs[0] / 2, t + off, 8.2, 0.055, 0.16)
        t += 32
    motif = [523.25, 659.25, 783.99, 659.25, 587.33, 523.25]
    for i, f in enumerate(motif * 24):
        t0 = 1.5 + i * 2.2
        if t0 > seconds - 2:
            break
        note(f, t0, 1.2, 0.028, 2.3)
    a, b = int(2.2 * sr), int(3.0 * sr)
    y[:a] *= np.linspace(0, 1, a)
    y[-b:] *= np.linspace(1, 0, b)
    y = y / (np.max(np.abs(y)) + 1e-6) * 0.8
    save_wav(path, np.column_stack([y, y]), sr)


def prepare_voice():
    recs = []
    for i in range(11):
        meta = json.loads((WORK / "voice" / f"seg{i:02d}.json").read_text(encoding="utf-8"))
        mp3 = WORK / "voice" / f"seg{i:02d}.mp3"
        end = min(probe(mp3), meta["words"][-1]["end"] + 0.28)
        wav = WORK / "voice" / f"seg{i:02d}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-t", f"{end:.3f}", "-ac", "2", "-ar", "44100", str(wav)], f"wav {i}")
        audio = load_wav(wav)
        recs.append({"i": i, "text": meta["text"], "words": meta["words"], "audio": audio, "spoken": len(audio) / 44100})
    speech = sum(r["spoken"] for r in recs)
    gap = float(np.clip((TARGET - HEAD - TAIL - speech) / 10, 0.12, 0.75))
    total = HEAD + speech + gap * 10 + TAIL
    print(f"speech {speech:.2f} gap {gap:.2f} planned {total:.2f}")
    return recs, gap


def build(resume=False):
    for d in (PNG, GEN, SHOTS, SEGS, ASS, ART, WORK / "qa"):
        d.mkdir(parents=True, exist_ok=True)
    if not (PNG / "official.png").exists():
        cutout(ROOT / "char" / "explorer_humanoid.jpg", PNG / "official.png")
    render_cards()
    recs, gap = prepare_voice()
    edit = []
    gen_seconds = 0.0
    voice_chunks = [silence(HEAD)]
    # prelude
    pre = SEGS / "prelude.mp4"
    if not (resume and pre.exists() and pre.stat().st_size > 5000):
        item = {"kind": "video", "src": "overview_01.mp4", "where": "clips", "ss": 0.15, "dur": HEAD, "t0": 0, "label": ""}
        shot = SHOTS / "prelude.mp4"
        render_shot(item, shot)
        # title card composite
        inputs = ["-i", str(shot), "-framerate", "30", "-loop", "1", "-i", str(PNG / "card_open.png"),
                  "-framerate", "30", "-loop", "1", "-i", str(PNG / "official.png")]
        fc = (
            f"[0:v]fade=t=in:st=0:d=0.35,format=yuv420p[v];"
            f"[1:v]format=rgba,fade=t=in:st=0.2:d=0.35:alpha=1[c];"
            f"[v][c]overlay=x=(W-w)/2:y=70:format=auto[v2];"
            f"[2:v]scale=-1:400:flags=lanczos,format=rgba[ch];"
            f"[v2][ch]overlay=x='W-w-30':y='if(lt(t,0.7),H-(t/0.7)*(h+70),H-h-70)':format=auto:shortest=1,format=yuv420p[vout]"
        )
        run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vout]", "-t", "3.0",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
             "-fps_mode", "cfr", "-video_track_timescale", "30000", "-an", str(pre)], "prelude")
    edit.append({"title": "片头", "start": 0, "dur": HEAD, "files": ["clips/overview_01.mp4"], "gen": []})
    t_cursor = HEAD
    files = [pre]
    for rec, spec in zip(recs, SEGMENTS):
        after = TAIL if rec["i"] == 10 else gap
        seg_dur = snap(rec["spoken"] + after + spec.get("extra", 0))
        times = window_times(rec["words"], spec["windows"], seg_dur)
        shots = expand(spec["windows"], times, seg_dur)
        print(f"\n# {spec['title']} {seg_dur:.2f}s")
        used, gens = [], []
        seg_dir = SHOTS / f"s{rec['i']:02d}"
        seg_dir.mkdir(parents=True, exist_ok=True)
        shot_files = []
        for j, s in enumerate(shots):
            print(f"  {s['t0']:6.2f}+{s['dur']:4.2f} {s['kind']:5} {s.get('src') or s.get('name')}  {s.get('label','')}")
            sp = seg_dir / f"{j:02d}.mp4"
            if not (resume and sp.exists() and sp.stat().st_size > 2000):
                render_shot(s, sp)
            shot_files.append(sp)
            if s["kind"] == "gen":
                gens.append(s["name"])
                gen_seconds += s["dur"]
                used.append(f"gen:{s['name']}")
            else:
                folder = "old_campus" if s.get("where") == "old" else ("stills" if s["kind"] == "still" else "clips")
                used.append(f"{folder}/{s['src']}")
        lst = seg_dir / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in shot_files), encoding="utf-8")
        bg = seg_dir / "bg.mp4"
        if not (resume and bg.exists()):
            run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(bg)], f"bg {rec['i']}")
        ass = ASS / f"seg{rec['i']:02d}.ass"
        write_ass(ass, shots, rec["words"], rec["text"], spec["side"])
        out = SEGS / f"seg{rec['i']:02d}.mp4"
        endcard = any(s.get("endcard") for s in shots) and shots[-1].get("endcard")
        # end card only on the closing portion: composite whole segment, card enabled late via fade using last shot time
        if not (resume and out.exists() and out.stat().st_size > 5000):
            if endcard:
                composite_end(bg, ass, out, seg_dur, spec, shots)
            else:
                composite(bg, ass, out, seg_dur, spec["side"], spec["h"], False)
        # audio
        voice_chunks.append(rec["audio"])
        voice_chunks.append(silence(max(0, seg_dur - rec["spoken"])))
        edit.append({"title": spec["title"], "start": round(t_cursor, 2), "dur": round(seg_dur, 2), "files": used, "gen": gens})
        t_cursor += seg_dur
        files.append(out)
    print(f"\nGENERATED FULL-FRAME {gen_seconds:.1f}s (cap 30)")
    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in files), encoding="utf-8")
    silent = WORK / "silent.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(silent)], "concat")
    voice = np.vstack(voice_chunks)
    vdur = probe(silent)
    n = int(round(vdur * 44100))
    if len(voice) < n:
        voice = np.vstack([voice, np.zeros((n - len(voice), 2), np.float32)])
    else:
        voice = voice[:n]
    voice *= 0.92 / (np.max(np.abs(voice)) + 1e-6)
    save_wav(WORK / "voice.wav", voice)
    write_bgm(WORK / "bgm.wav", vdur)
    ART.mkdir(parents=True, exist_ok=True)
    master = ART / "蜜小π_首发_v3.mp4"
    fc = (
        "[1:a]highpass=f=80,alimiter=limit=0.95,asplit=2[vo][vsc];"
        f"[2:a]volume=0.18,highpass=f=90,afade=t=in:st=0:d=2.0,afade=t=out:st={max(0, vdur-3):.2f}:d=2.8[bm];"
        "[bm][vsc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=300[bd];"
        "[vo][bd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]"
    )
    run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(WORK / "voice.wav"), "-i", str(WORK / "bgm.wav"),
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-metadata", "title=蜜小π首发 v3", str(master)], "mux")
    dur = probe(master)
    edit_path = WORK / "edit.json"
    edit_path.write_text(json.dumps({"duration": dur, "gen_seconds": gen_seconds, "segments": edit}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MASTER {dur:.2f}s {master.stat().st_size/1024/1024:.1f} MiB gen {gen_seconds:.1f}s")
    # qa
    qa = WORK / "qa"
    qa.mkdir(exist_ok=True)
    for seg in edit:
        ts = seg["start"] + min(0.6, seg["dur"] * 0.3)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(master), "-frames:v", "1", str(qa / f"{seg['title']}_{ts:.1f}.jpg")], check=False)
    if not (170 <= dur <= 190):
        print("WARNING duration", dur)
    if gen_seconds > 30.5:
        print("WARNING gen seconds", gen_seconds)
    return master


def composite_end(bg, ass, out, dur, spec, shots):
    """End card only during the final gate shot."""
    gate = next(s for s in shots if s.get("endcard"))
    t0 = gate["t0"]
    x = "W-w-20"
    y = "H-h-78"
    inputs = ["-i", str(bg), "-framerate", "30", "-loop", "1", "-i", str(PNG / "lower.png"),
              "-framerate", "30", "-loop", "1", "-i", str(PNG / "official.png"),
              "-framerate", "30", "-loop", "1", "-i", str(PNG / "card_end.png")]
    fc = (
        f"[0:v]fps={FPS},trim=duration={dur:.3f},setpts=PTS-STARTPTS,fade=t=out:st={max(0, dur-0.6):.2f}:d=0.6,format=yuv420p[v0];"
        f"[1:v]format=rgba,scale={W}:260[lt];[v0][lt]overlay=0:H-h:format=auto[v1];"
        f"[v1]subtitles={ass}:fontsdir={FONTS}[v2];"
        f"[2:v]scale=-1:{spec['h']}:flags=lanczos,format=rgba[ch];"
        f"[v2][ch]overlay=x='{x}':y='{y}':format=auto:shortest=1[v3];"
        f"[3:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.35:alpha=1[card];"
        f"[v3][card]overlay=x=(W-w)/2-60:y=80:format=auto:shortest=1,format=yuv420p[vout]"
    )
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vout]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
         "-fps_mode", "cfr", "-video_track_timescale", "30000", "-an", str(out)], out.name)


def share(master: Path):
    out = ART / "蜜小π_分享版_v3.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(master), "-vf", "scale=1280:720:flags=lanczos",
         "-c:v", "libx264", "-preset", "veryfast", "-b:v", "1400k", "-maxrate", "1800k", "-bufsize", "3600k",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)], "share")
    print("SHARE", out.stat().st_size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="film", choices=["plan", "film", "share"])
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    if args.step == "plan":
        recs, gap = prepare_voice()
        t = HEAD
        gen = 0
        print(f"0.00 +{HEAD:.2f} 片头 overview_01")
        for rec, spec in zip(recs, SEGMENTS):
            after = TAIL if rec["i"] == 10 else gap
            seg_dur = snap(rec["spoken"] + after + spec.get("extra", 0))
            times = window_times(rec["words"], spec["windows"], seg_dur)
            shots = expand(spec["windows"], times, seg_dur)
            print(f"\n{t:.2f} +{seg_dur:.2f} {spec['title']}")
            for s in shots:
                print(f"   {s['t0']:.2f}+{s['dur']:.2f} {s['kind']} {s.get('src') or s.get('name')} | {s.get('label')}")
                if s["kind"] == "gen":
                    gen += s["dur"]
            t += seg_dur
        print("TOTAL", round(t, 2), "GEN", round(gen, 2))
    elif args.step == "film":
        master = build(resume=args.resume)
        share(master)
    elif args.step == "share":
        share(ART / "蜜小π_首发_v3.mp4")


if __name__ == "__main__":
    main()
