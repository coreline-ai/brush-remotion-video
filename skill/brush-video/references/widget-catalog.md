# 위젯 카탈로그 — 핵심 15종 (v1)

`scenes[].widgets[]`에 넣는 카드 위젯. 스키마는 strict union — 타입에 없는 필드를 넣으면 parse가 거부한다.
유일한 정의: `src/schema.ts`의 `WidgetSchema`.

## 공통 필드 (전 타입)

| 필드 | 설명 |
|---|---|
| `x, y, w, h` | 절대 좌표(px, 1920×1080 기준) — 자막 하단 밴드·topTitle 영역 침범 금지, 가장자리 여백 ≥90px |
| `enterAt` | 등장 프레임 (기본 0) — 카드가 14f 페이드 + 18f rise로 등장 |
| `title` | 카드 제목 (필수) |
| `kicker` | 상단 소제목 (선택, 대문자 표시) |
| `caption` | 하단 각주 (선택) |
| `accent` | 강조색 (선택 — 미지정 시 팔레트 순환: lavender/sage/blue/clay/ochre) |

## 타입별 고유 필드

| 타입 | 고유 필드 | 바디 |
|---|---|---|
| `stat` | `value`(필수), `sub` | 큰 수치 + 단위 |
| `text` | `lines[]`(필수) | 불릿 줄 목록 |
| `donut` | `pct`(0~100 필수) | 링 차트 |
| `bars` | `values[]`(필수) | 미니 세로 막대 (최댓값 강조) |
| `Headline` | `items[]` | 큰 헤드라인 (items label을 줄로, 첫 줄 accent) |
| `QuoteText` | `items[]` | "인용문" (items[0].label) |
| `BulletList` | `items[]` | label + detail 불릿 |
| `CompareBars` | `items[]` (value 숫자) | 수평 비교 바 (마지막 항목 accent) |
| `ProcessStepCard` | `items[]` | 01/02/03 번호 칩 |
| `WarningCard` | `items[]` (tone) | 경고 칩 (첫 항목 danger 기본) |
| `FlowDiagram` | `items[]` | 노드 → 노드 흐름 (label 4자 이내 권장) |
| `TimelineStepper` | `items[]` | 기준선 + 번호 노드 + label |
| `DataTable` | `items[]` (value/detail) | label · value · detail 3열 표 |
| `PersonAvatar` | `items[]` | 이니셜 배지 + label/detail |
| `ChatBubble` | `items[]` | 좌/우 교대 말풍선 |

`items[]` 원소: `{ label, detail?, value?, tone?("ok"|"warn"|"danger") }`

## 예시

```json
{ "type": "stat", "x": 90, "y": 80, "w": 320, "h": 210, "enterAt": 20,
  "title": "자동화 씬", "kicker": "STAT", "value": "87%", "sub": "커버리지" }
```

전수 데모: `data/golden-widgets/props.json` (15종 2씬 배치 실물 예시)
