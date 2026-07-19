# TTS 엔진 카탈로그

이 문서는 `/Volumes/ExternalSSD/projects_7/brush-remotion-video` 파이프라인의 공통 TTS 선택·설치·재현성 계약이다. 실제 구현은 `pipeline/brushvid/tts.py`와 `pipeline/brushvid/tts_engines/`에 있으며, 이 문서는 엔진 선택을 위한 안내만 담당한다.

## 공통 입력

```yaml
input:
  script: narration.txt
  tts:
    engine: melo-ko
    voice: kr-default
    language: ko
    speed: 1.00
    pauseMs: 350
    timing: tts
```

- `engine`은 `supertonic`, `melo-ko`, `qwen3-base` 중 하나다. 생략 시 기존 `supertonic`이다.
- `language`는 신규 엔진에서 `ko`만 허용한다. Melo는 API에 `KR`, Qwen은 `Korean`으로 매핑한다.
- `speed`는 `0.70~2.00`의 유한 숫자이고 `pauseMs`는 0 이상 정수다.
- `input.audio`가 있으면 실더빙이 항상 우선하며 TTS는 실행하지 않는다.
- `script + srt + tts`는 텍스트 source가 모호하므로 hard fail한다.
- 모든 결과는 adapter native sample rate에서 44.1kHz mono로 정규화하고 실제 샘플 수로 SRT를 만든다.

## 최고 품질 실행 규칙

- BERT·문맥 embedding·공식 tokenizer·G2P·필수 speaker 등 모델의 정상 추론 구성요소를 비활성화하거나 영점/모의 구현으로 대체한 출력은 **비교·납품 금지**다.
- 의존성 또는 모델이 준비되지 않았으면 대체 오디오를 만들지 말고 명시적으로 중단·준비 상태를 알린다. 임시 우회 샘플은 어떤 청취 페이지에도 노출하지 않는다.
- 비교는 같은 대본과 loudness 기준에서 실시하며, 발음·억양·문장 연결·호흡감·노이즈를 사람 청취로 확인한다. 파일 생성 성공이나 파형 검사만으로 품질 합격 처리하지 않는다.
- 기본 청취 값은 `speed: 1.00`, `pauseMs: 350~450`이다. 더 차분한 요구도 작은 폭으로만 조절하고, 과도한 저속·긴 pause로 자연스러움을 위장하지 않는다.
- Melo의 `kr-default`는 단일 기본 화자다. 목표 음색을 제어해야 할 때에는 이 한계를 비교 화면과 납품 메타데이터에 명시하고 reference 기반 엔진을 별도 비교한다.

## 엔진별 계약

| ID | voice | 모델·revision | 속도 처리 | 선택 의존성 |
| --- | --- | --- | --- | --- |
| `supertonic` | 기존 F1~F5/M1~M5 또는 `female-01`~`female-10` | 기존 catalog의 `supertonic-3` | Supertonic native | `.[tts]` |
| `melo-ko` | `kr-default`만 허용, speaker `KR` 고정 | `myshell-ai/MeloTTS-Korean` @ `0207e5adfc90129a51b6b03d89be6d84360ed323` | Melo native length scale | `.[tts-melo]` |
| `qwen3-base` | reference pair를 식별하는 명시적 ID | `Qwen/Qwen3-TTS-12Hz-1.7B-Base` @ `fd4b254389122332181a7c3db7f27e918eec64e3` | 공통 `ffmpeg atempo` | `.[tts-qwen]`, 별도 Python 권장 |

Qwen은 반드시 다음 pair를 함께 받아야 한다.

```yaml
input:
  script: narration.txt
  tts:
    engine: qwen3-base
    voice: f1-reference
    language: ko
    reference:
      audio: inputs/voices/f1-reference.wav
      transcript: inputs/voices/f1-reference.txt
    speed: 1.00
    pauseMs: 350
    timing: tts
```

reference는 YAML 파일 기준 프로젝트 내부 regular file이어야 하며 symlink·`..` 경로·빈 transcript·bundled fallback을 허용하지 않는다. worker는 검증된 controlled copy만 사용하고 build 종료 시 `.work`를 삭제한다. 취소 시 worker process group에 SIGTERM을 보내고 5초 grace 후 필요하면 강제 종료하며 controlled workspace도 폐기한다. 음성 권리와 동의 범위는 제작자가 별도로 확인해야 한다.

## 설치·점검

정상 build는 network를 사용하지 않는다. 먼저 현재 checkout에서 점검한다.

```bash
cd /Volumes/ExternalSSD/projects_7/brush-remotion-video
pipeline/.venv/bin/python scripts/tts-doctor.py --check melo-ko
pipeline/.venv/bin/python scripts/tts-doctor.py --check qwen3-base
```

패키지 설치와 pinned snapshot 준비는 명시적으로 prepare할 때만 수행한다.

```bash
pipeline/.venv/bin/python scripts/tts-doctor.py --prepare melo-ko
BRUSHVID_QWEN_PYTHON=/path/to/qwen-venv/bin/python \
  pipeline/.venv/bin/python scripts/tts-doctor.py --prepare qwen3-base
```

Qwen worker는 `BRUSHVID_QWEN_PYTHON`을 지정하면 해당 Python으로 실행된다. 준비되지 않은 모델·패키지는 다른 엔진이나 다른 reference로 조용히 대체하지 않고 명확한 오류로 중단한다. idle worker의 explicit cancel command는 `CANCELLED` JSON error를 남기고 종료하며, 생성 중 취소는 client의 process-group lifecycle을 따른다.

## 산출물·고지

- `data/{projectId}/tts/narration.wav`: 44.1kHz mono WAV
- `data/{projectId}/tts/narration.srt`: 실제 문장 duration과 pause 기준
- `data/{projectId}/tts/voice-manifest.json`: 기존 Supertonic v1 또는 신규 engine v2
- manifest에는 model ID/revision, package, sample rate, speed/timing, audio hash, license, AI disclosure가 기록된다.
- Qwen v2에는 reference audio/transcript hash와 `xVectorOnlyMode=false`가 추가된다.

참조 구현의 기준은 읽기 전용 외부 저장소 `/Volumes/ExternalSSD/projects_7/tts-bench`의 `tts-bench@3958224dd6920de6f66abae878ec7e4d935e99c5`다. Melo의 임의 speaker fallback과 Qwen의 bundled reference fallback은 대상 파이프라인에서 의도적으로 제거했다.
