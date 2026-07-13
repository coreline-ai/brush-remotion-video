# FIELD-LOG — 실전 제작 갭 환류 기록

실전으로 영상을 만들다 발견한 갭(품질 문제·불편·빠진 규칙)을 기록하는 로그다.
**핵심 규칙: 기록만 하고 끝내지 않는다 — 모든 항목은 반드시 "환류"(어느 문서/검증기/프리셋에 반영했는지)로 닫는다.**
같은 문제를 두 번 손으로 잡게 되면 이 로그가 실패한 것이다.

## 기록 시점

- brush-video / pen-video / brush-qa-review 스킬로 실전 영상을 만들다 갭을 발견했을 때
- 개발 워크스트림의 갭은 dev-plan 이슈란에 (여기는 **제작 경험** 전용)

## 항목 템플릿

```markdown
## YYYY-MM-DD · {projectId} ({프로파일/모드})
- **발견**: 무엇이 이상했나 (프레임/씬 번호 포함)
- **원인**: 왜 그랬나
- **수정**: 이번 건은 어떻게 고쳤나
- **환류** ★필수: 어느 문서/검증기/프리셋에 반영해 재발을 막았나 (경로 명시)
```

---

## 2026-07-11 · pen-ref-demo (pen 프로파일 검증 제작)

- **발견**: 완성 화면에서 원본 이미지의 좌우가 잘려 있음 (사용자 지적)
- **원인**: 배경 준비가 cover-fit(화면을 꽉 채우려 가장자리를 잘라내는 방식)이었음
- **수정**: contain-fit(전체 보존) + 종이색 패딩으로 재생성
- **환류**: `brushvid.background.separate_ink()`가 contain을 강제하도록 구현(잘림 구조적 방지) +
  `skill/pen-video/SKILL.md` 연출 규칙 3번("이미지 잘림 금지") + `background-prompt.md` ✒️ 섹션에 명시

## 2026-07-11 · city-watercolor-600s (brush · 구 시스템 이전 재렌더)

- **발견**: 씬 전환마다 점프컷 체감 (사용자 지적). 경계 프레임 diff 12~23% — 특히 어두운 씬(야경)일수록 심함
- **원인**: ① 구 props의 `outroWashOpacity 0.42`(순백까지 수렴 안 함) + `outroFadeFrames 10`(0.33초) ② outro를 순백으로 고치자 이번엔 중간 씬 prewash(0.34~0.44)가 첫 프레임에 즉시 켜지며 2차 점프
- **수정**: outro 0.92/18f 일괄 + **중간 씬 59개 prewash 해제**(첫 씬만 유지) → 전 경계 diff 2.7~5.3%
- **환류**: brush-video SKILL.md "문제 해결"에 전환 점프 처방 추가 + 구 시스템 프로젝트 이전 시 outro/prewash 교정을 변환 단계의 기본 절차로 (data/city-watercolor-600s/props.json이 변환 실례). intent-map의 "prewash는 첫 씬 전용" 관행이 실측으로 재확인됨

## 2026-07-11 · city-watercolor-600s (brush · develop "번쩍" 스파이크)

- **발견**: 그림이 선명해지는(develop) 순간 화면이 한 번 번쩍 튐 (사용자 지적). 연속 프레임 diff 실측 — 주변 0.7% 구간에서 develop 92% 통과 프레임만 2.97% 스파이크
- **원인**: RevealLayer가 develop ≥ 0.92에서 faint 스트로크 레이어를 조기 언마운트 → 합성 불투명도 0.98→0.92 순간 하락 후 재상승. 어두운 씬일수록 체감 큼 (참조 시스템에서 물려받은 최적화 임계)
- **수정**: 임계 0.92 → 0.999 (사실상 develop 완료 후에만 생략) + develop 마감을 pattern rect 대신 이미지 직접 렌더로 안정화. 스파이크 2.97% → 0.46% (구간 최대 0.94% = 정상 페이드 수준)
- **환류**: RevealLayer 코드 주석에 근거 명시(임의 하향 방지) + 골든 회귀 재검증 통과(최대 0.29%). "참조 시스템에서 채택한 값도 실측 스파이크가 확인되면 교정" 원칙 확인

## 2026-07-12 · pen-brush-demo (pen-brush · 둔탁한 최종 외곽선)

