# 공통 수정 + Multi-Signal 인계 (요약)

**조인 정본 (모든 처방보다 우선):**  
[`docs/seamless-short-video/16-tail-overlap-content-model.md` §0](../../../docs/seamless-short-video/16-tail-overlap-content-model.md)

```text
이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받으면
→ 불필요 동작 연출 없이 자연 연결
```

**정본 아키텍처:**  
[`docs/seamless-short-video/14-multi-signal-handoff-architecture.md`](../../../docs/seamless-short-video/14-multi-signal-handoff-architecture.md)

**증상 처방 표:**  
[`docs/seamless-short-video/13-common-remediation-standard.md`](../../../docs/seamless-short-video/13-common-remediation-standard.md)

## 정본 vs 근사

| | |
| --- | --- |
| 정본 | 말미 ~2초 **영상** 이어 그리기 |
| 현재 I2V | 말미 **1장** → 근사만 |
| 근사 | packet 동작 명시 + continue-only + auto-head-trim |
| 정본 아님 | 고정 head_trim=2, 컷 직후 임의 포즈, still/dissolve 위장 |

## 증상 클래스 (보조 — 정본 근사·사고 방지)

| ID | 증상 | 1순위 |
| --- | --- | --- |
| C-EXP / C-EXP-TONE | 밝기·톤 | packet 재생성 + Look Lock |
| C-MOT | 동작 위상 끊김 | 말미 동작 이어 받기 (continue) |
| C-MOT-CHANGE | 컷 직후 새 안무 | **연출 추가 금지**, 이전 동작 복붙 |
| C-JOIN-TRIM | trim 오해·악화 | auto-head-trim; **trim≠2초 연속** |
