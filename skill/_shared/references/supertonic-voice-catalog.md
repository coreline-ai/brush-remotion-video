# Supertonic 여성 음성팩 v1.0.0

기존 영상 스킬이 공통으로 사용하는 음성 카탈로그다. 별도 음성 스킬을 만들지 않으며 실제 구현은
`pipeline/brushvid/voice_presets.py`, 단일 진실은 `assets/voices/catalog.json`이다.

## 빠른 사용

```yaml
input:
  script: narration.txt
  tts:
    engine: supertonic
    voice: female-09
    speed: 1.10
    pauseMs: 350
    timing: tts
```

- 공개 ID: `female-01`~`female-10`
- 기존 호환: `F1`~`F5`는 `female-01`~`female-05`의 별칭, `M1`~`M5`도 계속 지원
- 금지: `F6`~`F10`, 숨은 `voice: auto`, 알 수 없는 ID의 F1 자동 폴백
- speed: 기본 `1.05`, 운영 허용 `0.70`~`2.00`, 음성팩 권장 `1.10`
- 실제 더빙 `input.audio`가 있으면 TTS보다 우선한다.

## 10종 선택표

| ID | 구성 | 특징 | 추천 |
| --- | --- | --- | --- |
| `female-01` | F1 | 따뜻한 균형형 | brush-video 일반·교육·설명 |
| `female-02` | F2 | 가장 밝고 생동감 있음 | 홍보·밝은 쇼츠 |
| `female-03` | F3 | 낮고 공기감 있는 차분함 | 감성·다큐·cosmic |
| `female-04` | F4 | 빠르고 또렷함 | 정보 요약·튜토리얼 |
| `female-05` | F5 | 낮고 포근하며 안정적 | 힐링·명상·수면 |
| `female-06` | F1 65% + F3 35% | 따뜻하고 차분함 | 장편 교육·다큐 |
| `female-07` | F2 60% + F4 40% | 밝고 명료함 | shorts-brush |
| `female-08` | F3 50% + F5 50% | 부드럽고 시적임 | 동화·감성 스토리 |
| `female-09` | F4 65% + F1 35% | 중립적이고 신뢰감 있음 | pen·pen-brush·전문 해설 |
| `female-10` | F5 60% + F2 40% | 포근한 강조형 | 스토리텔링·생활 콘텐츠 |

혼합 5종은 여성 F1~F5 style vector만 사용한다. Supertonic에 공식 F6~F10이 존재하는 것은 아니다.

## 조회·청취·검증

```bash
python3 bin/voice-assets.py list
python3 bin/voice-assets.py show female-09
python3 bin/voice-assets.py preview female-09
python3 bin/voice-assets.py validate
python3 bin/voice-assets.py demo --all
```

`preview`는 선택 MP3와 전체 10종 청취 HTML의 `file://` 링크를 출력한다.

## 재현성과 공개 고지

- 빌드 결과: `data/{projectId}/tts/voice-manifest.json`
- 기록값: 요청/canonical ID, voice pack·package·model 버전, 구성 비율, speed, catalog/style SHA-256
- Supertonic 모델은 OpenRAIL-M 조건을 따른다.
- 공개 영상 설명에는 다음 고지를 포함한다.

> 이 콘텐츠의 내레이션은 Supertonic AI 합성 음성으로 제작되었습니다.
