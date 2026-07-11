# implement_20260711_215659_shorts.md

작성 일시: `2026-07-11 21:56:59 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

**shorts-brush** — 세로 풀블리드 힐링 브러시 쇼츠 프로파일 스킬 (참고 영상: 3씬×10초 수채 풍경 + 시적 자막).
전제인 기술 갭(파이프라인 가로 하드코딩)을 먼저 수정하고, 세로 연출 프리셋과 프로파일 스킬을 얹는다.

## 개발 범위 (확정 스펙 — 대화에서 합의된 전문)

- **Phase 1 — 세로 파이프라인 정합 (파이썬)**:
  - `format: shorts` → background 캔버스·RouteParams·separate_ink·layout 좌표계 전부 **1080×1920** 전파
    (background.py `W,H` 하드코딩 제거 — format 인자화)
  - imagegen **세로 프롬프트 템플릿** 신설: 9:16 vertical full-bleed, 상단 1/4 하늘·여백(타이틀 세이프존 겸), 중앙 주 소재, 하단 근경. preset(PIL)도 세로 캔버스 지원
  - 게이트: shorts E2E에서 배경 PNG·routes meta·mp4 해상도 전부 1080×1920 일치 + **가로(youtube) 경로 산출물 무변경**
- **Phase 2 — 세로 연출 프리셋 (파이썬, props 주입)**:
  - 쇼츠 자막 세이프존: `subtitleStyle{bottom ≥ 290(≈15%), maxWidth ~900, fontSize 34~38}` 기본 주입
  - **자막 강조색 씬 동조**: 씬 배경에서 `title_color()`로 추출한 색을 `highlightColor`로 (씬마다)
  - 훅: 첫 씬 프리워시 짧게(opacity 0.5, frames 18) / 씬 전환 outro 18f / **루프 엔딩**: 마지막 씬 outro 워시 순백 수렴
  - topTitle 사용 시 y ≥ 120 세이프존 (layout 검증이 세로 좌표계로 상하 세이프존 침범 차단)
  - 길이 규칙: 앰비언트 scenes 기본 3(=30초), **한도 18(=180초, 쇼츠 규정)** — 초과 시 검증 에러 + 60초 미만 권장 경고
- **Phase 3 — 스킬 편입 (메인 세션)**:
  - `skill/shorts-brush/SKILL.md` (트리거·기본 3씬 프리셋·세이프존·길이 규정 180s 한도/30s 권장·루프 가이드·yaml 예시)
  - `background-prompt.md`에 📱 세로 섹션(문서), director intent-map "쇼츠/세로" 행 위임 갱신 + mood-presets 세로 주석
  - install-skills.sh 5번째 symlink + **30초 데모(호수→숲→노을 3씬) → 사용자 판정 게이트**

## 제외 범위

- pen 프로파일의 세로 대응(이번엔 brush 계열만 — pen 쇼츠는 후속), 위젯 세로 데모, 환경음
- 렌더러(src/) 수정 없음 (BrushPortrait 기존 검증 완료)

## 참조 문서

- [이전 개발 계획](implement_20260711_212635_narration-sync.md) — 내레이션 동기 (완료)
- 참고 영상 실측: 1080×1920·24fps·31.25s·AAC, 3씬(호수/숲길/노을), 자막 하단 ~15% 위치·씬 팔레트 동조 강조색
- 쇼츠 규정(2026 확인): 최대 180초, 9:16 1080×1920, 초기 노출은 60초 미만 유리

## 공통 진행 규칙

- 체크박스 실제 진행 갱신, 범위 확장 금지.
- 기존 pytest 76·vitest 29·골든 3세트·youtube(가로) 경로 무변경.

## Phase 상태 요약

- [x] Phase 1 완료 (세로 파이프라인 정합)
- [x] Phase 2 완료 (세로 연출 프리셋)
- [ ] Phase 3 완료 (스킬 편입 + 사용자 판정)

## QA 관점

- [x] 해상도 정합: 배경·routes meta·mp4 전부 1080×1920 (shorts-healing E2E 실측: bg 3장 1080×1920, routes meta 3건 1080×1920, ffprobe 1080×1920/30fps/30.0s/h264+aac)
- [x] 가로 회귀 0: preset 배경(seed 7/42)·circle routes 변경 전 스냅샷과 바이트 동일 + pytest 기존 76건 전부 통과 (test_shorts.py 에 preset sha256 baseline 상시 가드 추가)
- [x] 세이프존: 자막 bottom 290 기본 주입, topTitle y ≥ 120 / 위젯 상·하단 침범 hard-fail (세로 canvas 전용, 가로 무변경 — 테스트 6건)
- [x] 강조색 동조: E2E 3씬 highlightColor = #8e8678 / #847e8b / #788584 (씬별 상이, 배경 추출색)
- [x] scenes 19 이상 → 검증 에러 / 7씬(70초) → 경고만 (테스트)
- [x] 루프: 최종 vs 첫 프레임 mean abs diff 1.87% (lum 244.7→247.1, 순백 수렴 확인)
- [ ] 최종: 30초 데모 사용자 육안 판정 (게이트 — Phase 3)

## Phase 1. 세로 파이프라인 정합

### 구현 태스크
- [x] background.py format 인자화(캔버스·contain·separate_ink) + 세로 imagegen 템플릿 + preset 세로
- [x] build.py format 전파(RouteParams W/H·layout 좌표계)
- [x] pytest: 세로 캔버스 산출 해상도 / 가로 경로 무변경(기존 fixture + preset sha256 baseline)

### 자체 테스트
- [x] shorts 스모크(examples/shorts-healing, preset 3씬)에서 해상도 3종 일치 / pytest 전체 통과 (93 passed)

### 이슈 및 수정
- [x] 발견 이슈 없음

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. 세로 연출 프리셋

### 구현 태스크
- [x] props 주입: 쇼츠 subtitleStyle 세이프존 + 씬별 highlightColor(title_color) + 훅/전환/루프 엔딩 프리셋
- [x] project.py: ambient scenes 한도 18 검증(초과 에러)·60초 초과 권장 경고
- [x] layout 세이프존 검증(상하) + pytest

### 자체 테스트
- [x] pytest 전체 + 프리셋 주입 값 확인 (92 passed = 기존 76 + 신규 16)

### 이슈 및 수정
- [x] 이슈 1: preset 배경의 수채 워시 채도(sat p99≈25)가 title_color 기본 min_sat=30 미달 →
      3씬 모두 잉크 폴백(#5a544c) 동일색. 수정: (a) 세로 preset 은 시드 회전 도미넌트 팔레트 +
      워시 alpha 92 (가로 분기 무변경 — sha256 baseline 유지 확인), (b) shorts 추출은 min_sat=14.
      결과: 3씬 3색 상이 (#8e8678/#847e8b/#788584).

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 3. 스킬 편입 + 판정 (메인 세션)

### 구현 태스크
- [x] skill/shorts-brush/SKILL.md(프로파일 스킬 — 트리거·자동 동작 표·길이 규정·세로 배경 규칙) + background-prompt.md 📱 세로 섹션 + director intent-map 위임·mood-presets 주석 + install(6번째 symlink)
- [x] 30초 데모 빌드 완료 (examples/shorts-healing, preset 배경) → output/shorts-healing.mp4 판정 제출. imagegen 풍경판(호수→숲→노을)은 판정 후 원하면 재생성

### 자체 테스트
- [x] 스킬 실행 코드 0건(실측) + symlink + 데모 산출 (ffprobe 1080×1920·30.0s·h264+AAC)

### 이슈 및 수정
- [ ] 발견 이슈 없음

### 완료 조건
- [ ] 사용자 판정 통과 / 커밋
