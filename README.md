<div align="center">

# 🖌️ brush_remotion_video

[![Remotion](https://img.shields.io/badge/Remotion-4.0.435-0B84F3?logo=remotion&logoColor=white)](https://www.remotion.dev/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](pipeline/README.md)
[![Zod Schema](https://img.shields.io/badge/schema-v1_(Zod)-8A2BE2?logo=zod&logoColor=white)](src/schema.ts)
[![Tests](https://img.shields.io/badge/tests-pytest_109_%C2%B7_vitest_30-2EA44F?logo=githubactions&logoColor=white)](#-검증)
[![Skills](https://img.shields.io/badge/skills-6_installed-FF8C00)](#-스킬-카탈로그)

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
project.yaml ─▶ stt ─▶ cues ─▶ background ─▶ clean ─▶ routes ─▶ sync ─▶ layout ─▶ props ─▶ render ─▶ mux ─▶ qa
              │ TTS/    자막    imagegen/     잉크     스켈레톤+   내레이션  세이프존   Zod v1    Remotion  오디오  콘택트
              │ whisper  프레임  preset/유저   분리     매크로 존   동기      검증      검증      렌더      결합    시트
              └──────────────────────────────────────────────────────────────────▶ output/{projectId}.mp4
```

| 특성 | 내용 |
| --- | --- |
| 단일 진실 | [src/schema.ts](src/schema.ts) — Zod 스키마 v1이 render-props의 유일한 정의 (JSON Schema로 일방향 내보내기) |
| 프로파일 | `drawing.profile: brush`(수묵 리빌) \| `pen`(잉크-알파 분리 스케치) — 엔진 공유, 프리셋만 분기 |
| 포맷 | `format: youtube`(1920×1080) \| `shorts`(1080×1920, 훅·루프 엔딩 자동) |
| 오디오 모드 | 내레이션(SRT+음성) · whisper(음성→SRT 전사) · TTS(자막/대본만으로 Supertonic 더빙 합성) · 앰비언트(합성 BGM) |
| 품질 게이트 | 골든 픽셀 diff ≤ 2%(실측 0.06~0.17%) + video-auditor 자동 검수(`--audit`) + FIELD-LOG 환류 |

---

## 📦 스킬 카탈로그

모든 스킬은 **코드를 내장하지 않는 얇은 스킬**이다 — 실행은 전부 이 리포의 `bin/build.py`·`bin/audit.py`가 담당하고,
스킬은 symlink로 설치되어 리포 수정이 즉시 반영된다. 새 스킬은 아래 표에 행 하나 + 상세 소절 하나로 추가한다.

| 스킬 | 역할 | 진입점 | 상태 |
| --- | --- | --- | --- |
| [brush-director](skill/director/SKILL.md) | 일반 요청("잔잔한 겨울밤 쇼츠") → 전문 연출 브리프·project.yaml 번역 (실행 없음, 앞단) | 대화 → yaml 초안 | ✅ 설치됨 |
| [brush-video](skill/brush-video/SKILL.md) | 수묵 붓 리빌 영상 생성 — 내레이션·TTS·앰비언트 모드 | `bin/build.py` | ✅ 설치됨 |
| [pen-video](skill/pen-video/SKILL.md) | 펜 윤곽 스케치 영상 — 잉크-알파 분리, 빠른 템포 설명형 | `bin/build.py` (`profile: pen`) | ✅ 설치됨 |
| [shorts-brush](skill/shorts-brush/SKILL.md) | 세로 풀블리드 힐링 쇼츠(1080×1920) — 훅·루프 친화 엔딩 | `bin/build.py` (`format: shorts`) | ✅ 설치됨 |
| [brush-qa-review](skill/qa-review/SKILL.md) | 씬별 QA 리뷰 → scene-fix-request JSON → 스테이지 재빌드 | `bin/qa.py` | ✅ 설치됨 |
| [video-auditor](skill/video-auditor/SKILL.md) | mp4 하나만으로 하드컷·번쩍·무음·규격 자동 검수 (PASS/FAIL + 증거 스틸) | `bin/audit.py` | ✅ 설치됨 |
| pen-brush-video | 채색 페이즈가 있는 펜+브러시 혼합 드로잉 (drawingPhases) | — | 🚧 계획 |

### 스킬 조합 워크플로

```text
사용자 요청 ─▶ brush-director ─▶ brush-video / pen-video / shorts-brush ─▶ video-auditor ─▶ 업로드
              (브리프·yaml 번역)   (빌드: project.yaml → mp4)              (자동 검수)
                                        │                                      │ FAIL
                                        ◀── brush-qa-review (씬별 수정) ◀──────┘
```

### brush-video — 수묵 붓 리빌 (기본 스킬)

- **입력**: `project.yaml` 하나 — SRT/음성이 있으면 내레이션, 대본만 있으면 TTS, 없으면 앰비언트(10초 씬 × N + 합성 BGM)
- **배경 전략**: `imagegen`(codex 내장, API 키 불필요) · `preset`(PIL 결정적 합성) · `user-images`(contain-fit)
- **위젯**: 씬 여백에 카드 위젯 15종 (`widgets: authored`) — [카탈로그](skill/brush-video/references/widget-catalog.md)
- **내레이션 동기**: 매크로 존(오브젝트) 단위 드로잉 순서 + 자막 큐와 질량 비례 동기 (`sync` 스테이지 자동)

### pen-video — 펜 스케치 (프로파일 스킬)

- `drawing.profile: pen` 한 줄로 잉크-알파 분리(종이는 항상 보이고 잉크만 점진 드로잉)·정밀 경로·펜 커서·프리셋 자동 적용
- 붓의 수묵 리빌과 구별되는 빠른 템포 — drawEnd 35%로 앞당겨 감상 구간 확보

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
2. [bin/install-skills.sh](bin/install-skills.sh)에 `install_link` 한 줄 추가 → 재실행
3. 이 README의 **카탈로그 표에 행 1개 + 상세 소절 1개** 추가 (위 소절들과 같은 형식)
4. 실전 제작에서 발견한 갭은 [FIELD-LOG.md](FIELD-LOG.md)에 환류 (발견→수정→문서/검증기 반영 필수)

---

## 📋 요구사항

| 도구 | 용도 |
| --- | --- |
| Node.js + npm | Remotion 렌더 (`npm install` 선행) |
| Python 3.11 + venv | 파이프라인 (`pipeline/.venv`) |
| ffmpeg / ffprobe | 오디오 mux · QA 캡처 · 검수 |
| (선택) codex CLI | `strategy: imagegen` 배경 생성 |
| (선택) faster-whisper / Supertonic | whisper 전사 / TTS 더빙 — [pipeline/README.md](pipeline/README.md) 부트스트랩 참조 |

---

## 🚀 설치

```bash
# 1. 의존성
npm install
python3 -m venv pipeline/.venv && pipeline/.venv/bin/pip install -e "pipeline[dev]"

# 2. 스킬 설치 (~/.claude/skills/ 에 symlink — 사본 아님)
bin/install-skills.sh
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

# 완성본만 따로 검수 (어떤 mp4든)
pipeline/.venv/bin/python bin/audit.py output/ambient-demo.mp4
```

`examples/`에 모드별 실행 예제 8종: `ambient` `narration` `whisper` `tts-script` `single-scene` `pen-sketch` `pen-sync` `shorts-healing`

---

## 📁 프로젝트 구조

```text
brush_remotion_video/
├── src/
│   ├── schema.ts            # ★ Zod 스키마 v1 — 유일한 진실 (npm run export-schema)
│   ├── scene/               # BrushScene(조립) + Reveal·Cursor·Subtitle·Title·Effect·Widget 레이어
│   ├── lib/                 # geometry·dynamics·easing — 순수 함수 (단위 테스트 대상)
│   └── widgets/             # 단일 registry 15종 (CardShell + 파일당 1바디)
├── pipeline/brushvid/       # routes·background·cues·layout·props·render·stt·tts·sync·audit·qa
├── bin/
│   ├── build.py             # ★ 단일 진입점 (스테이지 캐시 + --from 재개 + --audit)
│   ├── audit.py             # 독립 검수 CLI (mp4 하나 입력)
│   ├── qa.py                # 씬 캡처·콘택트시트·갤러리
│   └── install-skills.sh    # 스킬 symlink 설치
├── skill/                   # 얇은 스킬 6종 (코드 사본 0)
├── examples/                # 모드별 project.yaml 예제 8종
├── tests/                   # vitest 30건 + golden/ 픽셀 diff 게이트
├── docs/                    # schema.md · pipeline.md · impl-plan (전체 설계)
├── dev-plan/                # 워크스트림별 진행 기록 (implement_YYYYMMDD_HHMMSS.md)
└── FIELD-LOG.md             # 실전 제작 갭 환류 기록 (발견→수정→환류 필수)
```

---

## ✅ 검증

```bash
npm run typecheck && npm test                      # TS: tsc 에러 0 + vitest 30건
pipeline/.venv/bin/pytest pipeline/tests/          # Python: 109건
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
| [docs/impl-plan-brush-remotion-video.md](docs/impl-plan-brush-remotion-video.md) | 전체 설계 (Phase 0~6) |
| [dev-plan/](dev-plan/) | 워크스트림별 진행 기록 — 새 워크스트림마다 `implement_YYYYMMDD_HHMMSS.md` 추가 |
| [FIELD-LOG.md](FIELD-LOG.md) | 실전 제작 갭 환류 기록 |
| [pipeline/README.md](pipeline/README.md) | Python venv 부트스트랩 · whisper/TTS 설치 |
