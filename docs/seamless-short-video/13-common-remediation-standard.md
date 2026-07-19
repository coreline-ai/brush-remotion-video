# 13. 공통 수정 방향 표준 (Continuity Remediation Standard)

**문서 상태:** 운영 필수 (모든 seamless-short-video 제작에 적용)  
**근거 영상:** `seamless-lulu-star-walk-30s` (30s 파일럿)에서 발견된 오류를 **일반화**  
**목적:** 특정 작품 1건 수정이 아니라, **같은 원인 클래스가 다른 영상에서 재발하지 않도록**  
원인 → 해결책 → 보완책 → 재발 방지(게이트/프로세스)를 공통 규칙으로 고정한다.

> 이 문서는 “루루 영상만의 팁”이 아니다.  
> **Last Frame Handoff + I2V 연쇄**로 만드는 **모든** 숏폼의 공통 수정·예방 표준이다.

관련 상세: [04 노출](04-look-lock-and-exposure.md) · [05 보행](05-motion-and-walk-handoff.md) · [08 QA](08-qa-and-gates.md) · [10 파일럿 실측](10-pilot-lessons-lulu-30s.md) · [11 Playbook](11-failure-playbook.md) · **[15 10초 경계](15-ten-second-boundary-common-playbook.md)** · [14 Multi-Signal](14-multi-signal-handoff-architecture.md) · **[16 조인 정본 §0](16-tail-overlap-content-model.md)**

> **10초마다 부자연한 연결** → 먼저 [16 §0](16-tail-overlap-content-model.md) 정본, 증상 시 [15](15-ten-second-boundary-common-playbook.md) C0–C26.

---

## 0. 조인 공통 정본 (모든 처방보다 우선)

**전문:** [16-tail-overlap-content-model.md §0](16-tail-overlap-content-model.md)

```text
이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받으면
→ 경계에 불필요한 동작 연출을 넣을 필요가 없고 자연스럽게 연결된다.
```

| | |
| --- | --- |
| **정본** | 이전 말미 ~2초 **영상(모션)** 을 입력으로 이어 그리기 |
| **현재 I2V** | 말미 **1프레임**만 → 정본 불가, **근사**만 |
| **근사** | packet에 말미 동작 명시 + 조인 창 continue-only + auto-head-trim |
| **정본 아님** | 고정 head_trim=2, 컷 직후 임의 포즈/엔딩 연출, still/dissolve로 연결 위장 |

C-MOT / C-MOT-CHANGE / C-JOIN-TRIM 처방은  
**“정본(2초 동작 연속)에 가깝게 가기 위한 근사·사고 방지”** 이다.  
정본이 되면 불필요 연출·강제 trim 논의 자체가 줄어든다.

### 사용 규칙 (필수)

1. **새 프로젝트마다** Character Lock과 함께 **Look Lock**을 작성한다.  
2. **씬 경계마다** §0 정본을 목표로 두고, 이상 시 §2 클래스로 분류 후 공통 처방만 적용.  
3. **다음 씬으로 진행 전** 게이트를 통과한다. 실패면 체인에 넣지 않는다.  
4. 새 증상 클래스가 나오면 이 문서에 **행을 추가**하고 FIELD-LOG에 환류한다.

---

## 1. 핵심 전제 (공통 원인 모델)

파일럿에서 확인된 오해와 수정된 전제:

