# 04. Look Lock과 경계 밝기 (Exposure Continuity)

## 4.1 문제 정의

Match Cut에서 **한 프레임 만에 화면이 밝아지거나 어두워지는** 현상.

사용자는 “마지막 이미지로 다음 영상을 만들었는데도 밝기가 바뀐다”고 느낀다.

## 4.2 원인 분리

| 가설 | 판정 (파일럿) |
| --- | --- |
| handoff 파일 ≠ start 파일 | **아님** — sha256 일치 |
| concat 버그 | **아님** — 씬 경계와 동일 패턴 |
| I2V가 start를 재조명 | **맞음** — start meanY 112.4 vs frame0 123.5 (Δ+11) |
| 씬 내부 후반 노출 ramp | **기여** — S1 first Y90 → end Y112 후 S2가 또 상향 |

핵심 불변식:

```text
제공 start_image 정합  ≠  생성 frame0 정합
supports_exact_start_frame: partial 을 전제로 설계한다
```

## 4.3 Look Lock (전 장면 공통)

Character Lock과 별도로 **조명·노출·색 온도**를 고정한다.  
`character/look_lock.md` 또는 project.yaml `look_lock:` 블록.

```yaml
look_lock:
  time_of_day: moonlit night          # 예
  key_light: soft cool moonlight from upper-left
  fill: warm character lantern only
  exposure: dim garden, no daylight, no auto-HDR
  white_balance: cool night + warm practical
  contrast: medium-low
  bloom: low, stable (no end-of-shot bloom ramp)
  forbid:
    - sunrise / golden-hour boost
    - sudden brighter grade
    - relight on cut
    - new strong light sources in last 1s
```

모든 씬 프롬프트 **2번 블록(Character) 직후 또는 1번 블록**에 동일 문단 삽입.

## 4.4 프롬프트 강화 (frame0 노출)

### 필수 삽입 (씬 02+)

```text
Frame 0 MUST match the input image in composition, lighting, exposure,
white balance, and overall brightness. Do not re-light, brighten, or change
time of day. Only begin motion after frame 0.
```

### Negative

```text
relight, auto-exposure, brighter grade, HDR boost, daylight leak,
bloom spike, fade-in from black, contrast pop
```

### 인계 직전 1초 (이전 씬 9~10s)

- 새 광원 세기 증가 금지  
- bloom/glow ramp 금지  
- “magical brighter” 류 표현 금지  

## 4.5 생성 후 Hard gate

```text
ΔY = mean_luma(frame0) - mean_luma(start_image)
pass if abs(ΔY) ≤ 4  (권장; 운영 초기 6까지 soft)
AND mean|RGB| ≤ 8
```

- 후보 3~5개 생성 후 **ΔY 최소** 클립 채택  
- 실패 시 재생성 (프롬프트 노출 문장 강화, 동작 단순화)

## 4.6 후처리: grade-match (즉시 완화)

생성 실패를 완전히 없애기 전, concat 전 보정.

### 방식 A — 클립 전체 gain

```text
gain = meanY(prev_end) / meanY(next_clip)
next' = next * gain   # luma 또는 eq
```

### 방식 B — 페더 (권장)

다음 씬 **첫 0.6~0.8초만** gain을 목표에 맞추고 linear/ease로 1.0 복귀.  
컷 순간 팝만 줄이고 중반 룩 유지.

### 방식 C — 초단 dissolve

hard gate 실패·재생성 불가 시 **0.2~0.4s** Cross Dissolve.  
1s 이상은 보행 경계와 겹치면 더 어색해질 수 있음.

### CLI 목표 인터페이스

```bash
python3 bin/seamless-short.py frame0-check --project-dir <dir> --scene 2
python3 bin/seamless-short.py grade-match \
  --prev scenes/scene_01/scene_01.mp4 \
  --next scenes/scene_02/scene_02.mp4 \
  --feather-sec 0.8 \
  --out scenes/scene_02/scene_02_graded.mp4
```

## 4.7 우선순위

| 순위 | 조치 |
| --- | --- |
| 1 | frame0 ΔY 게이트 + 재생성 |
| 2 | Look Lock + 후반 노출 안정 프롬프트 |
| 3 | grade-match feather |
| 4 | 초단 dissolve (최후) |

## 4.8 검증 방법

```bash
# 수동 스케치
ffmpeg -y -ss 0 -i scene_02.mp4 -frames:v 1 frame0.png
# start_image.png 와 mean luma / MAE 비교 (Python PIL)
# final 타임라인: t=cut-0.05 vs t=cut+0.05 meanY 차이 ≤ 4 목표
```

파일럿 실측 표: [10-pilot-lessons-lulu-30s.md](10-pilot-lessons-lulu-30s.md).