- **발견**: 초기 데모의 최종 선 두께가 원본 3.831px 대비 5.908px로 54.2% 증가해 화면이 답답해짐
- **원인**: Canny+dilation 추출선과 color 원본선이 최종 프레임에 동시에 합성됨
- **수정**: 팽창 없는 local-contrast outline으로 교체하고 paint 완료 직전 outline을 fade-out. 최종 3.827px(오차 0.104%)
- **환류**: `brushvid.layers`, `DrawingPhaseSchema/Layer`, `pen-brush-report.json` 수치 게이트,
  `skill/pen-brush-video/references/fidelity-contract.md`, background prompt에 재발 방지 규칙 반영

## 2026-07-12 · africa-pen-60 (pen · 60씬 — 씬 전환/완성 "번쩍" 종합 규명)

- **발견**: 씬 전환마다·완성(develop) 순간마다 번쩍임/어색함 (사용자 지적). 실측(`data/africa-pen-60/flash-analysis/`) —
  경계 59/59곳 전부 프레임 diff 급등 + develop 밝기 혹(hump) 60/60씬(luma +6, 최악 scene-34)
- **원인**: 단일 버그가 아니라 3계층 메커니즘 — ① 경계 잔상 하드컷: 오버랩 0 버트조인 구조에서 outro가 순수 종이 미도달
  (`outroWashOpacity 0.88` 잔상 + 오버레이 자체 알파 0.96~0.98 + interpolate 끝점 `duration` vs 마지막 프레임 `duration-1`)
  ② develop 교차합성 펄스: 동일 이미지 2레이어 상보 페이드의 알파 비가산 — 커버리지 `d + faint·(1-d)²`가
  faint 1.0일 때 중간에 0.75까지 꺼짐 ③ 병렬 Chromium 결손 프레임: SVG `<image>`가 delayRender 미연결 → decode 전 캡처
- **수정**: pen 프리셋 `completionMode: masked-hold`(펄스 0.0001로 소멸) + outro dissolve 12f +
  develop을 Remotion `<Img>`+명시 decode로 교체 + 레이어 상시 마운트(DOM 고정) → post-fix-qa 전 씬/경계 통과.
  경계 잔상 diff 8~10 잔존 — 근치(순백 수렴 1.0 또는 마지막 프레임 paper 단색 스냅)는 처방으로 문서화
- **환류** ★: 메커니즘 3종+완성 전 공통 체크를 **`skill/brush-video/references/transition-checklist.md`로 신설**하고
  제작 4스킬(brush-video·pen-video·shorts-brush·pen-brush-video) + qa-review 점검 항목 + video-auditor 해석 가이드에서
  공통 참조하도록 연결 — "전환/번쩍" 클래스 전체를 스킬 공통 체크 항목으로 표준화
- **실증 (2026-07-12 · city-watercolor-600s-final-v2 · brush 60씬)**: transition-checklist A계열 처방(전 씬 `outroWashOpacity 1.0`
  순백 수렴)을 교정판 렌더러(Img+decode·언마운트 제거)와 함께 재렌더 → **경계 하드컷 59건(최악 30.5%) → 0건,
  spike 14건 → 0건, auditor FAIL 59 → 0 (PASS)**. 오디오도 2-pass loudnorm으로 -27.8 → -18.0 LUFS 정규화.
  잔여 WARN 15건은 corr 1.00(구도 유지) develop/outro 워시 온셋으로 연출상 허용. "순백 수렴 1.0" 근치 처방 검증 완료

## 2026-07-12 · 공통 BGM (약한 음량·라이선스 증빙)

- **발견**: 기존 앰비언트 합성 BGM이 최종 peak `0.24`로 고정되어 체감 음량이 약하고,
  내레이션과 BGM을 별도 조절할 계약·덕킹·장시간 playlist가 없었음
- **원인**: `stage_mux`가 ambient 합성 또는 단일 voice 파일 중 하나만 직접 mux했고,
  loudness 정규화·gain/fade 설정·라이선스 카탈로그·Content ID 증빙 단계가 없었음
- **수정**: `bgm` 독립 YAML 계약, 로컬 catalog/import/preflight, `mix` 스테이지,
  -23 LUFS 기준 정규화 + 기본 +5/+3dB + sidechain ducking + 2~3곡 crossfade + -1dBTP limiter 추가
- **환류**: `brushvid.bgm`, `brushvid.mix`, `bin/bgm-assets.py`, video-auditor LUFS/True Peak/manifest 검사,
  `skill/brush-video/references/bgm-policy.md`, director/pen/pen-brush/shorts/QA 문서에 반영
