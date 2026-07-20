---
name: piano-bgm
description: >-
  Stable Audio 3 MLX를 1순위로 사용해 시네마틱·웅장한·게임·영화 OST 피아노 BGM 생성 후보를 만들고,
  라이선스 검증된 로컬 다중 샘플 피아노를 결정적 fallback으로 작곡·렌더·검수하는 독립 스킬.
  뉴에이지·앰비언트·수면·명상·로파이·미니멀·시네마틱·영화 OST·게임·판타지·미스터리/호러 preset을 지원하며,
  생성 후보의 provenance·라이선스·화성·성부 진행·사람 청취 gate를 확인한다.
---

# piano-bgm — 독립 피아노 BGM 제작

**실행 대상 리포**: `/Volumes/ExternalSSD/projects_7/brush-remotion-video`

이 스킬은 완성곡·유튜브 음원·데모 MIDI·외부 loop를 가져다 붙이지 않는다. 생성 후보는 아래의 두 경로 중
선택한다. 원본 sample WAV/SFZ는 `local-assets/`에만 있으며 스킬·Git·배포본에 포함하지 않는다.

## 생성 엔진 우선순위 — Stable Audio 3 MLX 1순위 제안

1. **Stable Audio 3 MLX (`sm-music`)** — 웅장한 피아노, 박진감 있는 전개, 시네마틱·영화 OST·게임 BGM,
   `purpose: featured` 데모에 우선 사용한다. 현재 M4 로컬 설치 경로와 명령은
   [Stable Audio 3 MLX 참조](references/stable-audio-3-mlx.md)에 둔다.
2. **Noct-Salamander 샘플 score (`bin/piano-bgm.py`)** — 수면·명상·미니멀, 음 단위 화성/성부 진행
   hard gate, 완전 결정적 재현이 필요한 경우 사용한다.

Stable Audio 결과는 새로 생성한 후보 WAV이지 검증된 외부 asset이 아니다. 반드시 prompt·seed·model·파일
SHA-256을 기록하고, 기술 QA와 이어폰/노트북 스피커 청취 승인을 통과하기 전에는 BGM catalog·자동 선택·
최종 YouTube delivery에 연결하지 않는다. 두 경로의 공통 후처리는 [공통 BGM 정책](../_shared/references/bgm-policy.md)을 따른다.

## 지원 preset

| preset | 연주 계약 |
|---|---|
| `new-age` | 흐르는 아르페지오와 맑은 응답 선율 |
| `ambient-piano` | 긴 여백과 낮은 음 밀도 |
| `sleep-piano` | 3/4 자장가와 해결 중심 선율 |
| `meditation-piano` | 열린 5도와 느린 호흡; 드론/주파수 톤 없음 |
| `lofi-piano` | 7th/9th 화성, 느슨한 컴핑; 드럼/노이즈 없음 |
| `minimal-ambient` | 6/8 반복 세포의 점진 변화 |
| `cinematic-piano` | 넓은 옥타브와 점층 구조 |
| `film-ost-piano` | 노래형 선율과 명확한 종지 |
| `game-bgm-piano` | 6/8 오스티나토와 짧은 훅 |
| `fantasy-piano` | Lydian 모드 색채와 고음 장식 |
| `mystery-horror-piano` | 선언된 반음/트라이톤과 침묵; 무의도 불협은 금지 |

## 요청 파일

```yaml
projectId: quiet-garden-01
kind: piano-bgm
durationSec: 60                 # 15~600초, 정확히 닫힘
preset: new-age
# sleepRoutine: lullaby     # none | lullaby | breath | window; 지정 시 preset 생략 가능
mood: warm-hopeful
purpose: background             # background | featured
engine: auto                    # auto | stable-audio-3-mlx | sample-score
prompt: ""                     # Stable Audio 선택 시 생략 가능
negativePrompt: ""             # Stable Audio 선택 시 생략 가능
cfg: 1.0                        # Stable Audio 0~10; cinematic은 2.0~2.5부터
steps: 8                        # Stable Audio 1~16
key: G-major                    # 생략 시 preset 기본값
tempoBpm: 68                    # 생략 시 preset 기본값
seed: 20260717                  # 생략 시 projectId 기반 결정값
output:
  distribution: youtube         # local | youtube | shorts
  preview: true
```

