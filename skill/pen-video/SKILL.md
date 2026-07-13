---
name: pen-video
description: >-
  펜이 이미지의 윤곽선을 빠르고 정교하게 그려가는 화이트보드/스케치 영상 생성 스킬.
  종이는 항상 보이고 잉크 선만 점진적으로 그려진다(잉크-알파 분리) — 붓(brush-video)의
  수묵 리빌과 구별되는 빠른 템포의 설명형 드로잉. project.yaml에 drawing.profile: pen
  한 줄이면 파이프라인이 잉크 분리·정밀 경로·펜 커서·프리셋을 자동 적용한다.
  실행 엔진은 brush-video와 동일한 bin/build.py를 공유한다 (프로파일 스킬 — 코드 사본 0).
---

# pen-video — 펜 스케치 드로잉 영상

**실행 대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
**brush-video와 같은 엔진·같은 빌더**를 쓴다. 이 스킬은 pen 프로파일의 사용법과 연출 규칙만 담는다.
공통 사항(설치·QA·TTS·타이틀·위젯)은 [brush-video SKILL.md](../brush-video/SKILL.md)를 따른다.

## 언제 이 스킬인가

- "펜으로 그리는", "스케치 영상", "화이트보드 애니메이션", "손그림 설명 영상" 요청
- 감성·명상형(수묵 붓 리빌)이면 → brush-video / 빠른 설명·지식형 드로잉이면 → **pen-video**

## 사용법 — 한 줄이면 된다

```yaml
projectId: my-sketch
format: youtube
drawing:
  profile: pen          # ← 이 한 줄이 pen 프로파일 전체를 켠다
  preserveSource: true  # 선택: 완료 시 원본 전체 색면·그림자까지 자연스럽게 복원
background:
  strategy: imagegen    # 선화 프롬프트는 background-prompt.md의 "pen 프로파일용" 섹션 사용
input:
  script: 대본.txt      # TTS 더빙 (선택) — brush-video와 동일
  tts: { engine: supertonic, voice: female-09, speed: 1.10 }
bgm:
  mode: asset
  assetId: youtube-chris-zabriskie-chance-luck-finale
  gainDb: 3                 # TTS 구간은 자동 덕킹
```

YouTube 선화 기본 BGM은 `Chance, Luck, Errors in Nature, Fate, Destruction As a Finale`이다.
Pixabay 음원은 YouTube/Shorts 제작·교체·배포에 사용하지 않는다. 공식 다운로드·증빙·로컬 등록은
[공통 BGM 정책](../_shared/references/bgm-policy.md)을 따른다.
전문 설명형 기본 음성은 `female-09`이며 10종 특징·청취 방법은
[공통 Supertonic 음성 카탈로그](../_shared/references/supertonic-voice-catalog.md)를 따른다.

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/python bin/build.py <project.yaml>
```

## profile: pen이 자동으로 하는 일

| 단계 | 동작 |
|---|---|
| 배경 | **contain + 종이색 패딩** (이미지 잘림 금지) |
| 잉크 분리 | `separate_ink()` — 종이·그라데이션은 투명, 잉크 선만 RGBA로. **종이는 항상 보이고 잉크만 그려진다** (브러쉬 효과 방지의 핵심) |
| 붓 경로 | 정밀 파라미터 (분석 1.5x, 스트로크 ~1,200+, drawEnd = 씬의 35% — 빠르게 그리고 오래 감상) |
| 씬 프리셋 | faint 1.0(즉시 또렷) · edgeFeather 1 · developFrames 8(무팝업) · prewash 0 · jitter 0 · 순차 드로잉 |
| 커서 | 내장 벡터 펜 스프라이트 (`brush: {kind: "pen", w: 140}`) — 펜촉이 그리는 지점에 닿음 |

## 연출 규칙 (fidelity 계약 — video-builder에서 채택)

1. **펜이 지난 뒤 늦게 채워지면 실패** — 펜 좌표와 잉크 리빌은 같은 진행률 (엔진이 보장)
2. **최종 이미지를 한 번에 띄우면 실패** — developFrames 8은 안티앨리어싱 마감용일 뿐 (완료 직전 diff 0.02% 실측)
3. **이미지 잘림 금지** — 배경은 항상 contain
4. 배경은 **선화(line-art)** 가 최적 — 수채·그라데이션은 잉크 분리 시 사라지므로 imagegen 프롬프트는
   [brush-video/references/background-prompt.md](../brush-video/references/background-prompt.md)의 "✒️ pen 프로파일용" 섹션을 쓸 것
5. 기존 컬러 인포그래픽을 마지막에 원본 그대로 보여줘야 하면 `preserveSource: true`를 사용한다.
   펜 경로는 잉크에서 추출하고, 원본 전체를 32% 가이드로 유지하면서 그린 구간만 선명하게 만든다.
   완료 마스크는 18프레임 동안 원본 전체를 점진적으로 복원하며 마지막 이미지 팝업은 만들지 않는다.

## 내레이션 동기 드로잉 (자동)

pen 프로파일 + 내레이션(srt/tts/whisper)이면 **기본으로 동기가 켜진다** (`drawing.sync: auto`) —
펜이 "지금 말하는 요소"를 그 문장(cue) 구간에 그린다:

- 자동 배분: 존(그림 덩어리)을 드로잉 순서대로 문장들에 순차 배정 (존 잉크 양 ↔ 문장 길이 비례)
- 배정 문장 구간 안으로 스트로크 리타이밍 — 문장 사이에는 펜이 자연스럽게 들림 (휴지)
- 끄기: `drawing: { sync: off }` (기존 pen 타이밍과 완전 동일)

**정밀 매핑 (Claude가 직접 짝짓기)** — 자동 배분이 어색하면:

1. 빌드가 산출한 존 크롭을 본다: `data/{pid}/zones/scene-XX/zone-NN.png` (+ `zones.json` 메타)
2. 각 크롭 이미지를 Read로 보고 어떤 문장과 어울리는지 판단해 `data/{pid}/sync-map.json` 작성:
   ```json
   { "scenes": [ { "sceneId": "scene-01", "zoneToCue": { "0": 0, "3": 1, "7": 2 } } ] }
   ```
   (미지정 존은 자동 배분으로 폴백)
3. `--from sync`로 재빌드 — 동기 스테이지만 다시 돈다

실물 예시: `examples/pen-sync/` (대본 3문장 + TTS + 동기 — E2E 검증, cue 구간 포함율 100%)

## 미세 조정 (props 직접 수정 후 `--from render`)

- 더 빠르게/느리게: routes 재생성이 정석 (`--from routes` 전에 project.yaml duration 조정).
  props에서 즉석 조정은 `brushDynamics.drawSpeedScale` (0.8~1.2 권장)
- 펜 크기: `brush.w` (기본 140, 참고: 화면 폭의 ~7%)
- 커스텀 펜 이미지: `brush: {kind: "image", src: "...", w, h, tipx, tipy}` (기존 방식 그대로)

실물 예시: `examples/pen-sketch/project.yaml` (무입력 앰비언트 1씬 — E2E 검증됨)

> 완성 선언 전 씬 전환·완성(develop) 번쩍 공통 체크를 통과할 것:
> [씬 전환·번쩍 공통 체크](../_shared/references/transition-checklist.md)
> (pen은 faint 1.0이므로 `completionMode: masked-hold` 필수 — 교차합성 펄스 원천 제거).
>
> 제작 중 발견한 갭은 `FIELD-LOG.md`에 기록하고 문서/검증기에 환류한다 (brush-video §갭 환류와 동일).
