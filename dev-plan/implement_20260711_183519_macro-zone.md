# implement_20260711_183519_macro-zone.md

작성 일시: `2026-07-11 18:35:19 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

pen 프로파일의 스트로크 순서를 **매크로 존(오브젝트) 단위**로 바꾼다 — 한 오브젝트를 완성하고 다음으로.
효과: ① 사람이 그리는 느낌 ② 반쯤 그려진 요소 최소화 ③ 펜 순간이동 감소 ④ **오브젝트 단위 타이밍 확보**
(후속 "내레이션 동기 드로잉"의 기반). video-builder의 macro slot 개념 채택 — 코드 복사 금지.

## 개발 범위

- `brushvid/routes.py`:
  - 잉크 마스크의 **연결 성분(connected component) 라벨링**으로 매크로 존 산출 (근접 성분 병합: 팽창(dilation) 후 라벨링 — 글자처럼 조각난 요소가 한 존이 되게)
  - 각 contour/seal 스트로크를 존에 배정 (스트로크 중점이 속한/가장 가까운 존)
  - 존 순서: 첫 존(최좌상 존)부터 **존 중심 근접 순회** (deterministic, seed 영향 없음) — 존 내부는 기존 근접 순회 유지
  - `RouteParams.group_by_zone: bool = False` 노출 — **pen 프로파일 기본 true** (bin/build.py pen_route_params에 반영). brush는 무영향
  - meta에 `zoneCount` 기록
- 재검증: pen-ref-demo 배경으로 routes 재생성 → 렌더 → 스틸 비교 (오브젝트 완결성 육안) + pen-sketch E2E
- 정량 게이트: 존 단위 완결성 — 각 존의 드로잉 시간 구간이 서로 겹치는 비율 ≤ 10% (기존 방식은 수십%)
- pytest: 두 개의 떨어진 도형 fixture → 존 2개, 존1 스트로크 전부가 존2보다 먼저 / group_by_zone=False면 기존과 동일

## 제외 범위

- SOURCE_BEATS(원본 영상 손 추적·템포 이식) — 별도 후속
- 내레이션 동기 드로잉 (이번엔 기반만 — zone 타이밍 meta 기록까지)
- brush 프로파일 순서 변경 없음, 렌더러(src/) 무변경 (routes JSON 포맷 유지)

## 참조 문서

- [이전 개발 계획](implement_20260711_181423_stt-gallery.md) — B+A (완료)
- 개념 참조(읽기 전용): video-builder `references/whiteboard-source-video-contour-drawing-workflow.md`의 macro slot

## 공통 진행 규칙

- 체크박스 상태를 실제 진행 상태와 맞게 업데이트한다. 문서에 없는 범위 확장은 하지 않는다.
- 기존 pytest 64건·vitest 29건·골든 회귀·pen 무팝업(diff ≤0.1%) 유지.

## Phase 상태 요약

- [x] Phase 1 완료 (존 그룹핑 구현 + pytest)
- [x] Phase 2 완료 (pen 데모 재검증 + E2E + 게이트)

## QA 관점

- [x] 존 겹침 비율 ≤ 10% — pen-ref-demo 실측: **기존 59.7% → 존 그룹핑 0.0%** (scratchpad/measure-zone-overlap.py, 존 14개 기준)
- [x] group_by_zone=False 경로가 기존과 바이트 동일 routes 산출 — 변경 전 생성한 baseline fixture 와 json.dumps 문자열 동일 (test_zones.py), meta 에 zoneCount 미추가
- [x] 전부 붙어 있는 그림(존 1개, coverage 유지) / 백지(존 0개, 빈 strokes) 크래시 없음 — pytest
- [x] 존 순회로 인한 커버리지 저하 없음 — pen-ref-demo 98.2%→98.13%(래스터 방향차 0.07pp), pen-sketch 99.9% (≥95% 유지)
- [x] 펜 커서 순간이동 빈도: 존 체이닝(이전 존 끝점 → 다음 존 시작)으로 존 간 점프 = 존 수 - 1 회(14존 → 13회) 구조적 보장, 존 내부는 기존 근접 순회

## Phase 1. 존 그룹핑 구현

### 구현 태스크
- [x] routes.py: binary_dilation+라벨링 존 산출(`_compute_zones`) → 스트로크 존 배정(중점 라벨, 배경이면 최근접 중심) → 최좌상(cx+cy 최소) 존 시작 중심 근접 순회, seed 무관 결정적(`_order_by_zone`) — 존 내부는 기존 `_order_routes` 유지 + start_pt 체이닝. `RouteParams.group_by_zone=False` 기본 / `zone_merge_px=12` (글자 조각 병합·오브젝트 분리)
- [x] build.py pen_route_params에 group_by_zone=True + meta.zoneCount (True 경로에서만 기록)
- [x] pytest: 2도형 존 분리·순서(존1 전체가 존2보다 선행 + 타이밍 비겹침) / False 바이트 동일성(사전 baseline fixture) / 존1개·백지 엣지 (test_zones.py 3건)

### 자체 테스트
- [x] pytest 전체 통과 — 67 passed (기존 64 + 신규 3, 회귀 없음)

### 이슈 및 수정
- [x] zone_merge_px 초기값 36px 은 pen-ref-demo 에서 전체가 존 1개로 병합(팽창 과다) → 반경 스윕(36/24/18/12/9/6) 후 12px 로 조정 (글자 간격은 합치고 오브젝트는 분리 — 참조 프레임에서 14존)

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. 재검증 + 게이트

### 구현 태스크
- [x] pen-ref-demo routes 재생성(존 그룹핑, pen_route_params: drawEnd 105) → data/pen-demo props 렌더 → 스틸 f30/f75/f120 (scratchpad/zone-30.png 등) — 분리 존(카드 묶음·타이틀 글자)이 단위로 완성되는 것 육안 확인, f120 완전체
- [x] 존 겹침 비율 측정 스크립트(scratchpad/measure-zone-overlap.py) — 기존 59.7% vs 신규 0.0%
- [x] examples/pen-sketch E2E 재실행 (--from routes) — exit 0, coverage 0.999, zoneCount 1(preset 배경은 단일 연결체), mp4 10.0s

### 자체 테스트
- [x] 정량 게이트(0.0% ≤10%) + 커버리지 98.13%/99.9% ≥95% + 무팝업: 정착(f120) 이후 diff 0.000%, f114→f120 은 0.304%의 전역 develop 크로스페이드 꼬리(팝업성 등장 아님 — f250 vs f256 = 0.000%로 정적 상태 무결)

### 이슈 및 수정
- [x] develop 크로스페이드가 developFrames(8)보다 ~7f 길게 정착(f105+15) — 팝업 아님(전역 페이드), 렌더층(src) 특성으로 파이썬 범위 밖. 관찰만 기록

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / Phase 완료 커밋 (메인 검수 후)
