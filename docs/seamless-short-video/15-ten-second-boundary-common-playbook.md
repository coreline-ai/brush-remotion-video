# 15. 10초 경계 공통 적용 플레이북

**상태:** 모든 seamless-short-video **필수 적용**  
**정본 아키텍처:** [14-multi-signal-handoff-architecture.md](14-multi-signal-handoff-architecture.md)  
**증상 분류:** [13-common-remediation-standard.md](13-common-remediation-standard.md)

10초(또는 씬 duration)마다 부자연한 연결이 반복되는 문제에 대한  
**공통 적용 항목 + 처방 순서**다. 작품별 즉흥 패치를 금지한다.

---

## 0. 한 줄 목표

```text
【정본 — 공통 적용 1순위, doc16 §0】
이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받는다
→ 경계에 불필요한 동작 연출을 넣을 필요가 없고 자연 연결

【지금 도구에서의 근사】
마지막 이미지 = 다음 frame0 앵커
+ 말미 ~2초 동작을 packet에 명시 + 조인 창 continue-only
+ Motion/State/Look/Camera 다중 신호
+ frame0 게이트 통과 후에만 다음 씬
+ 결합: hard cut + auto-head-trim (고정 2s 폐기 ≠ 이전 2초 연속)
+ still multi-frame / long dissolve 금지
```

**혼동 금지:** `head_trim=2` 는 “이전 2초를 이어 쓴 것”이 아니다.  
정본 전문: [16 §0](16-tail-overlap-content-model.md).

---

## 1. 공통 원인 (10초마다 티가 나는 이유)

| ID | 층 | 증상 | 대표 원인 |
| --- | --- | --- | --- |
| B-VIS | 픽셀 | 컷 순간 밝기·질감·하단 잔디 점프 | I2V frame0 재합성 (start≠frame0) |
| B-MOT | 동작 | 걸음/부유 리셋, 미끄러짐 | 0s부터 새 샘플 / peak-swing 인계 |
| **B-MOT-CHANGE** | **동작 스타일** | **컷 직후 직립·올려다보기·엔딩 포즈** | **조인 창 안 모터/포즈 변경** (C-MOT-CHANGE) |
| B-SPD | 속도 | 멈춤 후 재출발 느낌 | 말미 감속·초반 가속 불일치 |
| **B-ACC** | **가속 점프** | **컷 직후 갑자기 빨라짐 (더 이상함)** | **말미 settle/저속 + 다음 씬 초반 가속** (모션 축소 처방의 부작용) |
| B-CAM | 카메라 | 앵글·속도 리셋 | 카메라 문장 씬마다 변경 |
| B-BIT | 스토리 | 텔레포트·갑작 도착 | 0–2s에 새 비트 |
| B-EDIT | 편집 | 멈춤 끊김 / 멍한 중간 | multi-frame still / long dissolve |
| **B-TRIM** | **조립** | “2초 중복인데 티” / trim 후 더 어색 | **고정 head_trim**이 최량 조인(t≈0) 폐기 (C-JOIN-TRIM) |

---

## 2. 공통 적용 항목 (체크리스트 — 매 씬·매 프로젝트)

### 2.1 프로젝트 초기 (1회)

- [ ] **C0** 조인 정본 합의: **이전 말미 ~2초 동작 연속** → 불필요 연출 없이 연결 ([16](16-tail-overlap-content-model.md) §0)  
- [ ] **C1** Character Lock 작성·전 씬 동일 삽입  
- [ ] **C2** Look Lock 작성·전 씬 동일 삽입  
- [ ] **C3** `generator.supports_exact_start_frame` 정직 기록 (대개 `partial`)  
- [ ] **C4** 씬 계획: 경계마다 “이어 받을 말미 ~2초 동작” + `scene_end_type`  
- [ ] **C5** 한 씬 = 한 모터 스킬 (경계에서 **새** 안무·다중 행동 금지; 말미 동작 **연속**은 허용)

### 2.2 씬 생성 전 (패킷)

- [ ] **C6** 이전 `handoff_frame`만 start로 사용 (신규 시작 이미지 생성 금지)  
- [ ] **C7** `handoff_packet.yaml` 작성 (visual + state + motion + camera + look)  
- [ ] **C8** 프롬프트 **조인 창** = `active_motion` **복붙**, `do_not_restart: true`  
  - 최소 0–2s / **권장 0–8s continue-only** (엔딩 포즈·새 비트 금지)  
- [ ] **C9** 프롬프트 블록1 = exact frame0 + no relight  
- [ ] **C10** 말미 1s = **hold/plant-feet** *또는* **constant cruise 감속 금지** + 노출 고정 + no bloom ramp  
- [ ] **C21** 중간 씬: 조인 창 안 **모터 스킬 1개** (C-MOT-CHANGE)  
- [ ] **C22** 엔딩/감정 비트는 unique 후반 또는 **마지막 씬 말미**에만  

