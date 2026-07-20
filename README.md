<div align="center">

# 🖌️ brush_remotion_video

[![Remotion](https://img.shields.io/badge/Remotion-4.0.435-0B84F3?logo=remotion&logoColor=white)](https://www.remotion.dev/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](pipeline/README.md)
[![Zod Schema](https://img.shields.io/badge/schema-v1_(Zod)-8A2BE2?logo=zod&logoColor=white)](src/schema.ts)
[![Tests](https://img.shields.io/badge/tests-pytest_312_%C2%B7_vitest_50-2EA44F?logo=githubactions&logoColor=white)](#-검증)
[![CI](https://github.com/coreline-ai/brush-remotion-video/actions/workflows/ci.yml/badge.svg)](https://github.com/coreline-ai/brush-remotion-video/actions/workflows/ci.yml)
[![Skills](https://img.shields.io/badge/skills-11_installed-FF8C00)](#-스킬-카탈로그)

**화이트 종이 위에 붓/펜이 그림을 그려가는 영상을 `project.yaml` 하나로 자동 생성하는 독립 시스템**

new-video-gen을 이식한 것이 아니라 스펙 참고만 하여 **완전히 새로 만든** 프로젝트 —
최종 산출물은 코드 사본 0의 **얇은 스킬**들이며, 이 리포가 유일한 소스다 (드리프트 방지 제1원칙)

[스킬 카탈로그](#-스킬-카탈로그) · [설치](#-설치) · [Quick Start](#-quick-start) · [구조](#-프로젝트-구조) · [검증](#-검증)

</div>

---

## Overview

SRT 자막·음성·대본, 또는 아무 입력 없이도(앰비언트) 배경 생성부터 붓 경로 추출, 씬/자막 구성,
렌더, 오디오 mux, QA까지 **한 명령**으로 완성 mp4를 만든다.

```text
              ┌─────────────────────────── bin/build.py (스테이지 캐시 + --from 재개) ───────────────────────────┐
project.yaml ─▶ stt ─▶ cues ─▶ background ─▶ clean ─▶ routes ─▶ sync ─▶ layout ─▶ props ─▶ render ─▶ mix ─▶ mux ─▶ qa
              │ TTS/    자막    imagegen/     잉크     스켈레톤+   내레이션  세이프존   Zod v1    Remotion  오디오  콘택트
              │ whisper  프레임  preset/유저   분리     매크로 존   동기      검증      검증      렌더      음량/덕킹 결합    시트
              └──────────────────────────────────────────────────────────────────▶ output/{projectId}.mp4
```

| 특성 | 내용 |
| --- | --- |
| 단일 진실 | [src/schema.ts](src/schema.ts) — Zod 스키마 v1이 render-props의 유일한 정의 (JSON Schema로 일방향 내보내기) |
| 프로파일 | `brush`(수묵 리빌) \| `pen`(잉크 스케치) \| `pen-brush`(외곽선→채색) \| `dark-random-brush`(다크 랜덤 터치, runtime 호환키 `cosmic-random-brush`) — 엔진 공유 |
| 포맷 | `format: youtube`(1920×1080) \| `shorts`(1080×1920, 훅·루프 엔딩 자동) |
| 오디오 모드 | 내레이션 · whisper · TTS(여성팩 `female-01`~`female-10`, F1~F5/M1~M5 호환) · 앰비언트 + BGM `off|synth|asset|playlist|piano-auto` |
| 품질 게이트 | 골든 픽셀 diff ≤ 2% + video-auditor 경계/빠른 spike/느린 완료 pulse/LUFS/True Peak/라이선스 검수 + FIELD-LOG 환류 |

---

## 📦 스킬 카탈로그

모든 스킬은 **코드를 내장하지 않는 얇은 스킬**이다 — 실행은 전부 이 리포의 `bin/build.py`·`bin/audit.py`가 담당하고,
스킬은 symlink로 설치되어 리포 수정이 즉시 반영된다. 새 스킬은 `skill/catalog.json`에 등록하고 생성기를 실행한다. 아래 표는 catalog에서 자동 생성되며 직접 편집하지 않는다.

<!-- BEGIN GENERATED SKILL CATALOG -->
| 스킬 | 구분 | 역할 | 진입점 | 상태 |
| --- | --- | --- | --- | --- |
| [brush-director](skill/director/SKILL.md) | 설계 | 일반 영상 요청과 일상적인 카메라 표현을 전문 연출 브리프·한/영 Camera Prompt Pack·project.yaml 초안으로 변환하며 직접 렌더하지 않습니다. | `conversation -> brief + optional camera prompt pack + project.yaml draft` | 정식 v1.1.0 |
| [brush-video](skill/brush-video/SKILL.md) | 제작 | 수묵·수채 이미지를 붓이 그려 완성하는 내레이션·TTS·앰비언트 영상을 제작하며, 무음 15~120초에는 Stable Audio 피아노 BGM을 우선 시도합니다. | `bin/build.py` | 정식 v1.0.0 |
| [full-color-motion-video](skill/full-color-motion-video/SKILL.md) | 제작 | 원본 색상을 보존한 정지 이미지에 2D 모션·환경 효과·전환·오디오를 연결하고, 무음 영상에는 Stable Audio 피아노 BGM 우선 정책을 적용합니다. | `bin/build.py` | 정식 v1.0.0 |
| [pen-video](skill/pen-video/SKILL.md) | 제작 | 원본을 자르지 않고 얇고 정교한 펜 윤곽선을 순차적으로 그리는 영상을 제작하며, 음성 없는 영상은 Stable Audio 피아노를 우선 시도합니다. | `bin/build.py` | 정식 v1.0.0 |
| [pen-brush-video](skill/pen-brush-video/SKILL.md) | 제작 | 펜으로 샤프한 외곽선을 먼저 완성한 뒤 브러시로 색을 채우며, 무음 영상에는 분위기 기반 Stable Audio 피아노를 우선 연결합니다. | `bin/build.py` | 정식 v1.0.0 |
| [shorts-brush](skill/shorts-brush/SKILL.md) | 제작 | 1080×1920 세로 화면에서 훅·세이프존·루프 엔딩을 적용하고, 15~120초 무음 구간에는 Stable Audio 피아노 BGM을 우선 시도합니다. | `bin/build.py` | 정식 v1.0.0 |
| [dark-random-brush-video](skill/dark-random-brush-video/SKILL.md) | 제작 | 우주·심해·야간 등 어두운 16:9 이미지를 자유 랜덤 붓 터치로 드러내며, 무음 영상에는 어두운 분위기의 Stable Audio 피아노를 우선 시도합니다. | `bin/build.py` | 전문화 v0.3.0 |
| [storybook-full-touch-video](skill/storybook-full-touch-video/SKILL.md) | 제작 | 동화 이미지·씬별 TTS·자막·BGM과 펜 외곽선→브러시 채색을 통합하며, TTS 영상은 명시적 piano-auto일 때만 Stable Audio를 생성합니다. | `scripts/prepare-storybook-full-touch.py + bin/build.py` | 전문화 v0.1.0 |
| [seamless-short-video](skill/seamless-short-video/SKILL.md) | 제작 | 이전 씬 말미 ~2초 동작 연속(정본)과 Last Frame·Multi-Signal Handoff로 캐릭터·동작이 이어지는 연속형 숏폼 I2V를 반자동 제작합니다. Remotion 붓 라인과 독립. | `bin/seamless-short.py` | 정식 v1.0.0 |
| [brush-qa-review](skill/qa-review/SKILL.md) | QA | 파이프라인의 씬 캡처와 capture manifest를 검토해 수정 요청과 재빌드 시작점을 제시합니다. | `bin/qa.py` | 정식 v1.0.0 |
| [video-auditor](skill/video-auditor/SKILL.md) | 감사 | 완성 MP4의 하드컷·번쩍임·정지·무음·클리핑·음량·규격을 독립적으로 검사합니다. | `bin/audit.py` | 정식 v1.0.0 |
| [piano-bgm](skill/piano-bgm/SKILL.md) | 제작 | Stable Audio 3 MLX를 1순위로 시네마틱·웅장한 피아노 BGM 생성 후보를 만들고, 로컬 샘플 score fallback과 라이선스·provenance·사람 청취 gate까지 검증합니다. | `bin/piano-bgm.py generate/build (Stable Audio 3 MLX 또는 sample-score)` | 전문화 v0.2.0 |
| [promo-widget-video](skill/promo-widget-video/SKILL.md) | 제작 | KIMI-K3 분석에서 자산화한 다크 프로모 위젯 31종(게이지·바·리더보드·카운트업·데이터 패널·UI 크롬·배지)으로 위젯 씬 시퀀스를 props JSON 하나로 조립·렌더합니다. 붓/펜 라인과 독립. | `src/promo/PromoWidgetGallery.tsx` | 전문화 v0.1.0 |
<!-- END GENERATED SKILL CATALOG -->

### 스킬 조합 워크플로

```text
사용자 요청 ─▶ brush-director ─▶ brush-video / pen-video / pen-brush-video / dark-random-brush-video / shorts-brush ─▶ video-auditor ─▶ 업로드
              (브리프·yaml 번역)   (빌드: project.yaml → mp4)              (자동 검수)
                                        │                                      │ FAIL
                                        ◀── brush-qa-review (씬별 수정) ◀──────┘

동화 요청 ───▶ storybook-full-touch-video ─▶ 종이 정규화·씬 고정 TTS ─▶ pen-brush 렌더 ─▶ video-auditor
              (시나리오·SRT·이미지 계약)    (1이미지=1씬)          (가로/세로)       (FAIL 0 필수)
```

### brush-director — Camera Prompt Interpreter

- 촬영 용어를 모르는 사용자의 `뒤에서 따라가 줘`, `웅장하게 멀어져 줘`, `문을 통과해 이어 줘` 같은
  표현을 37개 canonical 기법과 9개 legacy alias 중 하나로 정규화한다.
- 출력은 연출 브리프 → 선택적 Camera Prompt Pack → 실행 가능한 `project.yaml` 초안 → 확인 질문 최대 2개 순서다.
- Camera Prompt Pack에는 필수 슬롯, 전문 한/영 prompt, negative prompt, `remotionStill`/`aiVideo`/
  `imageGeneration`/`sceneTransition` 호환성이 포함된다.
- Camera Prompt Pack은 전문 브리프이지 render props가 아니다. 미지원 `camera:`/`cameraMotion:`을
  `project.yaml`에 넣지 않으며 true orbit·tracking·FPV 등은 `external-required`로 정직하게 표시한다.

```text
사용자: "숲길을 걷는 아이 뒤에서 어깨 너머로 따라가 줘"
해석: follow-over-shoulder (19), forward, subject-matched, close-follow, clarification=false
KO: 아이의 뒤쪽 어깨 너머 구도를 유지하며 걷는 속도에 맞춰 일정한 거리로 부드럽게 따라간다.
EN: Follow the child smoothly from behind in an over-the-shoulder framing at a matched pace and constant distance.
호환성: remotionStill=external-required, aiVideo=supported, imageGeneration=composition-only
```

[해석 지도](skill/director/references/camera-intent-map.md) ·
[프롬프트 조립 가이드](skill/_shared/references/camera-prompt-guide.md) ·
[대표 예시 12건](skill/director/references/camera-prompt-examples.md)

```bash
python3 bin/camera-prompt-catalog.py validate
python3 bin/camera-prompt-catalog.py list
python3 bin/camera-prompt-catalog.py check
```

### brush-video — 수묵 붓 리빌 (기본 스킬)

- **입력**: `project.yaml` 하나 — SRT/음성이 있으면 내레이션, 대본만 있으면 TTS, 없으면 앰비언트. BGM은 별도 `bgm` 블록
- **TTS 엔진**: 기존 Supertonic과 `melo-ko`, `qwen3-base` 선택 가능 — [공통 카탈로그](skill/_shared/references/tts-engine-catalog.md)
- **TTS 음성팩**: Supertonic 여성 10종 조회·청취·검증 `python3 bin/voice-assets.py validate` — [선택표](skill/_shared/references/supertonic-voice-catalog.md)
- **배경 전략**: `imagegen`(codex 내장, API 키 불필요) · `preset`(PIL 결정적 합성) · `user-images`(contain-fit)
- **위젯**: 씬 여백에 카드 위젯 15종 (`widgets: authored`) — [카탈로그](skill/brush-video/references/widget-catalog.md)
- **내레이션 동기**: 매크로 존(오브젝트) 단위 드로잉 순서 + 자막 큐와 질량 비례 동기 (`sync` 스테이지 자동)
- **BGM**: 무음 15~120초는 Stable Audio 피아노 후보를 1순위로 시도하고, 실패 시 기존 catalog/synth로 fallback. 음성 영상은 명시적 `piano-auto`에서만 생성하며 -23 LUFS·덕킹·승인 gate를 적용한다 — [정책](skill/_shared/references/bgm-policy.md)
- **YouTube 배포 금지**: Pixabay 음원은 YouTube 일반 영상·Shorts 제작/교체/배포에 사용하지 않으며 preflight에서 차단한다. 로컬 청취·내부 데모·과거 검증용으로만 보존한다.
- **완료 연출**: 일반 가로 brush는 `integrated-develop` 단일 레이어 + 밝기 고정·채도 정착 + phase-aware QA가 기본

### pen-video — 펜 스케치 (프로파일 스킬)

- `drawing.profile: pen` 한 줄로 잉크-알파 분리(종이는 항상 보이고 잉크만 점진 드로잉)·정밀 경로·펜 커서·프리셋 자동 적용
- 붓의 수묵 리빌과 구별되는 빠른 템포 — drawEnd 35%로 앞당겨 감상 구간 확보

### pen-brush-video — 외곽선 후 채색 (프로파일 스킬)

- `drawing.profile: pen-brush` 한 줄로 원본에서 얇은 outline/color 레이어와 2종 routes를 자동 생성
- outline 38% → handoff 8f → paint 88% → 최종 원본선 복원. 고정 좌표 없이 가로·세로 지원
- QA 수치 계약: outline ≥99%, paint ≥99.99%, missing 0, 색 누출/커서 겹침 0
- 실물 예제: `examples/pen-brush/`, `examples/pen-brush-shorts/`

### storybook-full-touch-video — 동화 풀터칭 영상 (오케스트레이션 스킬)

- 주제·교훈에서 시나리오, `narration.txt`, SRT, 장면별 이미지 계약, Supertonic 음성, 최종 MP4까지 한 흐름으로 제작한다.
- 새 기본 프리셋은 **10씬×10초=100초**, Shorts 1080×1920, 씬당 이미지 1장·문장 cue 2개, Supertonic `female-08`이다. 기존 F1 예제는 호환된다.
- `scripts/normalize-storybook-paper.py`가 외곽 연결 종이를 중성 웜화이트로 정규화하고,
  `scripts/prepare-storybook-full-touch.py`가 장면별 음성을 고정 길이 블록으로 합성한다.
- 렌더러를 복사하지 않고 `drawing.profile: pen-brush`, `format: shorts|youtube`, `bin/build.py --audit`를 사용한다.
- 완료 기준은 outline ≥99%, paint ≥99.99%, missing 0, 경계 diff <6%, video-auditor FAIL 0이다.
- 검증 예제: `projects/star-seed-fairy-tale-100s/` → `output/star-seed-fairy-tale-100s.mp4` (100.000초·3,000f·audit PASS).

### dark-random-brush-video — 다크 랜덤 터치 (프로파일 스킬)

- `drawing.profile: dark-random-brush`로 우주·심해·야간 풍경에 의미 윤곽을 따라가지 않는 자유 랜덤 터치를 생성한다.
- 기존 project와 golden은 `cosmic-random-brush` runtime key로 계속 호환된다.
- 기본 36터치 뒤 같은 붓 폭(230~365px)의 보완 터치만 추가해 마스크 커버리지 99.1% 이상을 달성한다.
- v0.3은 YouTube 1920×1080·30fps에서 1씬 골든, 대표 6씬(60초), 본편 60씬(600초)을 지원한다.
- 60씬 실물 예제는 `examples/cosmic-random-brush-v03/`, 결과는 `output/cosmic-random-brush-v03-60.mp4`다.
- 60씬 QA는 최종 MP4에서 씬별 3프레임을 배치 추출하며 source/credit/hash는 assets manifest에 기록한다.
- QA는 붓 폭, 기본/보완 터치 수, 전체 coverage, 가시 콘텐츠 coverage, 이동 거리, 결정성을 hard gate로 검사한다.

### shorts-brush — 세로 힐링 쇼츠 (프로파일 스킬)

- `format: shorts` 하나로 배경·경로·레이아웃 전체가 세로(1080×1920) 동작
- 첫 씬 훅(짧은 프리워시), 씬 전환 outro 페이드, 순백 수렴 루프 엔딩 자동 — 기본 3씬×10초, 쇼츠 한도 180초

### brush-qa-review / video-auditor — 품질 게이트 2종

| | brush-qa-review | video-auditor |
| --- | --- | --- |
| 판단 주체 | 사람 눈 (씬별 연출 리뷰) | 수치 (자동 결함 검출) |
| 입력 | `data/{pid}/qa/` 캡처 + manifest | **mp4 하나** (props 불필요, 외부 영상도 가능) |
| 산출 | scene-fix-request JSON → 재빌드 | PASS/FAIL 리포트 + 증거 스틸 + FIELD-LOG 초안 |
| 자동화 | — | `bin/build.py <yaml> --audit` (exit code 게이트) |

### 새 스킬 추가 체크리스트

1. `skill/{이름}/SKILL.md` 작성 (필요 시 `references/` 동봉) — 코드 내장 금지, 실행은 리포 진입점 참조
2. [skill/catalog.json](skill/catalog.json)에 등록하고 `python3 bin/skill-catalog.py generate-readme` 실행
3. `agents/openai.yaml` 생성 후 `python3 bin/skill-catalog.py check`와 installer `--check` 실행
4. 실전 제작에서 발견한 갭은 [FIELD-LOG.md](FIELD-LOG.md)에 환류 (발견→수정→문서/검증기 반영 필수)

---

## 📋 요구사항

| 도구 | 용도 |
| --- | --- |
| Node.js + npm | Remotion 렌더 (`npm install` 선행) |
| Python 3.11 + venv | 파이프라인 (`pipeline/.venv`) |
| ffmpeg / ffprobe | 오디오 mux · QA 캡처 · 검수 |
| (선택) codex CLI | `strategy: imagegen` 배경 생성 |
| (선택) faster-whisper / TTS 엔진 | whisper 전사 / TTS 더빙 — [pipeline/README.md](pipeline/README.md)·[엔진 카탈로그](skill/_shared/references/tts-engine-catalog.md) 참조 |

---

## 🚀 설치

```bash
# 1. 의존성
npm install
python3 -m venv pipeline/.venv && pipeline/.venv/bin/pip install -e "pipeline[dev]"

# 2. 기존 호환 기본값: Claude에 symlink 설치
bin/install-skills.sh

# Codex 또는 양쪽에 설치
bin/install-skills.sh --target codex
bin/install-skills.sh --target all

# 실제 변경 전 확인 / 설치 상태 검사
bin/install-skills.sh --target all --dry-run
bin/install-skills.sh --target all --check
```

---

## ⚡ Quick Start

```bash
# 빌드 — 이것 하나로 영상 완성
python3 bin/build.py examples/ambient/project.yaml
# → output/ambient-demo.mp4 + data/ambient-demo/qa/ (씬 캡처·콘택트시트)

# 실패 지점부터 재개 (스테이지 캐시)
python3 bin/build.py examples/ambient/project.yaml --from render

# 빌드 + 자동 검수 게이트 (FAIL 시 exit 1)
python3 bin/build.py examples/ambient/project.yaml --audit

# 공개 Git tree 자산·self-contained 예제·문서 링크 검사
python3 scripts/check-public-tree.py

# 외부 BGM은 공식 다운로드 후 로컬 등록·검증
python3 bin/bgm-assets.py sources
python3 bin/bgm-assets.py scan --attach  # ~/Downloads 자동 탐색 + 단일 일치 곡 일괄 등록
python3 bin/bgm-assets.py status
python3 bin/bgm-assets.py dashboard  # 진행도·공식 링크·등록 후 로컬 청취 플레이어
python3 bin/bgm-assets.py review     # 검증 영상·이어폰/스피커 승인·JSON 내보내기
# 내보낸 JSON의 5개 항목·2개 환경이 모두 승인인지 검증해 로컬 근거로 기록
python3 bin/bgm-assets.py review --import-result ~/Downloads/bgm-listening-review.json
python3 bin/bgm-assets.py gate       # 14곡 + 필수 E2E 4종 + 라이선스 + 사람 승인 최종 판정
# Supertonic 여성 음성팩 조회·청취·검증
python3 bin/voice-assets.py list
python3 bin/voice-assets.py preview female-09
python3 bin/voice-assets.py validate
# 등록 완료 뒤: 영상 재렌더 없이 BGM만 재믹스
python3 bin/build.py examples/pen-brush-bgm/project.yaml --from mix --audit

# project.yaml이 없는 대사 없는 완성 MP4의 BGM만 교체(영상 stream-copy)
python3 bin/replace-bgm.py --video output/input.mp4 --project-id demo \
  --asset-id youtube-chris-zabriskie-fight-for-your-honor \
  --out output/demo-bgm.mp4 --title "공개 제목" --confirm-no-voice

# 완성본만 따로 검수 (어떤 mp4든)
pipeline/.venv/bin/python bin/audit.py output/ambient-demo.mp4
```

`examples/`에는 기존 10종과 로컬 BGM 4종(`ambient-bgm` `narration-bgm` `pen-brush-bgm` `long-bgm-playlist`)이 있다.
대용량 원본 이미지가 별도로 필요한 장편 예제는 [로컬 전용 예제 에셋 안내](examples/LOCAL_ASSETS.md)를 따른다.

---

## 📁 프로젝트 구조

```text
brush_remotion_video/
├── src/
│   ├── schema.ts            # ★ Zod 스키마 v1 — 유일한 진실 (npm run export-schema)
│   ├── scene/               # BrushScene(조립) + Reveal·Cursor·Subtitle·Title·Effect·Widget 레이어
│   ├── lib/                 # geometry·dynamics·easing — 순수 함수 (단위 테스트 대상)
│   └── widgets/             # 단일 registry 15종 (CardShell + 파일당 1바디)
├── pipeline/brushvid/       # routes·background·props·render·stt·tts·bgm·mix·audit·qa
├── bin/
│   ├── build.py             # ★ 단일 진입점 (스테이지 캐시 + --from 재개 + --audit)
│   ├── audit.py             # 독립 검수 CLI (mp4 + 선택적 BGM license manifest)
│   ├── bgm-assets.py        # 로컬 음원 scan/import/attach/status/verify/dashboard
│   ├── voice-assets.py      # Supertonic 여성 음성팩 list/show/preview/demo/validate
│   ├── replace-bgm.py       # 대사 없는 완성 MP4의 catalog BGM 교체·감사·delivery
│   ├── qa.py                # 씬 캡처·콘택트시트·갤러리
│   └── install-skills.sh    # 스킬 symlink 설치
├── skill/                   # catalog + 공통 계약 + 얇은 스킬 11종 (코드 사본 0)
├── examples/                # 기존 모드 + 로컬 BGM project.yaml 예제
├── tests/                   # vitest 50건 + golden/ 픽셀 diff 게이트
├── docs/                    # schema.md · pipeline.md · impl-plan (전체 설계)
├── dev-plan/                # 워크스트림별 진행 기록 (implement_YYYYMMDD_HHMMSS.md)
└── FIELD-LOG.md             # 실전 제작 갭 환류 기록 (발견→수정→환류 필수)
```

---

## ✅ 검증

```bash
npm run check-schema && npm run typecheck && npm test  # schema sync + tsc + vitest 50건
pipeline/.venv/bin/pytest pipeline/tests/              # Python: 312건
python3 bin/skill-catalog.py check                      # catalog/schema/README/agents 10/10
python3 bin/camera-prompt-catalog.py check              # canonical 37/alias 9/fixture 96/docs
python3 scripts/check-public-tree.py                     # 공개 자산/예제/문서 fresh-tree 계약
npx remotion render src/index.ts BrushLandscape output/golden-single.mp4 --props=data/golden-single/props.json
python3 tests/golden/diff.py --baseline tests/golden/baseline --candidate <스틸 폴더>
```

| 게이트 | 기준 | 실측 |
| --- | --- | --- |
| 골든 스틸 픽셀 diff | ≤ 2% | 0.06~0.17% (기준 갱신은 `diff.py --update`로만) |
| 렌더 재현성 | 동일 프레임 2회 렌더 diff 0% | 0.0000% |
| video-auditor | 씬 경계 하드컷 ≤ 10%, 번쩍 스파이크 ≤ 2.5% | 실전 결함(하드컷 55곳·번쩍 1곳) 재발견 검증 |

---

## 📖 문서

| 문서 | 내용 |
| --- | --- |
| [docs/schema.md](docs/schema.md) | render-props v1 / routes JSON 스키마 |
| [docs/pipeline.md](docs/pipeline.md) | 빌드 스테이지와 모드 |
| [docs/seamless-short-video/](docs/seamless-short-video/README.md) | Last Frame Handoff 숏폼 스킬 설계·QA·파일럿 교훈 (SSOT) |
| [docs/impl-plan-brush-remotion-video.md](docs/impl-plan-brush-remotion-video.md) | 전체 설계 (Phase 0~6) |
| [dev-plan/](dev-plan/) | 워크스트림별 진행 기록 — 새 워크스트림마다 `implement_YYYYMMDD_HHMMSS.md` 추가 |
| [FIELD-LOG.md](FIELD-LOG.md) | 실전 제작 갭 환류 기록 |
| [CHANGELOG.md](CHANGELOG.md) | 사용자 영향 변경과 릴리스 게이트 |
| [pipeline/README.md](pipeline/README.md) | Python venv 부트스트랩 · whisper/TTS 설치 |
| [skill/_shared/references/tts-engine-catalog.md](skill/_shared/references/tts-engine-catalog.md) | Supertonic·Melo·Qwen 선택, 설치, reference, manifest 계약 |
| [scripts/tts-doctor.py](scripts/tts-doctor.py) | TTS 오프라인 점검과 명시적 engine prepare |

---

## ⚖️ 라이선스

> **이 프로젝트의 사용·복제·배포·상업적 활용은 반드시 `coreline-ai`와의 사전 협의를 거쳐 진행되어야 합니다.**

- 본 리포지토리(코드·스킬·파이프라인·문서 일체)의 저작권은 **coreline-ai**에 있습니다.
- 개인·상업·재배포 여부와 무관하게, 사용 전 **coreline-ai와 라이선스 조건을 협의**하고 서면 합의를 받아야 합니다.
- 협의 없이 이루어진 사용·수정·배포는 허가되지 않습니다.
- 파생물(생성 영상 포함)의 활용 범위 역시 coreline-ai와의 협의 대상입니다.
- 제3자 에셋(예: Pixabay·YouTube 오디오 보관함 BGM, Supertonic TTS)은 각 공급자의 라이선스가 별도로 적용되며,
  본 협의는 이를 대체하지 않습니다 — 자세한 내용은 [BGM 정책](skill/brush-video/references/bgm-policy.md) 참조.

**문의·협의**: `coreline-ai`

전체 조건은 [LICENSE](LICENSE), 포함된 외부 구성요소와 에셋 고지는
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 확인하세요.
