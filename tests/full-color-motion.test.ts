import {describe, expect, it} from "vitest";
import {FullColorMotionPropsSchema} from "../src/schema";
import {
  FULL_COLOR_MOTION_TRANSITION_FRAMES,
  getFullColorMotionState,
} from "../src/scene/FullColorMotionSequence";

const props = {
  schemaVersion: 1,
  projectId: "full-color-test",
  scenes: [{
    id: "scene-01",
    image: "full-color-test/bg/scene-01.png",
    durationInFrames: 300,
  }],
};

describe("FullColorMotion props contract", () => {
  it("독립 schema가 원본 이미지 씬의 V1 기본값을 채운다", () => {
    const parsed = FullColorMotionPropsSchema.parse(props);
    expect(parsed.format).toBe("youtube");
    expect(parsed.audio).toBeNull();
    expect(parsed.scenes[0].movement).toBe("push-in");
    expect(parsed.scenes[0].effect).toBe("none");
    expect(parsed.scenes[0].reveal).toMatchObject({mode: "none", frames: 96});
  });

  it("선택형 brush reveal은 routes 없이는 props 단계에서 거부된다", () => {
    const bad = structuredClone(props) as typeof props & {scenes: Array<Record<string, unknown>>};
    bad.scenes[0].reveal = {mode: "brush", frames: 96};
    expect(FullColorMotionPropsSchema.safeParse(bad).success).toBe(false);
  });

  it("이전 씬 이후에는 정확히 12프레임 crossfade하고 brush reveal은 0→1이다", () => {
    const scene = FullColorMotionPropsSchema.parse({
      ...props,
      scenes: [{...props.scenes[0], movement: "pan-right", reveal: {
        mode: "brush", frames: 96, routes: "full-color-test/routes/scene-01.motion-reveal.routes.json",
      }}],
    }).scenes[0];
    const start = getFullColorMotionState(0, scene, true);
    const end = getFullColorMotionState(FULL_COLOR_MOTION_TRANSITION_FRAMES, scene, true);
    const revealEnd = getFullColorMotionState(96, scene, false);
    expect(start.incomingOpacity).toBe(0);
    expect(end.incomingOpacity).toBe(1);
    expect(start.revealProgress).toBe(0);
    expect(revealEnd.revealProgress).toBe(1);
    expect(start.transform).not.toBe(end.transform);
  });
});