| 잘못된 전제 | 올바른 공통 전제 |
| --- | --- |
| “마지막 프레임을 다음 입력으로 쓰면 컷이 안 보인다” | **입력 start ≠ 생성 frame0**. I2V는 재조명·재포즈·재보행을 할 수 있다. |
| “해시가 맞으면 연속성 OK” | 해시는 **파일 인계**만 증명. **시각 연속성**은 frame0·모션 게이트가 필요. |
| “밝기 문제와 걸음 문제는 같은 처방” | **증상 클래스가 다르다**. 노출 클래스 vs 모션 클래스로 분리 처방. |
| “프롬프트를 길게 쓰면 해결” | **불변 문장(Lock) + 타이밍 구조(0–2s / 말미 hold) + 측정 게이트**가 본령. |
| “2초 head_trim이면 어색함 0 / 그게 이전 2초 연속” | head_trim = **다음 클립 앞부분 폐기**. **이전 2초 동작 연속이 아님** ([16](16-tail-overlap-content-model.md) §0). |
| “조인에 연출을 넣어 자연스럽게” | **이전 2초 동작을 이어 받으면 연출이 불필요**. 임의 포즈 추가는 해로움. |
| “조인 구간에서 동작이 바뀌어도 편집으로 덮는다” | 정본·근사 모두 **이어 받기**가 1순위. 편집은 보조. |

공통 실패 축 (5축):

```text
① 픽셀 인계 (handoff → start 파일)
② 생성 정합 (start → frame0)
③ 노출/룩 연속 (Look Lock)
④ 동작 위상·스타일 연속 (active_motion / scene_end_type / no early pose change)
⑤ 조립 조인 지점 (head_trim 선택 — 고정값 금지, 스코어 우선)
```

①만 지켜도 ②③④⑤에서 끊길 수 있다. **5축 모두** 공통 관리 대상이다.

---

## 2. 공통 원인 분류표 (증상 → 원인 클래스 → 처방)

모든 영상에서 경계 이상을 보면 **먼저 클래스 ID를 붙인다.**

| ID | 사용자 체감 (공통) | 원인 클래스 (공통) | 1차 해결 (생성) | 2차 보완 (후처리) | 재발 방지 게이트 |
| --- | --- | --- | --- | --- | --- |
| **C-EXP** | 컷에서 밝아짐/어두워짐, 색 온도 점프 | I2V **재조명**; 또는 이전 씬 말미 **노출 ramp** | Look Lock 고정 + frame0 no-relight 문장 + 후보 재생성 | grade-match feather 0.6~0.8s; 최후 0.2~0.4s dissolve | \|ΔY(frame0,start)\|≤4, MAE≤8; cut±0.05s \|ΔY\|≤5 |
| **C-EXP-TONE** | meanY는 맞는데도 “밝기/느낌이 바뀜”, 캐릭터 광채·대비 점프 | I2V **톤 커브 재해석** (하이라이트 압축·암부 lift·대비 붕괴). uniform gain으로 안 고쳐짐 | Look Lock + no-relight 재생성; 하이라이트 유지 문구 | **Y-CDF histogram / tone-match** to prev handoff (권장); mean-only gain은 불충분 | \|ΔcenterY\|≤3, \|ΔstdY\|≤3, \|Δp90\|≤5, \|Δp10\|≤5 동시 통과 |
| **C-MOT** | 걷기/손동작이 끊김, 미끄러짐, 멈췄다 다시 감 | **동작 위상 리셋**; 다음 씬 0s부터 새 행동 | scene_end_type=hold\|plant-feet **또는** constant-cruise 연속 이동; 0–2s(권장 0–8s 조인창) overlap 문장 복붙 | timeline overlap 0.4~0.8s; speed ramp 85% | soft: 발 위상/재출발 없음; walk **peak** handoff 금지 |
| **C-MOT-CHANGE** | 컷 직후 “동작이 바뀐 느낌”(달리다→서기, 올려다보기, 엔딩 포즈 조기) | 조인 창 안 **모터 스킬·포즈 스타일 변경**; I2V 드리프트 | **조인 창(권장 0–8s) continue-only**; 엔딩 비트는 **마지막 씬 말미에만**; 한 씬=한 모터 | auto-head-trim이 t>0을 고르면 드리프트 신호 → 재생성 1순위 | soft: 조인±0.5s 포즈 계열 동일; join-score t=0이 현저히 최선이면 trim=0 유지 |
| **C-JOIN-TRIM** | “2초 중복인데도 티 남” / 고정 trim 후 더 어색 | **고정 head_trim**이 최량 조인 프레임(t≈0)을 폐기 | frame0 게이트 후 **`join-score` / `--auto-head-trim`** 으로 t∈[0,max] 선택 | 고정 `--head-trim 2`는 frame0 불량 시에만 | report에 후보 MAE/corr; 채택 trim 기록 |
| **C-FR0** | 첫 순간 구도·자세가 입력과 다름 | start-frame **partial lock** 실패 | 블록1 강화; 동작 단순화; 재생성 | (약한 경우) 1~2f handoff 스틸 삽입은 비권장·신중 | frame0 vs start 동일 게이트 (C-EXP와 공유) |
| **C-CHR** | 얼굴·의상·비율이 씬마다 달라짐 | Character 재서술·드리프트 | Character Lock 동일 삽입; 복잡도 하향; ref 재주입 | 해당 씬부터 재생성 (그레이드로는 불가) | soft face/outfit; 연속 2 fail → 복잡도↓ |
| **C-BG** | 배경 순간이동·구조 붕괴 | “새 장소” 프롬프트·공간 전환 과다 | 한 씬 공간전환 ≤1; 이동 과정 명시 | 재생성 | soft 배경 연속 |
| **C-END** | 인계 프레임 자체 불량 (블러·페이드·프레임아웃) | 말미 연출 불안정 | 말미 1s 큰 동작/페이드/bloom 금지; hold | Last Usable Frame lookback 선택 | handoff blur ≥ min; 페이드 금지 soft |
| **C-CAM** | 컷에서 카메라가 튀거나 렌즈감 변화 | 경계 전후 camera_motion 불일치 | 양 씬 카메라 문장 **동일 복사**; 경계 2s 속도 고정 | 약한 dissolve만 | soft 카메라 연속 |

