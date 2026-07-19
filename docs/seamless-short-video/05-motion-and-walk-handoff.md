# 05. 동작·보행 인계 (Motion Continuity)

## 5.1 문제 정의

경계(예: 20초)에서 캐릭터가 **걷는데 미끄러지거나, 순간 멈췄다 다시 걷거나, 발이 바뀌는** 느낌.

파일럿 20s 경계: 밝기 ΔY ≈ −1 (문제 없음) → **순수 모션 불연속**.

## 5.2 메커니즘

```text
S_n  end:  foot phase φ, velocity v, torso lean θ, camera move c
S_n+1 start: I2V가 “걷기”를 새로 샘플 → φ', v', θ', c' 불일치
```

사람은 보행 주기 10~20% 위상 오차만으로도 부자연스러움을 감지한다.

## 5.3 scene_end_type

각 씬 종료 시 타입을 명시하고 인계 전략을 고른다.

| 타입 | 정의 | 성공률 | 용도 |
| --- | --- | --- | --- |
| **hold** | 0.3~0.8s 준정지, 얼굴 선명 | 최고 | 감정 비트, 결말, **권장 기본 인계** |
| **plant-feet** | 양발·무게 이동 완료, 다음 한 보 직전 | 높음 | 이동 스토리 |
| **gesture** | 발 고정, 손·고개만 | 높음 | 발견·대화 느낌 |
| **walk** | 보행 중 인계 | 조건부 | **peak 금지**; **constant-cruise + 조인 창 continue-only** 이면 허용 (v0.5) |
| **turn** | 빠른 회전 | 최저 | v1 금지에 가깝게 |

### walk handoff 금지(권장) 위상

- peak swing (한 발 공중)  
- 최대 bounce  
- 방향 전환 중  
- 가속/감속 피크  
- 조인 직후 **포즈 스타일 변경**(직립·올려다보기·엔딩) — **C-MOT-CHANGE**

### walk 시 허용에 가까운 위상

- 착지 직후  
- double support에 가까운 짧은 보폭  
- **constant cruise 중 mid-stride** + 다음 씬 0–8s 동일 걷기만 (실측: momo-demo)

### 공통 적용 정본 (v0.5.1)

```text
정본: 이전 씬 마지막 ~2초 동작을 다음 씬이 그대로 이어 받는다
      → 경계에 불필요 연출을 넣을 필요가 없고 자연 연결
      → [16 §0](16-tail-overlap-content-model.md)

근사(현재 I2V): 말미 동작 packet + 조인 창 continue-only
                + auto-head-trim (head_trim=2 ≠ 이전 2초 연속)

엔딩 비트: 연결 구간이 지난 뒤 / 마지막 씬 말미
```

상세: [16 §0](16-tail-overlap-content-model.md) · [13](13-common-remediation-standard.md) · [15](15-ten-second-boundary-common-playbook.md) C0·C21–C26.
- 사실상 plant-feet에 수렴  

## 5.4 프롬프트 규칙

### 동작 Overlap 문장 복붙

이전 씬 마지막 active_motion 문장을 다음 씬 0~2s에 **동일 문구**로 넣는다.

```text
0–2.0s: Continues the exact same slow step already in progress —
same leading foot, same stride length, same speed, no pause,
no restart of the walk cycle. No new story beats.
2.0s–: (비로소 새 행동)
```

### 한 씬 = 한 모터 스킬

| 나쁜 예 | 좋은 예 |
| --- | --- |
| 0s부터 걷기+도착+고개+랜턴 | 0–2s 걷기만 → 이후 도착·고개 |
| 경계에서 장거리 보행 지속 | 경계 전 hold, 다음 씬에서 짧은 이동 |

### 카메라

경계 전후 2초: follow 속도·push-in on/off를 바꾸지 않음.  
카메라 문장 양 씬 동일 복사.

## 5.5 스토리 리라이트 패턴 (30s 권장)

걷기를 **경계에 걸치지 않게** 씬 안쪽으로만 배치.

```text
S1: 발견 → 한 발 → hold (시선 목표)
S2: hold에서 출발 → 길 걷기 → 언덕 앞 plant-feet hold
S3: hold에서 2~3걸음 또는 이미 정상 근처 → 올려다보며 hold
```

## 5.6 편집 보정 (생성 후)

| 기법 | 파라미터 | 효과 |
| --- | --- | --- |
| Timeline overlap | 0.4~0.8s | 보행 리셋 완화 (길이 약간 감소) |
| Speed ramp | 경계 전후 0.5s, 100%→85%→100% | 운동 충격 완화 |
| Optical flow (RIFE 등) | 컷 전후 4~6f | 선택; 얼굴 붕괴 시 폐기 |
| Morph/match cut | 유사 실루엣 | hold 인계와 궁합 |

Exact duration이 필수면 overlap 대신 **hold 인계 재생성**이 우선.

## 5.7 Soft gate (사람)

- 첫 1초가 이전 종료 자세에서 자연스러운가  
- 발 위상이 갑자기 바뀌지 않는가  
- 순간 정지 후 재출발이 없는가  
- 이동 방향이 반대로 튀지 않는가  

## 5.8 우선순위

| 순위 | 조치 |
| --- | --- |
| 1 | 인계를 hold / plant-feet로 재설계·재생성 |
| 2 | 다음 씬 0–2s 새 연출 금지 + 문장 복붙 |
| 3 | 결말 씬에서 장거리 보행 제거 |
| 4 | overlap + speed ramp |
| 5 | flow 보간 (선택) |
