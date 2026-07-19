# 08. QA와 게이트

## 8.1 계층

| 계층 | 주체 | 실패 시 |
| --- | --- | --- |
| **Hard** | 자동(CLI/스크립트) | 다음 씬 진행 **금지** |
| **Soft** | 사람 (기록 필수) | retry / waive+reason |
| **Final** | concat 후 | 배포 전 재작업 |

---

## 8.2 Hard gate

### H1. Start 해시 체인 (N≥2)

```text
sha256(start_image) == sha256(prev handoff_frame)
```

### H2. 미디어 메타

- duration ∈ [scene_seconds − tol, scene_seconds + tol] (기본 tol 0.5~0.6s)  
- 전 씬 동일 해상도·화면비 (또는 project 설정 일치)  

### H3. Handoff blur

- Laplacian variance ≥ min_blur (기본 40)  
- 미달 시 warning 또는 fail (운영 정책)

### H4. frame0 vs start (v0.2)

| 지표 | pass |
| --- | --- |
| \|Δ meanY\| | ≤ 4 (초기 완화 6) |
| mean \|RGB\| | ≤ 8 |
| SSIM (선택) | ≥ 0.92 |

### H5. (선택) 경계 luma 팝

concat 후보에서 cut−0.05s vs cut+0.05s \|ΔY\| ≤ 5.

---

## 8.3 Soft gate (체크리스트)

- [ ] 얼굴이 Character Lock / Scene01과 동일 계열  
- [ ] 의상·고정 소품 유지  
- [ ] 포즈가 이전 종료에서 자연 연결  
- [ ] 이동 방향 급반전 없음  
- [ ] 설명 없는 배경 재구성 없음  
- [ ] 카메라 렌즈·각도 점프 없음  
- [ ] 손·발·얼굴 심각 변형 없음  
- [ ] 시작 1초 ≈ start_image 체감  
- [ ] 종료가 다음 생성에 쓸 만한 안정 (또는 결말 hold)  
- [ ] 보행 시 발 위상·정지 후 재출발 없음  
- [ ] 노출이 Look Lock과 크게 안 벗어남  

### 즉시 재생성 (심각 soft → 사실상 hard)

- 다른 캐릭터처럼 변함  
- 의상 변경  
- 첫 1초 배경 재구성  
- 이전 동작과 무관한 자세로 시작  
- 순간 이동  
- 시작 즉시 카메라 반대  

---

## 8.4 qa.json 스키마 예시

```json
{
  "scene_id": "scene_02",
  "hard": {
    "start_hash_match": true,
    "duration_ok": true,
    "blur_ok": true,
    "frame0_delta_y": 2.1,
    "frame0_mae": 5.4,
    "frame0_ok": true
  },
  "soft": {
    "face": "pass",
    "outfit": "pass",
    "pose_link": "pass",
    "walk_phase": "pass",
    "exposure_feel": "pass"
  },
  "decision": "pass",
  "retry_count": 1,
  "notes": ""
}
```

---

## 8.5 재시도 정책

| 항목 | 값 |
| --- | --- |
| 장면당 최대 재생성 | 3 |
| 연속 face fail 2회 | 동작 복잡도 1단계 하향 |
| frame0 노출 fail | Look Lock 문구 강화 후 재시도 → grade-match |
| walk soft fail | scene_end_type을 hold/plant-feet로 변경 |
| completed | immutable; 재개는 from scene_id |

---

## 8.6 CLI

```bash
# 현재 구현
python3 bin/seamless-short.py verify --project-dir <dir>

# 목표 (체크리스트)
python3 bin/seamless-short.py frame0-check --project-dir <dir> --scene N
python3 bin/seamless-short.py grade-match ...
```

`verify` 현재: start 해시, duration, handoff blur.  
frame0·grade-match는 [12-skill-adoption-checklist.md](12-skill-adoption-checklist.md) 구현 항목.