### 파일럿 매핑 (근거 → 공통 ID)

| 파일럿 증상 | 시각 | 공통 ID | 비고 |
| --- | --- | --- | --- |
| 10초 밝기 점프 | ~10s | **C-EXP** (+ 기여: 말미 ramp) | start sha OK, frame0 ΔY≈+11 (lulu) |
| 20초 걷기 부자연 | ~20s | **C-MOT** | 밝기 ΔY≈0 → 노출 처방 금지 (lulu) |
| 고정 trim=2 후 조인 티 | ~10s | **C-JOIN-TRIM** + **C-MOT-CHANGE** | tori-18s: s1끝↔s2@0 corr0.87 / @2 corr0.75; 런→직립 |
| 동작 유지 + auto trim=0 | ~10s | 통과 (대조) | momo-demo: MAE1.55 corr0.999 trim=0 |

---

## 3. 클래스별 공통 수정 방향 (상세)

### 3.1 C-EXP — 노출·룩 불연속

#### 원인 (공통)

1. I2V가 start 이미지를 **새로운 노출로 재해석** (partial lock).  
2. 이전 씬 후반에 glow/광원/분위기 표현으로 **의도치 않은 밝기 ramp**.  
3. 다음 씬 프롬프트의 “magical / brighter / cinematic HDR” 류 단어가 노출을 밀어 올림.

#### 해결책 (생성 단계 — 모든 영상 공통)

| # | 조치 | 적용 시점 |
| --- | --- | --- |
| E1 | `character/look_lock.md` 작성, **전 씬 동일 문단** 삽입 | 프로젝트 초기 |
| E2 | 모든 씬(특히 02+) 프롬프트 블록1에 **no-relight / frame0 exposure match** 고정 문구 | 매 씬 |
| E3 | 씬 말미 1초: 신규 강광원·bloom ramp·“밝아지는” 서술 금지 | 매 씬 프롬프트 |
| E4 | 씬당 I2V **3~5 후보**, frame0 ΔY 최소 채택 | 매 생성 |

고정 문구 (공통 템플릿 — 복사해서 사용):

```text
Frame 0 MUST match the input image in lighting, exposure, white balance,
and overall brightness. Do not re-light, brighten, or change time of day.
Only begin motion after frame 0.
```

