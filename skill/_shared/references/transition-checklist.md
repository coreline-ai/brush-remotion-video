# 씬 전환·완성 "번쩍" 공통 체크리스트

씬 전환이나 완성(develop) 순간의 번쩍임·점프컷은 **단일 버그가 아니라 서로 다른 3계층 메커니즘**이
같은 증상으로 보이는 것이다 (실측: FIELD-LOG 2026-07-11 city-watercolor 2건 + 2026-07-12 africa-pen-60).
모든 제작 스킬(brush-video·pen-video·shorts-brush·pen-brush-video)은 완성 선언 전에 이 문서의
체크를 통과해야 한다.

## 메커니즘 3종과 처방

| # | 메커니즘 | 증상 | 근본 원인 | 처방 |
|---|---|---|---|---|
| A | **경계 잔상 하드컷** | 매 씬 전환마다 1프레임 점프 (어두운 씬일수록 심함) | 씬은 오버랩 0프레임 버트조인이라 "마지막 outro 프레임 ≡ 빈 종이"가 전제인데, ① `outroWashOpacity < 1.0` 잔상 ② outro 오버레이 자체가 알파 0.96~0.98 그라디언트(순수 불투명 아님) ③ interpolate 끝점(`duration`)과 실제 마지막 프레임(`duration-1`) 불일치로 전제가 깨짐 | `outroWashOpacity 0.9~1.0 + outroFadeFrames ≥ 12`(권장 18). 경계 diff가 여전히 ≥6%면 순백 수렴 1.0. **prewash는 첫 씬 전용** (중간 씬 prewash는 첫 프레임에 즉시 켜져 2차 점프) |
| B | **develop 교차합성 밝기 펄스** | 완성 순간 화면이 밝아졌다 돌아오는 혹(hump) | 같은 이미지를 faint·develop 2레이어로 쌓고 상보 페이드하면 알파 합성은 비가산이라 커버리지가 중간에 꺼짐. 실측 africa-pen-60: 60/60씬 luma +6 혹 | 일반 brush 기본은 `integrated-develop`: 같은 마스크의 누락 영역만 채운 뒤 밝기 1 고정·채도 정착. pen은 승인 프리셋에 따라 `masked-hold`/integrated를 사용한다. legacy develop의 조기 언마운트는 금지한다. |
| C | **병렬 렌더 결손 프레임** | 전환과 무관한 무작위 위치에서 1프레임 종이만 찍힘/요소 소실 | SVG `<image>`는 Remotion delayRender에 안 잡혀 decode 전에 병렬 Chromium이 캡처. 조건부 언마운트로 프레임 간 DOM 교체 시 SVG paint 무효화 | 이미지는 Remotion `<Img>` 사용 또는 명시 `decode()` 완료 후 continueRender. 렌더 중 레이어 조건부 언마운트 금지(DOM 구조 고정) |

## 완성 선언 전 공통 체크

- [ ] `bin/build.py <yaml> --audit` 또는 `bin/audit.py <mp4>` **PASS** — 경계 하드컷(WARN 6% / FAIL 10%)·스파이크(FAIL 2.5%) 자동 검출
- [ ] 씬 경계 프레임 diff가 정상 페이드 수준(<6%)인지 — evidence 스틸을 눈으로 확인
- [ ] props 제공 audit의 `completion-pulse`가 PASS인지 (정상 채움 최대 1.30, WARN>2, FAIL>4 luma)
- [ ] `completion-report.json`의 luma/saturation 방향성과 완료 contact sheet를 확인했는지
- [ ] prewash가 기본 0인지 (명시 사용 시에도 첫 씬만, 중간 씬 금지)
- [ ] `colorSettleEnd + 12f <= outroStart` 시간 계약을 통과했는지
- [ ] props를 손으로 고쳤다면 outro 3종(`outroFadeFrames`/`outroWashOpacity`/`outroBlur`)이 프로파일 프리셋과 정합인지
- [ ] (렌더 코드 수정 시) 동일 프레임 2회 렌더 diff 0% — C계열 비결정 결손 검출

## 원리 한 줄

> 전환을 "오버랩 없는 버트조인 + 씬 내부 outro/develop 연출"로 구성하는 한,
> **알파 합성의 비가산성**(교차 딥)과 **끝점 미도달**(잔상 컷)은 파라미터가 아니라 구조에서 나온다.
> 처방은 그 구조의 전제(마지막 프레임 ≡ 종이, 단일 레이어 완성)를 실제로 성립시키는 것이다.
