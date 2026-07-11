---
name: brush-director
description: >-
  일반 사용자의 영상 요청("잔잔한 겨울밤 느낌 쇼츠 만들어줘")을 전문 영상 연출 용어 브리프와
  project.yaml/props 초안으로 번역하는 스킬. brush-video 스킬의 앞단 — 무드·붓 느낌·전환·파티클·
  오디오·정보 요소를 실측 검증된 파라미터로 매핑해 의도 손실 없이 파이프라인에 전달한다.
  실행은 하지 않고 번역·설계만 한다 (실행은 brush-video).
---

# brush-director — 연출 브리프 변환기

**대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
이 스킬은 코드를 실행하지 않는다. 일반 요청 → 전문 브리프 + yaml 초안까지가 역할이고,
실행은 **brush-video 스킬**로 넘긴다.

## 워크플로

1. **의도 축 5개 추출** — 요청에서 다음을 식별한다 (없는 축은 기본값):
   ① 무드/분위기 ② 소재(그림 주제) ③ 포맷·길이 ④ 오디오(더빙/BGM) ⑤ 정보 요소(타이틀/자막/위젯)
2. **매핑** — references 순서로 번역한다:
   - [mood-presets.md](references/mood-presets.md) — 무드가 프리셋과 맞으면 그 조합에서 출발
   - [intent-map.md](references/intent-map.md) — 개별 표현을 파라미터로 (권장값은 실측 분포 기반)
   - [glossary.md](references/glossary.md) — 브리프에 쓸 전문 용어와 v1 필드 대응
3. **출력 계약** — 반드시 이 3가지를 이 순서로:
   - ⓐ **연출 브리프 표**: 의도 축별로 [전문 용어 + 한 줄 설명 + 선택한 값]. 사용자가 용어를 배우면서 확인하게
   - ⓑ **project.yaml 초안** (+ 위젯·타이틀이 있으면 props 씬 초안)
   - ⓒ **확인 질문 최대 2개** — 결과를 크게 바꾸는 모호한 축만 (전부 되묻지 않기)
4. 사용자가 확정하면 **brush-video 스킬 워크플로로 실행**한다.

## 규칙

- **실측 범위 밖 값 제안 금지** — intent-map의 권장 범위 안에서만
- **연속 제작 시 직전 영상과 변주** — mood-presets의 "운용 규칙"을 따라 직전 프로젝트의 프리셋·seed를 확인하고 겹치지 않게 제안
- **미구현 기능을 약속하지 않기** — 환경음(빗소리 등)·트랙 크로스페이드는 "확장 후보"로 정직하게 안내하고 대안(합성 피아노 BGM) 제시
- 구 시스템 용어(scene-XX.routes.json, build-shorts-*.py 등)가 와도 glossary 하단 표로 v1로 번역
- TTS 요청 + 미설치 환경이면 brush-video의 "TTS 첫 사용 설치" 안내를 함께 전달

## 변환 예시 1 — "겨울밤 느낌으로 잔잔하게, 별 반짝이는 쇼츠 하나 만들어줘"

| 의도 축 | 전문 번역 | 값 |
|---|---|---|
| 무드 | ❄️ 겨울밤 프리셋 — 별빛 파티클(starTwinkle, 은은하게 0.04) + 느긋한 등속 드로잉 | drawSpeedScale 1.12 |
| 소재 | 겨울 소재 손그림 배경 (imagegen, 잉크+수채) | strategy: imagegen |
| 포맷 | 쇼츠 세로형 | format: shorts |
| 오디오 | 합성 피아노 패드 BGM (앰비언트 모드) | 자동 |
| 전환 | 아웃트로 워시 24f — 순백 수렴 | outroFadeFrames 24 |

```yaml
projectId: winter-night-shorts
format: shorts
background: { strategy: imagegen, style: ink-watercolor }
ambient:
  scenes: 3
  cues: ["별이 내려앉는 밤", "고요가 쌓이는 시간", "겨울밤은 천천히 깊어진다"]
```
확인 질문: 씬 수(기본 3×10초)와 cue 문구, 이대로 갈까요?

## 변환 예시 2 — "우리 제품 소개를 목소리로 설명하면서 수치도 보여주는 영상"

| 의도 축 | 전문 번역 | 값 |
|---|---|---|
| 무드 | 📚 지식·설명형 — 파티클 없음, faint 0.72로 또렷하게 | — |
| 오디오 | TTS 내레이션 (대본 → Supertonic 합성, 음성 길이가 타이밍의 시계) | input.tts{voice: F1} |
| 정보 | 상단 타이틀(wash) + stat/CompareBars 위젯 (타이틀 아래 y≥230) | topTitle + widgets |
| 포맷 | 유튜브 가로 | format: youtube |

```yaml
projectId: product-intro
format: youtube
input:
  script: 대본.txt
  tts: { engine: supertonic, voice: F1, pauseMs: 350 }
background: { strategy: imagegen, style: ink-watercolor }
widgets: authored
```
확인 질문: ① 보이스 남/여 선호? ② 강조할 수치 2~3개를 알려주시면 위젯으로 배치합니다.
