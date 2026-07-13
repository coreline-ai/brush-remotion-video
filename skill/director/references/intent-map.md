# 의도 매핑 — 일반 표현 → 전문 번역 → 파라미터

권장값은 실측 분포(1,500+ 씬) 기반. 범위를 벗어난 값을 제안하지 않는다.

## 붓 · 드로잉 느낌

| 사용자가 이렇게 말하면 | 전문 번역 | 파라미터 (실측 근거) |
|---|---|---|
| 천천히 / 여유롭게 / 명상하듯 그려지게 | 드로잉 타임라인 연장 + 등속 | `linearDraw: true` + `brushDynamics.drawSpeedScale: 1.1~1.17` (med 1.06, max 1.17) |
| 빠르게 / 경쾌하게 | 타임라인 단축 | `drawSpeedScale: 0.8~0.95` |
| 붓 터치 진하게 / 굵게 | 스트로크 터치 확대 | `touchScale: 1.4~1.55` (med 1.46) |
| 손맛 나게 / 자연스럽게 흔들리게 | 터치·경로 지터 | `touchJitter: 0.2~0.28` (med 0.22), `pathJitter: 30~48` (med 44) |
| 여기저기서 동시에 그려지듯 | 스트로크 순서 랜덤화 | `randomizeOrder: true, randomReverse: true` (실전 76%) + `seed` 고정 |
| 은은하게 / 수묵화처럼 옅게 | faint 하향 | `faint: 0.5~0.65` (진하게: 0.72~0.76) |
| 경계 부드럽게 / 붓 번짐 느낌 | 에지 페더 | `edgeFeather: 10~14` (med 12) |

## 씬 시작 · 끝 · 전환

| 표현 | 번역 | 파라미터 |
|---|---|---|
| 처음에 살짝 보여줬다 그리기 / 몽환적 도입 | 프리워시 예고 | 첫 씬만: `prewashOpacity: 0.5~0.7, prewashFrames: 24~48, prewashHoldFrames: 8~12, prewashBlur: 7~16` |
| 끝에서 부드럽게 사라지게 / 끊기지 않게 | 아웃트로 워시 dissolve | `outroFadeFrames: 18` (길게: 45~90), `outroWashOpacity: 0.9`, `outroBlur: 1.4` (강한 블러 오버랩: 8) |
| 완성되고 잠깐 감상하게 | develop 후 홀드 | `developFrames: 18~24` + 씬 duration 여유 (routes 기준 develop 후 ~60f 홀드) |
| 벌렁거림/꿀렁거림 없이, 다른 액션 없이 색감만 진하게 | 무펄스 자연 정착 | 일반 brush 기본 `integrated-develop`, prewash/effect/parallax/blur 0, `colorSettleFrames` 뒤 최소 12f 홀드 |

## 분위기 · 파티클 (전부 opacity 0.02~0.05로 은은하게)

| 표현 | kind | 비고 |
|---|---|---|
| 안개 / 아침 숲 / 차분한 | `mist` | 실전 최다 (67%) |
| 빛 내리는 숲 / 먼지 반짝 | `forestDust` | 골드빛 입자 |
| 시냇물 / 물빛 반짝 | `streamSparkle` | 물줄기 + 스파클 |
| 바람 / 들판 | `meadowWind` | 흐르는 바람 선 |
| 노을 / 따뜻한 저녁 | `sunsetGlow` | 광원 그라데이션 |
| 밤하늘 / 별 / 겨울밤 | `starTwinkle` | + `endFadeOpacity`로 밤 마무리 가능 |
| 살아있는 느낌 / 미세한 줌 | parallax | `parallaxScale: 1.02~1.03` (develop 후 부유) |

> `parallax`는 정지 레이어의 2D 깊이 근사다. 사용자가 실제 pan/zoom/arc/orbit/tracking/FPV나
> 장면 통과를 요청하면 [camera-intent-map](camera-intent-map.md)에서 canonical 기법과 타깃
> 호환성을 해석한다. 그 결과는 선택적 Camera Prompt Pack이며 미지원 YAML 필드가 아니다.

## 텍스트 · 정보 요소

