---
name: storybook-full-touch-video
description: >-
  동화 주제·대본·SRT와 캐릭터 레퍼런스로부터 장면별 풀터칭 그림, 펜 외곽선→브러시 채색 애니메이션,
  로컬 TTS 내레이션, 자막, BGM, 자동 QA가 포함된 가로 또는 세로 동화 영상을 제작하는 스킬. 기본 voice preset은 Supertonic이며 다른 엔진은 공통 카탈로그를 따른다.
  "동화 영상", "그림책 쇼츠", "10씬 100초", "풀터칭 이미지", "펜으로 그리고 채색",
  "젊고 밝은 여성 동화 낭독" 요청과 기존 동화 영상을 같은 형식으로 확장·재제작할 때 사용한다.
---

# storybook-full-touch-video

`brush_remotion_video`의 기존 엔진을 조합하는 얇은 오케스트레이션 스킬이다. 렌더러를 복사하지 않는다.

## 핵심 계약

1. 장면 수와 전체 시간을 먼저 고정한다. 기본값은 `10씬 × 10초 = 100초`다.
2. 장면마다 네이티브 화면비 이미지 1장을 사용한다. 가로 이미지를 쇼츠로 잘라 쓰지 않는다.
3. 모든 이미지는 균일한 중성 종이 배경, 닫힌 외곽선, 분리된 중대형 색면을 사용한다.
4. `drawing.profile: pen-brush`로 펜 외곽선 뒤 브러시 채색을 실행한다.
5. 장면마다 내레이션을 독립 합성하고 고정 길이 블록에 배치한다. 전체 음성을 한 번에 과도하게 늘이거나 줄이지 않는다.
6. 완성 선언 전에 `pen-brush-report.json`과 `video-auditor`를 모두 통과한다.

## 실행 리포와 진입점

- 리포: `/Users/hwanchoi/project_202606/brush_remotion_video`
- 종이 정규화: `scripts/normalize-storybook-paper.py`
- 고정 씬 TTS 준비: `scripts/prepare-storybook-full-touch.py`
- 렌더: `bin/build.py`
- 독립 감사: `bin/audit.py` 또는 `bin/build.py --audit`

## 워크플로

1. 주제, 교훈, 주인공, 포맷, 전체 시간, 씬 수를 결정한다.
2. `scenario.md`, `narration.txt`, 수동 기준 `subtitles.srt`, `project.yaml`을 만든다.
3. 장면별 이미지를 이미지 생성 도구로 별도 생성한다. 첫 장면을 이후 장면의 캐릭터·스타일 레퍼런스로 사용한다.
4. 이미지에 [풀터칭 이미지 계약](references/full-touch-image-contract.md)을 적용한다.
5. 종이색을 정규화하고 모든 이미지를 정확한 캔버스 크기로 맞춘다.
6. [스토리·SRT·TTS 계약](references/story-srt-tts-contract.md)에 따라 장면별 음성과 고정 타임라인을 만든다.
7. `bin/build.py ... --audit`로 렌더한다.
8. 실패하면 [빌드·QA 계약](references/build-and-qa.md)의 실패 유형별 처방을 적용하고 해당 스테이지부터 재실행한다.
9. 최종 MP4, 이미지 콘택트시트, 진행 프레임 갤러리, SRT, 감사 리포트를 함께 전달한다.

## 프로젝트 기본 구조

```text
projects/<project-id>/
├── scenario.md
├── narration.txt              # 비어 있지 않은 한 줄 = 한 씬
├── subtitles.srt              # 사람이 검토하는 기준 자막
├── project.yaml
└── public/bg/
    ├── scene-01-full-touch-shorts.png
    └── ...
```

## 기본 설정

```yaml
projectId: <project-id>
format: shorts
input:
  srt: subtitles.srt
  tts:
    engine: supertonic
    voice: female-08
    speed: 1.10
    pauseMs: 350
    timing: tts
background:
  strategy: user-images
  fit: contain
  images: [<장면 이미지 목록>]
drawing:
  profile: pen-brush
  sync: auto
widgets: none
bgm:
  mode: asset
  assetId: youtube-jesse-gallagher-satya-yuga
  gainDb: 1.5
  fadeInSec: 1.5
  fadeOutSec: 3.0
  ducking:
    enabled: true
    amountDb: 10.0
    attackMs: 100
    releaseMs: 500
  licensePolicy: strict
```

Pixabay 음원은 YouTube/Shorts 제작·교체·배포에 사용하지 않는다. 동화 영상도 예외가 아니며
YouTube Audio Library 또는 검증된 CC BY/artist-site 자산만 사용한다.

## 실행

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video

pipeline/.venv/bin/python scripts/normalize-storybook-paper.py \
  --project-dir projects/<project-id>

pipeline/.venv/bin/python scripts/prepare-storybook-full-touch.py \
  --project-dir projects/<project-id> \
  --scene-count 10 --scene-seconds 10 --voice female-08 --speed 1.10

pipeline/.venv/bin/python bin/build.py \
  projects/<project-id>/project.yaml --audit
```

## 중단 조건

- 세로 프로젝트인데 원본 이미지가 9:16이 아니면 생성 단계로 돌아간다.
- 종이 영역이 중성·균일하지 않으면 렌더하지 말고 정규화한다.
- 캐릭터 색, 목도리, 얼굴 비율이 장면마다 달라지면 이미지 단계에서 수정한다.
- 장면 음성이 허용 속도 보정 `1.15×`를 넘으면 대본을 줄인다.
- outline `< 0.99`, paint `< 0.9999`, missing pixels `> 0`, 경계 diff `≥ 6%`면 완성으로 전달하지 않는다.
- 감사 결과가 `FAIL`이면 실패 항목을 수정하고 재감사한다.

## 참고 자료 라우팅

- 이미지 생성·정규화·캐릭터 일관성: [full-touch-image-contract.md](references/full-touch-image-contract.md)
- 시나리오·SRT·Supertonic 고정 타이밍: [story-srt-tts-contract.md](references/story-srt-tts-contract.md)
- 엔진 선택·설치·reference·공개 고지: [TTS 엔진 카탈로그](../_shared/references/tts-engine-catalog.md)
- Supertonic 10종 음색·청취: [Supertonic 음성 카탈로그](../_shared/references/supertonic-voice-catalog.md)
- 스테이지·전환·수치 QA·실패 복구: [build-and-qa.md](references/build-and-qa.md)
- 검증된 100초 예제와 기준 수치: [validated-example.md](references/validated-example.md)
