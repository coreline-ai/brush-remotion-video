# Implementation Plan: brush_remotion_video — 화이트 브러시 드로잉 영상 생성기 (완전 신규 제작)

> SRT/음성만으로 "붓으로 그리는" 수묵화 리빌 영상을 자동 생성하는 독립 프로젝트를 처음부터 새로 만든다.
> Generated: 2026-07-11
> Project: brush_remotion_video

---

## 1. Context (배경)

### 1.1 Why (왜 필요한가)

- new-video-gen 안의 브러시 드로잉 기능은 3중 사본 드리프트(라이브 761줄 vs 스킬 사본 390줄), 5세대 누적 스키마, 복붙 빌더 42종(1.4만 줄)이라는 부채를 안고 있다.
- **이전(verbatim 복사)이 아니라 완전 신규 제작**으로 부채를 끊고, 처음부터 스키마 단일 진실 + 소형 컴포넌트 + 단일 CLI + 골든 테스트 체계로 만든다.
- new-video-gen은 **참고용 스펙 소스로만** 사용한다. 코드 복사 금지.

### 1.2 Current State (현재 상태)

- `brush_remotion_video/`에는 `MIGRATION-PLAN.md`(분석 자료로 활용)와 `docs/source-anatomy.html`(소스 해부 문서)만 존재. 코드 없음.
- 참고 스펙의 소재 (2026-07-11 검증 완료):

| 참고 대상 | 위치 (new-video-gen 기준) | 상태 |
|---|---|---|
| 씬 렌더 스펙 (튜닝 파라미터 포함) | `src/remotion/BrushDrawScene.tsx` (761줄) | **최신 — 유일 기준** |
| 시퀀서 스펙 | `src/remotion/BrushDrawSequence.tsx` (69줄) | 최신 |
| 위젯 스펙 | `WhiteWidgetLayer.tsx` / `WhiteBrushWidgetLayer.tsx` / `WhiteBrushContainerLayer.tsx` / `white-widgets/` | 최신 |
| 파이썬 파이프라인 스펙 | `scripts/brush-draw/` 헬퍼 10종 | 최신 |
| 워크플로/프롬프트 문서 | `.claude/skills/brush-draw-reveal/` SKILL.md + references | 문서만 참고 |
| QA 스킬 구조 | `skills/scene-qa-json-builder/` | 구조 참고, 스코프 재작성 필요 |
| 골든 입력 샘플 | `data/winter-snow-pine-demo/render-props.json` + `public/winter-snow-pine-demo/` | 테스트 입력으로 차용 |

- **주의**: 스킬 내장 코드 사본(`.claude/skills/brush-draw-reveal/src/`, 390줄)은 구버전. **참고 금지.**

### 1.3 Target State (목표 상태)

```bash
python bin/build.py project.yaml   # → output/{projectId}.mp4 + QA 리포트
```

- `project.yaml` 하나로: 오디오(→whisper→SRT→씬/자막) 또는 앰비언트 모드 → 배경 생성 → routes → 렌더 → mux까지 자동.
- Remotion 4.x + React 19 단독(Next.js 없음), Zod 스키마 v1이 유일한 진실.
- 레이어별 소형 컴포넌트(파일당 ~100–300줄), 위젯은 registry 패턴 핵심 10~15종.
- 골든 프레임 픽셀 diff 테스트가 1일차부터 존재.
- 스킬 2종(드로잉 생성 + QA)은 **코드 사본 없이** 이 리포를 실행 대상으로 지정하는 얇은 스킬.

### 1.4 Scope Boundary (범위)

- **In scope**: 신규 렌더 컴포넌트 일체, Zod 스키마 v1, Python `pipeline` 패키지, `bin/build.py`, 골든 테스트, 스킬 2종 재작성, 문서(schema/pipeline/widgets).
- **Out of scope**:
  - new-video-gen 코드/데이터 수정 (읽기 전용 참조).
  - 구세대 스키마 하위호환 (`meta{}`, 레거시 `widgets[]` 등) — 기존 프로젝트 재렌더는 new-video-gen에 남긴다.
  - 위젯 68종 전체 이식 — 핵심 10~15종만. 나머지는 수요 발생 시.
  - 빌더 42종 아카이브 이관.

---

## 2. Architecture Overview (아키텍처)

### 2.1 Design Diagram

