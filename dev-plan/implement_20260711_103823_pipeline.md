# implement_20260711_103823_pipeline.md

작성 일시: `2026-07-11 10:38:23 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

이미지 하나가 **routes JSON과 스키마 검증된 render-props로 변환**되는 Python 파이프라인 패키지(`brushvid`)를 만든다.
(구현계획서 Phase 3에 해당. 연출 레이어 워크스트림과 병렬 — 접점은 schema/render-props.schema.json과 routes 포맷뿐)

## 개발 범위

- `pipeline/pyproject.toml` + `pipeline/brushvid/` 패키지 (deps: pillow, numpy, scipy, scikit-image, pyyaml, jsonschema; dev: pytest)
- `pipeline/.venv` 부트스트랩 + `pipeline/README.md`에 절차 명시
- `brushvid/routes.py` — 이미지→콘텐츠 마스크→skeletonize→폴리라인 추적→RDP→seal 밴드→타이밍 → routes JSON (+커버리지 리포트)
- `brushvid/background.py` — clean(종이색 키잉) + 전략 3종(imagegen/preset/user-images), imagegen 부재 시 preset 폴백
- `brushvid/layout.py` — 빈 영역 탐지 + 위젯 자동 배치 + 겹침 검증(UI 겹침 hard-fail, 여백≥90px)
- `brushvid/cues.py` — SRT 파싱→frame 환산(fps 30), 긴 문장 분할(한글 글리프 비례), 씬 그룹핑 + title_color
- `brushvid/props.py` — render-props 빌더, `schema/render-props.schema.json`으로 jsonschema 검증 (스키마 자체 정의 금지)
- `brushvid/render.py` + `brushvid/qa.py` — remotion render 호출/세그먼트 concat/오디오 mux, 프레임 캡처→capture-manifest.json→콘택트시트
- `pipeline/tests/` pytest — 구현계획서 Phase 3 TC 전부
- 스펙 소스(읽기 전용): new-video-gen `scripts/brush-draw/` 헬퍼들 — 알고리즘 채택, 코드 파일 복사 금지, 모듈로 재구성

## 제외 범위

- stt.py(whisper), bin/build.py, project.yaml (Phase 4 워크스트림)
- TS/렌더 코드 수정 (src/ 전체 — 병렬 워크스트림 소유)
- new-video-gen 수정 금지, 스킬 구버전 사본 참조 금지

## 참조 문서

- [상세 구현계획서](../docs/impl-plan-brush-remotion-video.md) — Phase 3 섹션 (태스크·TC 원본)
- [이전 개발 계획](implement_20260711_095315.md) — 리빌 코어 (완료)

## 공통 진행 규칙

- 각 Phase는 앞선 Phase의 자체 테스트 완료 후에만 시작한다.
- 구현 중 발생한 이슈는 해당 Phase에서 수정하고 기록한다.
- 체크박스 상태를 실제 진행 상태와 맞게 업데이트한다.
- 문서에 없는 범위 확장은 하지 않는다.
- JSON Schema는 TS에서 내보낸 것을 소비만 한다 (이중 정의 금지).

## Phase 상태 요약

- [ ] Phase 1 완료 (패키지 스캐폴드 + routes.py)
- [ ] Phase 2 완료 (background/layout/cues/props)
- [ ] Phase 3 완료 (render/qa + 통합 게이트)

## QA 관점

- [ ] 게이트: winter-snow-pine composed.png → 신규 routes 커버리지 ≥ 95%, 스트로크 수 기존(303) ±20%
- [ ] props.py 산출물이 jsonschema + (가능하면) TS Zod parse 양쪽 통과
- [ ] 백지 이미지 → 빈 strokes + 경고 (크래시 금지)
- [ ] 타임코드 역전 SRT → 명시적 에러
- [ ] codex 부재 환경에서 imagegen → preset 폴백 + 경고

## Phase 1. 패키지 스캐폴드 + routes.py

### 구현 태스크
- [ ] pyproject.toml + brushvid/__init__.py + .venv 부트스트랩 + README
- [ ] routes.py (마스크→skeletonize→추적→RDP→seal→순서/타이밍→JSON)
- [ ] pytest: TC-3.1(검은 원 → 스트로크 ≥1, 경계 밴드 내), TC-3.E1(백지 → 빈 strokes+경고)

### 자체 테스트
- [ ] winter composed.png 입력 → 커버리지 ≥95%, 스트로크 수 303±20%
- [ ] 산출 routes가 RoutesDataSchema 형태(meta 필수 필드 + strokes)와 일치

### 이슈 및 수정
- [ ] 발견 이슈 없음

### 완료 조건
- [ ] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. background / layout / cues / props

### 구현 태스크
- [ ] background.py (clean + 3전략 + 폴백) — TC-3.E3
- [ ] layout.py (빈영역 + 배치 + 겹침 hard-fail) — TC-3.4
- [ ] cues.py (SRT→frame, 분할, title_color) — TC-3.2, TC-3.E2
- [ ] props.py (빌더 + jsonschema 검증) — TC-3.3

### 자체 테스트
- [ ] pytest 전부 통과

### 이슈 및 수정
- [ ] 발견 이슈 없음

### 완료 조건
- [ ] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 3. render / qa + 통합 게이트

### 구현 태스크
- [ ] render.py (remotion render 호출, 세그먼트 concat, ffmpeg mux)
- [ ] qa.py (프레임 캡처, capture-manifest.json, 콘택트시트)
- [ ] 통합: 신규 routes로 BrushLandscape 렌더 성공 (E2E 스모크)

### 자체 테스트
- [ ] 신규 생성 routes JSON → 렌더에서 정상 드로잉 (스틸 육안/기존 golden과 유사성)
- [ ] pytest 전체 + 커버리지 게이트 재확인

### 이슈 및 수정
- [ ] 발견 이슈 없음

### 완료 조건
- [ ] 구현 완료 / 자체 테스트 완료 / 게이트 통과 (커밋은 메인 세션에서 검수 후)
