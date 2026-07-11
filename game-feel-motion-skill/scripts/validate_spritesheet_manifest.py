#!/usr/bin/env python3
"""Validate a game-feel spritesheet/VFX manifest.

Checks layout math, required fields, pivot/baseline bounds, and optional image
dimensions when Pillow is installed and --image is provided.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def require_number(value, name: str, *, integer: bool = False, minimum: float | None = None):
    if integer and not isinstance(value, int):
        fail(f"{name} must be an integer")
    if not integer and not isinstance(value, (int, float)):
        fail(f"{name} must be a number")
    if minimum is not None and value < minimum:
        fail(f"{name} must be >= {minimum}")
    return value


def load_image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        warn("Pillow is not installed; skipping image dimension check")
        return None

    with Image.open(path) as img:
        return img.size


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--image", type=Path, help="Optional spritesheet image to check dimensions")
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))

    for field in ["id", "type", "motion", "frames", "fps", "layout", "pivot", "loop"]:
        if field not in data:
            fail(f"missing required field: {field}")

    frames = require_number(data["frames"], "frames", integer=True, minimum=1)
    fps = require_number(data["fps"], "fps", minimum=0.001)

    layout = data["layout"]
    for field in ["columns", "rows", "frameWidth", "frameHeight", "margin", "gap", "paddingInsideFrame"]:
        if field not in layout:
            fail(f"missing layout field: {field}")

    columns = require_number(layout["columns"], "layout.columns", integer=True, minimum=1)
    rows = require_number(layout["rows"], "layout.rows", integer=True, minimum=1)
    frame_width = require_number(layout["frameWidth"], "layout.frameWidth", integer=True, minimum=1)
    frame_height = require_number(layout["frameHeight"], "layout.frameHeight", integer=True, minimum=1)
    margin = require_number(layout["margin"], "layout.margin", integer=True, minimum=0)
    gap = require_number(layout["gap"], "layout.gap", integer=True, minimum=0)
    padding = require_number(layout["paddingInsideFrame"], "layout.paddingInsideFrame", integer=True, minimum=0)

    if frames > columns * rows:
        fail(f"frames ({frames}) exceeds grid capacity ({columns * rows})")

    if padding * 2 >= frame_width or padding * 2 >= frame_height:
        fail("paddingInsideFrame is too large for the frame size")

    expected_width = margin * 2 + columns * frame_width + (columns - 1) * gap
    expected_height = margin * 2 + rows * frame_height + (rows - 1) * gap

    pivot = data["pivot"]
    if not isinstance(pivot, list) or len(pivot) != 2:
        fail("pivot must be [x, y]")
    px = require_number(pivot[0], "pivot[0]")
    py = require_number(pivot[1], "pivot[1]")
    if not (0 <= px <= frame_width and 0 <= py <= frame_height):
        fail("pivot must be inside one frame cell")

    if "baselineY" in data:
        baseline_y = require_number(data["baselineY"], "baselineY")
        if not (0 <= baseline_y <= frame_height):
            fail("baselineY must be inside one frame cell")

    if args.image:
        actual_size = load_image_size(args.image)
        if actual_size is not None and actual_size != (expected_width, expected_height):
            fail(
                f"image size {actual_size[0]}x{actual_size[1]} does not match "
                f"expected {expected_width}x{expected_height}"
            )

    duration_ms = frames / fps * 1000
    ok(f"manifest: {data['id']}")
    ok(f"grid capacity: {columns * rows}, frames: {frames}")
    ok(f"expected sheet size: {expected_width}x{expected_height}")
    ok(f"duration: {duration_ms:.1f}ms at {fps}fps")
    ok("spritesheet manifest passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
