// P5 연출 계층 계약 테스트 — 씬 오프셋·전환 창·플래시 커브(계측 스펙)·스키마 strict.
// external_samples/implement_20260718_212631.md Phase 5.
import { describe, expect, it } from "vitest";
import {
  FLASH_PEAK,
  activeSceneIndex,
  cameraTransform,
  flashOpacity,
  sceneFlash,
  sceneLayout,
  sweepX,
  totalDuration,
  transitionProgress,
} from "../src/promo/scene/transitions";
import { heroScale } from "../src/promo/bodies/HeroTitle";
import { sealSlam } from "../src/promo/bodies/SealStamp";
import { PromoSceneSchema, PromoScenePropsSchema, PromoWidgetSchema } from "../src/promo/schema";
import { BRUSH_IN_FRAMES, brushClipPath } from "../src/promo/shared";
import { P, PALETTE_KEYS, PROMO_THEMES, themeStyle } from "../src/promo/tokens";

const scenes = [{ durationInFrames: 90 }, { durationInFrames: 120 }, { durationInFrames: 60 }];

describe("scene layout", () => {
  it("씬 시작/끝 프레임 누적이 정확하다", () => {
    expect(sceneLayout(scenes)).toEqual([
      { start: 0, end: 90 },
      { start: 90, end: 210 },
      { start: 210, end: 270 },
    ]);
    expect(totalDuration(scenes)).toBe(270);
  });

  it("activeSceneIndex: 경계 프레임은 다음 씬, 범위 밖은 마지막 씬 클램프", () => {
    const layout = sceneLayout(scenes);
    expect(activeSceneIndex(layout, 0)).toBe(0);
    expect(activeSceneIndex(layout, 89)).toBe(0);
    expect(activeSceneIndex(layout, 90)).toBe(1);
    expect(activeSceneIndex(layout, 269)).toBe(2);
    expect(activeSceneIndex(layout, 9999)).toBe(2);
  });
});

describe("transition math (원본 계측 스펙)", () => {
  it("transitionProgress: 창 내 0→1, duration 0이면 항상 1", () => {
    expect(transitionProgress(90, 90, 12)).toBe(0);
    expect(transitionProgress(90, 102, 12)).toBe(1);
    expect(transitionProgress(90, 96, 12)).toBeCloseTo(0.5, 5);
    expect(transitionProgress(90, 90, 0)).toBe(1);
  });

  it("flashOpacity: peak 0.5, 상승 1f·감쇠 4f — 원본 스파이크 diff 역산 재보정 스펙", () => {
    expect(FLASH_PEAK).toBe(0.5);
    expect(flashOpacity(10, 10)).toBeCloseTo(FLASH_PEAK, 5);
    expect(flashOpacity(9, 10)).toBe(0); // 상승 1f — 직전 프레임은 0 (프레임간 점프가 원본 스파이크 강도)
    expect(flashOpacity(14, 10)).toBe(0);
    expect(flashOpacity(12, 10)).toBeCloseTo(FLASH_PEAK / 2, 5);
  });

  it("sceneFlash: white-flash 진입 + flashAt 비트의 max 합성 / 기본(none)은 플래시 0", () => {
    const scene = PromoSceneSchema.parse({ durationInFrames: 90, transition: { type: "white-flash" }, flashAt: [30] });
    expect(sceneFlash(scene, 1)).toBeCloseTo(FLASH_PEAK, 5); // 진입 플래시 (opt-in)
    expect(sceneFlash(scene, 30)).toBeCloseTo(FLASH_PEAK, 5); // 내부 비트
    expect(sceneFlash(scene, 60)).toBe(0);
    const quiet = PromoSceneSchema.parse({ durationInFrames: 90 }); // 기본 = 클린 컷, 비트 없음
    expect(sceneFlash(quiet, 1)).toBe(0);
  });

  it("sweepX: 화면 밖에서 밖으로 통과 (-0.08 → 1.08)", () => {
    expect(sweepX(0)).toBeCloseTo(-0.08, 5);
    expect(sweepX(1)).toBeCloseTo(1.08, 5);
  });
});

describe("PromoSceneSchema (strict + 기본값)", () => {
  it("최소 씬 parse — 기본값: glow/blue 무대, 클린 컷(none) 진입 (재분석: 플래시는 opt-in)", () => {
    const s = PromoSceneSchema.parse({ durationInFrames: 90 });
    expect(s.stage).toEqual({ preset: "glow", tint: "blue", intensity: 1 });
    expect(s.transition).toEqual({ type: "none", durationInFrames: 10 });
    expect(s.widgets).toEqual([]);
  });

  it("계약 밖 필드·미지의 preset 거부", () => {
    expect(PromoSceneSchema.safeParse({ durationInFrames: 90, camera: "zoom" }).success).toBe(false);
    expect(PromoSceneSchema.safeParse({ durationInFrames: 90, stage: { preset: "fog" } }).success).toBe(false);
  });

  it("props: scenes 최소 1개", () => {
    expect(PromoScenePropsSchema.safeParse({ scenes: [] }).success).toBe(false);
  });
});

