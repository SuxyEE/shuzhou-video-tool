#!/usr/bin/env python3
"""蜜小π首发片 v2.

Real Dongdu No.2 campus plates + cut-out explorer poses + Xiaoxiao narration.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path("/workspace/mixiaopi/v2")
CAMPUS = ROOT / "upload" / "campus"
CHAR_DIR = ROOT / "upload" / "char"
GEN = ROOT / "gen"
WORK = ROOT / "work"
PNG = WORK / "png"
VOICE = WORK / "voice"
ASS = WORK / "ass"
SEGS = WORK / "segs"
ART = ROOT / "artifacts"
FONT = Path("/workspace/src/assets/fonts/NotoSansSC-Regular.ttf")
FONTS = FONT.parent

W, H, FPS = 1920, 1080, 30
HEAD, TAIL, TARGET = 3.0, 2.0, 182.0
VOICE_NAME = "zh-CN-XiaoxiaoNeural"

GEN_SRC = {
    "wave": "/opt/cursor/artifacts/assets/mixiaopi_char_wave.jpg",
    "look": "/opt/cursor/artifacts/assets/mixiaopi_char_look.jpg",
    "fly": "/opt/cursor/artifacts/assets/mixiaopi_char_fly.jpg",
    "stars_a": "/opt/cursor/artifacts/assets/mixiaopi_stars_a.jpg",
    "stars_b": "/opt/cursor/artifacts/assets/mixiaopi_stars_b.jpg",
    "front_gen": "/opt/cursor/artifacts/assets/mixiaopi_char_front.jpg",
}

# Standing pose uses the approved explorer drawing. Wave / look / fly are
# generated from that reference so the film can change pose.
SEGMENTS = [
    {
        "title": "开场",
        "char": "wave",
        "motion": "right",
        "side": "right",
        "h": 530,
        "shots": [
            {"kind": "video", "src": "enter.mp4", "ss": 0.35, "src_len": 10.0, "pan": "ltr", "zoom": 1.07, "weight": 1.45, "grade": "campus"},
            {"kind": "video", "src": "gate1.mp4", "ss": 0.15, "src_len": 5.7, "pan": "hold", "zoom": 1.08, "weight": 1.0, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "蜜小π", "text": "蜜小π", "kicker": "学校 IP"},
            {"anchor": "厦门市东渡第二小学", "text": "厦门市东渡第二小学"},
            {"anchor": "今天就让我", "text": "π 是什么？", "kicker": "跟着蜜小π"},
        ],
    },
    {
        "title": "理念",
        "char": "front",
        "motion": "left",
        "side": "left",
        "h": 520,
        "shots": [
            {"kind": "video", "src": "front_field.mp4", "ss": 0.25, "src_len": 9.6, "pan": "ltr", "zoom": 1.07, "weight": 1.25, "grade": "campus"},
            {"kind": "video", "src": "playground1.mp4", "ss": 0.3, "src_len": 8.6, "pan": "rtl", "zoom": 1.06, "weight": 1.15, "grade": "campus"},
            {"kind": "video", "src": "playground2.mp4", "ss": 0.2, "src_len": 6.6, "pan": "hold", "zoom": 1.06, "weight": 0.85, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "自然教育", "text": "自然教育 · 自主发展"},
            {"anchor": "全学科阅读", "text": "全学科阅读"},
            {"anchor": "思维生长", "text": "思维生长"},
        ],
    },
    {
        "title": "自然π",
        "char": "look",
        "motion": "right",
        "side": "right",
        "h": 530,
        "shots": [
            {"kind": "video", "src": "clip_extra.mp4", "ss": 0.12, "src_len": 4.05, "pan": "hold", "zoom": 1.1, "weight": 0.65, "grade": "campus"},
            {"kind": "video", "src": "front_field.mp4", "ss": 0.35, "src_len": 9.4, "pan": "rtl", "zoom": 1.08, "weight": 1.2, "grade": "campus"},
            {"kind": "video", "src": "playground3.mp4", "ss": 0.3, "src_len": 9.4, "pan": "ltr", "zoom": 1.07, "weight": 1.15, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "自然π", "text": "自然π", "kicker": "2024", "place": True},
            {"anchor": "植物和昆虫", "text": "植物与昆虫"},
            {"anchor": "一整个生态", "text": "一整个生态"},
        ],
    },
    {
        "title": "银河π",
        "char": "fly",
        "motion": "rise",
        "side": "right",
        "h": 490,
        "mode": "galaxy",
        "keys": [
            {"anchor": "银河π", "text": "银河π", "kicker": "2026", "place": True},
            {"anchor": "厦门科技馆展教中心", "text": "厦门科技馆展教中心"},
            {"anchor": "抬向头顶", "text": "抬向星空"},
        ],
    },
    {
        "title": "落地转场",
        "char": "wave",
        "motion": "top",
        "side": "right",
        "h": 520,
        "shots": [
            {"kind": "video", "src": "enter.mp4", "ss": 8.8, "src_len": 8.2, "pan": "ltr", "zoom": 1.07, "weight": 1.2, "grade": "campus"},
            {"kind": "video", "src": "gate2.mp4", "ss": 0.2, "src_len": 7.3, "pan": "hold", "zoom": 1.08, "weight": 1.0, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "生态探秘博物馆", "text": "生态探秘博物馆", "place": True},
            {"anchor": "跟我看看", "text": "跟我看看东二"},
        ],
    },
    {
        "title": "马年形象墙",
        "char": "front",
        "motion": "settle",
        "side": "left",
        "h": 390,
        "shots": [
            {"kind": "video", "src": "thousand_horses.mp4", "ss": 7.0, "src_len": 16.0, "pan": "hold", "zoom": 1.04, "weight": 1, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "马年形象墙", "text": "马年形象墙", "place": True},
            {"anchor": "1100", "text": "1100 个孩子"},
        ],
    },
    {
        "title": "π空间等",
        "char": "front",
        "motion": "right",
        "side": "right",
        "h": 470,
        "note": "校园外景",
        "shots": [
            {"kind": "video", "src": "gate2.mp4", "ss": 0.35, "src_len": 7.1, "pan": "rtl", "zoom": 1.08, "weight": 1.0, "grade": "campus"},
            {"kind": "video", "src": "enter.mp4", "ss": 1.6, "src_len": 7.4, "pan": "up", "zoom": 1.1, "weight": 1.05, "grade": "campus"},
            {"kind": "video", "src": "front_field.mp4", "ss": 0.8, "src_len": 8.6, "pan": "hold", "zoom": 1.07, "weight": 1.0, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "π空间", "text": "π空间", "kicker": "校园外景", "place": True},
            {"anchor": "图书馆", "text": "图书馆", "kicker": "校园外景", "place": True},
            {"anchor": "奇点工坊", "text": "奇点工坊", "kicker": "校园外景", "place": True},
            {"anchor": "馆长信箱", "text": "CC 馆长信箱", "kicker": "校园外景", "place": True},
        ],
    },
    {
        "title": "共建自然",
        "char": "look",
        "motion": "left",
        "side": "left",
        "h": 510,
        "shots": [
            {"kind": "video", "src": "clip_extra.mp4", "ss": 0.15, "src_len": 4.0, "pan": "hold", "zoom": 1.12, "weight": 0.7, "grade": "campus"},
            {"kind": "video", "src": "playground3.mp4", "ss": 0.45, "src_len": 9.0, "pan": "ltr", "zoom": 1.07, "weight": 1.15, "grade": "campus"},
            {"kind": "video", "src": "front_field.mp4", "ss": 0.4, "src_len": 8.8, "pan": "down", "zoom": 1.08, "weight": 1.0, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "共建花园", "text": "自然而然共建花园"},
            {"anchor": "半野观察园", "text": "半野观察园"},
            {"anchor": "有序栖境", "text": "有序栖境"},
        ],
    },
    {
        "title": "操场",
        "char": "front",
        "motion": "run",
        "side": "right",
        "h": 500,
        "shots": [
            {"kind": "video", "src": "playground1.mp4", "ss": 0.35, "src_len": 8.5, "pan": "ltr", "zoom": 1.05, "weight": 1.3, "grade": "campus"},
            {"kind": "video", "src": "playground3.mp4", "ss": 1.2, "src_len": 8.2, "pan": "hold", "zoom": 1.05, "weight": 1.0, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "操场", "text": "操场"},
            {"anchor": "绿语花园", "text": "绿语花园"},
        ],
    },
    {
        "title": "专业教室",
        "char": "front",
        "motion": "settle",
        "side": "left",
        "h": 450,
        "note": "教学楼外立面",
        "shots": [
            {"kind": "video", "src": "enter.mp4", "ss": 14.0, "src_len": 6.6, "pan": "hold", "zoom": 1.08, "weight": 1.0, "grade": "campus"},
            {"kind": "video", "src": "playground2.mp4", "ss": 0.25, "src_len": 6.5, "pan": "up", "zoom": 1.1, "weight": 1.0, "grade": "campus"},
        ],
        "keys": [
            {"anchor": "美术教室", "text": "美术教室", "kicker": "教学楼外立面", "place": True},
            {"anchor": "科学教室", "text": "科学教室", "kicker": "教学楼外立面", "place": True},
        ],
    },
    {
        "title": "结尾",
        "char": "wave",
        "motion": "settle",
        "side": "right",
        "h": 430,
        "mode": "finale",
        "keys": [
            {"anchor": "读世界", "text": "读世界 · 长思维"},
            {"anchor": "让生命自然生长", "text": "让生命自然生长"},
        ],
    },
]


def run(cmd, label):
    print(f"\n== {label} ==", flush=True)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace")
        print(err[-6000:])
        raise SystemExit(f"failed: {label}")
    return p


def probe_dur(path: Path) -> float:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(p.stdout.strip())


def snap(sec: float) -> float:
    return round(sec * FPS) / FPS


def even(n: float) -> int:
    n = int(round(n))
    return n if n % 2 == 0 else n + 1


_DURS: dict[str, float] = {}


def media_dur(name: str) -> float:
    if name not in _DURS:
        _DURS[name] = probe_dur(CAMPUS / name)
    return _DURS[name]


# ---------- assets ----------

def cutout_white(src: Path, dst: Path, crop_box=None, keep_nearby=True):
    im = Image.open(src).convert("RGB")
    if crop_box:
        im = im.crop(crop_box)
    rgb = np.asarray(im).astype(np.int16)
    mn = rgb.min(axis=2)
    mx = rgb.max(axis=2)
    sat = mx - mn
    white = (mn >= 248) & (sat <= 10)
    lab, n = ndimage.label(white, structure=np.ones((3, 3), dtype=int))
    if n:
        edge = np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
        edge = edge[edge > 0]
        bg = np.isin(lab, edge) if len(edge) else np.zeros(white.shape, bool)
    else:
        bg = np.zeros(white.shape, bool)
    # one-pixel halo only: very light pixels touching the backdrop
    ring = ndimage.binary_dilation(bg, iterations=1) & ~bg
    bg = bg | (ring & (mn >= 246) & (sat <= 12))
    dist = ndimage.distance_transform_edt(~bg)
    lum = rgb.mean(axis=2)
    alpha = np.where(bg, 0, 255).astype(np.float32)
    edgeband = (dist > 0) & (dist <= 2.2)
    lightness = np.clip((lum - 170.0) / 80.0, 0, 1)
    alpha[edgeband] = np.clip(255.0 * (1.0 - lightness[edgeband]) * np.clip(dist[edgeband] / 2.2, 0, 1), 0, 255)
    fg = alpha > 28
    lab2, n2 = ndimage.label(fg, structure=np.ones((3, 3), dtype=int))
    if n2:
        sizes = ndimage.sum(fg, lab2, index=range(1, n2 + 1))
        main = int(np.argmax(sizes)) + 1
        objs = ndimage.find_objects(lab2)
        ms = objs[main - 1]
        my0, my1 = ms[0].start, ms[0].stop
        mx0, mx1 = ms[1].start, ms[1].stop
        pad = 48
        keep = np.zeros(fg.shape, bool)
        for i, sl in enumerate(objs, start=1):
            if sl is None:
                continue
            area = float(sizes[i - 1])
            cy = (sl[0].start + sl[0].stop) / 2
            cx = (sl[1].start + sl[1].stop) / 2
            inside = (my0 - pad) <= cy <= (my1 + pad) and (mx0 - pad) <= cx <= (mx1 + pad)
            if i == main or (keep_nearby and inside and area > 350):
                keep |= lab2 == i
        alpha[~keep] = 0
    # shadow
    sh = np.zeros_like(alpha)
    shift = 18
    sh[shift:, :] = alpha[:-shift, :]
    sh = ndimage.gaussian_filter(sh, 8)
    shadow = np.zeros((*alpha.shape, 4), np.uint8)
    shadow[:, :, 3] = np.clip(sh * 0.42, 0, 130).astype(np.uint8)
    color = np.zeros((*alpha.shape, 4), np.uint8)
    color[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    color[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    base = Image.fromarray(shadow, "RGBA")
    base.alpha_composite(Image.fromarray(color, "RGBA"))
    bb = base.getchannel("A").getbbox()
    if not bb:
        raise SystemExit(f"empty cutout: {src}")
    m = 16
    bb = (max(0, bb[0] - m), max(0, bb[1] - m), min(base.width, bb[2] + m), min(base.height, bb[3] + m))
    out = base.crop(bb)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    fg_ratio = float((np.asarray(out.getchannel("A")) > 20).mean())
    print(f"cutout {dst.name} {out.size} fg={fg_ratio:.2f}")
    return out


def preview(char: Image.Image, name: str):
    canvas = Image.new("RGBA", (900, 900), (32, 96, 180, 255))
    sprite = char.copy()
    sprite.thumbnail((780, 780), Image.Resampling.LANCZOS)
    canvas.alpha_composite(sprite, ((900 - sprite.width) // 2, (900 - sprite.height) // 2))
    canvas.convert("RGB").save(WORK / "preview" / f"{name}.jpg", quality=90)


def _font(size):
    return ImageFont.truetype(str(FONT), size)


def _center(draw, text, font, y, fill, canvas_w, stroke=0):
    b = font.getbbox(text)
    tw = b[2] - b[0]
    x = (canvas_w - tw) / 2 - b[0]
    yy = y - b[1]
    if stroke:
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx * dx + dy * dy <= stroke * stroke + 0.2:
                    draw.text((x + dx, yy + dy), text, font=font, fill=(0, 0, 0, 150))
    draw.text((x, yy), text, font=font, fill=fill)


def render_cards():
    gold = (226, 182, 86, 255)
    white = (255, 255, 255, 255)
    cream = (232, 242, 250, 255)
    # opening
    Wd, Hd = 1200, 420
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, Wd - 7, Hd - 7), radius=30, fill=(8, 16, 34, 168))
    d.rectangle((56, 28, Wd - 56, 34), fill=gold)
    _center(d, "蜜小π", _font(104), 78, white, Wd, stroke=2)
    _center(d, "学校 IP 形象首发", _font(36), 214, cream, Wd)
    _center(d, "厦门市东渡第二小学", _font(32), 278, gold, Wd)
    d.rectangle((56, Hd - 40, Wd - 56, Hd - 34), fill=gold)
    im.save(PNG / "card_open.png")
    # end
    lines = [
        (52, "从自然π到银河π · 读世界 · 长思维", white),
        (34, "让生命自然生长 · 让爱传递", cream),
        (30, "厦门市东渡第二小学 & 自然π·校园生态探秘博物馆", gold),
    ]
    Wd, Hd = 1320, 460
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, Wd - 7, Hd - 7), radius=30, fill=(8, 16, 34, 176))
    d.rectangle((64, 36, Wd - 64, 42), fill=gold)
    y = 86
    for size, text, fill in lines:
        font = _font(size)
        # shrink until it fits
        while font.getbbox(text)[2] > Wd - 120 and size > 22:
            size -= 2
            font = _font(size)
        _center(d, text, font, y, fill, Wd, stroke=2 if size > 40 else 0)
        y += size + 36
    d.rectangle((64, Hd - 40, Wd - 64, Hd - 34), fill=gold)
    im.save(PNG / "card_end.png")
    # lower third + scrim
    h = 280
    arr = np.zeros((h, W, 4), np.uint8)
    ramp = (np.linspace(0, 1, h) ** 1.35)[:, None]
    arr[:, :, 3] = (ramp * 168).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(PNG / "lower.png")
    scrim = np.zeros((H, W, 4), np.uint8)
    scrim[:, :, 3] = 108
    Image.fromarray(scrim, "RGBA").save(PNG / "scrim.png")


def sticker_from(cut: Image.Image, dst: Path, size=210):
    sprite = cut.copy()
    sprite.thumbnail((size - 28, size - 28), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (sprite.width + 28, sprite.height + 28), (0, 0, 0, 0))
    plate = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(plate)
    dr.rounded_rectangle((2, 2, plate.width - 3, plate.height - 3), radius=26, fill=(255, 255, 255, 232), outline=(226, 182, 86, 255), width=4)
    canvas.alpha_composite(plate)
    canvas.alpha_composite(sprite, ((canvas.width - sprite.width) // 2, (canvas.height - sprite.height) // 2))
    canvas.save(dst)


def prepare_assets():
    GEN.mkdir(parents=True, exist_ok=True)
    PNG.mkdir(parents=True, exist_ok=True)
    (WORK / "preview").mkdir(parents=True, exist_ok=True)
    for key, src in GEN_SRC.items():
        if Path(src).exists():
            shutil.copy(src, GEN / Path(src).name)
    # approved drawing, drop the annotation triangle via component keep
    official = cutout_white(CHAR_DIR / "explorer_humanoid.jpg", PNG / "official.png", keep_nearby=False)
    preview(official, "official")
    wave = cutout_white(GEN / "mixiaopi_char_wave.jpg", PNG / "wave.png")
    preview(wave, "wave")
    look = cutout_white(GEN / "mixiaopi_char_look.jpg", PNG / "look.png")
    preview(look, "look")
    fly = cutout_white(GEN / "mixiaopi_char_fly.jpg", PNG / "fly.png")
    preview(fly, "fly")
    front = cutout_white(GEN / "mixiaopi_char_front.jpg", PNG / "front_gen.png")
    preview(front, "front_gen")
    plush_im = Image.open(CHAR_DIR / "plush_3view.jpg")
    plush = cutout_white(CHAR_DIR / "plush_3view.jpg", PNG / "plush.png", crop_box=(0, 0, int(plush_im.width * 0.40), plush_im.height))
    preview(plush, "plush")
    flat = cutout_white(CHAR_DIR / "flat_simple.jpg", PNG / "flat.png")
    preview(flat, "flat")
    sticker_from(plush, PNG / "sticker_plush.png", 200)
    sticker_from(flat, PNG / "sticker_flat.png", 180)
    render_cards()
    print("assets ready")


# ---------- voice / timeline ----------

def load_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2 or sr != 44100:
        raise SystemExit(f"bad wav {path}")
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return data.reshape(-1, ch)


def save_wav(path: Path, data: np.ndarray, sr=44100):
    data = np.clip(data, -1, 1)
    pcm = (data * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(pcm.shape[1] if pcm.ndim == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def silence(sec: float) -> np.ndarray:
    return np.zeros((max(0, int(round(sec * 44100))), 2), np.float32)


def find_anchor(words, anchor: str):
    spans = []
    chars = []
    for w in words:
        for ch in w["text"]:
            if ch.isspace():
                continue
            spans.append(w["start"])
            chars.append(ch)
    hay = "".join(chars)
    key = "".join(anchor.split())
    i = hay.find(key)
    if i < 0:
        return None
    return spans[i]


def cues_from_words(words, text, limit=16):
    """Break subtitles on the narration's own punctuation. Word timings omit marks."""
    stream = []
    for w in words:
        for ch in w["text"]:
            if not ch.isspace():
                stream.append((ch, w["start"], w["end"]))
    punct = set("，。；、：！？…—《》「」『』“”\"'")
    cues = []
    buf, st, en = "", None, None
    si = 0
    for ch in text:
        if ch.isspace() or ch in punct:
            if buf and ch in punct:
                cues.append([st, en, buf])
                buf, st, en = "", None, None
            continue
        if si >= len(stream):
            break
        if stream[si][0] != ch:
            found = None
            for k in range(si, min(si + 6, len(stream))):
                if stream[k][0] == ch:
                    found = k
                    break
            if found is None:
                continue
            si = found
        _, cs, ce = stream[si]
        si += 1
        if buf and len(buf) >= limit:
            cues.append([st, en, buf])
            buf, st = "", None
        if st is None:
            st = cs
        buf += ch
        en = ce
    if buf:
        cues.append([st, en, buf])
    merged = []
    for c in cues:
        if not c[2]:
            continue
        if merged and len(c[2]) <= 4 and len(merged[-1][2]) <= 8 and len(merged[-1][2]) + len(c[2]) <= limit:
            merged[-1][2] += c[2]
            merged[-1][1] = c[1]
        else:
            merged.append(c)
    for i, c in enumerate(merged):
        nxt = merged[i + 1][0] if i + 1 < len(merged) else c[1] + 0.28
        c[1] = min(max(c[1] + 0.06, c[0] + 0.28), max(c[0] + 0.2, nxt - 0.04))
    return merged


