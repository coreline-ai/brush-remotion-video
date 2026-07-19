# KIMI K3 프로모 영상 에셋 완벽 재현 제안서

> 근거 분석: [`KakaoTalk_Video_2026-07-18-19-03-47_분석.md`](./KakaoTalk_Video_2026-07-18-19-03-47_분석.md)
> 목표: 원본 영상에서 사용된 **모든 에셋**을 픽셀·모션·오디오 수준까지 재현 가능한 자산으로 재구축
> 전제: 실행 스택은 이 레포(Remotion)로 통일. 붓/펜 파이프라인과 **분리된 신규 라인**으로 설계.

---

## 1. "완벽"의 정의 — 3단계 충실도(Fidelity)

에셋마다 완벽의 의미가 다르므로 3단계로 나눠 목표를 명시한다.

| 등급 | 의미 | 대상 |
|---|---|---|
| **F1 벡터-완전 재현** | 원본과 픽셀/모션이 사실상 구별 불가 (파라메트릭 재생성) | 36개 위젯·타이포·전환·게이지·카운트업 |
| **F2 근사 재현** | 형태·질감·라이팅을 새로 제작, 원본과 "같은 계열"로 인지 | 3D 구체·게임기·파티클·환경광 |
| **F3 대체 제작** | 원본 자산 확보 불가 → 라이선스 클린한 신규 자산으로 대체 | 게임 푸티지·BGM·내레이션 음성 |

> 핵심 원칙: 원본은 참조일 뿐 **원본 픽셀/음원을 추출·재배포하지 않는다.** 모든 산출물은 코드·프롬프트로 재생성한 신규 자산이어야 배포 안전.

---

## 2. 권장 기술 스택

| 레이어 | 도구 | 이유 |
|---|---|---|
| 합성/렌더 | **Remotion** (이 레포) | 프레임 결정성, 코드 기반 재현성, 기존 파이프라인 재사용 |
| 위젯(2D) | **React + SVG + 인라인 모션** (Remotion `interpolate`/`spring`) | 파라메트릭 = F1 달성. 벡터라 해상도 독립 |
| 3D 요소 | **@react-three/fiber + drei** (Remotion Three 통합) | 구체·게임기 F2. 프레임 동기 렌더 |
| 파티클 | R3F points 또는 2D canvas 셰이더 | MoE 필드·파티클 아크 |
| 게임 푸티지 | **대체 제작**(아래 6장) | 원본 추출 불가 → 신규 캡처/생성 |
| 내레이션 | **이 레포 TTS(Supertonic)** | `brush-video` TTS 모드 재사용 |
| BGM | **이 레포 `piano-bgm` 스킬** 또는 라이선스 로컬 BGM | 라이선스 증빙 체계 이미 존재 |
| 최종 검수 | **이 레포 `video-auditor` 스킬** | 하드컷·번쩍·오디오·규격 자동 게이트 |

---

## 3. 에셋 인벤토리 (재현 대상 전량)

| 카테고리 | 항목 수 | 충실도 목표 | 주 제작법 |
|---|---|---|---|
| 데이터 위젯 | 36종 (W1–W36) | F1 | 파라메트릭 SVG 컴포넌트 |
| 3D 오브젝트 | 2 (구체, 게임기) | F2 | R3F |
| 파티클/환경 | 3 (MoE필드, 파티클아크, 라이트빔) | F2 | R3F/셰이더 |
| 게임 푸티지 | 4클립 | F3 | 대체 제작 |
| 타이포/컬러 시스템 | 1 토큰셋 | F1 | 디자인 토큰 JSON |
| 전환 | 4종 | F1 | Remotion 시퀀스 |
| 오디오 | 2 (내레이션, BGM) | F3 | TTS + piano-bgm |

---

## 4. 위젯 라이브러리 설계 (F1 — 최우선)