- **실음원 검증**: Gentle 30초 `-18.23 LUFS / -2.45 dBTP`, Dreamcloud 30초
  `-18.54 LUFS / -5.80 dBTP`, 두 곡 610초 playlist `-17.98 LUFS / -1.19 dBTP`; 모두 auditor FAIL 0.
  짧은 10초 Dreamcloud는 인트로와 양끝 fade 비중 때문에 `-23.64 LUFS`로 낮아 30초 기본 데모로 교정함
- **실음원 덕킹**: Dreamcloud+65.2초 내레이션 master `-16.14 LUFS / -9.13 dBTP`, 음성 활성 구간
  `5.61dB` 감쇄, 비활성 구간 `0.33dB` 감쇄로 자연스러운 복귀 확인; auditor FAIL 0
- **성능 수정**: Remotion render/still이 매번 약 3.7GB 전체 `public/`을 복사하지 않고 props가 참조하는
  projectId·brush 자산만 scoped public으로 전달하도록 공통화
- **등록 UX·안전성**: `bgm-assets.py scan --attach`가 `~/Downloads`의 공식 Pixabay slug를 자동 대조해
  단일 일치 MP3만 연결한다. 빈 파일·손상 파일·확장자 위장·실제 비-MP3 코덱·무단 교체는 회귀 테스트로 거부한다
- **회귀 게이트**: Python 189건, TypeScript/Vitest 40건, typecheck·schema export·diff check 통과.
  기존 ambient synth도 `--from mix --audit` 재빌드해 FAIL 0을 확인함
- **장시간·덕킹 검증**: 실제 두 음원 30분 playlist가 `-18.0 LUFS / -1.24 dBTP`, 900초 전환
  `-29.45dB`, 최대 child RSS `59.58MB`로 PASS. 덕킹은 120ms 내 반응·600ms 뒤 복귀·경계 sample step `<0.03` 확인
- **기존 fixture 발견**: `narration-demo`는 이름과 달리 원래 음성 파일 없이 SRT만 있어 재빌드 후에도 전체 무음
  auditor FAIL 1이다. TTS/whisper/ambient legacy는 PASS했으며, 이 무음은 신규 BGM 회귀가 아니라 기존 예제 입력 한계로 기록함
- **사람 승인 UX**: `bgm-assets.py review`가 검증 영상 5종과 이어폰/노트북 스피커별 체크,
  판정·메모의 localStorage 보존, `bgm-listening-review.json` 내보내기를 제공한다. 다시 import할 때 5개 항목의
  두 환경·pass를 모두 검증하고 원본 SHA-256이 포함된 `listening-approval.json`만 기록해 수치 PASS와 사람 청취를 분리함
- **실음원 확대**: Pixabay URL의 `meditationspiritual-` prefix가 공식 MP3 파일명에서는 빠지는 규칙을
  자동 스캐너 alias로 반영해 Autumn·Quiet·Slow Boat·Summer Breeze·Ambient 003·Summer Rain 6곡을 추가 등록함
- **Quiet 최종 E2E**: 실제 TTS 내레이션 25초와 35초 BGM 복귀 구간을 가진 60초 영상으로 교정.
  `-18.17 LUFS / -1.60 dBTP`, 활성 `5.80dB`·비활성 `0.22dB` 감쇄, strict manifest, auditor FAIL 0
- **auditor 교정**: 긴 무음 감상 구간 때문에 전체 평균 덕킹이 낮아도 활성 구간 감쇄가 정상인 경우
  잘못 WARN하지 않도록 regionMetrics를 우선 판정하고 회귀 테스트를 추가함
- **최종 10곡 등록**: Ocean Choir(NaturesEye, `1079.208초`, 48kHz stereo)와 Digital Ambient
  (Amurich, `709.564초`, 44.1kHz stereo)를 추가해 `ready=10/10`. Digital의 초기 catalog 작가 오기를
  공식 페이지·파일명으로 발견해 Amurich로 교정했으며 믹스 중간 포맷은 기존대로 48kHz stereo로 통일함
- **완료 판정**: `bgm-assets.py gate` 현재 실측은 `assets 10/10 · E2E 4/4 · human false`.
  자동 게이트는 모두 통과했고 사람 청취 승인만 남았으며 `not-displayed`는 Content ID 미등록 보장이 아님

## 2026-07-12 · cosmic-random-brush-golden (우주 랜덤 브러시 · 골든 이관)

