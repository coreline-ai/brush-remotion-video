#!/usr/bin/env python3
"""Validate and normalize one built-in imagegen result without cropping."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SIZE = (1920, 1080)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--scene", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "examples/cosmic-fullscreen-v05/assets")
    args = parser.parse_args()
    source = args.source.resolve()
    image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    ratio = image.width / image.height
    target = SIZE[0] / SIZE[1]
    ratio_error = abs(ratio - target) / target
    if ratio_error > 0.012:
        raise SystemExit(f"scene-{args.scene:02d}: source ratio {ratio:.6f} is not 16:9; no crop allowed")
    output = args.out_dir.resolve() / f"scene-{args.scene:02d}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize(SIZE, Image.Resampling.LANCZOS).save(output, optimize=True)
    metadata = {
        "scene": args.scene,
        "title": args.title,
        "file": str(output.relative_to(ROOT)),
        "source": str(source),
        "sourceWidth": image.width,
        "sourceHeight": image.height,
        "ratioError": round(ratio_error, 8),
        "width": SIZE[0],
        "height": SIZE[1],
        "sha256": sha256(output),
        "cropApplied": False,
        "fullBleed": True,
    }
    output.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
