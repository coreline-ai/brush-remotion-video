# implement_20260711_111409_widgets.md

작성 일시: `2026-07-11 11:14:09 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

3중 위젯 체계(레거시 4 + Azure 9 + 카탈로그 50)를 **단일 registry + 통일된 카드 시스템**으로 재설계하고,
실사용 빈도 기준 핵심 15종을 구현한다. (구현계획서 Phase 5. 자동화 워크스트림과 병렬 — 이쪽은 src/·schema 소유)

## 개발 범위

- **핵심셋 15종 (실사용 12프로젝트 집계 근거)**:
  - 레거시 계열: `stat`(35회) `text`(41) `donut`(19) `bars`(15) — 카드 시스템으로 통합 재설계
  - 카탈로그 상위: `FlowDiagram`(37) `TimelineStepper`(31) `DataTable`(25) `ProcessStepCard`(19) `WarningCard`(19) `PersonAvatar`(19) `ChatBubble`(13) `CompareBars`(13) `BulletList`(13) `QuoteText`(13) `Headline`(13)
- `schema.ts`에 `WidgetSchema` — **strict discriminated union** (타입별 필드 혼입은 parse 거부) + `scenes[].widgets` + JSON Schema 재내보내기
- `src/widgets/shared.tsx` — 팔레트(T) + CardShell(kicker/title/glyph/divider/caption) + 공용 아톰(Chip/Node/Ring/Bar)
- `src/widgets/registry.tsx` — type→body 매핑, 미등록 타입 placeholder+경고
- `src/widgets/bodies/` — 파일당 위젯 1개 (15파일, 전부 items/value 데이터 구동)
- `src/scene/BrushScene.tsx`에 WidgetLayer 조립 (z 22 — Effect 18과 Title 23 사이)
- `data/golden-widgets/` 15종 전수 데모 props + 골든 스틸 등록
- 시각 언어는 참조(WhiteBrushWidgetLayer의 화이트 카드·잉크·muted accent) 채택하되, **바디를 하드코딩 샘플이 아닌 items/value 데이터 구동으로 개선**

## 제외 범위

- 컨테이너 9종 (Grid/Stack 등 — 절대좌표 배치로 대체, 수요 시 후속)
- 나머지 카탈로그 ~35종 (수요 발생 시 registry에 추가)
- pipeline/·bin/ 수정 금지 (자동화 워크스트림 소유), 위젯 auto 배치 연동은 두 워크스트림 완료 후 통합
- 하위호환 필드 (donut의 label 등 — v1은 title로 통일)

## 참조 문서

- [상세 구현계획서](../docs/impl-plan-brush-remotion-video.md) — Phase 5
- [이전 개발 계획](implement_20260711_103823_directing.md) — 연출 레이어 (완료)

## 공통 진행 규칙

- 각 Phase는 앞선 Phase의 자체 테스트 완료 후에만 시작한다.
- 구현 중 발생한 이슈는 해당 Phase에서 수정하고 기록한다.
- 체크박스 상태를 실제 진행 상태와 맞게 업데이트한다.
- 문서에 없는 범위 확장은 하지 않는다.
- 기존 골든(single/multi) diff 게이트가 계속 통과해야 한다.

## Phase 상태 요약

- [x] Phase 1 완료 (스키마 union + 카드 시스템 + 레거시 4종) — 2026-07-11
- [x] Phase 2 완료 (카탈로그 11종 + 전수 데모 + 골든) — 2026-07-11

## QA 관점

- [x] TC-5.1: registry 키 15종 전부 등록 (vitest 통과)
- [x] TC-5.2: stat {value:"87%"} → 스틸 f250에 "87% 커버리지" 표기 (육안 확인)
- [x] TC-5.E1: registry 미등록 키("hologram") → placeholder + console.warn (vitest)
- [x] TC-5.E2: donut+values 혼입 → strict union 거부 (vitest)
- [x] golden-single 회귀 diff 0.045~0.124% ≤ 2% (WidgetLayer 추가 후 재렌더)

## Phase 1. 스키마 + 카드 시스템 + 레거시 4종

### 구현 태스크
- [x] `schema.ts` WidgetSchema(strict discriminated union 15종) + scenes[].widgets + export-schema 재실행
- [x] `widgets/shared.tsx` (팔레트 T·CardShell·Chip/Node/Ring/HBar) + `widgets/registry.tsx` + `scene/WidgetLayer.tsx` (z22)
- [x] bodies: stat / text / donut / bars (데이터 구동)
- [x] vitest: TC-5.1/5.E1/5.E2 (28건 전체 통과)

### 자체 테스트
- [x] tsc + vitest 통과, 스틸 f250 육안 확인

### 이슈 및 수정
- [x] 발견 이슈 없음

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. 카탈로그 11종 + 전수 데모

### 구현 태스크
- [x] bodies 11종 전부 items/value 데이터 구동으로 구현 (참조의 하드코딩 샘플 방식 개선)
- [x] `data/golden-widgets/` 15종 전수 props (2씬×8+7 배치) + 스틸 f250/f550 → tests/golden/baseline-widgets/ 등록
- [x] golden-single 회귀 재확인 (0.045~0.124%)

### 자체 테스트
- [x] 15종 전부 스틸에 정상 표시 (f250: 레거시4+텍스트4 / f550: 다이어그램·데이터·말풍선 7종 육안 확인)

### 이슈 및 수정
- [x] 발견 이슈 없음

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / Phase 완료 커밋
