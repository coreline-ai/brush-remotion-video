# 무드 프리셋 — 검증된 조합 6종

프리셋은 출발점이다. 확정 후 intent-map으로 미세 조정한다.
공통 베이스(실측 중앙값): `linearDraw: true, faint: 0.7, edgeFeather: 12, developFrames: 18,
brushDynamics: {touchScale: 1.45, touchJitter: 0.22, randomizeOrder: true, randomReverse: true}`

## ❄️ 겨울밤 (잔잔·별빛)
```yaml
naturalEffects: { kind: starTwinkle, opacity: 0.04, endFadeOpacity: 0.3 }
brushDynamics: { drawSpeedScale: 1.12 }   # 느긋한 붓
outroFadeFrames: 24
# 팔레트 힌트: 청회색 계열 accent (#6b8499), BGM 피아노 패드
```

## 🌄 아침 숲 (안개·차분)
```yaml
naturalEffects: { kind: mist, opacity: 0.035 }
prewashOpacity: 0.6         # 첫 씬만 — 안개 낀 도입
prewashFrames: 36
faint: 0.65
```

## 🌅 노을 산책 (따뜻함·부유감)
```yaml
naturalEffects: { kind: sunsetGlow, opacity: 0.045, parallaxScale: 1.02 }
outroBlur: 8                # 몽환적 오버랩 전환
# 팔레트 힌트: ochre/clay accent
```

## 🌾 들판 바람 (가벼움·흐름)
```yaml
naturalEffects: { kind: meadowWind, opacity: 0.04 }
brushDynamics: { drawSpeedScale: 0.95, pathJitter: 40 }   # 경쾌 + 손맛
```

## 💧 시냇물 (청량·반짝임)
```yaml
naturalEffects: { kind: streamSparkle, opacity: 0.04 }
faint: 0.72
outroWashOpacity: 0.9
```

## 📚 지식·설명형 (또렷함·정보)
```yaml
# 파티클 없음 — 위젯·타이틀이 주인공
faint: 0.72
topTitle: { wash: true, fontSize: 44, enterAt: 12 }
# widgets: 내용에 맞게 2~4장 (타이틀 아래 y ≥ 230), TTS 더빙 권장
```

> 쇼츠(`format: shorts`)일 때: 위젯·타이틀 좌표는 1080×1920 기준으로 재배치, 자막 bottom 여유 확대.
