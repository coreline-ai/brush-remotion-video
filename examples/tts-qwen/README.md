# Qwen3-TTS Base local reference 예제

이 디렉터리는 개인 음성 파일을 포함하지 않는다. 사용자가 권리와 동의 범위를 확인한 뒤 다음 파일을 로컬에만 만든다.

```text
/Volumes/ExternalSSD/projects_7/brush-remotion-video/examples/tts-qwen/local-assets/reference/local-reference.wav
/Volumes/ExternalSSD/projects_7/brush-remotion-video/examples/tts-qwen/local-assets/reference/local-reference.txt
```

그 다음 Qwen Python과 pinned model snapshot을 준비하고 실행한다.

```bash
cd /Volumes/ExternalSSD/projects_7/brush-remotion-video
BRUSHVID_QWEN_PYTHON=/path/to/qwen-venv/bin/python \
  pipeline/.venv/bin/python scripts/tts-doctor.py --check qwen3-base
BRUSHVID_QWEN_PYTHON=/path/to/qwen-venv/bin/python \
  pipeline/.venv/bin/python bin/build.py examples/tts-qwen/project.yaml --audit
```

reference 원본 경로와 transcript 본문은 manifest·로그에 기록하지 않는다. hash와 `voice` ID만 manifest에 남는다.
