---
name: dark-random-brush-video
description: >-
  어두운 배경의 16:9 이미지를 자유로운 랜덤 붓 터치로 드러내는 1920×1080·30fps Remotion 영상 스킬.
  우주·행성·성운·심해·야간 풍경 등 어두운 이미지 1/6/60씬에 사용한다.
  project.yaml에는 drawing.profile: dark-random-brush를 권장하며,
  엔진은 기존 cosmic-random-brush runtime key를 호환 유지한다.
---

# dark-random-brush-video

**실행 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`

이 스킬은 실행 코드를 복사하지 않는다. 리포의 `bin/build.py`, Python 파이프라인,
Remotion Scene이 유일한 실행 소스다. public profile은 `dark-random-brush`이고,
기존 골든·렌더 분기와의 호환을 위해 내부 canonical runtime key는
`cosmic-random-brush`로 유지한다.

## 적용 범위

- 어두운 배경의 우주·행성·성운·심해·야간 산·달 표면 등 의미가 분명한 16:9 이미지.
- YouTube 1920×1080, 30fps, 씬당 300프레임(10초).
- 골든 1씬, 대표 검증 6씬(60초), 본편 60씬(600초).
- `background.strategy: user-images`, `fit: cover`를 기본으로 한다.
- 세로 포맷, 2~5씬·7~59씬, non-ambient 입력은 현재 지원 범위가 아니다.

## project.yaml

```yaml
projectId: dark-random-brush-demo
title: "심해의 빛"
format: youtube

background:
  strategy: user-images
  images: [./source.png]
  fit: cover

drawing:
  profile: dark-random-brush # public name; runtime은 cosmic-random-brush로 호환 정규화
  seed: 260712

ambient:
  scenes: 1

bgm:
  mode: asset
  assetId: local-approved-track
  sourceStartSec: 3.4
  fadeInSec: 0.4
  fadeOutSec: 5.0
  licensePolicy: strict
```

## 실행

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
pipeline/.venv/bin/python bin/build.py <project.yaml> --audit
```

산출물:

- `output/{projectId}.mp4`
- `data/{projectId}/qa/contact-sheet.png`
- `data/{projectId}/qa/gallery.html`
- `data/{projectId}/qa/cosmic-random-brush-report.json` (historical filename, runtime 호환)
- `data/{projectId}/audit/audit-report.md`

실패 지점부터 재개:

```bash
pipeline/.venv/bin/python bin/build.py <project.yaml> --from routes --audit
```

## 영상 제작 중 보완된 공통 규칙

### 1. 풀 화면 이미지 계약

- 모든 입력은 1920×1080 RGB/RGBA 또는 동등한 16:9 원본이어야 한다.
- `cover`로 채우되 주 피사체가 프레임 밖으로 잘리지 않도록 safe margin을 확보한다.
- 검은 띠, 빈 프레임, 콜라주, 텍스트·워터마크·다이어그램, 의미를 알 수 없는 crop을 금지한다.
- 파일명·cue·이미지의 장면 의미가 일치해야 한다. 60장은 manifest에 원본/정규화 SHA-256을 기록한다.
- 영상 렌더 전에 contact sheet와 HTML gallery로 각 이미지가 풀 화면인지 눈으로 확인한다.

### 2. 자연스러운 랜덤 붓 터치 계약

- route family는 `free-random-touch`다. 의미 윤곽이나 행성 곡선을 따라 그리지 않는다.
- 기본 36터치 뒤 같은 폭의 supplemental touch 1~20개만 추가한다.
- 붓 폭은 230~365px, 평균 중심 이동 ≥650px, 최대 이동 ≥1200px를 유지한다.
- 이동 중 커서는 보이더라도 이미지 mask가 증가하면 안 된다.
- 수백 개의 작은 stamp, 갑작스러운 순간이동, bitmap fade로 coverage를 속이는 방식을 금지한다.
- 동일 이미지·seed는 동일 routes를 생성해야 한다. draw는 36~40f에 시작하고 210f 이내에 끝낸다.

### 3. coverage hard gate

