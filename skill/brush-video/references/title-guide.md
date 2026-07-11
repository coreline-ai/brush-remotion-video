# 상단 타이틀(topTitle) 가이드

씬당 1개, `scenes[].topTitle`로 정의한다. 유일한 정의는 `src/schema.ts`의 `TopTitleSchema` — 이 문서는 요약이다.
렌더는 TitleLayer(z 23)가 담당: 골드 kicker(좌우 구분선) + 굵은 제목, wash 패널 옵션.

## 필드

| 필드 | 기본값 | 설명 |
|---|---|---|
| `lines[]` | (필수) | 제목 줄들 — 최소 1줄. 줄바꿈은 배열 원소로 |
| `kicker` | 없음 | 상단 소제목 — 대문자·자간 확장, 정렬에 맞는 구분선과 함께 표시 |
| `x` / `y` / `width` | 110 / 74 / 700 | 좌상단 기준 위치·폭 |
| `align` | `left` | left / center / right |
| `enterAt` | 0 | 등장 프레임 — 18f 페이드 + 20f 상승 모션 |
| `accent` | `#b8862f` (골드) | kicker·구분선 색 |
| `firstWordColor` | 없음 | **첫 줄 첫 단어만** 강조색 |
| `fontSize` / `kickerFontSize` | 60 / 20 | 글자 크기 (44/16이 검증된 축소 프리셋) |
| `wash` | false | true면 반투명 화이트 패널 — 배경 그림 위에 얹을 때 가독성 확보 |

## 관행 (검증된 튜닝)

- **firstWordColor는 배경에서 추출한 인상색**을 쓴다 — 파이프라인의 `brushvid.cues.title_color()`가 자동 추출 (도미넌트 채도색 + 가독성 darken)
- 배경 그림과 겹치면 `wash: true`, 빈 여백 위면 wash 없이
- 축소 프리셋 예시 (winter 데모 검증값):

```json
"topTitle": {
  "kicker": "WINTER · GOLDEN",
  "lines": ["눈 얹힌 소나무 가지"],
  "x": 110, "y": 74, "width": 700, "align": "left",
  "enterAt": 12, "accent": "#6b8499", "firstWordColor": "#6b8499",
  "fontSize": 44, "kickerFontSize": 16, "wash": true
}
```

## 배치 규칙 (위젯과의 관계)

- 타이틀 영역은 대략 **y 74 ~ 74+140px** (kicker+제목 1줄, fontSize 44 기준)을 차지한다 —
  **위젯은 이 영역을 침범하면 안 된다** (예: 타이틀이 있으면 위젯 첫 줄 y ≥ 230 권장)
- 위젯 배치 검증(layout 스테이지)이 타이틀 존 겹침을 hard-fail로 차단한다
- 실물 조합 예시: `data/golden-single-widgets/props.json` (타이틀 + 위젯 4종)
