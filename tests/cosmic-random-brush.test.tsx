import {describe, expect, it} from "vitest";
import {RandomTouchRoutesDataSchema, type RandomTouchStroke} from "../src/schema";
import {randomTouchBrushPose, sampleRandomTouchStroke} from "../src/scene/TravelingBrushLayer";

const stroke = (id: string, start: number, end: number, x = 100): RandomTouchStroke => ({
  id,
  kind: "random-touch",
  width: 260,
  start,
  end,
  opacity: 0.9,
  dryness: 0.2,
  points: [[x, 100, 0.2], [x + 100, 100, 1], [x + 200, 120, 0.2]],
});

const validRoutes = () => ({
  meta: {
    family: "free-random-touch",
    image: "fixture/source.png",
    width: 1920,
    height: 1080,
    fps: 30,
    durationInFrames: 300,
    drawStart: 37,
    drawEnd: 207,
    settleStart: 216,
    settleEnd: 232,
    brushInvisibleAfter: 214,
    strokeCount: 37,
    baseStrokeCount: 36,
    coverageStrokeCount: 1,
    targetMaskCoverage: 0.991,
    maskCoverage: 0.992,
    brushWidthRange: [230, 365],
    meanCenterJump: 800,
    maxCenterJump: 1500,
    seed: 260712,
    deterministic: true,
  },
  strokes: Array.from({length: 37}, (_, i) => stroke(`touch-${i + 1}`, 37 + i * 4.5, 40 + i * 4.5, 20 + i * 35)),
});

describe("cosmic random brush routes contract", () => {
  it("accepts the fixed brush-width and coverage contract", () => {
    const data = validRoutes();
    data.strokes[data.strokes.length - 1].end = 207;
    expect(RandomTouchRoutesDataSchema.parse(data).meta.maskCoverage).toBe(0.992);
  });

  it("rejects widening the brush to reach coverage", () => {
    const data = validRoutes();
    data.strokes[0].width = 480;
    expect(() => RandomTouchRoutesDataSchema.parse(data)).toThrow();
  });

  it("rejects an unknown routes family instead of falling through", () => {
    const data = validRoutes();
    data.meta.family = "semantic-contour";
    expect(() => RandomTouchRoutesDataSchema.parse(data)).toThrow();
  });

  it("keeps the brush visible while traveling but marks it as lifted", () => {
    const strokes = [stroke("a", 10, 14, 100), stroke("b", 18, 22, 900)];
    const active = sampleRandomTouchStroke(strokes[0], 12);
    const travel = randomTouchBrushPose(16, strokes);
    expect(active.touching).toBe(true);
    expect(travel).not.toBeNull();
    expect(travel?.touching).toBe(false);
    expect(travel!.x).toBeGreaterThan(strokes[0].points.at(-1)![0]);
    expect(travel!.x).toBeLessThan(strokes[1].points[0][0]);
  });

  it("hides the brush outside the drawing window", () => {
    const strokes = [stroke("a", 10, 14)];
    expect(randomTouchBrushPose(4, strokes)).toBeNull();
    expect(randomTouchBrushPose(20, strokes)).toBeNull();
  });
});
