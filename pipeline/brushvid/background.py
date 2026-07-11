"""background.py — 배경 이미지 준비.

- clean(): 원본의 종이/격자/여백(near-paper) 픽셀을 종이색으로 치환 (붓이 지나가도 배경만 드러나게)
- generate(): 전략 3종
    imagegen    — codex exec 내장 image_gen 으로 손그림 배경 생성 (codex 부재 시 preset 폴백 + 경고)
    preset      — PIL 절차 합성 (잉크 스트로크 + 수채 워시, 시드 고정 결정적)
    user-images — 사용자 이미지를 1920×1080 종이 캔버스에 contain-fit 배치
"""
from __future__ import annotations

import logging
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

log = logging.getLogger(__name__)

W, H = 1920, 1080
PAPER = (251, 250, 246)  # #fbfaf6
CODEX_APP_BIN = "/Applications/Codex.app/Contents/Resources/codex"

_PROMPT_TEMPLATE = (
    "A hand-drawn ink line-art sketch combined with soft, light pastel watercolor washes, "
    "on a clean warm-white paper background. Subject: {subject}. Loose confident pen strokes, "
    "delicate watercolor in violet / teal / amber tones, airy editorial composition with GENEROUS "
    "EMPTY WHITE SPACE in the upper-left third (reserved for title and widgets). Absolutely NO text, "
    "no letters, no numbers, no labels. Minimal, elegant, high detail, 16:9 landscape."
)


def clean(image_path: str | Path, out_path: str | Path,
          lum_thresh: float = 237.0, sat_thresh: float = 12.0,
          paper: tuple[int, int, int] = PAPER) -> Path:
    """near-paper 픽셀(밝고 채도 낮음)을 종이색으로 치환한 정제 이미지를 저장."""
    im = Image.open(image_path).convert("RGB")
    arr = np.asarray(im).astype(np.int16)
    mx = arr.max(2)
    mn = arr.min(2)
    lum = arr.mean(2)
    content = (lum < lum_thresh) | ((mx - mn) > sat_thresh)
    out = arr.copy()
    for c, v in enumerate(paper):
        out[:, :, c][~content] = v
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out.astype(np.uint8)).save(out_path)
    log.info("clean: content %.1f%% -> %s", content.mean() * 100, out_path)
    return out_path


PEN_PAPER = (242, 238, 227)  # pen 프로파일 종이 톤 (#f2eee3)