### 2.3 씬 생성 후 (게이트 — 다음 씬 진행 전)

- [ ] **C11** `sha256(start)==sha256(prev handoff)`  
- [ ] **C12** frame0 vs start:  
  - \|ΔmeanY\| ≤ 3.5  
  - \|ΔbottomY\| ≤ 4  
  - \|ΔcenterY\| ≤ 4  
  - MAE ≤ 8  
- [ ] **C13** soft: 0–1s 동작 리셋·텔레포트·카메라 반전 없음  
- [ ] **C14** fail 시 **같은 packet으로 재생성** (후처리로 “완료” 선언 금지). 씬당 최대 3회  
- [ ] **C23** soft: 조인 창 초반에 직립·올려다보기·엔딩 포즈 조기 진입 없음  

### 2.4 결합 (assemble)

- [ ] **C15** 기본: **hard match-cut** + (필요 시) 다음 클립 tone-match to prev end  
- [ ] **C16** 선택: **모션 overlap 3–6f (≤0.25s)** equal-power — 포즈 유사·meanY 선정합 후에만  
- [ ] **C17** **금지:** multi-frame still inject (양옆 handoff 고정)  
- [ ] **C18** **금지:** 1s+ crossfade / 전 구간 일괄 long dissolve  
- [ ] **C19** 선택 보조: 경계 전후 0.3s speed ramp 100→90→100 (모션 충격 완화)  
- [ ] **C20** 단일 인코드 패스 권장 (클립별 재인코딩 누적 오차 감소)  
- [ ] **C24** 조립 기본: **`concat --auto-head-trim --head-trim-max 2`** (C-JOIN-TRIM)  
- [ ] **C25** **금지 기본값:** 무조건 `--head-trim 2` (frame0 불량·의도 실험 외)  
- [ ] **C26** `report/join_score_*.json` + 채택 trim 기록 |

---

## 3. 처방 순서 (경계가 부자연할 때)

```text
1) 원인 ID 분류 (B-VIS / B-MOT / B-MOT-CHANGE / B-SPD / B-ACC / B-CAM / B-BIT / B-EDIT / B-TRIM)
2) 생성 재시도 (packet 고정, 조인 창 continue-only)  ← 본류
3) join-score / auto-head-trim (B-TRIM) — 고정 2s부터 쓰지 말 것
4) tone-match (B-VIS만, still 아님)
5) hard cut 유지 또는 ≤6f overlap (B-MOT 경미)
6) speed ramp / velocity-match (B-SPD / B-ACC)
7) 스토리·end_type 재설계 후 재생성 (근본)
```

| 원인 | 1순위 처방 | 2순위 | 하지 말 것 |
| --- | --- | --- | --- |
| B-VIS | frame0 게이트 재생성 + Look Lock | Y-CDF tone-match | mean-only로 완료 선언 |
| B-MOT | 0–2s(권장 0–8s) 복붙 재생성 + end_type hold/plant-feet 또는 cruise | ≤6f motion overlap | multi still |
| **B-MOT-CHANGE** | **조인 창 모터 고정 재생성**; 엔딩 비트 말미로 이동 | auto-head-trim이 t=0 가리키면 그 값 유지 | 조인 직후 look-up/정지 연출 |
| B-SPD | 말미/초반 속도 문장 통일 재생성 | speed ramp 0.3s | 긴 freeze hold |
| **B-ACC** | **상수 순항(constant cruise)** 프롬프트 재생성: 말미 감속 금지·초반 가속 금지 | **velocity-match**: 다음 씬 초반 1.0~1.5s를 이전 말미 모션 에너지에 맞춰 리타임 후 1.0으로 ease | 말미만 줄이고 다음 씬을 빠르게 시작하기 |
| B-CAM | 카메라 문장 복붙 재생성 | — | whip pan |
| B-BIT | 0–2s 새 비트 제거 재생성 | 씬 분할 수정 | 텔레포트 프롬프트 |
| B-EDIT | still/long dissolve 제거 | hard cut + tone | 편집으로 인계 대체 |
| **B-TRIM** | **`join-score` → auto-head-trim** | frame0 불량 시에만 min_trim↑ | 무조건 head_trim=2 |

---

## 4. 프롬프트 공통 템플릿 (복붙)

### 4.1 Frame0 + Look (매 씬)

```text
Use the provided input image as the EXACT first frame.
Match lighting, exposure, white balance, and overall brightness on frame 0.
Do not re-light, recompose, or change time of day. Only begin motion after frame 0.
[Look Lock paragraph — identical every scene]
```

### 4.2 Motion continue (0–2s, 매 씬 02+)

```text
0–2.0s: Continues the exact same motion already in progress —
same direction, same speed, same limbs. No pause, no restart, no new story beat.
2.0s–: [ONE main action for this scene only]
```