- 전체 mask coverage ≥0.991.
- 6/60씬의 가시 콘텐츠 coverage ≥0.985.
- 보완 터치 20개 뒤에도 미달이면 폭을 키우지 말고 입력 이미지·profile을 점검한 후 실패한다.
- 커버리지가 낮다고 브러싱 방식을 임의로 바꾸지 않는다. 방식 변경은 골든 diff와 사용자 승인 뒤에 한다.

### 4. 다크 화면 연출

- paper는 거의 검정(`#01020d`)을 사용하고, 이미지는 잉크 질감과 저채도 대비를 유지한다.
- prewash로 시작 화면을 미리 노출하지 않는다. opening → random-pass → base-pass → complete 순서를 지킨다.
- 완료 후에는 이미지 전체를 유지하고 outro pulse나 밝기 튐으로 coverage를 보정하지 않는다.

### 5. 씬 매트릭스와 장기 렌더

- ambient만 허용하며 1/6/60씬을 각각 10/60/600초로 만든다.
- 60씬은 `background.images`와 `ambient.cues`가 각각 정확히 60개여야 한다.
- 총 18,000프레임을 3,000프레임 단위로 segmented render하고 cache/resume을 사용한다.
- 씬 경계 59개에서 앞뒤 이미지·오디오가 섞이지 않는지 검사한다.

### 6. BGM 계약

- Pixabay 음원은 YouTube 제작·교체·배포에 사용하지 않는다. 로컬 청취·내부 데모·과거 검증용으로만 보존한다.
- 기본 후보는 `youtube-chris-zabriskie-fight-for-your-honor`, 장편 playlist는 공통 BGM 정책의 YouTube 허용 3곡을 사용한다.
- 외부 음원은 로컬 catalog 등록, source/license manifest, strict preflight를 통과해야 한다.
- 긴 source pre-roll은 `sourceStartSec`로 제거하고, 시작 즉시 짧은 fade(기본 0.4초)로 들어간다.
- 끝부분은 약 5초 fade-out, 최종 master는 48kHz stereo로 확인한다.
- 앞쪽 무음이 길면 합격으로 보지 않는다. Content ID 결과는 라이선스 보증이 아니다.

## 완료 판정

1. `cosmic-random-brush-report.json.pass`가 `true`이고 FAIL이 없어야 한다.
2. 붓 폭 230~365px, 기본/보완 터치 36+1~20, mask/visible coverage 계약을 확인한다.
3. contact sheet에서 opening, first-touch, random-pass, base-pass, complete, outro를 눈으로 확인한다.
4. 최종 MP4에서 씬별 3프레임(60씬은 총 180장)과 59개 경계를 검사한다.
5. video-auditor는 PASS, FAIL 0이어야 하며 letterbox WARN은 실제 밴드가 아닌지 증거 스틸로 확인한다.

## 대표 실행 예제

```bash
# 골든 1씬
pipeline/.venv/bin/python bin/build.py examples/cosmic-random-brush/project.yaml --audit
pipeline/.venv/bin/python tests/golden/cosmic-random-brush/check.py

# 대표 6씬
pipeline/.venv/bin/python bin/build.py examples/cosmic-random-brush-v02/project.yaml --audit
pipeline/.venv/bin/python tests/golden/cosmic-random-brush-v02/check.py

# 본편 60씬
pipeline/.venv/bin/python bin/build.py examples/cosmic-random-brush-v03/project.yaml --audit
pipeline/.venv/bin/python tests/golden/cosmic-random-brush-v03/check.py
```

기존 `cosmic-random-brush` profile을 입력한 historical project도 계속 허용한다.
새 프로젝트와 새 문서에서는 `dark-random-brush`를 사용한다.

## 이름 변경 호환 정책

- 설치 경로와 사용자-facing skill 이름은 `dark-random-brush-video`로 통일한다.
- `bin/install-skills.sh`는 기존 `cosmic-random-brush-video` symlink만 정리하고,
  사용자가 만든 실체 파일·디렉터리는 삭제하지 않는다.
- historical project의 `drawing.profile: cosmic-random-brush`, golden fixture,
  report 파일명은 변경하지 않는다. parser가 새 public alias를 같은 runtime route로 정규화한다.
