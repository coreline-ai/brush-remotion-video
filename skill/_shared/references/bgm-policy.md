# 로컬 BGM·라이선스·믹싱 정책

## YouTube·Shorts Pixabay 사용 금지 (필수)

> **금지:** Pixabay 음원은 YouTube 일반 영상과 YouTube Shorts의 신규 제작·BGM 교체·최종 배포에 사용하지 않는다.

- Pixabay 자산은 로컬 청취, 내부 데모, 과거 회귀 검증용으로만 보존한다.
- 기존 Pixabay 적용 결과물을 재업로드·재편집할 때는 허용 음원으로 교체한다.
- YouTube 배포에는 catalog의 `youtube-audio-library` 또는 검증된 `artist-site` 자산만 사용한다.
- catalog의 `youtubeAllowed: true`가 없는 자산은 YouTube/Shorts 후보로 취급하지 않는다.
- `CC BY 4.0`과 저작자 표시 필수 음원은 catalog의 `attributionText`를 설명란 또는 크레딧에 그대로 넣는다.
- `format: youtube`와 `format: shorts`에서 Pixabay asset/playlist를 지정하면 strict/warn과 관계없이 preflight hard fail이다.
- `bin/replace-bgm.py`도 YouTube 배포 도구이므로 Pixabay 자산을 거부한다.

이 금지는 Pixabay 라이선스의 적법성 판단을 대신하려는 것이 아니라, Content ID·권리 상태 변경과
수익화 리스크를 피하기 위한 **이 프로젝트의 보수적 배포 정책**이다.

## 원칙

- BGM은 `input.audio`와 분리한다. `input.audio`는 실더빙/STT 입력만 의미한다.
- 빌드 중 인터넷 다운로드를 하지 않는다.
- 공식 곡 페이지에서 내려받은 파일만 `local-assets/bgm/`에 import한다.
- MP3와 함께 곡 페이지 증빙, 라이선스 증빙, 다운로드/확인 날짜, 작가명, SHA-256을 보관한다.
- `Content ID 표시 없음`은 `미등록 보장`이 아니다. 상태는 `not-displayed`로 기록한다.
- 외부 BGM을 사용하면 `data/<projectId>/licenses/bgm-manifest.json`을 남긴다.
- 원본 MP3와 증빙은 Git에 커밋하거나 스킬에 포함하지 않는다.
- 새 매니페스트의 `distribution`이 `youtube|shorts`이면 auditor도 Pixabay source를 FAIL 처리한다.

