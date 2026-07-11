---
name: brush-video
description: >-
  화이트 종이 위에 붓이 그림을 그리는(수묵화 리빌) 영상을 자동 생성하는 스킬.
  실행 대상은 brush_remotion_video 리포이며 이 스킬은 코드를 내장하지 않는다 —
  project.yaml 하나를 작성해 bin/build.py를 실행하면 배경 생성 → 붓 경로 추출 →
  씬/자막 구성 → 렌더 → 오디오 mux → QA까지 자동으로 완성 mp4가 나온다.
  내레이션(SRT/음성) · TTS(음성 없이 자막/대본만으로 Supertonic이 더빙 합성) ·
  앰비언트(무입력, BGM 합성) 모드를 지원한다.
  구 brush-draw-reveal 스킬의 후속 (newVideoGen 의존 제거, 완전 독립).
---

# brush-video — 화이트 붓 드로잉 영상 생성

**실행 대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
이 스킬은 코드를 내장하지 않는다. 리포가 유일한 소스다 (드리프트 방지 제1원칙).

## 워크플로

1. **project.yaml 작성** — 사용자의 요청에서 projectId·포맷·입력·배경 전략을 정리한다.
   전체 필드는 [references/project-yaml-guide.md](references/project-yaml-guide.md) 참조.

   ```yaml
   projectId: my-video
   format: youtube            # youtube(16:9) | shorts(9:16)
   input:
     srt: 자막.srt            # 있으면 내레이션 모드
     audio: 더빙.mp3          # srt 없고 audio만 있으면 whisper로 SRT 생성
     script: 대본.txt         # 대본 텍스트 (tts와 함께 사용)
     tts:                     # 음성이 없어도 TTS로 더빙 자동 생성 (아래 "TTS" 섹션)
       engine: supertonic
       voice: F1              # F1~F5 / M1~M5
       pauseMs: 350
     # 아무 입력도 없으면 앰비언트 모드 (10초 씬 × N + 합성 BGM)
   background:
     strategy: imagegen       # imagegen | preset(PIL, 결정적) | user-images
   widgets: none              # none | authored (auto는 준비 중)
   ```

2. **빌드 실행** — 리포 루트에서:

   ```bash
   cd /Users/hwanchoi/project_202606/brush_remotion_video
   python3 bin/build.py <project.yaml 경로>
   ```

   - 산출: `output/{projectId}.mp4` + `data/{projectId}/qa/`(캡처·콘택트시트)
   - 스테이지 캐시가 있어 실패 지점부터 재개 가능: `--from <stage>` (stt/cues/background/clean/routes/layout/props/render/mux/qa)

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

`input.tts` 블록이 있으면 실제 더빙 없이도 Supertonic TTS(온디바이스, API 키 불필요)가 더빙을 합성한다:

- **srt + tts**: SRT의 텍스트를 문장별 합성 — 타이밍은 합성 음성 길이가 시계 (SRT 타이밍은 재계산됨)
- **script + tts**: 대본 텍스트 → 더빙 + SRT 동시 생성
- **srt + audio 동시 제공 시 TTS는 무시** (실제 더빙 우선)
- 실측: 실시간 대비 약 4배 합성 속도(RTF 0.24), 보이스 F1~F5/M1~M5

**첫 사용 설치 (1회)** — 미설치 상태로 tts를 쓰면 빌드가 설치 명령을 안내하며 중단된다. 그때 실행:

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/pip install -e "pipeline[tts]"
# 첫 합성 시 모델(385MB)이 ~/.cache/supertonic3 에 자동 다운로드된다 (이후 오프라인)
```

**라이선스 주의(OpenRAIL-M)**: 합성 더빙이 들어간 영상을 공개 배포할 때는
**AI 생성 콘텐츠임을 고지**해야 한다 (영상 설명란 등). 딥페이크·사칭 등 금지 용도는 Attachment A 참조.
실물 예시: `examples/tts-script/` (대본 → 더빙 E2E)

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