Negative 공통 추가:

```text
relight, auto-exposure, brighter grade, HDR boost, bloom spike,
daylight leak, fade-in exposure pop
```

#### 보완책 (이미 뽑힌 클립 — 모든 영상 공통)

| # | 조치 | 언제 |
| --- | --- | --- |
| E5a | **hard match-cut + tone-match (끊김 최소, 권장)** — still/bridge **0프레임**, dissolve **0**. S2만 Y-CDF tone-match 후 클립 그대로 이음. | multi-frame still·ease-to-still은 **멈춤 체감** 유발. long crossfade는 이중노출 플래시 |
| E5b | short overlap ≤6f equal-power (선택) | 포즈가 거의 같을 때만. 중간 meanY 들뜸 있으면 쓰지 말 것 |
| E5c | exact still inject | 밝기 픽셀 잠금 실험용. **동작 끊김 부작용** — 본편 비권장 | 
| E6 | **tone-match (Y-CDF histogram)** to prev handoff | meanY OK·로컬 톤만 틀어질 때 보조 |
| E7 | **grade-match feather** (mean only) | 순수 mean ΔY만 클 때 |
| E8 | 클립 전체 uniform gain | 응급 only — 하단/하이라이트 잔차에 불충분 |
| E9 | Cross Dissolve 0.2~0.4s | 최후 |

##### 왜 “마지막 이미지로 시작”만으로는 안 잡히는가

```text
운영자 기대:  start_image = handoff.png  →  I2V frame0 == handoff.png (픽셀 동일)
I2V 실제:    start_image = handoff.png  →  I2V frame0 ≈ 재합성 프레임 (구도 비슷, 톤·잔디·하단 다름)
```

파일 인계(sha256)와 **디코드 첫 프레임 동일**은 다른 문제다.  
하단만 남는 잔차는 대부분 **I2V가 바닥 잔디/그림자를 다시 그린 것**이며, mean/tone 게이트만으로는 픽셀 일치가 안 된다.  
**exact inject**만이 컷 순간 Δ=0을 보장한다.

##### C-EXP-TONE 판별 (mean 게이트 통과 후에도 수행)

컷 전후 또는 start vs frame0에서 아래 중 **2개 이상**이면 C-EXP-TONE:

- \|ΔcenterY\| > 4  
- \|ΔstdY\| > 4  
- \|Δp90\| > 8  
- \|Δp10\| > 6  
- 캐릭터 발광/금속/하늘 하이라이트가 눈에 띄게 죽거나 암부가 들뜸  

**실측 근거 (lulu-30s v2):** meanY Δ≈−1 인데 centerY −8, std −9, p90 −17 → 사용자 “밝기 변화” 잔존.  
tone-match 후 동일 지표 ≈0 (v3).

#### 재발 방지 (프로세스)

- Hard: `frame0` vs `start` \|ΔY\|≤4, MAE≤8 → 실패 시 **다음 씬 handoff 진행 금지**.  
- project.yaml `generator.supports_exact_start_frame: partial` 기본 가정.  
- Look Lock 없는 프로젝트는 init 미완료로 간주.

---

### 3.2 C-MOT — 동작·보행 위상 불연속

#### 원인 (공통)

1. 인계 시점이 **보행 peak-swing**(한 발 공중·무게 이동 피크).  
2. 다음 씬 **0초부터 새 스토리 비트**(도착, 고개, 랜턴 들기 등)를 시켜 걸음 사이클 리셋.  
3. 경계 전후 **카메라 속도**가 바뀌어 모션 오인지 증폭.  
4. “걸음 중간 자세가 좋은 인계”라는 일반 연출 가이드를 I2V 보행에 그대로 적용.

#### 해결책 (생성 단계 — 모든 영상 공통)

