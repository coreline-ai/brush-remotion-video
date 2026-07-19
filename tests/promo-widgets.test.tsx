// 프로모 위젯 P1 계약 테스트 — registry 등록·placeholder 안전·스키마 strict·값 애니메이션 결정성.
// dev-plan/implement_20260718_212631.md Phase 1.
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import catalog from "../assets/promo-widgets/catalog.json";
import { GALLERY_DEMO_WIDGETS, GALLERY_PAGES, PromoWidgetGallery } from "../src/promo/PromoWidgetGallery";
import { countUpValue } from "../src/promo/bodies/CountUp";
import { gaugeState } from "../src/promo/bodies/Gauge";
import { litCount } from "../src/promo/bodies/HeatmapGrid";
import { rowAppear } from "../src/promo/bodies/Leaderboard";
import { marqueeOffset } from "../src/promo/bodies/Marquee";
import { flapChar } from "../src/promo/bodies/SplitFlap";
import { statBarFill } from "../src/promo/bodies/StatBar";
import { PROMO_WIDGET_REGISTRY, PromoPlaceholderBody, getPromoWidgetBody } from "../src/promo/registry";
import { PromoGalleryPropsSchema, PromoWidgetSchema, type CountUpWidget, type GaugeWidget, type LeaderboardWidget, type StatBarWidget } from "../src/promo/schema";
import { normalizeRatio, promoProgress } from "../src/promo/shared";

describe("promo widget registry", () => {
  it("registry id 집합 = catalog id 집합 (단일 근원 3중 정합의 vitest 축)", () => {
    const catalogIds = catalog.widgets.map((w) => w.id).sort();
    expect(Object.keys(PROMO_WIDGET_REGISTRY).sort()).toEqual(catalogIds);
    expect(catalogIds).toHaveLength(33);
  });

  it("미등록 타입 조회 → placeholder + 경고 (크래시 금지)", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    expect(getPromoWidgetBody("hologram")).toBe(PromoPlaceholderBody);
    expect(warn).toHaveBeenCalledOnce();
    warn.mockRestore();
  });
});

describe("PromoWidgetSchema (strict union)", () => {
  const base = { x: 100, y: 100, w: 400, h: 300 };

  it("gauge parse 통과 + 기본값(kind=needle, min=0) 채움", () => {
    const r = PromoWidgetSchema.parse({ type: "gauge", ...base, value: 2.8, max: 3 });
    expect(r.type === "gauge" && r.kind).toBe("needle");
    expect(r.type === "gauge" && r.min).toBe(0);
  });

  it("타입 전용 필드 혼입 → parse 거부 (countUp에 gauge 전용 ticks)", () => {
    const r = PromoWidgetSchema.safeParse({ type: "countUp", ...base, to: 6.3, ticks: 24 });
    expect(r.success).toBe(false);
  });

  it("스키마에 없는 타입은 거부된다", () => {
    expect(PromoWidgetSchema.safeParse({ type: "hologram", ...base }).success).toBe(false);
  });

  it("leaderboard rows는 최소 1행", () => {
    expect(PromoWidgetSchema.safeParse({ type: "leaderboard", ...base, rows: [] }).success).toBe(false);
  });

  it("갤러리 데모 위젯 전량이 스키마 parse를 통과한다", () => {
    for (const w of GALLERY_DEMO_WIDGETS) {
      expect(PromoWidgetSchema.safeParse(w).success).toBe(true);
    }
  });

  it("갤러리 페이지: 모든 페이지가 비어있지 않고, flat = 전량 목록", () => {
    expect(GALLERY_PAGES.length).toBeGreaterThanOrEqual(5);
    for (const page of GALLERY_PAGES) expect(page.length).toBeGreaterThan(0);
    expect(GALLERY_PAGES.flat()).toEqual(GALLERY_DEMO_WIDGETS);
  });

  it("registry 전 타입이 카탈로그 demo로 최소 1회 시연된다", () => {
    const demoTypes = new Set(GALLERY_DEMO_WIDGETS.map((w) => w.type));
    for (const id of Object.keys(PROMO_WIDGET_REGISTRY)) expect(demoTypes.has(id as never)).toBe(true);
  });
});

