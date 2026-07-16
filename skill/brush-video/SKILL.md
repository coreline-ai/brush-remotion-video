---
name: brush-video
description: >-
  화이트 종이 위에 붓이 그림을 그리는(수묵화 리빌) 영상을 자동 생성하는 스킬.
  실행 대상은 brush_remotion_video 리포이며 이 스킬은 코드를 내장하지 않는다 —
  project.yaml 하나를 작성해 bin/build.py를 실행하면 배경 생성 → 붓 경로 추출 →
  씬/자막 구성 → 렌더 → 오디오 mux → QA까지 자동으로 완성 mp4가 나온다.
  내레이션(SRT/음성) · TTS(음성 없이 자막/대본만으로 Supertonic이 더빙 합성) ·
  앰비언트(무입력, 합성 또는 라이선스 증빙된 로컬 BGM) 모드를 지원한다.
  구 brush-draw-reveal 스킬의 후속 (newVideoGen 의존 제거, 완전 독립).
---

# brush-video — 화이트 붓 드로잉 영상 생성

**실행 대상 리포**: `/Volumes/ExternalSSD/projects_7/brush-remotion-video`
이 스킬은 코드를 내장하지 않는다. 리포가 유일한 소스다 (드리프트 방지 제1원칙).

## 워크플로

1. **project.yaml 작성** — 사용자의 요청에서 projectId·포맷·입력·배경 전략을 정리한다.
   전체 필드는 [project.yaml 공통 가이드](../_shared/references/project-yaml-guide.md) 참조.

   ```yaml
   projectId: my-video
   format: youtube            # youtube(16:9) | shorts(9:16)
   input:
     srt: 자막.srt            # 있으면 내레이션 모드
     audio: 더빙.mp3          # srt 없고 audio만 있으면 whisper로 SRT 생성
     script: 대본.txt         # 대본 텍스트 (tts와 함께 사용)
     tts:                     # 음성이 없어도 TTS로 더빙 자동 생성 (아래 "TTS" 섹션)
       engine: supertonic     # melo-ko / qwen3-base도 선택 가능
       voice: female-01       # 여성팩 female-01~10 / 호환 F1~F5·M1~M5
       speed: 1.10
       pauseMs: 350
     # 아무 입력도 없으면 앰비언트 모드 (10초 씬 × N)
   background:
     strategy: imagegen       # imagegen | preset(PIL, 결정적) | user-images
   widgets: none              # none | authored (auto는 준비 중)
   bgm:                       # 선택: off | synth | asset | playlist
     mode: asset
     assetId: youtube-chris-zabriskie-fight-for-your-honor
     gainDb: 5
   ```

2. **빌드 실행** — 리포 루트에서:

   ```bash
   cd /Volumes/ExternalSSD/projects_7/brush-remotion-video
   python3 bin/build.py <project.yaml 경로>
   ```

   - 산출: `output/{projectId}.mp4` + `data/{projectId}/qa/`(캡처·콘택트시트)
   - 스테이지 캐시가 있어 실패 지점부터 재개 가능: `--from <stage>` (stt/cues/background/clean/routes/sync/layout/props/render/mix/mux/qa)

3. **QA 확인** — `data/{projectId}/qa/contact-sheet.png`를 열어 씬별 상태를 확인한다.
   씬별 리뷰·수정요청은 brush-qa-review 스킬로 진행.

4. **수정 반복** — props(`data/{projectId}/props.json`)나 project.yaml을 고친 뒤
   해당 스테이지부터 재실행 (`--from props` 또는 `--from render`).
5. **갭 환류** — 제작 중 발견한 품질 갭·빠진 규칙은 리포 루트 `FIELD-LOG.md`에 기록하고,
   반드시 해당 문서/검증기에 반영해 재발을 막는다 (기록만 하고 끝내지 않기).

## 배경 이미지

- `strategy: imagegen` — codex exec 내장 image_gen (API 키 불필요). 프롬프트 규칙은
  [references/background-prompt.md](references/background-prompt.md) — 흰 종이·잉크+수채·여백 확보·글자 금지.
- `strategy: preset` — PIL 절차 합성 (로컬·시드 결정적). imagegen 불가 환경 폴백.
- `strategy: user-images` — 사용자가 준 이미지를 contain-fit.

## TTS — 음성 없이 자막/대본만으로 더빙 생성 (선택)

