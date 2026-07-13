# 로컬 전용 예제 에셋

이 저장소의 작은 기능 예제는 clone 직후 실행할 수 있다. 다만 아래 5개 장편·검증 프로젝트는
원본 이미지의 용량과 출처별 재배포 조건 때문에 `project.yaml`과 manifest만 추적하고 PNG는
의도적으로 Git에서 제외한다.

| 프로젝트 | 필요한 로컬 입력 | 준비 방법 |
| --- | --- | --- |
| `cosmic-random-brush` | `source.png` 1장 | 프로젝트 폴더에 1920×1080 이미지를 직접 배치 |
| `cosmic-random-brush-v02` | `assets/scene-01..06-*.png` | scene 01 원본을 먼저 배치한 뒤 `pipeline/.venv/bin/python scripts/prepare-cosmic-v02-assets.py` |
| `cosmic-random-brush-v03` | `assets/scene-01..60-*.png` | `pipeline/.venv/bin/python scripts/prepare-cosmic-v03-assets.py` |
| `cosmic-random-brush-v05-ink` | `cosmic-fullscreen-v05/assets-ink-v1/scene-01..60.png` | `prompts.json`으로 생성 후 `ingest-cosmic-v05-image.py`, 마지막에 `validate-cosmic-ink-assets.py` |
| `deepsea-light-v01` | `assets-ink-v1/scene-01..60.png` | `GENERATION-SPEC.md`에 맞춰 생성 후 `pipeline/.venv/bin/python scripts/qa_deepsea_assets.py` |

## 공개 저장소 계약

- 위 표의 프로젝트는 `local-assets-required` 예제다. 이미지가 없을 때 preflight 실패가 정상이다.
- 그 밖의 `examples/**/project.yaml`은 Git에 추적된 입력만 사용하며 clone 직후 preflight를 통과해야 한다.
- 새 로컬 전용 예제를 추가하면 이 문서와 `scripts/check-public-tree.py`의 허용 목록을 함께 갱신한다.
- NASA 등 외부 원본을 준비할 때 manifest의 출처·크레딧과 원본 제공자의 최신 이용 조건을 확인한다.
- 생성 이미지나 사용자 제공 이미지는 공개 저장소에 추가하기 전에 재배포 권한과 개인정보를 별도로 검토한다.

## 대표 self-contained 예제

다음 예제는 저장소에 포함된 프로젝트 소유 fixture를 사용하므로 추가 이미지 다운로드 없이
`project.yaml` preflight를 통과한다.

- `examples/pen-brush/project.yaml`
- `examples/pen-brush-shorts/project.yaml`
- `examples/pen-sync/project.yaml`
- `examples/voice-pack/female-08/project.yaml`

BGM asset 모드 예제는 이미지 preflight와 별개로, README의 절차에 따라 음원과 라이선스 증빙을
`local-assets/bgm/`에 등록해야 한다.
