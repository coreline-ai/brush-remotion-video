# 09. 워크플로 · 프로젝트 구조 · CLI

## 9.1 디렉터리 구조

```text
projects/<project-id>/
├── project.yaml
├── character/
│   ├── character_lock.md
│   ├── look_lock.md                 # v0.2 권장
│   └── character_reference.png
├── story/
│   ├── story_summary.md
│   └── scene_plan.md
├── scenes/
│   ├── scene_01/
│   │   ├── start_image.png
│   │   ├── image_prompt.md          # scene01 only
│   │   ├── video_prompt.md
│   │   ├── scene_01.mp4
│   │   ├── handoff_frame.png
│   │   ├── handoff_meta.json
│   │   ├── planned_end_state.yaml
│   │   ├── observed_end_state.yaml
│   │   └── qa.json
│   └── scene_0N/ ...
├── edit/
│   ├── timeline.md
│   └── final_video.mp4
└── report/
    ├── continuity_report.md
    └── verify-hard-gate.json
```

Scene 02+ `start_image.png` = 이전 `handoff_frame.png` 복사본.

---

## 9.2 project.yaml 예시

```yaml
project:
  id: example-30s
  name: 예제
  total_duration: 30
  scene_count: 3
  scene_duration: 10
  aspect_ratio: "9:16"
  transition_mode: last_frame_match_cut   # or smooth_cross_dissolve
  dialogue: false
  status: PROJECT_INITIALIZED

generator:
  id: grok-imagine          # or manual-upload | other
  max_duration_sec: 10
  aspect: "9:16"
  supports_exact_start_frame: partial   # true | partial | unknown

character_lock:
  path: character/character_lock.md
  reference: character/character_reference.png

look_lock:
  path: character/look_lock.md

scenes:
  - id: scene_01
    start_image: scenes/scene_01/start_image.png
    source_video: scenes/scene_01/scene_01.mp4
    handoff_frame: scenes/scene_01/handoff_frame.png
    scene_end_type: hold
    qa_status: pending
  - id: scene_02
    start_image: scenes/scene_02/start_image.png
    start_image_source: scenes/scene_01/handoff_frame.png
    source_video: scenes/scene_02/scene_02.mp4
    handoff_frame: scenes/scene_02/handoff_frame.png
    scene_end_type: plant-feet
    qa_status: pending

retry:
  max_per_scene: 3
  immutable_completed: true

gates:
  max_frame0_delta_y: 4
  max_frame0_mae: 8
  min_handoff_blur: 40
  duration_tol_sec: 0.6
```

---

## 9.3 CLI 레퍼런스

진입점: `bin/seamless-short.py`  
(Remotion `bin/build.py`와 무관)

### init

```bash
python3 bin/seamless-short.py init \
  --project-dir projects/<id> \
  --project-id <id> \
  --title "제목" \
  --scenes 3 \
  --scene-seconds 10 \
  --aspect 9:16 \
  --transition-mode last_frame_match_cut \
  --generator grok-imagine
```

골격·project.yaml·빈 character/story/scene 폴더 생성.

### handoff

```bash
python3 bin/seamless-short.py handoff \
  --project-dir projects/<id> \
  --scene 1 \
  --video path/to/clip.mp4 \
  [--lookback 0.8] [--sample-fps 10] [--min-blur 40]
```

- 영상을 `scenes/scene_XX/scene_XX.mp4`로 정규화 복사  
- Last Usable Frame → `handoff_frame.png`  
- 다음 씬 `start_image.png` 복사 (마지막 씬 제외)  
- `handoff_meta.json` · project.yaml 갱신  

### verify

```bash
python3 bin/seamless-short.py verify \
  --project-dir projects/<id> \
  [--duration-tol 0.6] [--min-blur 40]
```

Hard: start 해시 체인, duration, handoff blur.  
리포트: `report/verify-hard-gate.json`.

### frame0-check

```bash
python3 bin/seamless-short.py frame0-check \
  --project-dir projects/<id> \
  --scene N \
  [--start-image path] [--video path] \
  [--max-dmean-y 3.5] [--max-dbottom-y 4] [--max-dcenter-y 4] [--max-mae 8]
```

start_image vs 영상 **frame0** (docs 15 **C12**):  
`|ΔmeanY|≤3.5`, `|ΔbottomY|≤4`, `|ΔcenterY|≤4`, `MAE≤8`.  
PASS/FAIL를 `scenes/scene_XX/qa.json` hard.frame0 과  
`report/frame0-check-scene_XX.json`에 기록. **FAIL 시 exit≠0**.

### join-score

```bash
python3 bin/seamless-short.py join-score \
  --project-dir projects/<id> \
  --scene 1 \
  [--max-trim 2] [--min-trim 0] [--step 0.5] \
  [--out projects/<id>/report/join_score_s01_s02.json]
```

prev 씬 말미 vs next@t (t=0..max) MAE/corr/dY 스코어.  
**C-JOIN-TRIM:** 고정 head_trim 전에 반드시 확인. 상세 [13](13-common-remediation-standard.md) · [16](16-tail-overlap-content-model.md).

### concat

```bash
# 공통 기본: 적응형 head_trim (씬2..N)
python3 bin/seamless-short.py concat \
  --project-dir projects/<id> \
  --auto-head-trim --head-trim-max 2 \
  [--out output/<id>.mp4] \
  [--drop-last-frame]

# 예외: 고정 discard (frame0 불량·비교 실험)
python3 bin/seamless-short.py concat \
  --project-dir projects/<id> \
  --head-trim 2 \
  [--out output/<id>_trim2.mp4]
```

전 씬 동일 해상도·30fps 정규화 후 concat. Exact match-cut.  
`--auto-head-trim` 시 `report/auto_head_trim.json` 기록.

### 후속 구현 예정

- `frame0-check`  
- `grade-match`  

---

## 9.4 운영 루프 (한 씬)

```text
1. (N=1) start 이미지 생성·배치
   (N≥2) start = prev handoff (이미 handoff CLI가 준비)
2. video_prompt.md 확정 (observed 반영)
3. I2V 생성 → scene_0N.mp4
4. frame0 vs start 측정 (수동 또는 CLI)
5. soft QA
6. handoff CLI
7. observed_end_state 기록
8. project.yaml qa_status=passed
9. 다음 씬 프롬프트 초안
```

## 9.5 생성기 capability matrix

| id | duration | aspect | start lock | 비고 |
| --- | --- | --- | --- | --- |
| grok-imagine | 6/10 | 소스 이미지 따름 | partial | 파일럿 사용 |
| manual-upload | 가변 | 가변 | unknown | 외부 도구 |
| (기타) | 문서화 후 추가 | | | |

미지원 시 장면 길이·비율을 생성기 한도에 맞추고 가정을 명시.

## 9.6 스킬 설치

```bash
bin/install-skills.sh --target all
bin/install-skills.sh --target all --check   # 10/10 포함 seamless-short-video
```

얇은 스킬 경로: `skill/seamless-short-video/`.  
상세 사양 원천: **본 문서 디렉터리** `docs/seamless-short-video/`.
