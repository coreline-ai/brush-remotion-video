#!/usr/bin/env python3
"""Create the visually curated v0.4 60-scene asset review set.

Unlike v0.3 this script never accepts a search result automatically. Every replacement
is pinned by NASA ID and every non-16:9 source is preserved with a dark extended stage.
"""
from __future__ import annotations

import hashlib
import json
import random
import runpy
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
V03 = ROOT / "examples/cosmic-random-brush-v03/assets/manifest.json"
OUT = ROOT / "examples/cosmic-random-brush-v04/assets"
SIZE = (1920, 1080)
TOOLS = runpy.run_path(str(ROOT / "scripts/prepare-cosmic-v03-assets.py"))

# v0.3에서 의미가 불명확하거나 부분 관측/콜라주였던 소스만 정확한 ID로 교체한다.
REPLACEMENTS = {
    5: "iss007e14882",                         # 선명한 태풍의 눈
    8: "GSFC_20171208_Archive_e001593",       # Black Marble 도시 불빛
    7: "iss074e0603570",                      # 제목과 일치하는 히말라야
    9: "GSFC_20171208_Archive_e002167",       # 장비가 보이지 않는 구름 소용돌이
    13: "art002e009276",                      # 달 전체가 보이는 far-side view
    17: "PIA00003",                           # Valles Marineris hemisphere
    18: "PIA00300",                           # Olympus Mons full view
    19: "PIA13163",                           # Mars northern ice cap
    21: "PIA15160",                           # Mercury full globe
    22: "PIA00104",                           # recognizable color Venus globe
    24: "PIA21985",                           # rectangular Great Red Spot close-up
    25: "PIA00023",                           # Io full disk
    27: "PIA17172",                           # complete backlit Saturn and rings
    30: "PIA00046",                           # natural-color Neptune full disk
    33: "PIA01322",                           # Orion Nebula full view
    56: "PIA13616",                           # galaxy cluster / dark matter field
    53: "PIA26274",                           # label-free magnetar artwork
    58: "GSFC_20171208_Archive_e000497",       # single newborn star image
    60: "PIA18033",                           # recognizable full Earth finale
}

SOURCE_CROPS = {
    5: (0.0, 0.0, 1.0, 0.975),  # remove the ISS frame line, not the hurricane
}

TRIM_SCENES = {
    2, 4, 10, 13, 14, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 35, 60,
}

CUTOUT_SCENES = {4, 13, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 35, 60}

# 전체 피사체가 보여야 하는 장면. 나머지는 crop retention 88% 이상일 때만 safe-cover.
STAGE_SCENES = {
    2, 4, 5, 10, 12, 13, 14, 17, 18, 19, 20,
    21, 22, 23, 25, 26, 27, 28, 29, 30,
    33, 34, 35, 36, 38, 39,
    42, 43, 44, 45, 46, 47, 48,
    50, 53, 56, 58, 60,
}

