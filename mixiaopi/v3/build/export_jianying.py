#!/usr/bin/env python3
"""把蜜小π首发片收成一份可拷给同事的剪映专业版草稿。

轨道是分开的，方便二创：
画面、底部渐变、标题卡、蜜小π（带位置关键帧）、地点、旁白字幕、标注、旁白、背景音乐。
素材放在草稿目录里，路径用剪映的草稿占位符，导入脚本会改成同事电脑上的绝对路径。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path

import pyJianYingDraft as draft
from pyJianYingDraft import (
    AudioSegment,
    ClipSettings,
    KeyframeProperty,
    TextBorder,
    TextSegment,
    TextStyle,
    Timerange,
    TrackSpec,
    TrackType,
    VideoSegment,
    trange,
)

import build_v3 as b
import reoverlay_poses as pose

ROOT = b.ROOT
WORK = b.WORK
SHOTS = b.SHOTS
PNG = b.PNG
ART = b.ART
PLACEHOLDER = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
DRAFT_NAME = "蜜小π首发"
W, H = 1920, 1080

POSE_LABEL = {
    "wave": "挥手",
    "point_left": "左指",
    "point_right": "右指",
    "walk": "走路",
    "fly": "飞行",
    "look": "放大镜",
    "peek": "探头",
    "cheer": "欢呼",
}


def us(seconds: float) -> int:
    return int(round(float(seconds) * 1_000_000))


def probe_us(path: Path) -> int:
    return us(b.probe(path))


def eval_expr(expr: str, w: float, h: float) -> float:
    return float(eval(expr, {"__builtins__": {}}, {"W": W, "H": H, "w": w, "h": h}))


def to_transform(x: float, y: float, disp_w: float, disp_h: float) -> tuple[float, float]:
    cx = x + disp_w / 2
    cy = y + disp_h / 2
    return (cx - W / 2) / (W / 2), (H / 2 - cy) / (H / 2)


def ass_seconds(stamp: str) -> float:
    hh, mm, rest = stamp.split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(rest)


def parse_ass(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        style = parts[3]
        body = parts[9]
        pos = re.search(r"\\pos\(([\d.]+),([\d.]+)\)", body)
        text = re.sub(r"\{.*?\}", "", body).strip()
        if not text:
            continue
        rows.append({
            "style": style,
            "start": ass_seconds(parts[1]),
            "end": ass_seconds(parts[2]),
            "text": text,
            "x": float(pos.group(1)) if pos else 960,
            "y": float(pos.group(2)) if pos else 1016,
        })
    return rows


def copy_media(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".mp4":
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
             "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(dest)],
            check=True,
        )
        return dest
    if not dest.exists() or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)
    return dest


def safe_name(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]", "_", text).strip()
    return text[:40] or "clip"


def abut(items: list[dict]) -> None:
    """让主轨片段首尾相接，避免剪映主轨出现空隙。"""
    items.sort(key=lambda item: item["start"])
    for i in range(1, len(items)):
        prev = items[i - 1]
        prev_end = prev["start"] + prev["slot"]
        if items[i]["start"] < prev_end:
            prev["slot"] = max(1, items[i]["start"] - prev["start"])
        elif items[i]["start"] > prev_end:
            prev["slot"] += items[i]["start"] - prev_end


def load_pieces():
    timeline = pose.load_timeline()
    edit = json.loads((WORK / "edit.json").read_text(encoding="utf-8"))
    keys = ["prelude", "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
    if len(edit["segments"]) != len(keys):
        raise SystemExit("edit.json 段数和分镜不一致")
    plates = []
    characters = []
    texts = []
    for key, meta in zip(keys, edit["segments"]):
        shots = timeline[key]
        base = float(meta["start"])
        for j, shot in enumerate(shots):
            src = SHOTS / "prelude.mp4" if key == "prelude" else SHOTS / f"s{key}" / f"{j:02d}.mp4"
            if not src.exists():
                raise SystemExit(f"缺少画面 {src}")
            label = shot.get("label") or meta["title"]
            plates.append({
                "src": src,
                "start": us(base + shot["t0"]),
                "slot": us(shot["dur"]),
                "name": f"{meta['title']}_{j:02d}_{safe_name(label)}",
            })
            if shot.get("endcard"):
                texts.append({
                    "kind": "card",
                    "start": us(base + shot["t0"]),
                    "end": us(base + shot["t0"] + shot["dur"]),
                })
        for cue in pose.build_cues(shots, pose.seg_index(key)):
            characters.append({
                "pose": cue["pose"],
                "start": us(base + cue["a"]),
                "end": us(base + cue["c"]),
                "frm": cue["frm"],
                "to": cue["to"],
                "arc": cue["arc"],
                "h": cue["h"],
                "label": cue["label"] or meta["title"],
            })
        for row in parse_ass(WORK / "ass" / f"seg{key}.ass"):
            texts.append({
                "kind": row["style"],
                "start": us(base + row["start"]),
                "end": us(base + row["end"]),
                "text": row["text"],
                "x": row["x"],
                "y": row["y"],
            })
    abut(plates)
    total = us(edit["duration"])
    if plates:
        tail = plates[-1]["start"] + plates[-1]["slot"]
        if tail < total:
            plates[-1]["slot"] += total - tail
    return plates, characters, texts, total


def non_overlap(items: list[dict]) -> list[dict]:
    items = sorted(items, key=lambda item: (item["start"], item["end"]))
    kept = []
    for item in items:
        if item["end"] - item["start"] < 40_000:
            continue
        if kept and item["start"] < kept[-1]["end"]:
            kept[-1]["end"] = item["start"]
            if kept[-1]["end"] - kept[-1]["start"] < 40_000:
                kept.pop()
        if item["end"] - item["start"] >= 40_000:
            kept.append(item)
    return kept


def add_plate(script, item: dict, media: Path):
    file_us = probe_us(media)
    slot = item["slot"]
    if file_us <= 0 or slot <= 0:
        return
    if abs(file_us - slot) <= 20_000:
        seg = VideoSegment(
            str(media),
            trange(item["start"], slot),
            source_timerange=Timerange(0, min(file_us, slot)),
            volume=0,
        )
    elif file_us > slot:
        seg = VideoSegment(
            str(media),
            trange(item["start"], slot),
            source_timerange=Timerange(0, slot),
            volume=0,
        )
    else:
        speed = file_us / slot
        seg = VideoSegment(
            str(media),
            trange(item["start"], slot),
            source_timerange=Timerange(0, file_us),
            speed=speed,
            volume=0,
        )
    seg.material_instance.material_name = item["name"]
    script.add_segment(seg, "画面")


def add_still(script, media: Path, start: int, duration: int, track: str, name: str,
              tx: float, ty: float, scale: float):
    seg = VideoSegment(
        str(media),
        trange(start, duration),
        source_timerange=Timerange(0, duration),
        volume=0,
        clip_settings=ClipSettings(transform_x=tx, transform_y=ty, scale_x=scale, scale_y=scale),
    )
    seg.material_instance.material_name = name
    script.add_segment(seg, track)


def add_character(script, item: dict, media: Path, img_w: int, img_h: int):
    disp_h = float(item["h"])
    disp_w = img_w * disp_h / img_h
    scale = disp_h / img_h
    x0 = eval_expr(pose.SPOTS[item["frm"]][0], disp_w, disp_h)
    y0 = eval_expr(pose.SPOTS[item["frm"]][1], disp_w, disp_h)
    x1 = eval_expr(pose.SPOTS[item["to"]][0], disp_w, disp_h)
    y1 = eval_expr(pose.SPOTS[item["to"]][1], disp_w, disp_h)
    tx0, ty0 = to_transform(x0, y0, disp_w, disp_h)
    tx1, ty1 = to_transform(x1, y1, disp_w, disp_h)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + item["arc"]
    txm, tym = to_transform(mx, my, disp_w, disp_h)
    dur = item["end"] - item["start"]
    seg = VideoSegment(
        str(media),
        trange(item["start"], dur),
        source_timerange=Timerange(0, dur),
        volume=0,
        clip_settings=ClipSettings(transform_x=tx0, transform_y=ty0, scale_x=scale, scale_y=scale),
    )
    seg.material_instance.material_name = f"蜜小π_{POSE_LABEL.get(item['pose'], item['pose'])}_{item['label']}"
    seg.add_keyframe(KeyframeProperty.position_x, 0, tx0)
    seg.add_keyframe(KeyframeProperty.position_y, 0, ty0)
    seg.add_keyframe(KeyframeProperty.position_x, dur // 2, txm)
    seg.add_keyframe(KeyframeProperty.position_y, dur // 2, tym)
    seg.add_keyframe(KeyframeProperty.position_x, dur, tx1)
    seg.add_keyframe(KeyframeProperty.position_y, dur, ty1)
    script.add_segment(seg, "蜜小π")


def add_text(script, item: dict, track: str, size: float, align: int, tx: float, ty: float):
    style = TextStyle(size=size, color=(1, 1, 1), align=align, bold=track == "地点")
    border = TextBorder(color=(0.08, 0.06, 0.04), width=26)
    seg = TextSegment(
        item["text"],
        trange(item["start"], item["end"] - item["start"]),
        style=style,
        border=border,
        clip_settings=ClipSettings(transform_x=tx, transform_y=ty),
    )
    script.add_segment(seg, track)


def write_meta(draft_dir: Path, duration_us: int, materials: list[dict]):
    meta_path = draft_dir / "draft_meta_info.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    now = int(time.time() * 1000)
    meta.update({
        "draft_id": str(uuid.uuid4()).upper(),
        "draft_name": DRAFT_NAME,
        "draft_fold_path": "",
        "draft_root_path": "",
        "tm_duration": duration_us,
        "tm_draft_create": now,
        "tm_draft_modified": now,
        "draft_cover": "draft_cover.jpg",
        "draft_new_version": "80.0.0",
    })
    for group in meta["draft_materials"]:
        if group.get("type") == 0:
            group["value"] = materials
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def material_row(path: Path, kind: str, duration_us: int, width: int, height: int) -> dict:
    rel = path.as_posix().split("/Resources/", 1)[-1]
    return {
        "create_time": int(time.time()),
        "duration": duration_us,
        "extra_info": path.name,
        "file_Path": f"{PLACEHOLDER}/Resources/{rel}",
        "height": height,
        "id": uuid.uuid4().hex,
        "import_time": int(time.time()),
        "import_time_ms": int(time.time() * 1000),
        "item_source": 1,
        "md5": "",
        "metetype": kind,
        "roughcut_time_range": {"duration": duration_us, "start": 0},
        "sub_time_range": {"duration": -1, "start": -1},
        "type": 0,
        "width": width,
    }


def rewrite_paths(draft_dir: Path):
    prefixes = []
    for path in (draft_dir, draft_dir.resolve()):
        text = path.as_posix()
        if text not in prefixes:
            prefixes.append(text)
    for name in ("draft_content.json", "draft_info.json", "draft_meta_info.json"):
        path = draft_dir / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for prefix in prefixes:
            text = text.replace(prefix, PLACEHOLDER)
        path.write_text(text, encoding="utf-8")


def write_import_helpers(pack_root: Path):
    note = """蜜小π首发 · 剪映专业版草稿
