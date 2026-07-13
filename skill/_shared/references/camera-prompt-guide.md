# Camera Prompt Interpreter 가이드

이 문서는 사용자의 일상 표현을 모델 중립적인 전문 카메라 프롬프트로 바꾸는 공통 계약이다.
37개 기법의 값은 [카탈로그](camera-prompt-catalog.json), 구조는
[JSON Schema](camera-prompt-catalog.schema.json)를 단일 진실로 사용한다.

## 목차

1. [역할과 경계](#역할과-경계)
2. [해석 순서](#해석-순서)
3. [기법 선택](#기법-선택)
4. [프롬프트 조립](#프롬프트-조립)
5. [호환성 분기](#호환성-분기)
6. [모호성과 충돌](#모호성과-충돌)
7. [Negative Prompt](#negative-prompt)
8. [품질 Rubric](#품질-rubric)

## 역할과 경계

- 입력: 사용자의 자연어 장면 설명과 선택적 타깃
- 출력: canonical 해석, 슬롯, 한/영 전문 프롬프트, negative prompt, 타깃 호환성
- 목적: 촬영 용어를 모르는 사용자의 의도를 전문 용어로 보존해서 후속 제작 단계에 전달
- 비목적: 특정 AI 영상 모델 API 호출, 실제 3D 카메라 이동 구현, 새 render props 생성
- `cameraPrompt`는 **연출 브리프의 선택적 블록**이다. 현재 `project.yaml`에 `camera:` 또는
  `cameraMotion:` 필드로 복사하지 않는다.
- 카메라 의도가 없으면 기존 director 출력에 Camera Prompt Pack을 만들지 않는다.

## 해석 순서

문장을 아래 순서로 읽고, 사용자가 명시한 값은 기본값보다 항상 우선한다.

1. **피사체**: 무엇을 화면의 기준점으로 유지하는가
2. **움직임 주체**: 렌즈 화각, 카메라 위치, 피사체, 시간 중 무엇이 변하는가
3. **방향**: 좌/우, 상/하, 전진/후진, 위에서 본 회전 방향
4. **속도·리듬**: slow, fast, instant, subject-matched, accelerating
5. **거리·구도**: 시작 구도, 종료 구도, 거리 유지 여부
6. **초점·잠금**: focal point와 subject lock
7. **안정화·블러**: locked, smooth, controlled-handheld, directional blur
8. **연속성**: screen direction, 전환축, 시작/종료 구도의 연결
9. **타깃**: `remotionStill`, `aiVideo`, `imageGeneration`, `sceneTransition`
10. **제약**: 선화, 얼굴, 제품 형태, 로고, 텍스트 보존

해석 결과의 최소 구조는 다음과 같다.

```yaml
cameraPrompt:
  userRequest: "인물 뒤를 천천히 따라가 줘"
  interpretation:
    canonicalId: follow-over-shoulder
    canonicalNo: 19
    primaryTechnique: follow-over-shoulder
    secondaryTechnique: null
    emotionalIntent: 몰입
    confidence: 0.94
    needsClarification: false
  parameters:
    subject: main-character
    direction: forward
    speed: subject-matched
    startComposition: over-the-shoulder-medium
    endComposition: over-the-shoulder-medium
    subjectLock: true
    stabilization: smooth
  promptKo: "..."
  promptEn: "..."
  negativePrompt: ["..."]
  compatibility: {remotionStill: external-required, aiVideo: supported, imageGeneration: composition-only, sceneTransition: not-applicable}
```

## 기법 선택

- primary technique은 정확히 1개를 원칙으로 한다.
- 보조 동작이 명확하고 충돌하지 않을 때만 secondary technique을 최대 1개 사용한다.
- 같은 의미의 legacy 37~45번을 별도 기법으로 세지 않는다.
- 37→28, 38→29, 39→30, 40→31, 41→32, 42→33, 43→34, 44→35, 45→36으로 정규화한다.
- 사용자가 기법 번호를 직접 지정해도 방향·피사체·속도 등 필수 슬롯은 문맥에서 추출한다.
- `tilt-shift`는 렌즈 효과, `timelapse`는 시간 효과, `first-person-pov`는 시점 방식이다.
  모두를 카메라 위치 이동으로 잘못 표현하지 않는다.

### Zoom과 이동 구분

| 표현 | 움직이는 것 | 전문 해석 |
| --- | --- | --- |
| 확대해 줘 | 렌즈 화각 | zoom in |
| 주변을 보여 줘 | 렌즈 화각 또는 카메라 후진 | 문맥에 따라 zoom out / pull-back |
| 다가가 줘 | 카메라 위치 | push-in / tracking |
| 스치며 들어가 줘 | 카메라 위치와 전경 상대운동 | fast push-in pass-by |

## 프롬프트 조립

한글과 영어는 동일한 슬롯을 동일한 순서로 사용한다.

1. shot/technique
2. subject와 focal point
3. direction과 speed
4. camera-to-subject distance 또는 lens behavior
5. start composition → end composition
6. subject lock와 stabilization
7. motion blur와 transition continuity
8. preservation/negative constraints

### 한국어 공식

`[기법]으로 [피사체/초점]을 유지하며 [기준 방향]으로 [속도] 이동한다. [시작 구도]에서
[종료 구도]로 전환하고 [거리/안정화/연속성]을 유지한다.`

### English formula

`Use a [technique], keeping [subject/focal point] locked while moving [direction] at [speed].
Transition from [start composition] to [end composition], preserving [distance/stabilization/continuity].`

한/영 결과를 따로 창작하지 않는다. 방향, 속도, 시작/종료 구도, 피사체 잠금이 서로 다르면 실패다.

## 호환성 분기

| 값 | 의미 | 출력 행동 |
| --- | --- | --- |
| `supported` | 해당 타깃이 의도를 직접 표현 가능 | 전문 prompt를 그대로 제공 |
| `simulated` | 2D 변환·크롭·블러 등으로 근사 | 근사임을 한 줄로 명시 |
| `composition-only` | 단일 이미지에서 시작/종료 구도만 설계 가능 | 움직임을 약속하지 않고 구도 지시만 제공 |
| `external-required` | 현재 정지 이미지/Remotion만으로 진짜 이동 불가 | 외부 영상 생성 또는 촬영 단계가 필요하다고 표시 |
| `not-applicable` | 타깃의 목적과 맞지 않음 | 실행 지시를 생성하지 않음 |

- `remotionStill`: 2D pan/tilt/zoom으로 가능한지와 실제 공간 이동이 필요한지를 구분한다.
- `aiVideo`: 모델 중립 문장을 사용하고 특정 서비스의 비공식 토큰을 넣지 않는다.
- `imageGeneration`: 움직임 대신 시작 또는 종료 구도와 시점만 설명한다.
- `sceneTransition`: 휩팬·인피니트 줌·지구 줌·오브젝트 통과처럼 두 씬 연속성이 핵심일 때 사용한다.
- `external-required`를 `project.yaml`의 실행 가능한 필드처럼 표시하지 않는다.

## 모호성과 충돌

`needsClarification: true` 조건은 다음 중 하나다.

- 표현만으로 움직임 주체나 방향을 결정할 수 없음
- 두 canonical 기법이 동일 확률로 남음
- 선택된 기법끼리 `conflictsWith` 관계임
- 필수 슬롯 누락이 결과의 의미를 크게 바꿈
- 현재 타깃이 `external-required`인데 사용자가 실제 렌더 완료를 기대함

확인 질문은 결과를 크게 바꾸는 항목만 최대 2개다.

| 입력 | 확인할 핵심 |
| --- | --- |
| 당겨 줘 | 렌즈 확대인가, 카메라 전진인가 |
| 돌아 줘 | 제한된 arc인가, 완전 orbit인가; 방향은 무엇인가 |
| 흔들리게 | 제어된 handheld인가, 효과성 shake인가 |
| 웅장하게 멀어져 | 지상 zoom-out인가, aerial pull-back인가 |
| 고정인데 흔들리게 | static과 handheld 중 우선 의도 |
| 줌 인하면서 멀어져 | 의도된 dolly-zoom인지 모순인지 |

명확한 문장에는 불필요하게 되묻지 않는다. 방향 없는 orbit을 임의 선택해야 한다면
`위에서 내려다본 기준 시계 방향`을 안전 기본값으로 밝히고, 방향이 중요하면 질문한다.

## Negative Prompt

항상 기법별 `negativeRules`와 공통 `common`을 합친다. 입력 자산에 따라 아래 그룹을 추가한다.

- 펜/펜브러시: `lineArt` — 선 굵어짐, 샤프니스 저하, 선 디테일 삭제 금지
- 인물: `identity` — 얼굴 정체성, 신체 비율, 손발 구조 보존
- 제품: `product` — 외형, 재질, 로고 위치, 라벨 보존
- 텍스트 포함 이미지: `text` — 철자, 방향, 타이포그래피 보존
- 전환: 나가는 방향과 들어오는 방향의 축·빛·가림 연속성 보존

금지 문장은 긍정 프롬프트와 모순되지 않아야 하며, `no camera movement`처럼 선택 기법 자체를
무효화하는 문장을 넣지 않는다.

## 품질 Rubric

대표 결과는 각 축 5점 만점 중 4점 이상이어야 한다.

| 축 | 5점 기준 |
| --- | --- |
| 전문성 | canonical 용어와 카메라/렌즈/시점 차이를 정확히 사용 |
| 충실성 | 사용자가 지정한 피사체·방향·속도·구도를 덮어쓰지 않음 |
| 일관성 | 한/영 prompt와 구조화 슬롯이 동일한 의미 |
| 간결성 | primary 1개, secondary 최대 1개로 과잉 기법 나열 없음 |
| 실행 가능성 | 필수 슬롯이 채워지고 타깃 호환성·한계가 명시됨 |
| 안전 제약 | identity/shape/text/line-art 보존 조건이 입력에 맞게 포함됨 |

한 축이라도 3점 이하면 prompt를 다시 조립한다. `external-required`를 숨겼다면 실행 가능성은
최대 2점, 사용자 방향을 반대로 바꿨다면 충실성은 1점으로 판정한다.