36개 위젯을 **재사용 파라메트릭 컴포넌트**로 만든다. 각 위젯 = `props`로 값·상태·타이밍을 받는 순수 함수 컴포넌트. 이것이 "완벽 재현"의 핵심 자산.

### 4.1 코어 4종 (ROI 최상 — 먼저 구현)

```ts
// W1 게이지
<Gauge
  kind="needle" | "fill-arc"      // 니들(W1a) / 필-아크(W1b)
  value={2.8} min={0} max={3}
  unit="T" label="OFFICIAL WEIGH-IN"
  ticks={40} goldTail                // 스포크 개수, 골드 테일
  sweepFrames={24} easing="out"      // 스윕 지속·이징
/>

// W2 수평 바
<StatBar
  value={1_000_000} scaleTicks={[100_000, 500_000, 1_000_000]}
  fillColor="#4a7fff" goldLabel="1M TOKENS"
  fillFrames={30}
/>

// W5 리더보드
<Leaderboard
  header="PROGRAM BENCH" rows={[
    {rank:1, name:"KIMI K3", score:77.8, highlight:true},
    {rank:2, name:"GPT-5.6 SOL", score:77.6},
    {rank:3, name:"FABLE 5", score:76.8},
  ]}
  footer="NEW LEADER" reorder                // 순위 리오더 애니메이션
/>

// W8 카운트업
<CountUp from={2.1} to={2.8} suffix="T" rule caption="TRILLION PARAMETERS" frames={24}/>
```

### 4.2 위젯 → 컴포넌트 매핑 (36종 전량)

| 컴포넌트 | 흡수 위젯 | props 핵심 |
|---|---|---|
| `Gauge` | W1a·W1b·W4 | kind, value, ticks, goldTail |
| `StatBar` | W2·W3(mode="vs") | value, scaleTicks, vsBadge |
| `Leaderboard` | W5 | rows, highlight, reorder |
| `RankLadder` | W6 | steps, token, climbTo |
| `NumberLinePlot` | W7 | axis, points[], closingArrow |
| `CountUp` | W8·W9(prefix="×") | from, to, rule, caption |
| `PriceTag` | W10 | value, swing, dropTo |
| `NodeGraph` | W11 | nodes, edges, drawOn |
| `CurvePlot` | W12 | baseline, curve, markers |
| `HeatmapGrid` | W13 | cols, rows, litSequence |
| `ParticleField` | W14 | count, activeCounter |
| `Oscilloscope` | W15 | main, reference |
| `FlowDiagram` | W16 | steps[] |
| `StrataDiagram` | W17 | layers, tunnelDots |
| `LogCard` | W18 | entries, typewriter |
| `Terminal` | W19 | bootLines, prompt, cursor |
| `ChecklistPanel` | W20 | items, statusFlags |
| `CalloutPanel` | W21 | target, items[], connectors |
| `PlatformSelector` | W22 | primary, options[] |
| `Kicker` | W23 | text, tick, align |
| `PillBadge` | W24 | text, icon |
| `SportsCallout` | W25 | type: vs/winner/doublekill/bonus/upgraded |
| `Marquee` | W26 | text, speed |
| `SplitFlap` | W27 | text |
| `TimelineScrubber` | W28 | from, to |
| `FrameBrackets` | W29 | corners, reticle |
| `GameHUD` | W30 | live, minimap, counters, healthBars |
| `Subtitle` | W31 | text (전역 고정 슬롯) |
| `ChevronBadges` | W32 | items[] |
| `DateFlip` | W33 | date, label |
| `TicketProp` | W34 | tier, upgraded |
| `Orb` | W35 | glow, particles (R3F 연동) |
| `LogoLockup` | W36 | wordmark, bunting, white |

→ **28개 컴포넌트로 36개 위젯 전량 커버.** (일부는 mode/kind prop으로 통합)

### 4.3 디자인 토큰 (모든 컴포넌트가 상속)