TITLE_OVERRIDES = {
    5: "05. 태풍의 눈",
    8: "08. 지구의 도시 불빛",
    9: "09. 구름의 소용돌이",
    17: "17. 마리너 계곡",
    18: "18. 올림푸스 산",
    19: "19. 화성의 북극관",
    21: "21. 수성의 전경",
    25: "25. 이오의 전경",
    30: "30. 해왕성의 전경",
    33: "33. 오리온 성운",
    56: "56. 암흑물질 속 은하단",
    58: "58. 태어나는 별",
    60: "60. 우주의 집, 지구",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_for(entry: dict) -> tuple[Path, dict]:
    scene = int(entry["scene"])
    nasa_id = REPLACEMENTS.get(scene) or entry.get("nasaId")
    if nasa_id:
        metadata = TOOLS["metadata_for_id"](nasa_id)
        return TOOLS["fetch_candidate"](nasa_id, metadata)
    source = ROOT / entry["file"]
    return source, {
        "nasaId": None,
        "sourceTitle": "Approved cosmic-random-brush scene-01 source",
        "credit": entry.get("credit") or "Approved v0.1 source",
        "sourcePage": entry.get("sourcePage"),
        "originalUrl": entry.get("originalUrl"),
        "dateCreated": entry.get("dateCreated"),
        "center": entry.get("center"),
    }


def crop_retention(size: tuple[int, int]) -> float:
    sw, sh = size
    source_ratio = sw / sh
    target_ratio = SIZE[0] / SIZE[1]
    return target_ratio / source_ratio if source_ratio > target_ratio else source_ratio / target_ratio


def trim_dark_margins(source: Image.Image, pad_ratio: float = 0.06) -> Image.Image:
    """Remove archival black canvas while retaining the complete bright/chromatic subject."""
    src = ImageOps.exif_transpose(source).convert("RGB")
    arr = np.asarray(src, dtype=np.float32)
    luma = arr @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    chroma = arr.max(axis=2) - arr.min(axis=2)
    content = (luma >= 13) | (chroma >= 9)
    ys, xs = np.where(content)
    if len(xs) < src.width * src.height * 0.01:
        return src
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    px = round((x1 - x0) * pad_ratio)
    py = round((y1 - y0) * pad_ratio)
    box = (max(0, x0 - px), max(0, y0 - py), min(src.width, x1 + px), min(src.height, y1 + py))
    return src.crop(box)


def vignette(image: Image.Image) -> Image.Image:
    w, h = image.size
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (h / 2)
    edge = np.clip((np.sqrt(nx * nx + ny * ny) - 0.48) / 0.55, 0, 1)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 1] = 2
    rgba[:, :, 2] = 12
    rgba[:, :, 3] = np.round(150 * edge).astype(np.uint8)
    overlay = Image.fromarray(rgba, "RGBA")
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def dark_stage(source: Image.Image, seed: int, *, cutout: bool = False) -> Image.Image:
    """Full source over a dark blurred extension; no source pixel is cropped."""
    src = ImageOps.exif_transpose(source).convert("RGB")
    bg = ImageOps.fit(src, SIZE, method=Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(54))
    bg = ImageEnhance.Brightness(bg).enhance(0.28)
    bg = ImageEnhance.Color(bg).enhance(0.72)
    canvas = vignette(bg).convert("RGBA")

    scale = min(1840 / src.width, 1000 / src.height)
    fg = src.resize((max(1, round(src.width * scale)), max(1, round(src.height * scale))),
                    Image.Resampling.LANCZOS)
    # Edge feather prevents a visible rectangular boundary on archival square sources.
    if cutout:
        arr = np.asarray(fg, dtype=np.float32)
        luma = arr @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        chroma = arr.max(axis=2) - arr.min(axis=2)
        alpha = np.clip(np.maximum((luma - 3) / 20, (chroma - 3) / 14), 0, 1)
        mask = Image.fromarray(np.round(alpha * 255).astype(np.uint8), "L").filter(
            ImageFilter.GaussianBlur(1.4))
    else:
        mask = Image.new("L", fg.size, 255)
        edge = min(72, max(16, min(fg.size) // 14))
        md = ImageDraw.Draw(mask)
        for i in range(edge):
            alpha = round(255 * (i / edge) ** 0.65)
            md.rectangle((i, i, fg.width - 1 - i, fg.height - 1 - i), outline=alpha)
    x, y = (SIZE[0] - fg.width) // 2, (SIZE[1] - fg.height) // 2
    canvas.alpha_composite(Image.merge("RGBA", (*fg.split(), mask)), (x, y))

    # Sparse, deterministic stars keep the side extension from reading as empty letterbox.
    stars = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    rng = random.Random(seed)
    for _ in range(90):
        sx, sy = rng.randrange(SIZE[0]), rng.randrange(SIZE[1])
        if x - 12 <= sx <= x + fg.width + 12 and y - 12 <= sy <= y + fg.height + 12:
            continue
        r = rng.choice((1, 1, 1, 2))
        sd.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(175, 210, 255, rng.randrange(35, 105)))
    return Image.alpha_composite(canvas, stars).convert("RGB")


def safe_cover(source: Image.Image) -> Image.Image:
    """Cover only when at least 88% of the source remains visible."""
    src = ImageOps.exif_transpose(source).convert("RGB")
    retention = crop_retention(src.size)
    if retention < 0.88:
        raise ValueError(f"unsafe cover retention: {retention:.3f}")
    return ImageOps.fit(src, SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def write_contact_sheet(entries: list[dict]) -> Path:
    tw, th, lh, cols = 384, 216, 44, 5
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, (th + lh) * rows), (3, 5, 13))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 16)
    small = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 12)
    for i, entry in enumerate(entries):
        im = Image.open(ROOT / entry["file"]).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + lh)
        sheet.paste(im, (x, y))
        draw.text((x + 7, y + th + 4), entry["title"], fill=(225, 240, 255), font=font)
        draw.text((x + 7, y + th + 23),
                  f"{entry['reviewStatus']} · {entry['composition']} · retention {entry['sourceRetention']:.3f}",
                  fill=(115, 155, 190), font=small)
    out = OUT / "contact-sheet.jpg"
    sheet.save(out, quality=93)
    return out


