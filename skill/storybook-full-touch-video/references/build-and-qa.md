# 빌드·QA 계약

## 1. 스테이지

```text
story/SRT/images
  → normalize paper
  → scene-fixed Supertonic TTS
  → clean
  → outline/paint routes
  → cue sync
  → props
  → Remotion render
  → BGM ducking/mux
  → QA contact sheet
  → independent video audit
```

## 2. 펜·브러시 기본 타임라인

10초 씬 기준:

| 구간 | 역할 |
|---|---|
| 0.0–0.4초 | 종이·첫 호흡 |
| 0.4–약 4초 | 얇은 펜 외곽선 |
| 약 4초 | 펜→브러시 핸드오프 |
| 약 4–8.8초 | 채색 |
| 약 8.8–9.4초 | 완성 감상 |
| 마지막 18프레임 | 종이 워시 전환 |

펜 좌표와 outline reveal, 브러시 좌표와 paint reveal은 각각 같은 진행률을 사용한다.

## 3. 전환 계약

- pen-brush도 다른 프로파일과 동일하게 마지막 실재 프레임에서 종이 워시로 수렴해야 한다.
- `DrawingPhaseLayer`가 `outroFadeFrames`, `outroWashOpacity`, `outroBlur`를 적용해야 한다.
- 권장: `outroFadeFrames=18`, `outroWashOpacity=1.0`.
- 다음 씬 첫 프레임은 종이 화면이어야 한다.
- 경계 diff는 WARN 기준 6% 미만을 목표로 한다.

## 4. 이미지/경로 QA

| 지표 | 통과 기준 |
|---|---:|
| outline coverage | ≥ 0.99 |
| paint coverage | ≥ 0.9999 |
| paint missing pixels | 0 |
| color leak at outline end | 0 |
| cursor overlap frames | 0 |
| phase timing valid | true |
| 최종 선 두께 변화 | 허용 범위 내 |

## 5. 최종 영상 QA

| 항목 | 기본 기준 |
|---|---|
| Shorts 규격 | 1080×1920 |
| FPS | 30 |
| 100초 프레임 | 3,000 |
| 비디오/오디오 | H.264 + AAC |
| Integrated loudness | 약 -16 LUFS |
| True Peak | ≤ -1 dBTP 권장 |
| 씬 경계 diff | < 6% |
| audit | FAIL 0 |

## 6. 실패와 복구

| 증상 | 원인 | 조치 |
|---|---|---|
| `full-bleed 이미지` | 노란 종이·질감이 전체 콘텐츠로 검출 | 종이 정규화 후 `--from clean` |
| 캐릭터가 작거나 잘림 | 다른 화면비 원본 재사용 | 네이티브 화면비로 재생성 |
| 20개의 씬이 생김 | 문장 cue를 그대로 장면화 | 고정 씬 준비 스크립트 실행 |
| 음성이 씬을 넘김 | 전역 TTS/전역 속도 보정 | 씬별 합성·패딩 |
| 마지막에 이미지 팝업 | 최종 bitmap patch 사용 | patch 제거, route coverage 보완 |
| 씬 경계 하드컷 | pen-brush outro 미적용 또는 불완전 워시 | DrawingPhaseLayer outro 확인, 18f/1.0 |
| 채색 누락 | paper mask/paint route 불완전 | 종이 정규화 후 routes 재생성 |
| BGM이 대사를 덮음 | 덕킹 미적용 | 10dB, attack 100ms, release 500ms |
| Content ID 경고 | 라이선스와 플랫폼 등록은 별개 | 매니페스트 보존, 게시 전 확인 |

## 7. 검증 명령

```bash
npm test -- --run tests/drawing-phase.test.ts
npm run typecheck

pipeline/.venv/bin/python bin/build.py \
  projects/<project-id>/project.yaml --audit

ffprobe -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,r_frame_rate,nb_frames \
  -of json output/<project-id>.mp4
```

## 8. 전달물

- `output/<project-id>.mp4`
- `projects/<project-id>/contact-sheet.png`
- `data/<project-id>/qa/gallery.html`
- `projects/<project-id>/subtitles.srt`
- `data/<project-id>/audit/audit-report.md`
- 로컬에서는 MP4와 콘택트시트의 직접 실행 링크를 제공한다.

