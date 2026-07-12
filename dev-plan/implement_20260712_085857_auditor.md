# implement_20260712_085857_auditor.md

작성 일시: `2026-07-12 08:58:57 KST`

이 문서는 이번 개발의 범위를 고정하고, 구현이 목적 밖으로 확장되지 않도록 하기 위한 작업 문서다.

## 개발 목적

**video-auditor** — 완성 mp4 하나만으로 결함(하드컷·번쩍 스파이크·정지·오디오·규격)을 자동 검출하는
독립 검수 도구 + 스킬. 어제 수동으로 두 번 수행한 검수(city 하드컷 12~23%, develop 스파이크 2.97%)를
자동화하며, 그 실측치가 임계값·회귀 fixture가 된다.

## 개발 범위 (확정 스펙 — 대화 합의 전문)

- **`pipeline/brushvid/audit.py`** — brushvid 타 모듈 import 없이 단독 완결 (ffmpeg/ffprobe/PIL/numpy만, 신규 의존성 0):
  - 2-패스 프레임 스캔: ① 저해상도(192px 그레이) rawvideo 파이프 전 프레임 diff ② 후보 지점만 원본 해상도 정밀 재측정
  - 검출 6종: ①경계 하드컷(WARN>6%/FAIL>10%) ②씬 중간 스파이크(WARN>1.5%&3×롤링중앙값/FAIL>2.5%&4×)
    ③정지(diff≈0 3s+, 씬 끝 감상 구간은 info) ④오디오(silencedetect 무음>2s, volumedetect 클리핑>-0.5dB, 전체 무음 FAIL)
    ⑤규격(해상도 1920×1080|1080×1920, 30fps, h264/aac, 쇼츠>180s FAIL) ⑥레터박스 밴드(info/WARN)
  - 씬 경계: `--props` 주면 정확 판정, 없으면 순백 근접 프레임(밝기>기준)으로 추정
