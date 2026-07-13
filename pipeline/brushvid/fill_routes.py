"""pen-brush 채색 단계용 자동 brush routes 생성.

콘텐츠 마스크를 침식/연결성분 및 정규화 공간 셀로 자동 분할한다. 채색 경로는
아직 드러나지 않은 색 영역을 기준으로 seed 기반의 대각·세로 자유 붓길을
반복 배치한다. 따라서 같은 seed는 재현 가능하지만, 화면에는 좌우 래스터 스캔이
아닌 이리저리 쓱쓱 문지르는 붓질로 보인다. 피사체 이름이나 고정 좌표를 사용하지
않는다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def _mask_from_rgba(path: str | Path) -> np.ndarray:
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im)
    alpha = arr[..., 3]
    return alpha >= 12


def _zone_labels(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """침식 성분을 원본 마스크 전체로 확장. 성분이 적으면 3x3 정규화 셀 사용."""
    h, w = mask.shape
    iters = max(1, round(min(w, h) * 0.0045))
    seeds = ndimage.binary_erosion(mask, iterations=iters)
    labels, count = ndimage.label(seeds, structure=np.ones((3, 3), int))
    sizes = np.bincount(labels.ravel()) if count else np.array([])
    keep = [i for i in range(1, count + 1) if sizes[i] >= max(12, mask.sum() * 0.00015)]
    if len(keep) >= 2:
        compact = np.zeros_like(labels)
        for new, old in enumerate(keep, 1):
            compact[labels == old] = new
        # 모든 content pixel을 가장 가까운 seed label에 배정한다.
        _, inds = ndimage.distance_transform_edt(compact == 0, return_indices=True)
        expanded = compact[inds[0], inds[1]]
        expanded[~mask] = 0
        return expanded, len(keep)

    # 연결된 일러스트도 자연스럽게 여러 덩어리로 진행되도록 캔버스 비율 기반 셀 분할.
    rows, cols = (3, 2) if h > w else (2, 3)
    out = np.zeros(mask.shape, np.int32)
    n = 0
    min_pixels = max(8, int(mask.sum() * 0.004))
    for ry in range(rows):
        for cx in range(cols):
            y0, y1 = round(ry * h / rows), round((ry + 1) * h / rows)
            x0, x1 = round(cx * w / cols), round((cx + 1) * w / cols)
            cell = mask[y0:y1, x0:x1]
            if int(cell.sum()) < min_pixels:
                continue
            n += 1
            out[y0:y1, x0:x1][cell] = n
    if n == 0:
        out[mask] = 1
        n = 1
    return out, n


def _runs(row: np.ndarray) -> list[tuple[int, int]]:
    padded = np.pad(row.astype(np.int8), (1, 1))
    changes = np.diff(padded)
    return list(zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1) - 1))


def _coverage(mask: np.ndarray, routes: list[dict]) -> tuple[float, int]:
    h, w = mask.shape
    raster = Image.new("1", (w, h), 0)
    draw = ImageDraw.Draw(raster)
    for route in routes:
        _draw_route(draw, route)
    covered = np.asarray(raster, dtype=bool)
    missing = int((mask & ~covered).sum())
    return 1.0 - missing / max(1, int(mask.sum())), missing


def _draw_route(draw: ImageDraw.ImageDraw, route: dict) -> None:
    """SVG round-cap stroke와 동일하게 route를 coverage raster에 그린다."""
    pts = [tuple(p) for p in route["points"]]
    width = max(1, round(route["width"]))
    if len(pts) == 1:
        x, y = pts[0]
        r = width / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=1)
        return
    draw.line(pts, fill=1, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=1)


def _freehand_swoosh(
    cx: float,
    cy: float,
    *,
    length: float,
    width: float,
    angle: float,
    rng: np.random.Generator,
) -> list[list[float]]:
    """대각/세로 방향으로 휘어지는 한 번의 큰 붓질을 만든다.

    ``angle``은 의도적으로 수평을 제외한다. 각 획의 중간은 붓 폭의 일부만큼
    수직으로 흔들려 정렬된 줄무늬 대신 손으로 쓱쓱 문지른 느낌을 만든다.
    """
    ux, uy = math.cos(angle), math.sin(angle)
    nx, ny = -uy, ux
    points: list[list[float]] = []
    point_count = 7
    bend = float(rng.uniform(-0.22, 0.22) * width)
    for index in range(point_count):
        t = index / (point_count - 1)
        along = (t - 0.5) * length
        # 끝은 잔잔하게, 중간은 매번 다르게 휘게 한다.
        envelope = math.sin(math.pi * t)
        jitter = 0.0 if index in (0, point_count - 1) else float(rng.uniform(-0.16, 0.16) * width)
        sideways = envelope * bend + jitter
        points.append([cx + ux * along + nx * sideways, cy + uy * along + ny * sideways])
    if bool(rng.integers(0, 2)):
        points.reverse()
    return points


def _freehand_angle(rng: np.random.Generator) -> float:
    """좌우로 곧게 긋는 획은 배제하고 대각·세로 방향을 고른다."""
    return float(rng.uniform(math.radians(28), math.radians(152)))


def generate_fill_routes(
    color_rgba_path: str | Path,
    *,
    image_rel: str,
    duration: int,
    draw_start: float,
    draw_end: float,
    fps: int = 30,
    seed: int = 1,
) -> dict:
    """색상 RGBA 알파 영역을 99.99% 이상 덮는 brush routes를 생성."""
    rng = np.random.default_rng(seed)
    mask = _mask_from_rgba(color_rgba_path)
    if not mask.any():
        raise ValueError("fill routes 생성 실패: 채색 마스크가 비어 있음")
    h, w = mask.shape
    _labels, zone_count = _zone_labels(mask)

    brush_width = max(12.0, min(w, h) * 0.085)
    raw: list[dict] = []
    # 채색 중인 픽셀을 직접 추적한다. 다음 붓질은 아직 드러나지 않은 곳에서 시작하므로
    # 규칙적인 스캔 패턴 없이도 coverage 계약을 유지할 수 있다.
    raster = Image.new("1", (w, h), 0)
    raster_draw = ImageDraw.Draw(raster)

    def uncovered(target: np.ndarray) -> np.ndarray:
        return np.flatnonzero(target & ~np.asarray(raster, dtype=bool))

    def append_swoosh(center_index: int, *, zone: int, max_length: float,
                      width: float = brush_width, kind: str = "fill") -> None:
        cy, cx = divmod(int(center_index), w)
        length = float(rng.uniform(max(width * 2.8, max_length * 0.62), max_length))
        route = {
            "kind": kind,
            "width": width,
            "points": _freehand_swoosh(
                float(cx), float(cy), length=length, width=width,
                angle=_freehand_angle(rng), rng=rng,
            ),
            "zone": zone,
        }
        raw.append(route)
        _draw_route(raster_draw, route)

    # 자동 분할 라벨은 coverage 통계용으로만 남긴다. 색칠은 모든 피사체를 하나의
    # 캔버스로 보고 자유롭게 가로지른다. 그렇지 않으면 각 라벨 bbox 안에서만 붓이
    # 왕복해 다시 타일/블록처럼 보인다.
    target = mask
    ys, xs = np.nonzero(target)
    target_pixels = int(target.sum())
    span = math.hypot(float(xs.max() - xs.min()), float(ys.max() - ys.min()))
    max_length = min(max(w, h) * 0.72, max(brush_width * 4.8, span * 0.88))
    all_indices = np.flatnonzero(target)
    # 먼저 화면 곳곳에 긴 자유 붓길을 흩뿌린다.
    primer_count = max(4, min(8, math.ceil(target_pixels / max(1.0, brush_width * max_length * 2.4))))
    for _ in range(primer_count):
        append_swoosh(int(all_indices[int(rng.integers(0, len(all_indices)))]), zone=0,
                      max_length=max_length)

    # 이후에는 미노출 픽셀만 골라 메운다. 수평/수직 타일 스캔은 전혀 사용하지 않는다.
    max_guided = max(18, math.ceil(target_pixels / max(1.0, brush_width * max_length * 0.42)))
    for _ in range(max_guided):
        missing = uncovered(target)
        if len(missing) == 0:
            break
        append_swoosh(int(missing[int(rng.integers(0, len(missing)))]), zone=0,
                      max_length=max_length)

    # 첫 패스 뒤에도 남은 세밀한 알파 영역은 같은 대각/세로 붓질로만 보강한다.
    # 기존의 수평 seal을 쓰면 마지막에 줄무늬가 생기므로 금지한다.
    for _ in range(max(96, zone_count * 24)):
        missing = uncovered(mask)
        if len(missing) == 0:
            break
        append_swoosh(int(missing[int(rng.integers(0, len(missing)))]), zone=0,
                      max_length=brush_width * 3.3, width=brush_width * 1.06,
                      kind="fill-touchup")

    if len(uncovered(mask)):
        raise RuntimeError("자유 브러시 coverage 보강이 수렴하지 않았습니다")

    # 생성 순서대로 재생하면 한 존이 통째로 끝나 보인다. 전체 붓길을 seed로 섞어
    # 색이 화면 여러 곳에서 자유롭게 나타나도록 한다.
    rng.shuffle(raw)

    # 경로 길이 비례로 전체 단계 타이밍 배정.
    weights = []
    for rt in raw:
        (x0, y0), (x1, y1) = rt["points"][0], rt["points"][-1]
        weights.append(max(1.0, math.hypot(x1 - x0, y1 - y0)))
    total = max(1.0, sum(weights))
    cursor = float(draw_start)
    strokes = []
    for i, (rt, weight) in enumerate(zip(raw, weights)):
        span = (draw_end - draw_start) * weight / total
        end = draw_end if i == len(raw) - 1 else cursor + span
        strokes.append({"id": f"fill-{i:05d}", "kind": rt["kind"], "width": rt["width"],
                        "start": cursor, "end": end, "points": rt["points"], "zone": rt["zone"]})
        cursor = end

    coverage, missing = _coverage(mask, strokes)
    return {
        "meta": {"image": image_rel, "width": w, "height": h, "fps": fps,
                 "durationInFrames": duration, "drawStart": draw_start, "drawEnd": draw_end,
                 "penInvisibleAfter": min(duration, draw_end + 6), "routeCount": len(strokes),
                 "coverage": coverage, "missingPixels": missing, "zoneCount": zone_count,
                 "profile": "pen-brush-paint", "seed": seed,
                 "routeStyle": "seeded-freehand-swoosh"},
        "strokes": strokes,
    }


def write_fill_routes(data: dict, out_path: str | Path) -> Path:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
