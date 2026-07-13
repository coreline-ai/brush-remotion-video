# 풀터칭 이미지 계약

## 1. 정의

풀터칭 이미지는 보기 좋은 완성 일러스트만을 뜻하지 않는다. 펜 경로와 브러시 채색 경로가 의미 있는 객체를 따라가며 최종 픽셀을 빠짐없이 재현할 수 있는 애니메이션 입력 자산이다.

## 2. 캔버스

| 포맷 | 크기 | 규칙 |
|---|---:|---|
| Shorts | 1080×1920 | 처음부터 9:16으로 생성. 가로 이미지 크롭 금지 |
| YouTube | 1920×1080 | 처음부터 16:9로 생성. 세로 이미지 확장 금지 |

- 주인공과 핵심 소품을 안전 여백 안에 둔다.
- 쇼츠는 상단에 호흡 공간을 두고 하단 UI·자막 영역과 핵심 얼굴이 겹치지 않게 한다.
- 한 장면의 주 시선을 하나로 유지한다.

## 3. 종이 배경

- 캔버스 전체를 칠한 밤하늘·숲·그라디언트를 사용하지 않는다.
- 외곽과 연결된 배경은 균일한 중성 웜화이트 `RGB(250,249,247)`를 권장한다.
- 노란 기가 강한 아이보리는 저채도 종이가 아니라 색상 콘텐츠로 검출될 수 있으므로 금지한다.
- 이미지 생성 모델이 만든 종이 질감·명암·비네팅은 렌더 전에 정규화한다.

## 4. 객체와 색면

- 모든 주요 객체를 완전한 닫힌 짙은 잉크선으로 감싼다.
- 인접 색상은 잉크선으로 분리한다.
- 중대형 연결 색면을 우선한다.
- 주요 객체는 서로 과도하게 겹치지 않는다.
- 여우의 얼굴, 목도리, 손, 씨앗처럼 이야기 핵심 부위를 독립적인 의미 영역으로 만든다.

## 5. 금지 요소

- 미세 먼지, 수백 개 별가루, 스프레이, 작은 빗방울 군집
- 반투명 안개, 헤일로, 블룸, 렌즈 플레어
- 복잡한 그라디언트, 사진식 조명, 강한 그림자
- 불완전하거나 끊어진 외곽선
- 화면 전체 수채 워시
- 장면마다 달라지는 캐릭터 비율·색·의상
- 텍스트, 캡션, 로고, 워터마크

## 6. 캐릭터 일관성

첫 장면을 기준 레퍼런스로 고정하고 이후 생성마다 다음 불변 조건을 명시한다.

- 종, 연령감, 얼굴 비율, 눈 모양
- 털 색과 크림색 부위
- 의상과 고유색
- 꼬리 모양과 끝 색
- 선 굵기와 채색 질감

한 번에 여러 장을 생성하기보다 장면마다 생성하고 앞선 승인 이미지를 레퍼런스로 누적한다.

## 7. 기본 프롬프트 블록

```text
Asset type: 1080x1920 vertical storybook scene for pen-outline-to-brush-fill animation.
Preserve the exact character identity, clothing, proportions, palette and line weight from the references.
Use a uniform neutral warm-white paper background. Do not paint a full-bleed sky or environment.
Every drawable object must have a complete closed dark contour. Separate neighboring color regions with ink.
Prefer medium-to-large semantic shapes suitable for contour tracing and brush flood fill.
Avoid tiny particles, scattered dots, haze, gradients, heavy shadows, text, logo and watermark.
```

장면 설명에는 주인공 위치, 핵심 행동, 세로 시선 흐름, 객체 그리기 순서를 구체적으로 추가한다.

## 8. 종이 정규화

`scripts/normalize-storybook-paper.py`는 다음 순서로 처리한다.

1. 밝고 저채도인 후보 픽셀을 찾는다.
2. 이미지 외곽과 연결된 컴포넌트만 종이로 판정한다.
3. 닫힌 외곽선 안의 크림색·구름·달 색은 보존한다.
4. 종이 영역만 `RGB(250,249,247)`로 치환한다.
5. 네이티브 캔버스로 contain-fit한다.

정규화 후에도 `contentFraction > 0.97`이면 full-bleed 실패로 처리한다.

## 9. 이미지 승인 체크

- [ ] 네이티브 화면비와 정확한 픽셀 크기
- [ ] 외곽 연결 종이 영역이 충분함
- [ ] 주요 색면의 닫힌 외곽선
- [ ] 캐릭터 불변 조건 유지
- [ ] 미세 파티클·안개·전체 워시 없음
- [ ] 하단 자막 안전영역 확보
- [ ] 이미지 10장 콘택트시트에서 이야기 흐름이 읽힘

