import { describe, expect, it } from "vitest";
import { sharedProgress } from "../src/lib/easing";
import { pointOnPolyline } from "../src/lib/geometry";
import { buildDynamicStrokes, hash01, jitterPoints, normalizeBrushDynamics } from "../src/lib/dynamics";
import type { Stroke } from "../src/schema";

describe("pointOnPolyline (TC-1.1)", () => {
  const line: Array<[number, number]> = [[0, 0], [10, 0]];
  it("t=0 → 첫 점, t=1 → 끝 점, t=0.5 → 중간", () => {
    expect(pointOnPolyline(line, 0)).toMatchObject({ x: 0, y: 0, angle: 0 });
    expect(pointOnPolyline(line, 1)).toMatchObject({ x: 10, y: 0 });
    expect(pointOnPolyline(line, 0.5)).toMatchObject({ x: 5, y: 0 });
  });
  it("꺾인 폴리라인에서 경로 길이 기준으로 보간한다", () => {
    const bent: Array<[number, number]> = [[0, 0], [10, 0], [10, 10]]; // 총 길이 20
    const p = pointOnPolyline(bent, 0.75); // target 15 → 두 번째 구간 중간
    expect(p.x).toBeCloseTo(10);
    expect(p.y).toBeCloseTo(5);
    expect(p.angle).toBeCloseTo(90);
  });
  it("t 범위 밖은 클램프된다", () => {
    expect(pointOnPolyline(line, -1).x).toBe(0);
    expect(pointOnPolyline(line, 2).x).toBe(10);
  });
});

describe("sharedProgress (TC-1.3)", () => {
  it("start 이전 0, end 이후 1", () => {
    expect(sharedProgress(-5, 0, 100)).toBe(0);
    expect(sharedProgress(150, 0, 100)).toBe(1);
  });
  it("linear 모드는 정확한 등속", () => {
    expect(sharedProgress(50, 0, 100, true)).toBeCloseTo(0.5);
    expect(sharedProgress(72, 0, 100, true)).toBeCloseTo(0.72);
  });
  it("이징 모드는 raw 72%에서 조기 완성 스냅", () => {
    expect(sharedProgress(72, 0, 100, false)).toBe(1);
    expect(sharedProgress(71, 0, 100, false)).toBeLessThan(1);
  });
  it("단조 증가한다", () => {
    let prev = -1;
    for (let f = 0; f <= 100; f += 5) {
      const v = sharedProgress(f, 0, 100);
      expect(v).toBeGreaterThanOrEqual(prev);
      prev = v;
    }
  });
  it("end<=start면 스텝 함수", () => {
    expect(sharedProgress(4, 5, 5)).toBe(0);
    expect(sharedProgress(5, 5, 5)).toBe(1);
  });
});

const strokes: Stroke[] = [
  { id: "a", kind: "contour", width: 10, start: 8, end: 60, points: [[0, 0], [100, 0], [100, 100]] },
  { id: "b", kind: "seal", width: 20, start: 60.5, end: 120.7, points: [[0, 50], [200, 50]] },
];

describe("buildDynamicStrokes (TC-1.2)", () => {
  it("seed 고정 시 두 번 호출해도 완전 동일 (deterministic)", () => {
    const opts = { touchScale: 1.45, touchJitter: 0.22, pathJitter: 6, randomizeOrder: true, randomReverse: true, seed: 7701 };
    expect(buildDynamicStrokes(strokes, 228, opts)).toEqual(buildDynamicStrokes(strokes, 228, opts));
  });
  it("seed가 다르면 결과가 달라진다", () => {
    const a = buildDynamicStrokes(strokes, 228, { touchJitter: 0.3, seed: 1 });
    const b = buildDynamicStrokes(strokes, 228, { touchJitter: 0.3, seed: 2 });
    expect(a).not.toEqual(b);
  });
  it("drawSpeedScale이 타임라인을 첫 시작점 기준으로 늘린다", () => {
    const { strokes: out, penInvisibleAfter } = buildDynamicStrokes(strokes, 228, { drawSpeedScale: 2 });
    expect(out[0].start).toBeCloseTo(8); // firstStart는 고정
    expect(out[1].end).toBeCloseTo(8 + (120.7 - 8) * 2);
    expect(penInvisibleAfter).toBeCloseTo(8 + (228 - 8) * 2);
  });
  it("빈 strokes는 그대로 통과한다 (TC-1.E1 렌더 전제)", () => {
    const r = buildDynamicStrokes([], 228, { seed: 1 });
    expect(r.strokes).toEqual([]);
    expect(r.drawEnd).toBe(228);
  });
});

describe("normalizeBrushDynamics / jitterPoints / hash01", () => {
  it("범위 밖 값을 클램프한다", () => {
    const n = normalizeBrushDynamics({ drawSpeedScale: 9, touchScale: 0.01, touchJitter: 5, pathJitter: 999 });
    expect(n).toMatchObject({ drawSpeedScale: 2.0, touchScale: 0.2, touchJitter: 0.8, pathJitter: 120 });
  });
  it("jitter 0이면 원본 그대로, 2점 직선은 4점으로 보간된다", () => {
    const pts: Array<[number, number]> = [[0, 0], [30, 0]];
    expect(jitterPoints(pts, 1, "k", 0)).toBe(pts);
    expect(jitterPoints(pts, 1, "k", 4)).toHaveLength(4);
  });
  it("hash01은 0~1 범위의 deterministic 값", () => {
    const v = hash01(7701, "stroke-1", 23);
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThanOrEqual(1);
    expect(hash01(7701, "stroke-1", 23)).toBe(v);
  });
});
