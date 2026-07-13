# Camera Prompt Interpreter 대표 예시 12건

아래 결과는 모델 중립 예시다. 실제 응답에서는 피사체명과 시작/종료 구도를 사용자 문맥에 맞게
구체화하고, 입력 자산 종류에 맞는 공통 negative rule을 합친다.

## 1. 느린 접근 — Slow Zoom In

- 입력: `그림이 완성되면 천천히 인물에게 당겨 줘.`
- 해석: `slow-zoom-in`(08), primary 1개, clarification 없음
- 슬롯: inward / slow / medium-wide → medium-close-up / face lock / minimal blur
- 한국어: 카메라 위치는 유지하고 인물의 얼굴을 잠근 채 천천히 화각을 좁혀 중간 와이드에서 미디엄 클로즈업으로 확대한다.
- English: Keep the camera position fixed, lock onto the character's face, and slowly narrow the field of view from a medium-wide shot to a medium close-up.
- Negative: no dolly translation, no abrupt crop, no line thickening, preserve facial identity
- 호환성: Remotion `supported`, AI video `supported`, image `composition-only`, transition `not-applicable`

## 2. 웅장한 이탈 — Drone Pull-Back

- 입력: `산 정상의 사람을 중심에 두고 하늘에서 웅장하게 멀어져 줘.`
- 해석: `drone-pull-back`(30), clarification 없음
- 슬롯: backward / slow / aerial-wide → extreme-wide / subject lock
- 한국어: 안정된 공중 시점에서 산 정상의 인물을 중심에 잠그고 천천히 후진해 산맥 전체의 규모를 공개한다.
- English: From a stable aerial viewpoint, keep the person on the summit centered and pull backward slowly to reveal the full scale of the mountain range.
- Negative: no optical-only zoom, no subject loss, no terrain warping
- 호환성: Remotion `external-required`, AI video `supported`, image `composition-only`, transition `not-applicable`

## 3. 뒤따르기 — Follow Over-the-Shoulder

- 입력: `숲길을 걷는 아이 뒤에서 어깨 너머로 따라가 줘.`
- 해석: `follow-over-shoulder`(19), clarification 없음
- 슬롯: forward / subject-matched / close-follow / OTS medium / smooth
- 한국어: 아이의 뒤쪽 어깨 너머 구도를 유지하며 걷는 속도에 맞춰 일정한 거리로 부드럽게 따라간다.
- English: Follow the child smoothly from behind in an over-the-shoulder medium framing, matching the walking pace and maintaining constant distance.
- Negative: no front-facing reversal, no identity drift, no uncontrolled shake
- 호환성: Remotion `external-required`, AI video `supported`, image `composition-only`, transition `not-applicable`

## 4. 오른쪽 휩팬 전환

- 입력: `오른쪽으로 확 휙 넘겨서 다음 방으로 전환해 줘.`
- 해석: `whip-pan-right`(04), clarification 없음
- 슬롯: right / very-fast / directional blur / screen direction continuity
- 한국어: 오른쪽으로 매우 빠른 휩팬을 수행하고 방향성 모션 블러가 최대가 되는 지점에서 같은 축의 다음 방으로 전환한다.
- English: Execute a very fast whip pan to the right and transition at peak directional motion blur into the next room on the same screen axis.
- Negative: no leftward reversal, no radial blur, no transition seam
- 호환성: Remotion `simulated`, AI video `supported`, image `not-applicable`, transition `supported`

## 5. 지구 줌 아웃

- 입력: `서울의 이 건물에서 시작해서 지구 밖 우주까지 빠져나가 줘.`
- 해석: `earth-zoom-out`(35), clarification 없음
- 슬롯: outward / accelerating / building → Earth in space / geographic anchor
- 한국어: 건물의 지리적 위치를 잠그고 서울·한반도·지구·우주 순으로 가속하며 연속 줌 아웃한다.
- English: Lock the building's geographic location and accelerate outward continuously through Seoul, the Korean Peninsula, Earth, and space.
- Negative: no geographic jump, no anchor drift, no planet deformation
- 호환성: Remotion `external-required`, AI video `supported`, image `not-applicable`, transition `supported`

## 6. 오브젝트 통과

- 입력: `낡은 문을 통과해서 밝은 정원으로 자연스럽게 이어 줘.`
- 해석: `object-pass-through`(46), clarification 없음
- 슬롯: forward / medium / door opening / axis-and-light continuity
- 한국어: 낡은 문의 어두운 가림 구간을 통과점으로 사용해 전진축을 유지하며 밝은 정원으로 진입하고 노출을 자연스럽게 연결한다.
- English: Use the dark occlusion of the old doorway as the pass-through point, preserve the forward axis, and enter the bright garden with a continuous exposure transition.
- Negative: no solid-surface collision, no axis reversal, no hard exposure flash
- 호환성: Remotion `external-required`, AI video `supported`, image `not-applicable`, transition `supported`