| # | 조치 | 적용 시점 |
| --- | --- | --- |
| M1 | 모든 씬에 `scene_end_type` 명시: 기본 **hold** 또는 **plant-feet** | 씬 계획 |
| M2 | **walk를 씬 경계에 두지 않음**. 걷기는 씬 **내부**만. 경계는 정지/착지 | 스토리 분할 |
| M3 | 다음 씬 **0–2.0s = 이전 active_motion 문장 복붙만** (새 사건 금지) | 매 프롬프트 |
| M4 | 경계 전후 2s 카메라 문장 **동일 복사**, 속도 고정 | 매 프롬프트 |
| M5 | 한 씬 = 한 모터 스킬 (걷기 씬에서 동시에 절정 연출 금지) | 씬 설계 |

0–2s 공통 템플릿 (최소):

```text
0–2.0s: Continues the exact same motion already in progress —
same limbs, same direction, same speed, no pause, no restart.
No new story beats until after 2.0s.
```

**조인 창 강화 (공통 권장, C-MOT-CHANGE 방지)** — 연속 이동 스토리:

```text
0–8.0s: ONLY continue the exact same motor skill (e.g. gentle walk right)
at constant cruise speed. No ending pose, no look-up, no plant-and-stop,
no new story beat. Camera lateral follow constant.
8–10s: (final scene only, or unique beat after join window) soft end beat.
```

말미 공통 템플릿 — **정지 인계** 시:

```text
9–10s: Settle into a stable hold or plant-feet pose for handoff.
Both feet committed (or fully still). Clear face. No peak walk swing.
No fade. Exposure unchanged.
```

말미 공통 템플릿 — **연속 이동 인계** 시 (constant cruise, B-ACC·C-MOT-CHANGE):

```text
8–10s: Keep the same walk/run cruise — no slowdown, no plant-feet stop,
no ending glance. End mid-stride ready to continue. Clear face. No fade.
```

#### 보완책 (편집 — 모든 영상 공통)

| # | 조치 |
| --- | --- |
| M6 | 타임라인 overlap 0.4~0.8s (Exact 길이 양보 가능 시) |
| M7 | 경계 전후 0.5s speed 100%→85%→100% |
| M8 | optical flow 4~6f (얼굴 붕괴 시 폐기) |
| M9 | **`join-score` + auto-head-trim** (C-JOIN-TRIM) — 고정 2s 폐기 금지 |

#### 재발 방지

- Soft 필수 항목: “재출발/발 위상 점프 없음” + “조인 창 안 포즈 계열 동일”.  
- **peak-swing walk handoff 금지**는 유지.  
- **constant-cruise 연속 걷기**로 경계를 넘는 것은 허용하되, 조인 창에서 **동작 변경 금지** (C-MOT-CHANGE).  
- 스토리 리라이트 패턴(공통) A — 정지 인계:

```text
… → (이동은 씬 안) → hold/plant-feet 인계 → 다음 씬 0–2s 동일 동작 → 새 비트
```

- 패턴 B — 연속 이동 (실측 유효, momo-demo):

```text
… → cruise walk 말미 감속 금지 → 다음 씬 0–8s 동일 walk only → 말미에만 엔딩 비트
조립: auto-head-trim (frame0 좋으면 대개 0s)
```

---

### 3.2b C-MOT-CHANGE — 조인 창 동작 스타일 변경

#### 원인 (공통)

1. 다음 씬 초반에 **엔딩 연출**(올려다보기, 직립, 미소 포즈)이 조기 진입.  
2. “0–2s continue”만 넣고 **2s 직후** 바로 새 모터로 전환 → head_trim=2면 그 전환이 **시청 첫 프레임**.  
3. 고정 head_trim이 **가장 잘 맞는 t=0**을 버리고 드리프트 후 프레임에 컷 (C-JOIN-TRIM과 결합).

#### 해결책 (모든 영상 공통)

