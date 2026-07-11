# brush_remotion_video 이전 계획서

> new-video-gen의 화이트 브러쉬 드로잉 기능을 독립 스킬 프로젝트로 추출하는 계획.
> 목표: **자막(SRT) + 음성만 있으면 드로잉 영상을 자동 생성**하는 완전 독립 프로젝트 + 스킬.
> 작성일: 2026-07-10 (new-video-gen 상세 분석 기반)

---

## 1. 분석 요약 (이전 전략의 근거)

### 1-1. 렌더 코드는 코어와 결합도 0 — 그대로 추출 가능

`src/remotion/`의 브러쉬 렌더 경로는 **react + remotion 외에 어떤 코어 모듈도 import하지 않음**을
전수 grep으로 확인했다. StackNode 코어(`common/`, `nodes/`, `layouts/`, `@/types`)와의 유일한
접점은 `Root.tsx`의 컴포지션 등록뿐이다. 자막·타이틀·팔레트·아이콘까지 브러쉬 파일 안에
자체 구현되어 있다 (`SubtitleBar`/`SvgIcons`/`theme.ts` 미사용).

| 파일 | 줄수 | 역할 |
|---|---|---|
| `src/remotion/BrushDrawScene.tsx` | 760 | 메인 씬: 2단계 수묵화 리빌(스트로크→develop), PenCursor, 자막, TopTitle, NaturalEffect, brushDynamics |
| `src/remotion/BrushDrawSequence.tsx` | 69 | 멀티씬 시퀀서 (`<Sequence>` 연결 + 공용 Audio) + duration 계산 |
| `src/remotion/WhiteWidgetLayer.tsx` | 402 | 레거시 위젯 4종 (stat/donut/bars/text) + Azure 위젯 위임 |
| `src/remotion/WhiteBrushWidgetLayer.tsx` | 296 | 카탈로그 위젯 ~50종 (12 카테고리) |
| `src/remotion/WhiteBrushContainerLayer.tsx` | 320 | 컨테이너 9종 |
| `src/remotion/white-widgets/` (13파일) | 357 | Azure 데이터 시각화 위젯 9종 (자체 theme/types 포함, self-contained) |
| `src/remotion/index.ts` | 9 | registerRoot (그대로 사용) |
| `src/remotion/Root.tsx` | 132 | **유일한 코어 혼합 지점** → 새로 작성 필요 |

**컴포지션 3종** (모두 fps 30):

| ID | 용도 | 해상도 | duration |
|---|---|---|---|
| `BrushDrawSkill` | 단일 씬 (10초형) | 1920×1080 | props 고정 (calculateMetadata 없음) |
| `BrushDrawWhiteSequence` | 멀티씬 유튜브형 | 1920×1080 | scenes 합산 자동 계산 |
| `BrushDrawWhiteShorts` | 멀티씬 쇼츠형 | 1080×1920 | scenes 합산 자동 계산 |

### 1-2. 위젯 시스템은 4계층 — 전부 self-contained라 100% 이전 가능

| 계층 | scene 키 | 타입 수 | 정의 위치 |
|---|---|---|---|
| 레거시 위젯 | `widgets[]` | 4 (`text`,`stat`,`donut`,`bars`) | WhiteWidgetLayer.tsx L5–58 |
| Azure 데이터 위젯 | `widgets[]` (통합 union) | 9 (data-table-v2, line/multi-bar/stacked-bar/pie/gauge/sparkline/quadrant/funnel) | white-widgets/types.ts |
| 화이트 컨테이너 | `whiteContainers[]` | 9 (SceneRoot, SafeArea, Stack, Grid, Split, Overlay, AnchorBox, FrameBox, ScatterLayout) | WhiteBrushContainerLayer.tsx |
| 화이트 위젯 카탈로그 | `whiteWidgets[]` | ~50 / 12 카테고리 | WhiteBrushWidgetLayer.tsx |

세 레이어는 BrushDrawScene 안에서 z-index 22~23으로 병렬 마운트된다.
실사용 검증 데이터: `idea-to-product-brush-white`가 whiteWidgets 60개(29개 타입) 사용,
데모 props 2종이 50종 전수 + 컨테이너 9종 전수를 커버 → **전수 렌더 검증 가능**.

### 1-3. 파이썬 파이프라인 — 재사용 코어 8개 + 복붙 빌더 42개

