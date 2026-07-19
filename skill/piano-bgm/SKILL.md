---
name: piano-bgm
description: >-
  라이선스 검증된 로컬 다중 샘플 피아노만으로 새 솔로 피아노 BGM을 작곡·연주·렌더·검수하는 독립 스킬.
  뉴에이지·앰비언트·수면·명상·로파이·미니멀·시네마틱·영화 OST·게임·판타지·미스터리/호러 preset을 지원하며,
  화성·성부 진행·고음 어택 충돌을 WAV 생성 전에 검사한다.
---

# piano-bgm — 독립 피아노 BGM 제작

**실행 대상 리포**: `/Volumes/Eprojects/project_202606/brush_remotion_video`

이 스킬은 완성곡·유튜브 음원·데모 MIDI·외부 loop를 가져다 붙이지 않는다. 요청에서 생성한 새 score event를
로컬 Noct-Salamander 그랜드피아노 다중 샘플로만 연주한다. 원본 sample WAV/SFZ는 `local-assets/`에만 있으며
스킬·Git·배포본에 포함하지 않는다.

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
key: G-major                    # 생략 시 preset 기본값
tempoBpm: 68                    # 생략 시 preset 기본값
seed: 20260717                  # 생략 시 projectId 기반 결정값
output:
  distribution: youtube         # local | youtube | shorts
  preview: true
```

완성된 예시는 [examples/piano-bgm/fantasy-30s.yaml](../../examples/piano-bgm/fantasy-30s.yaml)에 있다.

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
cd /Volumes/Eprojects/project_202606/brush_remotion_video

# request/조성/key를 먼저 검증
pipeline/.venv/bin/python bin/piano-bgm.py validate \
  --request examples/piano-bgm/fantasy-30s.yaml

# score + 화성/성부 진행 lint만 생성
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
  raw-48k24.wav · master-48k24.wav · <projectId>-44k16.wav
  preview-30s-44k16.wav · render-report.json · provenance.json · qa.json
  listening-review.html · listening-result.json · youtube-description.txt
```

- `48kHz/24-bit`은 보존/영상 믹스 입력, `44.1kHz/16-bit`은 전달용 WAV다.
- YouTube/Shorts에는 `youtube-description.txt`의 Noct-Salamander CC BY 3.0 출처·변경 고지를 사용한다.
- Content ID 미등록을 보장할 수 없으며, shared sample source 기반 결과를 Content ID에 등록하지 않는다.
- 생성된 BGM은 사람이 승인될 때까지 기존 영상의 자동 BGM catalog/default에 등록하지 않는다.

## 문제 해결

- `scale-mismatch`, `strong-beat-non-chord`, `attack-collision` → score가 실패한 것이므로 WAV를 수동 수정하지 말고 request/preset을 수정한다.
- `sample WAV 없음` → `local-assets/instruments/noct-salamander-grand-v6-1a/`의 로컬 라이브러리를 준비한다. 원본 sample을 Git에 추가하지 않는다.
- `PENDING_USER_LISTENING` → 오류가 아니라 필수 사람 청취 gate다. 승인 전에는 “배포 완료”로 표시하지 않는다.
- 영상에 삽입할 때는 이 스킬의 delivery를 기존 [공통 BGM 정책](../_shared/references/bgm-policy.md)에 따라 `-23 LUFS` 영상 믹스로 처리한다. 1차 스킬은 자동 BGM 선택을 바꾸지 않는다.