| # | 조치 |
| --- | --- |
| MC1 | 조인 창(권장 **0–8s**) = continue-only, **한 모터 스킬** |
| MC2 | 스토리/엔딩 비트는 **unique 구간 후반** 또는 **마지막 씬 말미**에만 |
| MC3 | 중간 씬 말미: settle·정지 연출 금지 (constant cruise) — B-ACC와 동일 |
| MC4 | 생성 후 `join-score`: t=0이 최선이면 **억지로 trim하지 않음** |

#### 실측

| 프로젝트 | 조인 | 결과 |
| --- | --- | --- |
| tori-kite-18s | 고정 trim=2, 런 중 직립·올려다보기 드리프트 | 티 잔존 (역대 중 양호하나 비0) |
| join-fix-momo-demo | 0–8s walk only + auto trim=0 | MAE≈1.6, corr≈0.999 |

---

### 3.2c C-JOIN-TRIM — 조립 head_trim 오용

#### 원인 (공통)

| 오해 | 실제 |
| --- | --- |
| “2초 중복 = 같은 2초를 이어 씀” | A′ head_trim = **scene N+1 앞 t초 폐기** |
| “항상 2–3s 버리면 안전” | frame0이 좋으면 **t=0 조인이 최적**, t↑ 할수록 MAE↑ |

#### 해결책 (모든 영상 공통)

| # | 조치 |
| --- | --- |
| J1 | 조립 기본: **`concat --auto-head-trim --head-trim-max 2`** |
| J2 | 후보 t = 0, 0.5, … max; score = MAE + 0.5·centerMAE + 2·dY + 40·(1−corr) |
| J3 | frame0 hard-fail(ΔY/MAE)일 때만 min_trim>0 검토 |
| J4 | `report/auto_head_trim.json` · `join_score_*.json` 필수 기록 |
| J5 | 고정 `--head-trim 2`는 **의도적 비교 실험** 외 기본 금지 |

```bash
python3 bin/seamless-short.py join-score --project-dir projects/<id> --scene 1
python3 bin/seamless-short.py concat --project-dir projects/<id> \
  --auto-head-trim --head-trim-max 2 --out output/<id>.mp4
```

---

### 3.3 C-FR0 — 시작 프레임 잠금 실패 (구도·자세)

C-EXP와 겹치나, **밝기 없이 구도/자세만** 어긋날 때.

#### 공통 처방

- 블록1 “exact first frame / not a loose reference” 강화.  
- 첫 1초에 카메라 컷·재구성 금지.  
- 동작 복잡도 하향 후 재생성.  
- 게이트: frame0 vs start (구조 MAE/SSIM). 밝기만 grade-match로 덮지 말 것.

---

### 3.4 C-CHR / C-BG / C-END / C-CAM

요약 공통 방향 (상세 문장·예시는 04~07, 11 문서):

| ID | 해결 핵심 | 보완 | 게이트 |
| --- | --- | --- | --- |
| C-CHR | Lock 동일 문구, 재서술 금지, 복잡도↓ | 씬 재생성 | soft face/outfit |
| C-BG | 공간전환 ≤1, 이동 과정 명시 | 재생성 | soft background |
| C-END | 말미 hold, 페이드·블러 금지 | Last Usable Frame | blur, no-fade soft |
| C-CAM | 카메라 문장 복사, 경계 2s 고정 | 초단 dissolve | soft camera |

---

## 4. 모든 씬 경계 공통 게이트 (체크 후 다음 씬)

**Scene N 생성 직후 ~ Scene N+1 프롬프트 확정 전** 순서 고정:

```text
[1] 파일 인계 준비
    - (N≥2) start sha == prev handoff        → fail: 복사/경로 수정
[2] 생성 정합 (C-EXP / C-FR0)
    - frame0 vs start |ΔY| ≤ 4
    - frame0 vs start MAE ≤ 8
    → fail: 재생성 (E1–E4). 3회 실패 시 E5 grade-match 검토 후 기록
[3] 인계 프레임 품질 (C-END)
    - handoff blur OK, 페이드/프레임아웃 없음
[4] 모션 인계 설계 확인 (C-MOT / C-MOT-CHANGE) — 생성 전·후에도
    - 정지 인계: scene_end_type ∈ {hold, plant-feet, gesture}
    - 연속 이동: constant cruise + 조인 창 continue-only (권장 0–8s)
    - 다음 프롬프트 조인 창에 새 비트·엔딩 포즈 없음
[5] Soft 육안 (C-CHR/C-BG/C-CAM)
    - 얼굴·배경·카메라·보행
[6] 통과 시에만 handoff 확정 → observed_end_state → 다음 씬
[7] 전 씬 완료 후 조립 (C-JOIN-TRIM)
    - join-score / auto-head-trim (고정 2s 기본 금지)
```

