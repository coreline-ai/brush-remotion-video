---
name: seamless-short-video
description: >-
  캐릭터·이야기 콘셉트로부터 약 30~60초 연속형 숏폼을 Last Frame Handoff + Multi-Signal로 제작하는
  독립 스킬(Remotion 붓 라인과 무관). 조인 정본은 이전 씬 말미 ~2초 동작을 다음 씬이 이어 받는 것.
  Image-to-Video 연쇄 + bin/seamless-short.py. "심리스 숏폼", "연속 영상", "last frame handoff",
  "I2V 10초 연결", "SeamlessShortVideoMaker", "이전 2초 동작 연속", "auto-head-trim",
  "join-score", /seamless-short-video 요청에 사용한다.
---

# seamless-short-video (정식 v1.0)

`brush_remotion_video`의 **독립 제품 라인**이다.  
렌더러(`src/`)·`bin/build.py`(Remotion 붓/펜)를 쓰지 않는다.  
실행 코드는 리포 `bin/seamless-short.py`에만 두고, 이 스킬은 **워크플로·계약 요약**만 담는다 (코드 사본 0).

**SSOT 문서 패키지:** [`docs/seamless-short-video/`](../../docs/seamless-short-video/README.md)

---

## 조인 정본 (공통 적용 1순위)

전문: [16 §0](../../docs/seamless-short-video/16-tail-overlap-content-model.md)

```text
이전 Scene 마지막 ~2초 동작을 다음 Scene이 그대로 이어 받는다
→ 경계에 불필요한 동작 연출을 넣을 필요가 없고 자연 연결된다.

정본 입력(이상): 이전 말미 ~2초 영상 (모션 tail)
현재 I2V:        말미 1프레임만 → 정본 불가 → 아래 근사
head_trim=2:     이전 2초 연속이 아님 (다음 클립 앞부분 폐기)
```

| | |
| --- | --- |
| **정본** | 말미 ~2초 **영상** 이어 그리기 |
| **근사** | last frame + packet 동작 명시 + 조인 창 continue-only + `auto-head-trim` |
| **금지** | 컷 직후 임의 포즈/엔딩 연출, still multi-frame, long dissolve, trim=연속 오해 |

---

## Multi-Signal Handoff (인계 수단)

전문: [14](../../docs/seamless-short-video/14-multi-signal-handoff-architecture.md)

```text
다음 start 이미지     = 이전 Last Usable Frame (신규 이미지 생성 금지)
다음 frame0 목표      = 그 이미지와 동일 (relight·재구성 금지)
다음 시작 상태        = observed_end_state
다음 조인 창 동작     = 이전 말미 동작 연속 only
+ Look Lock / Character Lock / Camera / tail context
조립                  = join-score → auto-head-trim (고정 2s 비기본)
```

인계는 **파일 하나**가 아니라 **handoff_packet** 이다.  
예시: [examples/handoff-packet.example.yaml](../../docs/seamless-short-video/examples/handoff-packet.example.yaml)

---

## 언제 이 스킬인가

| 요청 | 스킬 |
| --- | --- |
| AI 클립을 이어 붙여 캐릭터·동작이 끊기지 않는 숏폼 | **이 스킬** |
| 흰 종이 붓/펜 Remotion | brush-video / pen-* / shorts-brush |
| 동화 정지화 + 펜→채색 + TTS | storybook-full-touch-video |

---

## 에이전트 행동 계약

1. Scene 02+ start 이미지를 **새로 생성하지 않는다** (sha = prev handoff).  
2. frame0 vs start 확인 없이 다음 씬으로 가지 않는다 (ΔY 목표 ≤4, MAE ≤8).  
3. **조인 정본**: 이전 말미 ~2초 동작을 이어 받기 — 불필요 연출 추가 금지.  
4. 조인 창 프롬프트 = active_motion **복붙 only** (권장 0–8s continue-only).  
5. observed_end_state로 다음 프롬프트를 확정한다 (planned 아님).  
6. completed scene immutable.  
7. `bin/build.py`와 혼동하지 않는다.  
8. 상세는 `docs/seamless-short-video/` SSOT. 충돌 시 docs 우선.  
9. 게이트 실패 시 **같은 packet 재생성** 1순위. still/long dissolve로 완료 선언 금지.  
10. 조립: `join-score` / `--auto-head-trim`. 고정 `--head-trim 2`를 “2초 연속”이라 부르지 않음.  
11. 증상은 [13](../../docs/seamless-short-video/13-common-remediation-standard.md) C-xxx, 경계는 [15](../../docs/seamless-short-video/15-ten-second-boundary-common-playbook.md) C0–C26.

