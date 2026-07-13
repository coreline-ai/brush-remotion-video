#!/usr/bin/env python3
"""Normalize outer connected storybook paper while preserving enclosed cream regions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageOps
from scipy import ndimage


CANVAS = {"youtube": (1920, 1080), "shorts": (1080, 1920)}


def normalize_image(
    path: Path,
    *,
    size: tuple[int, int],
    paper: tuple[int, int, int],
    sat_max: int,
    lum_min: float,
) -> dict:
    source = Image.open(path).convert("RGB")
    fitted = ImageOps.contain(source, size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, paper)
    canvas.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    arr = np.asarray(canvas).copy()

    sat = arr.max(axis=2).astype(np.int16) - arr.min(axis=2).astype(np.int16)
    lum = arr.mean(axis=2)
    candidate = (sat < sat_max) & (lum > lum_min)
    labels, _ = ndimage.label(candidate)
    border_ids = np.unique(
        np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    )
    border_ids = border_ids[border_ids > 0]
    mask = np.isin(labels, border_ids)
    paper_fraction = float(mask.mean())
    if paper_fraction < 0.20:
        raise SystemExit(f"paper region too small: {path} ({paper_fraction:.4f})")

    arr[mask] = np.asarray(paper, dtype=np.uint8)
    Image.fromarray(arr, "RGB").save(path)
    return {
        "image": str(path),
        "sourceSize": list(source.size),
        "finalSize": list(size),
        "paperRgb": list(paper),
        "paperFraction": round(paper_fraction, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("--paper", default="250,249,247")
    parser.add_argument("--sat-max", type=int, default=35)
    parser.add_argument("--lum-min", type=float, default=205)
    args = parser.parse_args()

    project = args.project_dir.resolve()
    config = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
    fmt = config.get("format", "youtube")
    if fmt not in CANVAS:
        raise SystemExit(f"unsupported format: {fmt}")
    paper = tuple(int(v) for v in args.paper.split(","))
    if len(paper) != 3 or any(v < 0 or v > 255 for v in paper):
        raise SystemExit("--paper must be R,G,B")

    images = config.get("background", {}).get("images") or []
    if not images:
        raise SystemExit("project.yaml background.images is empty")
    report = [
        normalize_image(
            project / rel,
            size=CANVAS[fmt],
            paper=paper,
            sat_max=args.sat_max,
            lum_min=args.lum_min,
        )
        for rel in images
    ]
    out = project / "paper-normalization-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"images": len(report), "report": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