- **`bin/audit.py <video.mp4> [--props ...] [--out dir]`** — 산출: audit-report.md(사람) + audit-report.json(기계)
  + evidence/*.png(문제 지점 전후 프레임) + FIELD-LOG 초안 스니펫 + exit code(0 PASS / 1 FAIL)
- **성능 목표**: 600초 영상 전체 스캔 ≤ 2분
- **회귀 fixture 게이트** (자기 실증):
  - `output/city-watercolor-600s-final.mp4`(수정 전) → **FAIL** — 경계 하드컷 다수 + f556 부근 스파이크 검출
  - `output/city-watercolor-600s-fixed.mp4` → **PASS** (경계 ≤5.3%)
  - `output/shorts-healing.mp4` → PASS + 쇼츠 규격 / `output/pen-sync-demo.mp4` → PASS
- **Phase 3 (메인 세션)**: `skill/video-auditor/SKILL.md`(7번째 스킬, 코드 0) + install + build.py `--audit` 선택 옵션

## 제외 범위

- 내용·미적 품질 판단(스킬 워크플로에서 Claude가 스틸 보고 수행), 자막-오디오 싱크 검사(후속)
- 검출기 신규 의존성(scdet 등 외부 라이브러리) 추가 금지 — ffmpeg+numpy로 완결

## 참조 문서

- [이전 개발 계획](implement_20260711_215659_shorts.md) — shorts (완료)
- FIELD-LOG.md 2·3번 항목 — 하드컷·스파이크 실측 사례 (이 도구의 존재 이유)

## 공통 진행 규칙

- 체크박스 실측 갱신, 범위 확장 금지. 기존 pytest 93·vitest 29·골든 무영향(렌더러·파이프라인 본선 무수정).

## Phase 상태 요약

- [x] Phase 1 완료 (코어 스캐너 + fixture 게이트)
- [x] Phase 2 완료 (오디오·리포트·exit code)
- [x] Phase 3 완료 (스킬 편입) — 2026-07-12

## QA 관점

- [x] fixture 4종 기대 결과 일치 — final FAIL(경계 하드컷 55 FAIL 10.1~30.5% + f575 develop 스파이크 2.70% FAIL: 어제 수동 발견 2건 재발견) / fixed PASS / shorts PASS / pen PASS
- [x] 600s 스캔 소요 실측 ≤ 2분: final 38.6s(props 없이)·56.1s(props) / fixed 74.2s — 전부 2분 미만
- [x] props 없이(경계 추정)도 city 원본의 하드컷을 검출 — FAIL 59 (하드컷은 hardcut/spike 분류로 검출, exit 1)
- [x] 오탐: fixed FAIL 0(WARN 2: 어두운 씬 경계 6.3/7.1%) · shorts FAIL 0(WARN 2: 1.5% 언저리 transient) · pen FAIL 0(WARN 1: 씬 중간 4.1s 정지 — 스펙 규칙대로)
- [x] audit.py가 brushvid 타 모듈 import 0 (grep: `from .|from brushvid|import brushvid` 0건, 의존 = stdlib+numpy+PIL+ffmpeg)

## Phase 1. 코어 스캐너

### 구현 태스크
- [x] audit.py: 2-패스 스캔 + 경계/스파이크/정지/규격/레터박스 검출
- [x] bin/audit.py CLI (--props/--out)
- [x] pytest: 합성 클립 fixture(하드컷/스파이크/정지/무음 mp4 생성) + 임계 로직 단위 (16건)

### 자체 테스트
- [x] 회귀 fixture 4종 기대 일치 + 성능 실측(600s ≤ 75s) + pytest 전체 109 passed (기존 93 회귀 0)

### 이슈 및 수정
- [x] 이슈 1: ffmpeg 입력 시킹 시작 프레임이 컨테이너에 따라 ±1~2 흔들려 2-패스 재측정이 0% 오측 →
      후보 중심 ±4 윈도우를 한 번에 뽑아 "윈도우 내 최대 연속 diff"로 정렬 불요 측정으로 재설계.
- [x] 이슈 2: fixed 영상의 outro 워시 온셋(씬 끝 직전 1프레임 6~10% 점프, 같은 구도)이 스파이크
      오탐(FAIL 59) → 후보를 transient(번쩍 후 복귀)/워시(corr≥0.9 구도 유지)/하드컷(구도 변화)
      3분류로 정교화: 씬 끝 워시 온셋은 INFO, 결함 스파이크·하드컷만 WARN/FAIL. fixed PASS 회복.

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 2. 오디오·리포트

### 구현 태스크
- [x] 오디오 검사 3종(silencedetect>2s WARN·클리핑>-0.5dB WARN·전체무음 FAIL) + report.md/json
      + evidence 스틸(diff 최대 쌍 자동 선별) + FIELD-LOG 초안 + exit code(0/1)
- [x] pytest: 무음/클리핑 합성 오디오 케이스 (wav 합성 + aac mux 통합 2건 + 순수 규칙 2건)

### 자체 테스트
- [x] city 원본 리포트 실물 — data/audit/city-watercolor-600s-final-props/audit-report.md:
      경계 하드컷 55 FAIL(10.1~30.5%, 타임스탬프 mm:ss) + f575(00:19.2) develop 스파이크 2.70% FAIL,
      evidence/*.png 전후 스틸 8쌍 포함 (어제 수동 발견 2건 모두 자동 재발견)

### 이슈 및 수정
- [x] 발견 이슈 없음 (Phase 1 이슈 2건 외 추가 없음)

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 다음 Phase 진행 가능

## Phase 3. 스킬 편입 (메인 세션)

### 구현 태스크
- [x] skill/video-auditor/SKILL.md (7번째 스킬 — 실행·임계표·리포트 해석·FIELD-LOG 환류 절차) + install (symlink)
- [x] build.py `--audit` 선택 옵션 — shorts-healing으로 통합 검증 (PASS·exit 0)

### 자체 테스트
- [x] 스킬 실행 코드 0건(실측) + symlink + 독립 실행 E2E(shorts-healing props 없이 PASS·리포트/증거/FIELD-LOG 초안 확인)

### 이슈 및 수정
- [x] Phase 3 검증 중 발견: sync 기능 도입 전 구 캐시 프로젝트(pen-sketch-demo)를 `--from qa`로 재실행하면 zones.json 부재로 크래시 → 명확한 안내 에러(`--from routes`로 재생성)로 보강

### 완료 조건
- [x] 구현 완료 / 자체 테스트 완료 / 커밋
