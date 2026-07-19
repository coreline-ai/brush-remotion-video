---
name: promo-widget-video
description: >-
  KIMI-K3 프로모 분석에서 자산화한 다크 프로모 위젯 32종(게이지·바·리더보드·카운트업·키네틱 타이포·
  데이터 패널·UI 크롬·배지)과 연출 계층(가변 씬 길이·전환 3종·무대 5종·플래시 비트)으로 다크 모션그래픽
  영상을 조립·렌더하는 스킬. 붓/펜 리빌 없이 "게이지 스윕 + 카운트업 + 리더보드 리오더"가 정보 전개를
  담당한다. 실전 제작은 PromoScene 컴포지션(scenes JSON), 위젯 회귀 검증은 PromoWidgetGallery.
  위젯 목록·계약·데모 값의 단일 근원은 assets/promo-widgets/catalog.json 이다.
---

# promo-widget-video — 다크 프로모 위젯 씬 렌더

**실행 대상 리포**: `/Volumes/Eprojects/project_202606/brush_remotion_video`

이 스킬은 코드를 내장하지 않는다 (코드 사본 0). 실행 엔진은 리포의 Remotion 컴포지션
`PromoWidgetGallery`(`src/promo/PromoWidgetGallery.tsx`)이고, 위젯 계약의 단일 근원은
[assets/promo-widgets/catalog.json](../../assets/promo-widgets/catalog.json)이다.
브러시/펜 파이프라인(`bin/build.py`)과 완전히 분리된 라인이다 — project.yaml을 쓰지 않는다.

## 언제 이 스킬인가

| 요청 | 스킬 |
| --- | --- |
| 다크 배경 + 데이터 위젯(게이지·리더보드·카운트업) 프로모/발표 영상 | **이 스킬** |
| 흰 종이 붓/펜 리빌 | brush-video / pen-* |
| 어두운 이미지 랜덤 붓 리빌 | dark-random-brush-video |
| 완성 mp4 검수 | video-auditor |

## 위젯 카탈로그 (31종)

위젯 id·props 계약·원본 W-번호·데모 값은 전부 catalog.json에 있다. 씬을 설계할 때는
**catalog의 demos를 출발점으로 복사·수정**하는 것이 가장 안전하다 (스키마 기본값이 검증된 조합).

| 패밀리 | 위젯 id |
| --- | --- |
| meter | gauge |
| bar | statBar |
| ranking | leaderboard · rankLadder |
| hero-number | countUp · priceTag |
| data-panel | numberLinePlot · nodeGraph · curvePlot · heatmapGrid · particleField · oscilloscope · flowDiagram · strataDiagram |
| ui-chrome | logCard · terminal · checklistPanel · calloutPanel · platformSelector |
| label-badge | kicker · pillBadge · sportsCallout · marquee · splitFlap · timelineScrubber · frameBrackets · subtitle · chevronBadges · dateFlip · ticketProp · **heroTitle**(키네틱 타이포) · logoLockup |

디자인 토큰(블루 `#4a7fff` 데이터 / 골드 CTA / 레드 상대)은 `src/promo/tokens.ts`가 강제한다 —
씬 설계에서 색을 지정하지 않는다.

## 컴포지션 2종 — 용도를 혼동하지 않는다

| 컴포지션 | 용도 | props |
| --- | --- | --- |
| **`PromoScene`** | **실전 영상 제작** (기본 선택) — 가변 씬 길이·전환·무대·플래시 비트 | `scenes[]` |
| `PromoWidgetGallery` | 위젯 시각 회귀 카탈로그 (검증용 최대 적재 — 제품 아님) | `pages[]` |

## PromoScene props 계약 (실전)

씬마다 길이를 모션·내레이션에 맞춘다. 원본 KIMI-K3 문법: **씬당 히어로 위젯 1–3개 + 대형 여백**.

