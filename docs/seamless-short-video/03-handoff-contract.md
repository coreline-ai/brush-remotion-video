# 03. Handoff 계약

## 3.1 용어

| 용어 | 정의 |
| --- | --- |
| **start_image** | 해당 씬 I2V 입력 PNG/JPEG |
| **handoff_frame** | 씬 영상에서 추출한 인계 PNG |
| **Last Usable Frame** | 원칙 마지막 프레임, 품질 문제 시 말미 0.3~0.8s 내 최후방 정상 프레임 |
| **frame0** | 생성 mp4의 디코드 첫 프레임 (start_image와 **다를 수 있음**) |
| **planned_end_state** | 스토리 계획상 종료 목표 |
| **observed_end_state** | handoff/영상 관측 후 상태 — **다음 프롬프트 우선** |

## 3.2 파일 계약

```text
scenes/scene_0N/
  start_image.png      # N=1: 생성물 / N≥2: copy(prev handoff)
  scene_0N.mp4
  handoff_frame.png
  handoff_meta.json    # t, blur, duration, warning
  planned_end_state.yaml
  observed_end_state.yaml
  video_prompt.md
  qa.json
```

### Hard — 바이트 동일

```text
sha256(scenes/scene_0{N}/start_image.png)
  == sha256(scenes/scene_0{N-1}/handoff_frame.png)   for N ≥ 2
```

CLI가 handoff 시 다음 씬 start로 복사한다. 수동 재생성 금지.

## 3.3 Last Usable Frame 선택 알고리즘 (CLI)

```text
duration = probe(video)
end_cap  = duration - 0.05s
window   = [end_cap - lookback_sec, end_cap]   # default lookback 0.8s
sample   ≈ sample_fps (default 10) frames
score    = Laplacian variance (higher = sharper)
pick     = among score ≥ min_blur (default 40), the latest t
else     = sharpest overall + warning
```

## 3.4 frame0 정합 계약 (v0.2 필수 개념)

handoff 복사 후 I2V가 끝나면, **다음 씬으로 넘어가기 전에**:

```text
frame0 = extract(scene_0N.mp4, t=0)
start  = scene_0N/start_image.png

ΔY   = mean_luma(frame0) - mean_luma(start)
MAE  = mean |RGB(frame0) - RGB(start)|   # 리사이즈 정합 후
```

| 지표 | 권장 hard (채택) | 파일럿 실패 예 (10s) |
| --- | --- | --- |
| \|ΔY\| | ≤ 3~4 | **+11.1** |
| MAE | ≤ 6~8 | **~11.4** |
| SSIM (선택) | ≥ 0.92 | — |

실패 시: 해당 씬 재생성 (seed/후보 교체). handoff 체인에 넣지 않는다.

구현 상태: 문서·운영 규칙 확정. CLI `frame0-check` / `grade-match`는 체크리스트상 후속 구현 항목  
([12-skill-adoption-checklist.md](12-skill-adoption-checklist.md)).

## 3.5 상태 이중 기록

| 필드 | 사용 |
| --- | --- |
| planned_end_state | 계획·프롬프트 초안 |
| observed_end_state | handoff 후 갱신; **다음 씬 프롬프트 3번 블록** |

예시 필드:

```yaml
scene_end_state:
  scene_end_type: hold | plant-feet | gesture | walk  # v0.2
  character_position: ...
  facing_direction: ...
  gaze_direction: ...
  body_pose: ...
  left_hand: ...
  right_hand: ...
  expression: ...
  camera: ...
  camera_motion: ...
  lighting: ...
  exposure_notes: ...   # v0.2 Look Lock 정합
  background: ...
  active_motion: ...
```

## 3.6 Immutable completed scenes

- 통과한 scene_k 산출물은 덮어쓰지 않는다.  
- 재개는 `--from scene_id` 개념으로 해당 씬부터.  
- scene_k 재생성 시 scene_{k+1..} 체인 전부 invalid → 재handoff 필요.

## 3.7 인계 금지 패턴

- Scene 02+ 에서 새 start 이미지 생성  
- QA 전 다음 프롬프트 확정  
- walk peak-swing 인계 (권장 금지)  
- 인계 직전 1초 신규 강광원·노출 ramp  
- 설명 없는 장소 텔레포트  
