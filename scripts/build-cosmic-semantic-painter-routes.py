#!/usr/bin/env python3
"""Generate reusable Semantic Painter Flow routes for the orbital-arc family.

Unlike the coverage-first skeleton/seal generator, this module describes how a
human painter would construct the scene: horizon arcs, overlapping surface
sweeps, radial sunrise strokes, then a small number of detail passes.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public" / "cosmic-dark-pilot"
DATA = ROOT / "data" / "cosmic-dark-pilot"
SOURCE = PUBLIC / "luminous.png"
OUT = PUBLIC / "semantic-painter-routes.json"
MASK_OUT = DATA / "semantic-painter-mask.png"
PREVIEW_OUT = DATA / "semantic-painter-preview.png"
REPORT_OUT = DATA / "semantic-painter-report.json"
W, H = 1920, 1080


@dataclass(frozen=True)
class FlowStroke:
    id: str
    group: str
    curve: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]
    width: float
    start: float
    end: float
    opacity: float = 1.0
    bristle: float = 0.16


def cubic(curve, samples: int = 48) -> list[list[float]]:
    p0, p1, p2, p3 = [np.array(p, dtype=np.float64) for p in curve]
    out: list[list[float]] = []
    for i in range(samples):
        t = i / (samples - 1)
        mt = 1.0 - t
        p = mt**3 * p0 + 3 * mt**2 * t * p1 + 3 * mt * t**2 * p2 + t**3 * p3
        # Natural pressure: soft entry, confident middle, lifted exit.
        pressure = 0.34 + 0.66 * math.sin(math.pi * t) ** 0.72
        if i == 0 or i == samples - 1:
            pressure *= 0.58
        out.append([round(float(p[0]), 1), round(float(p[1]), 1), round(pressure, 4)])
    return out


def orbital_arc_family() -> list[FlowStroke]:
    strokes: list[FlowStroke] = []

    # 1) Establish the atmosphere with two continuous, confident arcs.
    strokes += [
        FlowStroke("atmosphere-01", "atmosphere", ((120, 1070), (620, 760), (1230, 520), (1920, 390)), 78, 10, 29, 1.0, 0.11),
        FlowStroke("atmosphere-02", "atmosphere", ((170, 1080), (700, 790), (1270, 548), (1920, 425)), 48, 32, 45, 0.9, 0.09),
    ]

    # 2) Paint the planet as overlapping curvature-following bands.  Every
    # stroke finishes the same visual object before the brush moves elsewhere.
    surface_curves = [
        ((170, 1080), (660, 805), (1260, 565), (1930, 455), 224),
        ((270, 1110), (760, 875), (1320, 650), (1940, 545), 260),
        ((410, 1130), (850, 930), (1380, 735), (1950, 635), 286),
        ((610, 1140), (980, 975), (1450, 820), (1960, 730), 300),
        ((820, 1150), (1120, 1020), (1530, 905), (1970, 830), 288),
        ((1050, 1160), (1280, 1060), (1630, 995), (1980, 930), 254),
    ]
    t = 48.0
    durations = [15, 15, 15, 14, 13, 12]
    for i, (p0, p1, p2, p3, width) in enumerate(surface_curves):
        strokes.append(FlowStroke(f"surface-{i+1:02d}", "earth-surface", (p0, p1, p2, p3), width, t, t + durations[i], 1.0, 0.19))
        t += durations[i] + 3.0

    # 3) Sunrise rays radiate from one focal point instead of crossing at
    # arbitrary angles.  These are shorter and lighter than the planet bands.
    rays = [
        ((1610, 430), (1535, 350), (1450, 285), (1350, 220), 62),
        ((1630, 420), (1605, 315), (1585, 225), (1570, 135), 52),
        ((1645, 430), (1700, 345), (1760, 285), (1840, 225), 58),
        ((1595, 440), (1480, 420), (1365, 405), (1230, 390), 46),
    ]
    t = 151.0
    for i, (p0, p1, p2, p3, width) in enumerate(rays):
        strokes.append(FlowStroke(f"sunray-{i+1:02d}", "sunrise-rays", (p0, p1, p2, p3), width, t, t + 7, 0.58, 0.12))
        t += 9.0

    # 4) A few restrained detail sweeps restore cloud texture and violet land
    # color without reverting to hundreds of random seal stamps.
    details = [
        ((540, 970), (850, 820), (1160, 690), (1450, 610), 72),
        ((760, 1030), (1050, 900), (1350, 790), (1670, 720), 64),
        ((1020, 1040), (1260, 955), (1510, 885), (1810, 835), 58),
        ((1180, 585), (1310, 535), (1455, 500), (1600, 478), 52),
    ]
    t = 188.0
    for i, (p0, p1, p2, p3, width) in enumerate(details):
        strokes.append(FlowStroke(f"detail-{i+1:02d}", "cloud-details", (p0, p1, p2, p3), width, t, t + 7, 0.78, 0.22))
        t += 10.0
    return strokes


def stamp_mask(strokes: list[dict]) -> Image.Image:
    mask = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(mask)
    for stroke in strokes:
        points = stroke["points"]
        width = float(stroke["width"])
        for i, (x, y, pressure) in enumerate(points):
            if i % 2:
                continue
            radius = width * pressure * 0.53
            draw.ellipse((x - radius, y - radius * 0.72, x + radius, y + radius * 0.72), fill=255)
    return mask


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    DATA.mkdir(parents=True, exist_ok=True)
    authored = orbital_arc_family()
    strokes = [{
        "id": s.id,
        "group": s.group,
        "width": s.width,
        "start": s.start,
        "end": s.end,
        "opacity": s.opacity,
        "bristle": s.bristle,
        "points": cubic(s.curve),
    } for s in authored]
    data = {
        "meta": {
            "family": "orbital-arc",
            "image": "cosmic-dark-pilot/luminous.png",
            "width": W,
            "height": H,
            "fps": 30,
            "durationInFrames": 300,
            "drawStart": min(s.start for s in authored),
            "drawEnd": max(s.end for s in authored),
            "brushInvisibleAfter": 226,
            "focalPoint": [1620, 430],
            "strokeCount": len(strokes),
            "deterministic": True,
        },
        "groups": ["atmosphere", "earth-surface", "sunrise-rays", "cloud-details"],
        "strokes": strokes,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    mask = stamp_mask(strokes)
    mask.save(MASK_OUT)
    source = Image.open(SOURCE).convert("RGBA")
    alpha = np.asarray(source.getchannel("A"), dtype=np.uint8) > 10
    painted = np.asarray(mask, dtype=np.uint8) > 8
    coverage = float((alpha & painted).sum() / max(1, alpha.sum()))

    preview = Image.new("RGB", (W, H), (1, 2, 13))
    preview.alpha_composite(source) if preview.mode == "RGBA" else None
    comp = Image.new("RGBA", (W, H), (1, 2, 13, 255))
    comp.alpha_composite(source)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    colors = {"atmosphere": (92, 226, 255, 165), "earth-surface": (99, 126, 255, 120),
              "sunrise-rays": (255, 194, 84, 175), "cloud-details": (193, 116, 255, 150)}
    for stroke in strokes:
        pts = [(p[0], p[1]) for p in stroke["points"]]
        od.line(pts, fill=colors[stroke["group"]], width=max(2, int(stroke["width"] * 0.12)), joint="curve")
    comp.alpha_composite(overlay)
    comp.convert("RGB").save(PREVIEW_OUT)

    report = {
        "family": "orbital-arc",
        "strokeCount": len(strokes),
        "groups": {g: sum(s["group"] == g for s in strokes) for g in data["groups"]},
        "softAlphaCoverage": round(coverage, 4),
        "drawEnd": data["meta"]["drawEnd"],
        "files": {"routes": str(OUT.relative_to(ROOT)), "mask": str(MASK_OUT.relative_to(ROOT)),
                  "preview": str(PREVIEW_OUT.relative_to(ROOT))},
    }
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