`input.tts` 블록이 있으면 실제 더빙 없이도 선택한 로컬 TTS 엔진이 더빙을 합성한다:

- **srt + tts**: SRT의 텍스트를 문장별 합성 — 타이밍은 합성 음성 길이가 시계 (SRT 타이밍은 재계산됨)
- **script + tts**: 대본 텍스트 → 더빙 + SRT 동시 생성
- **srt + audio 동시 제공 시 TTS는 무시** (실제 더빙 우선)
- `melo-ko`는 `voice: kr-default`, `language: ko`와 Melo `KR` speaker를 사용한다.
- `qwen3-base`는 명시적 `reference.audio` + `reference.transcript`가 필수이며 bundled voice fallback을 사용하지 않는다.
- 모든 엔진 출력은 44.1kHz mono로 정규화되고 실제 샘플 길이가 SRT 시계가 된다.
- 실측: 실시간 대비 약 4배 합성 속도(RTF 0.24)
- 여성 음성팩 10종은 [Supertonic 음성 카탈로그](../_shared/references/supertonic-voice-catalog.md)를 따른다.
  brush-video 새 프로젝트 권장은 `female-01`, 기존 `F1`~`F5`·`M1`~`M5`도 호환된다.
- 런타임 `voice:auto`는 쓰지 않는다. 선택한 명시적 ID를 YAML에 기록한다.

**첫 사용 설치 (1회)** — 미설치 상태로 tts를 쓰면 빌드가 설치 명령을 안내하며 중단된다. 그때 실행:

```bash
cd /Volumes/ExternalSSD/projects_7/brush-remotion-video
pipeline/.venv/bin/pip install -e "pipeline[tts]"
pipeline/.venv/bin/python scripts/tts-doctor.py --check supertonic
# Melo/Qwen은 scripts/tts-doctor.py --prepare <engine>를 명시할 때만 설치·snapshot 준비
```

공통 엔진 선택·license·reference·manifest 계약은 [TTS 엔진 카탈로그](../_shared/references/tts-engine-catalog.md)를 따른다.

**라이선스 주의(OpenRAIL-M)**: 합성 더빙이 들어간 영상을 공개 배포할 때는
**AI 생성 콘텐츠임을 고지**해야 한다 (영상 설명란 등). 딥페이크·사칭 등 금지 용도는 Attachment A 참조.
실물 예시: `examples/tts-script/` (대본 → 더빙 E2E)

## 기본 완료 연출 — 무펄스 자연 정착

일반 가로 brush는 `integrated-develop`가 기본이다. 실제 마지막 획 뒤 누락 영역을 같은
이미지 마스크 안에서 채우고, 전체 이미지가 완성된 뒤 `brightness(1)`을 유지한 채 채도만
정착시킨다. faint/develop 이미지 2장을 교차 페이드하지 않는다.

- 선호값: `developFrames 36`, `colorSettleFrames 18`, 최소 홀드 12f
- 짧은 씬은 기존 routes를 바꾸지 않고 2:1 비율로 12/6까지 결정적으로 축소한다.
- 그래도 완료→홀드→outro 시간이 부족하면 props 단계에서 실패한다.
- 기본 prewash/preview/blur/parallax/naturalEffects는 0 또는 비활성이다. 요청 시에만 opt-in한다.
- 기본 outro는 `24f / washOpacity 1.0 / blur 0`으로 마지막 실재 프레임에서 종이에 수렴한다.
- QA는 고정 mid/end가 아니라 draw-end→develop→settle→hold 프레임과
  `completion-report.json`을 사용한다.

## BGM — 로컬 음원·자동 덕킹·플레이리스트

**금지:** Pixabay 음원은 YouTube 일반 영상과 Shorts의 신규 제작·교체·배포에 사용하지 않는다.
Pixabay 자산은 로컬 청취·내부 데모·과거 검증용으로만 보존한다.
외부 BGM은 공식 페이지에서 먼저 로컬 다운로드하고 라이선스 증빙과 함께 등록한 뒤 사용한다.
렌더 중에는 인터넷을 사용하지 않는다. 다운로드·Content ID·YAML·게인·덕킹·크로스페이드의
단일 정책은 [공통 BGM 정책](../_shared/references/bgm-policy.md)을 따른다.

```bash
pipeline/.venv/bin/python bin/bgm-assets.py sources
pipeline/.venv/bin/python bin/bgm-assets.py status
```

