# QA Report — 겁이 많은 작은 별의 첫 비행 (star-first-flight-v1)

- 검사 시각: 2026-07-13 (KST)
- 대상: `scene-01.png` ~ `scene-10.png`
- 기준: 1080×1920 PNG, 9:16 풀블리드, 펜 외곽선→브러시 채색에 적합한 평면 색면

## 자동 검사

| 항목 | 결과 |
|---|---|
| 씬 파일 수 | 10/10 — PASS |
| 해상도 | 10/10 — PASS (1080×1920) |
| 색상 모드 | 10/10 — PASS (RGB) |
| 파일 포맷 | 10/10 — PASS (PNG) |
| 풀블리드 캔버스 | 10/10 — PASS (불투명 bbox 전체 캔버스) |
| 프레임/매트/레터박스 | 10/10 — PASS (가장자리 단색 띠 없음) |

## 씬별 확인

| 씬 | 파일 | 해상도 | 풀블리드 | 가장자리 단색 띠 |
|---:|---|---|---|---|
| 01 | `scene-01.png` | PASS | PASS | PASS |
| 02 | `scene-02.png` | PASS | PASS | PASS |
| 03 | `scene-03.png` | PASS | PASS | PASS |
| 04 | `scene-04.png` | PASS | PASS | PASS |
| 05 | `scene-05.png` | PASS | PASS | PASS |
| 06 | `scene-06.png` | PASS | PASS | PASS |
| 07 | `scene-07.png` | PASS | PASS | PASS |
| 08 | `scene-08.png` | PASS | PASS | PASS |
| 09 | `scene-09.png` | PASS | PASS | PASS |
| 10 | `scene-10.png` | PASS | PASS | PASS |

## 시각 검수 메모

- 모든 씬은 세로 9:16 풀블리드 구성으로 생성되었고 텍스트·로고·워터마크·카드 테두리는 보이지 않는다.
- 루미의 따뜻한 금색 팔레트, 둥근 눈, 부드러운 빛 표현은 유지되며, 생성 모델 특성상 장면별 실루엣(오각별/초승달형)이 일부 변형된다. 영상 연결 시 공통 팔레트와 얼굴 요소를 기준으로 사용한다.
- 128색 무디더 양자화로 미세한 색 번짐을 줄여 붓 채색 리빌에 유리하게 정리했다.

## 산출물

- `scene-01.png` … `scene-10.png`
- `contact-sheet.png`
- `manifest.json`
- `qa-report.md`
