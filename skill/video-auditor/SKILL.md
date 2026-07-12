---
name: video-auditor
description: >-
  완성된 mp4 하나만으로 영상 결함을 자동 검출하는 독립 검수 스킬. 씬 전환 하드컷·
  번쩍(develop) 스파이크·정지 구간·오디오(무음/클리핑)·규격(해상도/fps/코덱/쇼츠 길이)·
  레터박스를 스캔해 PASS/FAIL 리포트와 문제 지점 증거 스틸, FIELD-LOG 초안까지 산출한다.
  brush_remotion_video 산출물뿐 아니라 어떤 mp4든 검수 가능(파이프라인·props 불필요).
  600초 영상 스캔 ≤ 75초, exit code로 자동화 게이트 사용 가능.
---

# video-auditor — 완성본 자동 검수

**실행 대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
**입력은 mp4 하나** — 파이프라인·props 없이 동작한다. 어떤 영상이든(구 시스템·외부 영상 포함) 검수 가능.

## 언제 이 스킬인가

- "영상 검수해줘 / 이상한 부분 찾아줘 / 업로드 전 점검해줘"
- 씬별 연출 리뷰(사람 눈 판단)는 → brush-qa-review / **수치로 재는 결함 검출**은 → video-auditor

## 실행

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/python bin/audit.py <video.mp4> [--props data/{pid}/props.json] [--out <dir>]
```

- `--props`: 주면 씬 경계를 정확히 판정 (없으면 순백 프레임으로 자동 추정 — 독립 실행)
- 산출: `audit-report.md`(사람) + `audit-report.json`(기계) + `evidence/*.png`(문제 지점 전후 프레임) + **FIELD-LOG 초안**
- exit code: 0 = PASS, 1 = FAIL — 빌드 게이트로 쓰려면 `bin/build.py <yaml> --audit`

## 검출 항목과 임계값 (실전 실측 기반)

| 검사 | WARN | FAIL | 근거 사례 |
|---|---|---|---|
| 씬 경계 하드컷 | > 6% | **> 10%** | city 원본 12~23% (FIELD-LOG) |
| 씬 중간 번쩍 스파이크 | > 1.5% & 3×주변 | **> 2.5% & 4×주변** | develop 스파이크 2.97% (FIELD-LOG) |
| 정지 구간 | 씬 중간 3초+ | 전체 정지 | 씬 끝 감상 구간은 INFO |
| 오디오 | 무음 > 2초, 클리핑 > -0.5dB | 전체 무음 | — |
| 규격 | fps ≠ 30 | 비표준 해상도, 쇼츠 > 180초 | 2026 쇼츠 규정 |
| 워시 온셋 | 씬 중간이면 WARN | — | 구도 유지(corr≥0.9) 점프는 outro 워시로 분류 |

## 리포트 해석 가이드

- **FAIL** → 업로드 보류. evidence 스틸(전→후 프레임 쌍)을 Read로 열어 눈으로 확인 → 원인별 처방:
  - boundary-hardcut → `outroWashOpacity 0.9~1.0 + outroFadeFrames 18` + prewash 첫 씬 전용 (brush-video §문제 해결)
  - spike → develop 구간이면 렌더러 회귀 의심 (FIELD-LOG 3번 사례 참조)
- **WARN** → 사람이 판단. 어두운 씬 경계 6~7%는 허용 범위일 수 있음
- 미적·내용 품질은 도구가 판단하지 않는다 — evidence·QA 갤러리 스틸을 보고 직접 판단할 것

## FIELD-LOG 환류 (필수 절차)

FAIL을 수정했으면: 리포트가 만들어 준 **FIELD-LOG 초안**의 원인/수정/환류 칸을 채워
`FIELD-LOG.md`에 추가하고, 재발 방지를 해당 문서/검증기에 반영한다. 수정 후 재검수로 PASS 확인.

실물 예시: `data/audit/city-watercolor-600s-final-props/audit-report.md`
(사람이 수동으로 찾았던 하드컷 55곳 + 번쩍 1곳을 도구가 재발견한 리포트)