```
project.yaml
    │
    ▼
bin/build.py ──────────────────────────────── 단일 진입점
    │
    ├── pipeline.stt        더빙.mp3 → whisper → SRT        (내레이션 모드)
    ├── pipeline.cues       SRT → 씬 분할 + frame 기반 cues[]
    ├── pipeline.background imagegen | preset | user-images → 배경 PNG
    ├── pipeline.routes     배경 PNG → mask → skeletonize → RDP → routes JSON
    ├── pipeline.layout     빈 영역 탐지 → 위젯 자동 배치 → 겹침 검증
    ├── pipeline.props      Zod(JSON Schema) 검증 render-props 생성
    ├── pipeline.render     npx remotion render → 오디오 mux
    └── pipeline.qa         프레임 캡처 → capture-manifest.json → QA HTML

렌더 (src/) — React 19 + Remotion 4.x
    Root.tsx ── Landscape(1920×1080) / Portrait(1080×1920) 컴포지션 2종
        └── scene/BrushScene.tsx (조립 전용, ~100줄)
              ├── RevealLayer    스트로크 리빌 + develop  ← lib/brushDynamics
              ├── CursorLayer    붓 커서 (PenPose)
              ├── SubtitleLayer  cues[] 자막
              ├── TitleLayer     topTitle (kicker+lines)
              ├── EffectLayer    naturalEffects 6종
              └── widgets/registry.ts → 핵심 위젯 10~15종
    schema.ts ── Zod 스키마 v1 (schemaVersion: 1) = 유일한 진실
                 └─ zod-to-json-schema → pipeline/props.py 검증에 공유
```

### 2.2 Key Design Decisions

| 결정 사항 | 선택 | 근거 |
|-----------|------|------|
| 코드 확보 방식 | 신규 작성 (복사 금지) | 761줄 모놀리스·스키마 부채 단절. 단, **튜닝 파라미터 값(이징 곡선, faint=0.6, prewash 기본값, brushDynamics 권장치 등)은 라이브 코드에서 읽어 스펙으로 채택** |
| 프레임워크 | Remotion 4.x + React 19 단독 | Next.js 불필요 — 설치/렌더 경량화 |
| 스키마 | Zod v1 단일 정의 + `schemaVersion` 필드 | 5세대 optional 지옥 재발 방지. JSON Schema 내보내기로 Python 검증 공유 |
| 컴포넌트 구조 | 레이어별 분리 (Reveal/Cursor/Subtitle/Title/Effect/Widget) | 761줄 모놀리스 해체, 레이어 단위 테스트 가능 |
| 위젯 | registry 패턴, 핵심셋만 (stat, donut, bars, line, pie, gauge, data-table 등) | 3중 위젯 시스템(4+9+50종) → 단일 체계 |
| 파이프라인 언어 | Python 유지 (`pyproject.toml` 패키지) | routes 생성 심장부가 scipy/scikit-image 의존 — TS 전환 비용 과대 |
| 테스트 | `remotion still` 골든 프레임 + 픽셀 diff, Phase 1부터 | 기존에 없던 회귀 안전망 |
| 스킬 | 코드 사본 없는 얇은 스킬 2종 | 드리프트(390 vs 761줄) 재발 원천 차단 |
| routes JSON 포맷 | 기존 포맷 호환 유지 (`meta{image,width,height,fps,drawStart,drawEnd,penInvisibleAfter}, strokes[]`) | 검증된 golden 샘플을 테스트 입력으로 재사용 가능 |

### 2.3 New Files (신규 파일)

| 파일 경로 | 용도 |
|-----------|------|
| `package.json`, `tsconfig.json`, `remotion.config.ts` | Remotion 전용 스캐폴드 |
| `src/index.ts` | `registerRoot` |
| `src/Root.tsx` | 컴포지션 2종 등록 + `calculateMetadata`(scenes 합산 duration) |
| `src/schema.ts` | ★Zod 스키마 v1 (RenderProps/Scene/Cue/Routes/Widget…) |
| `src/scene/BrushScene.tsx` | 레이어 조립 전용 |
| `src/scene/RevealLayer.tsx` | 스트로크 리빌 + develop + prewash/outro |
| `src/scene/CursorLayer.tsx` | 붓 커서 (PenPose 계산 포함) |
| `src/scene/SubtitleLayer.tsx` | cues 자막 |
| `src/scene/TitleLayer.tsx` | topTitle (kicker + lines + firstWordColor) |
| `src/scene/EffectLayer.tsx` | naturalEffects 6종 (mist/forestDust/streamSparkle/meadowWind/sunsetGlow/starTwinkle) |
| `src/scene/SceneSequence.tsx` | 멀티씬 `<Sequence>` 연결 + 공용 Audio |
| `src/lib/{easing,dynamics,geometry,color}.ts` | sharedProgress, brushDynamics 정규화, pointOnPolyline, hash01/jitter |
| `src/widgets/registry.ts` + `src/widgets/*.tsx` | type→컴포넌트 매핑 + 핵심 위젯 |
| `pipeline/pyproject.toml` + `pipeline/brushvid/*.py` | routes/background/cues/stt/layout/audio/props/render/qa 모듈 |
| `bin/build.py`, `bin/qa.py` | 단일 진입점 / QA 단독 실행 |
| `tests/golden/` (스틸 + `diff.py`) | 골든 프레임 회귀 테스트 |
| `skill/brush-video/SKILL.md`, `skill/qa-review/SKILL.md` + references | 얇은 스킬 2종 |
| `docs/{schema,pipeline,widgets}.md` | 명세 문서 |
| `data/`, `public/`, `output/`(.gitignore) | 프로젝트 데이터/에셋/결과 |

