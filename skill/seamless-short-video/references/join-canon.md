# 조인 정본 (한 장 요약)

**전문:** [`docs/seamless-short-video/16-tail-overlap-content-model.md` §0](../../../docs/seamless-short-video/16-tail-overlap-content-model.md)

## 정본

```text
이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받는다
→ 불필요 동작 연출 없이 자연 연결
```

## 정본 ≠ 이것

| 오해 | 실제 |
| --- | --- |
| head_trim=2 | 다음 클립 **앞 2초 폐기** |
| 컷 직후 올려다보기·정지 연출 | **금지** (이어 받으면 불필요) |
| still / long dissolve | 인계 대체 아님 |

## 현재 근사 (I2V = 1프레임)

1. last frame handoff  
2. packet에 말미 ~2초 동작 명시  
3. 조인 창 continue-only  
4. `join-score` + `concat --auto-head-trim`  