| 표현 | 번역 | 파라미터 |
|---|---|---|
| 제목 넣어줘 / 주제 딱 보이게 | 상단 타이틀 | `topTitle{kicker, lines, fontSize: 42~44, enterAt: 8~20, wash: 배경 위면 true, firstWordColor: 배경 인상색}` |
| 자막 / 내레이션 문구 | 자막 큐 | `cues[]` (SRT/대본에서 자동 생성됨 — 수동은 앰비언트 모드) |
| 수치 보여줘 / 통계 / 차트 | 위젯 매핑 | 수치 1개→`stat`, 비율→`donut`, 추이→`bars`, 비교→`CompareBars`, 표→`DataTable`, 단계→`ProcessStepCard`/`TimelineStepper`, 흐름→`FlowDiagram`, 목록→`BulletList`, 인용→`QuoteText`, 대화→`ChatBubble`, 인물→`PersonAvatar`, 경고→`WarningCard` |

## 오디오

| 표현 | 번역 | 파라미터 |
|---|---|---|
| 잔잔한 음악 / 피아노 / BGM | YouTube 허용 Honor | `bgm{mode: asset, assetId: youtube-chris-zabriskie-fight-for-your-honor}` |
| 외곽선 후 채색 + 잔잔한 음악 | Satya Yuga + pen-brush | `drawing.profile: pen-brush` + `youtube-jesse-gallagher-satya-yuga` |
| Pixabay 음악 / Pixabay BGM | **YouTube·Shorts 사용 금지** | 로컬 청취·내부 데모만 허용하고 배포 YAML에는 넣지 않음 |
| 10분 초과 / 긴 영상 | 2~3곡 playlist | `bgm.mode: playlist`, `crossfadeSec: 3` |
| 목소리로 읽어줘 / 더빙 | TTS 내레이션 | 일반 `female-01`, 전문 `female-09`, 동화 `female-08`, 쇼츠 `female-07`, 힐링 `female-05`, 장편 다큐 `female-06`; `speed: 1.10`을 명시. 사용자 지정 우선 |
| 내 목소리 녹음 사용 | 실더빙 우선 | `input.audio` (tts 있어도 실더빙 우선) |
| 빗소리 / 장작 소리 / 파도 | **환경음은 확장 후보 (미구현)** | 음악 BGM은 지원하지만 별도 환경음 레이어는 추가 개발 필요 |

## 드로잉 프로파일

| 표현 | 번역 |
|---|---|
| 펜으로 / 스케치처럼 / 화이트보드 / 손그림 설명 | **pen 프로파일** — `drawing: {profile: pen}` (pen-video 스킬로 위임: 잉크만 빠르게 그려짐) |
| 외곽선을 먼저 그리고 채색 / 펜 다음 브러시 / 선화 완성 후 색칠 | **pen-brush 프로파일** — `drawing: {profile: pen-brush}` (pen-brush-video로 위임: outline→paint 2단계) |
| 붓으로 / 수묵화 / 잔잔하게 그려지는 | **brush 프로파일(기본)** — 수묵 faint 리빌 + develop |
| 어두운 화면 / 우주·행성·성운·심해·야간 풍경을 랜덤 붓 터치로 / golden-single-widgets 같은 브러싱 | **dark-random-brush 프로파일** — `drawing: {profile: dark-random-brush, seed: <고정값>}` (`dark-random-brush-video`로 위임; runtime은 `cosmic-random-brush` 호환키) |

## 포맷 · 구성

| 표현 | 번역 |
|---|---|
| 쇼츠 / 세로 / 릴스 / 힐링 짧은 영상 | **shorts-brush 스킬로 위임** — `format: shorts` (세로 파이프라인 + 세이프존·강조색 동조·루프 엔딩 자동) |
| 유튜브 / 가로 | `format: youtube` (1920×1080) |
| N개 장면 / 길이 ~초 | 앰비언트: `ambient.scenes: N` (씬당 10초) · 내레이션: SRT/대본 길이가 결정 |
| 씬마다 다른 그림 | 배경 N장 생성 (`background.strategy`) — imagegen(주제 프롬프트) / preset(결정적) / user-images |

## 카메라·시점·렌즈·전환 표현

- `당겨 줘`, `돌아 줘`, `뒤에서 따라가 줘`, `지구 밖까지 멀어져 줘` 같은 표현은
  [camera-intent-map](camera-intent-map.md)에서 먼저 해석한다.
- 정확한 37개 canonical 값과 37~45 legacy alias는
  [camera prompt catalog](../../_shared/references/camera-prompt-catalog.json)가 단일 진실이다.
- 한/영 prompt 조립, `supported`/`external-required` 등의 타깃 분기는
  [camera prompt guide](../../_shared/references/camera-prompt-guide.md)를 따른다.
- 카메라 요청이 없으면 Camera Prompt Pack을 만들지 않고 기존 무드·드로잉 변환만 수행한다.