완성된 예시는 [examples/piano-bgm/fantasy-30s.yaml](../../examples/piano-bgm/fantasy-30s.yaml)에 있다.
Stable Audio 명시 예시는 [stable-audio-epic-30s.yaml](../../examples/piano-bgm/stable-audio-epic-30s.yaml), 자동 선택 예시는 [auto-cinematic-30s.yaml](../../examples/piano-bgm/auto-cinematic-30s.yaml)에 있다.

## A 방식 수면 루틴 옵션

`sleepRoutine`은 **실제 피아노 선율 중심** 수면 루틴을 고르는 옵션이다. 이 옵션은 사인파·드론·바이노럴 비트·핑크노이즈 펄스를 추가하지 않으며, 아래의 기존 preset/기본 조성/템포를 안전하게 선택한다. `preset`은 생략할 수 있고, 지정하면 profile과 일치해야 한다.

| sleepRoutine | 선택되는 preset | 기본 조성·템포 | 성격 |
|---|---|---|---|
| `lullaby` | `sleep-piano` | C major · 60 BPM · 3/4 | 포근한 자장가 |
| `breath` | `minimal-ambient` | C major · 56 BPM · 6/8 | 느린 호흡·점진 변주 |
| `window` | `ambient-piano` | D minor · 48 BPM · 4/4 | 넓은 여백의 밤 창가 |

```yaml
projectId: sleep-lullaby-30s
kind: piano-bgm
durationSec: 30
sleepRoutine: lullaby
purpose: background
seed: 20260720
output: {distribution: local, preview: true}
```

대표 3종 request는 [examples/piano-bgm/sleep-lullaby-30s.yaml](../../examples/piano-bgm/sleep-lullaby-30s.yaml), [sleep-breath-30s.yaml](../../examples/piano-bgm/sleep-breath-30s.yaml), [sleep-window-30s.yaml](../../examples/piano-bgm/sleep-window-30s.yaml)에 있다.

## 실행 순서

```bash
cd /Volumes/ExternalSSD/projects_7/brush-remotion-video

# 1순위: 통합된 M4 로컬 Stable Audio 3 MLX 후보 + 공통 QA
export STABLE_AUDIO_3_MLX_ROOT=/Volumes/ExternalSSD/projects_7/stable-audio-3-local/optimized/mlx
pipeline/.venv/bin/python bin/piano-bgm.py validate \
  --request examples/piano-bgm/stable-audio-epic-30s.yaml
pipeline/.venv/bin/python bin/piano-bgm.py build \
  --request examples/piano-bgm/stable-audio-epic-30s.yaml

# engine:auto: cinematic/featured이면 Stable Audio, 미설치이면 sample-score fallback
pipeline/.venv/bin/python bin/piano-bgm.py build \
  --request examples/piano-bgm/auto-cinematic-30s.yaml

# 2순위 fallback: request/조성/key를 먼저 검증하는 결정적 샘플 score
pipeline/.venv/bin/python bin/piano-bgm.py validate \
  --request examples/piano-bgm/fantasy-30s.yaml

# Stable Audio에는 symbolic score가 없으므로 compose 대신 generate/build를 사용한다.
# sample-score 경로의 score + 화성/성부 진행 lint만 생성
pipeline/.venv/bin/python bin/piano-bgm.py compose \
  --request examples/piano-bgm/fantasy-30s.yaml

# 실제 local SFZ/WAV sample render + 48k/24 master + 44.1k/16 delivery + 기술 QA
pipeline/.venv/bin/python bin/piano-bgm.py build \
  --request examples/piano-bgm/fantasy-30s.yaml

# 사람 청취 파일/JSON template 생성
pipeline/.venv/bin/python bin/piano-bgm.py review --project-id fantasy-garden-30s
```

