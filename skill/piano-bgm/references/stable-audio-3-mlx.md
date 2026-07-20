# Stable Audio 3 MLX 우선 생성 경로

이 참조는 Apple Silicon 로컬 환경에서 Stable Audio 3를 사용해 피아노 BGM 생성 후보를 만드는 절차다.
현재 설치된 M4 경로는 `/Volumes/ExternalSSD/projects_7/stable-audio-3-local/optimized/mlx`이며,
`sm-music` 가중치와 `./sa3` 래퍼를 사용한다.

## 선택 기준

1. **Stable Audio 3 MLX 우선**: 웅장함·박진감·시네마틱·영화 OST·게임 BGM·featured 데모처럼
   빠른 아이디어 생성과 자연스러운 곡 전개가 중요한 요청에 사용한다.
2. **Noct-Salamander 샘플 score**: 수면·명상·미니멀처럼 음 하나의 조성, 화성, 성부 진행을
   결정적으로 검사해야 하거나 모델 없이 재현 가능한 결과가 필요한 요청에 사용한다.

두 경로 모두 완성곡·외부 loop를 가져다 붙이는 방식이 아니다. Stable Audio 결과도 생성 후보이며,
사람 청취와 기술 QA 전에는 자동 BGM catalog나 최종 YouTube delivery에 등록하지 않는다.

## 실행

```bash
SA3_ROOT=/Volumes/ExternalSSD/projects_7/stable-audio-3-local/optimized/mlx
PROJECT_ID=epic-piano-30s
OUT_DIR=output/original-audio/piano-bgm/$PROJECT_ID
mkdir -p "$OUT_DIR"

"$SA3_ROOT/sa3" \
  --prompt "Epic cinematic solo grand piano, powerful dramatic chords, fast arpeggios, heroic progression, intense rhythmic ostinato, triumphant climax, instrumental only, no vocals, 128 BPM" \
  --negative-prompt "vocals, singing, lyrics, spoken words, weak performance, distorted piano" \
  --cfg 2.5 \
  --dit sm-music \
  --decoder same-s \
  --seconds 30 \
  --steps 8 \
  --seed 20260720 \
  --out "$OUT_DIR/$PROJECT_ID-stable-audio-3.wav"
```

`sm-music`은 최대 120초 음악 생성용이다. 수면/명상은 `cfg 1.0~1.5`, cinematic/featured는
`cfg 2.0~2.5`부터 시도한다. 생성 후에는 프로젝트의 공통 믹스 기준인 `-23 LUFS`, `-1 dBTP`
이하로 정규화하고 이어폰·노트북 스피커에서 각각 청취한다.

## 기록과 라이선스

Stable Audio 후보를 보존할 때 다음 정보를 함께 기록한다.

- 모델: `stabilityai/stable-audio-3-optimized`, 런타임: MLX, bundle: `sm-music`
- prompt, negative prompt, `cfg`, steps, seconds, seed
- 생성 파일 SHA-256, 생성일, `stable_audio-3` 저장소 커밋 또는 설치 버전
- 모델 카드와 라이선스 URL: [Hugging Face model card](https://huggingface.co/stabilityai/stable-audio-3-optimized),
  [Stability AI License](https://stability.ai/license)

모델 카드는 `stable-audio-community` 라이선스를 명시하고 상업 사용 시 Stability AI 라이선스를
참조하도록 한다. 개인 또는 연 매출 100만 달러 미만 조직의 상업 사용과, 그 이상 조직의 Enterprise
License 조건을 구분한다. YouTube 업로드에서는 AI 생성 음악 공개 및 YouTube 수익화 정책도 별도로
확인한다.

현재 이 경로는 `bin/piano-bgm.py`에 통합된 1순위 생성 엔진이다. 직접 `sa3`를 호출할 수도 있지만,
재현 metadata·atomic output·공통 master/delivery·`generated-bgm-manifest.json`을 만들려면 다음 통합 CLI를 우선 사용한다.

```bash
cd /Volumes/ExternalSSD/projects_7/brush-remotion-video
export STABLE_AUDIO_3_MLX_ROOT=/Volumes/ExternalSSD/projects_7/stable-audio-3-local/optimized/mlx
pipeline/.venv/bin/python bin/piano-bgm.py build \
  --request examples/piano-bgm/stable-audio-epic-30s.yaml
pipeline/.venv/bin/python bin/piano-bgm.py review --project-id epic-piano-30s
```

`build`는 기술 QA 후 `PENDING_USER_LISTENING`으로 멈춘다. 이어폰과 노트북 스피커에서 확인한 뒤
두 필드를 모두 `pass`로 작성해 `approve`를 실행해야 `APPROVED`가 된다. 기존 BGM catalog나 영상
자동 선택에는 별도 등록 검토 전까지 연결하지 않는다.