**금지:** soft만 보고 “나중에 한꺼번에 고치자”며 체인 진행.

---

## 5. 공통 프로세스 변경 (작품 무관)

파일럿 이전(오류를 만든 프로세스) vs 이후(공통 표준):

| 단계 | 이전 (재발 유발) | 이후 (공통 표준) |
| --- | --- | --- |
| 초기화 | Character만 | Character + **Look Lock** + generator lock=partial 가정 |
| 씬 계획 | 행동 나열 | 행동 + **scene_end_type** + 경계에 walk 금지 |
| 프롬프트 | 6블록 | 6블록 + **노출 고정** + **0–2s overlap only** |
| 생성 | 1회 채택 | **3~5 후보** 중 frame0 게이트 통과분 |
| 검증 | start 해시·duration 위주 | + **frame0 ΔY/MAE** + soft 모션 |
| 인계 | 마지막 프레임 복사면 OK | 복사 + frame0 통과 + observed 갱신 |
| 편집 | Match cut only / 고정 head_trim=2 | hard cut + **auto-head-trim** + 필요 시 E5/M6/M7 |
| 조인 창 동작 | 0–2s만 continue, 곧 엔딩 포즈 | **0–8s continue-only**, 엔딩은 말미 (C-MOT-CHANGE) |
| 기록 | 프로젝트 메모 | **이 문서 ID(C-xxx)** + join-score JSON 환류 |

---

## 6. 공통 프롬프트 최소 키트 (매 프로젝트 동일 구조)

에이전트/제작자는 작품이 바뀌어도 아래 슬롯만 채운다.

```text
[LOCKS — 전 씬 동일]
Character Lock: ...
Look Lock: ...

[HANDOFF — 씬마다 observed로 갱신]
Continue from: pose / motion / camera / exposure_notes
scene_end_type: hold | plant-feet | gesture

[TIMELINE]
0–2s (min) / 0–8s (join window, recommended): ONLY continue active_motion
  — same motor skill, constant cruise, no ending pose
after join window: ONE main action or (final scene) soft end beat
last 1s of handoff scene: hold/plant-feet OR mid-cruise (no slowdown)

[FRAME0]
exact first frame + no relight (template fixed)

[NEGATIVE]
redesign, teleport, fade, relight, bloom spike, walk-peak handoff cues,
early ending pose, look-up pose change in first seconds, hard accelerate from still
```

---

## 7. 의사결정 트리 (모든 영상 공통)

```text
경계에서 이상 발견
    │
    ├─ 밝기/색이 튀는가?
    │     YES → C-EXP → E1–E4 재생성 → 그래도 남으면 E5–E7
    │
    ├─ 걸음/손/몸 동작이 리셋·미끄러운가?
    │     YES → C-MOT → M1–M5 재생성/리라이트 → M6–M9 편집
    │     (밝기 처방을 먼저 쓰지 말 것)
    │
    ├─ 컷 직후 동작 스타일만 바뀌는가? (직립·올려다보기·엔딩 포즈)
    │     YES → C-MOT-CHANGE → 조인 창 continue-only 재생성
    │           + join-score (고정 trim=2가 원인인지 확인)
    │
    ├─ 고정 head_trim 후에만 티가 커지는가?
    │     YES → C-JOIN-TRIM → auto-head-trim / trim=0 비교
    │
    ├─ 구도·자세만 입력과 다른가?
    │     YES → C-FR0
    │
    ├─ 얼굴·옷이 다른가? → C-CHR
    ├─ 배경이 점프인가? → C-BG
    ├─ 인계 프레임 자체가 나쁜가? → C-END
    └─ 카메라가 튀는가? → C-CAM
```

