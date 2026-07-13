import { describe, expect, it } from "vitest";
import { DrawingPhaseSchema } from "../src/schema";
import { phaseOpacity, phaseOutroOpacity } from "../src/scene/DrawingPhaseLayer";

describe("drawing phase handoff", () => {
  it("outline은 handoff 구간에서만 사라지고 paint는 유지된다", () => {
    const phase = DrawingPhaseSchema.parse({ kind: "outline", routes: "outline.json",
      fadeOutFrom: 100, fadeOutTo: 112 });
    expect(phaseOpacity(99, phase)).toBe(1);
    expect(phaseOpacity(106, phase)).toBeCloseTo(0.5);
    expect(phaseOpacity(113, phase)).toBe(0);
    const paint = DrawingPhaseSchema.parse({ kind: "paint", routes: "paint.json" });
    expect(phaseOpacity(999, paint)).toBe(1);
  });

  it("pen-brush 씬도 마지막 실재 프레임에서 종이 워시로 완전히 수렴한다", () => {
    expect(phaseOutroOpacity(281, 300, 18, 1)).toBe(0);
    expect(phaseOutroOpacity(290, 300, 18, 1)).toBeGreaterThan(0);
    expect(phaseOutroOpacity(299, 300, 18, 1)).toBe(1);
  });
});
