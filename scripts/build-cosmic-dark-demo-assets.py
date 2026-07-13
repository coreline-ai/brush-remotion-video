#!/usr/bin/env python3
"""Build the isolated dark-brush orbital-sunrise pilot assets.

The source is a flattened dark illustration.  We estimate the matte cosmic
canvas from the quiet upper-left region, derive a luminous RGBA foreground,
and create a black-on-white analysis matte for the existing route generator.
The render image and route-analysis image intentionally remain separate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from brushvid.routes import RouteParams, generate_routes, render_preview, write_routes  # noqa: E402

PUBLIC = ROOT / "public" / "cosmic-dark-pilot"
DATA = ROOT / "data" / "cosmic-dark-pilot"
SOURCE = PUBLIC / "source.png"
LUMINOUS = PUBLIC / "luminous.png"
ROUTE_MASK = PUBLIC / "route-mask.png"
ROUTES = PUBLIC / "routes.json"
PREVIEW = DATA / "route-preview.png"
REPORT = DATA / "asset-report.json"
W, H = 1920, 1080


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / max(1e-6, edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    image = Image.open(SOURCE).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    rgb = np.asarray(image, dtype=np.float32)

    # Quiet upper-left third is deliberately reserved as dark negative space.
    sample = rgb[: H // 3, : W // 3].reshape(-1, 3)
    base = np.median(sample, axis=0)
    base = np.maximum(base, np.array([1.0, 2.0, 11.0], dtype=np.float32))

    luma = rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    signal = luma + chroma * 0.22
    alpha = smoothstep(5.0, 36.0, signal)
    alpha[alpha < 0.012] = 0.0

    # Un-premultiply against the estimated matte so compositing on the same
    # dark canvas reconstructs the source instead of dimming it twice.
    a3 = alpha[..., None]
    foreground = np.where(
        a3 > 0.01,
        (rgb - base[None, None, :] * (1.0 - a3)) / np.maximum(a3, 0.01),
        0.0,
    )
    foreground = np.clip(foreground, 0, 255).astype(np.uint8)
    rgba = np.dstack([foreground, np.rint(alpha * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(LUMINOUS)

    # The legacy route detector expects dark content on bright paper.  This
    # matte carries only intended reveal coverage, not the foreground colors.
    # Include the soft low-alpha cosmic paint, otherwise the final mask leaves
    # dark stripe gaps between the broad routes even though the bright core is
    # numerically covered.
    route_strength = smoothstep(0.008, 0.09, alpha)
    mask_gray = np.rint(255.0 * (1.0 - route_strength)).astype(np.uint8)
    Image.fromarray(mask_gray, "L").convert("RGB").save(ROUTE_MASK)

    params = RouteParams(
        width=W,
        height=H,
        duration=300,
        draw_start=10,
        draw_end=190,
        pen_invisible_after=202,
        seed=203,
        analyze_scale=2.5,
        contour_width=62,
        seal_width=78,
        seal_step=46,
        lum_thresh=12,
        sat_thresh=250,
        rdp_eps=2.2,
        max_len=620,
        min_route_len=30,
        close=2,
        group_by_zone=True,
        zone_merge_px=18,
    )
    data = generate_routes(
        ROUTE_MASK,
        params,
        image_rel="cosmic-dark-pilot/luminous.png",
    )
    write_routes(data, ROUTES)
    render_preview(ROUTE_MASK, data, PREVIEW)

    report = {
        "projectId": "cosmic-dark-pilot",
        "canvas": {"width": W, "height": H, "rgb": [round(float(x), 1) for x in base]},
        "alpha": {
            "nonzeroFraction": round(float((alpha > 0.01).mean()), 4),
            "strongFraction": round(float((alpha > 0.5).mean()), 4),
            "mean": round(float(alpha.mean()), 4),
        },
        "routes": data["meta"],
        "files": {
            "source": str(SOURCE.relative_to(ROOT)),
            "luminous": str(LUMINOUS.relative_to(ROOT)),
            "routeMask": str(ROUTE_MASK.relative_to(ROOT)),
            "routes": str(ROUTES.relative_to(ROOT)),
            "preview": str(PREVIEW.relative_to(ROOT)),
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