def contain_fit(image: Image.Image, size: tuple[int, int] = (W, H),
                paper: tuple[int, int, int] = PEN_PAPER) -> Image.Image:
    """이미지를 잘림 없이 contain-fit — 남는 영역은 종이색 패딩 (pen 배경 규칙)."""
    tw, th = size
    canvas = Image.new("RGB", (tw, th), paper)
    im = image.convert("RGB")
    scale = min(tw / im.width, th / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    canvas.paste(im.resize((nw, nh), Image.LANCZOS), ((tw - nw) // 2, (th - nh) // 2))
    return canvas


def separate_ink(bg_path: str | Path, out_alpha_path: str | Path, out_flat_path: str | Path,
                 paper: tuple[int, int, int] = PEN_PAPER) -> dict:
    """잉크-알파 분리 (pen 프로파일 핵심): 종이는 항상 보이고 잉크만 리빌되도록.

    contain-fit(잘림 금지) 후 lum/sat 기반 잉크 알파를 계산한다:
      a_dark = (205 - lum) / 40, a_color = (sat - 45) / 50, alpha = max(둘) 0..1 클램프(경계 그라데이션)
    산출: out_alpha_path = 잉크 RGBA, out_flat_path = 잉크만 흰 배경(routes 입력용).
    """
    src = contain_fit(Image.open(bg_path), paper=paper)
    arr = np.asarray(src).astype(np.float32)
    lum = arr.mean(axis=2)
    sat = arr.max(axis=2) - arr.min(axis=2)
    a_dark = (205.0 - lum) / 40.0
    a_color = (sat - 45.0) / 50.0
    alpha = np.clip(np.maximum(a_dark, a_color), 0.0, 1.0)

    out_alpha_path, out_flat_path = Path(out_alpha_path), Path(out_flat_path)
    out_alpha_path.parent.mkdir(parents=True, exist_ok=True)
    out_flat_path.parent.mkdir(parents=True, exist_ok=True)

    rgba = np.dstack([arr.astype(np.uint8), (alpha * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(out_alpha_path)

    # flat: 잉크를 흰 배경 위에 알파 합성 (콘텐츠 마스크/routes 생성용)
    white = np.full_like(arr, 255.0)
    flat = arr * alpha[..., None] + white * (1.0 - alpha[..., None])
    Image.fromarray(flat.astype(np.uint8)).save(out_flat_path)

    ink_frac = float((alpha > 0.5).mean())
    log.info("separate_ink: 잉크 %.1f%% -> %s / %s", ink_frac * 100, out_alpha_path.name, out_flat_path.name)
    return {"alpha": out_alpha_path, "flat": out_flat_path, "inkFraction": ink_frac}


def find_codex() -> str | None:
    """작동하는 codex 바이너리 경로 (앱 우선, 없으면 PATH)."""
    if Path(CODEX_APP_BIN).is_file():
        return CODEX_APP_BIN
    return shutil.which("codex")


def generate(strategy: str, out_path: str | Path, *, subject: str | None = None,
             images: list[str | Path] | None = None, seed: int = 1,
             codex_bin: str | None = None) -> dict:
    """전략에 따라 배경 PNG 생성. 반환: {"strategy": 실제 사용 전략, "path": 경로}."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if strategy == "imagegen":
        cx = codex_bin if codex_bin is not None else find_codex()
        if cx and Path(cx).is_file():
            _gen_imagegen(cx, subject or "a calm natural landscape", out_path)
            return {"strategy": "imagegen", "path": out_path}
        log.warning("codex exec 부재 — imagegen 불가, preset 배경으로 폴백")
        strategy = "preset"

    if strategy == "preset":
        _gen_preset(out_path, subject=subject, seed=seed)
        return {"strategy": "preset", "path": out_path}

    if strategy == "user-images":
        if not images:
            raise ValueError("user-images 전략에는 images 가 최소 1장 필요")
        _compose_user_images([Path(p) for p in images], out_path)
        return {"strategy": "user-images", "path": out_path}

    raise ValueError(f"알 수 없는 배경 전략: {strategy}")


def _gen_imagegen(codex_bin: str, subject: str, out_path: Path) -> None:
    """codex exec 내장 image_gen 으로 배경 생성 (API 키 불필요)."""
    prompt = _PROMPT_TEMPLATE.format(subject=subject)
    instruction = (
        "너의 내장 image_gen 툴(imagegen 스킬)만 사용해 이미지 1장을 생성해. "
        "OPENAI_API_KEY 기반 CLI는 절대 쓰지 마. "
        f"생성 후 결과 PNG를 정확히 '{out_path}' 로 복사해. 프롬프트: {prompt}"
    )
    subprocess.run(
        [codex_bin, "exec", "--dangerously-bypass-approvals-and-sandbox",
         "--skip-git-repo-check", "-C", str(out_path.parent), instruction],
        check=True,
    )
    if not out_path.is_file():
        raise RuntimeError(f"imagegen 결과 파일 생성 실패: {out_path}")


def _gen_preset(out_path: Path, subject: str | None = None, seed: int = 1) -> None:
    """PIL 절차 합성 폴백 배경 — 종이 위 수채 워시 + 잉크 능선 스케치 (시드 고정 결정적)."""
    rng = np.random.default_rng(seed)
    canvas = Image.new("RGB", (W, H), PAPER)

    # 수채 워시 (반투명 타원 → 블러)
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    palette = [(148, 122, 190), (94, 158, 160), (214, 168, 96)]  # violet / teal / amber
    for i in range(7):
        col = palette[i % len(palette)]
        cx = int(rng.uniform(W * 0.42, W * 0.92))
        cy = int(rng.uniform(H * 0.3, H * 0.86))
        rx = int(rng.uniform(120, 300))
        ry = int(rng.uniform(70, 170))
        wd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=col + (46,))
    wash = wash.filter(ImageFilter.GaussianBlur(26))
    canvas.paste(wash, (0, 0), wash)

    # 잉크 능선/지평선 스케치 (우측 하단 위주 — 좌상단은 타이틀/위젯용 여백)
    d = ImageDraw.Draw(canvas)
    ink = (52, 48, 44)
    for k in range(3):
        base_y = H * (0.52 + 0.14 * k)
        amp = 36 + 22 * k
        pts = []
        for x in range(int(W * 0.34), W - 90, 24):
            t = x / W * math.tau
            y = base_y + amp * math.sin(t * (1.4 + 0.5 * k) + k) + float(rng.normal(0, 4))
            pts.append((x, min(H - 80.0, max(H * 0.3, y))))
        d.line(pts, fill=ink, width=4 - k if k < 3 else 2, joint="curve")
    # 소나무 실루엣 획
    for k in range(4):
        tx = int(rng.uniform(W * 0.5, W * 0.9))
        ty = int(rng.uniform(H * 0.42, H * 0.6))
        th = int(rng.uniform(90, 190))
        d.line([(tx, ty), (tx, ty + th)], fill=ink, width=5)
        for j in range(4):
            yy = ty + th * (j + 1) / 5
            span = th * 0.32 * (j + 2) / 5
            d.line([(tx - span, yy), (tx + span, yy - th * 0.1)], fill=ink, width=3)

    canvas.save(out_path)
    log.info("preset 배경 생성 (seed=%d, subject=%s) -> %s", seed, subject, out_path)


def _compose_user_images(images: list[Path], out_path: Path) -> None:
    """사용자 이미지들을 종이 캔버스에 contain-fit 으로 가로 배치."""
    canvas = Image.new("RGB", (W, H), PAPER)
    n = len(images)
    margin = 90
    slot_w = (W - margin * 2) // n
    slot_h = H - margin * 2
    for i, p in enumerate(images):
        im = Image.open(p).convert("RGB")
        scale = min(slot_w / im.width, slot_h / im.height)
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.LANCZOS)
        x = margin + i * slot_w + (slot_w - nw) // 2
        y = margin + (slot_h - nh) // 2
        canvas.paste(im, (x, y))
    canvas.save(out_path)