### 2.4 Modified Files (수정 파일)

| 파일 경로 | 변경 내용 |
|-----------|-----------|
| (없음) | 신규 프로젝트 — new-video-gen은 읽기 전용 참조. 기존 스킬 deprecated 표기는 Phase 6에서만 (`~/.claude/skills/brush-draw-reveal/SKILL.md` 상단 안내 1줄) |

---

## 3. Phase Dependencies (페이즈 의존성)

```
Phase 0 (스캐폴드+스키마)
    │
    ▼
Phase 1 (리빌 코어) ★핵심 마일스톤
    │
    ├────────────────┬─────────────────┐
    ▼                ▼                 │
Phase 2 (연출 레이어)  Phase 3 (파이프라인)   ← 병렬 가능 (TS vs Python, 접점은 스키마/routes 포맷뿐)
    │                │
    └───────┬────────┘
            ▼
       Phase 4 (SRT-first 자동화)
            │
            ├─────────────────┐
            ▼                 ▼
       Phase 5 (위젯)      Phase 6 (스킬)   ← Phase 5는 Phase 2 완료 시점부터 선행 착수 가능
```

- **병렬 1**: Phase 2(TS 연출)와 Phase 3(Python 파이프라인) — 의존 접점은 Phase 0의 `schema.ts`와 Phase 1의 routes JSON 포맷뿐.
- **병렬 2**: Phase 5(위젯)는 Phase 2 완료 후 언제든 착수 가능. Phase 6은 Phase 4 완료가 전제.

---

## 4. Implementation Phases (구현 페이즈)

### Phase 0: 스캐폴드 + Zod 스키마 v1
> 빈 컴포지션이 렌더되고, 스키마가 유일한 진실로 자리잡는다.
> Dependencies: 없음

#### Tasks
- [ ] `package.json` 작성: `remotion@^4`, `@remotion/cli@^4`, `react@^19`, `react-dom@^19`, `zod`, devDeps `typescript`, `vitest`, `zod-to-json-schema` — **remotion 3종 버전 완전 일치 고정**
- [ ] `tsconfig.json`(strict, bundler resolution, alias 없음 — 전부 상대 import) + `remotion.config.ts`(jpeg, h264/yuv420p, CRF 18, overwrite — new-video-gen `remotion.config.ts` 값 참조) + `.gitignore`(`output/`, `node_modules/`, `__pycache__/`) + `git init`
- [ ] `src/schema.ts` 작성: `CueSchema`(text/from/to), `RoutesDataSchema`(meta+strokes — 기존 포맷 호환), `BrushDynamicsSchema`, `TopTitleSchema`, `SubtitleStyleSchema`, `NaturalEffectsSchema`, `SceneSchema`, `RenderPropsSchema`(projectId/schemaVersion:1/format/audio/scenes[]) — 필드 사양은 `BrushDrawSceneProps`(라이브 L36–107) 기준으로 취사선택
- [ ] `scripts/export-schema.ts` 작성: `RenderPropsSchema` → `schema/render-props.schema.json` 내보내기 (Python 검증 공유용)
- [ ] `src/index.ts`(registerRoot) + `src/Root.tsx` 작성: `BrushLandscape`(1920×1080), `BrushPortrait`(1080×1920) 컴포지션 2종, `calculateMetadata`로 scenes 합산 duration, `defaultProps`는 스키마 파생
- [ ] `src/scene/BrushScene.tsx` 빈 골격 작성 (paper 배경색만 칠하는 placeholder)
- [ ] 렌더 스모크: 흰 배경 1초 mp4 산출 확인

#### Success Criteria
- `npx tsc --noEmit` 에러 0건
- `npx remotion compositions src/index.ts` 출력에 `BrushLandscape`, `BrushPortrait` 2종 노출
- 1초 렌더 성공 (mp4 파일 생성, ffprobe로 1920×1080/30fps 확인)
- `schema/render-props.schema.json` 생성되고 `"schemaVersion"` 포함

#### Test Cases
- [ ] TC-0.1: `RenderPropsSchema.parse(유효 props)` → 통과 (winter-snow-pine-demo props를 v1 형태로 손변환한 fixture)
- [ ] TC-0.2: `schemaVersion` 누락 props → parse 실패
- [ ] TC-0.E1: `scenes[0].cues[0].from`이 문자열이면 → ZodError에 경로 `scenes.0.cues.0.from` 포함

