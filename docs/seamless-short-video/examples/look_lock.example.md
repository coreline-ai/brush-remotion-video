# Look Lock 예시 — 달빛 정원

```yaml
look_lock:
  time_of_day: moonlit night
  key_light: soft cool moonlight from upper-left
  fill: warm glow only from character's small lantern
  exposure: dim magical garden; no daylight; no auto-HDR
  white_balance: cool night air + warm practical lantern
  contrast: medium-low
  bloom: low and stable
  forbid:
    - sunrise or golden-hour boost
    - sudden brightness increase on cut
    - new strong light sources in the last 1 second
    - bloom or glow ramp at shot end
```

프롬프트 삽입용 한 문단:

```text
Lighting lock: soft cool moonlight from upper-left, warm lantern fill only,
dim night exposure, medium-low contrast, low stable bloom.
Do not relight, brighten, or change time of day.
```
