# 11. 실패 유형별 처방 (Playbook)

**공통 수정 방향 SSOT:** 원인 클래스·전 영상 동일 처방은  
**[13-common-remediation-standard.md](13-common-remediation-standard.md)** 를 따른다.  
본 문서는 증상별 빠른 처방 메모이며, 클래스 ID(C-EXP, C-MOT …)와 충돌 시 **13번이 우선**이다.

## 11.1 캐릭터 얼굴이 변함

- 프롬프트를 늘리기보다 **동작 단순화**  
- 새 외형 묘사 추가 금지  
- Character Lock·입력 유지 명령 강화  
- 빠른 얼굴 회전·극단 표정 제거  
- Scene01 ref 재주입 (가능 시)  
- 연속 2회 실패 → 복잡도 하향  

## 11.2 의상·소품 변경

- Lock에 색 hex/짧은 고정 구 재삽입  
- “wardrobe change / new item” 표현 제거  
- 손 소품이 프레임 아웃되지 않게 구도  

## 11.3 배경이 바뀜 / 텔레포트

- 이전 배경 구조 문장 명시  
- “새로운 장소” 표현 삭제  
- 이동 과정이 같은 10초 안에 보이게 수정  
- 한 씬 공간 전환 1회 제한  

## 11.4 첫 프레임부터 화면이 바뀜 (구도)

```text
입력 이미지는 참고가 아니라 정확한 첫 프레임이다.
캐릭터·배경·자세·카메라 구도를 그대로 유지한 채 움직임만 시작한다.
```

frame0 MAE 게이트로 자동 탈락.

## 11.5 밝기·노출 점프 (컷에서)

→ [04-look-lock-and-exposure.md](04-look-lock-and-exposure.md)

1. frame0 ΔY 측정 → 재생성  
2. Look Lock + no relight  
3. 이전 씬 말미 bloom/광원 ramp 제거  
4. grade-match feather  
5. 0.2~0.4s dissolve (최후)  

## 11.6 동작이 끊김 / 걷기 부자연

→ [05-motion-and-walk-handoff.md](05-motion-and-walk-handoff.md) · **C-MOT** [13](13-common-remediation-standard.md)

1. 인계를 hold / plant-feet **또는** constant-cruise mid-stride  
2. 다음 씬 **조인 창(권장 0–8s)** 에 active_motion **복붙만**  
3. peak-swing walk handoff 제거  
4. overlap 0.5s + speed ramp (경미)  
5. flow 보간 선택  

## 11.6b 컷 직후 동작이 “바뀐” 느낌 (직립·올려다보기·엔딩 포즈)

→ 정본 위반: **이전 말미 ~2초 동작을 이어 받지 않음**  
→ [16 §0](16-tail-overlap-content-model.md) · **C-MOT-CHANGE** [13](13-common-remediation-standard.md)

1. 목표: 이전 2초 동작 연속 (불필요 연출 **추가 금지**)  
2. 근사: 조인 창 continue-only 재생성 (한 모터)  
3. 엔딩/감정 비트를 **연결 구간 밖으로**  
4. still/dissolve로 덮지 말 것  

## 11.6c “2초 중복인데도 티” / 고정 head_trim 후 악화

→ **head_trim ≠ 이전 2초 동작 연속** ([16 §0](16-tail-overlap-content-model.md))  
→ **C-JOIN-TRIM** [13](13-common-remediation-standard.md)

1. 정본은 “이전 말미 2초를 이어 그리기”; head_trim은 **다음 앞부분 폐기**  
2. `join-score` → **`concat --auto-head-trim`** (종종 best=0)  
3. 무조건 `--head-trim 2` 를 “2초 연속”이라고 부르지 말 것  


```bash
python3 bin/seamless-short.py join-score --project-dir projects/<id> --scene 1
python3 bin/seamless-short.py concat --project-dir projects/<id> --auto-head-trim --head-trim-max 2
```

## 11.7 마지막 프레임 불안정

- 마지막 1초 큰 동작 금지  
- 카메라 감속 후 settle  
- 0.5s hold 지시  
- 페이드아웃 금지  
- handoff lookback에서 blur 통과 프레임 선택  

## 11.8 손·사지 붕괴

- 손 클로즈·복잡 grasp 금지  
- 동작 속도 하향  
- hold 인계  
- 재생성 우선 (인페인트 최후)  

## 11.9 duration / 해상도 불일치

- 생성기 설정 10s·9:16 고정  
- concat 전 verify  
- 이질 해상도는 CLI concat 스케일·pad (품질 손실 가능 → 재생성 권장)  

## 11.10 드리프트 (후반 씬이 다른 캐릭터)

- Lock 문장 매 씬 동일  
- 홀수 씬 anchor hold  
- 복잡도 하향  
- 필요 시 중간 hard restart (스토리 허용 시)  

## 11.11 의사결정 트리 (컷 어색)

```text
컷에서 이상
  ├─ 밝기/색이 튀는가? ── yes → 11.5 노출 플레이북
  ├─ 캐릭터 얼굴/옷이 다른가? ── yes → 11.1 / 11.2
  ├─ 배경이 점프하는가? ── yes → 11.3
  ├─ 걸음/동작이 리셋되는가? ── yes → 11.6
  └─ 구도만 살짝 다른가? ── frame0 게이트 + 짧은 dissolve
```