`build` 결과는 기술적으로 통과해도 `PENDING_USER_LISTENING`이다. 이어폰과 노트북 스피커에서
`listening-review.html`을 듣고, 두 환경 모두 `pass`로 기록한 JSON을 가져와야 최종 승인된다.

```bash
pipeline/.venv/bin/python bin/piano-bgm.py approve \
  --project-id fantasy-garden-30s \
  --review-result output/original-audio/piano-bgm/fantasy-garden-30s/listening-result.json
```

## 품질 gate

WAV 렌더 전에 다음은 hard fail이다.

- declared key 밖의 비의도 음 (예: G major의 F natural, A major의 D#/F/A#/C)
- 강박에 놓인 비화성음, 해결되지 않는 tension
- 왼손/오른손 성부 교차, 가까운 register의 반음·온음·트라이톤 충돌
- 15~600초 범위/음역/velocity/event 범위 위반

렌더 후에는 실제 SFZ region 선택, raw/master 포맷, 정확한 길이, 무음, true peak, provenance와
sample archive SHA-256·CC BY attribution을 검사한다. 기술 PASS는 청취 승인과 다르다.

## 산출물

```text
projects/piano-bgm/<projectId>/
  request.yaml · score.json · performance.json · composition-report.json
output/original-audio/piano-bgm/<projectId>/
  source.wav · generation.json                 # Stable Audio 후보일 때
  raw-48k24.wav · master-48k24.wav · <projectId>-44k16.wav
  preview-30s-44k16.wav · render-report.json · provenance.json · qa.json
  listening-review.html · listening-result.json · youtube-description.txt
```

- `48kHz/24-bit`은 보존/영상 믹스 입력, `44.1kHz/16-bit`은 전달용 WAV다.
- sample-score YouTube/Shorts에는 `youtube-description.txt`의 Noct-Salamander CC BY 3.0 출처·변경 고지를 사용한다.
- Stable Audio 후보는 `stable-audio-community` 모델 라이선스와 생성 provenance를 별도로 기록한다. 모델 라이선스가
  YouTube 수익화 승인이나 Content ID 미등록을 보장하지 않으므로 업로드 시 YouTube AI 공개·수익화 정책을 따로 확인한다.
- Content ID 미등록을 보장할 수 없으며, shared sample source 기반 결과를 Content ID에 등록하지 않는다.
- 생성된 BGM은 사람이 승인될 때까지 전역 BGM catalog/default에 등록하지 않는다. 다만 `bin/build.py`의
  일반 preview/audit은 프로젝트별 `piano-auto` 후보를 사용할 수 있고, `--final`은 명시적
  `bgm.mode: piano-auto`와 `APPROVED` manifest를 요구한다.

## 문제 해결

- `scale-mismatch`, `strong-beat-non-chord`, `attack-collision` → score가 실패한 것이므로 WAV를 수동 수정하지 말고 request/preset을 수정한다.
- `sample WAV 없음` → `local-assets/instruments/noct-salamander-grand-v6-1a/`의 로컬 라이브러리를 준비한다. 원본 sample을 Git에 추가하지 않는다.
- `PENDING_USER_LISTENING` → 오류가 아니라 필수 사람 청취 gate다. 승인 전에는 “배포 완료”로 표시하지 않는다.
- 영상에 삽입할 때는 이 스킬의 delivery를 기존 [공통 BGM 정책](../_shared/references/bgm-policy.md)에 따라
  `-23 LUFS` 영상 믹스로 처리한다. `bin/build.py` 공유 영상 스킬은 무음 15~120초 영상에서
  Stable Audio 피아노 후보를 1순위로 시도하며, 음성 영상은 명시적 `piano-auto`일 때만 생성한다.
