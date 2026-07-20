---
name: pen-brush-video
description: >-
  완성 컬러 이미지 한 장을 펜이 얇고 샤프한 외곽선으로 먼저 그린 뒤, 브러시가 색을 채우는
  2단계 Remotion 영상으로 제작하는 스킬. "외곽부터 그리고 채색", "pen 다음 brush",
  "선화가 완성되면 색칠" 요청에 사용한다. project.yaml의 drawing.profile: pen-brush로
  공용 brush_remotion_video 엔진을 실행하며 가로 YouTube와 세로 Shorts를 지원한다.
---

# pen-brush-video

**실행 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
이 스킬에는 실행 코드가 없다. 공용 `bin/build.py`와 `brushvid` 엔진만 사용한다.

## 실행 순서

1. 흰색 또는 미색의 균일한 종이에 얇은 검은 선과 분리된 색면이 있는 완성 이미지를 준비한다.
2. 아래처럼 `project.yaml`을 작성한다.
3. 빌드하고 `qa/contact-sheet.png`, `qa/pen-brush-report.json`을 확인한다.
4. 최종 MP4를 `bin/audit.py` 또는 `bin/build.py --audit`로 검사한다.

```yaml
projectId: pen-brush-demo
format: youtube       # shorts도 지원
background:
  strategy: user-images
  images: [./source.png]
drawing:
  profile: pen-brush
  sync: auto
ambient:
  scenes: 1
  cues: ["외곽선을 그리고 색을 채웁니다"]
bgm:
  mode: asset
  assetId: youtube-jesse-gallagher-satya-yuga
  gainDb: 5.0
  fadeInSec: 1.8
  fadeOutSec: 2.0
  licensePolicy: strict
```

YouTube 기본 BGM은 `Satya Yuga`다. Pixabay 음원은 YouTube/Shorts 제작·교체·배포에 사용하지 않는다. 첫 사용 전
[공통 BGM 정책](../_shared/references/bgm-policy.md)에 따라 공식 페이지에서 MP3와
라이선스 증빙을 내려받아 `bin/bgm-assets.py import`로 등록한다. 내레이션이 있으면
`gainDb: 3.0`과 ducking을 사용한다.
무음 15~120초 영상에서 `bgm`을 생략하면 Stable Audio가 따뜻한 illustrative/cinematic 피아노를 자동 우선 생성한다. 내레이션/TTS는 자동 생성하지 않으며, 필요 시 `bgm.mode: piano-auto`를 명시한다.

설명 내레이션을 넣을 때 기본 Supertonic 권장은 `input.tts{engine: supertonic, voice: female-09, speed: 1.10}`이다. Melo/Qwen 선택은 [공통 TTS 엔진 카탈로그](../_shared/references/tts-engine-catalog.md)를 따른다.
10종 특징·미리듣기·AI 고지는
[공통 Supertonic 음성 카탈로그](../_shared/references/supertonic-voice-catalog.md)를 따른다.

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/python bin/build.py <project.yaml> --audit
```

## 자동 처리

| 단계 | 동작 |
|---|---|
| clean | 동일 좌표의 얇은 outline RGBA, 원본 color RGBA, content 자산 생성 |
| routes | outline은 펜 contour, paint는 자동 매크로 존의 넓은 왕복 붓질 생성 |
| sync | outline 경계를 씬 30~48% 안의 가장 가까운 cue 끝으로 스냅 |
| render | outline z20, paint z10. 채색 완료 직전 outline을 페이드해 원본 선 굵기 복원 |
| QA | 5개 핵심 프레임과 coverage·누출·커서 겹침·타이밍 JSON 검사 |

## 품질 계약

반드시 [fidelity-contract.md](references/fidelity-contract.md)를 따른다. 특히 다음은 실패다.

- 외곽선 완료 전에 색이 보임
- 펜과 브러시가 동시에 보임
- 마지막에 완성 이미지를 한 프레임으로 팝업함
- outline과 원본 선을 끝까지 중첩해 선이 두꺼워짐
- 이미지별 절대 좌표로 채색 존을 하드코딩함

## 문제 해결

- `빈 이미지`, `full-bleed`, `외곽선을 검출하지 못함`: 흰 종이 여백과 대비가 있는 원본으로 교체한다.
- `paint coverage ... < 0.9999`: `--from clean`부터 재실행하고 원본의 종이 배경이 균일한지 확인한다.
- phase routes 없음: `--from routes`로 재실행한다.
- 외곽선이 둔탁함: outline extraction에 dilation을 추가하지 않는다. 최종 outline fade도 제거하지 않는다.
- 세로에서 소재가 작음: 가로 이미지를 재사용하지 말고 9:16 원본을 생성한다.
- 씬 전환/완성 순간 번쩍임: 메커니즘 3종과 완성 전 공통 체크 —
  [씬 전환·번쩍 공통 체크](../_shared/references/transition-checklist.md)
  (이 프로파일은 outline→paint 핸드오프 프레임도 B계열 펄스 검사 대상).

검증된 예제: `examples/pen-brush/project.yaml`, `examples/pen-brush-shorts/project.yaml`.