- **발견**: 승인 데모와 동일한 원본을 본선 파이프라인으로 렌더했는데 반투명 우주 이미지 바깥에 푸른 텍스처가 드러나 골든 프레임 차이가 커짐
- **원인**: 범용 user-images 배경 단계가 RGBA를 RGB로 변환하면서 alpha 0 픽셀에 숨어 있던 RGB 값을 화면에 노출함
- **수정**: 다크 우주 프로파일은 원본 alpha를 유지하고 완전 투명 픽셀의 RGB를 0으로 정규화한 뒤 본선 렌더에 전달함
- **환류** ★: `pipeline/brushvid/background.py`의 `compose_dark_rgba()`와
  `pipeline/tests/test_background.py` 회귀 테스트, `tests/golden/cosmic-random-brush/check.py` 2% 프레임 게이트에 반영
- **감사 해석**: video-auditor의 letterbox/pillarbox WARN 2건은 `data/cosmic-random-brush-golden/qa/contact-sheet.png`에서
  검정 밴드가 아닌 의도된 다크 우주 여백임을 확인해 허용함. FAIL은 0건이며 스킬 fidelity contract에 증거 확인 절차를 고정함

## 2026-07-12 · cosmic-random-brush-v02 (우주 랜덤 브러시 · 대표 6씬)

- **발견**: 전체 캔버스 mask coverage만으로는 토성처럼 가시 피사체 비율이 낮은 장면에서 실제 콘텐츠가 충분히 칠해졌는지 설명할 수 없었음
- **원인**: 기존 0.991 지표가 의도된 검은 우주 여백과 실제 피사체를 구분하지 않았음
- **수정**: alpha·명도·채도 기반 가시 콘텐츠 영역을 별도로 계산하고 6씬에서 content coverage 0.985를 hard gate로 추가함
- **환류** ★: `pipeline/brushvid/cosmic_random_routes.py`, `pipeline/brushvid/qa.py`,
  `pipeline/tests/test_cosmic_random_brush.py`, `tests/golden/cosmic-random-brush-v02/check.py`,
  `skill/cosmic-random-brush-video/references/fidelity-contract.md`에 반영함
- **감사 해석**: final auditor WARN 2건은 36프레임 contact sheet에서 검정 밴드가 아닌 다크 우주 여백으로 확인했으며,
  씬 경계 diff는 최대 1.55%로 PASS함

## 2026-07-12 · cosmic-random-brush-v03-60 (우주 랜덤 브러시 · 60씬 본편)

- **발견**: 60개 seed 중 보완 터치가 많은 씬은 기존 고정 속도에서 drawEnd 214f를 넘었고, 희소한 3단 강착원반 이미지는 content coverage 0.985를 통과하지 못함
- **원인**: 36 기본 터치 뒤 1~20개 보완 터치 수에 따라 타임라인 길이가 달라지고, 희소 피사체는 전체 캔버스 coverage와 가시 콘텐츠 coverage 차이가 커짐
- **수정**: geometry·폭·순서는 유지한 채 필요한 seed만 209.5f 이내로 균등 시간 압축하고, scene-52를 full-frame NASA PIA14730으로 교체함
- **검증**: 60/60 routes PASS, scene-01 골든 geometry 유지, 18,000f/600초 H.264/AAC, 180장 QA, 59개 경계 최대 diff 1.54%, video-auditor FAIL 0
- **환류** ★: `tests/golden/cosmic-random-brush-v03/`, `examples/cosmic-random-brush-v03/assets/manifest.json`, `skill/cosmic-random-brush-video/references/fidelity-contract.md`

## 2026-07-12 · city-watercolor-600s-final-fixed (저메모리 장시간 렌더 복구)

- **발견**: 가용 RAM 약 0.74GiB 환경에서 18,000f 단일 Remotion 렌더가 병렬 인코딩을 비활성화하고 JPEG 시퀀스 stitch로 폴백한 뒤, 마지막 단계에서 `element-%05d.jpeg` 없음으로 실패함
- **원인**: 1920×1080 병렬 인코딩 예상 메모리보다 가용 RAM이 작아 장시간 디스크 프레임 경로가 선택됐고, 단일 임시 작업 디렉터리에 18,000프레임을 의존해 전체 작업의 재개 단위가 없었음
- **수정**: 10씬/100초 무음 청크 6개를 독립 렌더하고 각 3,000f/100.000s를 검증한 뒤 H.264 stream-copy concat, -18 LUFS 오디오 mux, yuv420p/BT.709 표준화를 적용함
- **검증**: 최종 600.000s/18,000f, auditor PASS(FAIL 0), 59개 경계 최대 1.021%·평균 0.786%, -18.0 LUFS/-5.64 dBTP
- **환류** ★: `skill/brush-video/SKILL.md` 문제 해결에 저메모리 600초 청크 렌더·재개 절차를 추가하고 `data/city-watercolor-600s/FINAL-GENERATION-REPORT.md`에 실물 경로를 기록함

