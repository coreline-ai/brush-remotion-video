# 빌드 파이프라인

`bin/build.py <project.yaml>` — 스테이지 순차 실행. 각 스테이지 산출물은 `data/{projectId}/stages/`에
기록(StageLedger)되어 `--from <stage>`로 실패 지점부터 재개할 수 있다.

## 스테이지

| # | 스테이지 | 모듈 | 입력 → 출력 |
|---|---|---|---|
| 1 | stt | brushvid.stt | 더빙 오디오 → whisper(small, ko) → SRT (audio만 있을 때) |
| 2 | cues | brushvid.cues | SRT → frame 환산 → 긴 문장 분할 → 씬 그룹핑 |
| 3 | background | brushvid.background | imagegen / preset(PIL, 결정적) / user-images → 씬별 PNG |
| 4 | clean | brushvid.background | 종이색 키잉 (빈 영역이 리빌되지 않게) |
| 5 | routes | brushvid.routes | mask→skeletonize→추적→RDP→seal → routes JSON (커버리지 리포트) |
| 6 | layout | brushvid.layout | 위젯 배치 검증 (겹침 hard-fail, 여백≥90px) — auto는 준비 중 |
| 7 | props | brushvid.props | render-props 조립 + JSON Schema 검증 |
| 8 | render | brushvid.render | npx remotion render (장편은 세그먼트 렌더+concat) |
| 9 | mux | brushvid.render | 오디오 ffmpeg 합성 (props는 audio null로 렌더) |
| 10 | qa | brushvid.qa | 씬별 캡처 → capture-manifest.json → 콘택트시트 |

## 모드

- **내레이션**: input.srt 제공 — SRT가 씬/자막의 시계
- **whisper**: input.audio만 제공 — STT로 SRT 생성 후 내레이션과 동일
- **앰비언트**: 입력 없음 — 300f×N 고정 씬 + BGM 합성(brushvid.audio, 시드 결정적) + 시적 cue

오디오 길이와 씬 합산이 1초 이상 어긋나면 경고 후 자동 보정(reconcile_scenes_with_audio).

## E2E 예시 (전부 검증됨)

```bash
python3 bin/build.py examples/narration/project.yaml   # SRT 94항목 → 31씬 427s
python3 bin/build.py examples/whisper/project.yaml     # 음성 → 전사 → 10s
python3 bin/build.py examples/ambient/project.yaml     # 무입력 → 30s + BGM
```
