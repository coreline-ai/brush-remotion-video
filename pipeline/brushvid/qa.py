"""qa.py — QA 산출물: 프레임 캡처 → capture-manifest.json → 콘택트시트 PNG.

캡처는 `npx remotion still`(props 기준)으로, 콘택트시트는 PIL 그리드로 만든다.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from .render import ENTRY, REPO_ROOT

log = logging.getLogger(__name__)


def capture_frames(props_path: str | Path, frames: list[int], out_dir: str | Path, *,
                   composition: str = "BrushLandscape", labels: dict[int, str] | None = None,
                   repo_root: str | Path = REPO_ROOT) -> list[dict]:
    """지정 프레임들을 PNG 스틸로 캡처. 반환: manifest 항목 목록."""
    out_dir = Path(out_dir).resolve()  # 서브프로세스 cwd(repo_root)와 무관하게 절대 경로 사용
    out_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    for f in frames:
        png = out_dir / f"frame-{f:05d}.png"
        cmd = ["npx", "remotion", "still", ENTRY, composition, str(png),
               f"--props={Path(props_path).resolve()}", f"--frame={f}"]
        log.info("$ %s", " ".join(cmd))
        subprocess.run(cmd, cwd=str(repo_root), check=True)
        entries.append({
            "frame": f,
            "file": png.name,
            "label": (labels or {}).get(f, ""),
        })
    return entries


def write_manifest(entries: list[dict], out_dir: str | Path, *, project_id: str = "",
                   props: str = "") -> Path:
    """capture-manifest.json 저장."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"projectId": project_id, "props": str(props), "captures": entries}
    path = out_dir / "capture-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def contact_sheet(out_dir: str | Path, out_path: str | Path | None = None, *,
                  cols: int = 4, thumb_w: int = 460) -> Path:
    """캡처 디렉토리의 manifest 기반 콘택트시트 PNG 생성."""
    out_dir = Path(out_dir)
    manifest = json.loads((out_dir / "capture-manifest.json").read_text(encoding="utf-8"))
    captures = manifest["captures"]
    if not captures:
        raise ValueError("캡처 항목이 없어 콘택트시트를 만들 수 없음")

    label_h = 34
    thumbs: list[tuple[Image.Image, str]] = []
    for c in captures:
        im = Image.open(out_dir / c["file"]).convert("RGB")
        th = max(1, int(im.height * thumb_w / im.width))
        text = f"f{c['frame']}" + (f" — {c['label']}" if c.get("label") else "")
        thumbs.append((im.resize((thumb_w, th), Image.LANCZOS), text))

    thumb_h = max(t.height for t, _ in thumbs)
    rows = (len(thumbs) + cols - 1) // cols
    pad = 12
    sheet = Image.new("RGB", (cols * (thumb_w + pad) + pad,
                              rows * (thumb_h + label_h + pad) + pad), (24, 24, 26))
    d = ImageDraw.Draw(sheet)
    for i, (im, text) in enumerate(thumbs):
        x = pad + (i % cols) * (thumb_w + pad)
        y = pad + (i // cols) * (thumb_h + label_h + pad)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + thumb_h + 8), text, fill=(230, 228, 220))

    out = Path(out_path) if out_path else out_dir / "contact-sheet.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out
