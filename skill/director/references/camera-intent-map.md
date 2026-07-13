# Camera Intent Map — 일상 언어를 전문 카메라 의도로 변환

37개 기법의 정확한 ID·번호·호환성은
[공통 카탈로그](../../_shared/references/camera-prompt-catalog.json)를 사용한다. 이 문서는
일상 표현의 의미를 찾는 탐색 지도이며 별도 기법 목록이 아니다.

## 빠른 매핑

| 사용자 표현 | 우선 후보 | 구분 기준 |
| --- | --- | --- |
| 가만히 보여 줘 | `static-shot` | 구도·화각 모두 고정 |
| 오른쪽/왼쪽을 훑어 줘 | `pan-right` / `pan-left` | 카메라 위치는 고정 |
| 위를 올려다봐 / 아래를 내려다봐 | `tilt-up` / `tilt-down` | 수직 회전, 높이 이동 아님 |
| 천천히 당겨 줘 | `slow-zoom-in` 또는 전진 계열 | 렌즈 확대인지 카메라 접근인지 확인 |
| 확 멀어져 전체를 보여 줘 | `fast-zoom-out` / `drone-pull-back` | 지상 렌즈인지 공중 후진인지 확인 |
| 물체를 스치며 들어가 줘 | `push-fast-passby` | 전경 상대운동과 공간 깊이 필수 |
| 옆으로 돌아 보여 줘 | `arc-right` / `arc-left` | 제한된 각도와 거리 유지 |
| 한 바퀴 돌아 줘 | clockwise/counterclockwise `orbit` | 위에서 본 방향을 명시 |
| 뒤에서 따라가 줘 | `follow-over-shoulder` | 인물 뒤·어깨 너머 구도 |
| 앞에서 뒤로 가며 따라가 줘 | `reverse-tracking-walk-talk` | 정면 유지, 카메라 후진 |
| 옆에서 나란히 따라가 줘 | `side-tracking` | 평행 이동과 screen direction 유지 |
| 바닥 가까이 따라가 줘 | `low-tracking` | 발/바퀴를 focal point로 |
| 현장감 있게 살짝 흔들어 줘 | `handheld-shot` | 제어된 미세 흔들림만 허용 |
| 인물은 고정, 배경만 움직여 | `body-mount-snorricam` | subject-frame lock |
| 위로 올라가며 펼쳐 줘 | `crane-up` | 카메라 높이 자체가 상승 |
| 높은 곳에서 내려와 집중해 줘 | `crane-down` | 와이드→근경으로 하강 |
| 하늘에서 목적지로 다가가 줘 | `drone-push-in` | 안정된 공중 전진 |
| 하늘에서 멀어져 규모를 보여 줘 | `drone-pull-back` | 공중 후진, 피사체 잠금 |
| 내 눈으로 보는 것처럼 | `first-person-pov` | 시점 방식, 별도 카메라 이동 아님 |
| 미니어처처럼 | `tilt-shift` | 선택 초점 렌즈 효과 |
| 계속 확대해 다음 공간으로 | `infinite-zoom` | 중심 포털 scale continuity |
| 여기서 지구 밖까지 멀어져 | `earth-zoom-out` | 지리적 anchor 유지 |
| 시간이 빨리 흐르게 | `timelapse` | 고정 구도와 시간 압축 |
| 문/창문/벽을 지나 다음 장면 | `object-pass-through` | 가림 지점과 이동축 연속성 |

## 감정에서 후보 찾기

감정어는 기법을 확정하지 않고 후보 순위만 만든다. 피사체·공간·방향 문맥으로 최종 선택한다.

