# project.yaml 필드 가이드

`bin/build.py`의 유일한 입력. 검증은 `brushvid/project.py`가 수행하며 오타는 파이프라인 진입 전에 즉시 실패한다.

```yaml
projectId: my-video          # 필수. 산출 경로 data/{projectId}/, output/{projectId}.mp4
format: youtube              # youtube(1920×1080) | shorts(1080×1920) — 컴포지션 자동 선택

input:                       # 모드 판정 (우선순위 순)
  srt: path/to/자막.srt      # ① 있으면 내레이션 모드 — SRT가 씬/자막의 시계
  audio: path/to/더빙.mp3    # ② srt 없고 audio만 → whisper(small, ko)로 SRT 생성 후 내레이션
  script: path/to/대본.txt   # 대본 텍스트 — tts와 함께 쓰면 더빙+SRT 동시 생성 (단독 사용 불가)
  tts:                       # 음성 없이 더빙 자동 합성 (srt 또는 script의 텍스트 사용)
    engine: supertonic       # supertonic | melo-ko | qwen3-base (공통 카탈로그 참조)
    voice: female-01         # 여성팩 female-01~10 / 호환 F1~F5·M1~M5
    speed: 1.10              # 기본 1.05, 허용 0.70~2.00
    pauseMs: 350             # 문장 사이 무음(ms)
    timing: tts              # tts(기본) — 합성 음성 길이가 타이밍의 시계
                             # ③ 아무 입력도 없음 → 앰비언트 모드

background:
  strategy: imagegen         # imagegen | preset | user-images
  style: ink-watercolor      # 프롬프트/프리셋 선택자
  images: [a.png, b.png]     # user-images일 때 씬 순서대로

drawing:
  profile: brush             # brush | pen | pen-brush | dark-random-brush (legacy cosmic-random-brush 호환)
  seed: 1                    # profile routes 결정성. 생략 시 최상위 seed 또는 1
  preserveSource: false      # pen 전용: 완료 시 잉크 알파 대신 원본 전체 이미지 복원

widgets: none                # none | authored (scenes[].widgets를 props에서 직접 작성)
                             # auto는 위젯 자동 배치 통합 후 활성화 예정

ambient:                     # 앰비언트 모드 전용 (선택)
  scenes: 3                  # 300프레임(10초) × N
  cues:                      # 씬당 시적 한 줄 (선택)
    - "바람이 지나간 자리에 고요가 남는다"

bgm:                         # input.audio와 별도. 상세: bgm-policy.md
  mode: asset                # off | synth | asset | playlist | piano-auto
  assetId: youtube-chris-zabriskie-fight-for-your-honor
  gainDb: 5.0                # 생략: 음성 없음 +5 / 음성 있음 +3
  fadeInSec: 1.8
  fadeOutSec: 2.0
  ducking:                   # 내레이션이 있으면 생략 시 enabled=true
    enabled: true
    amountDb: 8.0
    attackMs: 120
    releaseMs: 600
  licensePolicy: strict
```

`bgm` 블록을 생략한 15~120초 무음 ambient는 Stable Audio 피아노를 자동 우선 시도한다.
음성 영상에 생성 BGM을 넣거나 생성을 고정하려면 `bgm.mode: piano-auto`를 명시한다.

## 모드별 동작 요약

| 모드 | 조건 | 씬 분할 | 자막 | 오디오 |
|---|---|---|---|---|
| 내레이션 | srt + audio | SRT 구간 그룹핑 | cue로 변환 (긴 문장 자동 분할) | 제공 오디오 mux (**tts 있어도 무시 — 실더빙 우선**) |
| whisper | audio만 | 생성된 SRT 기준 | 위와 동일 | 제공 오디오 mux |
| **tts** | (srt 또는 script) + tts | **합성 음성 길이 기준 재계산** | 문장별 cue | 선택한 TTS 엔진 합성 더빙 mux |
| 앰비언트 | 무입력 | 300f × N 고정 | ambient.cues 수동 | `bgm` 미지정은 Stable Audio 피아노 우선(15~120초), 실패 시 catalog/synth |

TTS 엔진 선택·설치·voice manifest는 [공통 TTS 엔진 카탈로그](tts-engine-catalog.md)와 [supertonic-voice-catalog.md](supertonic-voice-catalog.md),
첫 사용 설치·모델 다운로드·AI 생성 고지 의무는 SKILL.md의 "TTS" 섹션 참조.
외부 BGM 다운로드·라이선스·Content ID·등록 절차는 [bgm-policy.md](bgm-policy.md) 참조.
`format: youtube|shorts`에서는 `pixabay-*` 음원이 금지되며 preflight에서 hard fail한다.

`dark-random-brush`는 `format: youtube`, `ambient.scenes: 1/6/60`, 풀 화면 `user-images`를 사용하는 공통 다크 화면 profile이다. 기존 `cosmic-random-brush` 입력도 runtime 호환으로 계속 허용한다.
profile 전용 seed는 `drawing.seed`에 고정하고 커버리지·붓 폭은 사용자 옵션으로 변경하지 않는다.

## 렌더 props와의 관계

build.py가 `data/{projectId}/props.json`(render-props v1)을 생성하고 `schema/render-props.schema.json`으로 검증한다.
세부 연출(prewash·brushDynamics·topTitle·widgets)을 조정하려면 props를 직접 수정 후 `--from render`로 재실행.
