# 14. Multi-Signal Handoff Architecture (방향 고정)

**상태:** 운영·스킬 설계의 **정본 방향** (v0.4)  
**배경:** lulu-30s에서 밝기/멈춤을 **후처리(assemble)로만** 반복 보정하다  
증상 하나에 과집중됨. 근본 방향은 생성 계약 자체를 바꾸는 것이다.

---

## 1. 문제 진단 (프로세스)

| 잘못된 접근 | 결과 |
| --- | --- |
| meanY gain / tone-match / still inject / crossfade를 컷마다 실험 | 밝기↑ ↔ 멈춤↑ 트레이드오프 루프 |
| “파일이 handoff다” = “영상이 이어진다”로 착각 | I2V frame0 재합성 잔차 방치 |
| 후처리로 픽셀만 맞춤 | 동작 정보 손실 → 끊김 |

**올바른 접근:**  
다음 씬을 만들 때 **마지막 이미지를 0프레임으로 쓰고**,  
그와 **동시에** 이전 프레임(구간)의 **여러 신호**를 넘긴다.

```text
후처리로 끊김을 가리는 것  ≠  인계 계약으로 연속을 만드는 것
```

---

## 2. 핵심 원칙 (한 줄)

> **Frame0 = 이전 Last Usable Frame (시각 앵커)**  
> **+ State / Motion / Look / Camera 신호 (의미 앵커)**  
> → 그 위에서만 I2V가 “이어서” 움직인다.

이미지만 넘기면 모델이  Tonemap·포즈·바닥을 다시 그린다.  
프롬프트 상태만 넘기면 픽셀 앵커가 없다. **둘 다 필요**하다.

---

## 3. 인계 신호 스택 (Multi-Signal)

다음 씬 생성 입력은 **단일 PNG가 아니라 패킷**이다.

| # | 신호 | 내용 | 전달 수단 | 실패 시 증상 |
| --- | --- | --- | --- | --- |
| **S0 Visual Anchor** | Last Usable Frame 이미지 | `handoff_frame.png` → `start_image` | 파일 (sha 동일) | 구도 점프 |
| **S1 Frame0 Lock** | “이 이미지가 정확한 0프레임” | 프롬프트 블록1 + (가능 시) API lock | 생성 계약 | 밝기/하단 재합성 |
| **S2 Look Lock** | 노출·화이트밸런스·광원 | `look_lock.md` 동일 삽입 | 텍스트 | C-EXP / C-EXP-TONE |
| **S3 Character Lock** | 얼굴·의상·소품 | `character_lock.md` | 텍스트 | C-CHR |
| **S4 Pose/State** | 위치·시선·손발·표정 | `observed_end_state.yaml` | YAML→프롬프트 블록3 | 포즈 리셋 |
| **S5 Motion Vector** | 진행 중 동작·속도·방향·발 위상 | `active_motion` + 0–2s 문장 **복붙** | 텍스트 | C-MOT 끊김 |
| **S6 Camera Continuity** | 앵글·이동 방향·속도 | state.camera + 동일 문장 | 텍스트 | C-CAM |
| **S7 Temporal Context (권장)** | 직전 0.3~1.0s 의미 요약 또는 키프레임 2–3장 | `tail_context.md` / optional refs | 텍스트±이미지 | “갑자기 다른 샷” |
| **S8 Negative Continuity** | relight / redesign / restart walk / teleport 금지 | 블록6 | 텍스트 | 재발 |

### 패킷 스키마 (개념)

```yaml
handoff_packet:
  from_scene: scene_01
  to_scene: scene_02
  visual_anchor: scenes/scene_01/handoff_frame.png
  sha256: ...
  observed_end_state: scenes/scene_01/observed_end_state.yaml
  look_lock_ref: character/look_lock.md
  character_lock_ref: character/character_lock.md
  motion:
    active_motion: "slowly stepping right toward firefly, same pace"
    leading_foot: right
    speed: slow
    do_not_restart: true
  camera:
    shot: medium-full
    motion: gentle push-in same direction
  frame0_contract:
    exact_first_frame: true
    no_relight: true
    no_recompose: true
  tail_context:
    last_seconds: 0.5
    summary: "Lulu finished standing and began first right step"
  generator:
    supports_exact_start_frame: partial   # truth-telling
```

---

## 4. 생성 타임라인 계약 (10초 씬)

| 구간 | 역할 | 신호 사용 |
| --- | --- | --- |
| **frame 0** | = visual_anchor (목표: 픽셀 정합) | S0+S1+S2 |
| **0–2s** | **새 스토리 금지** — active_motion만 연속 | S5+S6 복붙 |
| **2–7s** | 이번 씬 핵심 1행동 | S3+S4 유지 |
| **7–9s** | 노출·카메라 안정, 인계 준비 | S2 |
| **9–10s** | scene_end_type (hold/plant-feet 권장) | 다음 패킷용 S4/S5 기록 |