describe("테마 토큰 시스템 (P6-A)", () => {
  it("두 테마의 팔레트 키 집합이 완전 일치한다 (fallback 누수 방지)", () => {
    expect(Object.keys(PROMO_THEMES["gamji-gold"]).sort()).toEqual(Object.keys(PROMO_THEMES["dark-navy"]).sort());
  });

  it("themeStyle: 모든 키가 --pw-* 변수로 주입되고 dark-navy 계측값이 보존된다", () => {
    const navy = themeStyle("dark-navy") as Record<string, string>;
    expect(Object.keys(navy)).toHaveLength(PALETTE_KEYS.length);
    expect(navy["--pw-data"]).toBe("#4a7fff"); // KIMI 계측값 회귀 방어
    expect(navy["--pw-bg"]).toBe("#0a0e1a");
    const gamji = themeStyle("gamji-gold") as Record<string, string>;
    expect(gamji["--pw-data"]).toBe("#dfae4a"); // 금니
    expect(gamji["--pw-cta"]).toBe("#cf4a2f"); // 주사
  });

  it("P 팔레트는 var() 참조 + dark-navy fallback — 테마 미적용 렌더도 기존과 동일", () => {
    expect(P.data).toBe("var(--pw-data, #4a7fff)");
    expect(P.veil).toContain("var(--pw-veil");
  });

  it("scene props: theme 기본값 dark-navy, 미지의 테마 거부", () => {
    const p = PromoScenePropsSchema.parse({ scenes: [{ durationInFrames: 90 }] });
    expect(p.theme).toBe("dark-navy");
    expect(PromoScenePropsSchema.safeParse({ theme: "vaporwave", scenes: [{ durationInFrames: 90 }] }).success).toBe(false);
  });
});

describe("연출 밀도 (P7 — 카메라·무대 강도)", () => {
  it("씬 기본값: camera 고정(none) — 지속 확대/이동은 opt-in, stage.intensity 1", () => {
    const s = PromoSceneSchema.parse({ durationInFrames: 90 });
    expect(s.camera).toEqual({ move: "none", amount: 0.04 });
    expect(s.stage.intensity).toBe(1);
  });

  it("cameraTransform: push-in은 0→amount 단조 스케일, none은 'none'", () => {
    const cam = { move: "push-in" as const, amount: 0.08 };
    expect(cameraTransform(cam, 0, 100)).toBe("scale(1.0000)");
    expect(cameraTransform(cam, 100, 100)).toBe("scale(1.0800)");
    expect(cameraTransform(cam, 50, 100)).toBe("scale(1.0400)");
    expect(cameraTransform({ move: "none", amount: 0.1 }, 50, 100)).toBe("none");
    expect(cameraTransform({ move: "drift-left", amount: 0.05 }, 100, 100)).toContain("translateX(24.0px)");
  });

  it("intensity 경계: 0.2~2 허용, 밖은 거부", () => {
    expect(PromoSceneSchema.safeParse({ durationInFrames: 90, stage: { intensity: 3 } }).success).toBe(false);
    expect(PromoSceneSchema.parse({ durationInFrames: 90, stage: { intensity: 1.6 } }).stage.intensity).toBe(1.6);
  });
});

describe("붓 융합 (P6-B)", () => {
  it("brushClipPath: 진행 중 polygon, 완료(≥1) 시 undefined(클립 해제)", () => {
    expect(brushClipPath(0.5, 7)).toMatch(/^polygon\(/);
    expect(brushClipPath(1)).toBeUndefined();
    expect(brushClipPath(1.5)).toBeUndefined();
    expect(BRUSH_IN_FRAMES).toBeGreaterThan(0);
  });

  it("brushClipPath: 같은 입력 = 같은 polygon (결정성), seed 다르면 모서리 다름", () => {
    expect(brushClipPath(0.4, 3)).toBe(brushClipPath(0.4, 3));
    expect(brushClipPath(0.4, 3)).not.toBe(brushClipPath(0.4, 9));
  });

  it("entrance: 기본 rise, brushIn 허용, 미지 값 거부", () => {
    const base = { x: 0, y: 0, w: 400, h: 300 };
    expect(PromoWidgetSchema.parse({ type: "countUp", ...base, to: 5 }).entrance).toBe("rise");
    expect(PromoWidgetSchema.parse({ type: "countUp", ...base, to: 5, entrance: "brushIn" }).entrance).toBe("brushIn");
    expect(PromoWidgetSchema.safeParse({ type: "countUp", ...base, to: 5, entrance: "teleport" }).success).toBe(false);
  });

  it("무대: hanji·ink-wash preset 허용", () => {
    expect(PromoSceneSchema.parse({ durationInFrames: 90, stage: { preset: "hanji" } }).stage.preset).toBe("hanji");
    expect(PromoSceneSchema.parse({ durationInFrames: 90, stage: { preset: "ink-wash" } }).stage.preset).toBe("ink-wash");
  });

  it("sealSlam: 들었다(2.2) 내리찍고(0.92) 정착(1) — 단조 아님이 정상(눌림 반동)", () => {
    const w = PromoWidgetSchema.parse({ type: "sealStamp", x: 0, y: 0, w: 300, h: 300, enterAt: 10, text: "完", slamFrames: 10 }) as never;
    expect(sealSlam(w, 10)).toBeCloseTo(2.2, 5);
    expect(sealSlam(w, 16)).toBeCloseTo(0.92, 5);
    expect(sealSlam(w, 20)).toBe(1);
    expect(sealSlam(w, 999)).toBe(1);
  });
});

describe("heroTitle (P5-C 키네틱 타이포)", () => {
  it("heroScale: scaleFrom→1 단조 수축, 정착 후 1 고정", () => {
    const w = PromoWidgetSchema.parse({ type: "heroTitle", x: 0, y: 0, w: 1400, h: 480, enterAt: 10, text: "KIMI K3", scaleFrom: 1.5, settleFrames: 6 }) as never;
    expect(heroScale(w, 10)).toBeCloseTo(1.5, 5);
    expect(heroScale(w, 16)).toBe(1);
    expect(heroScale(w, 999)).toBe(1);
    let prev = Infinity;
    for (let f = 10; f <= 16; f++) {
      const s = heroScale(w, f);
      expect(s).toBeLessThanOrEqual(prev);
      prev = s;
    }
  });
});
