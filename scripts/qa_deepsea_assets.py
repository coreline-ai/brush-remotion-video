#!/usr/bin/env python3
"""Validate, normalize, and contact-sheet the deep-sea 60-scene image set."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "examples/deepsea-light-v01/assets-ink-v1"
OUT_SIZE = (1920, 1080)
EXPECTED = 60


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def perceptual_signature(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("L").resize((32, 18), Image.Resampling.BILINEAR), dtype=np.float32)


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    paths = [ASSET_DIR / f"scene-{i:02d}.png" for i in range(1, EXPECTED + 1)]
    missing = [p.name for p in paths if not p.is_file()]
    if missing:
        raise SystemExit(f"missing {len(missing)} scenes: {', '.join(missing)}")

    records = []
    signatures = []
    for i, path in enumerate(paths, start=1):
        image = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        ratio = image.width / image.height
        ratio_error = abs(ratio - (16 / 9)) / (16 / 9)
        if ratio_error > 0.012:
            raise SystemExit(f"{path.name}: ratio {ratio:.6f} is not 16:9; crop is forbidden")
        if image.size != OUT_SIZE:
            # Resize only: the accepted source ratio is already 16:9, so no crop or padding is introduced.
            image.resize(OUT_SIZE, Image.Resampling.LANCZOS).save(path, optimize=True)
            image = Image.open(path).convert("RGB")
        records.append({
            "scene": i,
            "asset": str(path.relative_to(ROOT)),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "ratioError": round(ratio_error, 8),
            "sha256": digest(path),
            "cropApplied": False,
            "fullBleed": True,
        })
        signatures.append(perceptual_signature(image))

    exact_duplicates = {}
    for row in records:
        exact_duplicates.setdefault(row["sha256"], []).append(row["scene"])
    exact_duplicate_groups = [v for v in exact_duplicates.values() if len(v) > 1]
    near_duplicates = []
    for i in range(EXPECTED):
        for j in range(i + 1, EXPECTED):
            mae = float(np.mean(np.abs(signatures[i] - signatures[j])))
            if mae < 2.5:
                near_duplicates.append({"sceneA": i + 1, "sceneB": j + 1, "meanAbsError": round(mae, 3)})

    thumb_w, thumb_h = 320, 180
    sheet = Image.new("RGB", (thumb_w * 5, (thumb_h + 26) * 12), (5, 8, 18))
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(paths):
        image = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % 5) * thumb_w
        y = (idx // 5) * (thumb_h + 26)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + 26), fill=(8, 14, 28))
        draw.text((x + 8, y + thumb_h + 5), f"SCENE {idx + 1:02d}", fill=(224, 239, 255))
    sheet.save(ASSET_DIR / "contact-sheet.png", optimize=True)

    manifest = {
        "version": "deepsea-light-v01",
        "expectedSceneCount": EXPECTED,
        "actualSceneCount": len(records),
        "expectedSize": list(OUT_SIZE),
        "exactDuplicateGroups": exact_duplicate_groups,
        "nearDuplicateWarnings": near_duplicates,
        "failures": [],
        "scenes": records,
    }
    (ASSET_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "sceneCount": len(records),
        "size": OUT_SIZE,
        "exactDuplicateGroups": exact_duplicate_groups,
        "nearDuplicateWarnings": near_duplicates,
        "contactSheet": str((ASSET_DIR / "contact-sheet.png").relative_to(ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
