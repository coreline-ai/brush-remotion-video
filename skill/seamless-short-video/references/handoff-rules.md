# Handoff 규칙 (요약)

**전문:** [`docs/seamless-short-video/03-handoff-contract.md`](../../../docs/seamless-short-video/03-handoff-contract.md)

## 불변식

```text
start_image(N) == handoff_frame(N-1)   # sha256
frame0(N) ≈ start_image(N)             # ΔY≤4, MAE≤8 권장
observed_end_state → next prompt
```

## Last Usable Frame

원칙 마지막 프레임. 블러·페이드·변형 시 말미 0.3~0.8s에서 최후방 정상 프레임.  
CLI: `bin/seamless-short.py handoff`

## 인계 포즈

기본 **hold / plant-feet**. walk peak-swing 경계 인계 비권장.  
→ [`05-motion-and-walk-handoff.md`](../../../docs/seamless-short-video/05-motion-and-walk-handoff.md)

## 노출

Look Lock + frame0 게이트.  
→ [`04-look-lock-and-exposure.md`](../../../docs/seamless-short-video/04-look-lock-and-exposure.md)
