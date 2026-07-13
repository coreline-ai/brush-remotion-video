#!/usr/bin/env python3
"""Validate and manifest the 60 full-screen realistic-ink cosmic assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "examples/cosmic-fullscreen-v05/prompts.json"
ASSETS = ROOT / "examples/cosmic-fullscreen-v05/assets-ink-v1"
OUT = ASSETS / "manifest.json"
EXPECTED_SIZE = (1920, 1080)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def edge_stats(image: Image.Image) -> dict[str, float]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    edge = max(8, round(min(width, height) * 0.01))
    strips = {
        "top": rgb.crop((0, 0, width, edge)),
        "bottom": rgb.crop((0, height - edge, width, height)),
        "left": rgb.crop((0, 0, edge, height)),
        "right": rgb.crop((width - edge, 0, width, height)),
    }
    result: dict[str, float] = {}
    for name, strip in strips.items():
        stat = ImageStat.Stat(strip)
        result[f"{name}_mean"] = round(sum(stat.mean) / 3, 3)
        result[f"{name}_stddev"] = round(sum(stat.stddev) / 3, 3)
    return result


def main() -> int:
    prompt_data = json.loads(PROMPTS.read_text(encoding="utf-8"))
    scenes = prompt_data["scenes"]
    if [scene["scene"] for scene in scenes] != list(range(1, 61)):
        raise SystemExit("prompt manifest is not exactly scenes 01..60")

    records = []
    hashes: dict[str, int] = {}
    failures = []
    for scene in scenes:
        number = scene["scene"]
        path = ASSETS / f"scene-{number:02d}.png"
        source = ASSETS / "source" / f"scene-{number:02d}.png"
        if not path.exists():
            failures.append(f"scene {number:02d}: missing production PNG")
            continue
        if not source.exists():
            failures.append(f"scene {number:02d}: missing generated source PNG")
        with Image.open(path) as image:
            size = image.size
            mode = image.mode
            stats = edge_stats(image)
        if size != EXPECTED_SIZE:
            failures.append(f"scene {number:02d}: {size}, expected {EXPECTED_SIZE}")
        digest = sha256(path)
        if digest in hashes:
            failures.append(
                f"scene {number:02d}: exact duplicate of scene {hashes[digest]:02d}"
            )
        hashes[digest] = number
        records.append(
            {
                "scene": number,
                "title": scene["title"],
                "required": scene["required"],
                "forbidden": scene["forbidden"],
                "asset": str(path.relative_to(ROOT)),
                "source": str(source.relative_to(ROOT)),
                "width": size[0],
                "height": size[1],
                "mode": mode,
                "sha256": digest,
                "edge_stats": stats,
                "prompt": scene["prompt"],
            }
        )

    payload = {
        "version": "v0.5-fullscreen-realistic-ink-v1",
        "style": "realistic-form Korean ink-and-mineral-pigment painting on dark dyed hanji",
        "expected_scene_count": 60,
        "actual_scene_count": len(records),
        "expected_size": list(EXPECTED_SIZE),
        "exact_duplicate_count": len(records) - len(hashes),
        "failures": failures,
        "scenes": records,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(f"scenes={len(records)} exact_duplicates={len(records) - len(hashes)}")
    if failures:
        print("\n".join(failures))
        return 1
    print("PASS: 60/60 assets, sources, 1920x1080 dimensions, and unique hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
