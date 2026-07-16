# 용어 사전 — 일반어 ↔ 전문 용어 ↔ v1 시스템 실체

브리프를 쓸 때 이 표의 "전문 용어"를 사용하고, yaml/props 초안에는 "v1 필드"를 사용한다.
권장 범위는 실제 프로젝트 1,500+ 씬의 사용 분포 실측값이다.

## 1. 시각 · 애니메이션 연출

| 전문 용어 | 뜻 | v1 실체 | 실측 권장 범위 |
|---|---|---|---|
| Brush Drawing (붓 드로잉 리빌) | 붓이 지나간 자리만 배경 그림이 연하게 드러나는 마스크 애니메이션 | RevealLayer + `routes.json`의 strokes | — |
| Contour Route (윤곽 경로) | 붓이 따라갈 이동 좌표 집합 — 이미지 경계 추적(contour) + 커버리지 보장 밴드(seal) | `brushvid.routes`가 생성하는 `routes.json` `strokes[]` | 커버리지 ≥95% 게이트 |
| Faint (수묵 농도) | 그리는 중 드러나는 그림의 옅은 불투명도 — 낮을수록 은은한 수묵 느낌 | `scenes[].faint` | 0.38~0.76, 중앙값 **0.72** (스키마 기본 0.6) |
| Develop (발현) | 드로잉 완료 후 전체 그림이 또렷하게 페이드인 되는 2단계 | `developFrames` | 16~54f, 중앙값 **18** |
| Linear Draw (등속 드로잉) | 이징 없이 일정한 속도로 긋기 — 명상적·차분한 붓 | `linearDraw: true` | 실전 99%가 true |
| Prewash (프리워시) | 씬 도입에 흐린 전체 그림을 잠깐 비춰 "빈 화면"을 가리는 예고 연출 | `prewashOpacity/Frames/HoldFrames/Blur` | **첫 씬 전용 관행**. opacity 0.5~1.0, frames ≤48, blur 7~16 |
| Outro Wash (아웃트로 워시) | 씬 끝을 순백 도화지로 수렴시키는 dissolve — 씬 전환의 하드컷 방지 | `outroFadeFrames/WashOpacity/Blur` | frames 14~90 중앙값 **18**, washOpacity **0.9**, blur 1.2~1.4 (강하면 8) |
| Edge Feather (에지 페더) | 리빌 경계만 붓 질감처럼 부드럽게 — 내용은 선명 유지 | `edgeFeather` | 10~14, 중앙값 **12** |
| Brush Dynamics (붓 다이내믹스) | 스트로크의 속도·굵기·흔들림·순서를 seed 기반으로 변주 | `brushDynamics{...}` | 아래 intent-map 참조 |
| Drawing Phases (드로잉 페이즈) | 펜 외곽선과 브러시 채색을 독립 routes·커서로 이어 붙이는 2단계 | `drawingPhases[outline, paint]` / `drawing.profile: pen-brush` | outline 38%, handoff 8f, paint 88% |
| Natural Effects (자연 파티클) | 완성 그림 위에 은은히 떠다니는 기후·광원 레이어 | `naturalEffects.kind` 6종: mist(안개, 최다 사용)·forestDust(빛 먼지)·streamSparkle(물빛)·meadowWind(바람 선)·sunsetGlow(노을)·starTwinkle(별빛) | opacity 0.02~0.058, 중앙값 **0.03** (아주 은은하게) |
| Parallax (패럴랙스) | develop 후 그림이 미세하게 확대·부유하는 생동감 | `naturalEffects.parallaxScale > 1` | ≤1.03 |
| Top Title (상단 타이틀) | 골드 kicker + 제목, 첫 단어 인상색 강조 | `topTitle{...}` — [brush-video의 title-guide](../../brush-video/references/title-guide.md) | fontSize 42~56 중앙값 42, enterAt 8~20 |
| Cue (자막 큐) | frame 단위 자막 구간 + 단어 하이라이트 | `cues[{text, from, to}]` | 자막 bottom 30~250 중앙값 42, fontSize 30 |
| Widget (카드 위젯) | 여백에 얹는 화이트 카드 15종 | `widgets[]` — [widget-catalog](../../brush-video/references/widget-catalog.md) | 타이틀 있으면 y ≥ 230 |

## 2. Camera Prompt Interpreter