#### Testing Instructions
```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
npx tsc --noEmit && npx vitest run tests/schema.test.ts
npx remotion render src/index.ts BrushLandscape output/smoke.mp4 --frames=0-29
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 다음 Phase 진행 금지**

---

### Phase 1: 리빌 코어 ★핵심 마일스톤
> routes JSON → 스트로크 리빌 + develop이 기존 화질과 동등하게 재현된다.
> Dependencies: Phase 0 (schema.ts, 컴포지션 골격)

**스펙 소스**: `new-video-gen/src/remotion/BrushDrawScene.tsx` — sharedProgress(L200), pointOnPolyline(L210), hash01/jitterPoints(L117/L144), buildDynamicStrokes(L164), normalizeBrushDynamics(L128), easeDraw/easeTravel/easeDevelop(L109–112), PenCursor(L256), 본체(L554–). **로직은 새로 작성하되 이징 곡선·기본값·수식은 여기서 채택.**

#### Tasks
- [ ] `src/lib/geometry.ts`: `toPath()`, `pointOnPolyline()`, 폴리라인 길이 계산 — 라이브 수식 채택
- [ ] `src/lib/dynamics.ts`: `hash01()`, `jitterPoints()`, `normalizeBrushDynamics()`, `buildDynamicStrokes()` (drawSpeedScale/touchScale/touchJitter/pathJitter/randomizeOrder/randomReverse/seed)
- [ ] `src/lib/easing.ts`: `sharedProgress()` + easeDraw/easeTravel/easeDevelop 상수 (clamp 포함)
- [ ] `src/scene/RevealLayer.tsx`: 2단계 리빌 — ① 스트로크 마스크로 faint(기본 0.6) 리빌 ② penInvisibleAfter 이후 develop(전체 선명화, developFrames). edgeFeather(마스크 alpha 블러), linearDraw(등속), prewash 3종(Opacity/Frames/HoldFrames/Blur), outro 3종(FadeFrames/WashOpacity/Blur) 지원
- [ ] `src/scene/CursorLayer.tsx`: `getPenPose()`(진행 중 stroke 위 위치+각도) + 붓 이미지 커서(tipx/tipy 보정, travel 구간 opacity 처리)
- [ ] `BrushScene.tsx`에 RevealLayer+CursorLayer 조립, 골든 입력 준비: `data/golden-single/`에 winter-snow-pine-demo의 routes JSON·배경 PNG·brush.png 복사 + v1 스키마 props 작성
- [ ] `tests/golden/` 구축: 기준 스틸 5프레임(드로잉 초·중·후반, develop 중, 완료) 생성 스크립트 + `tests/golden/diff.py`(PIL 픽셀 diff, 평균 채널 오차 임계 2%)

#### Success Criteria
- 골든 props 10초(300프레임) 렌더 성공, 육안으로 리빌→develop 2단계 확인
- **new-video-gen에서 동일 씬을 렌더한 스틸과 5프레임 비교 — 평균 픽셀 오차 ≤ 2%** (신규 구현이므로 완전 동일은 목표 아님, "동등 화질" 판정)
- linearDraw on/off, edgeFeather 0/8, prewashFrames 0/18 조합이 각각 시각적으로 구분됨 (스틸 diff > 0)

#### Test Cases
- [ ] TC-1.1: `pointOnPolyline(points, 0)` = 첫 점, `(points, 1)` = 끝 점, `(points, 0.5)` = 경로 중간(직선 2점 케이스로 수치 검증)
- [ ] TC-1.2: `buildDynamicStrokes(seed 고정)` 2회 호출 → 완전 동일 출력 (deterministic)
- [ ] TC-1.3: `sharedProgress(frame<start)=0`, `(frame>end)=1`, 단조 증가
- [ ] TC-1.4: 골든 스틸 5프레임 diff ≤ 2%
- [ ] TC-1.E1: strokes 빈 배열 routes → 크래시 없이 배경만 develop
- [ ] TC-1.E2: `data`와 `routes`(경로) 둘 다 없으면 → 명시적 에러 문구 렌더 (침묵 실패 금지)

#### Testing Instructions
```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
npx vitest run tests/lib.test.ts
npx remotion render src/index.ts BrushLandscape output/golden-single.mp4 --props=data/golden-single/props.json
python tests/golden/diff.py --baseline tests/golden/baseline --candidate output/stills
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 다음 Phase 진행 금지**

---

### Phase 2: 연출 레이어 (자막·타이틀·이펙트·오디오·시퀀서)
> 단일 씬이 완전한 "연출된 씬"이 되고, 멀티씬 영상이 조립된다.
> Dependencies: Phase 1 / **Phase 3과 병렬 가능**

**스펙 소스**: BrushDrawScene.tsx — Subtitles(L307), TopTitle(L332), NaturalEffectLayer(L421), particleCoord(L416); BrushDrawSequence.tsx(69줄).

