#!/usr/bin/env python3
"""Build a 60-scene review gallery for ai-personal-rules-imagegen-fhd."""

from __future__ import annotations

import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "ai-personal-rules-imagegen-fhd"
SOURCE = ROOT / "data" / PROJECT_ID / "source-render-props.json"
IMAGES = ROOT / "public" / PROJECT_ID / "bg"
OUTPUT = ROOT / "validation" / f"{PROJECT_ID}-scenes"

CHAPTERS = (
    (1, 10, "기준 세우기"),
    (11, 20, "검증·보안"),
    (21, 30, "프롬프트 운영"),
    (31, 40, "실전 적용"),
    (41, 50, "협업·자동화"),
    (51, 60, "나만의 AI 헌장"),
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size, index=7 if bold else 0)
            except (OSError, IndexError):
                try:
                    return ImageFont.truetype(str(path), size=size)
                except OSError:
                    pass
    return ImageFont.load_default()


def chapter_for(number: int) -> str:
    return next(label for start, end, label in CHAPTERS if start <= number <= end)


def load_scenes() -> list[dict]:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    scenes = []
    for number, scene in enumerate(raw["scenes"], 1):
        image = IMAGES / f"scene-{number:02d}-content.png"
        if not image.exists():
            raise FileNotFoundError(image)
        title = " / ".join(scene.get("topTitle", {}).get("lines", []))
        narration = " ".join(cue.get("text", "") for cue in scene.get("cues", []))
        scenes.append(
            {
                "number": number,
                "id": scene["id"],
                "chapter": chapter_for(number),
                "title": title,
                "narration": narration,
                "durationSeconds": round(scene["durationInFrames"] / 30, 3),
                "image": f"../../public/{PROJECT_ID}/bg/{image.name}",
            }
        )
    if len(scenes) != 60:
        raise ValueError(f"Expected 60 scenes, got {len(scenes)}")
    return scenes


def contact_sheet(scenes: list[dict], path: Path, heading: str) -> None:
    cols = 5
    thumb_w, thumb_h = 448, 252
    card_h = 336
    margin, gap, header_h = 56, 20, 128
    rows = (len(scenes) + cols - 1) // cols
    canvas = Image.new(
        "RGB",
        (margin * 2 + cols * thumb_w + (cols - 1) * gap, header_h + rows * card_h + margin),
        "#0c1622",
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 30), heading, fill="#f4ead6", font=font(34, bold=True))
    draw.text(
        (margin, 76),
        f"AI 개인 규칙 · 검증 · 보안 인포그래픽  |  {len(scenes)} scenes",
        fill="#a8b6c7",
        font=font(20),
    )
    for index, scene in enumerate(scenes):
        row, col = divmod(index, cols)
        x = margin + col * (thumb_w + gap)
        y = header_h + row * card_h
        with Image.open(ROOT / scene["image"].replace("../../", "")) as source:
            image = source.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        canvas.paste(image, (x, y))
        draw.rounded_rectangle((x, y + thumb_h + 10, x + 48, y + thumb_h + 52), 10, fill="#d49b46")
        draw.text((x + 10, y + thumb_h + 15), f"{scene['number']:02d}", fill="#0c1622", font=font(20, bold=True))
        draw.text(
            (x + 62, y + thumb_h + 14),
            scene["title"],
            fill="#f7f1e5",
            font=font(21, bold=True),
        )
    canvas.save(path, quality=92)


def build_markdown(scenes: list[dict]) -> str:
    lines = [
        "# AI 개인 규칙·검증·보안 인포그래픽 — 60씬 구성",
        "",
        "- 프로젝트: `ai-personal-rules-imagegen-fhd`",
        "- 규격: 1920×1080, 30fps",
        "- 길이: 10분 (씬당 10초)",
        "",
    ]
    for start, end, label in CHAPTERS:
        lines.extend([f"## {start:02d}–{end:02d}. {label}", ""])
        for scene in scenes[start - 1 : end]:
            lines.append(f"{scene['number']:02d}. **{scene['title']}** — {scene['narration']}")
        lines.append("")
    return "\n".join(lines)


