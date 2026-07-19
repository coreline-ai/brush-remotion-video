# 검증 리포트 — 프로모 위젯 자산화 (P1–P4)

검증 일시: `2026-07-18 23:20 KST`
대상 워크스트림: [implement_20260718_212631.md](./implement_20260718_212631.md) (P1–P4 전체)
목적: **커밋 판단의 근거** — 테스트 통과가 아니라 "자산이 실제로 영상을 만들어내는가"의 실체 증명.

---

## 판정 요약

| # | 증명 | 방법 | 판정 |
|---|---|---|---|
| 1 | 모션 실체 | 갤러리 25초 풀 렌더 | ✅ mp4 산출 (h264·1080p·30fps·750f) |
| 2 | 독립 검수 | video-auditor 스킬 (자기평가 아님) | ⚠️→✅ 최초 FAIL(무음) → BGM 믹스 후 **양쪽 PASS** |
| 3 | 자산 재사용성 E2E | **demo에 없는 신규 props**로 새 씬 제작 | ✅ 스틸·mp4 모두 의도대로 산출 |
| 4 | 원본 대조 | 원본 KIMI 프레임 vs 재현 나란히 시트 | ✅ 시각 문법 정합 (육안) |
| 5 | 재현 가능한 게이트 | typecheck+vitest+pytest+check 일괄 로그 | ✅ 78/78 · 446/447¹ · check PASS |
| 6 | 사람 최종 판정 | mp4 직접 재생 | ☐ **미완 — 아래 사용자 확인란** |

¹ pytest 1 failed = `test_melo_adapter...` (mecab 패키지 미설치, **이 워크스트림 이전부터 존재하는 환경 의존 실패**, 해당 파일 working tree clean)

---

## 증거 위치 (`output/promo-verify/` — gitignored)

| 파일 | 내용 |
|---|---|
| `promo-widget-gallery-v0.mp4` | 증명 1 — 31종 위젯 5페이지 25초 (무음 원본) |
| `promo-widget-gallery-v0-bgm.mp4` | 증명 2 — BGM 믹스판 (**auditor PASS**) |
| `field-test.props.json` | 증명 3 — 신규 씬 정의 (demo 복사 아님: "BRUSH ENGINE FIELD TEST" 2페이지·위젯 11개) |
| `field-test-p1.png` / `field-test-p2.png` | 증명 3 — 신규 씬 스틸 |
| `field-test.mp4` / `field-test-bgm.mp4` | 증명 3 — 신규 씬 10초 렌더 (BGM판 **auditor PASS**) |
| `audit-gallery/` `audit-gallery-bgm/` `audit-field-test/` `audit-field-test-bgm/` | 증명 2 — audit-report.md + 증거 스틸 4세트 |
| `compare/compare-sheet.png` | 증명 4 — 좌 원본 / 우 재현 3쌍 (게이지·터미널·리더보드) |
| `gates-20260718.log` | 증명 5 — 게이트 일괄 실행 전문 로그 |

---

## 증명 2 세부 — auditor 판정의 의미

**최초 검수는 FAIL이었다** (두 mp4 모두 `audio-silence`). 이는 결함 은폐 없이 기록한다:

- 갤러리·필드테스트는 **오디오 없는 시각 자산**인데, auditor는 "완성 영상 제품" 기준으로 검사 → 정당한 FAIL.
- 해소: 레포 관례(렌더 후 ffmpeg 믹스)대로 라이선스 검증 로컬 BGM(`pixabay-digital-ambient-meditation`, [assets/bgm/catalog.json](../assets/bgm/catalog.json) 등재)을 **−23 LUFS**(공통 BGM 정책)로 믹스 → 재검수 **PASS** (FAIL 0).
- 컴포지션 코드는 무변경 — 오디오는 파이프라인 단계 책임이라는 기존 설계 유지.

