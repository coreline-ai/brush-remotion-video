# 02. 전체 설계 사양 (원안 + v0.2)

원 SeamlessShortVideoMaker 설계를 보존하고, 검토·파일럿에서 확정된 보강을 `※ v0.2`로 표시한다.

---

## 2.1 Last Frame Handoff

각 장면을 독립 이미지/영상으로 재생성하지 않는다.  
이전 영상의 마지막 정상 프레임을 다음 I2V 입력으로 사용한다.

```text
Scene 01 시작 이미지
        ↓
Scene 01 영상 생성
        ↓
Scene 01 마지막 정상 프레임 추출 (Last Usable Frame)
        ↓
Scene 02 시작 이미지로 사용  (※ sha256 동일 강제)
        ↓
Scene 02 영상 생성
        ↓
… 반복 …
```

연속성이 높아지는 항목: 얼굴·의상·소품·위치·자세·배경 구조·카메라·조명·직전 동작 흐름.

※ v0.2: “이미지 복사 성공” 다음에 **frame0 측정 게이트**를 둔다.  
「마지막 이미지로 제작했다」≠「다음 영상 0프레임이 그 이미지다」.

---

## 2.2 Last Usable Frame

원칙: 영상의 **정확한 마지막 프레임**.

다만 다음에 해당하면 마지막 **0.3~0.8초** 구간에서 가장 뒤쪽의 정상 프레임을 고른다.

- 페이드아웃  
- 심한 모션 블러  
- 얼굴·손 변형  
- 화면 깨짐  
- 캐릭터가 프레임 아웃  
- 생성 모델 말미 왜곡  

CLI (`handoff`): lookback 샘플 + Laplacian blur score로 자동 선택.  
모두 기준 미달이면 sharpest를 쓰고 warning 기록.

---

## 2.3 10초 장면 내부 구조

| 구간 | 역할 |
| --- | --- |
| 0~1s (권장 0~2s) | 이전 움직임·자세 이어받기 (**새 사건 금지**) |
| 1~7s | 현재 핵심 행동 (한 장면 = 한 주요 공간 전환 이하) |
| 7~9s | 다음 준비 · 노출·카메라 안정 |
| 9~10s | 인계용 안정 자세 (마지막 씬은 결말 hold) |

### 나쁜 마지막 상태

눈 감음, 얼굴 가림, 빠른 회전, 카메라 흔들림, 프레임 아웃, 전체 블러, 페이드아웃,  
**보행 peak-swing(한 발 공중·무게 이동 피크)**, **노출 급변·강한 bloom ramp**.

### 좋은 마지막 상태

- **hold** 0.3~0.5s (최고 성공률)  
- **양발 착지 / plant-feet** 후 다음 한 보 직전  
- 문 열기 직전, 물체 응시, 손 뻗기 시작 직후 안정  
- 카메라 안정, 얼굴 선명, 다음 방향 명확  

※ v0.2: I2V 보행에서 “걸음 중간 자세 handoff”는 위험. walk 전용 규칙은 [05-motion-and-walk-handoff.md](05-motion-and-walk-handoff.md).

---

## 2.4 Overlap

### 동작 Overlap (필수)

이전 장면 마지막 1~2초에서 시작된 동작을 다음 장면 첫 1~2초 동안 **동일 방향·속도·발 위상**으로 이어 기술한다.  
실제 파일 길이를 줄이지 않으면서 동작 연속성을 만든다. **기본 Overlap 방식.**

### 편집 타임라인 Overlap (선택)

타임라인에서 1초씩 겹치면 6×10s → ~55s.  
정확히 60s(또는 30s)가 필요하면:

- last frame match cut  
- 동작 의미만 1~2초 이어지게 설계  
- 필요 시 0.2~0.5s Cross Dissolve만  
- ※ 밝기 점프 hard-fail 시에만 0.25s dissolve 허용  

### 모드

| 모드 | 내용 |
| --- | --- |
| Exact duration | 중첩 최소화, Match Cut, 길이 유지 |
| Smooth transition | 0.2~0.5s dissolve (구 문서 0.5~1s는 과도 — v0.2에서 단축) |

concat 시 중간 씬 **마지막 1프레임 drop** 옵션으로 start 중복 팝 완화 (`--drop-last-frame`).

---

## 2.5 입력

### 필수

| 입력 | 설명 |
| --- | --- |
| 캐릭터 | 이름·생김새 — **참조 이미지 강력 권장** (v0.2: 사실상 필수에 가깝게) |
| 이야기 콘셉트 | 사건 |
| 영상 스타일 | 동화 / 애니 / 실사 / 3D 등 |