def prepare_voice_clips():
    """Trim TTS mp3s to spoken length and return per-segment records."""
    recs = []
    for i in range(11):
        meta = json.loads((VOICE / f"seg{i:02d}.json").read_text(encoding="utf-8"))
        words = meta["words"]
        mp3 = VOICE / f"seg{i:02d}.mp3"
        file_dur = probe_dur(mp3)
        end = min(file_dur, (words[-1]["end"] + 0.30) if words else file_dur)
        end = max(end, 0.4)
        wav = VOICE / f"seg{i:02d}.wav"
        run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-t", f"{end:.3f}", "-ac", "2", "-ar", "44100", str(wav)],
            f"wav seg{i:02d}",
        )
        audio = load_wav(wav)
        spoken = len(audio) / 44100
        # drop words that start after the trim
        words = [w for w in words if w["start"] < spoken - 0.02]
        got = "".join(ch for w in words for ch in w["text"] if not ch.isspace())
        exp = "".join(ch for ch in meta["text"] if not ch.isspace())
        if got != exp:
            print(f"  warn subtitle coverage seg{i}: got {len(got)} exp {len(exp)}")
        recs.append({"i": i, "text": meta["text"], "words": words, "audio": audio, "spoken": spoken})
    return recs


def assemble_timeline(recs):
    speech = sum(r["spoken"] for r in recs)
    n_gaps = 10
    # natural pause between paragraphs; hero shots can breathe a little longer
    base_gap = (TARGET - HEAD - TAIL - speech) / n_gaps
    gap = float(np.clip(base_gap, 0.16, 0.85))
    holds = {5: 1.15, 8: 1.35}  # horses, playground
    total = HEAD + speech + gap * n_gaps + TAIL + sum(holds.values())
    if total > 188.5:
        # shrink holds first
        while total > 188.0 and any(holds.values()):
            for k in list(holds):
                if holds[k] > 0:
                    holds[k] = max(0.0, holds[k] - 0.2)
                    total -= 0.2
        gap = max(0.12, gap - max(0.0, (total - 186.0) / n_gaps))
        total = HEAD + speech + gap * n_gaps + TAIL + sum(holds.values())
    if total > 189.5:
        tempo = speech / (speech - (total - 185.0))
        tempo = float(np.clip(tempo, 1.0, 1.10))
        print(f"atempo {tempo:.3f} to land near 185s (raw total {total:.1f})")
        for r in recs:
            sped = VOICE / f"seg{r['i']:02d}_fast.wav"
            run(["ffmpeg", "-y", "-v", "error", "-i", str(VOICE / f"seg{r['i']:02d}.wav"), "-filter:a", f"atempo={tempo:.4f}", "-ac", "2", "-ar", "44100", str(sped)], f"tempo {r['i']}")
            r["audio"] = load_wav(sped)
            r["spoken"] = len(r["audio"]) / 44100
            for w in r["words"]:
                w["start"] /= tempo
                w["end"] /= tempo
        speech = sum(r["spoken"] for r in recs)
        gap = float(np.clip((TARGET - HEAD - TAIL - speech) / n_gaps, 0.16, 0.7))
        total = HEAD + speech + gap * n_gaps + TAIL + sum(holds.values())
    print(f"speech {speech:.2f}s gap {gap:.2f}s holds {holds} planned {total:.2f}s")

    parts = []
    # prelude
    parts.append({"kind": "prelude", "title": "片头", "dur": snap(HEAD), "voice": None})
    for i, r in enumerate(recs):
        after = holds.get(i, 0.0) + (TAIL if i == 10 else gap)
        dur = snap(r["spoken"] + after)
        # fix snap drift so the video isn't shorter than the voice
        if dur < r["spoken"] + 0.02:
            dur = snap(r["spoken"] + after + 1 / FPS)
        parts.append({
            "kind": "seg",
            "index": i,
            "title": SEGMENTS[i]["title"],
            "dur": dur,
            "spoken": r["spoken"],
            "after": dur - r["spoken"],
            "words": r["words"],
            "text": r["text"],
            "audio": r["audio"],
            "spec": SEGMENTS[i],
        })
    return parts, total


