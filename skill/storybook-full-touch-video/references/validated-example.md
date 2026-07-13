# 검증된 예제 — 별빛 씨앗을 심은 여우

## 경로

- 프로젝트: `/Users/hwanchoi/project_202606/brush_remotion_video/projects/star-seed-fairy-tale-100s`
- 영상: `/Users/hwanchoi/project_202606/brush_remotion_video/output/star-seed-fairy-tale-100s.mp4`
- QA: `/Users/hwanchoi/project_202606/brush_remotion_video/data/star-seed-fairy-tale-100s`

## 구성

- 10씬 × 10초
- 1080×1920, 30fps
- 장면 이미지 10장
- Supertonic F1
- 장면당 2문장 cue
- 펜 외곽선 → 브러시 채색
- 단일 피아노 BGM + 내레이션 덕킹

## 최종 수치

| 항목 | 결과 |
|---|---:|
| duration | 100.000초 |
| frames | 3,000 |
| outline coverage | 0.9948–0.9967 |
| paint coverage | 1.0 전 씬 |
| missing pixels | 0 전 씬 |
| cursor overlap | 0 전 씬 |
| boundary diff | 최대 4.48%, 평균 4.38% |
| Integrated | -16.16 LUFS |
| True Peak | -2.33 dBTP |
| video audit | PASS, FAIL 0, WARN 1 |

WARN 1건은 Pixabay 음원의 Content ID 등록 여부를 라이선스 페이지만으로 보장할 수 없다는 게시 전 확인 항목이다.

## 실전에서 발견한 필수 보완

1. 이미지 생성기의 따뜻한 아이보리 질감은 전체 콘텐츠로 오인될 수 있다. 외곽 연결 종이를 중성 웜화이트로 정규화해야 한다.
2. 긴 마지막 장면 문장은 1.15× 속도 한도를 넘었다. 대본을 줄이는 방식으로 해결했다.
3. pen-brush 전용 `DrawingPhaseLayer`에 outro 워시가 없으면 경계 하드컷이 발생한다. 공용 전환을 적용해 해결했다.