#### Tasks
- [ ] `src/scene/SubtitleLayer.tsx`: frame 기반 cues[] 표시, subtitleStyle 9필드(bottom/fontSize/maxWidth/paddingX·Y/color/highlightColor/background/border), 배경 해치지 않는 미니멀 스타일
- [ ] `src/scene/TitleLayer.tsx`: topTitle — kicker+lines, align 3종, enterAt 등장 모션, firstWordColor, wash 옵션
- [ ] `src/scene/EffectLayer.tsx`: naturalEffects 6종(mist/forestDust/streamSparkle/meadowWind/sunsetGlow/starTwinkle) — deterministic particle(seed), parallaxScale, endFadeOpacity
- [ ] `src/scene/SceneSequence.tsx`: scenes[] → `<Sequence>` 연결, 씬별 durationInFrames, 공용 `<Audio>` 1개(씬 간 끊김 없음), Root의 `calculateMetadata`와 duration 합산 일치
- [ ] `BrushScene.tsx` 최종 조립(레이어 z-order: Reveal < Effect < Widget자리 < Title < Subtitle < Cursor) — 조립 파일 150줄 이내 유지
- [ ] `data/golden-multi/` 작성: 2씬 + cues + topTitle + naturalEffects + audio 포함 v1 props (winter-snow-pine 에셋 재활용)
- [ ] 골든 스틸 확장: 자막 표시 중 / 타이틀 등장 / 씬 전환 직후 3프레임 추가

#### Success Criteria
- 2씬 골든 렌더: 총 duration = 씬 합산, 씬 경계에서 오디오 연속 (ffprobe로 audio stream 단일 확인)
- cues의 from/to 프레임에서 자막 등장/소멸 (스틸로 확인)
- seed 고정 시 EffectLayer 2회 렌더 스틸 diff = 0 (deterministic)

#### Test Cases
- [ ] TC-2.1: cue {from:30,to:60} → frame 29 자막 없음, frame 45 있음, frame 61 없음 (스틸 3장 검사)
- [ ] TC-2.2: scenes [300,240] → calculateMetadata durationInFrames = 540
- [ ] TC-2.3: topTitle enterAt=20 → frame 10에서 미표시(또는 opacity 0), frame 40에서 완전 표시
- [ ] TC-2.E1: cues 빈 배열 + topTitle 없음 → 크래시 없이 렌더
- [ ] TC-2.E2: naturalEffects.kind 오타(예: "mistt") → Zod parse 단계에서 거부

#### Testing Instructions
```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
npx vitest run tests/schema.test.ts tests/sequence.test.ts
npx remotion render src/index.ts BrushLandscape output/golden-multi.mp4 --props=data/golden-multi/props.json
python tests/golden/diff.py --baseline tests/golden/baseline --candidate output/stills
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 다음 Phase 진행 금지**

---

### Phase 3: Python 파이프라인 패키지
> 이미지 하나가 routes JSON과 검증된 render-props로 변환된다.
> Dependencies: Phase 0 (JSON Schema), Phase 1 (routes 포맷 확정) / **Phase 2와 병렬 가능**

**스펙 소스**: `new-video-gen/scripts/brush-draw/` — `generate-pen-contour-routes.py`(371줄, 심장부), `clean-image-for-brush.py`, `compose-canvas.py`, `find-empty-regions.py`, `place-widgets.py`, `validate-layout.py`, `split-cues.py`, `pick-title-color.py`, `gen-background.sh`. **알고리즘(마스크→skeletonize→폴리라인→RDP→seal 밴드→타이밍)은 채택하되 모듈로 재구성.**

#### Tasks
- [ ] `pipeline/pyproject.toml` + `pipeline/brushvid/__init__.py`: 패키지 스캐폴드 (deps: pillow, numpy, scipy, scikit-image, pyyaml, jsonschema), `pipeline/README.md`에 venv 부트스트랩 절차
- [ ] `brushvid/routes.py`: 이미지→콘텐츠 마스크→skeletonize→폴리라인 추적→RDP 단순화→seal 밴드(커버리지 ~100%)→스트로크 순서/타이밍→routes JSON. 커버리지 리포트 반환
- [ ] `brushvid/background.py`: 전략 3종 — `imagegen`(codex exec 호출, gen-background.sh 방식), `preset`(PIL 절차 합성 폴백), `user-images`(contain-fit) + `clean()`(종이색 키잉)
- [ ] `brushvid/layout.py`: 빈 영역 탐지(최대 빈 사각형) + 위젯 자동 배치 + 겹침 검증(UI 겹침 hard-fail, 여백≥90px)
- [ ] `brushvid/cues.py`: SRT 파싱→frame 환산, 긴 내레이션 1줄 cue 분할(한글 글리프 비례), 씬 경계 그룹핑(씬당 길이 상·하한) + `title_color()`(도미넌트 색 추출)
- [ ] `brushvid/props.py`: canonical props 빌더 + `schema/render-props.schema.json`으로 jsonschema 검증 (스키마는 TS에서 내보낸 것만 사용 — 이중 정의 금지)
- [ ] `brushvid/render.py` + `brushvid/qa.py`: `npx remotion render` 호출, 세그먼트 렌더+concat, ffmpeg 오디오 mux / 프레임 캡처→`capture-manifest.json`→콘택트시트

#### Success Criteria
- winter-snow-pine 배경 PNG 입력 → `brushvid.routes` 산출 routes JSON이 Phase 1 렌더에서 정상 드로잉 (기존 routes와 스트로크 수 ±20% 이내, 커버리지 ≥ 95%)
- `props.py`가 만든 props가 TS Zod parse 통과 (`npx tsx scripts/validate-props.ts <file>` 종료코드 0)
- pytest 전부 통과

#### Test Cases
- [ ] TC-3.1: 단순 도형 PNG(검은 원) → routes 스트로크 ≥ 1, 모든 점이 원 경계 ±밴드폭 내
- [ ] TC-3.2: 3-cue SRT(00:01→00:03 등) → cues from/to 프레임 정확 환산 (fps 30 기준 수치 검증)
- [ ] TC-3.3: `props.py` 출력 → jsonschema 검증 통과 + schemaVersion=1
- [ ] TC-3.4: `layout.py` — 위젯 2개가 서로/타이틀과 겹치면 hard-fail 리턴
- [ ] TC-3.E1: 완전 백지 이미지 → routes 빈 strokes + 경고 (크래시 금지)
- [ ] TC-3.E2: 파손 SRT(타임코드 역전) → cues.py 명시적 에러
- [ ] TC-3.E3: codex exec 부재 환경에서 `strategy: imagegen` → preset 폴백 + 경고 로그

#### Testing Instructions
```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video/pipeline
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
cd .. && npx tsx scripts/validate-props.ts data/golden-single/props.json
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 다음 Phase 진행 금지**

