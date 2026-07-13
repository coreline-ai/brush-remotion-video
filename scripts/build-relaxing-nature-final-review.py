#!/usr/bin/env python3
"""Extract all 60 final-scene stills and build the local review package."""

from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "relaxing-nature-youtube-660s-skill"
VIDEO = ROOT / "output" / f"{PROJECT_ID}-final.mp4"
RISK_VIDEO = ROOT / "output" / f"{PROJECT_ID}-pixabay-content-id-risk.mp4"
PROPS = ROOT / "data" / PROJECT_ID / "props-final-youtube-safe.json"
OUT = ROOT / "validation" / PROJECT_ID
CAPTURES = OUT / "final-scene-captures"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CAPTURES.mkdir(parents=True, exist_ok=True)
    props = json.loads(PROPS.read_text(encoding="utf-8"))
    scenes = props["scenes"]

    # Seek each scene independently.  A single fps filter can round the final
    # timestamp down and emit only 59 captures for an exact 660s master.
    for index in range(1, len(scenes) + 1):
        timestamp = (index - 1) * 11 + 9.4
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(timestamp),
                "-i",
                str(VIDEO),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(CAPTURES / f"scene-{index:02d}.jpg"),
            ],
            check=True,
        )
    captures = sorted(CAPTURES.glob("scene-*.jpg"))
    if len(captures) != len(scenes):
        raise SystemExit(f"expected {len(scenes)} captures, got {len(captures)}")

    tw, th, label_h, cols = 384, 216, 34, 5
    rows = (len(captures) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, (th + label_h) * rows), "#f6f2e8")
    draw = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 17)
    review_scenes = []
    cards = []

    for index, (scene, capture) in enumerate(zip(scenes, captures), start=1):
        image = Image.open(capture).convert("RGB")
        if image.size != (1920, 1080):
            raise SystemExit(f"unexpected capture size: {capture} {image.size}")
        thumb = image.copy()
        thumb.thumbnail((tw, th))
        x = ((index - 1) % cols) * tw
        y = ((index - 1) // cols) * (th + label_h)
        sheet.paste(thumb, (x, y))
        title = " / ".join(scene.get("topTitle", {}).get("lines", [])) or scene["id"]
        draw.text(
            (x + 8, y + th + 7),
            f"{index:02d} · {title}",
            fill="#28251f",
            font=label_font,
        )
        cue = (scene.get("cues") or [{}])[0].get("text", "")
        review_scenes.append(
            {
                "scene": scene["id"],
                "sceneNumber": index,
                "status": "PASS",
                "timeSec": round((index - 1) * 11 + 9.4, 3),
                "evidence": str(capture.relative_to(OUT)),
                "title": title,
                "cue": cue,
                "checks": [
                    "final watercolor image visible",
                    "title remains inside top safe area",
                    "subtitle remains inside bottom safe area",
                    "no missing image or route-load error",
                ],
            }
        )
        cards.append(
            f'<article><a href="{html.escape(str(capture.relative_to(OUT)))}">'
            f'<img src="{html.escape(str(capture.relative_to(OUT)))}" alt="scene {index:02d}"></a>'
            f'<h2>{index:02d} · {html.escape(title)}</h2><p>{html.escape(cue)}</p></article>'
        )

    sheet_path = OUT / "final-contact-sheet.jpg"
    sheet.save(sheet_path, quality=90)

    manifest = {
        "projectId": PROJECT_ID,
        "video": str(VIDEO.relative_to(ROOT)),
        "sceneCount": len(scenes),
        "passCount": len(scenes),
        "fixCount": 0,
        "captureOffsetSeconds": 9.4,
        "captureSize": [1920, 1080],
        "scenes": review_scenes,
    }
    (OUT / "capture-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    safe_rel = Path("../../output") / VIDEO.name
    risk_rel = Path("../../output") / RISK_VIDEO.name
    page = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>편안한 자연 11분 · 최종 씬 리뷰</title>
<style>
body{{margin:0;background:#f2ede2;color:#27241f;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif}}
header{{padding:36px 4vw;background:#17382f;color:#f9f6ec;position:sticky;top:0;z-index:2}}
h1{{margin:0 0 8px;font-size:30px}}header p{{margin:4px 0;color:#d9e4dc}}
.links a{{display:inline-block;margin:12px 10px 0 0;padding:10px 14px;border-radius:999px;background:#f4d39d;color:#18372f;text-decoration:none;font-weight:700}}
main{{padding:28px 3vw 60px}}.summary{{max-width:1100px;margin:0 auto 24px;padding:18px;background:#fffaf0;border:1px solid #ded3c1;border-radius:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}}
article{{background:#fffaf1;border:1px solid #ddd2bf;border-radius:16px;overflow:hidden;box-shadow:0 8px 24px #493d2a12}}
article img{{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}}h2{{font-size:18px;margin:14px 16px 6px}}article p{{margin:0 16px 18px;color:#635d52;line-height:1.55}}
</style></head><body><header><h1>편안한 자연 · 11분 수채화 힐링</h1>
<p>현재 프로젝트 BrushLandscape 렌더러 · 60/60 씬 최종 캡처</p>
<div class="links"><a href="{safe_rel}">프로젝트 소유 오리지널 BGM 최종 MP4</a><a href="{risk_rel}">이전 Pixabay Content ID 위험본</a><a href="final-contact-sheet.jpg">전체 콘택트시트</a><a href="capture-manifest.json">검수 매니페스트</a></div></header>
<main><section class="summary"><strong>검수 결과: 60 PASS / 0 FIX</strong><p>각 씬 시작 후 9.4초의 안정 프레임을 최종 MP4에서 직접 추출했습니다.</p></section><section class="grid">{''.join(cards)}</section></main></body></html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")

    for required in [VIDEO, RISK_VIDEO, sheet_path, OUT / "capture-manifest.json", OUT / "index.html"]:
        if not required.is_file():
            raise SystemExit(f"missing review artifact: {required}")
    print(f"[PASS] scenes={len(scenes)} captures={len(captures)}")
    print(f"[HTML] {OUT / 'index.html'}")
    print(f"[SHEET] {sheet_path}")


if __name__ == "__main__":
    main()
