# Pen-Brush Fidelity Contract

## 절대 규칙

1. 한 원본에서 모든 레이어를 파생해 좌표·크기를 동일하게 유지한다.
2. outline은 local contrast로 추출하고 팽창하지 않는다.
3. outline 완료 시 paint opacity는 0이며, paint 시작은 outline pen-off 이후다.
4. paint는 자동 존 bbox를 넓은 붓질로 덮고 RGBA alpha가 오브젝트 경계를 자른다.
5. paint 완료 직전 outline을 1→0으로 페이드한다. 최종 화면의 선은 color 원본선 하나뿐이다.
6. 완성 bitmap을 별도 레이어로 갑자기 붙이지 않는다.
7. contain-fit을 사용한다. 잘림·비율 왜곡을 금지한다.

## 자동 게이트

| 항목 | 기준 |
|---|---:|
| outline coverage | ≥ 99% |
| paint coverage | ≥ 99.99% |
| paint missingPixels | 0 |
| color leak at outline end | 0 |
| cursor overlap | 0 frame |
| 타임라인 | outline start < end ≤ paint start < end < duration |
| 영상 | 30fps, h264/aac, 1920×1080 또는 1080×1920 |

## 입력 권장

- 균일한 white/warm-white paper
- fine black ink outline
- 넓고 분리된 flat/pastel color regions
- no text, no labels, no grid, no shadow gradient
- 가로는 16:9, 세로는 9:16 원본을 각각 생성