`scripts/brush-draw/` 50개 스크립트(1.4만 줄)에 **공유 모듈이 전혀 없다.**
공유는 subprocess로 헬퍼를 호출하는 방식뿐이고, 나머지(run 래퍼, ffprobe, 오디오 합성,
QA HTML, smoothstep 등)는 파일마다 복사-붙여넣기 되어 있다.

**재사용 코어 (이전 대상):**

| 스크립트 | 역할 |
|---|---|
| `generate-pen-contour-routes.py` (371L) | **파이프라인 심장.** 이미지→콘텐츠 마스크→skeletonize→폴리라인 추적→RDP→seal 밴드(커버리지 ~100%)→스트로크 순서/타이밍→routes JSON |
| `clean-image-for-brush.py` | 종이색 키잉 (빈 영역 → paper 색) |
| `compose-canvas.py` | 배경 contain-fit + 위젯 패널/자막 존 예약 (right-panel/right-hero) |
| `find-empty-regions.py` | 최대 빈 사각형 탐지 |
| `place-widgets.py` | 위젯 자동 배치 (빈영역 우선) |
| `validate-layout.py` | UI 겹침 하드FAIL / 배경 겹침 소프트 / 여백≥90 검증 |
| `split-cues.py` | 긴 내레이션 → 1줄 cue 분할 (한글 글리프 비례 프레임 배분) |
| `pick-title-color.py` | 배경 도미넌트 색 → topTitle.firstWordColor |
| `apply-top-titles.py` / `apply-white-widgets.py` | 전체 씬 대상 후처리 적용기 |
| `gen-background.sh` | codex exec 내장 image_gen 배경 생성 (API키 불필요) |

**빌더 42개 (이전하지 않고 아카이브):** 프로젝트별 1회성 스크립트. 단, 그 안의 공통 패턴
(PIL 절차적 배경 합성, numpy/wave 오디오 합성, ffmpeg 믹스, 세그먼트 렌더+concat, QA 캡처)은
새 리포의 공통 모듈로 흡수한다.

**입력 모드 2가지 (둘 다 지원해야 함):**
- **내레이션 모드**: 더빙.mp3 → 로컬 whisper(small, ko) → SRT → 씬 타이밍/cues (예: adaptive-html)
- **앰비언트 모드**: SRT 없음, 고정 10초(300프레임) × N씬 + 시적 한줄 cue (예: winter, relaxing)

**외부 의존성 (전부 API 키 불필요):** PIL, numpy, scipy, scikit-image, ffmpeg/ffprobe,
로컬 whisper(.venv-whisper), codex exec image_gen(chatgpt 인증), Remotion(Chromium).

### 1-4. 데이터 스키마 — canonical은 최신 3개 프로젝트 세대

스키마 계보 5세대 중 **최신 세대(idea-to-product / winter-snow-pine / ai-personal-rules)** 를
canonical로 삼는다:

- 최상위: `projectId, title, audio, paper, faint, edgeFeather, linearDraw, brush{}, transition{}, scenes[]`
- 씬: `id, routes, durationInFrames, topTitle{}, subtitleStyle{}, cues[], naturalEffects{}, widgets[], whiteWidgets[], whiteContainers[], brushDynamics{}, developFrames, prewash*(4), outro*(3)`
- 참조 체인: render-props → `scenes[].routes` → routes JSON `meta.image` → 배경 PNG
  (모두 `public/` 기준 상대경로, staticFile 규약)
- 자막은 SRT 파일 참조가 아니라 **props 내 frame 기반 `cues[]`** (SRT는 빌드타임 산출물)
- `render-props-video-only.json` = 동일 파일에 `audio: null` (영상만 렌더 후 오디오 mux용)

구세대 필드(top-level `meta{}`, 레거시 `widgets[]`)는 컴포넌트가 optional로 처리하므로
하위호환 렌더 가능 — 기존 프로젝트 props도 새 리포에서 그대로 렌더된다.

### 1-5. 핵심 문제: 3중 사본 드리프트

동일 코드가 3곳에 존재하며 이미 어긋나 있다:

| 위치 | 상태 |
|---|---|
| `src/remotion/` (라이브) | **최신** — BrushDrawScene 760줄, 미커밋 +414줄 |
| `.claude/skills/brush-draw-reveal/src/` | 구버전 (390줄) |
| `~/.claude/skills/brush-draw-reveal/src/` | 구버전 (프로젝트 스킬과 동일) |

