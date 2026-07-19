# Changelog

이 프로젝트의 사용자 영향 변경 사항을 기록한다. 버전 태그는 모든 자동 게이트와 해당 릴리스의
수동 게이트가 완료된 뒤에만 생성한다.


## [Unreleased]

### Added

- **`seamless-short-video` 정식 v1.0.0 stable** (catalog 11종, Remotion 독립 라인)
  - 조인 정본: 이전 씬 말미 ~2초 동작 연속 (`docs/seamless-short-video/16` §0)
  - CLI: `init` / `handoff` / `verify` / `concat` / `join-score` / `--auto-head-trim`
  - SSOT: `docs/seamless-short-video/` · 개발 계획 `dev-plan/implement_20260717_141429.md`
  - 데모: momo join-fix · popo 60s · lulu 30s
- 설계·운영 SSOT 문서 패키지 `docs/seamless-short-video/` (Multi-Signal, C-xxx, 10초 경계 C0–C26)
- **공통 수정 방향 표준** `docs/seamless-short-video/13-common-remediation-standard.md`

### Changed

- `skill/catalog.json` catalogVersion `1.3.1`; seamless status specialized→**stable**, version **1.0.0**
- `bin/seamless-short.py frame0-check` (docs 15 C12 hard gate); `pipeline/tests/test_seamless_short.py`; `schema/seamless-project.schema.json` draft

## [0.1.0] - 2026-07-13

### Added

- `project.yaml` 기반 Remotion 영상 제작 파이프라인과 stage cache/재개
- brush, pen, pen-brush, shorts, dark-random-brush 렌더 프로파일
- storybook full-touch 오케스트레이션과 Supertonic 여성 음성팩 10종
- 로컬 BGM catalog, LUFS 정규화, ducking, playlist crossfade, 라이선스 manifest
- video-auditor, 장면 QA, golden fixture와 회귀 테스트
- 37개 canonical 카메라 기법과 9개 legacy alias를 사용하는 Camera Prompt Interpreter
- catalog 기반 Claude/Codex 스킬 9종 설치와 검증
- 공개 Git tree 계약 검사와 GitHub Actions CI

### Changed

- Pixabay BGM을 YouTube·YouTube Shorts 제작/교체/배포에서 hard block
- 일반 brush 완료 연출을 integrated no-pulse 방식으로 통일
- 펜 커서와 pen-brush 외곽선을 얇고 샤프한 자산·경로 계약으로 보정
- 작은 대표 예제를 clone 직후 preflight 가능한 추적 fixture로 전환

### Distribution

- 프로젝트 자체 저작물은 루트 `LICENSE`의 proprietary 조건을 따른다.
- 원본 BGM과 대형 이미지 원본은 재배포하지 않으며 로컬 자산으로 관리한다.
- Supertonic 음성 fixture와 외부 출처는 `THIRD_PARTY_NOTICES.md` 및 manifest를 따른다.

### Release gate

- 자동 회귀: pytest 312, Vitest 50, typecheck/schema/catalog/public-tree
- 수동 게이트: `local-assets/bgm/listening-approval.json` 승인 완료 전에는 BGM 운영 승인으로 표시하지 않는다.
