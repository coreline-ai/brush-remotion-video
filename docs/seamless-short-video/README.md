# Seamless Short Video — 설계·운영 문서 패키지

**스킬 ID (적용 예정/리포 등록명):** `seamless-short-video`  
**원 설계명:** SeamlessShortVideoMaker  
**문서 버전:** 0.5.1  
**스킬 버전:** **v1.0.0 stable** (`skill/seamless-short-video`)  
**최종 갱신:** 2026-07-17  

이 디렉터리는 신규 스킬 적용을 위한 **단일 문서 원천**이다.  
원 설계안, 설계 검토, 파일럿 실측, 공통 수정 표준,  
그리고 **Multi-Signal Handoff(마지막 이미지=frame0 + 다중 정보 인계)** 아키텍처를 포함한다.

> **정본 방향 (v0.4+):** 후처리로 끊김을 가리지 않는다.  
> **[14-multi-signal-handoff-architecture.md](14-multi-signal-handoff-architecture.md)**  
> — 마지막 이미지를 0프레임 앵커로 쓰고, State/Motion/Look/Camera/Context를 함께 넘긴다.  
> 증상 패치(C-xxx)는 [13](13-common-remediation-standard.md)이 담당하되, **14가 원칙에서 우선**한다.

> **공통 적용 v0.5.1 (조인 정본):**  
> **이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받으면,  
> 경계에 불필요 연출 없이 자연 연결된다.**  
> (지금 I2V는 영상 꼬리 입력이 없어 근사만 가능. 고정 head_trim=2 ≠ 이전 2초 연속.)  
> → **[16](16-tail-overlap-content-model.md) §0** · [13](13-common-remediation-standard.md) · [15](15-ten-second-boundary-common-playbook.md)

| 구분 | 경로 |
| --- | --- |
| **정식 스킬 v1.0.0** (코드 사본 0) | [`skill/seamless-short-video/`](../../skill/seamless-short-video/SKILL.md) · catalog `stable` |
| 로컬 CLI | [`bin/seamless-short.py`](../../bin/seamless-short.py) |
| 개발 계획 | [`dev-plan/implement_20260717_141429.md`](../../dev-plan/implement_20260717_141429.md) |
| 파일럿 (초기) | [`projects/seamless-lulu-star-walk-30s/`](../../projects/seamless-lulu-star-walk-30s/) |
| 조인 보정 데모 | [`projects/seamless-join-fix-momo-demo/`](../../projects/seamless-join-fix-momo-demo/) · [`output/seamless-join-fix-momo-demo.mp4`](../../output/seamless-join-fix-momo-demo.mp4) |
| head_trim 실험 | [`projects/seamless-tori-kite-18s/`](../../projects/seamless-tori-kite-18s/) |

---

## 문서 지도

| # | 문서 | 내용 |
| --- | --- | --- |
| 01 | [01-overview-and-principles.md](01-overview-and-principles.md) | 목적, 핵심 공식, brush 라인과 구분, v1 스코프 |
| 02 | [02-design-spec-full.md](02-design-spec-full.md) | 원 설계 전개(인계·Overlap·분할·프롬프트·상태머신) + v0.2 보강 |
| 03 | [03-handoff-contract.md](03-handoff-contract.md) | Last Frame / Last Usable Frame / start≡handoff 계약 |
| 04 | [04-look-lock-and-exposure.md](04-look-lock-and-exposure.md) | 경계 밝기 점프 원인·Look Lock·frame0 게이트·grade-match |
| 05 | [05-motion-and-walk-handoff.md](05-motion-and-walk-handoff.md) | 보행·동작 끊김, hold/착지 인계, overlap 편집 |
| 06 | [06-character-and-scene-state.md](06-character-and-scene-state.md) | Character Lock, planned/observed end_state |
| 07 | [07-prompt-system.md](07-prompt-system.md) | 6블록 프롬프트 + 노출/보행 강화 문장 |
| 08 | [08-qa-and-gates.md](08-qa-and-gates.md) | Hard/Soft 게이트, 재시도, 드리프트 |
| 09 | [09-workflow-and-cli.md](09-workflow-and-cli.md) | 실행 단계, CLI, 프로젝트 트리, project.yaml |
| 10 | [10-pilot-lessons-lulu-30s.md](10-pilot-lessons-lulu-30s.md) | 30초 파일럿 실측·교훈 |
| 11 | [11-failure-playbook.md](11-failure-playbook.md) | 실패 유형별 처방 |
| 12 | [12-skill-adoption-checklist.md](12-skill-adoption-checklist.md) | 신규 스킬 적용 체크리스트 |
| **13** | [13-common-remediation-standard.md](13-common-remediation-standard.md) | 공통 수정 방향 (C-xxx 증상 처방) |
| **14** | **[14-multi-signal-handoff-architecture.md](14-multi-signal-handoff-architecture.md)** | **정본: 마지막 이미지=frame0 + 다중 신호 인계 패킷** |
| **15** | **[15-ten-second-boundary-common-playbook.md](15-ten-second-boundary-common-playbook.md)** | **10초 경계 공통 적용 항목 C1–C20 + 처방·결합 레시피** |
| **16** | **[16-tail-overlap-content-model.md](16-tail-overlap-content-model.md)** | **★ 조인 정본: 이전 ~2초 동작 연속 + (부) head_trim 근사** |
| — | [references/](references/) | 템플릿·스키마 초안·체크리스트 사본 |
| — | [examples/](examples/) | 패킷 YAML·Look Lock·scene_end_type 예시 |

