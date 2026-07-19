# 06. Character Lock · Look Lock · 장면 상태

## 6.1 Character Lock

첫 단계에서 변경 금지 항목을 고정한다. **모든 장면 프롬프트에 동일 문구**를 넣는다.  
장면마다 캐릭터를 새롭게 묘사하지 않는다.

### 예시 구조 (`character/character_lock.md`)

```markdown
# Character Lock — {name}

- name:
- species/type:
- face: (구조, 눈 색, 특징)
- body_ratio:
- outfit: (색·디자인 고정)
- fixed_prop:
- style: (3D fairy-tale / ink / live-action …)
- personality: (연출 참고)

## 변경 금지
얼굴 구조, 눈·피부·털 색, 의상, 신발, 비율, 고정 소품, 스타일, 기본 나이·체형

## 변경 가능
표정, 손발 동작, 시선, 위치, 감정, 환경 상호작용
```

### v1 제약

- 주연 **1명**  
- 조연 등장 시 얼굴 클로즈 최소화, lock에 “extra characters forbidden”  

### 참조 이미지

`character/character_reference.png` 권장(사실상 필수).  
Scene 01 시작 이미지와 동일 계열. 드리프트 시 Scene01 ref를 보조 조건으로 재주입.

---

## 6.2 Look Lock

[04-look-lock-and-exposure.md](04-look-lock-and-exposure.md) 전문.  
요약: 시간대·키/필 라이트·노출·화이트밸런스·bloom 금지 목록을 Character와 분리 고정.

---

## 6.3 장면 상태 인계

이미지만으로 부족. 종료 시 상태를 기록하고 다음 시작 프롬프트에 넣는다.

### planned vs observed

| | planned_end_state | observed_end_state |
| --- | --- | --- |
| 작성 시점 | 스토리 설계 | handoff 후 |
| 작성 주체 | 사람/LLM 계획 | 사람 또는 VLM 보조 + 사람 확인 |
| 다음 프롬프트 | 초안용 | **우선 사용** |

### 스키마 (권장 필드)

```yaml
scene_id: scene_02
scene_end_type: plant-feet   # hold | plant-feet | gesture | walk
character_position: 화면 중앙보다 약간 오른쪽
facing_direction: 오른쪽
gaze_direction: 언덕 위
body_pose: 오른발 착지, 몸 약간 전경
left_hand: 가방끈 / 랜턴
right_hand: ...
expression: 호기심
camera: 미디엄 풀샷, 허리 높이
camera_motion: 천천히 따라감 (속도 일정)
lighting: 달빛 좌상단, 랜턴 필
exposure_notes: dim night, no bloom ramp
background: 돌길과 언덕 입구
active_motion: 오르기 직전 정지 / 또는 동일 속도 한 걸음 연속
```

### 다음 씬 시작 문장 패턴

```text
동일한 캐릭터가 동일한 위치·자세·노출에서 시작한다.
(active_motion을 그대로 반복)
카메라는 이전과 동일한 방향·속도로 계속한다.
```

---

## 6.4 드리프트 완화

6단(60s) 연쇄에서 후반 얼굴·비율 드리프트 누적.

| 기법 | 내용 |
| --- | --- |
| Lock 재삽입 | 매 씬 동일 Character+Look 문단 |
| Anchor | 홀수 씬 hold/정면 안정 서브골 |
| Ref 재주입 | multi-image 지원 시 Scene01 ref |
| 복잡도 상한 | 한 씬 한 행동 |
| Hard restart | 연속 2회 face soft-fail 시 해당 씬부터 start 재검토 |

---

## 6.5 Scene 01 시작 이미지 조건

- 전신 또는 필요 신체 확보  
- 얼굴·의상 명확  
- 첫 동작 시작에 좋은 자세  
- 배경 공간 여유  
- 이후 카메라와 호환  
- Look Lock 노출과 일치  
- 별도 **이미지 QA** 후 I2V (영상 QA와 분리)
