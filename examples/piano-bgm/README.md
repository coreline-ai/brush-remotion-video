# piano-bgm examples

- `fantasy-30s.yaml`: D Lydian 30초 판타지 피아노. 이전 prototype의 F# 기준음 오류를 회귀 검증하는 대표 request.
- `sleep-60s.yaml`: 60초 C major 수면 피아노. 수면 주파수/드론이 아닌 실제 피아노 자장가 score만 사용한다.


- `sleep-lullaby-30s.yaml`: `sleepRoutine: lullaby` — C major/3-4/60 BPM 포근한 자장가.
- `sleep-breath-30s.yaml`: `sleepRoutine: breath` — C major/6-8/56 BPM 느린 호흡형 미니멀 피아노.
- `sleep-window-30s.yaml`: `sleepRoutine: window` — D minor/4-4/48 BPM 여백 중심 앰비언트 피아노.
- `stable-audio-epic-30s.yaml`: Stable Audio 3 MLX 명시적 1순위, 웅장한 featured 피아노 후보.
- `auto-cinematic-30s.yaml`: `engine: auto` — cinematic/featured이면 Stable Audio를 우선하고, 설치가 없으면 사유를 남긴 뒤 sample-score로 fallback.

실행은 `skill/piano-bgm/SKILL.md`를 따른다. Stable Audio는 `STABLE_AUDIO_3_MLX_ROOT` 또는 CLI 옵션으로 로컬 설치를 지정한다. generated WAV/score는 `projects/`와 `output/`에 생기며 Git 추적 대상이 아니다.