请用电脑上的「剪映专业版」，不要用手机版剪映。

怎么导入
1. 双击「导入剪映.bat」（苹果电脑双击「导入剪映.command」）。
2. 脚本会把草稿拷进剪映的草稿目录，并把素材路径改成这台电脑的路径。
3. 完全退出剪映再打开。草稿列表里会出现「蜜小π首发」。

如果脚本没找到草稿目录：打开剪映专业版 → 全局设置 → 草稿位置 → 打开文件夹，把「蜜小π首发」这个文件夹放进去，再运行一次导入脚本。

轨道（从下到上）
- 画面：每镜一段实拍或插画，已经按成片裁好，可以直接替换、裁短。
- 底部渐变：字幕底下的暗角，可以关掉。
- 标题卡：片头片名和片尾落版，是图片，可以改字需另做。
- 蜜小π：8 种姿势的透明图，每段都有位置关键帧，可以拖位置、换大小、删掉重摆。
- 地点 / 旁白字幕 / 标注：文本，可以直接改字。
- 旁白、背景音乐：两条音轨，音乐音量大约是旁白的两成，可以再拉。

成片参考_720p.mp4 是已经合成好的分享版，不在时间线上，用来对照。
"""
    (pack_root / "导入说明.txt").write_text(note, encoding="utf-8")
    ps1 = r"""# 把蜜小π草稿装进这台电脑的剪映专业版
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $here "蜜小π首发"
if (-not (Test-Path $src)) { throw "找不到草稿文件夹：蜜小π首发" }