| 전문 용어 | 뜻 | 현재 계약 |
|---|---|---|
| Camera Prompt Interpreter | 일상적인 카메라 표현을 canonical 기법·슬롯·한/영 prompt·negative·호환성으로 변환 | [공통 가이드](../../_shared/references/camera-prompt-guide.md) |
| Canonical Technique | 번호·표기가 달라도 하나로 유지되는 전문 기법 ID. 01~36, 46의 37개 | [공통 카탈로그](../../_shared/references/camera-prompt-catalog.json) |
| Legacy Alias | 중복된 37~45번을 28~36번으로 되돌리는 호환 번호 | technique count에 포함하지 않음 |
| Camera Prompt Pack | 연출 브리프에만 들어가는 구조화된 카메라 해석 결과 | `project.yaml`의 `camera:`/`cameraMotion:` 필드가 아님 |
| Zoom | 카메라 위치는 그대로 두고 렌즈 화각을 바꾸는 확대·축소 | 정지 이미지 2D 변환으로 표현 가능 여부를 compatibility로 표시 |
| Push/Dolly | 카메라 자체가 공간 안에서 전진·후진해 원근 관계가 변함 | true 이동은 정지 Remotion에서 `external-required`일 수 있음 |
| Arc | 피사체 주변의 제한된 호 구간을 이동 | 완전 회전 Orbit과 구분 |
| Orbit | 위에서 본 시계/반시계 기준으로 피사체를 중심 삼아 회전 | 방향·거리·높이를 명시 |
| Compatibility | 타깃별 실행 수준 | `supported`, `simulated`, `composition-only`, `external-required`, `not-applicable` |
| Subject Lock | 이동 중에도 피사체나 초점점을 같은 화면 기준에 유지 | 인물 identity나 제품 shape 보존과 함께 사용 |
| Screen Continuity | 이전 씬의 이동 방향·축·가림·빛을 다음 씬 시작과 연결 | 휩팬·오브젝트 통과 등 transition에 필수 |

`parallax`는 정지 레이어의 상대 이동으로 깊이를 근사하는 기존 합성 효과다. true arc/orbit/tracking의
동의어가 아니다. 상세 표현 매핑은 [camera-intent-map](camera-intent-map.md)을 사용한다.

## 3. 청각 · 오디오

| 전문 용어 | 뜻 | v1 실체 | 비고 |
|---|---|---|---|
| Waveform Synthesis (파형 합성) | 녹음 파일 없이 코드로 주파수를 변조해 소리를 무에서 합성 | `brushvid.audio.synth_ambient_bgm()` — 48kHz 스테레오, 시드 결정적, 임의 길이 | 저작권 프리 |
| Piano Pad (피아노 패드) | 잔잔한 펠트 피아노 아르페지오 + 패드 + 벨 — 힐링 BGM 뼈대 | 위 함수의 현재 유일 프리셋 | — |
| Ambience (환경음) | 빗소리·장작·시냇물 등 공간 백색소음 | **확장 후보 — v1 미구현.** 요청 시 "합성 BGM 대체 + 추후 확장" 안내 | 구 시스템에만 존재 |
| Cross-Fade (크로스페이드) | 볼륨 곡선을 겹쳐 소리를 부드럽게 전환 | `bgm.mode: playlist`, `playlist.crossfadeSec` | 로컬 등록 음원 2~3곡 |
| Ducking (덕킹) | 음성이 나올 때 BGM을 자동 감쇄 | `bgm.ducking{amountDb,attackMs,releaseMs}` | 내레이션 BGM 기본 활성 |
| TTS Narration (합성 더빙) | 자막/대본 텍스트를 선택한 로컬 TTS 엔진으로 문장별 합성 — 음성 길이가 타이밍의 시계 | `input.tts{engine, voice, speed, pauseMs}`; Supertonic F1~F5/M1~M5 호환 | 엔진별 AI 생성 고지·voice manifest 필수 |
| STT (전사) | 더빙 음성 → whisper(small·ko) → SRT | `input.audio`만 제공 시 자동 | — |

## 4. 파이프라인 · 개발

| 전문 용어 | 뜻 | v1 실체 |
|---|---|---|
| Render Props (렌더 설계도) | Remotion에 주입하는 씬·연출·오디오 메타데이터 JSON | `data/{pid}/props.json` — **Zod 스키마 v1(`src/schema.ts`)이 유일한 정의** |
| Orchestrator (오케스트레이터) | 전 단계(배경→routes→props→렌더→mux→QA)를 일괄 지휘 | **`bin/build.py`** (10 스테이지, 캐시 + `--from` 재개) |
| Paper-Margin Cleaning (종이색 키잉) | 종이에 가까운 픽셀을 paper 색으로 치환 — 빈 여백이 리빌되지 않게 | `brushvid.background.clean()` |
| Golden Gate (골든 게이트) | 기준 스틸과의 픽셀 diff ≤2% 회귀 검증 | `tests/golden/diff.py` |
| Capture Manifest (QA 계약) | 씬별 스틸 + 메타 — 리뷰 루프의 입력 | `bin/qa.py` → `data/{pid}/qa/capture-manifest.json` |

> ⚠️ 구 시스템 용어 주의: `scene-XX.routes.json`, `build-shorts-1000s.py`, `render-props-1000s.json` 등은
> 폐기된 new-video-gen 세대의 이름이다. 사용자가 이 이름을 써도 위 v1 실체로 번역해서 답한다.