파이썬 헬퍼도 `scripts/brush-draw/`와 스킬 `scripts/`에 이중 존재.
→ **이전의 제1원칙: 새 리포가 유일한 소스가 되고, 스킬은 코드 사본을 내장하지 않는다.**

---

## 2. 이전 전략 결정

**채택: 클린 추출 + 재구조화 (파리티 우선, 단계적)**

- 렌더 코드(TS)는 **라이브 최신판을 그대로(verbatim) 복사** — 결합도 0이므로 수정 없이 동작.
  Phase 1에서는 파일 구조도 평평하게 유지해 import 수정을 0으로 만든다.
- 파이썬은 복사가 아니라 **패키지로 재구조화** — 42개 빌더의 복붙을 반복하지 않기 위한 핵심 결정.
- 스킬은 **코드를 내장하지 않고 새 리포를 실행 대상으로 지정**하는 얇은 스킬로 재작성.

**기각한 대안:**
- *git filter-repo / subtree 이력 보존 추출*: 브러쉬 코드 대부분이 최근/미커밋이라 보존할 이력이 거의 없음. 복잡도만 증가.
- *스킬 폴더에 코드 사본 유지 (현행 방식)*: 드리프트가 이미 발생한 방식. 반복 금지.
- *42개 빌더까지 전부 이관*: 1.4만 줄 복붙 부채를 새 리포에 그대로 옮기는 것. 공통 로직만 흡수하고 원본은 아카이브.

---

## 3. 새 리포 구조 (제안)

```
brush_remotion_video/
├── package.json               # remotion ^4.0.x + react 19 만 (Next.js 제거 → 설치/렌더 가벼움)
├── remotion.config.ts          # jpeg, h264/yuv420p, CRF 18, overwrite (기존 설정 이식)
├── tsconfig.json               # strict, bundler resolution (@/ alias 불필요 — 전부 상대 import)
├── src/
│   ├── index.ts                # registerRoot (그대로)
│   ├── Root.tsx                # ★신규: 브러쉬 3개 컴포지션만 등록 (코어 import 제거)
│   ├── BrushDrawScene.tsx      # 라이브 최신판 verbatim
│   ├── BrushDrawSequence.tsx   # verbatim
│   ├── WhiteWidgetLayer.tsx    # verbatim (평평한 구조 유지 → import 수정 0)
│   ├── WhiteBrushWidgetLayer.tsx
│   ├── WhiteBrushContainerLayer.tsx
│   └── white-widgets/          # 13파일 verbatim
├── pipeline/                   # ★파이썬 패키지 (기존 subprocess 헬퍼 → import 가능 모듈)
│   ├── __init__.py
│   ├── routes.py               # ← generate-pen-contour-routes.py
│   ├── clean.py  compose.py  regions.py  place.py  validate.py
│   ├── cues.py                 # ← split-cues.py
│   ├── title_color.py          # ← pick-title-color.py
│   ├── apply.py                # ← apply-top-titles.py + apply-white-widgets.py
│   ├── srt.py                  # ★신규: SRT 파싱 → 씬 경계/타이밍/cues
│   ├── stt.py                  # ★신규: 더빙 오디오 → whisper → SRT (내레이션 모드)
│   ├── background.py           # ★신규: 배경 전략 (image_gen / PIL 프리셋 / 사용자 이미지)
│   ├── audio.py                # 앰비언트·음악 합성 + ffmpeg 믹스 공통화 (빌더들에서 흡수)
│   ├── props.py                # canonical render-props 빌더 (스키마 단일 정의)
│   ├── renderer.py             # remotion render 호출 + 세그먼트 렌더/concat/오디오 mux
│   └── qa.py                   # 프레임 캡처, 콘택트시트, QA HTML, ffprobe/silencedetect
├── bin/
│   ├── build.py                # ★단일 진입점: project.yaml(or json) → 전체 파이프라인
│   └── qa.py                   # QA 단독 실행
├── skill/                      # 새 스킬 정의 (코드 사본 없음)
│   ├── SKILL.md
│   └── references/             # background-prompt.md, config-example.json, widget-pack.md 이식+갱신
├── public/
│   ├── brush-draw/brush.png    # 공용 붓 텍스처 (+selfcheck 골든 에셋, 5.5MB)
│   └── winter-snow-pine-demo/  # 단일씬 골든 샘플 (3.4MB)
├── data/                       # 프로젝트별 render-props (골든 샘플 3종 포함)
│   ├── golden-widgets/         # ← brush-draw-white-widgets (50종 전수)
│   ├── golden-containers/      # ← brush-draw-white-containers (9종 전수)
│   └── golden-single/          # ← winter-snow-pine-demo
├── examples/legacy-builders/   # (참고용 아카이브) 기존 42개 빌더 — 실행 보장 없음, 레시피 참조용
├── output/                     # 렌더 결과 (.gitignore)
└── docs/
    ├── schema.md               # canonical render-props + routes JSON 스키마 명세
    ├── widgets.md              # 위젯 4계층 카탈로그 (기존 docs 2종 통합·갱신)
    └── pipeline.md             # 파이프라인 스테이지 문서
```

