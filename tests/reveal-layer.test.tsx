import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { getCompletionVisualState, RevealLayer } from "../src/scene/RevealLayer";
import { SceneSchema } from "../src/schema";

describe("RevealLayer develop", () => {
  it("완성 전후에 mask와 직접 image를 계속 마운트해 SVG paint 경로를 안정화한다", () => {
    const scene = SceneSchema.parse({
      id: "rgba-pen",
      durationInFrames: 300,
      developFrames: 8,
      edgeFeather: 1,
      faint: 1,
    });

    const renderAt = (frame: number) => renderToStaticMarkup(
      <RevealLayer
        scene={scene}
        image="rgba-pen.png"
        strokes={[]}
        penInvisibleAfter={113}
        routesDuration={300}
        frame={frame}
        drawFrame={frame}
        W={1920}
        H={1080}
      />,
    );
    const before = renderAt(120);
    const complete = renderAt(121);

    // defs의 SVG pattern image + frame 0부터 상시 마운트되는 Remotion HTML Img
    expect(before.match(/<image/g)).toHaveLength(1);
    expect(complete.match(/<image/g)).toHaveLength(1);
    expect(before.match(/<img/g)).toHaveLength(1);
    expect(complete.match(/<img/g)).toHaveLength(1);
    expect(before).toContain("<mask");
    expect(complete).toContain("<mask");
    expect(complete).toMatch(/<img[^>]+opacity:1/);
    expect(complete).toMatch(/<rect[^>]+opacity="0"/);
  });

  it("masked-hold는 완성 시점에도 단일 마스크 이미지만 유지한다", () => {
    const scene = SceneSchema.parse({
      id: "pen-no-popup",
      durationInFrames: 300,
      completionMode: "masked-hold",
      edgeFeather: 1,
      faint: 1,
    });
    const markup = renderToStaticMarkup(
      <RevealLayer
        scene={scene}
        image="rgba-pen.png"
        strokes={[]}
        penInvisibleAfter={113}
        routesDuration={300}
        frame={117}
        drawFrame={117}
        W={1920}
        H={1080}
      />,
    );

    expect(markup).toMatch(/<rect[^>]+mask="url\(#fm-[^"]+\)"[^>]+opacity="1"/);
    expect(markup).toMatch(/<img[^>]+opacity:0/);
  });

  it("integrated-develop는 같은 마스크에서 누락 영역을 채우고 색감을 강화한다", () => {
    const scene = SceneSchema.parse({
      id: "pen-integrated-final",
      durationInFrames: 300,
      completionMode: "integrated-develop",
      developFrames: 8,
      colorSettleFrames: 18,
      edgeFeather: 1,
      faint: 0.78,
    });
    const renderAt = (frame: number) => renderToStaticMarkup(
      <RevealLayer
        scene={scene}
        image="rgba-pen.png"
        strokes={[]}
        penInvisibleAfter={113}
        routesDuration={300}
        frame={frame}
        drawFrame={frame}
        W={1920}
        H={1080}
      />,
    );

    const filling = renderAt(117);
    const complete = renderAt(121);
    const colored = renderAt(139);
    expect(filling).toMatch(/<mask[^>]*>[\s\S]*<rect[^>]+fill="#fff"[^>]+opacity="0.5"/);
    // 누락 영역을 채우는 동안 이미 그린 영역의 opacity는 0.78로 고정된다.
    expect(filling).toMatch(/<rect[^>]+mask="url\(#fm-[^"]+\)"[^>]+opacity="0.78"/);
    expect(complete).toMatch(/<rect[^>]+mask="url\(#fm-[^"]+\)"[^>]+opacity="0.78"/);
    expect(colored).toContain("saturate(1.12)");
    expect(colored).toContain("contrast(1)");
    expect(colored).toContain("brightness(1)");
    expect(colored).toMatch(/<img[^>]+opacity:0/);
  });

  it("preserveSourceColor는 완료 프레임에서 원본 채도를 변경하지 않는다", () => {
    const scene = SceneSchema.parse({
      id: "pen-preserve-source",
      durationInFrames: 300,
      completionMode: "integrated-develop",
      developFrames: 8,
      edgeFeather: 1,
      faint: 1,
    });
    const markup = renderToStaticMarkup(
      <RevealLayer
        scene={scene}
        image="source.png"
        strokes={[]}
        penInvisibleAfter={240}
        routesDuration={300}
        frame={270}
        drawFrame={270}
        W={1920}
        H={1080}
        preserveSourceColor
      />,
    );
    expect(markup).toContain("saturate(1) contrast(1) brightness(1)");
  });

  it("preview underlay는 첫 프레임에 희미한 원본을 표시하고 완성 시 사라진다", () => {
    const scene = SceneSchema.parse({
      id: "pen-opening-preview",
      durationInFrames: 300,
      completionMode: "integrated-develop",
      developFrames: 8,
      edgeFeather: 1,
      faint: 1,
      previewOpacity: 0.32,
    });
    const renderAt = (frame: number) => renderToStaticMarkup(
      <RevealLayer
        scene={scene}
        image="rgba-pen.png"
        strokes={[]}
        penInvisibleAfter={113}
        routesDuration={300}
        frame={frame}
        drawFrame={frame}
        W={1920}
        H={1080}
      />,
    );

    expect(renderAt(0)).toMatch(/<rect[^>]+fill="url\(#brushpat-[^"]+\)"[^>]+opacity="0.32"/);
    expect(renderAt(121)).not.toMatch(/opacity="0.32"/);
  });

  it("첫 씬 흐린 포스터는 routes 이미지와 별도 원본을 prewash로 사용한다", () => {
    const scene = SceneSchema.parse({
      id: "blurred-opening-poster",
      durationInFrames: 300,
      prewashImage: "opening-source.png",
      prewashOpacity: 0.5,
      prewashFrames: 12,
      prewashFadeOutFrames: 12,
      prewashBlur: 12,
    });
    const markup = renderToStaticMarkup(
      <RevealLayer
        scene={scene}
        image="routes-ink.png"
        strokes={[]}
        penInvisibleAfter={113}
        routesDuration={300}
        frame={0}
        drawFrame={-12}
        W={1920}
        H={1080}
      />,
    );

    expect(markup).toContain("opening-source.png");
    expect(markup).toContain('stdDeviation="12"');
    expect(markup).toMatch(/<rect[^>]+fill="url\(#prewashpat-[^"]+\)"[^>]+opacity="0.5"/);
  });

  it("integrated 완료 상태는 밝기·opacity 역전 없이 채도만 단조 증가한다", () => {
    const scene = SceneSchema.parse({
      id: "brush-monotonic-settle",
      durationInFrames: 300,
      completionMode: "integrated-develop",
      developFrames: 36,
      colorSettleFrames: 18,
      faint: 0.88,
    });
    const strokes = [{
      id: "s1", kind: "seal" as const, width: 40, start: 100, end: 206,
      points: [[0, 0], [100, 100]] as [number, number][],
    }];
    const states = Array.from({length: 55}, (_, i) => getCompletionVisualState({
      scene,
      strokes,
      penInvisibleAfter: 232,
      routesDuration: 300,
      drawFrame: 206 + i,
    }));
    expect(states.every((s) => s.brightness === 1 && s.contrast === 1)).toBe(true);
    expect(states.every((s) => s.revealOpacity === 0.88)).toBe(true);
    for (let i = 1; i < states.length; i++) {
      expect(states[i].developOpacity).toBeGreaterThanOrEqual(states[i - 1].developOpacity);
      expect(states[i].saturation).toBeGreaterThanOrEqual(states[i - 1].saturation);
    }
    expect(states.at(-1)?.saturation).toBeCloseTo(1.12, 6);
  });

  it("0프레임 develop/settle도 NaN 없이 즉시 완료된다", () => {
    const scene = SceneSchema.parse({
      id: "zero-duration-completion",
      durationInFrames: 120,
      completionMode: "integrated-develop",
      developFrames: 0,
      colorSettleFrames: 0,
      faint: 0.88,
    });
    const state = getCompletionVisualState({
      scene, strokes: [], penInvisibleAfter: 80, routesDuration: 120, drawFrame: 80,
    });
    expect(state.developOpacity).toBe(1);
    expect(state.colorProgress).toBe(1);
    expect(Number.isFinite(state.saturation)).toBe(true);
  });
});