# ---------- shot planning ----------

def pan_expr(pan: str, dur: float, zoom: float, kind: str):
    if kind == "video":
        sw, sh = even(W * zoom), even(H * zoom)
        zx, zy = sw - W, sh - H
        dur = max(dur, 0.2)
        if pan == "ltr":
            x, y = f"{zx}*(0.28+0.44*t/{dur:.3f})", f"{zy}*0.46"
        elif pan == "rtl":
            x, y = f"{zx}*(0.72-0.44*t/{dur:.3f})", f"{zy}*0.42"
        elif pan == "up":
            x, y = f"{zx}*0.50", f"{zy}*(0.78-0.55*t/{dur:.3f})"
        elif pan == "down":
            x, y = f"{zx}*0.48", f"{zy}*(0.18+0.5*t/{dur:.3f})"
        else:
            x, y = f"{zx}*0.5", f"{zy}*0.45"
        return sw, sh, x, y
    # still / stars: scale wide then crop. Expressions use in_w after scale.
    dur = max(dur, 0.2)
    if pan == "open":
        # Gate still is taller than 16:9; stay wide enough to keep the sign.
        x = f"(in_w-{W})*(0.46+0.08*t/{dur:.3f})"
        y = f"(in_h-{H})*(0.42+0.10*t/{dur:.3f})"
        scale_w = 2200
    elif pan == "end":
        x = f"(in_w-{W})*(0.58-0.10*t/{dur:.3f})"
        y = f"(in_h-{H})*(0.38+0.18*t/{dur:.3f})"
        scale_w = 2300
    elif pan == "rise":
        x = f"(in_w-{W})*(0.35+0.30*t/{dur:.3f})"
        y = f"(in_h-{H})*(0.62-0.42*t/{dur:.3f})"
        scale_w = 2400
    else:
        x = f"(in_w-{W})*0.5"
        y = f"(in_h-{H})*(0.40+0.12*t/{dur:.3f})"
        scale_w = 2300
    return scale_w, None, x, y