> “멈춤 연출(hold)”은 **인계 포즈 타입**으로만 쓰고,  
> **편집에서 still 프레임을 여러 장 박아 넣는 것**과 혼동하지 않는다.

---

## 5. Frame0 정합 전략 (계층)

I2V가 partial lock일 때의 **우선순위** (후처리 만능 금지):

| 순위 | 수단 | 설명 |
| --- | --- | --- |
| 1 | **생성 계약** | exact first frame + no relight + Look Lock + 단순 첫 동작 |
| 2 | **후보 게이트** | frame0 vs start: meanY, centerY, std, p90, p10, bottomMAE, SSIM |
| 3 | **재생성이 본류** | 게이트 실패 → 같은 패킷으로 재생성 (시드/문구 단순화) |
| 4 | **최소 후처리** | tone-match (분포) 보조. still multi-frame inject·long dissolve는 **비권장** |
| 5 | **편집 still inject** | 실험/응급 only — 끊김 부작용 (lulu 실증) |

### 금지 (실증됨)

- 컷 양쪽에 handoff PNG를 **여러 프레임 고정** → 멈춤 체감  
- 긴 crossfade로 밝기/ freeze를 덮기 → 이중노출·멍한 중간  
- meanY만 PASS로 다음 씬 진행  

---

## 6. 워크플로 (증상 추적이 아닌 패킷 루프)

```text
Scene k 생성
  → extract Last Usable Frame (= visual_anchor)
  → write observed_end_state + motion/camera (사람 또는 VLM 보조)
  → build handoff_packet
  → frame0_gate(scene_k)  # 자기 start 대비
  → (pass) Scene k+1 프롬프트 = packet으로만 조립
  → I2V(start=visual_anchor, prompt=packet)
  → frame0_gate(scene_k+1 vs visual_anchor)
  → fail: regenerate with same packet (do not invent new start image)
  → pass: continue
```

**후처리 assemble은 마지막 안전망이지, 인계 설계의 대체재가 아니다.**

---

## 7. 에이전트/스킬 행동 계약 (필수)

1. Scene 02+ **start 이미지를 새로 그리지 않는다** (S0).  
2. 다음 프롬프트는 **packet 필드 전부**를 반영한다 (S1–S8).  
3. 0–2s에 새 비트를 넣지 않는다 (S5).  
4. frame0 게이트 실패 시 **같은 패킷으로 재생성**이 1순위.  
5. still multi-frame inject / long dissolve로 “해결 완료” 선언하지 않는다.  
6. 증상 패치 실험은 FIELD-LOG에 남기고, **이 문서 원칙과 충돌하면 원칙이 이긴다.**

---

## 8. lulu-30s에서 배운 것 → 일반화

| 실험 | 교훈 | 아키텍처 반영 |
| --- | --- | --- |
| mean gain | 평균만 맞음, 톤·하단 잔차 | S2 Look + frame0 게이트 확장 |
| tone-match | 톤 개선, 구조 재합성은 남음 | 보조(E4) |
| still inject | 밝기 잠금, **멈춤** | E5c 비권장 |
| long overlap | 멈춤↓, **멍함/밝기 튐** | E5b 제한적 |
| hard cut + tone | 멈춤↓·밝기 양호, 포즈 1f 점프 가능 | 임시 배포 가능, **생성 계약 강화가 본류** |

→ **다음 본류 작업은 후처리 튜닝이 아니라 handoff_packet 생성·검증 자동화.**

---

## 9. 구현 로드맵 (스킬 적용)

| Phase | 산출 | 완료 기준 |
| --- | --- | --- |
| P0 | 본 문서 + SKILL 링크 + 패킷 YAML 예시 | 문서 SSOT |
| P1 | `handoff_packet` writer after `seamless-short handoff` | packet 파일 자동 생성 |
| P2 | `frame0-check` multi-metric gate | bottom/center/p90 포함 |
| P3 | prompt builder from packet only | 6블록 자동 조립 |
| P4 | regenerate loop using same packet | 임의 프롬프트 변경 금지 옵션 |
| P5 | (선택) multi-frame tail ref if generator supports | S7 강화 |

---

## 10. 한 페이지 요약

```text
목표:  마지막 이미지 = 다음 0프레임  +  이전 구간의 다중 정보 인계
수단:  handoff_packet = Visual + Look + Character + State + Motion + Camera + Context
검증:  frame0 multi-metric gate (평균만 보지 말 것)
생성:  0–2s motion 연속, 재생성 우선
후처리: 최소 보조. still/long-dissolve로 인계를 대체하지 말 것.
```