---

## 한 줄 정의

> 여러 개의 10초 Image-to-Video를 **단순 이어붙이지 않고**,  
> **(1) 마지막 정상 프레임 이미지 + (2) 종료 상태 + (3) 동작 방향**을 장면마다 연쇄 인계하여  
> 캐릭터·조명·동작이 이어지는 30~60초 숏폼을 반자동 제작하는 시스템.

---

## 핵심 공식 (강제)

```text
【조인 정본 — 공통 적용 1순위】
다음 Scene의 시작 동작 = 이전 Scene 마지막 ~2초 동작의 연속
→ 그 구간에는 새 안무·엔딩 연출·임의 포즈 변경을 넣지 않는다.
→ 불필요 동작을 “잘 넣을” 문제가 아니라, 이어 받으면 안 넣어도 된다.
상세: docs/16 §0

【인계 수단】
다음 Scene 시작 이미지 = 이전 Last Usable Frame
다음 Scene 시작 상태   = observed_end_state
(이상) 입력에 이전 말미 ~2초 영상 tail 포함 — 현재 I2V는 미지원 → 근사
```

**추가 불변식**

```text
frame0 ≈ start_image (노출·구도; ΔY·MAE 게이트)
조인 창 = 이전 말미 동작 복붙 only (정본·근사 공통)
고정 head_trim=2 를 “이전 2초 연속”이라고 부르지 말 것
walk peak-swing / 조인 직후 포즈 발명 금지
```

**공통 수정 표준:** C-xxx → [13](13-common-remediation-standard.md).  
**Multi-Signal:** [14](14-multi-signal-handoff-architecture.md).  
**이전 2초 동작 연속 정본:** [16 §0](16-tail-overlap-content-model.md).  
**근사 조립:** `auto-head-trim` (고정 2s 폐기 ≠ 정본).

---

## 빠른 시작

```bash
# 1) 프로젝트 골격
python3 bin/seamless-short.py init \
  --project-dir projects/<id> \
  --project-id <id> \
  --title "제목" \
  --scenes 3 --scene-seconds 10 --aspect 9:16

# 2) Scene01 이미지만 생성 → I2V → mp4 저장 후
python3 bin/seamless-short.py handoff --project-dir projects/<id> --scene 1 --video path.mp4

# 3) Hard gate (start 해시 체인 등)
python3 bin/seamless-short.py verify --project-dir projects/<id>

# 4) 조인 스코어 확인 후 적응형 head_trim 결합 (공통 기본)
python3 bin/seamless-short.py join-score --project-dir projects/<id> --scene 1
python3 bin/seamless-short.py concat \
  --project-dir projects/<id> \
  --auto-head-trim --head-trim-max 2 \
  --out output/<id>.mp4
```

상세 운영 규칙은 [09-workflow-and-cli.md](09-workflow-and-cli.md)를 따른다.

---

## 변경 이력

| 버전 | 일자 | 요약 |
| --- | --- | --- |
| 0.1.0 | 2026-07 | 원 설계안 SeamlessShortVideoMaker 초안 |
| 0.2.0 | 2026-07-17 | 설계 검토 P0 반영, 리포 스킬·CLI 파일럿, 밝기/보행 실측 보완, 본 문서 패키지 신설 |
| 0.3.0 | 2026-07-17 | 파일럿 오류를 전 영상 공통 원인 클래스(C-xxx)·해결·보완·게이트로 일반화 (doc 13) |
| 0.4.0 | 2026-07-17 | Multi-Signal Handoff 정본 (doc 14): frame0=last image + 다중 정보 인계; 후처리 과집중 탈피 |
| 0.4.1 | 2026-07-17 | doc 15 10초 경계 공통 적용 C1–C20; popo 60s tone-match hard-cut remaster |
| 0.5.0 | 2026-07-17 | 조인 공통: C-MOT-CHANGE·C-JOIN-TRIM, auto-head-trim, 조인 창 0–8s; tori/momo 실측 환류 |
| 0.5.1 | 2026-07-17 | **정본 명문화:** 이전 ~2초 동작 연속 → 불필요 연출 없이 자연 연결 (doc16 §0); head_trim≠연속 |
