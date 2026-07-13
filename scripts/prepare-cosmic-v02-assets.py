#!/usr/bin/env python3
"""Prepare the six deterministic validation images for cosmic v0.2.

Scene 01 is the approved v0.1 source byte-for-byte. Scenes 02-06 use NASA
Image and Video Library originals and record their source/credit in a manifest.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples/cosmic-random-brush-v02/assets"
CACHE = ROOT / "tmp/cosmic-random-brush-v02-source"
SIZE = (1920, 1080)
USAGE_URL = "https://www.nasa.gov/nasa-brand-center/images-and-media/"

SCENES = [
    {
        "scene": 1,
        "slug": "earth-orbit-sunrise",
        "title": "01. 지구 궤도 일출",
        "seed": 260712,
        "kind": "approved-golden",
        "local": ROOT / "examples/cosmic-random-brush/source.png",
        "credit": "Approved cosmic-random-brush v0.1 source",
        "fit": "identity",
    },
    {
        "scene": 2,
        "slug": "saturn-rings",
        "title": "02. 토성의 고리",
        "seed": 260749,
        "kind": "nasa-image-library",
        "nasaId": "PIA01969",
        "sourceTitle": "Saturn and its Rings",
        "credit": "NASA/JPL",
        "originalUrl": "https://images-assets.nasa.gov/image/PIA01969/PIA01969~orig.jpg",
        "sourcePage": "https://images.nasa.gov/details/PIA01969",
        "fit": "cover",
    },
    {
        "scene": 3,
        "slug": "barred-spiral-galaxy",
        "title": "03. 나선은하의 중심",
        "seed": 260786,
        "kind": "nasa-image-library",
        "nasaId": "GSFC_20171208_Archive_e002154",
        "sourceTitle": "Barred Spiral Galaxy",
        "credit": "NASA, ESA, and The Hubble Heritage Team (STScI/AURA); acknowledgment P. Knezek (WIYN)",
        "originalUrl": "https://images-assets.nasa.gov/image/GSFC_20171208_Archive_e002154/GSFC_20171208_Archive_e002154~orig.jpg",
        "sourcePage": "https://images.nasa.gov/details/GSFC_20171208_Archive_e002154",
        "fit": "cover",
    },
    {
        "scene": 4,
        "slug": "tarantula-nebula",
        "title": "04. 타란툴라 성운",
        "seed": 260823,
        "kind": "nasa-image-library",
        "nasaId": "PIA23647",
        "sourceTitle": "Tarantula Nebula Spitzer 3-Color Image",
        "credit": "NASA/JPL-Caltech",
        "originalUrl": "https://images-assets.nasa.gov/image/PIA23647/PIA23647~orig.jpg",
        "sourcePage": "https://images.nasa.gov/details/PIA23647",
        "fit": "cover",
    },
    {
        "scene": 5,
        "slug": "black-hole-accretion-disk",
        "title": "05. 블랙홀과 강착원반",
        "seed": 260860,
        "kind": "nasa-image-library",
        "nasaId": "PIA22085",
        "sourceTitle": "Black Hole With Jet (Artist's Concept)",
        "credit": "NASA/JPL-Caltech",
        "originalUrl": "https://images-assets.nasa.gov/image/PIA22085/PIA22085~orig.jpg",
        "sourcePage": "https://images.nasa.gov/details/PIA22085",
        "fit": "cover",
    },
    {
        "scene": 6,
        "slug": "low-contrast-lunar-surface",
        "title": "06. 고요의 바다",
        "seed": 260897,
        "kind": "nasa-image-library",
        "nasaId": "as11-40-5881",
        "sourceTitle": "Apollo 11 Mission image - Lunar surface and horizon",
        "credit": "NASA/JSC",
        "originalUrl": "https://images-assets.nasa.gov/image/as11-40-5881/as11-40-5881~orig.jpg",
        "sourcePage": "https://images.nasa.gov/details/as11-40-5881",
        "fit": "cover-dark-low-contrast",
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_image(source: Path, fit: str) -> Image.Image:
    im = Image.open(source).convert("RGB")
    if fit == "cover":
        scale = max(SIZE[0] / im.width, SIZE[1] / im.height)
        resized = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
        left = (resized.width - SIZE[0]) // 2
        top = (resized.height - SIZE[1]) // 2
        return resized.crop((left, top, left + SIZE[0], top + SIZE[1]))
    if fit == "cover-dark-low-contrast":
        im = ImageEnhance.Color(im).enhance(0.35)
        im = ImageEnhance.Contrast(im).enhance(0.62)
        im = ImageEnhance.Brightness(im).enhance(0.52)
        scale = max(SIZE[0] / im.width, SIZE[1] / im.height)
        resized = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
        left = (resized.width - SIZE[0]) // 2
        # 원본 상단의 검은 하늘과 하단 표면을 함께 남기기 위해 중심보다 약간 위를 취한다.
        top = max(0, min(resized.height - SIZE[1], (resized.height - SIZE[1]) // 2 - 80))
        return resized.crop((left, top, left + SIZE[0], top + SIZE[1]))
    raise ValueError(f"unknown fit: {fit}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = {
        "projectId": "cosmic-random-brush-v02",
        "version": "0.2-validation",
        "canvas": {"width": SIZE[0], "height": SIZE[1]},
        "mediaUsageGuidelines": USAGE_URL,
        "usageNote": "Validation/editorial use; acknowledge exact credits; no NASA endorsement implied.",
        "scenes": [],
    }
    for scene in SCENES:
        out = OUT / f"scene-{scene['scene']:02d}-{scene['slug']}.png"
        if scene["kind"] == "approved-golden":
            out.write_bytes(Path(scene["local"]).read_bytes())
            source = Path(scene["local"])
            source_url = None
        else:
            source = CACHE / f"{scene['nasaId']}.jpg"
            if not source.is_file():
                urllib.request.urlretrieve(scene["originalUrl"], source)
            fit_image(source, scene["fit"]).save(out, optimize=True)
            source_url = scene["originalUrl"]
        with Image.open(out) as image:
            if image.size != SIZE:
                raise ValueError(f"{out}: expected {SIZE}, got {image.size}")
        entry = {k: v for k, v in scene.items() if k not in {"local", "originalUrl"}}
        entry.update({
            "file": str(out.relative_to(ROOT)),
            "sourceFileSha256": sha256(source),
            "normalizedSha256": sha256(out),
            "originalUrl": source_url,
            "width": SIZE[0],
            "height": SIZE[1],
        })
        manifest["scenes"].append(entry)
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    thumb_w, thumb_h = 640, 360
    sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + 34) * 3), (4, 6, 15))
    draw = ImageDraw.Draw(sheet)
    for index, entry in enumerate(manifest["scenes"]):
        image = Image.open(ROOT / entry["file"]).convert("RGB").resize(
            (thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x, y = (index % 2) * thumb_w, (index // 2) * (thumb_h + 34)
        sheet.paste(image, (x, y))
        draw.text((x + 12, y + thumb_h + 8),
                  f"{entry['scene']:02d}. {entry['slug']}", fill=(222, 242, 255))
    sheet.save(OUT / "contact-sheet.jpg", quality=92)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
