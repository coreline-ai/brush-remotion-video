# 영상 제작 실전 학습 규칙

이 문서는 [FIELD-LOG](../FIELD-LOG.md)의 시간순 제작 기록에서 현재도 유효한 재발 방지 규칙만 추린다.
원인 분석과 당시 수치는 FIELD-LOG를 보존하고, 새 제작과 QA는 아래 rule ID를 기준으로 적용한다.

## 적용 원칙

- 문제를 발견하면 결과물만 고치지 말고 코드·테스트·스킬 계약 중 최소 한 곳에 환류한다.
- profile 고유 규칙보다 공통 계약을 먼저 적용한다.
- 수치 PASS와 사람의 시청·청취 승인을 구분한다.
- historical fixture 이름과 당시 수치는 소급 변경하지 않는다.

## 이미지와 원본 보존

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `IMG-001` | pen 계열 입력은 원본 전체를 보존한다. 기본은 contain과 종이색 패딩이며 피사체를 자르는 cover를 사용하지 않는다. | [FIELD-LOG pen-ref-demo](../FIELD-LOG.md), [background prompt](../skill/brush-video/references/background-prompt.md) |
| `IMG-002` | 동화의 따뜻한 종이 질감이 콘텐츠로 검출되면 외곽 연결 종이만 중성 `RGB(250,249,247)`로 정규화한다. | [storybook 이미지 계약](../skill/storybook-full-touch-video/references/full-touch-image-contract.md) |
| `IMG-003` | 다크 RGBA 입력은 alpha를 보존하고 완전 투명 픽셀의 숨은 RGB를 0으로 정규화한다. | [dark fidelity contract](../skill/dark-random-brush-video/references/fidelity-contract.md) |

## 펜·브러시 합성과 전환

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `PEN-001` | pen-brush 완료 화면에서 추출 outline과 원본 선을 중복 합성하지 않는다. paint 완료 직전 추출 outline을 제거하고 원본 선을 복원한다. | [pen-brush fidelity](../skill/pen-brush-video/references/fidelity-contract.md) |
| `PEN-002` | 최종 선 두께는 원본과 수치 비교한다. 승인 데모는 원본 3.831px, 최종 3.827px, 오차 0.104%였다. | [FIELD-LOG pen-brush-demo](../FIELD-LOG.md) |
| `TRN-001` | 씬 전환은 단순 fade가 아니라 앞·뒤 씬이 동일한 paper 상태로 수렴해야 한다. 흰 종이 계열의 기준 처방은 `outroWashOpacity: 1.0`이다. | [전환 공통 체크](../skill/_shared/references/transition-checklist.md) |
| `TRN-002` | 중간 씬 prewash를 금지하고 첫 씬에만 사용한다. | [전환 공통 체크](../skill/_shared/references/transition-checklist.md) |
| `TRN-003` | develop 92% 같은 조기 임계에서 레이어를 unmount하지 않는다. 레이어와 DOM 구조를 완료까지 유지한다. | [전환 공통 체크](../skill/_shared/references/transition-checklist.md) |
| `TRN-004` | 동일 이미지를 두 레이어로 교차합성해 완료를 만들지 않는다. 단일 레이어의 단조 변화 또는 `masked-hold`를 사용한다. | [전환 공통 체크](../skill/_shared/references/transition-checklist.md) |

## 렌더와 QA

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `REN-001` | Chromium 캡처 전에 이미지 decode를 명시적으로 기다리고 Remotion `<Img>` 경로를 사용한다. | [전환 공통 체크](../skill/_shared/references/transition-checklist.md) |
| `REN-002` | 렌더 public dir에는 props가 참조하는 project와 공통 brush 자산만 전달한다. 전체 public 복사를 반복하지 않는다. | [pipeline 문서](pipeline.md) |
| `REN-003` | 600초·18,000프레임은 단일 임시 디렉터리에 의존하지 않고 3,000프레임/100초 청크와 resume 단위를 사용한다. | [brush-video 문제 해결](../skill/brush-video/SKILL.md) |
| `QA-001` | start/mid/end 3장만으로 완료를 선언하지 않는다. lastStrokeEnd, develop 전후, outro 전후를 phase-aware하게 캡처한다. | [brush QA](../skill/qa-review/SKILL.md) |
| `QA-002` | dark 화면의 letterbox 경고는 자동 허용하지 않는다. 증거 스틸에서 실제 밴드인지 의도된 우주·심해 여백인지 확인한다. | [dark fidelity contract](../skill/dark-random-brush-video/references/fidelity-contract.md) |

