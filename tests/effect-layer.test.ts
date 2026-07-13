// EffectLayer 가시 창 계약 회귀 테스트.
// 배경: naturalEffects(mist 등)는 opacity 가 낮아(예: 0.035) 표시/소멸이 골든 픽셀 diff(2% 임계)로
// 감지되지 않는다. on/off 램프 공식이 바뀌면 이펙트가 조용히 전 프레임 사라질 수 있으므로
// (FIELD-LOG 2026-07-13) 그 계약을 여기서 고정해 무의식적 변경을 잡는다.
import { describe, expect, it } from "vitest";
import { EFFECT_RAMP_UP, effectWindow } from "../src/scene/EffectLayer";

describe("EffectLayer 가시 창 계약", () => {
  it("램프 상수와 off 창 종점이 고정 계약을 따른다", () => {
    const w = effectWindow(236, 300);
    expect(EFFECT_RAMP_UP).toBe(24);
    expect(w.onStart).toBe(236);
    expect(w.onFull).toBe(236 + 24);
    expect(w.offStart).toBe(300 - 36); // 264
    expect(w.offEnd).toBe(300 - 18); // 282
  });

  it("onStart < offEnd 이면 이펙트가 보이는 창이 존재한다 (건강한 케이스)", () => {
    expect(effectWindow(236, 300).hasVisibleWindow).toBe(true); // 236 < 282
  });

  it("golden-multi mist 타이밍(start=292, routesDuration=300)은 창이 비어 미표시 — 현재 의도된 계약", () => {
    // develop 모드: penInvisibleAfter 228 + developFrames 20 → developEnd 248,
    // colorSettleEnd 248 + colorSettleFrames 36 = 284, EffectLayer start = 284 + 8 = 292.
    // 이는 off 종점(282)보다 뒤라 이펙트가 표시되지 않는다. 이펙트를 다시 보이게 하려면
    // 이 테스트가 의도적으로 실패해야 하며(계약 변경 신호), 그때 값을 갱신한다.
    expect(effectWindow(292, 300).hasVisibleWindow).toBe(false); // 292 >= 282
  });
});