---

### Phase 4: SRT-first 자동화 (bin/build.py)
> `project.yaml` 하나로 mp4가 나온다 — 이 프로젝트의 존재 이유.
> Dependencies: Phase 2 + Phase 3

#### Tasks
- [ ] `brushvid/stt.py`: 더빙.mp3 → 로컬 whisper(small, ko) → SRT (기존 `.venv-whisper` 재사용 경로 + 부재 시 안내)
- [ ] `project.yaml` 스키마 확정 + 파서: `projectId, format(youtube|shorts), input{srt?, audio?}, background{strategy, style}, widgets(auto|none|authored)` — 모드 판정(srt→내레이션 / audio만→whisper / 둘 다 없음→앰비언트 10초×N)
- [ ] `bin/build.py`: 스테이지 오케스트레이션 — stt→cues→background→clean→routes→layout→props→render→mux→qa. 스테이지별 산출물 캐시(`data/{projectId}/`)와 `--from <stage>` 재개
- [ ] 앰비언트 모드: 고정 300프레임×N씬 + 시적 한줄 cue + 합성 BGM(numpy/wave — 기존 빌더 레시피 흡수)
- [ ] `bin/qa.py`: 씬별 프레임 캡처 + capture-manifest.json + QA HTML(콘택트시트) 단독 실행
- [ ] E2E 골든: 실제 SRT+mp3 한 쌍으로 `build.py` 1회 실행 → 완성 mp4 (수동 확인 체크포인트)

#### Success Criteria
- `python bin/build.py examples/narration/project.yaml` 1회 → `output/{projectId}.mp4` + `data/{projectId}/qa/` 산출, 수동 개입 0회
- 3모드(srt 제공/audio만/앰비언트) 각각 E2E 성공
- `--from render` 재실행 시 앞 스테이지 스킵 (로그로 확인)

#### Test Cases
- [ ] TC-4.1: project.yaml에 srt+audio → 내레이션 모드 판정 (whisper 미호출)
- [ ] TC-4.2: audio만 → stt 스테이지 실행 후 SRT 생성됨
- [ ] TC-4.3: 둘 다 없음 → 앰비언트 모드, scenes N×300프레임
- [ ] TC-4.E1: format 오타(`youtub`) → yaml 검증 단계 즉시 실패 (파이프라인 미진입)
- [ ] TC-4.E2: 오디오 duration과 scenes 합산 불일치 > 1초 → 경고 및 자동 보정

