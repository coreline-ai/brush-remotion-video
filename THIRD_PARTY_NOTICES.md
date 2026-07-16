# Third-Party Notices

이 문서는 저장소가 참조하거나 생성에 사용하는 외부 구성요소와 에셋 계약을 안내한다.
프로젝트의 자체 저작물은 루트 [LICENSE](LICENSE)를 따르며, 아래 고지는 각 제3자 조건을
대체하거나 축소하지 않는다.

## Supertonic 3

- 공급자: Supertone Inc.
- 모델: `supertonic-3`
- 모델 라이선스: [BigScience Open RAIL-M](https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE)
- 모델 카드: [Supertone/supertonic-3](https://huggingface.co/Supertone/supertonic-3)
- SDK/샘플 코드: 공급자 저장소의 MIT 조건 참조

이 저장소는 Supertonic 모델 가중치를 재배포하지 않는다. 첫 실행 시 사용자의 로컬 캐시에
별도로 내려받는다. 다음 파일은 Supertonic 3으로 생성한 AI 합성 음성 fixture다.

- `assets/voices/previews/female-01.mp3` ~ `female-10.mp3`

공개 결과물에는 다음 고지를 유지한다.

> 이 콘텐츠의 내레이션은 Supertonic AI 합성 음성으로 제작되었습니다.

생성자와 배포자는 OpenRAIL-M의 사용 제한과 생성 결과에 대한 책임을 직접 확인해야 한다.

## MeloTTS-Korean

- 모델: `myshell-ai/MeloTTS-Korean`
- pinned revision: `0207e5adfc90129a51b6b03d89be6d84360ed323`
- 모델 라이선스: [MIT 모델 카드](https://huggingface.co/myshell-ai/MeloTTS-Korean)
- 패키지: `melotts` upstream commit `209145371cff8fc3bd60d7be902ea69cbdb7965a` (metadata `0.1.2`)

대상 adapter는 한국어 `KR` speaker가 없으면 중단하며 다른 speaker로 대체하지 않는다. 배포자는
MeloTTS와 모델 카드의 최신 조건을 다시 확인하고 다음 AI 고지를 유지한다.

> 이 콘텐츠의 내레이션은 MeloTTS-Korean AI 합성 음성으로 제작되었습니다.

## Qwen3-TTS Base

- 모델: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
- pinned revision: `fd4b254389122332181a7c3db7f27e918eec64e3`
- 모델 라이선스: [Apache-2.0 모델 카드](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base)
- 패키지: `qwen-tts==0.1.1`

Qwen reference cloning은 사용자가 권리를 확인한 audio/transcript pair만 사용한다. x-vector-only와
bundled reference fallback은 이 프로젝트에서 허용하지 않는다. reference 원본은 저장소에 넣지 않고,
manifest에는 voice ID와 audio/transcript SHA-256만 기록한다.

> 이 콘텐츠의 내레이션은 Qwen3-TTS Base AI 합성 음성으로 제작되었습니다.

## 합성 테스트 오디오

`examples/narration-bgm/voice-60s.mp3`, `examples/whisper/voice.mp3`,
`public/golden-multi/audio.wav`는 파이프라인 회귀를 위한 합성 테스트 fixture다. 최종 제작용
음원이나 실연자 음원으로 제공되는 파일이 아니며, 새 fixture는 생성 도구·음성·라이선스 정보를
manifest에 남긴 뒤 추가한다.

## BGM catalog

`assets/bgm/catalog.json`은 음원 식별자, 공식 출처, 라이선스, 해시와 attribution 문구를
기록하지만 원본 BGM 파일은 재배포하지 않는다. 원본과 증빙은 `.gitignore` 대상인
`local-assets/bgm/`에 사용자가 직접 등록한다.

- Pixabay 항목: 로컬 청취·내부 데모·과거 회귀 검증 전용. 이 프로젝트 정책상 YouTube와
  YouTube Shorts 제작·교체·배포에는 사용하지 않는다.
- Creative Commons Attribution 4.0 항목: 저작자, 출처, 라이선스 링크와 변경 사항을
  catalog의 `attributionText`에 따라 표시한다.
- YouTube Audio Library 항목: 다운로드 시점의 공식 항목 조건과 attribution 요구를 다시 확인한다.

정확한 운영 계약은 `skill/_shared/references/bgm-policy.md`를 따른다.

## NASA 및 외부 이미지 출처

장편 우주 예제의 manifest와 준비 스크립트는 NASA Image and Video Library 등 외부 출처를
가리킬 수 있다. 대용량 원본 이미지는 저장소에 포함하지 않는다. 사용자는 각 manifest의
credit, source page와 [NASA Images and Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)를
확인하고, 제3자가 별도로 표시된 자료의 조건도 개별 확인해야 한다.

`examples/cosmic-random-brush-v04/assets/manifest.json`에는 CC BY-NC-SA로 표시된 항목이
있으므로 상업 배포용 영상에서는 해당 원본을 자동 허용하지 않는다.

## 소프트웨어 의존성

Node.js 및 Python 의존성은 `package-lock.json`과 `pipeline/pyproject.toml`에 선언되며
설치 시 각 패키지의 자체 라이선스가 적용된다. `node_modules/`, Python 가상환경, Supertonic
모델 가중치는 이 저장소에 포함하지 않는다.

## 새 에셋 추가 규칙

1. 파일 출처, 제작자, 원본 URL, 다운로드 날짜와 SHA-256을 기록한다.
2. 재배포 가능한지 확인하기 전에는 `local-assets/`에만 둔다.
3. attribution 또는 AI 생성 고지가 필요하면 최종 영상 manifest와 게시 설명에 함께 기록한다.
4. 라이선스가 불명확하거나 조건이 충돌하면 공개·상업 배포를 중단한다.
