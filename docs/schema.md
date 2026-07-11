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
- 리빌 튜닝(기본값은 스키마에 단일 정의): `faint(0.6)`, `edgeFeather(0)`, `linearDraw(false)`, `developFrames?`
- prewash 4종 / outro 3종, `brushDynamics{drawSpeedScale·touchScale·touchJitter·pathJitter·randomizeOrder·randomReverse·seed}`
- 연출: `cues[{text,from,to}]`(frame 단위), `topTitle`, `subtitleStyle`, `naturalEffects{kind 6종}`
- `widgets[]` — strict discriminated union 15종 ([위젯 카탈로그](../skill/brush-video/references/widget-catalog.md))

## routes JSON (참조 시스템과 포맷 호환)

```
{
  meta: { image, width, height, fps, durationInFrames,
          drawStart, drawEnd, penInvisibleAfter, routeCount, ... },  // 부가 필드 passthrough
  strokes: [{ id, kind, width, start, end, points: [[x,y],...] }]   // start/end는 소수 프레임
}
```

- 참조 체인: render-props → `scenes[].routes` → routes JSON `meta.image` → 배경 PNG (전부 public/ 기준, staticFile 규약)
- 구세대 필드(top-level meta{}, 레거시 widgets 등)는 **지원하지 않는다** — 옛 프로젝트 재렌더는 new-video-gen에서.