### 선택 (기본값)

| 입력 | 기본 |
| --- | --- |
| 전체 길이 | 30 또는 60 |
| 장면 수 | 3 또는 6 |
| 장면 길이 | 10 |
| 화면 비율 | 9:16 |
| 대사 | 없음 |
| 카메라 | 부드러운 시네마틱 |
| 전환 | last_frame_match_cut |
| 분위기 | 밝고 따뜻한 동화 |
| 편집 도구 가이드 | CapCut + FFmpeg draft |

※ v0.2 추가 입력: `generator` capability, `look_lock`, `scene_end_type`.

---

## 2.6 장면 자동 분할 (60초=6 / 30초=3)

### 60초 6역할

| 장면 | 역할 |
| --- | --- |
| 01 | 소개 |
| 02 | 목표 발견 |
| 03 | 행동·첫 변화 |
| 04 | 긴장 |
| 05 | 절정 |
| 06 | 결말 |

### 30초 3역할 (파일럿)

| 장면 | 역할 |
| --- | --- |
| 01 | 소개·발견 |
| 02 | 추적·이동 |
| 03 | 도착·결말 |

잘못된 분할: 숲 → 갑자기 성 → 갑자기 바다 (이동 과정 없음).  
올바른 분할: 발견 → 통과 → 도착 (이동이 영상 안에 보임).  
※ 한 장면당 주요 공간 전환 **최대 1**.

---

## 2.7 실행 단계

1. 프로젝트 초기화 (제목, Character Lock, Look Lock, 비율, 전환, 장면 수)  
2. 스토리 설계 (씬별 start/action/end/link_motion/camera/emotion + **scene_end_type**)  
3. Scene 01 시작 이미지만 생성  
4. Scene k I2V 생성  
5. **frame0 vs start 게이트** (v0.2) — 실패 시 재생성  
6. Last Usable Frame 추출 → `handoff_frame.png`  
7. Continuity QA (hard/soft)  
8. 다음 start 등록 + observed_end_state 갱신 후 다음 프롬프트 확정  
9. 반복 → concat → timeline / continuity report  

상태 머신:

```text
PROJECT_INITIALIZED
  → CHARACTER_LOCKED (+ LOOK_LOCKED)
  → STORY_PLANNED
  → SCENE_01_IMAGE
  → SCENE_GENERATED
  → FRAME0_QA          ※ v0.2
  → HANDOFF_FRAME_EXTRACTED
  → CONTINUITY_QA
       ├── fail → SCENE_RETRY (max 3)
       └── pass → NEXT_SCENE_READY → …
  → ALL_SCENES_COMPLETED
  → EDIT_PLAN / CONCAT
  → FINAL_QA
```

---

## 2.8 반자동화 범위

### 자동 가능

캐릭터 정규화, Character/Look Lock, 스토리·분할, 프롬프트, 상태 삽입,  
프레임 추출, 폴더·파일명, 타임라인 초안, QA 체크리스트, FFmpeg concat,  
※ frame0 비교·grade-match (구현 대상)

### 사용자/외부

I2V 업로드·프롬프트 입력·결과 선택·다운로드·재시도 판단·soft QA

watch-folder 패턴:

```text
영상 저장 감지 → frame0 QA → handoff 추출 → 다음 start 등록 → 다음 프롬프트 출력 → QA 항목 표시
```

---

## 2.9 스킬 출력물

1. Character Lock / Look Lock  
2. 전체 이야기  
3. N개 장면 구성표  
4. Scene 01 이미지 프롬프트  
5. 장면별 영상 프롬프트 (순차 확정)  
6. planned / observed end_state  
7. Handoff 지침  
8. QA 체크리스트·리포트  
9. 실패 시 재생성 프롬프트  
10. 편집 타임라인  
11. (선택) 내레이션·SRT 초안  
12. 폴더·파일명 규칙  
13. final_video.mp4 (concat)

---

## 2.10 최종 정의

이 시스템은 다음 세 가지(+ v0.2 한 가지)를 장면마다 연쇄한다.

```text
1. 이전 영상의 마지막 실제 이미지 (및 frame0 정합)
2. 이전 장면 종료 시점의 캐릭터·배경·카메라·조명 상태
3. 이전 장면에서 시작된 동작의 진행 방향
4. ※ 노출/룩 불변 (Look Lock) 과 인계 포즈 타입
```
