# 데이터 스키마 (v1)

유일한 정의는 [src/schema.ts](../src/schema.ts). 이 문서는 요약이다.
파이썬은 `npm run export-schema`가 내보낸 `schema/render-props.schema.json`을 **소비만** 한다 (이중 정의 금지).

## render-props (RenderPropsSchema)

```
{
  schemaVersion: 1,               // literal — 누락/불일치 시 parse 거부
  projectId, title?, format(youtube|shorts),
  audio: string|null,             // null = 영상만 렌더 후 ffmpeg mux
  paper: "#fbfaf6",
  brush?: { src, w, h, tipx, tipy, visible, opacity },
  scenes: [Scene, ...]            // 최소 1개
}
```

## Scene

- 식별/길이: `id`, `routes`(routes JSON 경로, 없으면 명시적 에러 렌더), `durationInFrames`
- 리빌 튜닝(스키마 기본 + 프로파일 명시값): `faint`, `edgeFeather`, `linearDraw`, `developFrames`,
  `completionMode(develop|masked-hold|integrated-develop)`, `colorSettleFrames`, `previewOpacity`
- prewash 5종(`Opacity/Frames/HoldFrames/FadeOutFrames/Blur`) / outro 3종,
  `brushDynamics{drawSpeedScale·touchScale·touchJitter·pathJitter·randomizeOrder·randomReverse·seed}`
- 연출: `cues[{text,from,to}]`(frame 단위), `topTitle`, `subtitleStyle`, `naturalEffects{kind 6종}`
- `widgets[]` — strict discriminated union 15종 ([위젯 카탈로그](../skill/brush-video/references/widget-catalog.md))

`drawingPhases`는 선택적 2단계 계약이다. 지정하면 legacy `routes` 대신 사용한다.

```ts
drawingPhases: [
  {kind: "outline", routes, cursor: {kind: "pen"}, zIndex: 20, fadeOutFrom, fadeOutTo},
  {kind: "paint", routes, cursor: {kind: "image", src, w, h, tipx, tipy}, zIndex: 10}
]
```

순서는 `outline → paint` 정확히 2개이며 fade pair와 범위를 Zod가 검증한다.

일반 가로 brush 빌더는 렌더러 default에 의존하지 않고 no-pulse 완료 필드를 props에 명시한다.
routes의 마지막 stroke를 기준으로 `develop → colorSettle → 최소 12f hold → outro`가 겹치면
Python props 단계에서 실패한다. 짧은 씬은 routes를 바꾸지 않고 36/18을 2:1 비율로 최소 12/6까지 축소한다.

## routes JSON (참조 시스템과 포맷 호환)

```
{
  meta: { image, width, height, fps, durationInFrames,
          drawStart, drawEnd, penInvisibleAfter, routeCount, ... },  // 부가 필드 passthrough
  strokes: [{ id, kind, width, start, end, points: [[x,y],...] }]   // start/end는 소수 프레임
}
```

- 참조 체인: render-props → `scenes[].routes` 또는 `drawingPhases[].routes` → routes JSON `meta.image` → PNG (전부 public/ 기준)
- 구세대 필드(top-level meta{}, 레거시 widgets 등)는 **지원하지 않는다** — 옛 프로젝트 재렌더는 new-video-gen에서.

### dark-random-brush routes (runtime key: cosmic-random-brush)

`meta.family: free-random-touch`이면 별도 `RandomTouchRoutesDataSchema`로 검증한다. 기존 2D point
routes 계약을 느슨하게 확장하지 않는다.

v0.2 production routes는 다음 콘텐츠 인식 보조 메타를 추가한다. 기존 v0.1 데모 routes 호환을
위해 schema에서는 optional이지만, 대표 6씬 QA에서는 필수 hard gate다.

- `contentAnalysisVersion: luma-chroma-v1`
- `visibleContentFraction`: alpha·명도·채도 기준 가시 영역 비율
- `visibleContentCoverage`: 가시 영역 중 route mask가 칠한 비율, 6씬 기준 0.985 이상

```ts
{
  meta: {family: "free-random-touch", image, width: 1920, height: 1080,
         fps: 30, durationInFrames: 300, drawStart, drawEnd,
         settleStart, settleEnd, brushInvisibleAfter,
         strokeCount, baseStrokeCount: 36, coverageStrokeCount,
         targetMaskCoverage: 0.991, maskCoverage, brushWidthRange,
         meanCenterJump, maxCenterJump, seed, deterministic: true},
  strokes: [{id, kind: "random-touch", width, start, end, opacity, dryness,
             points: [[x, y, pressure], ...]}]
}
```

붓 폭은 230~365px, 보완 터치는 1~20개, coverage는 0.991 이상이어야 Zod와 QA를 통과한다.

## project.yaml BGM 계약

`bgm`은 렌더 props에 들어가지 않고 `mix` 스테이지가 소비한다. 따라서 `audio`는 계속 `null`로
Remotion을 렌더하고 완성 master WAV를 나중에 mux한다.

```yaml
bgm:
  mode: off | synth | asset | playlist
  assetId: string                  # asset 전용
  sourceStartSec: 0.0              # 원본 앞쪽 무음/프리롤 제거, 0~60초
  playlist:                        # playlist 전용, 2~3개
    assetIds: [string, string]
    crossfadeSec: 3.0              # 0.5~10
  gainDb: 5.0                      # -24~12, 생략 시 음성 없음 5 / 있음 3
  fadeInSec: 1.8                   # 0~10
  fadeOutSec: 2.0                  # 0~10
  ducking:
    enabled: true
    amountDb: 8.0                  # 0~24
    attackMs: 120                  # 1~2000
    releaseMs: 600                 # 10~5000
  licensePolicy: strict | warn
```

블록이 없으면 기존 프로젝트 하위 호환: ambient는 기존 synth, 나머지는 기존 음성만 mux한다.
외부 asset 메타데이터 진실은 `assets/bgm/catalog.json`, 로컬 원본·증빙은 Git 제외된
`local-assets/bgm/<assetId>/`이다.