def grade_filter(kind_grade: str) -> str:
    if kind_grade == "stars":
        return "eq=contrast=1.06:saturation=1.14:brightness=-0.01"
    return "eq=contrast=1.04:saturation=1.06:gamma=1.02"


def plan_normal(shots, dur, xfade=0.40):
    shots = [dict(s) for s in shots]
    if dur < 6.5:
        shots = shots[:1]
    n = len(shots)
    fd = xfade if n > 1 else 0.0
    need = dur + fd * (n - 1)
    weights = [s.get("weight", 1.0) for s in shots]
    caps = []
    for s in shots:
        if s["kind"] == "video":
            avail = max(0.4, media_dur(s["src"]) - s["ss"] - 0.05)
            s["src_len"] = min(s["src_len"], avail)
            caps.append(s["src_len"] * 1.7)
        else:
            caps.append(999.0)
    outs = [0.0] * n
    active = set(range(n))
    remaining = need
    for _ in range(8):
        if not active or remaining <= 0.04:
            break
        wsum = sum(weights[i] for i in active) or 1
        capped = False
        for i in list(active):
            share = remaining * weights[i] / wsum
            if share > caps[i] + 0.02:
                outs[i] = caps[i]
                remaining -= caps[i]
                active.remove(i)
                capped = True
        if not capped:
            for i in active:
                outs[i] = remaining * weights[i] / wsum
            remaining = 0
            active.clear()
    if remaining > 0.05:
        outs[-1] += remaining
    total = sum(outs) - fd * (n - 1)
    outs[-1] += dur - total
    plans = []
    for s, out in zip(shots, outs):
        out = max(out, 0.8)
        if s["kind"] == "video":
            use = min(s["src_len"], out)
            if out > s["src_len"]:
                use = s["src_len"]
            use = max(0.35, use)
            slow = (out * 1.03) / use
        else:
            use, slow = out, 1.0
        item = dict(s)
        item.update(out=out, use=use, slow=slow, join="fade", join_d=fd if plans else 0.0)
        plans.append(item)
    # rebalance exact duration
    acc = plans[0]["out"]
    for p in plans[1:]:
        acc += p["out"] - p["join_d"]
    plans[-1]["out"] += dur - acc
    if plans[-1]["kind"] == "video":
        plans[-1]["slow"] = (plans[-1]["out"] * 1.03) / max(0.35, plans[-1]["use"])
    return plans


