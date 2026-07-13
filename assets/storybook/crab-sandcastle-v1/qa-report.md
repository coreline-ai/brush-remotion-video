# QA Report — 작은 게의 모래성 대회 (crab-sandcastle-v1)

- 검사 기준: 1080×1920 PNG / 9:16 풀블리드 / 펜 외곽선→브러시 채색용 색면
- 생성 경로: built-in image_gen → 로컬 정규화(128색 무디더)

## 자동 검사

| 항목 | 결과 |
|---|---|
| 씬 수 | 10/10 — PASS |
| 해상도 | 10/10 — PASS (1080×1920) |
| 색상 모드 | 10/10 — PASS (RGB) |
| 포맷 | 10/10 — PASS (PNG) |
| 캔버스 풀블리드 | 10/10 — PASS |
| 외곽 프레임/여백/레터박스 | 10/10 — PASS (단색 가장자리 띠 없음) |
| 텍스트/로고/워터마크 | 시각 검수 PASS |

## 씬별 결과

| 씬 | 해상도 | RGB | 풀블리드 | 가장자리 검사 |
|---:|---|---|---|---|
| 01 | PASS | PASS | PASS | PASS |
| 02 | PASS | PASS | PASS | PASS |
| 03 | PASS | PASS | PASS | PASS |
| 04 | PASS | PASS | PASS | PASS |
| 05 | PASS | PASS | PASS | PASS |
| 06 | PASS | PASS | PASS | PASS |
| 07 | PASS | PASS | PASS | PASS |
| 08 | PASS | PASS | PASS | PASS |
| 09 | PASS | PASS | PASS | PASS |
| 10 | PASS | PASS | PASS | PASS |

## 시각 검수 메모

- 콩이의 주황색 몸, 둥근 눈, 파란 줄무늬 조개 모자, 작은 나무 삽을 전 씬 공통 기준으로 유지했다.
- 불가사리와 보라색 소라게 친구도 동일한 단순 동화풍 외형으로 유지했다.
- 일부 장면은 파도·모래 표현에 색조 변화가 있으나 128색 무디더 처리로 브러시 채색용 색면을 정리했다.
- 접촉 시트의 SCENE 라벨은 검수용이며, 개별 씬 PNG에는 텍스트가 없다.

## 산출물

- `scene-01.png` … `scene-10.png`
- `contact-sheet.png`
- `manifest.json`
- `qa-report.md`