#### Testing Instructions
```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/pytest pipeline/tests/test_build.py -v
python bin/build.py examples/narration/project.yaml
python bin/build.py examples/ambient/project.yaml
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 다음 Phase 진행 금지**

---

### Phase 5: 위젯 registry (핵심 10~15종)
> 빈 여백에 데이터 위젯을 얹는다 — registry 패턴으로 단일 체계.
> Dependencies: Phase 2 / **Phase 4·6과 병렬 가능**

**스펙 소스**: 실사용 빈도 근거 — `data/idea-to-product-brush-white/`가 whiteWidgets 60개(29타입) 사용. 여기서 사용 빈도 상위 + 레거시 4종을 합쳐 핵심셋 확정 (Phase 착수 시 사용 통계 집계가 첫 태스크).

#### Tasks
- [ ] 핵심셋 확정: idea-to-product props의 위젯 타입 빈도 집계 → 상위 타입 + {text, stat, donut, bars} 합산 10~15종 목록을 `docs/widgets.md`에 기록
- [ ] `src/widgets/registry.ts`: `WidgetSpec`(Zod discriminated union) → 컴포넌트 매핑, 공통 배치 필드(x/y/w/h/enterAt/style) + 미등록 타입 렌더 시 placeholder+경고
- [ ] 기본 위젯 구현 1차: text, stat, donut, bars (파일당 1위젯, 등장 모션 포함)
- [ ] 데이터 위젯 구현 2차: line, multi-bar, pie, gauge, data-table 등 확정 목록 잔여분
- [ ] `schema.ts`에 `scenes[].widgets[]` 통합 (단일 union — whiteWidgets/whiteContainers 분리 개념 제거)
- [ ] `data/golden-widgets/` 데모 props: 전 위젯 1회 이상 등장하는 검증 씬 + 골든 스틸 추가
- [ ] `layout.py`의 자동 배치 대상 위젯 타입 연동 (widgets: auto 경로 검증)

#### Success Criteria
- 확정 위젯 전종이 golden-widgets 렌더에 표시 (스틸 육안 + diff 기준선 등록)
- 미등록 타입 사용 시 렌더는 계속되고 placeholder 표시 (크래시 금지)
- Zod discriminated union으로 위젯 오타 필드가 parse 단계에서 잡힘

#### Test Cases
- [ ] TC-5.1: registry에 확정 목록 전 타입 등록 확인 (vitest로 키 목록 검사)
- [ ] TC-5.2: stat 위젯 {value:"87%"} → 렌더 스틸에 텍스트 존재 (골든 diff)
- [ ] TC-5.E1: 미등록 타입 "hologram" → placeholder 렌더 + console 경고
- [ ] TC-5.E2: donut에 bars 전용 필드 혼입 → Zod parse 실패

#### Testing Instructions
```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
npx vitest run tests/widgets.test.ts
npx remotion render src/index.ts BrushLandscape output/golden-widgets.mp4 --props=data/golden-widgets/props.json
python tests/golden/diff.py --baseline tests/golden/baseline --candidate output/stills
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 다음 Phase 진행 금지**

---

### Phase 6: 스킬 재패키징 (드로잉 스킬 + QA 스킬)
> 코드 사본 없는 얇은 스킬 2종 — 드리프트 원천 차단.
> Dependencies: Phase 4 (E2E 완성) / **Phase 5와 병렬 가능**

#### Tasks
- [ ] `skill/brush-video/SKILL.md` 작성: 실행 대상을 `/Users/hwanchoi/project_202606/brush_remotion_video`로 지정, 워크플로 = project.yaml 작성→`bin/build.py`→QA 확인. **src/scripts 코드 사본 절대 미포함**
- [ ] `skill/brush-video/references/` 작성: `background-prompt.md`(기존 스킬 것 이식+갱신), `project-yaml-guide.md`(설정 스키마 전 필드), `widget-catalog.md`(Phase 5 확정셋)
- [ ] `skill/qa-review/SKILL.md` 작성: scene-qa-json-builder 구조 차용하되 스코프를 새 리포로, `bin/qa.py`가 만드는 capture-manifest.json 계약 기준으로 재작성 + `references/scene-fix-request-schema.md` 갱신
- [ ] `~/.claude/skills/`에 새 스킬 2종 설치 (`brush-video`, `brush-qa-review` — 사본이 아니라 symlink 권장, 불가 시 설치 스크립트 `bin/install-skills.sh`)
- [ ] 구 스킬 deprecated 표기: `~/.claude/skills/brush-draw-reveal/SKILL.md`와 `new-video-gen/.claude/skills/brush-draw-reveal/SKILL.md` 상단에 "brush_remotion_video로 대체됨" 1줄 안내
- [ ] `docs/schema.md`, `docs/pipeline.md` 최종화 + 루트 `README.md`(설치→build.py→QA 3단계 안내)

#### Success Criteria
- 새 세션에서 스킬 호출 → 새 리포에서 end-to-end 영상 생성 성공
- 스킬 폴더 내 `.tsx`/`.py` 실행 코드 사본 0개 (`find skill/ -name "*.tsx" -o -name "*.py"` 결과 없음, scripts 제외 확인)
- QA 스킬이 `bin/qa.py` 산출물로 QA HTML 생성

#### Test Cases
- [ ] TC-6.1: `find skill/ ~/.claude/skills/brush-video -name "*.tsx"` → 0건
- [ ] TC-6.2: 새 Claude 세션에서 "브러시 영상 만들어줘" → 스킬이 새 리포 경로에서 build.py 실행
- [ ] TC-6.E1: 구 스킬 호출 시 → deprecated 안내가 응답에 반영

#### Testing Instructions
```bash
ls ~/.claude/skills/brush-video ~/.claude/skills/brush-qa-review
find skill/ -name "*.tsx" | wc -l   # 기대: 0
# 새 세션에서 스킬 호출 E2E는 수동 확인
```

