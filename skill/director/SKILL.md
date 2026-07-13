---
name: brush-director
description: >-
  일반 사용자의 영상 요청("잔잔한 겨울밤 느낌 쇼츠 만들어줘")을 전문 영상 연출 용어 브리프와
  project.yaml/props 초안으로 번역하고, 일상적인 카메라 표현을 37개 canonical 기법과 전문 한/영
  Camera Prompt Pack으로 변환하는 스킬. brush-video 스킬의 앞단 — 무드·붓 느낌·전환·파티클·
  오디오·정보·카메라 요소를 검증된 계약으로 매핑해 의도 손실 없이 파이프라인에 전달한다.
  실행은 하지 않고 번역·설계만 한다 (실행은 brush-video).
---

# brush-director — 연출 브리프 변환기

**대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
이 스킬은 코드를 실행하지 않는다. 일반 요청 → 전문 브리프 + yaml 초안까지가 역할이고,
실행은 **brush-video 스킬**로 넘긴다.

## 워크플로

1. **의도 축 6개 추출** — 요청에서 다음을 식별한다 (없는 축은 기본값):
   ① 무드/분위기 ② 소재(그림 주제) ③ 포맷·길이 ④ 오디오(더빙/BGM)
   ⑤ 정보 요소(타이틀/자막/위젯) ⑥ 카메라·시점·렌즈·전환
2. **매핑** — references 순서로 번역한다:
   - [mood-presets.md](references/mood-presets.md) — 무드가 프리셋과 맞으면 그 조합에서 출발
   - [intent-map.md](references/intent-map.md) — 개별 표현을 파라미터로 (권장값은 실측 분포 기반)
   - [glossary.md](references/glossary.md) — 브리프에 쓸 전문 용어와 v1 필드 대응
   - 카메라 표현이 있으면 [camera-intent-map.md](references/camera-intent-map.md)로 후보와 모호성을 해석
   - 이어 [camera-prompt-guide.md](../_shared/references/camera-prompt-guide.md)의 조립·호환성·negative 규칙 적용
   - 필요할 때만 [camera-prompt-catalog.json](../_shared/references/camera-prompt-catalog.json)의 해당 canonical 항목을 읽고,
     출력 형태는 [camera-prompt-examples.md](references/camera-prompt-examples.md)를 따른다
3. **출력 계약** — 반드시 아래 순서를 지킨다:
   - ⓐ **연출 브리프 표**: 의도 축별로 [전문 용어 + 한 줄 설명 + 선택한 값]. 사용자가 용어를 배우면서 확인하게
   - ⓐ-1 **Camera Prompt Pack(선택)**: 카메라 의도가 있을 때만 canonical 해석 + 슬롯 + 한/영 prompt +
     negative prompt + 4개 타깃 호환성. 이것은 전문 브리프이며 `project.yaml` 필드가 아니다
   - ⓑ **project.yaml 초안** (+ 위젯·타이틀이 있으면 props 씬 초안)
   - ⓒ **확인 질문 최대 2개** — 결과를 크게 바꾸는 모호한 축만 (전부 되묻지 않기)
4. 사용자가 확정하면 요청에 맞는 **brush-video / pen-video / pen-brush-video / dark-random-brush-video** 워크플로로 실행한다.

## 규칙

- **실측 범위 밖 값 제안 금지** — intent-map의 권장 범위 안에서만
- **연속 제작 시 직전 영상과 변주** — mood-presets의 "운용 규칙"을 따라 직전 프로젝트의 프리셋·seed를 확인하고 겹치지 않게 제안
- **미구현 기능을 약속하지 않기** — 환경음(빗소리 등)은 확장 후보로 안내한다. BGM 트랙 크로스페이드는 로컬 등록 음원 2~3곡 playlist로 지원한다.
- **Camera Prompt Pack을 YAML로 위장하지 않기** — `camera:`/`cameraMotion:` 같은 미지원 필드를
  `project.yaml`에 넣지 않는다. `external-required`는 외부 영상 생성·촬영 단계가 필요하다고 그대로 표시한다.
- **기법 과잉 결합 금지** — primary는 1개, 충돌하지 않는 secondary는 최대 1개다.
  방향·속도·시작/종료 구도 등 사용자가 명시한 슬롯을 catalog 기본값으로 덮어쓰지 않는다.
- **모호성과 충돌을 숨기지 않기** — `당겨줘`, `돌아줘`, `흔들리게`가 둘 이상 후보로 남거나
  static+handheld, zoom-in+pull-back처럼 충돌하면 `needsClarification: true`와 질문 최대 2개를 출력한다.
- **정지 합성과 실제 공간 이동을 구분** — 기존 `parallax`는 2D 깊이 근사다. true arc/orbit/tracking/FPV의
  동의어로 사용하지 않고 타깃 호환성을 함께 표시한다.
