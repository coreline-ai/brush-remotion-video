# 무드 프리셋 — 검증된 조합 6종 + 운용 규칙

## 운용 규칙 ("매번 같은 템플릿" 방지)

1. **한 영상 = 한 프리셋** — 한 영상 안에서 프리셋을 섞지 않는다 (일관성). 변주는 프리셋 안에서 씬별로만.
2. **새 영상은 직전 영상과 다르게** — 연속 제작 시 직전 프로젝트와 **다른 프리셋 또는 다른 seed(brushDynamics·naturalEffects)·accent·배경 소재**를 쓴다.
   확인 방법: `ls -t data/ | head`로 최근 projectId를 찾아 그 props의 프리셋·seed를 보고 겹치지 않게 제안한다.

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

> 쇼츠(`format: shorts`)일 때: **shorts-brush 스킬로 위임** — 자막 세이프존(bottom 290)·씬별 강조색 동조·훅/루프 엔딩이 자동. 위 프리셋들은 세로에서도 그대로 쓰되 씬마다 소재·팔레트 변주.

## ✒️ 펜 스케치 (빠른 설명형 — pen-video 스킬로 위임)
```yaml
drawing: { profile: pen }   # 잉크-알파 분리 + 정밀 routes + 펜 커서 자동
background: { strategy: imagegen }   # 선화 프롬프트 (background-prompt.md ✒️ 섹션)
# 특징: 종이 항상 보임, 잉크 선만 빠르게(씬의 35%) 그려짐, faint 1.0 즉시 또렷
# 무드가 "펜/스케치/화이트보드/설명"이면 이 프리셋 — 실행은 pen-video 스킬
```
