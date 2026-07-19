# 검증 예제

## 조인 보정 데모 (권장 — 정본 근사)

| 항목 | 값 |
| --- | --- |
| projectId | `seamless-join-fix-momo-demo` |
| 길이 | ≈20.07s (2×10s, auto head_trim=**0**) |
| 핵심 | 0–8s walk continue-only + join-score best=0 (MAE≈1.55, corr≈0.999) |
| 산출 | `output/seamless-join-fix-momo-demo.mp4` |
| 리포트 | `projects/seamless-join-fix-momo-demo/report/` |

## 60s Multi-Signal

| projectId | `seamless-popo-dandelion-60s` |
| 길이 | 6×10s ≈ 60s, 9:16 |
| 산출 | `output/seamless-popo-dandelion-60s.mp4` |

## 30s 파일럿 (교훈)

| projectId | `seamless-lulu-star-walk-30s` |
| 교훈 | C-EXP / C-MOT → doc 13·14 |
| 상세 | `docs/seamless-short-video/10-pilot-lessons-lulu-30s.md` |

## head_trim 실험 (고정 2s ≠ 정본)

| projectId | `seamless-tori-kite-18s` |
| 교훈 | s1끝↔s2@0 양호, @2 악화 → 고정 trim=2가 최적 조인 폐기 |
