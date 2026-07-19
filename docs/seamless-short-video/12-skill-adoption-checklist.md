# 12. 신규 스킬 적용 체크리스트

이 문서 패키지를 **스킬로 적용·유지**할 때 사용하는 체크리스트다.  
리포 현황(2026-07-17): **정식 v1.0.0 stable** (`skill/catalog.json`, `skill/seamless-short-video/`).  
개발 계획: [dev-plan/implement_20260717_141429.md](../../dev-plan/implement_20260717_141429.md)  
아래는 v1 잔여 자동화·검증 항목.

---

## 12.1 문서 패키지 (본 디렉터리)

- [x] `docs/seamless-short-video/` 신설  
- [x] 원 설계 + 검토 보완 + 파일럿 실측 반영  
- [x] 밝기(Look Lock·frame0)·보행(hold/plant-feet) 전용 문서  
- [x] Playbook · CLI · QA · 적용 체크리스트  
- [ ] (선택) HTML 해부 페이지 / 다이어그램  

---

## 12.2 얇은 스킬 폴더

경로: `skill/seamless-short-video/`

- [x] `SKILL.md` frontmatter + 워크플로 (**v1.0 정식**)  
- [x] `agents/openai.yaml`  
- [x] `references/*` + **join-canon.md**  
- [x] SKILL.md를 본 문서 패키지 **링크로 동기화** (상세는 docs가 SSOT)  
- [x] references를 docs 요약과 중복 최소화 (docs 링크 우선)  
- [x] 조인 정본(16 §0)·Multi-Signal·frame0 불변식을 SKILL 본문에 요약  
- [x] Remotion `build.py`와 독립 제품 라인 명시  

---

## 12.3 카탈로그 · 설치

- [x] `skill/catalog.json` 등록 (`seamless-short-video`)  
- [x] version **1.0.0** · status **stable** · catalogVersion 1.3.1  
- [x] `catalog.schema.json` enum·min/max 11  
- [x] README GENERATED 표 동기화  
- [x] `bin/skill-catalog.py validate` + `check` PASS  
- [x] `bin/install-skills.sh --check`  
- [x] FIELD-LOG 정식화 항목 기록  
- [x] 개발 계획 `dev-plan/implement_20260717_141429.md`  

---

## 12.4 CLI

| 명령 | 상태 | 비고 |
| --- | --- | --- |
| `init` | 구현 | look_lock 파일 자동 생성 보강 가능 |
| `handoff` | 구현 | Last Usable Frame + next start |
| `verify` | 구현 | 해시·duration·blur |
| `concat` | 구현 | drop-last-frame · `--head-trim` · **`--auto-head-trim`** |
| `join-score` | 구현 | 조인 후보 MAE/corr (C-JOIN-TRIM) |
| `frame0-check` | **구현** | ΔY/MAE hard gate (C12); `qa.json` + report; fail exit≠0 |
| `grade-match` | **미구현** | feather 노출 매칭 |
| `status` / `--from` | 미구현 | immutable 재개 UX |

---

## 12.5 스키마

- [x] `schema/seamless-project.schema.json` (project.yaml JSON Schema **초안**)  
- [ ] qa.json / handoff_meta / end_state 스키마 또는 예시 고정 (잔여)  
- [x] frame0 게이트 기본값 문서·코드 일치 (3.5 / 4 / 4 / MAE 8)  

참고: [references/project-yaml-schema.md](references/project-yaml-schema.md) ·  
`schema/seamless-project.schema.json`

---

## 12.6 QA 자동화 목표

1. handoff 후 **`frame0-check`** (구현됨)  
2. fail 시 exit≠0, qa.json 기록 (구현됨)  
3. concat 전 전 씬 hard pass 필수 (운영 계약)  
4. soft 항목은 checklist md 또는 JSON 템플릿  

---

## 12.7 테스트

- [x] unit: sha 체인 fixture (`pipeline/tests/test_seamless_short.py`)  
- [x] unit: frame0 pass/fail + CLI tiny mp4  
- [x] unit: join-score ranking (pair metrics)  
- [x] e2e 단편: init → fake mp4 → handoff sha  
- [ ] 골든: 파일럿 handoff 해시 회귀 (대용량 mp4는 로컬 only)  

---

## 12.8 적용 시 에이전트 행동 계약 (SKILL에 넣을 문장)

```text
1. Scene 02+ start 이미지를 새로 생성하지 않는다.
2. frame0 vs start 노출 게이트 없이 다음 씬으로 진행하지 않는다.
3. 보행 경계는 hold/plant-feet를 기본으로 한다.
4. planned가 아니라 observed_end_state로 다음 프롬프트를 확정한다.
5. completed scene을 덮어쓰지 않는다.
6. Remotion bin/build.py 경로와 혼동하지 않는다.
7. 상세 사양은 docs/seamless-short-video/ 를 따른다.
```

---

## 12.9 배포 전 수동 게이트

- [ ] 30s 또는 60s 1편 soft QA 통과 (밝기·보행 포함)  
- [ ] catalog check PASS  
- [ ] install --check PASS  
- [ ] 라이선스: 생성 영상·외부 에셋 고지 경로 확인  
- [ ] README 스킬 표·배지 스킬 수 일치  

---

## 12.10 버전 정책

| 버전 | 의미 |
| --- | --- |
| 0.1.0 | 설계+CLI 골격+파일럿 (현재 specialized) |
| 0.2.0 | 문서 패키지 SSOT + frame0/walk 규칙 문서화 |
| 0.3.0 | frame0-check·grade-match 구현 후 |
| 1.0.0 | E2E 게이트·테스트·운영 안정화 |