- **자동 BGM (기본)**: `bgm` 블록을 안 써도 **대사 없는(ambient) 영상엔 로컬 BGM이 자동으로 붙는다.**
  대사(음성/TTS)가 있으면 음성만 쓰고, 완전 무음은 `bgm: { mode: "off" }`로 끈다. 특정 곡은 그때만 `assetId` 지정.
  자동 선택(결정적): brush/dark→Honor · pen→Chance/Luck · pen-brush/shorts→Satya Yuga · 10분 초과→허용 3곡 playlist.
  로컬 자산 미준비 시 synth 폴백. 상세: [공통 BGM 정책](../_shared/references/bgm-policy.md) §자동 BGM.
- 내레이션이 있으면 기본 `+3dB`와 자동 덕킹, 없으면 기본 `+5dB`
- BGM만 고치면 `--from mix --audit`로 영상 프레임 재렌더 없이 재실행한다.
- project.yaml이 없는 대사 없는 완성 MP4는 `bin/replace-bgm.py`로 영상 stream-copy 상태에서
  catalog asset만 교체한다. `--confirm-no-voice`가 필수이며 라이선스·mix·audit·YouTube 설명을 함께 생성한다.
- YouTube 배포에는 YouTube 오디오 보관함/검증된 CC BY·artist-site 음원만 사용한다. `CC BY 4.0`은 저작자·출처·라이선스 링크와
  수정 여부 표시가 필수이며, 현재 허용 목록과 복사 가능한 표시 문구는
  [공통 BGM 정책](../_shared/references/bgm-policy.md) §YouTube 오디오 보관함·CC BY를 따른다.

## 상단 타이틀 (선택)

씬 좌상단의 골드 kicker + 제목은 props의 `scenes[].topTitle`로 정의한다.
필드·기본값·검증된 프리셋·위젯과의 배치 관계는 [references/title-guide.md](references/title-guide.md) 참조.
배경 그림 위에 얹을 때는 `wash: true`, 첫 단어 강조색은 배경 인상색을 쓴다.

## 위젯 (선택)

씬의 빈 여백에 카드 위젯을 얹을 수 있다 (`widgets: authored` + props의 `scenes[].widgets[]`).
사용 가능한 15종과 필드는 [references/widget-catalog.md](references/widget-catalog.md) 참조.
네온·다크 글래스 금지, 자막·타이틀 영역 침범 금지 (타이틀이 있으면 위젯 y ≥ 230 권장).

## 환경 요구사항

- Node + npm (리포에 `npm install` 선행), ffmpeg/ffprobe
- Python venv: `pipeline/.venv` (없으면 `pipeline/README.md`의 부트스트랩 절차)
- whisper 모드: faster-whisper — 미설치 시 빌드가 안내하는 `pip install -e "pipeline[stt]"` 1회 (첫 실행 시 모델 자동 다운로드, 이후 캐시)

## 문제 해결

- 렌더/스키마 에러 → `data/{projectId}/props.json`이 `schema/render-props.schema.json`(v1)과 맞는지 확인.
  스키마의 유일한 정의는 리포의 `src/schema.ts`.
- 특정 씬만 이상 → `bin/qa.py <projectId> --frames <프레임들>`로 스틸 뽑아 확인 후 해당 스테이지 재실행.
- 씬 전환이 점프컷처럼 보임 → 일반 brush 기본 `outroWashOpacity 1.0 + outroFadeFrames 24` (순백 수렴).
  prewash는 기본 비활성이고 명시적으로 쓸 때도 첫 씬 전용
  (중간 씬 prewash는 첫 프레임에 즉시 켜져 2차 점프를 만든다 — FIELD-LOG 2026-07-11 city-watercolor 사례).
- 전환/완성 순간 번쩍임 전반 → 메커니즘 3종(경계 잔상 컷·develop 교차합성 펄스·렌더 결손 프레임)과
  **완성 선언 전 공통 체크**: [씬 전환·번쩍 공통 체크](../_shared/references/transition-checklist.md) ★모든 제작 스킬 공통
- 600초/18,000f 렌더가 마지막 stitch에서 `element-%05d.jpeg` 없음으로 실패하고 가용 RAM이 낮다면,
  단일 렌더 반복 대신 10씬/100초 무음 청크로 분할 렌더 → 동일 H.264 설정으로 stream-copy concat →
  최종 오디오 1회 mux한다. 청크별 3,000f/100.000s를 먼저 검증해 실패 구간만 재개한다.
