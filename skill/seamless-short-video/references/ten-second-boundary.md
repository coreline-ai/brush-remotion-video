# 10초 경계 공통 적용 (요약)

**전문:** [`docs/seamless-short-video/15-ten-second-boundary-common-playbook.md`](../../../docs/seamless-short-video/15-ten-second-boundary-common-playbook.md)  
**조인 정본:** [`docs/seamless-short-video/16-tail-overlap-content-model.md` §0](../../../docs/seamless-short-video/16-tail-overlap-content-model.md)

## 정본 (공통 적용 1순위)

```text
이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받는다
→ 경계에 불필요한 동작 연출을 넣을 필요가 없고 자연 연결
```

- 정본 입력: 이전 말미 **~2초 영상(모션 tail)**  
- 현재 I2V: **1프레임만** → 정본 불가, 아래는 **근사**  
- **head_trim=2 ≠ 이전 2초 연속** (그건 다음 클립 앞 2초 **폐기**)

## 근사 (도구 제약 시)

1. Character + Look Lock  
2. start = prev handoff only  
3. packet에 말미 ~2초 동작 명시  
4. 조인 창 continue-only (새 안무·엔딩 포즈 금지)  
5. frame0 게이트 → fail 시 같은 packet 재생성  
6. `join-score` + `concat --auto-head-trim`  
7. **금지:** multi-frame still, long dissolve, “연결용” 임의 포즈, 고정 trim을 연속이라고 부름  

## 처방 한 줄

```text
정본: 이전 2초 동작 이어 받기
근사: packet continue-only + auto-head-trim
불필요 연출 추가 / head_trim=연속 오해 금지
```
