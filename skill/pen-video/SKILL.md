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
background:
  strategy: imagegen    # 선화 프롬프트는 background-prompt.md의 "pen 프로파일용" 섹션 사용
input:
  script: 대본.txt      # TTS 더빙 (선택) — brush-video와 동일
  tts: { engine: supertonic, voice: F1 }
```

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

## 미세 조정 (props 직접 수정 후 `--from render`)

- 더 빠르게/느리게: routes 재생성이 정석 (`--from routes` 전에 project.yaml duration 조정).
  props에서 즉석 조정은 `brushDynamics.drawSpeedScale` (0.8~1.2 권장)
- 펜 크기: `brush.w` (기본 140, 참고: 화면 폭의 ~7%)
- 커스텀 펜 이미지: `brush: {kind: "image", src: "...", w, h, tipx, tipy}` (기존 방식 그대로)

실물 예시: `examples/pen-sketch/project.yaml` (무입력 앰비언트 1씬 — E2E 검증됨)