```json
{
  "kicker": "ANTHROPIC // CLAUDE COWORK",
  "scenes": [
    {
      "durationInFrames": 120,
      "stage": { "preset": "orb", "tint": "blue" },
      "transition": { "type": "none" },
      "subtitle": "씬별 하단 자막",
      "flashAt": [16],
      "widgets": [
        { "type": "heroTitle", "x": 260, "y": 400, "w": 1400, "h": 430, "enterAt": 10,
          "text": "CLAUDE", "accent": "COWORK", "sub": "AGENT-POWERED", "underline": true,
          "scaleFrom": 1.5, "settleFrames": 6 }
      ]
    },
    {
      "durationInFrames": 150,
      "stage": { "preset": "grid" },
      "transition": { "type": "light-sweep", "durationInFrames": 12 },
      "widgets": [ { "type": "terminal", "...": "..." } ]
    }
  ]
}
```

- **전환 3종**: `light-sweep`(발광 빔 와이프) · `white-flash`(전프레임 노출 리프트 컷) · `push-in`(원근 교대) · `none`
- **무대 5종**: `orb`(구체 북엔드) · `grid`(드리프트 그리드) · `particle-dust`(상승 파티클) · `spotlight`(아레나 콘) · `glow`(펄스) + `tint: blue|warm|none` + `glyph`(워터마크)
- **`flashAt[]`**: 씬 내부 플래시 비트 (원본 리듬의 핵심 — 히어로 정착 직후 프레임에 둔다. heroTitle이면 `enterAt+settleFrames`)
- **키네틱 오프닝 관례**: heroTitle(scaleFrom 1.5) + orb 무대 + 정착 직후 flashAt = 원본 타이틀 문법
- 검수(video-auditor) 주의: 플래시·컷은 spike/hardcut FAIL로 검출된다 — **원본 참조 영상 자체가 FAIL 47인 장르 특성**이므로 오디오·규격 항목만 게이트로 삼는다

## PromoWidgetGallery props 계약 (회귀 검증)

씬 = **페이지** (페이지당 150프레임 = 5초, 30fps). `pages` 배열 하나가 곧 씬 시퀀스다.
각 위젯의 `enterAt`은 페이지 로컬 프레임 기준이다.

```json
{
  "kicker": "GRAND FINALE // 2026",
  "subtitle": "2.8조 파라미터 — 오픈소스 사상 최대 규모",
  "pages": [
    [
      { "type": "gauge", "kind": "needle", "x": 560, "y": 300, "w": 800, "h": 480,
        "label": "OFFICIAL WEIGH-IN", "value": 2.8, "max": 3, "unit": "T", "sweepFrames": 36 }
    ],
    [
      { "type": "leaderboard", "x": 560, "y": 240, "w": 800, "h": 420,
        "header": "PROGRAM BENCH", "reorder": true,
        "rows": [
          { "name": "KIMI K3", "score": 77.8, "highlight": true },
          { "name": "GPT-5.6 SOL", "score": 77.6 }
        ] }
    ]
  ]
}
```

- 위젯 props는 `PromoWidgetSchema`(`src/promo/schema.ts`, zod strict)로 검증된다 —
  계약 밖 필드는 렌더가 즉시 거부한다.
- 배치는 1920×1080 절대 px. 키커 좌상(x≈140, y≈48)·자막 중앙하단은 컴포지션이 그린다.

## 실행 순서

```bash
cd /Volumes/Eprojects/project_202606/brush_remotion_video

# 1) 갤러리로 위젯 시각 확인 (기본 props = catalog demos 5페이지)
npx remotion still src/index.ts PromoWidgetGallery out/gallery.png --frame=120

# 2) 씬 props 작성 후 스틸로 배치 검증
npx remotion still src/index.ts PromoWidgetGallery out/scene1.png \
  --frame=120 --props=props.json

# 3) 실전 씬 시퀀스 렌더 (duration = 씬 길이 합산 자동 계산)
npx remotion render src/index.ts PromoScene out/promo.mp4 --props=scenes.json

# 4) BGM 믹스 — 렌더 후 ffmpeg, 영상 믹스 -23 LUFS (공통 BGM 정책)
#    주의: assets/bgm/catalog.json에서 youtubeAllowed=true 곡만 배포용으로 사용
```

렌더 후 검수는 [video-auditor](../video-auditor/SKILL.md)에 위임한다 (독립 mp4 검수).

## 씬 연출 프롬프트 (SCENE DIRECTION PROMPT — 씬 저작 시 반드시 적용)