## 2026-07-12 · 자동 BGM 기본 정책 (대사 없으면 로컬 BGM 자동 부착)

- **발견**: 대사 없는 영상마다 `bgm:` 블록에 `assetId`를 손으로 넣어야 BGM이 붙어 반복 수작업이 많았다.
  잊으면 무음(구 legacy-synth)으로 나가 체감 품질이 낮았다
- **원인**: `stage_mix`가 `bgm` 블록이 없으면 무조건 legacy 경로(ambient→synth, 그 외 음성만)로만 분기했고,
  "대사 유무"를 기준으로 로컬 BGM을 자동 선택하는 정책이 없었다
- **수정**: `brushvid.bgm.select_auto_bgm(profile, fmt, duration_sec)` 결정적 정책 함수 추가 +
  `stage_mix`에서 `cfg.bgm is None and voice is None`(대사 없음)일 때 자동 선택→preflight→부착.
  대사 있으면 기존대로 음성 우선, `mode: off`는 명시적 무음, 자산 미준비 시 synth 폴백(빌드 실패 없음).
  시그니처는 명시 `cfg.bgm`만 반영해 캐시 안정성 유지(자동선택은 결정적이라 재현 가능)
- **환류** ★: `skill/brush-video/references/bgm-policy.md` §자동 BGM + `skill/brush-video/SKILL.md` BGM 소절에
  정책표 반영. 회귀 테스트 3건 추가(`test_build.py`: 정책 결정성·자동부착·synth폴백) — pytest 192건 통과.
  실카탈로그 5케이스(brush/pen/pen-brush/shorts/playlist) preflight가 실제 로컬 MP3로 해석됨을 E2E 확인.
  기존 동작 보존: 명시 `bgm`·음성 프로젝트·`mode: off`는 불변(테스트로 고정)

## 2026-07-12 · star-seed-fairy-tale-100s (storybook-full-touch-video · 정식 도입)

- **발견**: ① 이미지 생성기의 따뜻한 아이보리 종이 질감이 전체 콘텐츠로 검출되어 `full-bleed 이미지` 오류 발생
  ② 전역 TTS로는 10씬×10초와 문장 경계를 동시에 고정하기 어려움 ③ pen-brush 전용 `DrawingPhaseLayer`에 outro 워시가 없어
  9개 경계 중 FAIL 8건·최대 diff 22.09% 발생
- **원인**: 종이 채도가 콘텐츠 알파 임계값을 넘었고, 기본 cue grouping은 20문장을 10씬에 2개씩 고정하는 계약이 없었으며,
  outro 구현은 단일 `RevealLayer` 경로에만 존재해 2단계 drawing phases에 적용되지 않았음
- **수정**: 외곽 연결 종이를 `RGB(250,249,247)`로 정규화하는 공용 스크립트, 씬별 Supertonic 합성·10초 패딩·고정 scenes를
  만드는 공용 스크립트, `DrawingPhaseLayer` outro 18f/1.0 수렴을 추가. 최종 100.000초/3,000f, 경계 최대 4.48%,
  outline 0.9948~0.9967, paint 1.0, missing 0, auditor PASS 달성
- **환류** ★: `skill/storybook-full-touch-video/`를 정식 v0.1 스킬로 등록하고 `README.md` 카탈로그·워크플로·상세 소절,
  `bin/install-skills.sh`, `scripts/normalize-storybook-paper.py`, `scripts/prepare-storybook-full-touch.py`,
  `src/scene/DrawingPhaseLayer.tsx`, `tests/drawing-phase.test.ts`에 재발 방지 계약과 회귀 테스트를 반영함

## 2026-07-12 · 일반 brush no-pulse 완료 연출 + Honor BGM 본선화