def plan_segment(part):
    dur = part["dur"]
    if part["kind"] == "prelude":
        return [{
            "kind": "still", "src": "school_gate.jpg", "ss": 0, "pan": "open", "zoom": 1.2,
            "grade": "still", "out": dur, "use": dur, "slow": 1, "join": "fade", "join_d": 0,
        }]
    spec = part["spec"]
    mode = spec.get("mode", "normal")
    words = part["words"]
    if mode == "galaxy":
        anchor = find_anchor(words, "当孩子们把目光") or find_anchor(words, "抬向头顶")
        campus = dur * 0.40
        if anchor:
            campus = max(5.2, min(anchor + 0.15, dur * 0.52))
        campus = min(campus, dur - 6.0)
        fd1 = 1.20
        remain_vis = dur - campus
        # two star plates if there is room
        if remain_vis > 8.5:
            fd2 = 0.85
            star_sum = remain_vis + fd1 + fd2
            a_out = star_sum * 0.48
            b_out = star_sum - a_out
            plans = [
                {"kind": "video", "src": "front_field.mp4", "ss": 0.3, "src_len": 9.5, "pan": "up", "zoom": 1.16, "grade": "campus", "out": campus, "join": "fade", "join_d": 0},
                {"kind": "stars", "src": "mixiaopi_stars_a.jpg", "pan": "rise", "grade": "stars", "out": a_out, "join": "smoothup", "join_d": fd1},
                {"kind": "stars", "src": "mixiaopi_stars_b.jpg", "pan": "rise", "grade": "stars", "out": b_out, "join": "fade", "join_d": fd2},
            ]
        else:
            a_out = remain_vis + fd1
            plans = [
                {"kind": "video", "src": "front_field.mp4", "ss": 0.3, "src_len": 9.5, "pan": "up", "zoom": 1.16, "grade": "campus", "out": campus, "join": "fade", "join_d": 0},
                {"kind": "stars", "src": "mixiaopi_stars_a.jpg", "pan": "rise", "grade": "stars", "out": a_out, "join": "smoothup", "join_d": fd1},
            ]
        for p in plans:
            if p["kind"] == "video":
                avail = max(0.4, media_dur(p["src"]) - p["ss"] - 0.05)
                p["use"] = min(p["src_len"], avail, p["out"])
                p["use"] = max(0.4, p["use"])
                p["slow"] = (p["out"] * 1.03) / p["use"]
            else:
                p["use"] = p["out"]
                p["slow"] = 1.0
        acc = plans[0]["out"]
        for p in plans[1:]:
            acc += p["out"] - p["join_d"]
        plans[-1]["out"] += dur - acc
        return plans
    if mode == "finale":
        still = min(7.2, max(5.4, dur * 0.34))
        rest = dur - still
        fd = 0.45
        # two campus shots then the gate still; overlap two joins
        need = rest + still + fd * 2
        # allocate rest across gate2 + enter
        g_out = rest * 0.46 + fd * 0.5
        e_out = rest * 0.54 + fd * 0.5
        # g+e+still - 2*fd = dur
        # set precisely
        g_out = max(3.2, rest * 0.48)
        e_out = max(3.2, rest - g_out + fd)
        s_out = dur - (g_out + e_out - 2 * fd)
        if s_out < 4.8:
            s_out = 4.8
            # shrink e
            e_out = dur - s_out - g_out + 2 * fd
        plans = [
            {"kind": "video", "src": "gate2.mp4", "ss": 0.25, "src_len": 7.2, "pan": "hold", "zoom": 1.08, "grade": "campus", "out": g_out, "join_d": 0, "join": "fade"},
            {"kind": "video", "src": "enter.mp4", "ss": 8.2, "src_len": 8.0, "pan": "ltr", "zoom": 1.07, "grade": "campus", "out": e_out, "join_d": fd, "join": "fade"},
            {"kind": "still", "src": "school_gate.jpg", "pan": "end", "grade": "still", "out": s_out, "join_d": fd, "join": "fade", "use": s_out, "slow": 1},
        ]
        for p in plans:
            if p["kind"] == "video":
                avail = max(0.4, media_dur(p["src"]) - p["ss"] - 0.05)
                p["use"] = min(p.get("src_len", avail), avail)
                if p["out"] <= p["use"]:
                    p["use"] = max(0.4, min(p["use"], p["out"]))
                p["slow"] = (p["out"] * 1.03) / max(0.4, p["use"])
        acc = plans[0]["out"]
        for p in plans[1:]:
            acc += p["out"] - p["join_d"]
        plans[-1]["out"] += dur - acc
        return plans
    return plan_normal(spec["shots"], dur)


def shot_filter(p) -> str:
    dur = max(0.3, p["out"])
    sw, sh, x, y = pan_expr(p.get("pan", "hold"), dur, p.get("zoom", 1.07), "video" if p["kind"] == "video" else "still")
    grade = grade_filter(p.get("grade", "campus"))
    if p["kind"] == "video":
        ss = p["ss"]
        use = p["use"]
        slow = p["slow"]
        return (
            f"trim=start={ss:.3f}:end={ss + use + 0.08:.3f},setpts=PTS-STARTPTS,setpts=PTS*{slow:.4f},"
            f"scale={sw}:{sh}:flags=lanczos,crop={W}:{H}:x='{x}':y='{y}',"
            f"fps={FPS},setsar=1,format=yuv420p,{grade},trim=duration={dur:.3f},setpts=PTS-STARTPTS"
        )
    scale_w = sw  # pan_expr returns scale width for stills
    return (
        f"scale={scale_w}:-2:flags=lanczos,crop={W}:{H}:x='{x}':y='{y}',"
        f"fps={FPS},setsar=1,format=yuv420p,{grade},trim=duration={dur:.3f},setpts=PTS-STARTPTS"
    )