> public/ 슬림 원칙 유지: 렌더 시 Chromium 기동 지연을 피하기 위해 프로젝트별
> `--public-dir` 분리 또는 필요 에셋만 담기 (기존 스킬의 15–26MB 권장 관행 계승).

---

## 4. 단계별 이전 계획

### Phase 0 — 원본 스냅샷 (안전장치) `[소요: 짧음]`
- [ ] new-video-gen의 미커밋 브러쉬 변경 커밋 (BrushDrawScene +414줄, Sequence, Root)
- [ ] 기준 렌더 확보: 골든 샘플 3종을 현 리포에서 렌더해 기준 mp4/스틸 보관
- **검증**: `git status` 클린, 기준 mp4 3개 존재

### Phase 1 — 렌더 파리티 (TS 이관) `[핵심 마일스톤]`
- [ ] Remotion 전용 스캐폴드 (package.json / remotion.config.ts / tsconfig.json)
- [ ] TS 19파일 verbatim 복사 (평평한 구조 → import 수정 0)
- [ ] 새 Root.tsx 작성: `BrushDrawSkill` / `BrushDrawWhiteSequence` / `BrushDrawWhiteShorts`만 등록
  - 개선 1건 포함 권장: `BrushDrawSkill`에도 calculateMetadata 추가 (props의 duration 자동 반영)
- [ ] 골든 샘플 3종의 data/public 복사
- [ ] 3종 렌더 → Phase 0 기준 렌더와 파리티 비교 (씬 스틸 diff)
- **검증**: 위젯 50종 + 컨테이너 9종 + 레거시 4종 + Azure 9종이 새 리포에서 픽셀 동등 렌더
  → **"화이트 위젯 100% 이전" 요구사항이 이 시점에 충족·증명됨**

### Phase 2 — 파이썬 파이프라인 패키지화
- [ ] 헬퍼 10종 → `pipeline/` 모듈로 이식 (argparse CLI 진입점 유지 → 기존 호출 방식 호환)
- [ ] 빌더들의 복붙 공통 로직 흡수: `audio.py`(numpy/wave 합성 + ffmpeg 믹스),
      `renderer.py`(세그먼트 렌더+concat+mux), `qa.py`(캡처/콘택트시트/HTML/음량검증)
- [ ] `props.py`에 canonical 스키마 단일 정의 (+ 스키마 검증)
- **검증**: 기존 프로젝트 1개(예: winter-snow-pine-demo)를 새 파이프라인으로 재빌드 → 동등 결과

### Phase 3 — SRT-first 자동 파이프라인 (신규 핵심 가치) ★
사용자 목표: **"자막과 SRT만 있으면 자동으로 영상 생성"**
- [ ] `bin/build.py` 단일 진입점 + `project.yaml` 설정 스키마:
  ```yaml
  projectId: my-video
  format: youtube | shorts          # 16:9 / 9:16 → 컴포지션 자동 선택
  input:
    srt: 자막.srt                    # 있으면 내레이션 모드
    audio: 더빙.mp3                  # srt 없고 audio만 있으면 whisper로 SRT 생성
    # 둘 다 없으면 앰비언트 모드 (고정 10s 씬 + 합성 BGM)
  background:
    strategy: imagegen | pil-preset | user-images
    style: ink-watercolor           # 프롬프트/프리셋 선택
  widgets: auto | none | authored   # auto = find-empty-regions + place-widgets
  ```
- [ ] SRT → 씬 분할 규칙 (cue 그룹핑, 씬당 길이 상·하한) → 씬 타이밍/cues 자동 생성
- [ ] 배경 전략 3종 연결 (image_gen / PIL 프리셋 / 사용자 제공 이미지)
- [ ] 씬별: clean → compose → routes → (widgets auto-place) → validate → props → render → QA
- **검증**: 실제 SRT+mp3 한 쌍으로 명령 1회 실행 → 완성 mp4 산출

