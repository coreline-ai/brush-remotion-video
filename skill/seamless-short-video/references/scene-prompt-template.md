# 장면 프롬프트 6블록 (요약)

**전문:** [`docs/seamless-short-video/07-prompt-system.md`](../../../docs/seamless-short-video/07-prompt-system.md)

1. **Start lock + exposure** — frame0 = 입력, relight 금지  
2. **Character Lock + Look Lock** — 매 씬 동일  
3. **observed_end_state**  
4. **Timeline** — 0–2s overlap only, 9–10s hold/plant-feet  
5. **Handoff goal / ending hold**  
6. **Negative** — redesign, teleport, fade, relight, bloom spike  

짧은 I2V 한 줄:

```text
Same character continues [active_motion], then [main action],
camera [same], lighting unchanged, ends in stable hold/plant-feet.
No cut, no redesign, no relight.
```