def motion_xy(motion: str, dur: float, side: str):
    by = "7*sin(t*2.05)"
    bx = "11*sin(t*1.35)"
    if motion == "right":
        x = f"if(lt(t,0.7),W-(t/0.7)*(w+26),W-w-26+{bx})"
        y = f"H-h-4+{by}"
    elif motion == "left":
        x = f"if(lt(t,0.7),-w+(t/0.7)*(w+26),26+{bx})"
        y = f"H-h-4+{by}"
    elif motion == "bottom":
        x = f"W-w-34+{bx}"
        y = f"if(lt(t,0.85),H-(t/0.85)*(h+4),H-h-4+{by})"
    elif motion == "top":
        x = f"W-w-30+{bx}"
        y = f"if(lt(t,0.8),-h+(t/0.8)*(H-4),H-h-4+{by})"
    elif motion == "rise":
        x = f"W-w-40+16*sin(t*0.55)"
        y = f"H-h-8-(t/{max(dur, 1):.3f})*430+8*sin(t*1.6)"
    elif motion == "run":
        x = f"W-w-18+26*sin(t*3.1)"
        y = f"H-h-2+6*sin(t*6.2)"
    else:
        x = f"W-w-30+{bx}" if side == "right" else f"30+{bx}"
        y = f"H-h-4+{by}"
    return x, y


def ass_time(t: float) -> str:
    if t < 0:
        t = 0
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
Style: Narr,Noto Sans SC,48,&H00FFFFFF,&H000000FF,&H00181010,&H64000000,0,0,0,0,100,100,0.5,0,1,3.2,0.8,2,40,40,36,1
Style: Key,Noto Sans SC,64,&H00FFFFFF,&H000000FF,&H00141018,&H00000000,0,0,0,0,100,100,1,0,1,4,0,7,60,60,40,1
Style: Place,Noto Sans SC,76,&H00FFFFFF,&H000000FF,&H00141018,&H00000000,0,0,0,0,100,100,1,0,1,4,0,7,60,60,40,1
Style: Kick,Noto Sans SC,28,&H0056B6E2,&H000000FF,&H00141018,&H00000000,0,0,0,0,100,100,2,0,1,2,0,7,60,60,28,1
Style: Note,Noto Sans SC,28,&H00F4FBFF,&H000000FF,&H00181010,&H00000000,0,0,0,0,100,100,1,0,1,2.4,0,9,48,48,36,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def write_ass(path: Path, part):
    lines = [ASS_HEAD]
    side = "right"
    if part["kind"] == "seg":
        spec = part["spec"]
        side = spec["side"]
        sx = 720 if side == "right" else 1200
        for st, en, text in cues_from_words(part["words"], part.get("text", "")):
            if en <= st:
                continue
            safe = text.replace("{", "(").replace("}", ")")
            lines.append(
                f"Dialogue: 0,{ass_time(st)},{ass_time(en)},Narr,,0,0,0,,{{\\an2\\pos({sx},1004)\\fad(80,80)}}{safe}\n"
            )
        # keywords
        placed = []
        for k in spec.get("keys", []):
            t0 = find_anchor(part["words"], k["anchor"])
            if t0 is None:
                print(f"  missing anchor {k['anchor']} in {spec['title']}")
                continue
            placed.append((t0, k))
        placed.sort(key=lambda z: z[0])
        for i, (t0, k) in enumerate(placed):
            t1_cap = t0 + (4.6 if k.get("place") else 3.8)
            if i + 1 < len(placed):
                t1_cap = min(t1_cap, placed[i + 1][0] - 0.08)
            t1_cap = min(t1_cap, part["dur"] - 0.15)
            if t1_cap - t0 < 1.05:
                continue
            style = "Place" if k.get("place") else "Key"
            text = k["text"].replace("{", "(").replace("}", ")")
            fs = 76 if k.get("place") else 62
            if len(text) > 12:
                fs -= 14
            elif len(text) > 8:
                fs -= 6
            y = 86
            if k.get("kicker"):
                kick = k["kicker"].replace("{", "(").replace("}", ")")
                lines.append(
                    f"Dialogue: 1,{ass_time(t0)},{ass_time(t1_cap)},Kick,,0,0,0,,{{\\an7\\pos(72,40)\\fad(160,180)}}{kick}\n"
                )
                y = 82
            lines.append(
                f"Dialogue: 2,{ass_time(t0)},{ass_time(t1_cap)},{style},,0,0,0,,{{\\an7\\pos(72,{y})\\fs{fs}\\fad(160,180)}}{text}\n"
            )
        # end-card window: hide late keywords? they are short and top-left, card is center. OK.
        if spec.get("mode") == "finale":
            # stop keywords before the card fully covers, already timed to speech
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8-sig")


def char_file(name: str) -> Path:
    if name == "front":
        return PNG / "official.png"
    return PNG / f"{name}.png"