```json
{
  "color": {
    "data": "#4a7fff", "cta": "#f5b73c", "rival": "#e2483d",
    "bg": "#0a0e1a", "text": "#ffffff", "muted": "rgba(255,255,255,.6)"
  },
  "radius": { "sm": 4, "md": 8 },
  "stroke": { "hairline": 1 },
  "type": {
    "hero": "condensed-bold", "label": "mono-uppercase-tracked",
    "value": "tabular-right"
  },
  "motion": { "ease": "cubic-bezier(.16,1,.3,1)", "settleFrames": 12 },
  "slots": { "kicker": {"x":"7%","y":"5%"}, "subtitle": {"y":"92%","align":"center"} }
}
```

---

## 5. 3D·파티클 에셋 (F2)

| 에셋 | 방법 | 세부 |
|---|---|---|
| **발광 구체(W35)** | R3F Sphere + emissive + bloom(postprocessing) | 프레넬 림라이트, 하단 파티클 dust, 오프닝/엔딩 북엔드 공유 |
| **게임기(W20)** | R3F glTF 모델 + 스크린 텍스처(비디오/캔버스) | 모델은 **자체 제작 glTF**(라이선스 클린). 화면에 위젯 렌더를 텍스처로 투영 |
| **MoE 파티클 필드(W14)** | R3F `<points>` + 셰이더 활성화 | 896개 인스턴스, 활성 카운터와 동기 발광 |
| **라이트빔 스윕(전환)** | 2D 그라디언트 플레인 + additive blend | 수직 빔 스와이프 |

> glTF 3D 모델은 원본에서 추출 불가 → **신규 모델링 또는 CC0 에셋**으로 제작해야 배포 안전(F2).

---

## 6. 게임 푸티지 (F3 — 가장 어려운 파트, 정직한 대안)

원본의 4개 게임 클립(풍선 FPS·무협 RPG·콜로세움·격투)은 **추출·재사용 불가**. 3가지 대체 경로를 제안하며, 목적에 따라 선택:

| 옵션 | 방법 | 충실도 | 리스크 |
|---|---|---|---|
| **6-A 자체 3D 씬 캡처** | R3F/게임엔진으로 유사 씬 제작 후 화면 녹화 | 중~상 | 제작 공수 큼 |
| **6-B 라이선스 스톡** | CC0/구매 게임플레이 스톡 클립 | 중 | 정확히 일치 어려움 |
| **6-C 스타일라이즈드 플레이스홀더** | 로우폴리 프리뷰 + 강한 HUD 오버레이(W30)로 "게임"임을 기표화 | 하 | 원본과 다름 명시 필요 |

**권장**: 6-C(빠른 프로토) → 필요 시 6-A(고품질). 어느 경우든 HUD 오버레이(W30)가 "게임 데모" 인상을 만들어 클립 자체의 완성도 요구를 낮춘다.

---

## 7. 오디오 (F3 — 이 레포 스킬 재사용)

| 트랙 | 방법 | 근거 |
|---|---|---|
| **내레이션** | 이 레포 **TTS(Supertonic)** — 자막 대본을 씬 타이밍에 맞춰 합성 | `brush-video` TTS 모드가 이미 SRT→음성 지원 |
| **BGM** | 이 레포 **`piano-bgm` 스킬**(cinematic-piano/game-bgm-piano preset) 또는 라이선스 로컬 BGM | 라이선스 증빙(`assets/bgm/evidence/`) 체계 존재 |
| **믹스** | 내레이션 우선, BGM 덕킹, 영상 믹스 −16~−18 LUFS(원본 매칭) 또는 −14(유튜브) | 원본 −18 LUFS 계측값 기준 |

---

## 8. 폴더 구조 제안