## 7. 제품 오비트

- 입력: `향수병 주위를 위에서 봤을 때 시계 방향으로 천천히 한 바퀴 돌아 줘.`
- 해석: `orbit-clockwise`(16), clarification 없음
- 슬롯: clockwise-top-view / slow / constant distance / product lock
- 한국어: 향수병을 중심에 잠그고 위에서 내려다본 기준 시계 방향으로 일정한 거리와 높이를 유지하며 천천히 오비트한다.
- English: Lock the perfume bottle at center and orbit slowly clockwise as viewed from above, maintaining constant distance and height.
- Negative: preserve exact bottle shape and label, no spiral drift, no product rotation
- 호환성: Remotion `external-required`, AI video `supported`, image `composition-only`, transition `not-applicable`

## 8. 통제된 핸드헬드

- 입력: `시장 골목을 다큐처럼 현장감 있게 살짝 흔들리게 보여 줘.`
- 해석: `handheld-shot`(25), clarification 없음
- 슬롯: controlled-handheld / small amplitude / natural minimal blur
- 한국어: 시장 골목의 가독성을 유지하면서 작고 제어된 핸드헬드 움직임만 더해 다큐멘터리 현장감을 만든다.
- English: Preserve readability of the market alley and add only small, controlled handheld motion for documentary immediacy.
- Negative: no violent random shake, no horizon flipping, no motion-sickness jitter
- 호환성: Remotion `supported`, AI video `supported`, image `composition-only`, transition `not-applicable`

## 9. 타임랩스

- 입력: `고정된 구도에서 노을이 밤하늘로 바뀌는 시간을 빠르게 보여 줘.`
- 해석: `timelapse`(36), clarification 없음
- 슬롯: locked-off / time-compressed / sunset → night / fixed spatial reference
- 한국어: 완전히 고정된 와이드 구도에서 노을이 밤하늘로 바뀌는 시간을 압축하고 지평선과 건물의 위치를 끝까지 유지한다.
- English: Compress the transition from sunset to night from a completely locked wide view, preserving the horizon and building positions throughout.
- Negative: no camera drift, no exposure flicker, no object teleportation
- 호환성: Remotion `external-required`, AI video `supported`, image `not-applicable`, transition `simulated`

## 10. 모호한 “당겨 줘”

- 입력: `주인공 쪽으로 당겨 줘.`
- 잠정 해석: `slow-zoom-in`(08), confidence 0.62, `needsClarification: true`
- 질문: `렌즈로 확대할까요, 카메라가 공간 안에서 실제로 다가갈까요?`
- 임시 기본값: 렌즈 확대 / slow / face lock. 답을 받기 전 실제 이동을 확정하지 않는다.
- Negative: no unsupported camera translation, no abrupt crop, preserve facial identity

## 11. 충돌 — 고정 + 흔들림

- 입력: `카메라는 완전히 고정인데 현장감 있게 계속 흔들리게 해 줘.`
- 잠정 해석: primary `static-shot`(01), competing `handheld-shot`(25), confidence 0.54
- 상태: `needsClarification: true`
- 질문: `완전 고정의 안정감과 미세 핸드헬드 현장감 중 어느 쪽을 우선할까요?`
- 규칙: 답을 받기 전 두 기법을 한 프롬프트에 동시에 명령하지 않는다.

## 12. 한영 혼용 + 보조 기법

- 입력: `인물 뒤를 follow하면서 아주 subtle하게 slow zoom in 해 줘.`
- 해석: primary `follow-over-shoulder`(19), secondary `slow-zoom-in`(08), clarification 없음
- 한국어: 인물 뒤의 오버 더 숄더 구도로 같은 속도를 유지해 따라가며, 얼굴을 잠근 채 매우 약한 슬로우 줌 인을 보조로 적용한다.
- English: Follow behind the subject at a matched pace in an over-the-shoulder framing, with a very subtle secondary slow zoom in locked to the face.
- Negative: no third technique, no distance pumping, no identity drift, no softened outlines
- 호환성: Remotion `external-required`, AI video `supported`, image `composition-only`, transition `not-applicable`

## 수동 Rubric 결과

위 12건은 전문성·충실성·한영 일관성·간결성·실행 가능성·안전 제약의 6축을 검토한다.
명확한 10건은 각 축 4/5 이상, 모호·충돌 2건은 질문 전 실행을 보류함으로써 실행 가능성과
충실성 4/5 이상을 충족한다. 특정 AI 영상 서비스 문법이나 미지원 `project.yaml` 필드는 사용하지 않는다.
