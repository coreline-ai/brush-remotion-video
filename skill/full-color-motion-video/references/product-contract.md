# Full Color Motion 제품 계약

## 처리 경계

```text
project.yaml
  → background(user-images, cover)              public/<id>/bg/*.png
  → clean (원본 유지; 재색/종이화 없음)
  → routes (reveal: brush인 scene만)
  → motion props (별도 FullColorMotion schema)
  → Remotion FullColorMotionLandscape / Portrait / Landscape4K
  → 기존 mix/mux/qa/audit
```

기존 brush `RenderProps`와 Full Color Motion props는 별도 schema다. 따라서 `faint`, `paper`, `completionMode`, `drawingPhases` 같은 붓 전용 기본값을 승계하지 않는다.

## 모드별 사용 범위

| mode | 장면 시간 | motion.scenes 규칙 | 오디오 |
| --- | --- | --- | --- |
| ambient | 300f(10초) 고정 | 없으면 default, 있으면 ambient.scenes와 동일 | BGM/무음 |
| narration | SRT cue 그룹 | 없으면 default, 있으면 그룹 수와 동일 | 입력 오디오 또는 BGM |
| whisper | Whisper 결과 cue 그룹 | 동일 | 입력 오디오 |
| tts | TTS SRT cue 그룹 | 동일 | 생성 TTS + BGM ducking |

## 리빌 안전 규칙

- `reveal: brush`은 `routes`와 `cursor`를 포함한 props로만 렌더한다.
- route 좌표·cursor 크기는 출력 캔버스(FHD/UHD/Shorts)에 같은 비율로 맞춘다.
- reveal 마지막 28%의 mask fill은 route coverage가 아닌 **visual close** 보장이다. route 분석 실패나 빈 route는 build 실패다.
- brush reveal 중에도 동일한 image transform을 mask/cursor/base image에 적용해 경로가 밀리지 않게 한다.

## 의도적으로 제외한 기능

- 3D parallax/depth reconstruction, face/body tracking, lip sync, optical-flow interpolation
- 외부 클라우드/CI 의존. 모든 실행과 검수는 로컬에서 끝낸다.
