#!/usr/bin/env python3
"""Move 蜜小π around the frame: fly, walk, and point, instead of a fixed corner sticker.

Real plates, narration, and the ≤30s illustration budget stay as in v3.
The character is a transparent overlay on top of those plates.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import build_v3 as b

ROOT = b.ROOT
POSES = ROOT / "char" / "poses"
PNG = b.PNG
WORK = b.WORK
OUT = WORK / "segs_pose"
ART = b.ART

# (x, y) of the overlay's top-left. y grows downward.
# Low spots sit above the subtitle band. Top-left of frame is reserved for place labels.
SPOTS = {
    "low_left": ("(24)", "(H-h-220)"),
    "low_right": ("(W-w-24)", "(H-h-220)"),
    "mid_left": ("(16)", "((H-h)*0.34+150)"),
    "mid_right": ("(W-w-16)", "((H-h)*0.32+150)"),
    "upper_left": ("(30)", "(176)"),
    "top_right": ("(W-w-28)", "(14)"),
    "top_mid": ("((W-w)*0.58)", "(12)"),
    "sky_left": ("(8)", "(4)"),
    "sky_right": ("(W-w-8)", "(4)"),
    "off_left": ("(-w-30)", "((H-h)*0.42+120)"),
    "off_right": ("(W+20)", "(H-h-220)"),
    "off_top": ("((W-w)*0.72)", "(-h-16)"),
    "off_sky_left": ("(-w-16)", "(4)"),
    "mail_right_low": ("(1340)", "(H-h-180)"),
    "mail_right_mid": ("(1380)", "(430)"),
    "mail_right_high": ("(1320)", "(188)"),
    "lead_left": ("(-w-20)", "(H-h-240)"),
    "lead_right": ("(W-w-16)", "(H-h-240)"),
}

# upper_left sits on faces in classroom close-ups, so it is not a place the character settles.
OPEN = ["top_right", "low_left", "mid_right", "low_right", "mid_left", "top_mid"]
RIGHT = ["low_right", "top_right", "mid_right"]
SKY = ["sky_left", "sky_right"]
MAIL = ["mail_right_low", "mail_right_high", "mail_right_mid"]
LEAD = ["lead_right"]
STARS = ["low_right", "top_right", "mid_right", "top_mid"]
LEFT_VERT = ["upper_left", "low_left", "mid_left"]
RIGHT_VERT = ["top_right", "low_right", "mid_right"]

SIGN_SRC = {"gate1.mp4"}
WIDE_SRC = {"overview_01.mp4", "school_gate.jpg"}
DIAGRAM = {"map", "trees", "triptych", "piroll"}


def side_of(name: str) -> str:
    if "left" in name:
        return "L"
    if "right" in name:
        return "R"
    return "C"


def band_of(name: str) -> str:
    if any(k in name for k in ("sky", "top", "high", "upper")):
        return "T"
    if "mid" in name or name.startswith("off"):
        return "M"
    return "B"


def zone_of(shot: dict) -> str:
    if shot.get("zone"):
        return shot["zone"]
    if shot.get("endcard"):
        return "card"
    name = shot.get("name") or ""
    src = shot.get("src") or ""
    label = shot.get("label") or ""
    if src in SIGN_SRC:
        return "sign"
    if src in WIDE_SRC:
        return "wide"
    if name == "mailbox" or "信箱" in label:
        return "mail"
    if name == "stars" or label.startswith("银河"):
        return "stars"
    if "跟我看看" in label:
        return "lead"
    if name in DIAGRAM:
        return "diagram"
    return "open"


def pool_for(zone: str, current: str) -> list[str]:
    if zone == "sign":
        return SKY
    if zone in ("wide", "card", "prelude"):
        return RIGHT
    if zone == "mail":
        return MAIL
    if zone == "lead":
        return LEAD
    if zone == "stars":
        return STARS
    if zone == "diagram":
        return LEFT_VERT if side_of(current) == "L" else RIGHT_VERT
    return OPEN


def snap_start(zone: str, current: str) -> str:
    """Jump only when a straight line from the previous spot would cover something we must keep clear."""
    if zone == "sign" and "sky" not in current:
        return "off_sky_left"
    if zone == "wide" and side_of(current) != "R":
        return "off_right"
    if zone == "prelude":
        return "off_right"
    if zone == "card" and side_of(current) != "R":
        return "mid_right"
    if zone == "mail" and not current.startswith("mail_right"):
        return "mail_right_low"
    if zone == "lead":
        return "lead_left"
    if zone == "stars" and side_of(current) != "R":
        return "low_right"
    return current


def score(current: str, cand: str) -> int:
    s = 0
    if side_of(cand) != side_of(current):
        s += 10
    if band_of(cand) != band_of(current):
        s += 6
    if "off" in cand:
        s -= 8
    return s


def pick(pool: list[str], current: str, idx: int) -> tuple[str, int]:
    best = None
    for j in range(len(pool)):
        k = (idx + 1 + j) % len(pool)
        cand = pool[k]
        if cand == current:
            continue
        item = (score(current, cand), -j, cand, k)
        if best is None or item > best:
            best = item
    assert best is not None
    return best[2], best[3]


def h_for(zone: str) -> int:
    return {
        "sign": 156,
        "wide": 280,
        "prelude": 300,
        "card": 250,
        "mail": 300,
        "lead": 320,
        "stars": 290,
        "diagram": 280,
        "open": 310,
    }[zone]


def pose_for(a: str, b: str, shot: dict, leg: int, zone: str) -> str:
    label = shot.get("label") or ""
    if zone in ("card", "prelude") and leg == 0:
        return "wave"
    if zone == "card":
        return "wave" if leg % 2 == 0 else "cheer"
    if "1100" in label or "马年" in label:
        return "cheer" if leg % 2 == 0 else "fly"
    if zone == "mail":
        return "point_left" if leg % 2 else "fly"
    if zone == "lead":
        return "walk"
    if zone == "sign":
        return "fly"
    name = shot.get("name") or shot.get("src") or ""
    crossing = side_of(a) != side_of(b) or "off" in a
    if name in ("moss.mp4", "plant.mp4", "soil.mp4") or any(k in label for k in ("观察", "苔藓", "泥土")):
        return "look" if not crossing else "fly"
    if not crossing:
        # Parked on an edge: point back into the picture.
        if side_of(a) == "R" or side_of(b) == "R":
            return ["point_left", "look", "peek"][leg % 3]
        return ["point_right", "peek", "cheer"][leg % 3]
    toward = "point_left" if side_of(b) == "L" else "point_right"
    return ["fly", "fly", toward, "walk", "look"][leg % 5]


def arc_for(a: str, b: str, zone: str) -> float:
    if zone == "sign" or ("sky" in a and "sky" in b):
        return 0.0
    if zone == "lead":
        return -46.0
    if band_of(a) == "T" and band_of(b) == "T":
        return 28.0
    if side_of(a) != side_of(b):
        if band_of(a) == "B" and band_of(b) == "B":
            return -230.0
        return -150.0
    return -26.0


def legs_for(zone: str, dur: float) -> int:
    if zone == "lead":
        return 1
    if dur < 1.45:
        return 1
    if dur < 3.6:
        return 2
    if dur < 6.5:
        return 3
    return 4


def build_cues(shots: list[dict], seg_index: int) -> list[dict]:
    if not shots:
        return []
    z0 = zone_of(shots[0])
    spot = "off_left" if seg_index % 2 == 0 else "off_right"
    if z0 in ("prelude", "wide", "card"):
        spot = "off_right"
    idx = seg_index
    cues = []
    leg_i = 0
    for si, shot in enumerate(shots):
        zone = zone_of(shot)
        t0 = float(shot["t0"])
        t1 = float(shot["t0"] + shot["dur"])
        if t1 - t0 < 0.25:
            continue
        spot = snap_start(zone, spot)
        pool = pool_for(zone, spot)
        n = legs_for(zone, t1 - t0)
        h = h_for(zone)
        for k in range(n):
            a = t0 + (t1 - t0) * k / n
            c = t0 + (t1 - t0) * (k + 1) / n
            nxt, idx = pick(pool, spot, idx)
            pose = pose_for(spot, nxt, shot, leg_i, zone)
            cues.append({
                "a": a,
                "c": c,
                "frm": spot,
                "to": nxt,
                "pose": pose,
                "h": h,
                "arc": arc_for(spot, nxt, zone),
                "label": shot.get("label") or "",
                "zone": zone,
            })
            spot = nxt
            leg_i += 1
        # Keep the segment's last spot; next shot continues from here unless snap_start says otherwise.
        _ = si
    return cues


def move_expr(t0: float, t1: float, e0: str, e1: str, arc: float, pose: str, axis: str) -> str:
    span = max(t1 - t0, 0.08)
    p = f"clip((t-{t0:.3f})/{span:.3f},0,1)"
    s = f"({p})*({p})*(3-2*({p}))"
    base = f"(({e0})+(({e1})-({e0}))*({s}))"
    if axis == "y" and arc:
        base = f"({base})+({arc:.1f})*sin(PI*({p}))"
    if axis == "x":
        base = f"({base})+16*sin(t*1.65)"
        if pose == "fly":
            base = f"({base})+12*sin(t*2.6)"
        return f"min(max({base},-w-40),W+16)"
    base = f"({base})+13*sin(t*2.15)"
    if pose == "fly":
        base = f"({base})+22*sin(t*3.05)"
    if pose == "walk":
        base = f"({base})-34*abs(sin((t-{t0:.3f})*8))"
    return f"min(max({base},-16),H-h-150)"


def cut_poses():
    for jpg in sorted(POSES.glob("*.jpg")):
        name = jpg.stem.replace("mixiaopi_", "")
        dst = PNG / f"pose_{name}.png"
        if not dst.exists():
            b.cutout(jpg, dst)


def load_timeline():
    recs, gap = b.prepare_voice()
    timeline = {
        "prelude": [{
            "t0": 0.0, "dur": b.HEAD, "src": "overview_01.mp4", "kind": "video",
            "label": "", "zone": "prelude",
        }]
    }
    for rec, spec in zip(recs, b.SEGMENTS):
        after = b.TAIL if rec["i"] == 10 else gap
        seg_dur = b.snap(rec["spoken"] + after + spec.get("extra", 0))
        times = b.window_times(rec["words"], spec["windows"], seg_dur)
        timeline[f"{rec['i']:02d}"] = b.expand(spec["windows"], times, seg_dur)
    return timeline


def render_one(key: str, shots: list[dict], seg_index: int):
    if key == "prelude":
        bg = WORK / "shots" / "prelude.mp4"
        ass = None
    else:
        bg = WORK / "shots" / f"s{key}" / "bg.mp4"
        ass = WORK / "ass" / f"seg{key}.ass"
    dur = b.probe(bg)
    cues = []
    for cue in build_cues(shots, seg_index):
        a = max(0.0, cue["a"])
        c = min(dur, cue["c"])
        if c - a < 0.18:
            continue
        cue = dict(cue)
        cue["a"], cue["c"] = a, c
        cues.append(cue)
    if not cues:
        raise SystemExit(f"no cues for {key}")
    print(f"\n# {key} {dur:.2f}s  {len(cues)} moves")
    for cue in cues:
        print(f"  {cue['a']:6.2f}-{cue['c']:6.2f} {cue['pose']:12} {cue['frm']:16} -> {cue['to']:16} {cue['label']}")

    inputs = ["-i", str(bg)]
    inputs += ["-framerate", "30", "-loop", "1", "-i", str(PNG / "lower.png")]
    chains = [
        f"[0:v]fps=30,trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p[v0]",
        "[1:v]format=rgba,scale=1920:260[lt]",
        "[v0][lt]overlay=0:H-h:format=auto[v1]",
    ]
    cur = "v1"
    n = 2
    if ass and ass.exists():
        chains.append(f"[{cur}]subtitles={ass}:fontsdir={b.FONTS}[vsub]")
        cur = "vsub"
    if key == "prelude":
        inputs += ["-framerate", "30", "-loop", "1", "-i", str(PNG / "card_open.png")]
        chains.append(f"[{n}:v]format=rgba,fade=t=in:st=0.2:d=0.35:alpha=1[card]")
        chains.append(f"[{cur}][card]overlay=x=(W-w)/2:y=70:format=auto:shortest=1[vcard]")
        cur = "vcard"
        n += 1

    for i, cue in enumerate(cues):
        inputs += ["-framerate", "30", "-loop", "1", "-i", str(PNG / f"pose_{cue['pose']}.png")]
        x0, y0 = SPOTS[cue["frm"]]
        x1, y1 = SPOTS[cue["to"]]
        x = move_expr(cue["a"], cue["c"], x0, x1, cue["arc"], cue["pose"], "x")
        y = move_expr(cue["a"], cue["c"], y0, y1, cue["arc"], cue["pose"], "y")
        fade_in = 0.16 if i == 0 else 0.08
        parts = [
            f"[{n}:v]scale=-1:{cue['h']}:flags=lanczos,format=rgba",
            f"fade=t=in:st={cue['a']:.3f}:d={fade_in}:alpha=1",
        ]
        # Last move stays through the end of the segment.
        if i < len(cues) - 1:
            parts.append(f"fade=t=out:st={max(cue['a'], cue['c'] - 0.08):.3f}:d=0.08:alpha=1")
        chains.append(",".join(parts) + f"[p{i}]")
        chains.append(
            f"[{cur}][p{i}]overlay=x='{x}':y='{y}':enable='between(t,{cue['a']:.3f},{cue['c'] + 0.02:.3f})':format=auto:shortest=1[c{i}]"
        )
        cur = f"c{i}"
        n += 1

    end = next((s for s in shots if s.get("endcard")), None)
    if end:
        inputs += ["-framerate", "30", "-loop", "1", "-i", str(PNG / "card_end.png")]
        t0 = float(end["t0"])
        chains.append(f"[{n}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.35:alpha=1[endc]")
        chains.append(f"[{cur}][endc]overlay=x=(W-w)/2-60:y=80:format=auto:shortest=1[vend]")
        cur = "vend"
        chains.append(f"[{cur}]fade=t=out:st={max(0, dur - 0.55):.2f}:d=0.55,format=yuv420p[vout]")
    else:
        chains.append(f"[{cur}]format=yuv420p[vout]")

    out = OUT / ("prelude.mp4" if key == "prelude" else f"seg{key}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    b.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains),
         "-map", "[vout]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
         "-video_track_timescale", "30000", "-an", str(out)],
        out.name,
    )
    return out


def mux(files):
    lst = WORK / "concat_pose.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in files), encoding="utf-8")
    silent = WORK / "silent_pose.mp4"
    b.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], "concat")
    vdur = b.probe(silent)
    master = ART / "蜜小π_首发_v3.mp4"
    fc = (
        "[1:a]highpass=f=80,alimiter=limit=0.95,asplit=2[vo][vsc];"
        f"[2:a]volume=0.18,highpass=f=90,afade=t=in:st=0:d=2.0,afade=t=out:st={max(0, vdur - 3):.2f}:d=2.8[bm];"
        "[bm][vsc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=300[bd];"
        "[vo][bd]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]"
    )
    b.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(WORK / "voice.wav"), "-i", str(WORK / "bgm.wav"),
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-metadata", "title=蜜小π首发 v3", str(master)],
        "mux",
    )
    print("MASTER", b.probe(master), master.stat().st_size)
    share = ART / "蜜小π_分享版_v3.mp4"
    b.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(master), "-vf", "scale=1280:720:flags=lanczos",
         "-c:v", "libx264", "-preset", "veryfast", "-b:v", "1400k", "-maxrate", "1800k", "-bufsize", "3600k",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(share)],
        "share",
    )
    print("SHARE", share.stat().st_size)


def seg_index(key: str) -> int:
    return 0 if key == "prelude" else int(key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma keys: prelude,00,01,...")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--no-mux", action="store_true")
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args()
    timeline = load_timeline()
    keys = ["prelude", "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]
    if args.only:
        want = {k.strip() for k in args.only.split(",") if k.strip()}
        keys = [k for k in keys if k in want]
    if args.plan:
        for key in keys:
            print(f"\n# {key}")
            for cue in build_cues(timeline[key], seg_index(key)):
                print(f"  {cue['a']:6.2f}-{cue['c']:6.2f} {cue['pose']:12} {cue['frm']:16} -> {cue['to']:16} h={cue['h']} {cue['label']}")
        return
    cut_poses()
    if args.jobs > 1 and len(keys) > 1:
        files = {}
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(render_one, key, timeline[key], seg_index(key)): key for key in keys}
            for fut in as_completed(futs):
                files[futs[fut]] = fut.result()
        ordered = [files[k] for k in keys]
    else:
        ordered = []
        for key in keys:
            ordered.append(render_one(key, timeline[key], seg_index(key)))
    if args.no_mux:
        return
    if args.only:
        # Mux needs every segment. Fill gaps from the last full pose render.
        full = []
        for key in ["prelude", "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]:
            name = "prelude.mp4" if key == "prelude" else f"seg{key}.mp4"
            full.append(OUT / name)
        if not all(p.exists() for p in full):
            print("skip mux, missing segments")
            return
        mux(full)
    else:
        mux(ordered)


if __name__ == "__main__":
    main()
