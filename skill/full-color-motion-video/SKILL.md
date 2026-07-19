---
name: full-color-motion-video
description: >-
  사용자가 준비한 컬러 정지 이미지를 색상 보존 상태로 2D 카메라 모션·환경 효과·crossfade·로컬
  BGM/내레이션/자막까지 연결하는 Full Color Motion 제작 스킬. 가로 FHD/UHD와 세로 Shorts를
  지원하며, 마지막 옵션으로 이미지를 붓 경로로 드러내는 brush reveal을 선택할 수 있다.
  "풀컬러 모션", "사진에 움직임", "켄번즈", "Full Color Motion", "붓 리빌 옵션" 요청에 사용한다.
---

# Full Color Motion Video — 독립 제품 라인 v1.0

**실행 대상 리포**: `/Volumes/Eprojects/project_202606/brush_remotion_video`  
**실행 진입점**: `bin/build.py` (`drawing.profile: full-color-motion`)  
**코드 사본 없음**: 이 스킬은 제품 선택·입력 계약·실행/QA 절차만 담고, 구현은 리포의 단일 파이프라인을 사용한다.

## 무엇을 만드는가

입력 이미지를 `cover`로 정규화한 뒤 색상·질감·구도를 보존하고, 장면별로 아래를 조합한다.

| 계층 | V1 | V2 | 선택 옵션 |
| --- | --- | --- | --- |
| 화면 | 8종 2D movement, 12종 ambient effect, 12f crossfade | 타이틀·SRT/Whisper/TTS cue 자막, Shorts safe zone | 시작 1~6초 brush reveal + cursor |
| 오디오 | 로컬 BGM 또는 의도적 무음 AAC | 실더빙/Whisper/TTS + BGM ducking | 없음 |
| 출력 | YouTube FHD 1920×1080 / UHD 3840×2160 | Shorts 1080×1920 | 같은 출력 규격 |

**정직한 범위**: 실제 3D 카메라 이동, depth 추정, 인물 추적, AI image-to-video는 하지 않는다. 정지 이미지에 적용하는 2D Ken-Burns 계열 모션과 코드 기반 효과다.

## 언제 사용하나

- 완성된 사진/일러스트를 **원본 색상 그대로** 천천히 움직이는 영상으로 만들 때
- 제품 소개, 여행/자연 B-roll, 갤러리, 교육 내레이션, 앰비언트/쇼츠에 적합
- 흰 종이 위 붓 그림이 제품 의도라면 → `brush-video` / `pen-video` / `pen-brush-video`
- 장면 간 실제 캐릭터 동작 연속이 필요하면 → `seamless-short-video`

## 필수 입력 계약

```yaml
background:
  strategy: user-images  # 필수
  fit: cover             # 필수
  images: [scene-01.png, scene-02.png]
drawing:
  profile: full-color-motion
motion:
  default:
    movement: push-in
    effect: none
```

- 이미지 수: ambient는 `ambient.scenes`와 정확히 같아야 한다. narration/TTS/Whisper는 cue 그룹으로 생긴 실제 scene 수와 `motion.scenes` 수가 같아야 한다. 불확실하면 `motion.default`만 사용한다.
- 입력 이미지는 자체 사용 권한을 확인한다. `cover`는 구도를 자를 수 있으므로 핵심 인물/텍스트를 안전영역에 둔다.
- `drawing.preserveSource`, `drawing.fullBleed`, `background.fit: contain`은 이 제품에서 허용하지 않는다.

## V1 — 원본색 모션 영상

`examples/full-color-motion/project.yaml`은 3×10초 FHD 데모다. `overlays: none`과 `bgm.mode: off`로 최소 화면/오디오 경로도 검증할 수 있다.

```bash
cd /Volumes/Eprojects/project_202606/brush_remotion_video
pipeline/.venv/bin/python bin/build.py examples/full-color-motion/project.yaml --audit
```

현재 로컬 Python venv가 없거나 깨졌다면 환경을 바꾸지 않고 다음처럼 실행한다.

```bash
PYTHONPATH=pipeline python3 bin/build.py examples/full-color-motion/project.yaml --audit
```

UHD는 `render: {resolution: uhd}`와 3840×2160 원본을 사용한다. Shorts는 `format: shorts`로 바꾸고 세로 원본을 넣는다(UHD Shorts는 지원하지 않음).

## V2 — 내레이션/자막/Shorts

| 입력 | 동작 |
| --- | --- |
| `input.srt` + `input.audio` | 실더빙 타이밍의 자막·BGM ducking |
| `input.audio` | Whisper 전사 후 cue/자막 |
| `input.script` + `input.tts` | 로컬 TTS 더빙·SRT 생성 후 cue/자막 |
| `input.srt`만 | cue/자막 검증용 무음 또는 BGM 영상 |

`examples/full-color-motion/narration-project.yaml`은 SRT cue 3개를 쓰는 V2 최소 예시다. 실제 오디오는 `input.audio` 또는 TTS를 추가한다. 세로에서는 기존 Shorts 자막 기본값(`bottom: 290`, `maxWidth: 900`, `fontSize: 36`)이 적용된다.

## scene motion 옵션

```yaml
motion:
  default:
    movement: push-in        # push-out | pan-left/right | rise/fall | arc-left/right
    effect: mist             # none | rays | mist | birds | stars | storm | sparkles
                                # lanterns | fireflies | ripples | aurora | trail
    intensity: 1.0           # 0.25~2.0
  scenes:
    - movement: arc-right
      effect: rays
      reveal: brush          # none | brush
      revealFrames: 96       # 30~180 frame (1~6초)
```

`scenes` 항목은 `default`를 상속한다. `brush`를 선택한 scene만 route를 생성하며, 마지막 28%는 전체 mask fill로 닫아 누락 픽셀로 인한 색면 팝업을 방지한다. 이 옵션은 **시작 연출**이지, 전체 씬을 다시 수묵화로 바꾸지 않는다.

## 실행 결과와 QA

```text
public/<projectId>/bg/scene-XX.png                         정규화된 원본 색상
public/<projectId>/routes/scene-XX.motion-reveal.routes.json  brush 선택 scene만
data/<projectId>/props.json                                 FullColorMotion 별도 schema props
data/<projectId>/qa/                                        opening/reveal/mid/transition capture
data/<projectId>/audit/                                     --audit 사용 시 독립 MP4 감사
output/<projectId>.mp4
```

완료 전 확인:

1. 첫/중간/전환 직전 capture에서 색상·구도·자막 safe zone 확인.
2. brush scene은 `reveal-end`에서 전체 이미지가 자연스럽게 닫히는지 확인.
3. `--audit`은 MP4의 규격·정지·하드컷·오디오를 검사한다. `WARN`은 근거 프레임을 보고 승인한다.
4. 수정은 movement/effect/reveal만이면 `--from routes`, cue/title/audio면 `--from cues` 또는 `--from props`부터 재실행한다.

## 운영 규칙

- 화면 한 장면에는 movement 1개, effect 1개만 선택한다. 과도한 효과 중첩은 하지 않는다.
- 사람 얼굴/브랜드 텍스트에는 `push-in`, `mist`, `none`부터 검토하고 강한 `storm/trail`은 피한다.
- `motion.scenes`를 확정하기 전 narration/TTS의 scene grouping을 먼저 확인한다.
- CI는 요구하지 않는다. 빌드·렌더·QA·audit은 모두 이 로컬 리포에서 수행한다.

상세 계약: [product-contract.md](references/product-contract.md) · [YAML template](references/project-template.yaml)