def build_visual(part, out_path: Path):
    plans = plan_segment(part)
    # log
    desc = []
    for p in plans:
        if p["kind"] == "video":
            desc.append(f"{p['src']}@{p['ss']:.2f}+{p['use']:.2f}s x{p['slow']:.2f} -> {p['out']:.2f}s")
        else:
            desc.append(f"{p['kind']}:{p['src']} {p['out']:.2f}s")
    print("   shots:", " | ".join(desc), flush=True)
    acc = plans[0]["out"]
    for p in plans[1:]:
        acc += p["out"] - p["join_d"]
    if abs(acc - part["dur"]) > 0.12:
        print(f"   duration drift plan {acc:.3f} vs {part['dur']:.3f}")

    inputs = []
    for p in plans:
        if p["kind"] == "video":
            inputs += ["-i", str(CAMPUS / p["src"])]
        elif p["kind"] == "still":
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{p['out'] + 0.25:.3f}", "-i", str(CAMPUS / p["src"])]
        else:
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{p['out'] + 0.25:.3f}", "-i", str(GEN / p["src"])]
    # extras
    extra_start = len(plans)
    inputs += ["-framerate", str(FPS), "-loop", "1", "-i", str(PNG / "lower.png")]
    if part["kind"] == "prelude":
        char_name, motion, side, ch_h = "wave", "bottom", "right", 490
    else:
        spec = part["spec"]
        char_name, motion, side, ch_h = spec["char"], spec["motion"], spec["side"], spec["h"]
    inputs += ["-framerate", str(FPS), "-loop", "1", "-i", str(char_file(char_name))]
    idx = {"lower": extra_start, "char": extra_start + 1}
    next_i = extra_start + 2
    if part["kind"] == "prelude":
        inputs += ["-framerate", str(FPS), "-loop", "1", "-t", f"{part['dur']:.3f}", "-i", str(PNG / "card_open.png")]
        inputs += ["-framerate", str(FPS), "-loop", "1", "-i", str(PNG / "sticker_flat.png")]
        idx["card"] = next_i
        idx["sticker"] = next_i + 1
        next_i += 2
    elif part["spec"].get("mode") == "finale":
        inputs += ["-framerate", str(FPS), "-loop", "1", "-i", str(PNG / "scrim.png")]
        inputs += ["-framerate", str(FPS), "-loop", "1", "-i", str(PNG / "card_end.png")]
        idx["scrim"] = next_i
        idx["card"] = next_i + 1
        next_i += 2
    elif part["spec"]["title"] == "自然π" and (PNG / "sticker_flat.png").exists():
        inputs += ["-framerate", str(FPS), "-loop", "1", "-i", str(PNG / "sticker_flat.png")]
        idx["bug"] = next_i
        next_i += 1

    ass_path = ASS / f"{out_path.stem}.ass"
    write_ass(ass_path, part)

    chains = []
    labels = []
    for i, p in enumerate(plans):
        lab = f"s{i}"
        chains.append(f"[{i}:v]{shot_filter(p)}[{lab}]")
        labels.append(lab)
    if len(labels) == 1:
        bg = labels[0]
    else:
        prev = labels[0]
        acc_t = plans[0]["out"]
        for i in range(1, len(labels)):
            fd = plans[i]["join_d"]
            trans = plans[i]["join"]
            offset = acc_t - fd
            outl = f"x{i}"
            chains.append(
                f"[{prev}][{labels[i]}]xfade=transition={trans}:duration={fd:.3f}:offset={offset:.3f}[{outl}]"
            )
            acc_t = acc_t + plans[i]["out"] - fd
            prev = outl
        bg = prev
    chains.append(
        f"[{bg}]vignette=PI/4.2,fps={FPS},trim=duration={part['dur']:.3f},setpts=PTS-STARTPTS,format=yuv420p[bg]"
    )
    if part["kind"] == "prelude":
        chains.append(f"[bg]fade=t=in:st=0:d=0.45:color=black[bg2]")
        bgv = "bg2"
    elif part["kind"] == "seg" and part["spec"].get("mode") == "finale":
        chains.append(f"[bg]fade=t=out:st={max(0, part['dur'] - 0.65):.3f}:d=0.65:color=black[bg2]")
        bgv = "bg2"
    else:
        bgv = "bg"
    chains.append(f"[{idx['lower']}:v]format=rgba,scale={W}:280[lt]")
    chains.append(f"[{bgv}][lt]overlay=0:H-h:format=auto[v1]")
    cur = "v1"
    if "scrim" in idx:
        t0 = max(0.4, part["dur"] - 6.4)
        chains.append(
            f"[{idx['scrim']}:v]format=rgba,fade=t=in:st={t0:.3f}:d=0.55:alpha=1,fade=t=out:st={max(0, part['dur'] - 0.6):.3f}:d=0.45:alpha=1[scr]"
        )
        chains.append(f"[{cur}][scr]overlay=0:0:format=auto:shortest=1[vscr]")
        cur = "vscr"
    ass_esc = str(ass_path).replace("\\", "\\\\").replace(":", "\\:")
    fonts_esc = str(FONTS).replace("\\", "\\\\").replace(":", "\\:")
    chains.append(f"[{cur}]subtitles={ass_esc}:fontsdir={fonts_esc}[vsub]")
    cur = "vsub"
    chains.append(f"[{idx['char']}:v]scale=-1:{ch_h}:flags=lanczos,format=rgba[ch]")
    x, y = motion_xy(motion, part["dur"], side)
    chains.append(f"[{cur}][ch]overlay=x='{x}':y='{y}':format=auto:shortest=1[vch]")
    cur = "vch"
    if "card" in idx and part["kind"] == "prelude":
        chains.append(
            f"[{idx['card']}:v]format=rgba,fade=t=in:st=0.25:d=0.4:alpha=1,fade=t=out:st={max(0.4, part['dur'] - 0.45):.3f}:d=0.35:alpha=1[card]"
        )
        chains.append(f"[{cur}][card]overlay=x=(W-w)/2:y=86:format=auto:shortest=1[vcard]")
        cur = "vcard"
    if "card" in idx and part["kind"] == "seg":
        t0 = max(0.5, part["dur"] - 6.2)
        chains.append(
            f"[{idx['card']}:v]format=rgba,fade=t=in:st={t0:.3f}:d=0.45:alpha=1,fade=t=out:st={max(0, part['dur'] - 0.55):.3f}:d=0.4:alpha=1[card]"
        )
        chains.append(f"[{cur}][card]overlay=x=(W-w)/2-120:y=118:format=auto:shortest=1[vcard]")
        cur = "vcard"
    if "sticker" in idx and part["kind"] == "prelude":
        chains.append(f"[{idx['sticker']}:v]format=rgba,fade=t=in:st=0.35:d=0.3:alpha=1[stk]")
        chains.append(f"[{cur}][stk]overlay=x=40:y=36:format=auto:shortest=1[vout]")
        cur = "vout"
    elif "sticker" in idx:
        chains.append(
            f"[{idx['sticker']}:v]format=rgba,fade=t=in:st={max(0, part['dur'] - 6.0):.3f}:d=0.3:alpha=1[stk]"
        )
        chains.append(f"[{cur}][stk]overlay=x=36:y='H-h-20+5*sin(t*1.8)':format=auto:shortest=1[vout]")
        cur = "vout"
    elif "bug" in idx:
        t_bug = find_anchor(part["words"], "昆虫") or 1.0
        t1 = min(part["dur"] - 0.2, t_bug + 3.4)
        chains.append(
            f"[{idx['bug']}:v]format=rgba,fade=t=in:st={t_bug:.3f}:d=0.25:alpha=1,fade=t=out:st={max(t_bug + 0.4, t1 - 0.25):.3f}:d=0.25:alpha=1[bug]"
        )
        chains.append(f"[{cur}][bug]overlay=x=W-w-36:y=36:format=auto:shortest=1[vout]")
        cur = "vout"
    else:
        chains.append(f"[{cur}]format=yuv420p[vout]")
        cur = "vout"
    if cur != "vout":
        chains.append(f"[{cur}]format=yuv420p,fps={FPS}[vout]")
    fc = ";".join(chains)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error", *inputs,
        "-filter_complex", fc,
        "-map", "[vout]", "-t", f"{part['dur']:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-fps_mode", "cfr",
        "-video_track_timescale", "30000", "-an",
        str(out_path),
    ]
    try:
        run(cmd, out_path.name)
    except SystemExit:
        if out_path.exists():
            out_path.unlink()
        raise
    got = probe_dur(out_path)
    if abs(got - part["dur"]) > 0.25:
        print(f"   WARN duration {got:.2f} vs {part['dur']:.2f}")
    return plans