```text
projects/kimi-k3-promo/           # 신규 제품 라인 (붓/펜과 분리)
  project.yaml                    # 씬 타이밍·자막·에셋 바인딩
  design-tokens.json              # 4.3 토큰
  scenes/                         # 씬별 구성(30씬)
  assets/
    3d/ (orb.gltf, console.gltf)
    footage/ (game-01..04.mp4)    # F3 대체 클립
    audio/ (narration.wav, bgm.wav)
src/kimi/                         # 신규 Remotion 컴포넌트 라이브러리
  widgets/ (Gauge.tsx, StatBar.tsx, Leaderboard.tsx, ... 28개)
  three/ (Orb.tsx, Console.tsx, ParticleField.tsx)
  transitions/ (LightSweep.tsx, WhiteFlash.tsx, PushIn.tsx)
  KimiPromo.tsx                   # 루트 컴포지션
```

---

## 9. 단계별 빌드 플랜 (Phased)

| Phase | 산출물 | 완료 기준(self-test) |
|---|---|---|
| **P0 기반** | 디자인 토큰 + Remotion 컴포지션 스켈레톤 + Kicker/Subtitle 전역 슬롯 | 빈 30씬 타임라인이 규격(1080p/30 또는 720p/24)으로 렌더 |
| **P1 코어 위젯** | Gauge·StatBar·Leaderboard·CountUp (4.1) | 4개 위젯이 값·스윕·리오더까지 원본과 시각 대조 통과 |
| **P2 전체 위젯** | 나머지 24개 컴포넌트 | 36개 위젯 전량 스토리북 카탈로그화 |
| **P3 3D·파티클** | Orb·Console·ParticleField·LightSweep | 북엔드 구체 + 게임기 인스펙트 씬 렌더 |
| **P4 푸티지·오디오** | 4클립(F3) + TTS 내레이션 + piano-bgm | 오디오 mux, −18 LUFS 매칭 |
| **P5 조립·전환** | 30씬 시퀀싱 + 4전환 + 자막 동기 | 풀 렌더 mp4 산출 |
| **P6 검수** | `video-auditor` 리포트 | 하드컷·번쩍·오디오·규격 PASS |

각 Phase는 독립 렌더 가능하도록 설계 → 중간 산출물로 진척 확인.

---

## 10. 완벽도 QA 게이트

- **시각 대조**: 씬별 원본 정착 프레임 vs 재현 프레임 나란히 비교(이번 분석의 몽타주 방식 재사용)
- **모션 대조**: 카운트업 지속 프레임·게이지 이징 커브를 원본 시간축 프레임과 대조
- **자동 검수**: `video-auditor`로 결함 스캔(exit code 게이트)
- **오디오**: LUFS/True Peak 계측을 원본(−18 LUFS)과 비교

---

## 11. 리스크와 결론

| 리스크 | 대응 |
|---|---|
| 게임 푸티지 원본 확보 불가 | F3 대체 3경로(6장), HUD로 인상 보강 |
| 3D 모델 라이선스 | 자체 제작/CC0로 F2 |
| 폰트 특정 불가 | 유사 콘덴스드/모노 오픈폰트로 근사 |
| 원본 음원 재사용 금지 | TTS+piano-bgm으로 신규 합성 |

**결론**: 전체 에셋의 **약 70%(위젯 36종·타이포·전환·게이지)는 F1(픽셀-완전 재현)이 가능**하며, 이 레포 Remotion 스택으로 파라메트릭 컴포넌트화하면 재사용·수정까지 확보된다. 3D(F2)·게임 푸티지/오디오(F3)는 원본 재사용이 불가하므로 신규 제작으로 "같은 계열"까지 도달한다. **ROI 순서: P1 코어 위젯 4종 → P2 전체 위젯 → P3 3D → P4 푸티지/오디오.**

---

### 다음 액션 제안
이 제안을 실행에 옮긴다면, 먼저 **P0(토큰+스켈레톤) + P1(코어 위젯 4종)** 을 신규 컴포지션으로 프로토타이핑하여 원본 대비 시각 대조를 검증하는 것을 권장한다. 원하시면 P0–P1을 실제 코드로 착수하겠다.
