# brushvid 파이프라인

이미지 1장을 **routes JSON**(붓 드로잉 스트로크)과 **스키마 검증된 render-props**로 변환하는
Python 패키지. Remotion 렌더(`src/`)와의 접점은 `schema/render-props.schema.json`과
routes JSON 포맷뿐이다.

## 부트스트랩

```bash
cd pipeline
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## 테스트

```bash
.venv/bin/pytest tests/ -v
```

## 모듈

| 모듈 | 책임 |
| --- | --- |
| `brushvid/routes.py` | 이미지 → content mask → skeletonize → 폴리라인 추적 → RDP → seal 밴드 → 타이밍 → routes JSON (+커버리지) |
| `brushvid/background.py` | 배경 생성 전략 3종(imagegen/preset/user-images) + `clean()` 종이색 키잉 |
| `brushvid/layout.py` | 빈 영역 탐지, 위젯 자동 배치, 겹침 검증(UI 겹침 hard-fail) |
| `brushvid/cues.py` | SRT 파싱→frame 환산, 긴 문장 분할, 씬 그룹핑, `title_color()` |
| `brushvid/props.py` | render-props 빌더 + `schema/render-props.schema.json` jsonschema 검증 |
| `brushvid/render.py` | `npx remotion render` 호출, 세그먼트 concat, ffmpeg 오디오 mux |
| `brushvid/qa.py` | 프레임 캡처 → `capture-manifest.json` → 콘택트시트 |
| `brushvid/project.py` | project.yaml 로드/검증 + 모드 판정 (narration/whisper/ambient) |
| `brushvid/stt.py` | 더빙 오디오 → 로컬 whisper(small, ko) → SRT |
| `brushvid/audio.py` | 앰비언트 BGM 합성(numpy/wave) + 오디오-씬 길이 정합 |

## SRT-first 자동화 (bin/build.py)

`project.yaml` 하나로 완성 mp4 를 만든다. 스테이지 캐시(`data/{pid}/stages/`)와
`--from <stage>` 재개를 지원한다.

```bash
pipeline/.venv/bin/python bin/build.py examples/narration/project.yaml   # SRT 제공
pipeline/.venv/bin/python bin/build.py examples/whisper/project.yaml     # audio만 → whisper
pipeline/.venv/bin/python bin/build.py examples/ambient/project.yaml     # 입력 없음 → 앰비언트
pipeline/.venv/bin/python bin/build.py examples/ambient/project.yaml --from render  # 재개
pipeline/.venv/bin/python bin/qa.py examples/ambient/project.yaml        # QA 단독 재실행
```

## 사용 예 (routes 생성 → props → 렌더)

```python
from brushvid.routes import RouteParams, generate_routes, write_routes
from brushvid.props import build_scene, build_props, validate_props, write_props
from brushvid.render import render

data = generate_routes("public/my-proj/composed.png",
                       RouteParams(duration=300, draw_start=8, draw_end=220,
                                   pen_invisible_after=228, seed=1))
write_routes(data, "public/my-proj/routes.json")

props = build_props("my-proj", [build_scene("scene-01", "my-proj/routes.json", 300)])
validate_props(props)
write_props(props, "data/my-proj/props.json")

render("data/my-proj/props.json", "output/my-proj.mp4")
```

routes JSON 포맷(기존 호환):
`{meta: {image, width, height, fps, durationInFrames, drawStart, drawEnd, penInvisibleAfter, routeCount, ...}, strokes: [{id, kind, width, start, end, points: [[x, y], ...]}]}`