- **원본 보존 제약** — 펜·펜브러시에는 선 굵어짐·외곽 흐림 금지, 인물에는 identity,
  제품에는 shape/logo, 텍스트에는 철자·방향 보존 negative rule을 추가한다.
- **Pixabay 배포 금지** — `format: youtube|shorts`에는 Pixabay 음원을 제안하거나 YAML에 넣지 않는다. 로컬 청취·내부 데모만 허용한다.
- 구 시스템 용어(scene-XX.routes.json, build-shorts-*.py 등)가 와도 glossary 하단 표로 v1로 번역
- TTS 요청 + 미설치 환경이면 brush-video의 "TTS 첫 사용 설치" 안내를 함께 전달
- TTS 음성은 [10종 공통 카탈로그](../_shared/references/supertonic-voice-catalog.md)에서 의도에 맞게 고르고
  결과 YAML에 명시적 `female-*` ID를 쓴다. 사용자가 지정한 음성은 덮어쓰지 않고 `voice:auto`는 쓰지 않는다.

## 변환 예시 1 — "겨울밤 느낌으로 잔잔하게, 별 반짝이는 쇼츠 하나 만들어줘"

| 의도 축 | 전문 번역 | 값 |
|---|---|---|
| 무드 | ❄️ 겨울밤 프리셋 — 별빛 파티클(starTwinkle, 은은하게 0.04) + 느긋한 등속 드로잉 | drawSpeedScale 1.12 |
| 소재 | 겨울 소재 손그림 배경 (imagegen, 잉크+수채) | strategy: imagegen |
| 포맷 | 쇼츠 세로형 | format: shorts |
| 오디오 | YouTube 허용 Honor 로컬 BGM (미등록이면 합성 피아노 폴백을 명시적으로 선택) | bgm.assetId |
| 전환 | 아웃트로 워시 24f — 순백 수렴 | outroFadeFrames 24 |

```yaml
projectId: winter-night-shorts
format: shorts
background: { strategy: imagegen, style: ink-watercolor }
ambient:
  scenes: 3
  cues: ["별이 내려앉는 밤", "고요가 쌓이는 시간", "겨울밤은 천천히 깊어진다"]
bgm:
  mode: asset
  assetId: youtube-chris-zabriskie-fight-for-your-honor
  gainDb: 5
```
확인 질문: 씬 수(기본 3×10초)와 cue 문구, 이대로 갈까요?

## 변환 예시 2 — "우리 제품 소개를 목소리로 설명하면서 수치도 보여주는 영상"

| 의도 축 | 전문 번역 | 값 |
|---|---|---|
| 무드 | 📚 지식·설명형 — 파티클 없음, faint 0.72로 또렷하게 | — |
| 오디오 | 전문 설명형 TTS (음성 길이가 타이밍의 시계) | input.tts{voice: female-09, speed: 1.10} |
| 정보 | 상단 타이틀(wash) + stat/CompareBars 위젯 (타이틀 아래 y≥230) | topTitle + widgets |
| 포맷 | 유튜브 가로 | format: youtube |

```yaml
projectId: product-intro
format: youtube
input:
  script: 대본.txt
  tts: { engine: supertonic, voice: female-09, speed: 1.10, pauseMs: 350 }
background: { strategy: imagegen, style: ink-watercolor }
widgets: authored
```
확인 질문: 강조할 수치 2~3개를 알려주시면 위젯으로 배치합니다.

## 변환 예시 3 — "그림이 완성되면 인물 뒤에서 천천히 따라가 줘"

| 의도 축 | 전문 번역 | 값 |
|---|---|---|
| 카메라 | 팔로우·오버 더 숄더 — 인물 뒤 어깨 너머에서 이동 속도와 거리를 유지 | `follow-over-shoulder`(19) |
| 움직임 | 카메라 실제 이동, forward, subject-matched | primary 1개 |
| 타깃 | 정지 Remotion만으로 true tracking 불가, AI video prompt는 지원 | `external-required` / `supported` |

```yaml
cameraPrompt:
  interpretation:
    canonicalId: follow-over-shoulder
    canonicalNo: 19
    confidence: 0.94
    needsClarification: false
  parameters:
    direction: forward
    speed: subject-matched
    distance: close-follow
    subjectLock: true
    stabilization: smooth
  promptKo: "인물의 뒤쪽 어깨 너머 구도를 유지하며 걷는 속도에 맞춰 일정한 거리로 부드럽게 따라간다."
  promptEn: "Follow smoothly from behind in an over-the-shoulder framing at a matched pace and constant distance."
  negativePrompt: ["no identity drift", "no random shake", "no softened outlines"]
  compatibility:
    remotionStill: external-required
    aiVideo: supported
    imageGeneration: composition-only
    sceneTransition: not-applicable
```

이 `cameraPrompt` 블록은 브리프에만 둔다. 아래 `project.yaml`에는 현재 지원되는 필드만 작성한다.
