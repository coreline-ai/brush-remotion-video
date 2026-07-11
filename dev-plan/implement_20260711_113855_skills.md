# implement_20260711_113855_skills.md

작성 일시: `2026-07-11 11:38:55 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

**코드 사본 없는 얇은 스킬 2종**(brush-video 생성 + brush-qa-review)을 만들어 이 리포를 유일한 소스로 확정하고,
구 brush-draw-reveal 스킬을 deprecated 처리한다. (구현계획서 Phase 6 — 마지막 Phase)

## 개발 범위

- `skill/brush-video/SKILL.md` — 실행 대상을 이 리포로 지정, 워크플로 = project.yaml 작성 → bin/build.py → QA. 코드 사본 금지
- `skill/brush-video/references/` — background-prompt.md(구 스킬 문서 이식+갱신), project-yaml-guide.md, widget-catalog.md(핵심 15종)
- `skill/qa-review/SKILL.md` — bin/qa.py의 capture-manifest.json 계약 기준 리뷰 스킬 + scene-fix-request 스키마 reference
- `bin/install-skills.sh` — ~/.claude/skills/{brush-video,brush-qa-review} **symlink** 설치 (사본 금지)
- 구 스킬 deprecated 표기: `~/.claude/skills/brush-draw-reveal/SKILL.md` + `new-video-gen/.claude/skills/brush-draw-reveal/SKILL.md` 상단 안내 (new-video-gen 수정 금지의 유일한 예외)
- `README.md`(설치→build→QA) + `docs/schema.md` + `docs/pipeline.md`

## 제외 범위

- 스킬 폴더에 .tsx/.py 실행 코드 배치 (드리프트 원천 차단 — TC-6.1로 강제)
- 위젯 auto 배치 통합 (후속 과제로 명시)
- 새 세션 스킬 호출 E2E (TC-6.2)는 이 세션에서 불가 — 수동 확인 항목으로 남김

## 참조 문서

- [상세 구현계획서](../docs/impl-plan-brush-remotion-video.md) — Phase 6
- 구 스킬 문서(문서만 참고): `~/.claude/skills/brush-draw-reveal/SKILL.md`, references/

## 공통 진행 규칙

- 체크박스 상태를 실제 진행 상태와 맞게 업데이트한다.
- 문서에 없는 범위 확장은 하지 않는다.

## Phase 상태 요약

- [x] Phase 1 완료 (스킬 2종 + 설치 + deprecated + 문서) — 2026-07-11

## QA 관점

- [x] TC-6.1: skill/ 내 .tsx/.py/.ts 0건 (실측)
- [x] 설치 확인: symlink 2개 생성 + 세션 스킬 목록에 brush-video/brush-qa-review 등록 확인
- [x] 구 스킬 2곳 상단 deprecated 안내 (frontmatter 뒤 삽입)
- [x] TC-6.2(새 세션 E2E)는 수동 확인 필요 항목으로 인계 (아래 잔여 과제)

## Phase 1. 스킬 2종 + 설치 + deprecated + 문서

### 구현 태스크
- [x] skill/brush-video/SKILL.md + references 3종 (background-prompt 이식, project-yaml-guide, widget-catalog 15종)
- [x] skill/qa-review/SKILL.md + scene-fix-request-schema.md (kind→수정 위치→재빌드 스테이지 매핑)
- [x] bin/install-skills.sh 작성 + 실행 (symlink 2개)
- [x] 구 스킬 deprecated 표기 2곳
- [x] README.md / docs/schema.md / docs/pipeline.md

### 자체 테스트
- [x] TC-6.1 0건 + symlink + deprecated + 세션 스킬 목록 등록 확인

### 이슈 및 수정
- [x] 발견 이슈 없음

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / Phase 완료 커밋

## 잔여 리스크 / 후속 과제

- 새 세션에서 brush-video 스킬 호출 E2E (TC-6.2) — 수동 확인 필요
- 위젯 auto 배치 통합 (layout.py ↔ scenes[].widgets 연결) — 후속 워크스트림
- 구 brush-draw-reveal 스킬 완전 제거 시점은 사용자 결정