### Phase 4 — 스킬 재패키징
- [ ] 새 `skill/SKILL.md`: 실행 대상을 brush_remotion_video 리포로 지정, 코드 사본 미내장
- [ ] references 이식·갱신 (background-prompt, config-example → canonical 스키마 반영)
- [ ] `~/.claude/skills/`에 새 스킬 설치, 구 `brush-draw-reveal` 스킬은 deprecated 표기
  (SKILL.md 상단에 "brush_remotion_video로 이전됨" 안내)
- **검증**: 새 세션에서 스킬 호출 → 새 리포에서 end-to-end 영상 생성

### Phase 5 — 정리 (선택)
- [ ] new-video-gen의 브러쉬 데이터/스크립트 정리 여부 결정 (당분간 공존 무방 — 신규 작업만 새 리포)
- [ ] 기존 대형 프로젝트(idea-to-product 등)를 새 리포에서 재렌더할 필요가 생기면 data/public 폴더째 복사로 즉시 호환

---

## 5. 위젯 100% 이전 보장 체크리스트

| 항목 | 개수 | 이전 방법 | 검증 방법 |
|---|---|---|---|
| 레거시 widgets (text/stat/donut/bars) | 4 | WhiteWidgetLayer.tsx verbatim | 골든: relaxing-nature-shorts props 또는 config-example |
| Azure 데이터 위젯 | 9 | white-widgets/ 13파일 verbatim | 골든: data-visual-widget-pack 데모 |
| whiteContainers | 9 | WhiteBrushContainerLayer.tsx verbatim | 골든: golden-containers 데모 (9종 전수) |
| whiteWidgets 카탈로그 | ~50 | WhiteBrushWidgetLayer.tsx verbatim | 골든: golden-widgets 데모 (50종 전수, 5씬) |
| 실전 조합 검증 | 60 사용례 | — | idea-to-product props 씬 발췌 렌더 |

---

## 6. 리스크와 대응

| 리스크 | 대응 |
|---|---|
| 라이브 미커밋 코드 유실 | Phase 0에서 커밋 선행 (이전 원본 기준점 고정) |
| 렌더 결과 미묘한 차이 (폰트/Chromium) | 골든 샘플 스틸 diff로 파리티 검증, remotion 버전 동일 고정 |
| 스킬-리포 재드리프트 | 스킬에 코드 사본 금지, 리포가 단일 소스 (제1원칙) |
| public 비대 → Chromium 기동 지연 | 프로젝트별 public 분리 / --public-dir 스위치 관행 유지 |
| whisper/venv 환경 의존 | pipeline에 requirements.txt + venv 부트스트랩 스크립트 명시 |
| codex image_gen 가용성 | background.py에 PIL 프리셋 폴백 내장 (기존 빌더들이 이미 검증한 경로) |

---

## 7. 이관 파일 매핑 (요약)

**TypeScript (verbatim 19파일):**
`src/remotion/{BrushDrawScene,BrushDrawSequence,WhiteWidgetLayer,WhiteBrushWidgetLayer,WhiteBrushContainerLayer}.tsx`,
`src/remotion/white-widgets/*` (13), `src/remotion/index.ts` → 새 리포 `src/` (구조 동일)
**신규 작성:** `Root.tsx` (브러쉬 3종만), `package.json`, `tsconfig.json`, `remotion.config.ts`

**Python (모듈화 이식):** `scripts/brush-draw/` 헬퍼 10종 + `gen-background.sh` → `pipeline/`
**아카이브:** 빌더 42종 → `examples/legacy-builders/`

**에셋/데이터 (골든 샘플):**
`public/brush-draw/` (5.5MB), `public/winter-snow-pine-demo/` (3.4MB),
`data/{brush-draw-white-widgets,brush-draw-white-containers,winter-snow-pine-demo}/`

**스킬:** `.claude/skills/brush-draw-reveal/references/` → `skill/references/` (갱신 후),
`SKILL.md` 신규 작성, `src/`·`scripts/` 사본은 이관하지 않음 (드리프트 차단)

**문서:** `docs/brush-draw-white-{widgets,container-types}.md` → `docs/widgets.md` 통합·갱신
