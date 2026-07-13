#!/usr/bin/env python3
"""QA and review artifacts for the Semantic Painter Flow v2 pilot."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "output" / "cosmic-dark-pilot" / "cosmic-semantic-painter-pilot.mp4"
ROUTES = ROOT / "public" / "cosmic-dark-pilot" / "semantic-painter-routes.json"
OUT = ROOT / "data" / "cosmic-dark-pilot" / "semantic-qa"
TIMES = [("opening", 0.5), ("atmosphere", 1.2), ("surface", 3.2),
         ("sunrise", 5.5), ("complete", 7.5), ("outro", 9.7)]


def probe() -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-show_entries", "format=duration,size,bit_rate", "-of", "json", str(VIDEO),
    ], text=True))


def extract_frames() -> list[Path]:
    frames = OUT / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    results = []
    for label, sec in TIMES:
        path = frames / f"{label}.jpg"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(sec),
                        "-i", str(VIDEO), "-frames:v", "1", "-q:v", "2", str(path)], check=True)
        results.append(path)
    return results


def contact_sheet(frames: list[Path]) -> Path:
    tw, th = 320, 180
    sheet = Image.new("RGB", (tw * len(frames), th + 40), (5, 8, 20))
    draw = ImageDraw.Draw(sheet)
    for i, ((label, sec), path) in enumerate(zip(TIMES, frames)):
        im = Image.open(path).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        sheet.paste(im, (i * tw, 0))
        draw.text((i * tw + 10, th + 12), f"{label} {sec:.1f}s", fill=(220, 241, 255))
    out = OUT / "contact-sheet.jpg"
    sheet.save(out, "JPEG", quality=92)
    return out


def decode_small() -> np.ndarray:
    w, h = 160, 90
    raw = subprocess.check_output(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(VIDEO), "-an",
                                   "-vf", f"scale={w}:{h},format=rgb24", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def path_length(points: list[list[float]]) -> float:
    return sum(math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1])
               for i in range(1, len(points)))


def main() -> int:
    if not VIDEO.is_file():
        raise FileNotFoundError(VIDEO)
    OUT.mkdir(parents=True, exist_ok=True)
    frames = extract_frames()
    sheet = contact_sheet(frames)
    media = probe()
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    strokes = routes["strokes"]
    decoded = decode_small()
    gray = decoded @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    step = np.zeros(len(gray), dtype=np.float32)
    step[1:] = np.abs(gray[1:] - gray[:-1]).mean(axis=(1, 2))
    base = decoded[0]
    content = np.abs(decoded - base).mean(axis=3) > 12
    frame_index = {label: min(len(decoded) - 1, round(sec * 30)) for label, sec in TIMES}
    fractions = {label: round(float(content[idx].mean()), 4) for label, idx in frame_index.items()}

    video_stream = next(s for s in media["streams"] if s["codec_type"] == "video")
    audio_stream = next(s for s in media["streams"] if s["codec_type"] == "audio")
    duration = float(media["format"]["duration"])
    groups = ["atmosphere", "earth-surface", "sunrise-rays", "cloud-details"]
    group_counts = {g: sum(s["group"] == g for s in strokes) for g in groups}
    lengths = [path_length(s["points"]) for s in strokes]
    sorted_strokes = sorted(strokes, key=lambda x: x["start"])
    visible_gaps = [sorted_strokes[i]["start"] - sorted_strokes[i - 1]["end"] for i in range(1, len(sorted_strokes))]
    checks = {
        "duration10s": abs(duration - 10.0) < 0.02,
        "videoSpec": (video_stream.get("width"), video_stream.get("height"), video_stream.get("r_frame_rate")) == (1920, 1080, "30/1"),
        "audioPresent": audio_stream.get("codec_name") == "aac" and audio_stream.get("sample_rate") == "48000",
        "semanticStrokeBudget": 10 <= len(strokes) <= 30,
        "allSemanticGroups": all(group_counts[g] > 0 for g in groups),
        "noTinyStampRoutes": min(lengths) >= 120,
        "brushLiftBetweenStrokes": min(visible_gaps) >= 2.0,
        "deterministic": routes["meta"].get("deterministic") is True,
        "surfaceProgress": fractions["surface"] > fractions["opening"] + 0.08,
        "completionProgress": fractions["complete"] > fractions["surface"] + 0.05,
        "holdStable": float(step[232:268].max()) < 1.8,
        "darkOutro": float(gray[295:].mean()) < float(gray[248:265].mean()) * 0.35,
    }
    report = {
        "projectId": "cosmic-dark-pilot-v2",
        "ok": all(checks.values()),
        "checks": checks,
        "media": media,
        "semantic": {
            "family": routes["meta"]["family"], "strokeCount": len(strokes),
            "groupCounts": group_counts, "minPathLength": round(min(lengths), 2),
            "maxPathLength": round(max(lengths), 2), "minBrushLiftFrames": round(min(visible_gaps), 2),
        },
        "contentFractions": fractions,
        "motion": {"maxStep": round(float(step.max()), 4), "holdMaxStep": round(float(step[232:268].max()), 4)},
        "contactSheet": str(sheet.relative_to(ROOT)),
    }
    (OUT / "qa-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