- **발견**: 그림이 완성되는 약 20초 지점에서 동일 이미지의 완료 합성과 색 보정이 겹쳐 `연해짐 → 진해짐`이 느린 번쩍임·벌렁임처럼 보였다. 자동 선택 BGM은 실제 외부 asset을 사용해도 최종 audit에 manifest/mix-report가 전달되지 않는 우회도 있었다.
- **원인**: 일반 brush legacy 프리셋의 prewash와 불명시 color settle, 완료 시점 전후 상태를 보지 않는 start/mid/end QA, props 없는 일반 spike 규칙만으로는 1~2초 밝기 역전을 구분하지 못한 것이 결합됐다. 300f routes 중 늦은 stroke에서는 고정 36+18f가 12f hold와 충돌했다.
- **수정**: 가로 brush에만 명시적 integrated no-pulse 프리셋을 적용하고 opacity/brightness/scale/blur를 고정한 단일 reveal layer에서 saturation만 단조 증가시켰다. 실제 lastStrokeEnd 기준 36:18 타이밍을 쓰되 짧은 씬은 12:6까지 결정적으로 적응하고 불가능한 경우 사전 실패한다. phase-aware QA 6지점, completion-pulse auditor, schema drift gate를 추가했다. 자동 BGM audit는 실제 mix payload를 사용하도록 수정했다.
- **BGM 환류**: Honor 음원을 SHA-256·증빙·CC BY 4.0 attribution과 함께 정식 catalog에 등록했다. `bin/replace-bgm.py`가 대사 없는 완성 MP4의 video stream을 보존하며 공용 loudness/fade/mux/audit/delivery를 재사용하고 YouTube 제목·설명·표시 문구를 생성한다.
- **검증**: 현재 엔진 60씬을 6청크로 재렌더해 600.000초/18,000f/1920×1080/30fps/yuv420p/BT.709 limited/AAC 48kHz를 확인했다. 완료부 360장 60/60 PASS, auditor PASS(FAIL 0/WARN 1/INFO 79), 최대 완료 밝기 역전 0.45 luma, -18.0 LUFS/-3.35 dBTP다. BGM 전후 video stream SHA-256은 `ce6ea24c0c024f142750bfb68fa0df291c108d00802c98528b459bb609fc2235`로 동일하다.
- **회귀**: schema sync·typecheck·Vitest 44/44·pytest 209/209·cosmic golden 3종 PASS. 기존 output과 golden은 덮어쓰거나 갱신하지 않았다.
- **환류** ★: `brush-video` 전환/BGM 공통 참조, `qa-review`, `video-auditor`, director intent map, schema/pipeline/README, 실행 계획에 계약과 검증 경로를 동기화했다.

## 2026-07-13 · dark-random-brush-video (공통 다크 화면 스킬 정리)

- **발견**: `cosmic-random-brush-video`라는 이름은 우주 전용으로 보이지만 실제 승인 route는 심해·야간 등 어두운 16:9 이미지에도 재사용되고 있었다.
- **수정**: public skill을 `dark-random-brush-video`, YAML profile을 `dark-random-brush`로 이름 변경하고, 기존 `cosmic-random-brush` runtime key·golden fixture·report 파일명은 호환 유지했다.
- **통합 계약**: 풀 화면 `1920×1080/16:9/cover`·safe margin·crop 금지, `free-random-touch` 36+1~20 터치·230~365px·mask 0.991·visible content 0.985, 이동 중 mask 불변·seed 결정성, 다크 paper 대비, 60씬 18,000f segmented render/resume, BGM pre-roll 제거·즉시 fade·strict license, MP4 3프레임/씬 경계/auditor FAIL 0 검사를 공통 fidelity contract에 고정했다.
- **검증**: `test_project.py` + `test_build.py` 75 passed, 전체 `pipeline/tests` 268 passed, cosmic/deep-sea project preflight PASS, skill quick_validate PASS, install script `bash -n` 및 `git diff --check` PASS.
- **환류** ★: `skill/dark-random-brush-video/`, `pipeline/brushvid/project.py`, README·director·brush-video·BGM·pipeline/schema 문서, `dev-plan/implement_20260713_201628.md`에 동일 규칙을 반영했다.

## 2026-07-13 · Supertonic 여성 음성팩 10종 (공통 TTS 정식 편입)

