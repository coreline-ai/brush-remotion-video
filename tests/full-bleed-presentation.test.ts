import {describe, expect, it} from "vitest";
import {getFullBleedPresentationState} from "../src/scene/FullBleedPresentationLayer";

const scaleOf = (transform: string) => Number(/^scale\(([^)]+)\)/.exec(transform)?.[1]);

describe("full-bleed presentation", () => {
  it("progressive sequence uses a 30-frame cross-dissolve only after scene 1", () => {
    const first = getFullBleedPresentationState(0, "progressive-frame-sequence", false, 300);
    const nextStart = getFullBleedPresentationState(0, "progressive-frame-sequence", true, 300);
    const nextEnd = getFullBleedPresentationState(30, "progressive-frame-sequence", true, 300);

    expect(first.dissolveFrames).toBe(30);
    expect(first.incomingOpacity).toBe(1);
    expect(nextStart.incomingOpacity).toBe(0);
    expect(nextEnd.incomingOpacity).toBe(1);
  });

  it("keeps the camera continuous across a progressive scene boundary", () => {
    const previousEnd = getFullBleedPresentationState(299, "progressive-frame-sequence", false, 300);
    const nextStart = getFullBleedPresentationState(0, "progressive-frame-sequence", true, 300);
    const nextDissolveEnd = getFullBleedPresentationState(30, "progressive-frame-sequence", true, 300);
    const nativeAtDissolveEnd = getFullBleedPresentationState(30, "progressive-frame-sequence", false, 300);

    expect(nextStart.transform).toBe(previousEnd.transform);
    expect(nextStart.previousTransform).toBe(previousEnd.transform);
    expect(nextDissolveEnd.transform).toBe(nativeAtDissolveEnd.transform);
    expect(Math.abs(scaleOf(nextDissolveEnd.transform) - scaleOf(
      getFullBleedPresentationState(29, "progressive-frame-sequence", true, 300).transform,
    ))).toBeLessThan(0.0002);
  });

  it("storybook starts on its source image and uses a 24-frame subsequent dissolve", () => {
    const first = getFullBleedPresentationState(0, "storybook-full-bleed", false, 300);
    const nextStart = getFullBleedPresentationState(0, "storybook-full-bleed", true, 300);
    const nextEnd = getFullBleedPresentationState(24, "storybook-full-bleed", true, 300);

    expect(first.dissolveFrames).toBe(24);
    expect(first.incomingOpacity).toBe(1);
    expect(nextStart.incomingOpacity).toBe(0);
    expect(nextEnd.incomingOpacity).toBe(1);
  });

  it("keeps the camera continuous across a storybook scene boundary", () => {
    const previousEnd = getFullBleedPresentationState(299, "storybook-full-bleed", false, 300);
    const nextStart = getFullBleedPresentationState(0, "storybook-full-bleed", true, 300);
    const nextDissolveEnd = getFullBleedPresentationState(24, "storybook-full-bleed", true, 300);
    const nativeAtDissolveEnd = getFullBleedPresentationState(24, "storybook-full-bleed", false, 300);

    expect(nextStart.transform).toBe(previousEnd.transform);
    expect(nextStart.previousTransform).toBe(previousEnd.transform);
    expect(nextDissolveEnd.transform).toBe(nativeAtDissolveEnd.transform);
    expect(Math.abs(scaleOf(nextDissolveEnd.transform) - scaleOf(
      getFullBleedPresentationState(23, "storybook-full-bleed", true, 300).transform,
    ))).toBeLessThan(0.0002);
  });
});
