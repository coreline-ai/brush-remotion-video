# 빌드 파이프라인

`bin/build.py <project.yaml>` — 스테이지 순차 실행. 각 스테이지 산출물은 `data/{projectId}/stages/`에
기록(StageLedger)되어 `--from <stage>`로 실패 지점부터 재개할 수 있다.

## 스테이지

| # | 스테이지 | 모듈 | 입력 → 출력 |
|---|---|---|---|
| 1 | stt | brushvid.stt | 더빙 오디오 → whisper(small, ko) → SRT (audio만 있을 때) |
| 2 | cues | brushvid.cues | SRT → frame 환산 → 긴 문장 분할 → 씬 그룹핑 |
| 3 | background | brushvid.background | imagegen / preset(PIL, 결정적) / user-images → 씬별 PNG |
| 4 | clean | brushvid.background / layers | 종이색 키잉, pen-brush 레이어 분리, cosmic RGBA 무변형 보존 |
| 5 | routes | brushvid.routes / fill_routes / cosmic_random_routes | contour, 자동 존 paint, 또는 자유 랜덤 터치 routes와 커버리지 리포트 |
| 6 | sync | brushvid.sync | pen 존-cue 동기 또는 pen-brush phase 경계 스냅 |
| 7 | layout | brushvid.layout | 위젯 배치 검증 (겹침 hard-fail, 여백≥90px) — auto는 준비 중 |
| 8 | props | brushvid.props | render-props 조립 + JSON Schema 검증 |
| 9 | render | brushvid.render | npx remotion render (장편은 세그먼트 렌더+concat) |
| 10 | mix | brushvid.bgm / mix | 로컬 에셋 preflight → LUFS 정규화 → gain/fade/playlist/덕킹 → master.wav |
| 11 | mux | brushvid.render | master 오디오 AAC mux (props는 audio null로 렌더) |
| 12 | qa | brushvid.qa | 핵심 캡처·콘택트시트 + profile 수치 리포트. 일반 brush는 완료 phase 캡처와 completion-report 포함 |

## 모드

- **내레이션**: input.srt 제공 — SRT가 씬/자막의 시계
- **TTS**: input.script 또는 input.srt + input.tts — `female-01`~`female-10`과 호환 F1~F5/M1~M5, 실제 합성 길이가 시계. 설정은 `tts/voice-manifest.json`에 기록
- **whisper**: input.audio만 제공 — STT로 SRT 생성 후 내레이션과 동일
- **앰비언트**: 입력 없음 — 300f×N 고정 씬 + 합성 또는 로컬 BGM + 시적 cue

`bgm` 블록은 `input.audio`와 독립적이다. `off|synth|asset|playlist`를 지원하며 외부 음원은
렌더 전에 파일·SHA-256·곡 페이지/라이선스 증빙·Content ID 기록을 검사한다. `--from mix`는
영상 프레임을 다시 렌더하지 않고 오디오 이후만 재실행한다.
플레이리스트 원본 총 길이가 영상보다 짧으면 한 곡을 개별 loop하지 않고
`A → B → C → A` 순으로 전체 목록을 반복하며, 마지막 곡에서 첫 곡으로 돌아가는 경계에도
동일한 equal-power 크로스페이드를 적용한다.

자동 선택된 외부 BGM도 실제 mix stage payload를 기준으로 license manifest와 mix report를
`--audit`에 전달한다. project.yaml이 없는 대사 없는 완성 MP4는 `bin/replace-bgm.py`로
영상 stream-copy 상태에서 catalog BGM만 교체하고 audit/delivery 패키지를 생성한다.

오디오 길이와 씬 합산이 1초 이상 어긋나면 경고 후 자동 보정(reconcile_scenes_with_audio).

## E2E 예시 (전부 검증됨)

```bash
python3 bin/build.py examples/narration/project.yaml   # SRT 94항목 → 31씬 427s
python3 bin/build.py examples/whisper/project.yaml     # 음성 → 전사 → 10s
python3 bin/build.py examples/ambient/project.yaml     # 무입력 → 30s + BGM
python3 bin/bgm-assets.py status                       # 로컬 BGM 10개 상태
python3 bin/bgm-assets.py scan --attach                # ~/Downloads의 공식 파일명 자동 연결
python3 bin/bgm-assets.py dashboard                    # 브라우저형 진행도·청취 화면 생성
python3 bin/bgm-assets.py review                       # 환경별 사람 청취 승인 화면 생성
python3 bin/bgm-assets.py gate                         # 10곡·E2E·라이선스·사람 승인 최종 게이트
python3 bin/build.py examples/pen-brush-bgm/project.yaml --audit
python3 bin/build.py examples/cosmic-random-brush/project.yaml --audit
python3 bin/build.py examples/cosmic-random-brush-v02/project.yaml --audit
python3 bin/build.py examples/cosmic-random-brush-v03/project.yaml --audit
```

`dark-random-brush`(runtime 호환키 `cosmic-random-brush`) v0.3은 어두운 화면의 가로 1씬 골든, 대표 6씬, 본편 60씬을 지원한다. 기본 36터치 뒤
같은 붓 폭의 보완 터치를 추가하며, 20개 안에 전체 마스크 coverage 0.991을 달성하지 못하면
routes 단계에서 실패한다. 6/60씬 모드는 가시 콘텐츠 coverage 0.985도 QA hard gate로 검사한다.
60씬은 완성 MP4에서 씬별 핵심 3프레임을 추출해 180장 contact sheet를 만든다.