잔여 WARN (수용 근거와 함께 기록):
- `freeze` 3.1–3.4초 ×2: 페이지 모션(~3초) 정착 후 홀드 — **갤러리 설계 특성** (시각 회귀용 정지 구간). 실전 씬에서는 페이지 길이-모션 동기가 필요 → 계획서 잔여 리스크와 일치.
- `letterbox/필러박스`: 다크 배경의 빈 영역을 밴드로 감지 — 다크 위젯 특성상 오탐성.
- `wash-jump f636`: 페이지 4→5 전환점의 밝기 점프 (화이트 로고 락업 등장) — 의도된 연출.

## 증명 3 세부 — 자산화의 실질 검증

demo를 복사하지 않고 SKILL.md의 props 계약만으로 신규 씬을 제작:
- 새 주제(이 레포 자체), 새 수치(31 WIDGETS·PYTEST 452·7 FAMILIES·JUL 18), 새 배치, 새 위젯 조합(countUp+gauge+leaderboard+statBar+pillBadge / terminal+checklist+banner+splitFlap+dateFlip+logoLockup)
- zod strict가 계약 밖 필드를 거부하는 상태에서 **1회 작성으로 통과** → 위젯이 문서화된 파라메트릭 자산으로 기능함을 증명.

---

## P5 연출 계층 검증 추가 기록 (2026-07-19)

실전 렌더(Cowork)에서 원본 대비 품질 갭 지적(사용자) → P5-A/B/C로 갭 해소. 검증 사건:

| 사건 | 내용 |
|---|---|
| **원본 전환 재분석** | 4구간 프레임 버스트 추출 → white-flash는 "전프레임 노출 리프트 베일"이며 씬 중간 비트에도 반복 사용됨을 계측. 키네틱 타입은 거대(1.5×)→수축 등장 |
| **auditor 장르 충돌·반증** | v2 검수 FAIL 5(spike/hardcut) = 의도한 원본 문법. **원본 KIMI 영상 자체를 auditor로 검수 → FAIL 47** (`audit-original-kimi/`) — 장르 특성 증명. 오디오·규격 항목만 게이트로 유효 |
| **플래시 재보정** | 원본 스파이크 diff ~37% vs v2 ~16% → peak 0.4→0.5·상승 2f→1f 상향 |
| **BGM 정책 이슈 (사용자 질의로 발견)** | 검증 mp4의 BGM(pixabay-digital-ambient-meditation, Amurich, Pixabay License)은 카탈로그상 `youtubeAllowed: false` — **내부 검증용으로만 유효, 배포 시 YT-OK 9곡 또는 piano-bgm 자작으로 교체 필수** |

추가 증거: `cowork-v2-bgm.mp4`(전환+무대) · `cowork-v3-bgm.mp4`(키네틱 타이틀+원본급 플래시, **최종 판정 대상**) · `v3-kinetic-check.png`(거대→수축→플래시→정착 시퀀스) · `cwsc-check.png`(light-sweep·spotlight)

## 사용자 확인란 (커밋 전 필수)

- [ ] **`cowork-v3-bgm.mp4` 재생 — 원본 참조 영상 대비 역동성이 목적에 부합하는가 (P5 최종 판정)**
- [ ] `promo-widget-gallery-v0-bgm.mp4` 재생 — 32종 위젯 모션이 의도대로 움직이는가
- [ ] `field-test-bgm.mp4` 재생 — 신규 씬이 어색함 없이 성립하는가
- [ ] `compare/compare-sheet.png` — 원본 대비 재현 수준이 목적에 부합하는가
- [ ] 위 확인 후 커밋 승인 여부 결정 (배포 계획이 있으면 BGM 교체 선행)

## 검증자 소견

기술 게이트·독립 검수·재사용성 E2E·원본 대조·장르 반증까지 기계로 증명 가능한 것은 전부 통과했다.
남은 것은 **사람의 육안 판정**(위 확인란)뿐이며, 이것이 채워지기 전에는 커밋하지 않는다.