| 감정·목적 | 우선 후보 | 보조 후보 |
| --- | --- | --- |
| 집중·감정 고조 | slow zoom in | crane down |
| 충격·발견 | crash zoom in | fast zoom in, whip pan |
| 여운·외로움 | slow zoom out | drone pull-back |
| 웅장함·규모 | crane up, drone pull-back | helicopter shot, earth zoom-out |
| 몰입·여정 | follow OTS, tracking | first-person POV |
| 긴장·현장감 | controlled handheld | low tracking, chase shot |
| 제품의 입체감 | arc 또는 orbit | slow zoom in |
| 초현실적 연결 | infinite zoom | object pass-through |
| 시간 변화 | timelapse | static shot |

## 모호한 표현 판정

### “당겨 줘”

1. `확대`, `화각`, `클로즈업` 문맥이면 zoom in.
2. `공간 안으로`, `전경을 스치며`, `다가가` 문맥이면 camera push/track.
3. `멀어져`, `주변 공개` 문맥이면 zoom out 또는 pull-back.
4. 단서가 없으면 `렌즈 확대인가요, 카메라가 실제로 다가갈까요?` 한 번만 묻는다.

### “돌아 줘”

1. 15~90도 정도의 옆면 공개면 arc.
2. 180~360도 또는 `한 바퀴`면 orbit.
3. 방향은 `위에서 내려다본 기준 시계/반시계`로 정규화한다.
4. 각도와 방향이 모두 결과를 바꾸면 질문을 최대 2개 사용한다.

### “흔들리게”

1. `다큐`, `현장감`, `자연스럽게`, `살짝`이면 controlled handheld.
2. 인물을 프레임에 고정하고 배경이 움직이면 snorricam.
3. 의미 없는 random shake, 급격한 horizon roll, 멀미성 jitter는 제안하지 않는다.

### “웅장하게”

공간이 넓어지는지, 피사체로 접근하는지, 지상인지 공중인지 먼저 확인한다. 감정어 하나만으로
드론이나 지구 줌을 자동 삽입하지 않는다.

## 충돌 우선순위

| 충돌 | 처리 |
| --- | --- |
| static + handheld | 사용자에게 고정 안정감과 현장감 중 우선순위를 질문 |
| pan left + pan right | 시작·종료 대상을 확인하고 primary 방향 하나만 선택 |
| zoom in + zoom out | 시간 순서가 명시되면 두 구간, 아니면 질문 |
| zoom in + camera pull-back | 의도된 dolly zoom인지 확인; 임의 결합 금지 |
| clockwise + counterclockwise orbit | 위에서 본 기준 방향 하나를 확인 |
| timelapse + handheld | 시간 압축의 고정 기준과 흔들림 중 하나를 우선 |
| infinite zoom + earth zoom-out | inward/outward 방향이 반대이므로 primary 하나만 선택 |

충돌이 없고 명시적인 약한 보조 동작만 secondary로 허용한다. 예: follow OTS + subtle slow zoom in.

## Confidence와 질문

- `0.90~1.00`: 번호·전문명·방향·속도·피사체가 명시됨. 질문 없음.
- `0.75~0.89`: 일상 표현이 한 기법으로 수렴하고 안전 기본값만 보완. 기본값을 브리프에 공개.
- `0.50~0.74`: 두 후보 또는 중요한 필수 슬롯 누락. `needsClarification: true`.
- `<0.50`: 카메라 의도 없음 또는 해석 불가. Camera Prompt Pack을 생략하거나 질문 1개.

확인 질문은 최대 2개이며, 길이·색감처럼 카메라 선택과 무관한 내용을 여기서 다시 묻지 않는다.

## 기존 Director 용어와 경계

- 기존 `parallax`는 정지 레이어의 상대 이동으로 깊이를 **근사하는 합성 연출**이다.
- `arc`, `orbit`, `tracking`, `FPV`는 카메라와 피사체의 실제 공간 관계를 요구하는 전문 영상 의도다.
- `parallax`를 true orbit이나 tracking의 동의어로 쓰지 않는다.
- 카메라 의도가 없는 무드·드로잉 요청은 기존 [intent-map](intent-map.md)만으로 처리한다.
