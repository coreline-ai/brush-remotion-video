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
    engine: supertonic       # 현재 supertonic만 지원 (설치: pip install -e "pipeline[tts]")
    voice: F1                # F1~F5(여성) / M1~M5(남성)
    pauseMs: 350             # 문장 사이 무음(ms)
    timing: tts              # tts(기본) — 합성 음성 길이가 타이밍의 시계
                             # ③ 아무 입력도 없음 → 앰비언트 모드

background:
  strategy: imagegen         # imagegen | preset | user-images
  style: ink-watercolor      # 프롬프트/프리셋 선택자
  images: [a.png, b.png]     # user-images일 때 씬 순서대로

widgets: none                # none | authored (scenes[].widgets를 props에서 직접 작성)
                             # auto는 위젯 자동 배치 통합 후 활성화 예정

ambient:                     # 앰비언트 모드 전용 (선택)
  scenes: 3                  # 300프레임(10초) × N
  cues:                      # 씬당 시적 한 줄 (선택)
    - "바람이 지나간 자리에 고요가 남는다"
```

## 모드별 동작 요약

| 모드 | 조건 | 씬 분할 | 자막 | 오디오 |
|---|---|---|---|---|
| 내레이션 | srt + audio | SRT 구간 그룹핑 | cue로 변환 (긴 문장 자동 분할) | 제공 오디오 mux (**tts 있어도 무시 — 실더빙 우선**) |
| whisper | audio만 | 생성된 SRT 기준 | 위와 동일 | 제공 오디오 mux |
| **tts** | (srt 또는 script) + tts | **합성 음성 길이 기준 재계산** | 문장별 cue | **Supertonic 합성 더빙** mux |
| 앰비언트 | 무입력 | 300f × N 고정 | ambient.cues 수동 | BGM 합성 (numpy, 시드 결정적) |

TTS 첫 사용 시 설치·모델 다운로드·AI 생성 고지 의무는 SKILL.md의 "TTS" 섹션 참조.

## 렌더 props와의 관계

build.py가 `data/{projectId}/props.json`(render-props v1)을 생성하고 `schema/render-props.schema.json`으로 검증한다.
세부 연출(prewash·brushDynamics·topTitle·widgets)을 조정하려면 props를 직접 수정 후 `--from render`로 재실행.
