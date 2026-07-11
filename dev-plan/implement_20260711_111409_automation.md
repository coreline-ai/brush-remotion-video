# implement_20260711_111409_automation.md

작성 일시: `2026-07-11 11:14:09 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

**`project.yaml` 하나로 완성 mp4가 나오는 단일 진입점(`bin/build.py`)** 을 만든다 — 이 프로젝트의 존재 이유.
(구현계획서 Phase 4. 위젯 워크스트림과 병렬 — 접점 없음: 이쪽은 pipeline/·bin/, 위젯은 src/·schema)

## 개발 범위

- `brushvid/stt.py` — 더빙 오디오 → 로컬 whisper(small, ko) → SRT. whisper 경로: `/Users/hwanchoi/project_202606/new-video-gen/.venv-whisper/bin/whisper` 재사용(부재 시 설치 안내 에러)
- `brushvid/project.py` — project.yaml 파서 + 검증 + 모드 판정 (srt→내레이션 / audio만→whisper / 둘 다 없음→앰비언트)
- `bin/build.py` — 스테이지 오케스트레이션: stt→cues→background→clean→routes→layout(위젯 auto는 보류; none/authored만)→props→render→mux→qa. 스테이지 산출물 캐시(`data/{projectId}/`) + `--from <stage>` 재개
- 앰비언트 모드 — 고정 300프레임×N씬 + numpy/wave 합성 BGM(brushvid/audio.py) + 시적 한줄 cue
- `bin/qa.py` — QA 단독 실행 (기존 brushvid.qa 활용)
- E2E 3모드: ① SRT 제공(입력: new-video-gen/input/ai-coding-future.srt 복사본) ② audio만→whisper (음성 없으면 macOS `say -v Yuna`로 한국어 테스트 음성 합성 가능) ③ 앰비언트
- examples/{narration,ambient}/project.yaml 예시 2종

## 제외 범위

- 위젯 auto 배치의 렌더 연동 (위젯 워크스트림 완료 후 통합 — layout.py 호출은 옵션 플래그 뒤에 보류)
- src/ TS 수정 금지 (병렬 워크스트림 소유), schema/render-props.schema.json 재생성 금지 (소비만)
- new-video-gen 수정 금지 (input SRT는 복사해서 사용)

## 참조 문서

- [상세 구현계획서](../docs/impl-plan-brush-remotion-video.md) — Phase 4 섹션 (project.yaml 스키마 초안, TC)
- [이전 개발 계획](implement_20260711_103823_pipeline.md) — brushvid 패키지 (완료)

## 공통 진행 규칙

- 각 Phase는 앞선 Phase의 자체 테스트 완료 후에만 시작한다.
- 구현 중 발생한 이슈는 해당 Phase에서 수정하고 기록한다.
- 체크박스 상태를 실제 진행 상태와 맞게 업데이트한다.
- 문서에 없는 범위 확장은 하지 않는다.

## Phase 상태 요약

- [ ] Phase 1 완료 (project.py + stt.py + audio.py)
- [ ] Phase 2 완료 (bin/build.py 오케스트레이션 + 캐시/재개)
- [ ] Phase 3 완료 (E2E 3모드 + bin/qa.py + examples)

## QA 관점

- [ ] TC-4.1: srt+audio 제공 → 내레이션 모드 (whisper 미호출)
- [ ] TC-4.2: audio만 → stt 스테이지 실행, SRT 생성
- [ ] TC-4.3: 둘 다 없음 → 앰비언트 (scenes N×300f)
- [ ] TC-4.E1: format 오타 → yaml 검증 즉시 실패 (파이프라인 미진입)
- [ ] TC-4.E2: 오디오 duration vs scenes 합산 불일치 >1s → 경고+자동 보정
- [ ] `--from render` 재실행 시 앞 스테이지 스킵 (로그 확인)
- [ ] 명령 1회 → output/{projectId}.mp4 + QA 산출물, 수동 개입 0회

## Phase 1. project.py + stt.py + audio.py

### 구현 태스크
- [x] project.py: yaml 로드/검증(projectId/format/input/background/widgets), 모드 판정
- [x] stt.py: whisper 호출 래퍼 (모델 small, ko) + SRT 산출
- [x] audio.py: 앰비언트 BGM 합성 (numpy/wave — 참조 빌더들의 피아노/패드/벨 레시피를 임의 길이로 일반화, lfilter 로우패스) + 길이 정합(reconcile_scenes_with_audio)
- [x] pytest: 모드 판정 3종 + format 오타 거부 (TC-4.1/4.3 판정부, TC-4.E1)

### 자체 테스트
- [x] pytest 통과 (test_project 7 + test_audio 4 = 11 passed)

### 이슈 및 수정
- [x] widgets: auto 는 보류 범위 → 검증은 허용하되 경고 후 none 으로 강등 처리 (위젯 워크스트림 통합 후 해제)

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. bin/build.py 오케스트레이션

### 구현 태스크
- [ ] 스테이지 정의 + 순차 실행 + 산출물 캐시(data/{projectId}/stages/) + `--from` 재개
- [ ] 내레이션 경로: SRT→cues→씬 분할(길이 상·하한)→배경 N장→clean→routes→props
- [ ] 앰비언트 경로: N씬×300f + BGM 합성 + 시적 cue
- [ ] mux: 영상 렌더 후 오디오 합성 (render-props audio는 null로 렌더 → ffmpeg mux)
- [ ] TC-4.E2: 오디오 duration 자동 보정

### 자체 테스트
- [ ] pytest (스테이지 스킵/캐시 로직 단위 테스트)
- [ ] `--from render` 재실행 시 앞 스테이지 스킵 로그 확인

### 이슈 및 수정
- [ ] 발견 이슈 없음

### 완료 조건
- [ ] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 3. E2E 3모드 + qa.py + examples

### 구현 태스크
- [ ] examples/narration/project.yaml (SRT 제공 모드, 배경 strategy: preset) + 실행
- [ ] examples/ambient/project.yaml (앰비언트 3씬) + 실행
- [ ] whisper 모드: 테스트 음성(say -v Yuna 합성 가능) → SRT 생성 확인 → 빌드
- [ ] bin/qa.py 단독 실행 검증

### 자체 테스트
- [ ] 3모드 각각 output/{projectId}.mp4 산출 (ffprobe 스트림/길이 확인)
- [ ] QA 산출물 (capture-manifest.json + 콘택트시트) 생성

### 이슈 및 수정
- [ ] 발견 이슈 없음

### 완료 조건
- [ ] 구현 완료 / 자체 테스트 완료 / E2E 게이트 통과 (커밋은 메인 세션 검수 후)