function Find-DraftRoot {
    $found = @()
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "JianyingPro\User Data\Projects\com.lveditor.draft"),
        (Join-Path $env:USERPROFILE "Documents\JianyingPro Drafts"),
        (Join-Path $env:USERPROFILE "Documents\剪映专业版\草稿")
    )
    $setting = Join-Path $env:LOCALAPPDATA "JianyingPro\User Data\Config\globalSetting"
    if (Test-Path $setting) {
        $raw = Get-Content -Raw -Encoding UTF8 $setting
        $m = [regex]::Match($raw, '"currentCustomDraftPath"\s*:\s*"([^"]+)"')
        if ($m.Success) { $candidates = @($m.Groups[1].Value.Replace('/', '\')) + $candidates }
    }
    foreach ($dir in $candidates) {
        if ($dir -and (Test-Path $dir)) { $found += (Resolve-Path $dir).Path }
    }
    return $found | Select-Object -Unique
}

$roots = @(Find-DraftRoot)
if ($roots.Count -eq 0) {
    Write-Host "没有自动找到剪映草稿目录。"
    Write-Host "请打开剪映专业版 → 全局设置 → 草稿位置，把那个文件夹拖进下面的窗口后回车。"
    $typed = Read-Host "草稿目录"
    if (-not (Test-Path $typed)) { throw "目录不存在：$typed" }
    $roots = @($typed)
}
$root = $roots[0]
$dest = Join-Path $root "蜜小π首发"
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Copy-Item -Recurse $src $dest

$placeholder = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
$abs = ((Resolve-Path $dest).Path) -replace "\\", "/"
foreach ($name in @("draft_content.json", "draft_info.json", "draft_meta_info.json")) {
    $file = Join-Path $dest $name
    if (-not (Test-Path $file)) { continue }
    $text = [IO.File]::ReadAllText($file)
    $text = $text.Replace($placeholder, $abs)
    if ($name -eq "draft_meta_info.json") {
        $rootAbs = ($root -replace "\\", "/")
        $text = $text.Replace('"draft_fold_path": ""', '"draft_fold_path": "' + $abs + '"')
        $text = $text.Replace('"draft_root_path": ""', '"draft_root_path": "' + $rootAbs + '"')
    }
    [IO.File]::WriteAllText($file, $text, [Text.UTF8Encoding]::new($false))
}
Write-Host ""
Write-Host "已放入：$dest"
Write-Host "请完全退出剪映专业版，再打开。草稿列表里选「蜜小π首发」。"
"""
    (pack_root / "导入剪映.ps1").write_bytes(b"\xef\xbb\xbf" + ps1.encode("utf-8"))
    bat = """@echo off
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0导入剪映.ps1"
echo.
pause
"""
    (pack_root / "导入剪映.bat").write_text(bat, encoding="utf-8")
    command = """#!/bin/bash
cd "$(dirname "$0")"
SRC="$(pwd)/蜜小π首发"
DEST="$HOME/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
if [ ! -d "$DEST" ]; then
  echo "没有找到剪映草稿目录：$DEST"
  echo "请在剪映专业版 → 全局设置 → 草稿位置 里确认路径，然后把「蜜小π首发」放进去，再运行："
  echo "  python3 - <<'PY'"
  echo "  # 或把下面 DEST 改成你的草稿目录后重新运行本脚本"
  echo "PY"
  exit 1
fi
rm -rf "$DEST/蜜小π首发"
cp -R "$SRC" "$DEST/蜜小π首发"
python3 - "$DEST/蜜小π首发" "$DEST" <<'PY'
import json, sys
from pathlib import Path
dest, root = Path(sys.argv[1]), Path(sys.argv[2])
placeholder = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
abs_path = dest.resolve().as_posix()
for name in ("draft_content.json", "draft_info.json", "draft_meta_info.json"):
    file = dest / name
    if not file.exists():
        continue
    text = file.read_text(encoding="utf-8").replace(placeholder, abs_path)
    if name == "draft_meta_info.json":
        meta = json.loads(text)
        meta["draft_fold_path"] = abs_path
        meta["draft_root_path"] = root.resolve().as_posix()
        meta["draft_name"] = "蜜小π首发"
        text = json.dumps(meta, ensure_ascii=False, indent=2)
    file.write_text(text, encoding="utf-8")
print("已放入：", dest)
print("请完全退出剪映专业版，再打开「蜜小π首发」。")
PY
"""
    path = pack_root / "导入剪映.command"
    path.write_text(command, encoding="utf-8")
    try:
        path.chmod(0o755)
    except OSError:
        pass


def build(out_zip: Path):
    plates, characters, texts, duration_us = load_pieces()
    characters = non_overlap(characters)
    narr = non_overlap([t for t in texts if t["kind"] == "Narr"])
    place = non_overlap([t for t in texts if t["kind"] == "Place"])
    layer = non_overlap([t for t in texts if t["kind"] == "Layer"])
    card = next((t for t in texts if t["kind"] == "card"), None)

    pack = Path("/tmp/jianying_pack")
    if pack.exists():
        shutil.rmtree(pack)
    pack.mkdir(parents=True)
    folder = draft.DraftFolder(str(pack))
    script = folder.create_draft(DRAFT_NAME, W, H, fps=30, allow_replace=True)
    draft_dir = pack / DRAFT_NAME
    res = draft_dir / "Resources" / "local"
    (res / "video").mkdir(parents=True)
    (res / "image").mkdir(parents=True)
    (res / "audio").mkdir(parents=True)
    for spec in (
        TrackSpec(TrackType.video, "画面"),
        TrackSpec(TrackType.video, "底部渐变"),
        TrackSpec(TrackType.video, "标题卡"),
        TrackSpec(TrackType.video, "蜜小π"),
        TrackSpec(TrackType.text, "地点"),
        TrackSpec(TrackType.text, "旁白字幕"),
        TrackSpec(TrackType.text, "标注"),
        TrackSpec(TrackType.audio, "旁白"),
        TrackSpec(TrackType.audio, "背景音乐"),
    ):
        script.append_track(spec)

    print(f"画面 {len(plates)} 段，蜜小π {len(characters)} 段，字幕 {len(narr)}")
    meta_rows = []
    for item in plates:
        dest = copy_media(item["src"], res / "video" / f"{item['name']}.mp4")
        add_plate(script, item, dest)
        meta_rows.append(material_row(dest, "video", probe_us(dest), W, H))

    lower = copy_media(PNG / "lower.png", res / "image" / "底部渐变.png")
    add_still(script, lower, 0, duration_us, "底部渐变", "底部渐变", 0, (H / 2 - 950) / (H / 2), 1)
    meta_rows.append(material_row(lower, "photo", duration_us, 1920, 260))

    card_open = copy_media(PNG / "card_open.png", res / "image" / "片头标题.png")
    add_still(script, card_open, 0, us(3), "标题卡", "片头标题", 0, (H / 2 - 260) / (H / 2), 1)
    meta_rows.append(material_row(card_open, "photo", us(3), 1180, 380))
    if card:
        card_end = copy_media(PNG / "card_end.png", res / "image" / "片尾落版.png")
        tx = (900 - W / 2) / (W / 2)
        ty = (H / 2 - 290) / (H / 2)
        add_still(script, card_end, card["start"], card["end"] - card["start"], "标题卡", "片尾落版", tx, ty, 1)
        meta_rows.append(material_row(card_end, "photo", card["end"] - card["start"], 1360, 420))

    from PIL import Image
    pose_box = {}
    for jpg_name, pose_name in (
        ("pose_wave.png", "wave"),
        ("pose_point_left.png", "point_left"),
        ("pose_point_right.png", "point_right"),
        ("pose_walk.png", "walk"),
        ("pose_fly.png", "fly"),
        ("pose_look.png", "look"),
        ("pose_peek.png", "peek"),
        ("pose_cheer.png", "cheer"),
    ):
        src = PNG / jpg_name
        dest = copy_media(src, res / "image" / f"蜜小π_{POSE_LABEL[pose_name]}.png")
        im = Image.open(src)
        pose_box[pose_name] = (dest, im.width, im.height)
        meta_rows.append(material_row(dest, "photo", 3_000_000, im.width, im.height))
    for item in characters:
        media, iw, ih = pose_box[item["pose"]]
        add_character(script, item, media, iw, ih)

    for item in place:
        add_text(script, item, "地点", 11, 0, (item["x"] - W / 2) / (W / 2) * 0.15 - 0.62, 0.78)
    for item in narr:
        add_text(script, item, "旁白字幕", 8, 1, (item["x"] - W / 2) / (W / 2), (H / 2 - item["y"]) / (H / 2))
    for item in layer:
        add_text(script, item, "标注", 7, 0, (item["x"] - W / 2) / (W / 2), (H / 2 - item["y"]) / (H / 2))

    voice = res / "audio" / "旁白.m4a"
    bgm = res / "audio" / "背景音乐.m4a"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(WORK / "voice.wav"), "-c:a", "aac", "-b:a", "160k", str(voice)],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(WORK / "bgm.wav"), "-c:a", "aac", "-b:a", "160k", str(bgm)],
        check=True,
    )
    voice_us = probe_us(voice)
    bgm_us = probe_us(bgm)
    use_voice = min(voice_us, duration_us)
    use_bgm = min(bgm_us, duration_us)
    script.add_segment(AudioSegment(str(voice), trange(0, use_voice), source_timerange=Timerange(0, use_voice), volume=1.0), "旁白")
    script.add_segment(AudioSegment(str(bgm), trange(0, use_bgm), source_timerange=Timerange(0, use_bgm), volume=0.22), "背景音乐")
    meta_rows.append(material_row(voice, "music", use_voice, 0, 0))
    meta_rows.append(material_row(bgm, "music", use_bgm, 0, 0))

    script.save()
    content_path = draft_dir / "draft_content.json"
    text = content_path.read_text(encoding="utf-8")
    data = json.loads(text)
    data["name"] = DRAFT_NAME
    data["id"] = str(uuid.uuid4()).upper()
    content_path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
    shutil.copy(content_path, draft_dir / "draft_info.json")
    write_meta(draft_dir, int(data["duration"]), meta_rows)
    rewrite_paths(draft_dir)

    cover_src = ART / "蜜小π_分享版_v3.mp4"
    if not cover_src.exists():
        cover_src = ART / "蜜小π_首发_v3.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", "8", "-i", str(cover_src), "-frames:v", "1", str(draft_dir / "draft_cover.jpg")],
        check=True,
    )
    if (ART / "蜜小π_分享版_v3.mp4").exists():
        shutil.copy2(ART / "蜜小π_分享版_v3.mp4", pack / "成片参考_720p.mp4")
    write_import_helpers(pack)

    # 检查占位符都能对上包内文件
    packed = json.loads((draft_dir / "draft_content.json").read_text(encoding="utf-8"))
    missing = []
    for video in packed["materials"]["videos"] + packed["materials"]["audios"]:
        raw = video.get("path") or ""
        if PLACEHOLDER not in raw:
            missing.append(raw)
            continue
        rel = raw.split(PLACEHOLDER + "/", 1)[-1]
        if not (draft_dir / rel).exists():
            missing.append(rel)
    if missing:
        raise SystemExit("素材路径对不上：\n" + "\n".join(missing[:12]))
    print(f"草稿时长 {packed['duration'] / 1e6:.2f}s，轨道 {len(packed['tracks'])} 条")

    tmp_zip = Path("/tmp") / "mixiaopi_jianying_draft.zip"
    if tmp_zip.exists():
        tmp_zip.unlink()
    with zipfile.ZipFile(tmp_zip, "w") as zf:
        for path in pack.rglob("*"):
            if path.is_file():
                arc = str(Path("蜜小π_剪映草稿") / path.relative_to(pack))
                mode = zipfile.ZIP_STORED if path.suffix.lower() in {".mp4", ".m4a", ".jpg"} else zipfile.ZIP_DEFLATED
                zf.write(path, arc, compress_type=mode)
    shutil.copyfile(tmp_zip, out_zip)
    print("ZIP", out_zip, out_zip.stat().st_size)
    shutil.rmtree(pack)


if __name__ == "__main__":
    dest = Path(os.environ.get("JIANYING_ZIP", "/opt/cursor/artifacts/蜜小π_剪映草稿.zip"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    build(dest)