describe("값 애니메이션 (결정성·경계값)", () => {
  it("promoProgress: enterAt 이전 0, 완료 후 1, 구간 내 단조 증가", () => {
    expect(promoProgress(0, 10, 20)).toBe(0);
    expect(promoProgress(40, 10, 20)).toBe(1);
    let prev = -1;
    for (let f = 10; f <= 30; f++) {
      const p = promoProgress(f, 10, 20);
      expect(p).toBeGreaterThanOrEqual(prev);
      prev = p;
    }
  });

  it("normalizeRatio: 범위 밖 클램프 + max<=min 안전(0)", () => {
    expect(normalizeRatio(150, 0, 100)).toBe(1);
    expect(normalizeRatio(-5, 0, 100)).toBe(0);
    expect(normalizeRatio(50, 100, 100)).toBe(0);
    expect(normalizeRatio(Number.NaN, 0, 100)).toBe(0);
  });

  it("gaugeState: value>max여도 ratio≤1, 스윕 완료 시 표시값=클램프된 값", () => {
    const w = PromoWidgetSchema.parse({ type: "gauge", x: 0, y: 0, w: 400, h: 300, value: 120, max: 100, sweepFrames: 30 }) as GaugeWidget;
    const done = gaugeState(w, 100);
    expect(done.ratio).toBe(1);
    expect(done.shownValue).toBe(100);
    expect(gaugeState(w, 0).ratio).toBe(0);
  });

  it("statBarFill: fillFrames 경과 후 value/max 비율로 정착", () => {
    const w = PromoWidgetSchema.parse({ type: "statBar", x: 0, y: 0, w: 800, h: 130, value: 50, max: 100, fillFrames: 30 }) as StatBarWidget;
    expect(statBarFill(w, 0)).toBe(0);
    expect(statBarFill(w, 100)).toBeCloseTo(0.5, 5);
  });

  it("countUpValue: from→to 단조 진행, from==to면 상수", () => {
    const w = PromoWidgetSchema.parse({ type: "countUp", x: 0, y: 0, w: 700, h: 220, from: 2.1, to: 2.8, countFrames: 24 }) as CountUpWidget;
    expect(countUpValue(w, 0)).toBeCloseTo(2.1, 5);
    expect(countUpValue(w, 60)).toBeCloseTo(2.8, 5);
    const flat = PromoWidgetSchema.parse({ type: "countUp", x: 0, y: 0, w: 700, h: 220, from: 5, to: 5 }) as CountUpWidget;
    expect(countUpValue(flat, 0)).toBe(5);
    expect(countUpValue(flat, 99)).toBe(5);
  });

  it("rowAppear: 행 index별 stagger — 뒤 행은 같은 프레임에 덜 나타난다", () => {
    const w = PromoWidgetSchema.parse({
      type: "leaderboard", x: 0, y: 0, w: 560, h: 300, populateFrames: 8,
      rows: [{ name: "A", score: 1 }, { name: "B", score: 2 }, { name: "C", score: 3 }],
    }) as LeaderboardWidget;
    expect(rowAppear(w, 6, 0)).toBeGreaterThan(rowAppear(w, 6, 1));
    expect(rowAppear(w, 6, 1)).toBeGreaterThanOrEqual(rowAppear(w, 6, 2));
  });

  it("litCount: lit이 총 셀 수를 넘어도 총 셀 수로 클램프", () => {
    const w = PromoWidgetSchema.parse({ type: "heatmapGrid", x: 0, y: 0, w: 480, h: 360, cols: 3, rows: 3, lit: 99, litFrames: 10 }) as never;
    expect(litCount(w, 999)).toBe(9);
    expect(litCount(w, 0)).toBe(0);
  });

  it("flapChar: 정착 프레임 이후 목표 글자로 고정, 공백은 항상 공백", () => {
    const w = PromoWidgetSchema.parse({ type: "splitFlap", x: 0, y: 0, w: 560, h: 160, text: "AB C", staggerFrames: 4, flipFrames: 16 }) as never;
    expect(flapChar(w, 999, 0)).toBe("A");
    expect(flapChar(w, 999, 1)).toBe("B");
    expect(flapChar(w, 999, 2)).toBe(" ");
    expect(flapChar(w, 5, 0)).toMatch(/^[A-Z]$/); // 순환 중에도 항상 대문자 (결정적)
    expect(flapChar(w, 5, 0)).toBe(flapChar(w, 5, 0)); // 같은 프레임 = 같은 문자
  });

  it("marqueeOffset: enterAt 이전 0, 이후 speed 비례 등속", () => {
    const w = PromoWidgetSchema.parse({ type: "marquee", x: 0, y: 0, w: 1920, h: 56, text: "T", enterAt: 10, speed: 3 }) as never;
    expect(marqueeOffset(w, 5)).toBe(0);
    expect(marqueeOffset(w, 20)).toBe(30);
  });
});

describe("PromoWidgetGallery 렌더", () => {
  it("갤러리 props 스키마 parse + 전 위젯 정적 렌더가 크래시 없이 데모 텍스트를 포함한다", () => {
    const props = PromoGalleryPropsSchema.parse({ pages: GALLERY_PAGES });
    // useCurrentFrame은 컴포지션 밖에서 못 쓰므로 프레임 주입 대신 셸/바디 조합을 정적 마크업으로 검증
    const html = renderToStaticMarkup(
      <div>
        {props.pages.flat().map((w, i) => {
          const Body = getPromoWidgetBody(w.type);
          return <Body key={i} widget={w} frame={999} />;
        })}
      </div>,
    );
    expect(html).toContain("KIMI K3");
    expect(html).toContain("NEW LEADER");
    expect(html).toContain("TRILLION PARAMETERS");
    expect(html).toContain("PARALLEL AGENTS"); // 데이터 패널 페이지
    expect(html).toContain("K3 READY"); // UI 크롬 페이지
    expect(html).toContain("PRESS START"); // 배지 페이지
    expect(typeof PromoWidgetGallery).toBe("function");
  });
});