### 4.3 Handoff settle (9–10s) — **중간 씬은 과한 settle 금지**

결말 씬(마지막)만 강한 hold:

```text
9–10s: Settle into a stable hold pose. Face clear, camera stable, no fade.
```

**중간 씬 (연속 이동/부유)** — constant cruise (B-ACC 방지):

```text
8–10s: Keep the SAME constant slow speed — do NOT slow to a stop, do NOT accelerate.
Maintain clear face and stable framing. No bloom ramp, no fade-out.
Pose may be plant-feet or float-hold but velocity stays matched for handoff.
```

### 4.4 Next scene open — **가속 금지**

```text
0–2.0s: Continue at the SAME speed as the previous shot ending.
Do not start faster, do not ramp up, do not burst into a new motion.
Same direction, same pace, then after 2s allow the scene action without a speed jump.
```

---

## 5. 결합 레시피 (공통)

### 레시피 A — 기본 (권장)

```text
for each scene:
  tone-match clip so frame0 CDF ≈ prev handoff  (if gate borderline)
concat hard match-cut, single encode
```

### 레시피 A2 — 가속 점프 시 (B-ACC, 기존 클립 수정)

```text
pre_e  = mean stepMAE of last ~0.3–0.5s of scene N
         (if ending is over-settled vs mid-shot, use mid*0.85 as target cruise)
post_e = mean stepMAE of first ~0.5s of scene N+1
if post_e/pre_e > 1.25:
  retime first 1.0–1.5s of scene N+1 with initial speed s0=clamp(pre_e/post_e, 0.5, 1.0)
  ease s0 → 1.0 (smoothstep); keep wall-clock length of that window
then hard-cut concat
```

금지: 말미만 줄이고 다음 씬 초반을 그대로 빠르게 두기.

### 레시피 B — 경미한 포즈 단절 시

```text
pre-match meanY/CDF at boundary
overlap 4–6 frames equal-power (both sides moving)
NO pure still frames
abort overlap if mid meanY swing > 8
```

### 레시피 C — 금지

```text
handoff PNG × N frames both sides of cut
1s+ dissolve on every cut
말미 강제 감속 + 다음 씬 초반 가속 (B-ACC)
```

### 레시피 D — Tail / Head 기획 + **적응형 trim** (상세 [16](16-tail-overlap-content-model.md))

```text
생성: 10s I2V + last-frame handoff + packet
      조인 창(0–8s) continue-only / 엔딩은 말미 (B-MOT-CHANGE 방지)
기획: 대본·음원은 unique 구간에 맞춤 (고정 7–8s가 필수는 아님)
조립: concat --auto-head-trim --head-trim-max 2
      (후보 0..max 중 MAE/corr 최선 — 종종 0s)
      고정 head_trim=2 는 frame0 불량·비교 실험 시에만
금지: “2초 중복 = 연속 재생” 오해 / 무조건 앞 2s 폐기
```

**1차 권장: 동작 변경 최소화 + auto-head-trim.**  
고정 head_trim은 frame0·초반 가속이 **나쁠 때만** 쓰는 보조다.

### 레시피 E — 조인 스코어 (공통 필수, C-JOIN-TRIM)

```bash
python3 bin/seamless-short.py join-score --project-dir projects/<id> --scene N
python3 bin/seamless-short.py concat --project-dir projects/<id> \
  --auto-head-trim --head-trim-max 2 --out output/<id>.mp4
```

| 실측 | best trim | MAE@best | MAE@trim2 |
| --- | --- | --- | --- |
| tori-kite-18s (고정2) | (강제 2) | — | ~18.9 (corr~0.75) |
| join-fix-momo-demo | **0** | **1.55** (corr **0.999**) | 28.9 |

---

## 6. 검증 표 (프로젝트 report에 남길 것)

| cut | t | B-IDs | frame0 dmean | frame0 dbot | join best trim | MAE@0 / @best | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1→2 | 10s | | | | | | pass/regen/auto-trim |
| … | | | | | | | |

---

## 7. 개정

| 버전 | 일자 | 내용 |
| --- | --- | --- |
| 0.1 | 2026-07-17 | 10초 경계 공통 적용 항목 C1–C20·처방 순서·결합 레시피 신설 |
| 0.2 | 2026-07-17 | B-ACC(감속 후 가속) 추가, constant cruise 프롬프트, velocity-match 레시피 A2 |
| 0.3 | 2026-07-17 | 기획 대안: gen 10s / unique 7–8s / head_trim 2–3s → [16](16-tail-overlap-content-model.md) |
| 0.4 | 2026-07-17 | B-MOT-CHANGE·B-TRIM; C21–C26; 조인 창 0–8s; auto-head-trim 공통 1순위; 레시피 E |
| 0.5 | 2026-07-17 | §0·C0: 조인 정본 = 이전 ~2초 동작 연속; head_trim≠연속 명문화 |
