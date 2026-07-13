import { describe, expect, it } from "vitest";
import { getPenSpriteLayout } from "../src/scene/CursorLayer";
import { BrushSchema } from "../src/schema";

describe("pen cursor asset contract", () => {
  it("kind: pen은 하드코딩 도형 대신 기본 pen.svg를 사용한다", () => {
    const brush = BrushSchema.parse({ kind: "pen", w: 140 });
    const layout = getPenSpriteLayout(brush);

    expect(layout.src).toBe("brush-draw/pen.svg");
    expect(layout.width).toBe(140);
    expect(layout.height).toBeCloseTo(62.222, 3);
    expect(layout.tipx).toBeCloseTo(3.111, 3);
    expect(layout.tipy).toBeCloseTo(31.111, 3);
    expect(layout.rotationOffset).toBe(-132);
  });

  it("프로젝트별 pen 이미지와 앵커 값을 명시하면 그대로 사용한다", () => {
    const brush = BrushSchema.parse({
      kind: "pen",
      src: "custom/pen.png",
      w: 200,
      h: 80,
      tipx: 9,
      tipy: 41,
    });

    expect(getPenSpriteLayout(brush)).toMatchObject({
      src: "custom/pen.png",
      width: 200,
      height: 80,
      tipx: 9,
      tipy: 41,
    });
  });
});
