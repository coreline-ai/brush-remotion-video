import { describe, expect, it } from "vitest";
import { RenderPropsSchema, RoutesDataSchema } from "../src/schema";

const validProps = {
  schemaVersion: 1,
  projectId: "winter-demo",
  scenes: [
    {
      id: "scene-01",
      durationInFrames: 300,
      routes: "winter-demo/routes/scene-01.routes.json",
      cues: [{ text: "첫눈이 내립니다", from: 30, to: 90 }],
    },
  ],
};

describe("RenderPropsSchema", () => {
  it("TC-0.1: 유효 props가 parse를 통과하고 스키마 기본값이 채워진다", () => {
    const parsed = RenderPropsSchema.parse(validProps);
    expect(parsed.paper).toBe("#fbfaf6");
    expect(parsed.audio).toBeNull();
    expect(parsed.format).toBe("youtube");
    expect(parsed.scenes[0].faint).toBe(0.6);
    expect(parsed.scenes[0].linearDraw).toBe(false);
    expect(parsed.scenes[0].prewashHoldFrames).toBe(6);
  });

  it("TC-0.2: schemaVersion 누락 시 parse가 실패한다", () => {
    const { schemaVersion, ...withoutVersion } = validProps;
    expect(RenderPropsSchema.safeParse(withoutVersion).success).toBe(false);
  });

  it("TC-0.E1: cues[0].from이 문자열이면 에러 경로에 scenes.0.cues.0.from이 포함된다", () => {
    const bad = structuredClone(validProps) as Record<string, unknown>;
    (bad as typeof validProps).scenes[0].cues[0].from = "30" as unknown as number;
    const result = RenderPropsSchema.safeParse(bad);
    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((i) => i.path.join("."));
      expect(paths).toContain("scenes.0.cues.0.from");
    }
  });

  it("scenes가 비어 있으면 거부한다", () => {
    expect(RenderPropsSchema.safeParse({ ...validProps, scenes: [] }).success).toBe(false);
  });

  it("brush kind 'pen'은 src 없이 통과, 'image'는 src/w/h/tip 필수", () => {
    expect(RenderPropsSchema.safeParse({ ...validProps, brush: { kind: "pen" } }).success).toBe(true);
    expect(RenderPropsSchema.safeParse({ ...validProps, brush: { kind: "image" } }).success).toBe(false);
    // kind 미지정(기존 props) → image 기본 + 필수 필드 강제
    const legacy = RenderPropsSchema.parse({ ...validProps, brush: { src: "brush-draw/brush.png", w: 556, h: 344, tipx: 25, tipy: 315 } });
    expect(legacy.brush?.kind).toBe("image");
  });

  it("TC-2.E2: naturalEffects.kind 오타는 parse 단계에서 거부된다", () => {
    const bad = structuredClone(validProps) as Record<string, unknown> & typeof validProps;
    (bad.scenes[0] as Record<string, unknown>).naturalEffects = { kind: "mistt" };
    expect(RenderPropsSchema.safeParse(bad).success).toBe(false);
  });
});

describe("RoutesDataSchema (기존 포맷 호환)", () => {
  it("meta의 부가 필드(coverage 등)를 통과시킨다", () => {
    const routes = {
      meta: {
        image: "winter-demo/bg/scene-01.png",
        width: 1920,
        height: 1080,
        fps: 30,
        durationInFrames: 300,
        drawStart: 8,
        drawEnd: 220,
        penInvisibleAfter: 228,
        routeCount: 2,
        coverage: 0.98,
      },
      strokes: [
        { id: "s1", kind: "contour", width: 14, start: 8, end: 60, points: [[10, 20], [30, 40]] },
        { id: "s2", kind: "seal", width: 24, start: 60, end: 220, points: [[0, 100], [1920, 100]] },
      ],
    };
    const parsed = RoutesDataSchema.parse(routes);
    expect((parsed.meta as Record<string, unknown>).coverage).toBe(0.98);
    expect(parsed.strokes).toHaveLength(2);
  });

  it("strokes 빈 배열도 허용한다 (백지 이미지 케이스 — 렌더는 배경만 develop)", () => {
    const parsed = RoutesDataSchema.safeParse({
      meta: {
        image: "x.png", width: 1920, height: 1080, fps: 30, durationInFrames: 300,
        drawStart: 8, drawEnd: 220, penInvisibleAfter: 228, routeCount: 0,
      },
      strokes: [],
    });
    expect(parsed.success).toBe(true);
  });
});
