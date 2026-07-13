# Dark Random Brush Fidelity Contract

이 계약은 우주 전용 계약이 아니라 어두운 화면의 랜덤 붓 리빌 공통 계약이다.
public YAML profile은 `dark-random-brush`, historical golden과 runtime branch의
canonical key는 `cosmic-random-brush`다. 이 이름을 분리해도 route geometry와 결과를
바꾸지 않는다.

## 고정 프로파일

| 항목 | 계약 |
|---|---:|
| 캔버스 | 1920×1080 |
| fps / 길이 | 30fps / 300f / 10초 |
| routes family | `free-random-touch` |
| 기본 터치 | 36개 |
| 보완 터치 | 1~20개 |
| 붓 폭 | 230~365px |
| 마스크 커버리지 | 0.991 이상 |
| 가시 콘텐츠 커버리지 | 대표 6씬과 본편 60씬에서 0.985 이상 |
| 평균 중심 이동 | 650px 이상 |
| 최대 중심 이동 | 1200px 이상 |
| draw 시작 | 36~40f |
| draw 종료 | 210f 이하 |
| 결정성 | 동일 이미지·seed의 routes 동일 |

## 승인 골든

- seed: `260712`
- 기본/보완/전체 터치: `36 / 10 / 46`
- 붓 폭 실측: `232.8~364.2px`
- 마스크 커버리지: `0.992944`
- 평균/최대 중심 이동: `852.01px / 1928.28px`
- drawEnd: `207.31f`
- historical fixture: `tests/golden/cosmic-random-brush/`

fixture 디렉터리와 report 파일명은 호환성을 위해 변경하지 않는다. 새 문서와
project.yaml만 `dark-random-brush`를 사용한다.

## 실전 보완 기록

### 에셋

- 입력은 16:9 풀 화면을 기준으로 만들고 `fit: cover`를 사용한다.
- 주 피사체 safe margin을 확보해 crop을 방지한다. 검은 띠·빈 화면·콜라주·워터마크·의미 불명 이미지가 있으면 렌더 전에 reject한다.
- 60장은 이미지와 cue를 1:1로 고정하고, contact sheet/gallery와 SHA-256 manifest를 남긴다.

### 브러싱

- 랜덤하게 이동하는 붓의 인상을 유지하되, 이동 중 mask가 증가하지 않아야 한다.
- coverage를 위해 폭을 키우거나 semantic outline, 수백 개 stamp, bitmap fade를 사용하지 않는다.
- 36 base touch 후 같은 폭의 supplemental touch만 1~20개 허용한다.
- 보완 20개 뒤에도 0.991 미달이면 입력·profile 문제로 실패한다.

### 화면·씬

- paper는 `#01020d` 계열의 어두운 화면이며 prewash와 과도한 밝기 pulse를 금지한다.
- 1/6/60씬만 허용한다. 60씬은 18,000f/600초, 3,000f segmented render와 resume cache를 사용한다.
- 씬 경계 59개에서 이미지·오디오 bleed를 검사한다.

### 오디오

- 외부 BGM은 local catalog와 strict license preflight를 통과해야 한다.
- source pre-roll은 `sourceStartSec`로 제거하고 시작 fade는 길게 끌지 않는다(권장 0.4초).
- 끝은 약 5초 fade-out, 최종 master는 48kHz stereo로 확인한다.

## 금지 사항

- 목표 커버리지를 맞추기 위한 `brushWidth > 365`.
- 최종 bitmap fade로 미도색 영역을 숨기고 coverage 성공으로 보고하는 행위.
- 의미 영역·행성 곡선·광원 방향을 순차적으로 추적하는 semantic route.
- 수백 개의 작은 seal/stamp route.
- seed 없이 실행할 때마다 달라지는 routes.
- 터치 사이 순간이동 또는 이동 중 잘못된 마스크 증가.
- 16:9 입력을 무시한 강제 crop, 검은 띠, 피사체 잘림.

## 실패 처리

- width, timing, 이동 거리, 결정성 계약 위반은 QA hard-fail이다.
- `format: shorts`, ambient scenes가 1/6/60이 아닌 입력, 비 ambient 입력은 거부한다.
- 6/60씬에서 `user-images`가 아니거나 이미지 수가 씬 수와 다르면 거부한다.
- 60씬에서 `ambient.cues` 60개가 아니면 거부한다.
- video-auditor의 어두운 여백 letterbox WARN은 증거 스틸로 실제 밴드가 아닌지 확인 후 허용한다.

## v0.2 대표 6씬

- matrix: `tests/golden/cosmic-random-brush-v02/scene-matrix.json`
- 장면: 지구 일출, 토성 고리, 나선은하, 타란툴라 성운, 블랙홀·강착원반, 저대비 달 표면.
- 6씬은 각 300f, 총 1800f/60초다.
- 첫 씬은 v0.1 source와 geometry hash를 그대로 유지한다.
- 전체 mask와 가시 콘텐츠 coverage를 별도로 기록한다.

## v0.3 본편 60씬

- matrix: `tests/golden/cosmic-random-brush-v03/scene-matrix.json`
- 예제: `examples/cosmic-random-brush-v03/project.yaml`
- `ambient.cues`와 `background.images`는 각각 정확히 60개다.
- 모든 씬에서 전체 mask 0.991과 가시 콘텐츠 0.985를 hard gate로 검사한다.
- 최종 MP4 기반 180장 QA와 59개 씬 경계를 통과해야 한다.