def write_bgm(path: Path, seconds: float, sr=44100):
    n = int(round(seconds * sr))
    y = np.zeros(n, np.float32)

    def add_note(freq, t0, dur, amp, decay):
        i0 = int(t0 * sr)
        if i0 >= n or freq <= 0:
            return
        i1 = min(n, i0 + int(dur * sr))
        tt = np.arange(i1 - i0) / sr
        env = np.exp(-tt * decay) * (1 - np.exp(-tt * 6))
        fade = min(int(0.45 * sr), max(1, (i1 - i0) // 4))
        env[-fade:] *= np.linspace(1, 0, fade)
        wave_ = (
            np.sin(2 * np.pi * freq * tt)
            + 0.32 * np.sin(2 * np.pi * freq * 2 * tt + 0.4)
            + 0.12 * np.sin(2 * np.pi * freq * 3 * tt + 0.2)
        )
        y[i0:i1] += (amp * wave_ * env).astype(np.float32)

    prog = [
        (0, [130.81, 196.00, 261.63, 329.63]),
        (8, [110.00, 164.81, 220.00, 329.63]),
        (16, [87.31, 174.61, 220.00, 349.23]),
        (24, [98.00, 146.83, 196.00, 293.66]),
    ]
    t = 0.0
    while t < seconds:
        for off, freqs in prog:
            if t + off > seconds:
                break
            for f in freqs:
                add_note(f, t + off, 8.4, 0.045, 0.22)
            add_note(freqs[0] / 2, t + off, 8.4, 0.06, 0.16)
        t += 32
    motif = [523.25, 659.25, 783.99, 659.25, 587.33, 783.99, 659.25, 523.25]
    for i, f in enumerate(motif * 20):
        t0 = 1.6 + i * 2.05
        if t0 > seconds - 2:
            break
        add_note(f, t0, 1.3, 0.03, 2.4)
    a = int(2.4 * sr)
    b = int(3.2 * sr)
    y[:a] *= np.linspace(0, 1, a)
    y[-b:] *= np.linspace(1, 0, b)
    peak = float(np.max(np.abs(y)) + 1e-6)
    y = y / peak * 0.85
    stereo = np.column_stack([y, y])
    save_wav(path, stereo, sr)


def mix_and_finish(video: Path, voice: np.ndarray, out_path: Path):
    vdur = probe_dur(video)
    target_n = int(round(vdur * 44100))
    if len(voice) < target_n:
        voice = np.vstack([voice, np.zeros((target_n - len(voice), 2), np.float32)])
    else:
        voice = voice[:target_n]
    peak = float(np.max(np.abs(voice)) + 1e-6)
    if peak > 0.02:
        voice = voice * (0.92 / peak)
    voice_path = WORK / "voice_full.wav"
    bgm_path = WORK / "bgm.wav"
    save_wav(voice_path, voice)
    write_bgm(bgm_path, vdur)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fc = (
        "[1:a]highpass=f=80,alimiter=limit=0.95,asplit=2[vo][vsc];"
        f"[2:a]volume=0.20,highpass=f=90,afade=t=in:st=0:d=2.2,afade=t=out:st={max(0, vdur - 3.2):.3f}:d=3.0[bm];"
        "[bm][vsc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=320:makeup=1[bd];"
        "[vo][bd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]"
    )
    run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(video), "-i", str(voice_path), "-i", str(bgm_path),
            "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-metadata", "title=蜜小π首发 v2",
            "-metadata", "artist=厦门市东渡第二小学",
            "-metadata", "comment=自然π·校园生态探秘博物馆 IP形象蜜小π",
            str(out_path),
        ],
        "mux master",
    )


def make_share(master: Path, share: Path):
    run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(master),
            "-vf", "scale=1280:720:flags=lanczos",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            "-metadata", "title=蜜小π首发 v2 分享版",
            str(share),
        ],
        "share 720p",
    )


def extract_qa(master: Path, parts):
    qa = WORK / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    times = [0.8, 2.2]
    t = 0.0
    for p in parts:
        times.append(t + min(1.3, p["dur"] * 0.35))
        times.append(t + p["dur"] * 0.62)
        t += p["dur"]
    times.append(max(0, t - 1.2))
    for i, ts in enumerate(times):
        out = qa / f"f_{i:02d}_{ts:.1f}.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(master), "-frames:v", "1", "-q:v", "3", str(out)],
            check=False,
        )
    print("qa frames", qa)


def film(resume=False, share=False):
    if not (PNG / "official.png").exists():
        prepare_assets()
    recs = prepare_voice_clips()
    parts, _planned = assemble_timeline(recs)
    # build voice sample stream aligned to parts
    chunks = []
    edit = {"voice": VOICE_NAME, "segments": []}
    t = 0.0
    for part in parts:
        if part["kind"] == "prelude":
            chunks.append(silence(part["dur"]))
            plans = None
        else:
            chunks.append(part["audio"])
            pad = part["dur"] - part["spoken"]
            chunks.append(silence(max(0, pad)))
        out = SEGS / ("prelude.mp4" if part["kind"] == "prelude" else f"seg{part['index']:02d}.mp4")
        if resume and out.exists() and out.stat().st_size > 10000:
            print("skip", out.name)
            plans = []
        else:
            plans = build_visual(part, out)
        campus = []
        if plans:
            for p in plans:
                if p["kind"] in ("video", "still"):
                    campus.append(p["src"])
                elif p["kind"] == "stars":
                    campus.append("generated:" + p["src"])
        elif part["kind"] == "prelude":
            campus = ["school_gate.jpg"]
        edit["segments"].append({
            "title": part["title"],
            "start": round(t, 2),
            "duration": round(part["dur"], 2),
            "campus": campus,
            "char": "wave" if part["kind"] == "prelude" else part["spec"]["char"],
            "motion": "bottom" if part["kind"] == "prelude" else part["spec"]["motion"],
        })
        t += part["dur"]
    voice = np.vstack(chunks)
    # concat
    lst = WORK / "concat.txt"
    lines = []
    files = [SEGS / "prelude.mp4"] + [SEGS / f"seg{i:02d}.mp4" for i in range(11)]
    for f in files:
        lines.append(f"file '{f}'\n")
    lst.write_text("".join(lines), encoding="utf-8")
    silent = WORK / "video_silent.mp4"
    try:
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], "concat copy")
    except SystemExit:
        print("concat copy failed, reencoding")
        run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "-an", str(silent)],
            "concat reencode",
        )
    vdur = probe_dur(silent)
    edit["duration_silent"] = vdur
    master = ART / "蜜小π_首发_v2.mp4"
    mix_and_finish(silent, voice, master)
    vdur = probe_dur(master)
    edit["duration"] = vdur
    (WORK / "edit.json").write_text(json.dumps(edit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MASTER {master} {vdur:.2f}s {master.stat().st_size/1e6:.1f}MB")
    extract_qa(master, parts)
    if share:
        share_path = ART / "蜜小π_分享版_v2.mp4"
        make_share(master, share_path)
        print(f"SHARE {share_path} {share_path.stat().st_size/1e6:.1f}MB")
    if not (170 <= vdur <= 190):
        print(f"WARNING duration {vdur:.2f} outside 170-190")
    return edit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", default="all", choices=["assets", "plan", "film", "share", "all"])
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    if args.step in ("assets", "all"):
        prepare_assets()
    if args.step == "plan":
        recs = prepare_voice_clips()
        parts, total = assemble_timeline(recs)
        t = 0
        for p in parts:
            extra = ""
            if p["kind"] == "seg":
                shots = plan_segment(p)
                extra = " || " + " | ".join(
                    (f"{s['src']} {s['out']:.1f}s" if s["kind"] != "video" else f"{s['src']}@{s['ss']:.1f} use {s['use']:.1f} slow {s['slow']:.2f} out {s['out']:.1f}")
                    for s in shots
                )
            print(f"{t:7.2f} +{p['dur']:5.2f}  {p['title']}{extra}")
            t += p["dur"]
        print("TOTAL", round(t, 2), "planned", round(total, 2))
    if args.step in ("film", "all"):
        film(resume=args.resume, share=(args.step == "all"))
    if args.step == "share":
        make_share(ART / "蜜小π_首发_v2.mp4", ART / "蜜小π_分享版_v2.mp4")


if __name__ == "__main__":
    main()