> 2026-07-19 사용자 피드백("원본 대비 부실")으로 확립. 씬 props를 쓸 때 아래를 자기 점검표로 쓴다.
> 위반한 씬은 "슬라이드"지 "영상"이 아니다.

```text
너는 다크 모션그래픽 연출가다. 각 씬을 다음 규칙으로 저작하라:

[크기] 히어로 위젯이 프레임 면적의 45~65%를 점유해야 한다.
       1920×1080 기준 히어로 최소 폭 900px. 어둠에 떠 있는 작은 섬을 만들지 마라.

[레이어] 씬당 3~5층을 쌓아라 — ① 무대(stage, intensity 1.3~1.7)
       ② 히어로 위젯 1개 ③ 보조 크롬 1~2개(pillBadge·마퀴·미니 카운트업·낙관)
       ④ 워터마크 글리프(선택) ⑤ 씬별 자막.
       단, 보조는 히어로와 경합하지 않게 가장자리·하단에 작게.

[상시 모션] 어느 프레임을 멈춰도 무언가 움직이고 있어야 한다.
       위젯 애니메이션 길이(sweepFrames·countFrames·populateFrames)를
       씬 길이의 60~80%로 늘려 잡고, 마퀴·파티클·ink-wash로 잔여 시간을 채워라.
       단, 움직임의 주체는 카메라·무대·값 애니메이션이다 —
       **위젯 자체는 정착 후 완전 고정** (개별 흔들림은 떨림으로 읽혀 전문성을 해침).

[카메라] 기본 고정(none). 지속 확대/이동은 조잡함으로 읽힌다 — 프레임은 방송 그래픽처럼
       안정적으로. 카메라 이동은 특별한 연출 의도가 있을 때만 opt-in (amount ≤0.05).

[리듬] 플래시는 느낌표다 — **영상 전체에서 2~4회만**, 서사의 정점(핵심 수치 착지·선언·낙관)에.
       씬마다 치는 것 금지. 플래시는 반드시 시각 사건(착지·슬램)과 같은 프레임에 —
       정지 화면 위에 치면 스트로브로 읽힌다.

[전환] 기본은 클린 컷(none). light-sweep은 장(章)이 바뀔 때 1~3회.
       white-flash 전환은 클라이맥스 컷 전용.

[타이포] 수치·키워드는 heroTitle·countUp으로 화면을 채워라.
       설명은 자막에, 강조는 타입에. 작은 텍스트로 정보를 전달하려 하지 마라.
       **글로우 금지 — 서체는 항상 크리스프** (원본의 상시 타입은 완전 플랫.
       글로우는 조명 이벤트지 서체 속성이 아니다).
```

## 에이전트 행동 계약

1. 위젯 id·props는 catalog.json에 있는 것만 쓴다 — 즉흥 필드 금지 (zod strict가 거부).
2. 새 위젯이 필요하면 이 스킬에서 만들지 않는다 — `src/promo/` 라인에 컴포넌트+스키마+catalog+테스트 4종 세트로 편입하는 별도 작업이다.
3. 색·폰트·이징은 토큰(`src/promo/tokens.ts`)이 결정한다. props로 색을 흉내 내지 않는다.
4. 페이지당 5초 고정이 맞지 않는 요청(가변 씬 길이·오디오 동기)은 이 스킬 v0 범위 밖이다 — 정직하게 한계를 말하고 후속 작업으로 넘긴다.
5. 원본(KIMI-K3 영상)의 텍스트·수치·로고를 그대로 복제한 산출물을 배포용으로 만들지 않는다 — 위젯은 재사용 자산이고, 콘텐츠는 사용자 것이어야 한다.

## 검증 근거

- 위젯 31종 census와 시각 문법: [external_samples/KakaoTalk_Video_2026-07-18-19-03-47_분석.md](../../external_samples/KakaoTalk_Video_2026-07-18-19-03-47_분석.md)
- 자산화 구조·개발 이력: [external_samples/implement_20260718_212631.md](../../external_samples/implement_20260718_212631.md)
- 정합 게이트: vitest(`tests/promo-widgets.test.tsx`) + pytest(`pipeline/tests/test_promo_widget_catalog.py`) —
  catalog ↔ registry ↔ zod schema 3중 일치 강제