def main() -> int:
    old = json.loads(V03.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    for old_entry in old["scenes"]:
        scene = int(old_entry["scene"])
        source_path, metadata = source_for(old_entry)
        source_original = Image.open(source_path)
        source_original_size = source_original.size
        source = ImageOps.exif_transpose(source_original).convert("RGB")
        if scene in SOURCE_CROPS:
            x0, y0, x1, y1 = SOURCE_CROPS[scene]
            source = source.crop((round(source.width * x0), round(source.height * y0),
                                  round(source.width * x1), round(source.height * y1)))
        source = trim_dark_margins(source) if scene in TRIM_SCENES else source
        retention = crop_retention(source.size)
        composition = "identity-golden" if scene == 1 else "dark-stage"
        if scene == 1:
            result = Image.open(ROOT / old_entry["file"]).convert("RGB")
        elif scene not in STAGE_SCENES and retention >= 0.88:
            result = safe_cover(source)
            composition = "safe-cover"
        else:
            result = dark_stage(source, seed=260712 + (scene - 1) * 37,
                                cutout=scene in CUTOUT_SCENES)
            if scene in CUTOUT_SCENES:
                composition = "dark-cutout-stage"
        title = TITLE_OVERRIDES.get(scene, old_entry["title"])
        output = OUT / f"scene-{scene:02d}-{old_entry['slug']}.png"
        if scene == 1:
            output.write_bytes((ROOT / old_entry["file"]).read_bytes())
        else:
            result.save(output, optimize=True)
        review_status = "replace" if scene in REPLACEMENTS else ("golden" if scene == 1 else "recompose")
        entry = {
            **{k: old_entry[k] for k in ("scene", "slug", "seed")},
            "title": title,
            **metadata,
            "file": str(output.relative_to(ROOT)),
            "sourceWidth": source_original_size[0],
            "sourceHeight": source_original_size[1],
            "compositionSourceWidth": source.width,
            "compositionSourceHeight": source.height,
            "sourceRetention": 1.0 if composition != "safe-cover" else round(retention, 6),
            "composition": composition,
            "reviewStatus": review_status,
            "replacedV03Source": scene in REPLACEMENTS,
            "sourceCropApplied": scene in SOURCE_CROPS,
            "sourceFileSha256": sha256(source_path),
            "normalizedSha256": sha256(output),
            "width": SIZE[0],
            "height": SIZE[1],
            "manualQuality": {
                "subjectFullyVisible": True,
                "recognizableAtContactSheetSize": True,
                "noDiagramOrEmbeddedLabels": True,
                "noMultiPanelCollage": True,
            },
        }
        entries.append(entry)
        print(f"[{scene:02d}/60] {review_status:9s} {composition:15s} {metadata.get('nasaId') or 'golden'}")
    hashes = [entry["normalizedSha256"] for entry in entries]
    if len(set(hashes)) != 60:
        raise ValueError("v0.4 normalized image hashes are not unique")
    manifest = {
        "projectId": "cosmic-random-brush-v04-assets-review",
        "version": "0.4-assets-review",
        "canvas": {"width": SIZE[0], "height": SIZE[1]},
        "qualityContract": {
            "cropRetentionMin": 0.88,
            "darkStagePreservesFullSource": True,
            "diagramTextCollageAllowed": False,
            "approvalRequiredBeforeVideoRender": True,
        },
        "mediaUsageGuidelines": old.get("mediaUsageGuidelines"),
        "usageNote": old.get("usageNote"),
        "scenes": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_contact_sheet(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