공식 정책: [Pixabay Content License](https://pixabay.com/service/license-summary/),
[Pixabay FAQ·Content ID](https://pixabay.com/service/faq/),
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

## YouTube 오디오 보관함·CC BY 사용 가능 항목

YouTube 오디오 보관함에서 받은 음원도 로컬 원본·출처·라이선스 증빙·SHA-256을 등록하면
`bgm.mode: asset`으로 사용할 수 있다. 단, `CC BY 4.0` 음원은 `attributionRequired: true`와
완전한 `attributionText`가 반드시 있어야 하며, 이 문구를 영상 설명란 또는 크레딧에 포함한다.
음원을 자르거나 리믹스했다면 수정 사실도 표시한다.

| assetId | 곡 | 아티스트 | 라이선스 | 사용 조건 |
|---|---|---|---|---|
| `youtube-chris-zabriskie-chance-luck-finale` | Chance, Luck, Errors in Nature, Fate, Destruction As a Finale | Chris Zabriskie | CC BY 4.0 | 지정 저작자 표시 문구 필수 |
| `youtube-chris-zabriskie-fight-for-your-honor` | I Am a Man Who Will Fight for Your Honor | Chris Zabriskie | CC BY 4.0 | 지정 저작자 표시·변경 사항 필수 |

필수 표시 문구:

```text
Chance, Luck, Errors in Nature, Fate, Destruction As a Finale by Chris Zabriskie is licensed under a Creative Commons Attribution 4.0 license.
https://creativecommons.org/licenses/by/4.0/
Source: https://www.chriszabriskie.com/reappear/
Artist: https://www.chriszabriskie.com/
Changes: Audio may be trimmed, normalized, faded, or mixed for this video.
```

Honor 표시 문구는 catalog의 `license.attributionText`가 단일 진실이다. delivery 단계가 이를
`youtube-description.txt`와 `ATTRIBUTION.txt`에 그대로 내보낸다.

## 다운로드·등록 순서

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video

# 공식 청취·다운로드 페이지 확인
pipeline/.venv/bin/python bin/bgm-assets.py sources

# 브라우저에서 공식 페이지를 열어 MP3를 원래 파일명으로 ~/Downloads에 저장한 뒤
# 카탈로그 URL slug와 단일 일치하는 파일만 자동 등록
pipeline/.venv/bin/python bin/bgm-assets.py scan --attach

# 파일명을 바꿨거나 개별 증빙을 직접 지정해야 하면 수동 등록
# 아래 Pixabay 예시는 로컬 청취·내부 데모 등록 전용이며 YouTube/Shorts에는 사용할 수 없음
pipeline/.venv/bin/python bin/bgm-assets.py import \
  --id pixabay-piano-dreamcloud-meditation \
  --file ~/Downloads/piano-dreamcloud.mp3 \
  --artist NaturesEye \
  --content-id-status not-displayed \
  --source-evidence ~/Downloads/piano-dreamcloud-page.png \
  --license-evidence ~/Downloads/pixabay-license.pdf

# 카탈로그 전체 로컬 상태 확인. 미완료가 있으면 exit 1
pipeline/.venv/bin/python bin/bgm-assets.py verify
pipeline/.venv/bin/python bin/bgm-assets.py dashboard
pipeline/.venv/bin/python bin/bgm-assets.py review
```

대시보드는 `local-assets/bgm/index.html`에 생성된다. 다운로드 전에는 공식 청취·다운로드 링크와
증빙 상태를 보여주고, import/attach가 완료되면 동일 카드에 로컬 `<audio>` 플레이어가 활성화된다.
`scan`은 기본적으로 `~/Downloads`를 재귀 검색한다. 다른 폴더는 `--dir <폴더>`를 반복 지정하고,
`--attach`를 빼면 파일을 복사하지 않고 일치 결과만 미리 확인한다.
`review`가 생성하는 `listening-review.html`에서는 검증 영상별로 이어폰과 노트북 스피커를
각각 승인하고, 판정·메모를 `bgm-listening-review.json`으로 내보내 최종 청취 근거로 보관한다.
내보낸 결과는 `bin/bgm-assets.py review --import-result <JSON>`으로 검증한다. 다섯 영상 중
하나라도 두 환경 체크가 빠지거나 판정이 `pass`가 아니면 최종 승인 파일을 만들지 않는다.
최종 완료 선언 전 `bin/bgm-assets.py gate`를 실행한다. 카탈로그 전체 PASS, 일반 brush·pen-brush·
Quiet narration·10분 playlist E2E의 영상/audit/manifest, 사람 승인이 모두 있어야 exit 0이다.

리포가 미리 저장한 곡 페이지·라이선스 캡처가 `evidence: PASS`라면 MP3 다운로드 뒤 다음
축약 명령으로 연결할 수 있다.

```bash
pipeline/.venv/bin/python bin/bgm-assets.py attach \
  --id pixabay-piano-dreamcloud-meditation \
  --file ~/Downloads/piano-dreamcloud.mp3
```

위 attach 예시도 로컬 청취·내부 데모 전용이다. YouTube/Shorts project.yaml이나
`replace-bgm.py`에는 `pixabay-*` ID를 넣지 않는다.

Content ID 인증서가 제공되면 `--certificate <파일>`도 지정한다.

## project.yaml

### 단일곡

```yaml
bgm:
  mode: asset
  assetId: youtube-chris-zabriskie-fight-for-your-honor
  gainDb: 5.0
  fadeInSec: 1.8
  fadeOutSec: 2.0
  licensePolicy: strict
```

### 내레이션 자동 덕킹

```yaml
bgm:
  mode: asset
  assetId: youtube-jesse-gallagher-satya-yuga
  gainDb: 3.0
  ducking:
    enabled: true
    amountDb: 8.0
    attackMs: 120
    releaseMs: 600
  licensePolicy: strict
```

### 2~3곡 플레이리스트

```yaml
bgm:
  mode: playlist
  playlist:
    assetIds:
      - youtube-chris-zabriskie-fight-for-your-honor
      - youtube-chris-zabriskie-chance-luck-finale
      - youtube-jesse-gallagher-satya-yuga
    crossfadeSec: 3.0
  gainDb: 5.0
  fadeInSec: 1.8
  fadeOutSec: 2.0
  licensePolicy: strict
```

## 자동 BGM (기본 정책 — bgm 블록 생략 시)

`bin/build.py`를 사용하는 영상 스킬에서 `bgm` 블록을 생략하면 **대사(음성/TTS)가 없는
15~120초 영상은 Stable Audio 3 MLX 피아노 후보를 1순위로 자동 생성**한다. Stable Audio
환경변수가 없거나 길이·생성 조건을 만족하지 않으면 기존 로컬 catalog, 마지막으로 synth BGM으로
안전하게 fallback한다. 빌드 중 인터넷 다운로드는 하지 않는다.

| 상황 | 동작 |
|---|---|
| 대사 없음(ambient) + 15~120초 + `bgm` 없음 | **Stable Audio 피아노 후보 1순위** → catalog → synth |
| 대사 있음(narration/tts/whisper) + `bgm` 없음 | 음성만 사용 (자동 생성 안 함) — 원하면 `bgm.mode: piano-auto` 명시 |
| 완전 무음 원함 | `bgm: { mode: "off" }` 명시 |
| 특정 곡 고정 | 그때만 `bgm: { mode: asset, assetId: ... }` |
| Stable Audio 미설치·15초 미만·120초 초과·생성 실패 | 기존 catalog → synth로 안전 폴백 (implicit auto) |

Stable Audio prompt 기준과 fallback catalog 기준 (프로파일·포맷·길이만으로 **결정적** — 같은 입력이면 같은 후보):

| 상황 | 자동 선택 |
|---|---|
| 일반 brush / ambient | Stable Audio `ambient-piano`; 실패 시 `youtube-chris-zabriskie-fight-for-your-honor` |
| pen | Stable Audio `minimal-ambient`; 실패 시 `youtube-chris-zabriskie-chance-luck-finale` |
| pen-brush / full-color-motion | Stable Audio `cinematic-piano`; 실패 시 `youtube-jesse-gallagher-satya-yuga` |
| dark-random-brush (runtime 호환키: cosmic-random-brush) | Stable Audio `mystery-horror-piano`; 실패 시 `youtube-chris-zabriskie-fight-for-your-honor` |
| 밝은 쇼츠(format: shorts) | 프로파일 prompt를 유지하고 Stable Audio 우선; 실패 시 `youtube-jesse-gallagher-satya-yuga` |
| 120초 초과 | Stable Audio 제외, 기존 catalog/synth fallback (10분 초과는 허용 3곡 playlist) |

구현: `bin/build.py` `stage_mix()`가 `cfg.bgm is None and voice is None`일 때
`brushvid.piano_auto_bgm.build_candidate()`를 먼저 호출한다. 후보가 준비되면 기존
`prepare_bgm()`과 같은 정규화·fade·mix 경로를 사용한다. 후보 실패 시
`brushvid.bgm.select_auto_bgm(profile, fmt, duration_sec)`를 호출하고 catalog preflight 실패 시
synth로 폴백한다. `STABLE_AUDIO_3_MLX_ROOT`로 로컬 MLX 설치 위치를 지정한다.

## 모드 (bgm 블록을 명시할 때)

| mode | 동작 |
|---|---|
| `off` | BGM 없음. 내레이션이 있으면 음성만 mux |
| `synth` | 기존 결정적 피아노 합성을 공통 믹싱 경로로 처리 |
| `asset` | 등록한 로컬 음원 1곡 |
| `playlist` | 등록한 2~3곡을 정규화하고 크로스페이드 |
| `piano-auto` | Stable Audio 3 MLX 피아노 후보 생성 후 공통 믹싱·QA; 음성 영상은 명시할 때만 사용 |

플레이리스트가 영상보다 짧으면 각 곡을 따로 반복하지 않는다. 지정 순서 전체를
`A → B → C → A`로 반복하고 모든 경계에 크로스페이드를 적용한다.

`bgm` 블록이 없는 기존 프로젝트는 하위 호환된다. Stable Audio 환경이 준비된
15~120초 앰비언트는 피아노 후보를 먼저 시도하고, 그 외에는 기존 catalog/synth를 사용한다.
내레이션/TTS/whisper는 기존 음성만 유지하며 생성 BGM이 필요하면 `piano-auto`를 명시한다.

## 기본값

- 일반 brush 앰비언트: `youtube-chris-zabriskie-fight-for-your-honor`
- pen-brush: `youtube-jesse-gallagher-satya-yuga`
- pen-video: `youtube-chris-zabriskie-chance-luck-finale`
- 내레이션: `youtube-jesse-gallagher-satya-yuga`
- 10분 초과: 분위기가 유사한 2~3곡 playlist 권장

## 믹싱·검수 기준

- BGM 기준 정규화: `-23 LUFS`
- 내레이션 없음: 기본 `+5dB`, 목표 약 `-18 LUFS`
- 내레이션 있음: 기본 `+3dB`, 음성 구간 자동 덕킹
- 기본 fade: in `1.8초`, out `2.0초`
- 기본 crossfade: `3.0초`
- 최종 True Peak: `-1dBTP` 이하
- BGM만 수정할 때: `bin/build.py ... --from mix --audit`
- project.yaml이 없는 대사 없는 완성 MP4의 BGM 교체:

  ```bash
  pipeline/.venv/bin/python bin/replace-bgm.py \
    --video output/input.mp4 --project-id <pid> \
    --asset-id youtube-chris-zabriskie-fight-for-your-honor \
    --out output/<pid>-bgm.mp4 --title "공개 제목" \
    --props data/<pid>/props.json --confirm-no-voice
  ```

  영상 stream hash 동일을 강제하고 표준 license manifest·mix report·audit·delivery 텍스트를 생성한다.

최종 자동 검수와 별도로 이어폰·노트북 스피커에서 내레이션 가독성, 펌핑,
곡 전환, 시작/종료의 자연스러움을 직접 청취한다.

## generated BGM 후보 (piano-bgm 스킬·기존 영상 공용 자동 BGM)

`piano-bgm`의 생성 BGM은 완성곡을 가져온 asset이 아니라, (1) Stable Audio 3 MLX `sm-music`이 만든
생성 후보 또는 (2) `bin/piano-bgm.py`가 로컬 Noct-Salamander CC BY 3.0 샘플을 새 score event로
연주한 **generated candidate**다. `output/original-audio/piano-bgm/<projectId>/generated-bgm-manifest.json`에
request·prompt·model·SHA-256과 사람 청취 상태를 기록한다. 일반 preview/build와 auditor에서는
`PENDING_USER_LISTENING` 후보를 사용할 수 있지만, `bin/build.py --final`은 명시적
`bgm.mode: piano-auto`와 manifest `APPROVED` 없이는 거부한다.

- `TECHNICAL_PASS`/`PENDING_USER_LISTENING`은 사람이 이어폰과 노트북 스피커에서 모두 승인하기 전의 중간 상태다.
- Noct 경로는 `provenance.json`의 request/score/performance/renderer/sample archive hash와 `youtube-description.txt`의 CC BY attribution·변경 고지를 보존한다.
- Stable Audio 경로는 model ID/bundle/runtime, prompt/negative prompt, cfg/steps/seconds/seed, 생성일,
  model/install version, WAV SHA-256, [model card](https://huggingface.co/stabilityai/stable-audio-3-optimized),
  [Stability AI License](https://stability.ai/license)를 보존한다.
- Stable Audio의 Community License 상업 사용 조건은 프로젝트 라이선스 승인과 별도이며, YouTube의 AI 공개·
  수익화·Content ID 정책을 함께 확인한다.
- 자동 생성 후보는 다음으로 청취 검토한다.

  ```bash
  pipeline/.venv/bin/python bin/piano-bgm.py review --project-id <projectId>
  pipeline/.venv/bin/python bin/piano-bgm.py approve --project-id <projectId> \
    --review-result output/original-audio/piano-bgm/<projectId>/listening-result.json
  ```
- 사람이 승인한 candidate도 전역 catalog에 자동 등록하지 않으며, 최종 `--final`은 명시적인 `piano-auto` 설정과 승인 manifest를 요구한다.
- shared sample source 기반 결과는 Content ID에 등록하지 않는다.

## 스킬별 적용 경계

`bin/build.py`를 공용 진입점으로 사용하는 `brush-video`, `full-color-motion-video`, `pen-video`,
`pen-brush-video`, `shorts-brush`, `dark-random-brush-video`, `storybook-full-touch-video`에
위 자동 정책을 적용한다. `seamless-short-video`(`bin/seamless-short.py`)와
`promo-widget-video`(독립 props/Remotion 라인)는 이 공용 BGM 자동화의 대상이 아니다.
`brush-director`는 `piano-auto`를 YAML에 제안할 수 있지만 직접 생성하지 않고, `brush-qa-review`와
`video-auditor`는 후보를 생성하지 않고 승인·기술 검수만 보조한다.