**테스트 실패 시 워크플로우:** 에러 분석 → 근본 원인 수정 → 재테스트 → **전부 통과 전 완료 선언 금지**

---

## 5. Integration & Verification (통합 검증)

### 5.1 Integration Test Plan (통합 테스트)
- [ ] E2E-1 (내레이션): 실제 더빙.mp3 1개 → `build.py` → mp4. 검증: 자막 싱크(cue 프레임 vs 오디오), 드로잉 커버리지 ≥95%, 오디오 mux 정상(ffprobe stream 2개)
- [ ] E2E-2 (앰비언트): 오디오 없는 project.yaml → 10초×3씬 + 합성 BGM mp4
- [ ] E2E-3 (쇼츠): format: shorts → 1080×1920 mp4, 자막/타이틀이 세로 세이프존 안에 위치
- [ ] E2E-4 (스킬): 새 세션 스킬 호출 → 완성 영상 (Phase 6 겸용)
- [ ] 회귀: 전체 골든 스틸 diff 일괄 실행 (`python tests/golden/diff.py --all`)

### 5.2 Manual Verification Steps (수동 검증)
1. 완성 mp4를 실제 재생 — 리빌의 "수묵화 느낌"이 new-video-gen 결과물과 동등한지 육안 비교 (기준: winter-snow-pine-demo 기존 렌더)
2. develop 시점(또렷해지는 순간)이 부자연스러운 점프 없이 이어지는지
3. 자막이 배경 그림을 가리지 않는지 (미니멀 원칙)
4. QA HTML에서 씬별 캡처가 모두 뜨고 수정요청 JSON 다운로드가 동작하는지

### 5.3 Rollback Strategy (롤백 전략)
- 신규 독립 리포이므로 기존 시스템 영향 없음 — new-video-gen과 구 스킬은 Phase 6 전까지 무변경으로 항상 사용 가능한 폴백.
- Phase 6의 구 스킬 deprecated 표기는 SKILL.md 안내 1줄뿐 — 해당 줄 삭제로 즉시 원복.
- 리포 내부는 Phase 단위 커밋 → 문제 시 해당 Phase 커밋 revert.

---

## 6. Edge Cases & Risks (엣지 케이스 및 위험)

| 위험 요소 | 영향도 | 완화 방안 |
|-----------|--------|-----------|
| 신규 구현이 기존 "수묵화 느낌"을 재현 못함 | 높음 | 튜닝 파라미터(이징·기본값·수식)를 라이브 코드에서 스펙으로 채택 + Phase 1에서 기존 렌더 스틸과 2% diff 검증을 통과해야 진행 |
| routes 알고리즘 재구성 중 커버리지 저하 | 높음 | 기존 routes JSON을 중간 fixture로 사용해 렌더(Phase 1)와 생성(Phase 3)을 분리 검증. 커버리지 리포트 ≥95% 게이트 |
| Zod↔Python 스키마 이중화 드리프트 | 중간 | JSON Schema는 TS에서만 내보내고 Python은 소비만 (단방향). CI에서 export 최신성 검사 |
| whisper venv 환경 의존 | 중간 | 기존 `.venv-whisper` 경로 재사용 + 부재 시 설치 안내. srt 직접 제공 경로가 항상 우회로 |
| codex image_gen 가용성 | 중간 | `background.py`에 PIL preset 폴백 내장 (TC-3.E3로 강제) |
| 스킬-리포 재드리프트 | 중간 | 스킬에 코드 사본 금지(TC-6.1로 강제), symlink 설치 |
| 골든 diff가 폰트/Chromium 버전에 흔들림 | 낮음 | remotion 버전 고정, 임계 2%로 여유, 기준 스틸 재생성 절차를 diff.py --update로 문서화 |
| public 비대 → Chromium 기동 지연 | 낮음 | 프로젝트별 `--public-dir` 분리 관행 유지 (기존 15–26MB 권장 계승) |

---

## 7. Execution Rules (실행 규칙)

1. **독립 모듈**: 각 Phase는 독립적으로 구현하고 테스트한다
2. **완료 조건**: 모든 태스크 체크박스 체크 + 모든 테스트 통과
3. **테스트 실패 워크플로우**: 에러 분석 → 근본 원인 수정 → 재테스트 → 통과 후에만 다음 Phase 진행
4. **Phase 완료 기록**: 체크박스를 체크하여 이 문서에 진행 상황 기록
5. **병렬 실행**: Phase 2∥3, Phase 5∥(4 완료 후) 6 병렬 가능
6. **변경 금지 영역**: new-video-gen 리포는 읽기 전용 (예외: Phase 6 구 스킬 deprecated 안내 1줄). 스킬 내장 구버전 코드 사본(390줄)은 참고도 금지 — 스펙은 항상 라이브 코드에서
7. **커밋 단위**: Phase 완료 시점마다 커밋 (메시지에 Phase 번호 명시)