## Dark random brush

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `DRK-001` | public 이름은 `dark-random-brush`, historical runtime·golden 이름은 `cosmic-random-brush`로 유지한다. | [dark skill](../skill/dark-random-brush-video/SKILL.md) |
| `DRK-002` | 기본 36터치와 같은 폭의 보완 1~20개만 허용하고 붓 폭은 230~365px를 유지한다. | [dark fidelity contract](../skill/dark-random-brush-video/references/fidelity-contract.md) |
| `DRK-003` | 전체 mask coverage 0.991과 가시 콘텐츠 coverage 0.985를 분리 측정한다. 보완 20개 후 미달이면 입력·profile 문제로 실패한다. | [dark fidelity contract](../skill/dark-random-brush-video/references/fidelity-contract.md) |
| `DRK-004` | 동일 이미지와 seed는 동일 routes를 만들어야 하며 semantic tracing, 수백 stamp, bitmap fade로 coverage를 속이지 않는다. | [dark fidelity contract](../skill/dark-random-brush-video/references/fidelity-contract.md) |

## Storybook

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `STY-001` | 기본 10씬×10초는 씬별 이미지 1장, 씬별 TTS, 10초 padding을 사용해 타이밍을 고정한다. | [SRT·TTS 계약](../skill/storybook-full-touch-video/references/story-srt-tts-contract.md) |
| `STY-002` | pen-brush storybook도 각 씬 끝에서 동일 paper로 수렴하는 outro를 적용하고 모든 경계를 검사한다. | [storybook build and QA](../skill/storybook-full-touch-video/references/build-and-qa.md) |

## BGM과 라이선스

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `BGM-001` | BGM은 -23 LUFS 기준으로 정규화한 뒤 profile gain, fade, -1dBTP limiter를 적용한다. 최종 체감 기준은 약 -18 LUFS다. | [공통 BGM 정책](../skill/_shared/references/bgm-policy.md) |
| `BGM-002` | 내레이션 영상은 활성 구간 감쇄와 비활성 구간 복귀를 따로 측정한다. 전체 평균만으로 덕킹을 판정하지 않는다. | [공통 BGM 정책](../skill/_shared/references/bgm-policy.md) |
| `BGM-003` | MP3, 공식 URL, 작가, 다운로드 날짜, SHA-256, 라이선스 증빙을 manifest로 보관한다. 페이지에 Content ID 표시가 없다는 사실은 미등록 보장이 아니다. | [공통 BGM 정책](../skill/_shared/references/bgm-policy.md) |
| `BGM-004` | 자동 자산·E2E PASS와 사람 청취 승인을 분리한다. `listening-approval.json`이 없으면 최종 human gate는 false다. | `python3 bin/bgm-assets.py gate` |
| `BGM-005` | Pixabay 음원은 YouTube 일반 영상·Shorts의 신규 제작·교체·배포에 사용하지 않는다. 로컬 청취·내부 데모·과거 회귀 자산으로만 보존하며 preflight와 auditor가 금지 조합을 FAIL 처리한다. | [공통 BGM 정책](../skill/_shared/references/bgm-policy.md) |