- **발견**: F1~F5 이름과 데모 생성기 내부 조합만으로는 스킬별 추천 음색, 혼합 비율, 속도, 모델·스타일 버전을 프로젝트 산출물에서 재현하기 어려웠다. 알 수 없는 ID가 조용히 F1로 대체되면 결과 드리프트도 추적할 수 없었다.
- **수정**: `female-01`~`female-10` 공개 ID, `voicePackVersion: 1.0.0`, F1~F5 alias, M1~M5 native passthrough, `speed: 0.70~2.00`, catalog/style hash를 단일 카탈로그와 resolver로 구현했다. 빌드마다 `voice-manifest.json`에 요청/해석 ID, 구성, package/model, speed, 해시, AI 합성 고지를 기록하고 TTS cache signature에 포함했다.
- **검증**: 프리뷰 10/10이 44.1kHz mono·10.000초·clipped sample 0으로 PASS했다. `female-01/07/08/09` 대표 영상과 F1/M1 호환 영상 6/6이 video-auditor PASS·FAIL 0이었고 WAV 종료와 SRT 마지막 종료 오차는 최대 0.0003초였다.
- **환류** ★: `assets/voices/catalog.json`, `pipeline/brushvid/voice_presets.py`, `bin/voice-assets.py`, TTS/build/audit 테스트, `skill/_shared/references/supertonic-voice-catalog.md`, 기존 제작·director·QA 스킬, `dev-plan/implement_20260713_190836.md`에 동일 계약을 반영했다.

## 2026-07-13 · 스킬 9종 catalog·Claude/Codex 설치 정리 (회귀 0)

- **발견**: 프로젝트에는 정식 스킬이 9개였지만 목록은 README와 installer에 수동 중복됐고 `agents/openai.yaml`은 2/9만 존재했다. Claude에는 8개 현재 링크와 끊어진 cosmic legacy 링크가 남아 있었고 신규 dark 링크가 없었으며, Codex에는 프로젝트 스킬이 0개였다. 일부 구조 문서는 여전히 초기 `스킬 2종` 상태를 현재처럼 표시했다.
- **수정**: exact 9종 `skill/catalog.json`·JSON Schema와 `bin/skill-catalog.py validate/list/generate-readme/emit-install/check`를 추가하고 README 표를 결정적 생성 영역으로 전환했다. UI metadata를 9/9로 맞추고 installer에 `claude|codex|all`, dry-run, check, broken symlink 복구, 사용자 실체 경로 보호를 추가했다. 공통 YAML·전환·BGM·음성 계약은 `skill/_shared/references/`로 단일화하고 이전 경로에는 한 릴리스용 호환 문서를 남겼다.
- **설치 결과**: Claude/Codex 각각 catalog 9/9 symlink PASS, cosmic legacy symlink 제거, dark skill 설치를 확인했다. installer는 temp HOME 정상/broken/실체 충돌/재실행/dry-run 행렬을 통과했다.
- **회귀**: 신규 테스트 19건을 포함해 Python 287 passed, Vitest 47 passed, typecheck·schema sync·skill validator 9/9·Markdown/HTML 링크·`git diff --check` PASS. 작업 전 고정한 runtime/examples/golden/대표 MP4 517개 파일의 SHA-256 변경 0·누락 0을 확인했다.
- **잔여 수동 게이트**: BGM은 assets 13/13·E2E 4/4지만 `listening-approval.json`이 없어 human approval은 false다. 자동 PASS로 위장하지 않고 사람 청취 승인 과제로 유지한다.

## 2026-07-13 · Pixabay 음원 YouTube 사용 금지

- **정책**: Pixabay 음원은 YouTube 일반 영상과 YouTube Shorts의 신규 제작·BGM 교체·최종 배포에 사용하지 않는다. 로컬 청취·내부 데모·과거 회귀 검증용으로만 보존한다.
- **강제**: `format: youtube|shorts` 자동 BGM은 YouTube Audio Library/검증된 CC BY 자산으로 교체하고, 명시 Pixabay asset/playlist는 `licensePolicy: warn`이어도 preflight hard fail한다. `replace-bgm.py`도 동일하다.
- **감사**: 새 BGM manifest에 `distribution`을 기록하고 video-auditor는 `youtube|shorts + source: pixabay`를 `bgm-source-policy` FAIL로 판정한다.
- **문서 환류**: 공통 BGM/YAML 정책, director, brush, pen, pen-brush, shorts, dark, storybook, QA, auditor와 README/production lessons의 예제·규칙을 허용 음원 기준으로 맞췄다.
- **검증**: BGM/build/audit 집중 테스트 79 passed, Python 전체 293 passed, Vitest 47 passed, typecheck·schema sync·skill validator 9/9·Markdown 링크 missing 0을 확인했다. 현재 YouTube/Shorts project/example BGM 23건의 Pixabay 선택은 0건이다.
- **환류** ★: `skill/catalog.json`, `bin/skill-catalog.py`, `bin/install-skills.sh`, 9개 `agents/openai.yaml`, `docs/production-lessons.md`, README·시스템 구조 문서, `dev-plan/implement_20260713_202803.md`에 관리·설치·회귀 규칙을 고정했다.