**중요:** 한 컷에 C-EXP와 C-MOT가 동시에 있으면 **둘 다** 처리한다.  
노출 grade-match만으로 보행 리셋은 고쳐지지 않는다.  
**동작 변경 최소화 + auto-head-trim** 이 편집 디졸브보다 우선한다.

---

## 8. 새 영상 제작 시 필수 산출물 (공통)

각 `projects/<id>/`에 최소:

| 산출 | 공통 목적 |
| --- | --- |
| `character/character_lock.md` | C-CHR 방지 |
| `character/look_lock.md` | C-EXP 방지 |
| `story/scene_plan.md` 내 scene_end_type + 조인 창 동작 | C-MOT / C-MOT-CHANGE 방지 |
| 씬별 `qa.json` (hard.frame0_* 포함 권장) | 게이트 증거 |
| `report/join_score_*.json` · `auto_head_trim.json` | C-JOIN-TRIM 증거 |
| `report/continuity_report.md` | 경계별 C-xxx 판정 기록 |

continuity_report 경계 행 예시:

```markdown
| cut | t | class | ΔY frame0 | decision | note |
| 1→2 | 10s | C-EXP | +11.1 | retry | relight; regenerate S2 |
| 2→3 | 20s | C-MOT | -1.0 | rewrite end_type hold | walk phase reset |
```

---

## 9. CLI / 검증기 환류 목표 (공통 자동화)

문서 규칙을 도구로 고정할 항목 (구현 체크리스트와 동기):

| 기능 | 막는 클래스 |
| --- | --- |
| `verify` start 해시 | ① 파일 인계 |
| **`frame0-check` ΔY/MAE** | **C-EXP, C-FR0** (구현됨; C12 임계, fail exit≠0) |
| `grade-match` | C-EXP 보완 (미구현) |
| handoff blur | C-END |
| **`join-score` / `concat --auto-head-trim`** | **C-JOIN-TRIM** (구현됨) |
| (향후) cut luma probe on concat | C-EXP 최종 |

자동화 전에도 **§4 수동 게이트**는 모든 영상에서 동일하게 수행한다.

---

## 10. 한 페이지 요약 (공통 수정 방향)

```text
1) 인계는 파일만이 아니라 frame0·노출·동작 위상·조립 조인까지다 (5축).
2) 밝기 끊김(C-EXP): Look Lock + no-relight + frame0 게이트 + (보조) grade-match.
3) 동작 끊김(C-MOT): hold/plant-feet 또는 constant-cruise + 조인 창 continue-only.
4) 동작 변경 티(C-MOT-CHANGE): 조인 창(0–8s) 모터 고정, 엔딩은 말미.
5) 조립(C-JOIN-TRIM): auto-head-trim — 고정 2s 폐기로 최적 조인을 버리지 말 것.
6) 해시는 필요조건, 시각·조인 게이트가 충분조건.
7) 다음 씬 진행 = 해당 경계 게이트 PASS 이후에만.
```

---

## 11. 개정 이력

| 버전 | 일자 | 내용 |
| --- | --- | --- |
| 0.1 | 2026-07-17 | 파일럿(lulu-30s) 10s 밝기·20s 보행을 C-EXP/C-MOT로 일반화, 공통 해결·보완·게이트 최초 고정 |
| 0.2 | 2026-07-17 | C-MOT-CHANGE·C-JOIN-TRIM 추가; 5축; 조인 창 0–8s continue; auto-head-trim 공통; tori/momo 실측 |
| 0.3 | 2026-07-17 | §0 조인 정본: 이전 ~2초 동작 연속 → 불필요 연출 불필요; 근사≠정본 명문화 |