## TTS와 재현성

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `TTS-001` | 신규 YAML은 `voice:auto` 대신 `female-01`~`female-10` 중 명시적 ID와 speed를 기록한다. | [Supertonic 음성 카탈로그](../skill/_shared/references/supertonic-voice-catalog.md) |
| `TTS-002` | F1~F5 alias와 M1~M5 native 경로를 유지하되 알 수 없는 ID를 F1로 조용히 대체하지 않는다. | [Supertonic 음성 카탈로그](../skill/_shared/references/supertonic-voice-catalog.md) |
| `TTS-003` | voice manifest에 pack/package/model, 구성, speed, catalog/style hash, AI 합성 고지를 남긴다. | [pipeline 문서](pipeline.md) |
| `TTS-004` | 실제 WAV 샘플 길이를 SRT와 씬 타이밍의 시계로 사용한다. | [project.yaml 가이드](../skill/_shared/references/project-yaml-guide.md) |

## 자연어 카메라 프롬프트

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `PRM-001` | 일상적인 카메라 표현은 01~36·46의 37개 canonical 기법으로 정규화하고, 중복 번호 37~45는 28~36 alias로만 처리한다. | [Camera Prompt Catalog](../skill/_shared/references/camera-prompt-catalog.json) |
| `PRM-002` | 한 출력의 primary technique은 1개, 충돌하지 않는 secondary는 최대 1개다. 방향·속도·피사체·구도 등 사용자 명시값을 기본값으로 덮어쓰지 않는다. | [Camera Prompt Guide](../skill/_shared/references/camera-prompt-guide.md) |
| `PRM-003` | Zoom은 렌즈 화각 변화, push/dolly/tracking은 카메라 위치 이동으로 구분한다. `당겨줘`, `돌아줘`, `흔들리게`가 둘 이상 후보로 남으면 확인 질문은 최대 2개다. | [Camera Intent Map](../skill/director/references/camera-intent-map.md) |
| `PRM-004` | Camera Prompt Pack은 연출 브리프이며 `project.yaml` 또는 render props가 아니다. 미지원 `camera:`/`cameraMotion:`을 추가하지 않고 true 3D 이동은 `external-required`로 표시한다. | [Brush Director](../skill/director/SKILL.md) |
| `PRM-005` | 한/영 prompt는 technique→subject→direction/speed→start/end composition→lock/stabilization→continuity 순서의 동일 슬롯을 사용한다. 방향이나 구도가 다르면 실패다. | [Camera Prompt Guide](../skill/_shared/references/camera-prompt-guide.md) |
| `PRM-006` | 펜·펜브러시는 line weight와 outline sharpness, 인물은 identity, 제품은 shape/logo, 텍스트는 철자·방향 보존 negative rule을 포함한다. | [대표 예시 12건](../skill/director/references/camera-prompt-examples.md) |

카메라 의도가 없는 요청에는 Camera Prompt Pack을 생성하지 않는다. 이 기능은 특정 AI 영상 모델의
비공식 문법이나 API를 추가하지 않는 모델 중립 번역 지식 계층이다.

## 운영과 스킬 관리

| Rule | 규칙 | 근거·현재 계약 |
| --- | --- | --- |
| `OPS-001` | 스킬은 코드를 내장하지 않고 프로젝트의 공통 CLI와 파이프라인만 실행한다. | [README](../README.md) |
| `OPS-002` | 정식 스킬 목록의 단일 진실은 `skill/catalog.json`이며 README·installer·UI metadata와 교차 검증한다. | `python3 bin/skill-catalog.py check` |
| `OPS-003` | 문제 해결은 FIELD-LOG 기록 → 코드/계약 수정 → 회귀 테스트 → 스킬 환류 순서로 닫는다. | [FIELD-LOG](../FIELD-LOG.md) |
| `OPS-004` | 실제 사용자 파일·디렉터리는 installer가 삭제하지 않는다. symlink만 안전하게 생성·교체한다. | `bin/install-skills.sh --check` |

## 현재 자동 검증 기준선

- Python: 312건
- Vitest: 50건
- TypeScript typecheck 및 schema sync: PASS
- Skill validator: 9/9
- Voice preview: 10/10
- BGM: assets 14/14, E2E 4/4
- BGM 사람 청취: `listening-approval.json`이 없으면 미완료

이 수치는 현재 상태를 설명하는 기준선이다. 테스트가 추가되면 총수는 늘 수 있지만 기존 테스트를 삭제해 기준선을 낮추면 안 된다.
