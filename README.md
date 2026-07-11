# brush_remotion_video

화이트 종이 위에 붓이 그림을 그리는(수묵화 리빌) 영상을 **project.yaml 하나로** 자동 생성하는 독립 프로젝트.
new-video-gen의 브러시 기능을 이식한 것이 아니라, 그것을 스펙 참고로 삼아 **완전히 새로 만든** 시스템이다.

```bash
# 1. 설치
npm install
python3 -m venv pipeline/.venv && pipeline/.venv/bin/pip install -e "pipeline[dev]"

# 2. 빌드 — 이것 하나로 영상 완성
python3 bin/build.py examples/ambient/project.yaml
# → output/ambient-demo.mp4 + data/ambient-demo/qa/ (씬 캡처·콘택트시트)

# 3. QA
python3 bin/qa.py ambient-demo
```

## 구조

| 경로 | 역할 |
|---|---|
| `src/schema.ts` | ★ Zod 스키마 v1 = render-props의 유일한 진실 (`npm run export-schema`로 JSON Schema 내보내기) |
| `src/scene/` | BrushScene(조립) + Reveal·Cursor·Subtitle·Title·Effect·Widget 레이어 + SceneSequence |
| `src/lib/` | geometry·dynamics·easing — 순수 함수 (단위 테스트 대상) |
| `src/widgets/` | 단일 registry 핵심 15종 (CardShell + 파일당 1바디) |
| `pipeline/brushvid/` | routes 생성·배경·자막·레이아웃·props·렌더·QA 파이썬 모듈 |
| `bin/build.py` | ★ 단일 진입점 (스테이지 캐시 + `--from` 재개) |
| `skill/` | 얇은 스킬 2종 (코드 사본 0) — `bin/install-skills.sh`로 symlink 설치 |
| `tests/golden/` | 골든 스틸 회귀 게이트 (픽셀 diff ≤ 2%) |

## 검증

```bash
npm run typecheck && npm test                      # TS: vitest 28건
pipeline/.venv/bin/pytest pipeline/tests/          # Python: 43건
npx remotion render src/index.ts BrushLandscape output/golden-single.mp4 --props=data/golden-single/props.json
python3 tests/golden/diff.py --baseline tests/golden/baseline --candidate <스틸 폴더>
```

## 문서

- [docs/schema.md](docs/schema.md) — render-props v1 / routes JSON 스키마
- [docs/pipeline.md](docs/pipeline.md) — 빌드 스테이지와 모드
- [docs/impl-plan-brush-remotion-video.md](docs/impl-plan-brush-remotion-video.md) — 전체 설계 (Phase 0~6)
- `dev-plan/` — 워크스트림별 진행 기록