def build_html(scenes: list[dict]) -> str:
    nav = "".join(
        f'<a href="#scene-{start:02d}">{start:02d}–{end:02d} {html.escape(label)}</a>'
        for start, end, label in CHAPTERS
    )
    cards = []
    for scene in scenes:
        eager = ' loading="eager"' if scene["number"] <= 4 else ' loading="lazy"'
        cards.append(
            f'''<article class="scene" id="scene-{scene['number']:02d}">
  <a class="image" href="{scene['image']}" target="_blank"><img src="{scene['image']}" alt="{scene['number']:02d}. {html.escape(scene['title'])}"{eager}></a>
  <div class="copy"><div class="meta"><span class="num">{scene['number']:02d}</span><span>{html.escape(scene['chapter'])}</span><span>10초</span></div>
  <h2>{html.escape(scene['title'])}</h2><p>{html.escape(scene['narration'])}</p></div>
</article>'''
        )
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 개인 규칙 · 60 Scene Review</title>
<style>
:root{{--ink:#101c29;--paper:#f5efe3;--gold:#d49b46;--muted:#607184;--line:#d9cdb9}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}
header{{padding:50px clamp(24px,5vw,84px) 36px;background:linear-gradient(130deg,#0a1420,#142a3b 72%,#31465a);color:white}}
.eyebrow{{color:#e7b567;font-weight:800;letter-spacing:.14em;font-size:13px}}h1{{font-size:clamp(38px,5vw,74px);line-height:1.03;margin:14px 0 16px;max-width:1100px;letter-spacing:-.04em}}.intro{{color:#c6d0db;font-size:18px;max-width:850px;line-height:1.7}}
.stats{{display:flex;gap:10px;flex-wrap:wrap;margin-top:26px}}.stat{{border:1px solid #536779;border-radius:999px;padding:8px 13px;color:#eef3f6;font-weight:700;font-size:14px}}
.actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}}.actions a{{background:var(--gold);color:#102131;text-decoration:none;padding:12px 16px;border-radius:10px;font-weight:900}}.actions a.secondary{{background:#edf1f4;color:#14283a}}
nav{{position:sticky;top:0;z-index:10;display:flex;gap:8px;overflow:auto;padding:12px clamp(20px,4vw,70px);background:rgba(245,239,227,.94);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}}nav a{{white-space:nowrap;color:#23394b;text-decoration:none;border:1px solid var(--line);background:#fffaf1;border-radius:999px;padding:8px 12px;font-size:13px;font-weight:800}}
main{{padding:38px clamp(18px,4vw,70px) 80px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:24px;max-width:1700px;margin:auto}}
.scene{{scroll-margin-top:76px;background:#fffaf2;border:1px solid var(--line);border-radius:20px;overflow:hidden;box-shadow:0 14px 38px rgba(39,49,60,.08)}}.image{{display:block;aspect-ratio:16/9;background:#ddd;overflow:hidden}}.image img{{display:block;width:100%;height:100%;object-fit:cover;transition:transform .35s}}.scene:hover img{{transform:scale(1.015)}}
.copy{{padding:20px 22px 24px}}.meta{{display:flex;gap:9px;align-items:center;color:var(--muted);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.05em}}.num{{display:grid;place-items:center;width:38px;height:30px;border-radius:9px;background:var(--gold);color:#172433;font-size:14px}}h2{{margin:14px 0 8px;font-size:25px;letter-spacing:-.025em}}p{{margin:0;color:#45586a;font-size:16px;line-height:1.65}}
footer{{padding:36px;text-align:center;background:#0d1925;color:#aebbc8}}@media(max-width:600px){{header{{padding-top:36px}}main{{padding-left:12px;padding-right:12px}}.copy{{padding:16px}}}}
</style></head><body>
<header><div class="eyebrow">AI PERSONAL OPERATING SYSTEM · FULL SCENE REVIEW</div><h1>AI 개인 규칙·검증·보안 인포그래픽</h1><div class="intro">로컬 원본 구성에서 60개 씬의 제목·내레이션·FHD 이미지를 모두 찾아 한 화면에 정리했습니다. 각 이미지를 누르면 1920×1080 원본을 엽니다.</div>
<div class="stats"><span class="stat">60 SCENES</span><span class="stat">10 MINUTES</span><span class="stat">1920×1080</span><span class="stat">30 FPS</span><span class="stat">10 SEC / SCENE</span></div>
<div class="actions"><a href="SCENARIO-PEN-VIDEO.md">펜 드로잉 시나리오</a><a class="secondary" href="contact-sheet-all.jpg">60씬 콘택트시트</a><a class="secondary" href="SCENE-CONTENT.md">전체 내용 문서</a><a class="secondary" href="scene-manifest.json">JSON 매니페스트</a></div></header>
<nav>{nav}</nav><main><section class="grid">{''.join(cards)}</section></main><footer>ai-personal-rules-imagegen-fhd · 60 scene source review</footer></body></html>'''


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    scenes = load_scenes()
    (OUTPUT / "scene-manifest.json").write_text(
        json.dumps({"projectId": PROJECT_ID, "sceneCount": len(scenes), "scenes": scenes}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT / "SCENE-CONTENT.md").write_text(build_markdown(scenes), encoding="utf-8")
    (OUTPUT / "index.html").write_text(build_html(scenes), encoding="utf-8")
    contact_sheet(scenes, OUTPUT / "contact-sheet-all.jpg", "AI 개인 규칙 · 60 Scene Overview")
    for start, end, label in CHAPTERS:
        contact_sheet(
            scenes[start - 1 : end],
            OUTPUT / f"contact-sheet-{start:02d}-{end:02d}.jpg",
            f"{start:02d}–{end:02d} · {label}",
        )
    print(OUTPUT / "index.html")


if __name__ == "__main__":
    main()
