import { describe, expect, it, vi } from "vitest";
import { CARD_WIDGET_TYPES, WidgetSchema } from "../src/schema";
import { PlaceholderBody, WIDGET_REGISTRY, getWidgetBody } from "../src/widgets/registry";

const CORE_15 = ["stat", "text", "donut", "bars", ...CARD_WIDGET_TYPES];

describe("widget registry", () => {
  it("TC-5.1: 핵심 15종이 전부 registry에 등록되어 있다", () => {
    expect(Object.keys(WIDGET_REGISTRY).sort()).toEqual([...CORE_15].sort());
    expect(Object.keys(WIDGET_REGISTRY)).toHaveLength(15);
  });

  it("TC-5.E1: 미등록 타입 조회 → placeholder + 경고 (크래시 금지)", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    expect(getWidgetBody("hologram")).toBe(PlaceholderBody);
    expect(warn).toHaveBeenCalledOnce();
    warn.mockRestore();
  });
});

describe("WidgetSchema (strict union)", () => {
  const base = { x: 100, y: 100, w: 340, h: 210, title: "테스트" };

  it("TC-5.2: stat {value:'87%'} parse 통과", () => {
    const r = WidgetSchema.safeParse({ type: "stat", ...base, value: "87%", sub: "만족도" });
    expect(r.success).toBe(true);
  });

  it("TC-5.E2: donut에 bars 전용 필드(values) 혼입 → parse 거부", () => {
    const r = WidgetSchema.safeParse({ type: "donut", ...base, pct: 80, values: [1, 2, 3] });
    expect(r.success).toBe(false);
  });

  it("카드형은 items가 기본 []로 채워진다", () => {
    const r = WidgetSchema.parse({ type: "FlowDiagram", ...base });
    expect("items" in r && r.items).toEqual([]);
  });

  it("스키마에 없는 타입은 거부된다", () => {
    expect(WidgetSchema.safeParse({ type: "hologram", ...base }).success).toBe(false);
  });
});
