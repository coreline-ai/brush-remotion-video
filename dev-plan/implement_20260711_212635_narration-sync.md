# implement_20260711_212635_narration-sync.md

작성 일시: `2026-07-11 21:26:35 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

**내레이션 동기 드로잉** — pen 프로파일에서 펜이 "지금 말하는 요소"를 그 cue 구간에 그리게 한다.
C(매크로 존)가 확보한 존 타이밍과 cue 타이밍을 정렬. **기본은 완전 자동**(휴리스틱), 스킬에서 Claude 비전 매핑으로 정밀화 가능.

## 개발 범위

- **자동 동기(기본, LLM 불필요)** — `brushvid/sync.py` 신규:
  - 존을 드로잉 순서(존 근접 순회)대로 cue들에 **순차 배분** — 배분 가중치는 존 잉크 질량 vs cue 길이 비례(최대잔여법).
    근거: 일러스트는 대개 서사 순서로 배치됨(참고 영상: 사람→공장→카드 = 내레이션 순서)
  - **리타이밍**: 각 존의 스트로크 start/end를 배정된 cue 구간 안에 재배분 (구간 앞 10%는 펜 이동 여유, 존 간 펜은 자연 소실 — getPenPose가 무스트로크 구간에서 null)
  - penInvisibleAfter/drawEnd = 마지막 존 창 끝 + 8f (develop 무팝업 유지)
- **정밀 매핑(선택)** — 파이프라인이 `data/{pid}/zones/scene-XX/zone-NN.png` 크롭 + `zones.json`(존 메타·잉크 질량·bbox)을 항상 산출.
  `data/{pid}/sync-map.json`({sceneId, zone→cue} 목록)이 있으면 자동 배분 대신 사용 — 스킬에서 Claude가 크롭을 보고 생성하는 계약
- **project.yaml**: `drawing.sync: auto(기본)|off` — pen+내레이션(srt/tts/whisper)일 때만 동작, 앰비언트/brush는 무영향
- **build.py**: routes 뒤·props 앞 `sync` 스테이지 신설 (StageLedger 캐시, `--from sync` 재개)
- routes.py: 스트로크에 `zone` 필드 추가(추가 필드 — TS parse는 무해하게 무시 확인됨) + zones.json 산출
- **스킬 문서(메인 세션 담당)**: pen-video SKILL.md에 동기 섹션 + Claude 매핑 절차(크롭 보기→sync-map.json 작성→`--from sync`)
- pytest: 배분(존3/cue2, 존2/cue4, 존1, cue0=off 폴백), 리타이밍(창 밖 스트로크 0), sync-map 우선, off/brush 무영향
- E2E: 대본 3문장 + pen-ref 배경(14존, user-images) 1씬 — **게이트: 각 cue 구간에 배정 존 스트로크의 95%+ 포함**

## 제외 범위

- 비전 매핑의 자동 실행(파이프라인이 LLM 호출하지 않음 — 크롭·계약만 제공, 실행은 스킬에서 Claude가)
- brush 프로파일·앰비언트 모드 동기 없음, 렌더러(src/) 무변경
- cue 중 무존 구간의 "펜 대기 모션" 연출 — 후속 (지금은 펜 소실이 자연스러움)

## 참조 문서

- [이전 개발 계획](implement_20260711_183519_macro-zone.md) — C 존 그룹핑 (완료, 이 작업의 기반)

## 공통 진행 규칙

- 체크박스를 실제 진행에 맞게 갱신, 범위 확장 금지.
- 기존 pytest 67·vitest 29·골든·pen 무팝업 회귀 없음. sync: off면 기존 pen 결과와 동일.

## Phase 상태 요약

- [x] Phase 1 완료 (sync.py 자동 배분·리타이밍 + zones 산출 + pytest)
- [x] Phase 2 완료 (build.py 스테이지 + sync-map 계약 + E2E 게이트)

## QA 관점

- [x] 게이트: E2E(pen-sync-demo)에서 cue별 배정 존 스트로크 포함율 **cue0 831/831 = 100%, cue3 97/97 = 100%, 전체 100%** (≥95%, scratchpad/measure-sync-gate.py)
- [x] sync: off → routes 파일 바이트 불변 (test_stage_sync_off_bytes_identical)
- [x] 존3/cue2·존2/cue4(분산 [0,2])·존1·cue0(원본 유지+경고) 엣지 크래시 없음 — pytest
- [x] 리타이밍 후 무팝업 유지 — 정착(f455) 이후 diff 0.000%; f447→f460 0.286%는 기존 관찰된 develop 크로스페이드 꼬리(팝업성 등장 아님, macro-zone 기록과 동일 특성)
- [x] 존 간 펜 소실 육안 — 스틸 sync-1(cue0: 본체 존 드로잉)/sync-2(cue1: 펜 휴지)/sync-3(cue3: 타이틀 텍스트 존 드로잉)에서 자연스러움 확인

## Phase 1. sync.py + zones 산출

### 구현 태스크
- [x] routes.py: 스트로크 zone 필드(존 그룹핑 경로에서만 — brush/False 산출물 불변, TS는 추가 필드 무시) + 존 정보(inkPixels/bbox/strokeCount/start/end) 반환, write_routes 는 meta/strokes 만 기록. 크롭·zones.json 산출은 build.py `_export_zone_assets`(pen 프로파일)
- [x] sync.py: 순차 비례 배분(`allocate_zones_to_cues` — cue 길이 비례 질량 쿼터, 찬 쿼터 건너뛰기로 존<cue 분산) + 리타이밍(`apply_sync` — cue 앞 10% 여유, 같은 cue 다중 존은 질량 비례 분할, drawEnd/penInvisibleAfter=마지막 창+8f) + sync-map 우선(미지정 존은 자동 폴백, 범위 밖 cue 는 에러)
- [x] pytest: 배분 3건/리타이밍 창 밖 0건/엣지(존1·cue0)/sync-map 우선/stage off 바이트 동일/cue0 씬 원본 유지/drawing.sync 검증 (test_sync.py 9건)

### 자체 테스트
- [x] pytest 전체 통과 — 76 passed (기존 67 + 신규 9, 회귀 없음)

### 이슈 및 수정
- [x] YAML bare `off` 가 불리언 False 로 파싱됨 → project.py 에서 bool → "auto"/"off" 정규화

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. 스테이지 통합 + E2E

### 구현 태스크
- [x] build.py sync 스테이지 (routes 뒤·layout 앞, StageLedger 캐시, `--from sync` 재개. pen+sync=auto 에서만 동작, cue 0개 씬은 자동 off) + project.py `drawing.sync: auto|off` 검증
- [x] E2E: examples/pen-sync (대본 3문장 + user-images pen-ref bg + TTS + pen 1씬 468f) → 동기 렌더 → 게이트 측정 + QA 스틸 (ffprobe: 14.60s, h264+aac. 10존·4cue, 배정 [0,0,3,3,3,3,3,3,3,3] — 거대 존(90% 질량)이 cue0 쿼터를 채워 잔여 존은 cue3 로)
- [x] 스킬 문서 갱신 완료(메인 세션): pen-video SKILL.md 동기 섹션 + Claude 매핑 절차 (sync-map 계약: data/{pid}/sync-map.json = {"scenes": [{"sceneId", "zoneToCue": {"존번호": cue번호}}]}, 크롭: data/{pid}/zones/scene-XX/zone-NN.png + zones.json)

### 자체 테스트
- [x] 게이트 100% (≥95%) / 무팝업(정착 후 0.000%) / 육안 스틸 3장 (scratchpad/sync-1~3.png)

### 이슈 및 수정
- [x] 참조 배경(pen-ref bg)은 잉크 90%가 존 1개에 몰려 cue1·2 구간이 펜 휴지가 됨 — 배분 알고리즘의 의도된 결과(존 분할은 SOURCE_BEATS 후속). 정밀 제어가 필요하면 sync-map 으로 수동 배정 가능

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 커밋(메인 검수 후)