## 2026-07-13 · Camera Prompt Interpreter (`brush-director` v1.1.0)

- **발견**: 사용자의 `당겨줘`, `뒤에서 따라가 줘`, `웅장하게 멀어져 줘` 같은 표현을 전문 카메라 언어로 바꾸는 공통 계약이 없었고, 원본 번호 37~45는 28~36과 중복되어 기법 수·명칭·타깃 지원 수준이 흔들릴 수 있었다.
- **수정**: 01~36·46의 37개 canonical technique과 37→28~45→36의 9개 legacy alias를 JSON catalog/schema로 단일화했다. `brush-director`를 v1.1.0으로 올려 카메라 의도가 있을 때만 구조화 해석·필수 슬롯·한/영 전문 prompt·negative prompt·4개 타깃 compatibility를 담은 Camera Prompt Pack을 출력하게 했다. primary 1개·secondary 최대 1개, zoom과 실제 카메라 이동 구분, 확인 질문 최대 2개, 선화·identity·제품 shape/logo·text 보존 규칙을 고정했다.
- **경계**: Camera Prompt Pack은 연출 브리프이며 `project.yaml`/render props가 아니다. 이번 편입은 `src/`, render schema, 실제 카메라 레이어나 특정 AI 영상 API를 추가하지 않았다. baseline 해시 대조 중 별도 동시 작업으로 보이는 untracked `pipeline/brushvid/fill_routes.py` 변경을 21:26에 감지해 되돌리지 않았고, 변경 후 전체 회귀를 다시 통과시켰다.
- **검증**: catalog `canonical=37, aliases=9`, 자연어 fixture 96건(37종×2, alias 9, 모호·충돌·혼용 12, 비카메라 1), 실패 주입 집중 테스트 18건 PASS. Python 전체 312 passed, Vitest 47 passed, typecheck·schema sync·skill catalog·skill validator 9/9·Markdown 40파일/상대 링크 126개/missing 0·HTML docs 2파일/anchor 18개/missing 0·`git diff --check` PASS.
- **환류** ★: `skill/_shared/references/camera-prompt-*`, `skill/director/`, `bin/camera-prompt-catalog.py`, `pipeline/tests/test_camera_prompt_catalog.py`, `docs/production-lessons.md`의 `PRM-001~006`, README, `dev-plan/implement_20260713_211157.md`에 같은 계약과 검증 절차를 반영했다.

## 2026-07-13 · EffectLayer 타이밍 — 골든 픽셀 사각지대 (회귀 감사 발견)

- **발견**: 커밋 전 회귀 감사에서, EffectLayer 통일 리팩터로 naturalEffects(mist 등)의 on 램프 start 가
  `penInvisibleAfter+8`(≈236) → `colorSettleEnd+8`(≈292)로 밀렸는데 off 램프는 `routesDuration-18`(=282)에서 0에 도달.
  golden-multi(mist)에서 onStart(292) ≥ offEnd(282)라 alpha 가 전 프레임 0 → 이펙트가 조용히 완전 소멸.
- **원인**: on/off 두 램프가 서로 다른 기준점(colorSettleEnd vs routesDuration)에 앵커돼 겹치지 않는 씬이 생김.
  골든 픽셀 diff(2% 임계)는 mist opacity 0.035 의 표시/소멸을 감지 못해(샘플 프레임 50/100 은 옛 코드에서도 mist 없는 구간)
  회귀를 통과시킴 — 저opacity 이펙트에 대한 픽셀 게이트의 구조적 사각지대.
- **수정**: 이펙트 소멸은 "outro 전 종료" 의도로 수용(코드 동작 유지). 대신 사각지대를 **타이밍 계약 단위 테스트**로 방어 —
  `EffectLayer.effectWindow()` 순수 함수 노출(동작 불변) + `tests/effect-layer.test.ts`로 램프 상수·가시 창 계약 고정.
- **환류** ★: 램프 공식이 바뀌면 vitest 가 즉시 실패해 의식적 갱신을 강제. "저opacity 이펙트는 골든 픽셀이 아니라
  타이밍 단위 테스트로 회귀 방어" 원칙 확립. 회귀 감사 워크플로(골든 실측 + blast-radius + 하위호환)가 픽셀 게이트가
  놓친 클래스를 잡아낸 사례.