---

## 제작 루프 (한 프로젝트)

```text
1. init (project.yaml, scenes/, character/, story/)
2. Character Lock + Look Lock
3. scene01 start image 생성 → I2V 10s
4. frame0 게이트 → soft QA → handoff CLI
5. handoff_packet 작성 (말미 ~2초 동작 명시)
6. scene N+1: start=handoff only → 프롬프트는 packet만으로
   조인 창 continue-only → I2V → 게이트 → handoff
7. 전 씬 완료 후 join-score → concat --auto-head-trim
8. report/continuity_report.md + join_score JSON
```

---

## 실행 진입점

```bash
python3 bin/seamless-short.py init \
  --project-dir projects/<id> --scenes 3 --scene-seconds 10 --aspect 9:16

python3 bin/seamless-short.py handoff --project-dir projects/<id> --scene 1
python3 bin/seamless-short.py frame0-check --project-dir projects/<id> --scene 1
python3 bin/seamless-short.py verify --project-dir projects/<id>

python3 bin/seamless-short.py join-score --project-dir projects/<id> --scene 1
python3 bin/seamless-short.py concat \
  --project-dir projects/<id> \
  --auto-head-trim --head-trim-max 2 \
  --out output/<id>.mp4
```

상세 CLI: [09-workflow-and-cli.md](../../docs/seamless-short-video/09-workflow-and-cli.md)

---

## v1 스코프

| 포함 | 제외 |
| --- | --- |
| Character/Look Lock, N×10s I2V, Multi-Signal packet | Remotion 연동 |
| handoff / verify / concat / join-score / auto-head-trim | 립싱크·BGM·TTS 통합 |
| hard·soft QA, hard match-cut, silent visual | 브라우저 자동화, 다중 주연 |
| 조인 정본 문서·근사 운영 | video-tail 생성 API (미제공) |

기본: 30s=3씬 또는 60s=6씬, 9:16, 주연 1, 재시도 3.

---

## 문서 지도 (SSOT)

| 주제 | 문서 |
| --- | --- |
| 개요 | [01](../../docs/seamless-short-video/01-overview-and-principles.md) |
| **조인 정본** | **[16 §0](../../docs/seamless-short-video/16-tail-overlap-content-model.md)** |
| Multi-Signal | [14](../../docs/seamless-short-video/14-multi-signal-handoff-architecture.md) |
| C-xxx 처방 | [13](../../docs/seamless-short-video/13-common-remediation-standard.md) |
| 10초 경계 C0–C26 | [15](../../docs/seamless-short-video/15-ten-second-boundary-common-playbook.md) |
| CLI | [09](../../docs/seamless-short-video/09-workflow-and-cli.md) |
| 적용 체크리스트 | [12](../../docs/seamless-short-video/12-skill-adoption-checklist.md) |
| 개발 계획 | [dev-plan/implement_20260717_141429.md](../../dev-plan/implement_20260717_141429.md) |

---

## 검증 데모

| 데모 | 경로 |
| --- | --- |
| 조인 보정 (trim=0) | `projects/seamless-join-fix-momo-demo/` · `output/seamless-join-fix-momo-demo.mp4` |
| Multi-Signal 60s | `projects/seamless-popo-dandelion-60s/` · `output/seamless-popo-dandelion-60s.mp4` |
| 초기 파일럿 30s | `projects/seamless-lulu-star-walk-30s/` |
| head_trim 실험 | `projects/seamless-tori-kite-18s/` |

---

## 로컬 references (요약 — 충돌 시 docs 우선)

- [references/join-canon.md](references/join-canon.md)  
- [references/handoff-rules.md](references/handoff-rules.md)  
- [references/scene-prompt-template.md](references/scene-prompt-template.md)  
- [references/qa-checklist.md](references/qa-checklist.md)  
- [references/ten-second-boundary.md](references/ten-second-boundary.md)  
- [references/common-remediation.md](references/common-remediation.md)  
- [references/validated-example.md](references/validated-example.md)  
