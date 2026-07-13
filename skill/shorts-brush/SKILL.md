---
name: shorts-brush
description: >-
  세로 풀블리드 힐링 브러시 쇼츠(1080×1920) 생성 스킬. 씬마다 다른 수채 풍경을 붓이
  화면 가득 그려가고, 하단 세이프존에 시적 자막이 씬 팔레트와 동조한 강조색으로 얹힌다.
  format: shorts 하나로 파이프라인 전체(배경·붓 경로·레이아웃)가 세로로 동작하며,
  훅(짧은 프리워시)·씬 전환·루프 친화 엔딩(순백 수렴)이 자동 적용된다.
  기본 3씬×10초=30초, 쇼츠 한도 180초. 실행 엔진은 brush-video와 동일한 bin/build.py
  (프로파일 스킬 — 코드 사본 0).
---

# shorts-brush — 세로 힐링 브러시 쇼츠

**실행 대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
**brush-video와 같은 엔진·같은 빌더**를 쓴다. 공통 사항(설치·QA·갭 환류)은 [brush-video SKILL.md](../brush-video/SKILL.md)를 따르고,
완성 선언 전 [씬 전환·번쩍 공통 체크](../_shared/references/transition-checklist.md)를 통과한다 (루프 엔딩의 순백 수렴 1.0이 A계열 표준 처방).

## 언제 이 스킬인가

- "쇼츠/릴스/세로 영상", "힐링 짧은 영상", "폰으로 보는 감성 영상" 요청
- 가로 유튜브 장편이면 → brush-video / 펜 스케치 설명이면 → pen-video

## 사용법 — format: shorts 하나로 세로 전체가 켜진다

```yaml
projectId: healing-morning
format: shorts               # ← 배경 생성·붓 경로·레이아웃 검증까지 전부 1080×1920
background:
  strategy: imagegen         # 세로 프롬프트 자동 선택 (background-prompt.md 📱 섹션)
ambient:
  scenes: 3                  # 기본 3씬 × 10초 = 30초
  cues:
    - "고요한 아침이 열린다"
    - "복잡한 생각은 바람에 흘려보내고"
    - "오늘도 다시, 가볍게 시작해"
bgm:
  mode: asset
  assetId: youtube-jesse-gallagher-satya-yuga
  gainDb: 5
```

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/python bin/build.py <project.yaml>
```

## format: shorts가 자동으로 하는 일

| 항목 | 동작 |
|---|---|
| 해상도 | 배경·붓 경로·레이아웃·렌더 전부 **1080×1920** 정합 |
| 자막 세이프존 | `bottom 290 / maxWidth 900 / fontSize 36` 기본 — 하단 유튜브 UI 회피 (명시하면 존중) |
| **강조색 씬 동조** | 씬 배경에서 색을 추출해 자막 강조 단어 색이 **씬마다 팔레트와 맞음** |
| 훅 | 첫 씬 프리워시 짧게(0.5/18f) — 첫 1~2초 안에 그림이 움직임 |
| 루프 엔딩 | 마지막 씬 outro 순백 수렴(washOpacity 1.0) — 반복 재생이 매끄러움 |
| 타이틀·위젯 | 사용 시 상단 세이프존(y ≥ 120)·자막 밴드 침범을 검증이 hard-fail로 차단 |
| BGM | 기본 추천 Satya Yuga 로컬 1곡. Pixabay는 YouTube Shorts 사용 금지. 미등록/미지정 기존 프로젝트는 합성 피아노 |

## 길이 규정 (2026 쇼츠 기준)

- **한도: 180초** (씬 18개) — 초과는 빌드가 거부
- **권장: 30초 내외** (알고리즘 초기 노출은 60초 미만이 유리) — 60초 초과 시 빌드가 경고
- 씬 구성 관행: 씬마다 **다른 풍경·다른 팔레트** (예: 호수 → 숲길 → 노을), 무드는 하나로 통일
- 쇼츠는 기본 1곡을 쓰며 2~3곡 playlist는 60초를 넘는 특별한 경우에만 사용한다.

## TTS 쇼츠

목소리가 필요한 새 프로젝트는 밝고 명료한 `female-07`, `speed: 1.10`을 기본 추천한다.
사용자가 지정한 음성은 유지하며 `voice:auto`는 쓰지 않는다. 10종 비교와 청취는
[공통 Supertonic 음성 카탈로그](../_shared/references/supertonic-voice-catalog.md)를 따른다.

## 세로 배경

- imagegen: **9:16 세로 전용 구도** — 상단 1/4 하늘·여백(타이틀 자리 겸용) + 중앙 주 소재 + 하단 근경.
  프롬프트는 [brush-video/references/background-prompt.md](../brush-video/references/background-prompt.md)의 📱 섹션
- **가로 그림 재활용 금지** — 잘리거나 늘어남. 세로로 새로 생성
- preset(PIL): 세로 캔버스 + 씬별 시드 회전 팔레트 (imagegen 불가 환경 폴백)

## 미세 조정

- 자막 위치·크기: project.yaml `subtitleStyle` 또는 props에서 명시 (기본값 대체)
- 씬 수·길이: `ambient.scenes` (씬당 300f=10초 고정)
- 무드: brush-director의 프리셋(겨울밤/아침 숲/노을…)과 조합 — "한 영상=한 프리셋" 운용 규칙 준수

실물 예시: `examples/shorts-healing/project.yaml` (3씬 30초 — E2E 검증: 해상도 3종 정합, 씬별 강조색 3색, 루프 diff 1.87%)

> 제작 중 발견한 갭은 `FIELD-LOG.md`에 기록하고 문서/검증기에 환류한다.
