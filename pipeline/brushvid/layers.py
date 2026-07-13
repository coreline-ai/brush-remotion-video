"""pen-brush 프로파일용 원본 이미지 레이어 분리.

한 장의 완성 이미지를 다음 세 자산으로 변환한다.
  - outline RGBA: 얇은 중성 잉크선만 포함
  - outline-flat RGB: outline routes 분석용 흰 배경 합성본
  - color RGBA: 원본 색상/질감을 보존한 채 종이 배경만 투명화

고정 좌표나 피사체별 규칙을 사용하지 않는다. 모든 임계값은 정규화된
명도/채도와 캔버스 크기에 대해 계산된다.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize

from .background import PEN_PAPER, contain_fit

log = logging.getLogger(__name__)


def _border_paper(arr: np.ndarray) -> np.ndarray:
    """외곽 띠의 저채도 밝은 픽셀로 종이색을 강건하게 추정."""
    h, w, _ = arr.shape
    band = max(2, round(min(w, h) * 0.025))
    border = np.concatenate([
        arr[:band].reshape(-1, 3), arr[-band:].reshape(-1, 3),
        arr[:, :band].reshape(-1, 3), arr[:, -band:].reshape(-1, 3),
    ])
    sat = border.max(1) - border.min(1)
    lum = border.mean(1)
    candidates = border[(sat < 24) & (lum > np.percentile(lum, 45))]
    if len(candidates) < 16:
        candidates = border
    return np.median(candidates, axis=0)


def _content_alpha(arr: np.ndarray, paper: np.ndarray) -> np.ndarray:
    """종이와의 색 거리 + 채도 + 어두움을 합친 부드러운 콘텐츠 알파."""
    rgb = arr / 255.0
    paper01 = paper / 255.0
    dist = np.sqrt(np.mean((rgb - paper01) ** 2, axis=2))
    sat = rgb.max(2) - rgb.min(2)
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    paper_lum = float(0.299 * paper01[0] + 0.587 * paper01[1] + 0.114 * paper01[2])
    a_dist = np.clip((dist - 0.018) / 0.085, 0.0, 1.0)
    a_sat = np.clip((sat - 0.025) / 0.12, 0.0, 1.0)
    a_dark = np.clip((paper_lum - lum - 0.025) / 0.19, 0.0, 1.0)
    alpha = np.maximum.reduce([a_dist, a_sat, a_dark])
    alpha[alpha < 0.045] = 0.0
    return alpha


def _outline_alpha(arr: np.ndarray, content_alpha: np.ndarray) -> np.ndarray:
    """local contrast 기반 샤프 선 추출. 팽창(dilation)을 하지 않아 두께를 보존."""
    rgb = arr / 255.0
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    sat = rgb.max(2) - rgb.min(2)
    local = ndimage.gaussian_filter(lum, sigma=1.7) - lum
    neutral_ink = np.clip((0.34 - sat) / 0.14, 0.0, 1.0)
    edge = np.clip((local - 0.025) / 0.10, 0.0, 1.0) * neutral_ink
    dark_core = np.clip((0.24 - lum) / 0.13, 0.0, 1.0) * neutral_ink
    alpha = np.maximum(edge, dark_core) * np.clip(content_alpha * 1.35, 0.0, 1.0)
    alpha[alpha < 0.05] = 0.0
    return alpha


def line_thickness(alpha: np.ndarray) -> float:
    """검은 면적 / skeleton 길이 기반 평균 선 두께(px)."""
    mask = alpha >= 0.32
    if not mask.any():
        return 0.0
    skeleton_px = int(skeletonize(mask).sum())
    return float(mask.sum() / max(1, skeleton_px))


def estimate_line_thickness(image_path: str | Path, *, paper: tuple[int, int, int] = PEN_PAPER) -> float:
    """RGB/RGBA 이미지의 중성 local-contrast 선 두께를 동일 공식으로 계측."""
    im = Image.open(image_path)
    if im.mode == "RGBA":
        # The transparent color layer keeps the source RGB underneath its alpha.
        # Estimate that paper first instead of compositing on the pen-only paper tone;
        # otherwise a contain-fitted image produces a false border and inflates the
        # measured final line thickness for pen-brush QA.
        rgba = np.asarray(im.convert("RGBA"))
        rgba_paper = _border_paper(rgba[..., :3].astype(np.float32))
        base = Image.new("RGBA", im.size, (*[int(round(v)) for v in rgba_paper], 255))
        base.alpha_composite(im)
        im = base.convert("RGB")
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    content_alpha = _content_alpha(arr, _border_paper(arr))
    return line_thickness(_outline_alpha(arr, content_alpha))


def prepare_pen_brush_layers(
    image_path: str | Path,
    outline_path: str | Path,
    outline_flat_path: str | Path,
    color_path: str | Path,
    *,
    size: tuple[int, int],
    paper: tuple[int, int, int] = PEN_PAPER,
    content_path: str | Path | None = None,
) -> dict:
    """원본 한 장을 pen-brush 렌더 자산으로 분리하고 계측값을 반환.

    빈 이미지와 사실상 전체 화면이 콘텐츠인 입력은 명시적으로 거부한다. 후자는
    종이 배경을 투명화할 근거가 없어 색상 누출 없는 2단계 리빌을 보장할 수 없다.
    """
    src = contain_fit(Image.open(image_path), size=size, paper=paper)
    arr = np.asarray(src).astype(np.float32)
    estimated_paper = _border_paper(arr)
    color_alpha = _content_alpha(arr, estimated_paper)
    content_fraction = float((color_alpha >= 0.10).mean())
    if content_fraction < 0.0005:
        raise ValueError("pen-brush 레이어 분리 실패: 콘텐츠가 없는 빈 이미지")
    if content_fraction > 0.97:
        raise ValueError("pen-brush 레이어 분리 실패: 종이 배경을 식별할 수 없는 full-bleed 이미지")

    outline_alpha = _outline_alpha(arr, color_alpha)
    outline_fraction = float((outline_alpha >= 0.20).mean())
    if outline_fraction < 0.00005:
        raise ValueError("pen-brush 레이어 분리 실패: 외곽선을 검출하지 못함")

    outline_path = Path(outline_path)
    outline_flat_path = Path(outline_flat_path)
    color_path = Path(color_path)
    content_path = Path(content_path) if content_path is not None else None
    for path in (outline_path, outline_flat_path, color_path, content_path):
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)

    # 원본 RGB를 outline에 복사하지 않는다. 중성 charcoal로 고정해 색상 선누출 방지.
    charcoal = np.empty_like(arr)
    charcoal[:] = (48, 45, 42)
    outline_rgba = np.dstack([charcoal.astype(np.uint8), (outline_alpha * 255).astype(np.uint8)])
    Image.fromarray(outline_rgba, "RGBA").save(outline_path)

    white = np.full_like(arr, 255.0)
    outline_flat = charcoal * outline_alpha[..., None] + white * (1.0 - outline_alpha[..., None])
    Image.fromarray(outline_flat.astype(np.uint8), "RGB").save(outline_flat_path)

    color_rgba = np.dstack([arr.astype(np.uint8), (color_alpha * 255).astype(np.uint8)])
    Image.fromarray(color_rgba, "RGBA").save(color_path)
    if content_path is not None:
        content = arr * color_alpha[..., None] + white * (1.0 - color_alpha[..., None])
        Image.fromarray(content.astype(np.uint8), "RGB").save(content_path)

    metrics = {
        "outline": outline_path,
        "outlineFlat": outline_flat_path,
        "color": color_path,
        "content": content_path,
        "contentFraction": content_fraction,
        "outlineFraction": outline_fraction,
        "lineThickness": line_thickness(outline_alpha),
        "paperRgb": [round(float(v), 2) for v in estimated_paper],
    }
    log.info(
        "pen-brush layers: content %.2f%% outline %.2f%% thickness %.3fpx -> %s",
        content_fraction * 100, outline_fraction * 100, metrics["lineThickness"], outline_path.parent,
    )
    return metrics
