# implement_20260711_185258_ops-rules.md

작성 일시: `2026-07-11 18:52:58 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

video-builder 검토의 잔여 채택 2건 — 운영 규칙·관행을 문서 체계에 편입한다:
**E) 스타일 프리셋 운용 규칙** — "매번 같은 템플릿" 방지 (한 영상=한 프리셋 / 새 영상은 직전과 변주).
**F) FIELD-LOG 관행** — 실전 제작에서 발견한 갭을 반드시 문서·검증기로 환류하는 순환 도입.

## 개발 범위

- **E**: `skill/director/references/mood-presets.md` 상단에 "운용 규칙" 섹션
  (한 영상=한 프리셋 / 직전 영상과 다른 프리셋·seed·소재 변주 / director가 브리프 전 직전 프로젝트 확인) +
  `skill/director/SKILL.md` 규칙 목록에 1줄 연결
- **F**: 리포 루트 `FIELD-LOG.md` 신설 — 기록 규칙(발견→수정→**문서/검증기 환류 필수**) + 항목 템플릿 +
  실제 첫 항목 1건(pen 제작 중 cover-fit 잘림 → contain 규칙 환류 사례) 시드.
  `skill/brush-video`·`skill/pen-video`·`skill/qa-review` SKILL.md에 "실전 갭 발견 시 FIELD-LOG 기록" 1줄씩 +
  README 문서 목록에 추가

## 제외 범위

- 코드/파이프라인 변경 없음 (순수 문서), D(보이스 클로닝)는 계속 기록만

## 참조 문서

- [이전 개발 계획](implement_20260711_183519_macro-zone.md) — C (완료)
- 개념 참조: video-builder `STYLE-PRESETS.md`(운용 규칙), `FIELD-TEST-LOG.md`(보강 라운드 형식)

## 공통 진행 규칙

- 체크박스 상태를 실제 진행 상태와 맞게 업데이트한다. 문서에 없는 범위 확장은 하지 않는다.

## Phase 상태 요약

- [x] Phase 1 완료 (E+F 문서 편입) — 2026-07-11

## QA 관점

- [x] FIELD-LOG 템플릿의 "환류" 필드 ★필수 표기 + 시드 항목(펜 cover-fit 잘림 사례)이 형식 시연
- [x] 스킬 3종 + README에서 FIELD-LOG 언급 grep 4곳 확인
- [x] director 운용 규칙에 확인 방법(`ls -t data/ | head`) 명시

## Phase 1. E+F 문서 편입

### 구현 태스크
- [x] mood-presets.md 운용 규칙 섹션 (한 영상=한 프리셋 / 직전과 변주 / 확인 방법) + director SKILL.md 규칙 1줄
- [x] FIELD-LOG.md (규칙+템플릿+시드 1건) + brush-video §갭 환류 / pen-video / qa-review 각 1항목 + README 목록

### 자체 테스트
- [x] grep 확인 — FIELD-LOG 4곳(스킬 3종+README), 운용 규칙 2문서

### 이슈 및 수정
- [x] 검수 중 실갭 발견: brush-video SKILL.md 환경 요구사항이 구 whisper 경로(new-video-gen/.venv-whisper)를 안내 — B(faster-whisper) 전환 때 갱신 누락 → pipeline[stt] 안내로 정정. F 관행이 도입 즉시 효용을 증명한 사례

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 커밋
