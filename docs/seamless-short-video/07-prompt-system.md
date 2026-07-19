# 07. 프롬프트 시스템

## 7.1 여섯 블록 (기본)

각 장면 영상 프롬프트는 다음 순서로 생성한다.

| # | 블록 | 목적 |
| --- | --- | --- |
| 1 | 입력 이미지 유지 + **노출 고정** | frame0 lock |
| 2 | Character Lock + Look Lock | 외형·조명 불변 |
| 3 | 이전 observed_end_state | 자세·동작 인계 |
| 4 | 현재 0~10s 타임라인 | 행동 (0~2s는 overlap only) |
| 5 | 인계 목표 또는 결말 hold | scene_end_type |
| 6 | Negative | 재디자인·텔레포트·페이드·relight 금지 |

언어: 생성기 기본이 EN이면 EN 본문 + KO 요약 병기. 고유명사·의상 색 고정.

---

## 7.2 블록 템플릿

### 1) Start frame + exposure

```text
Use the provided input image as the EXACT first frame.
Do not redesign character, outfit, background layout, or camera on frame 0.
Frame 0 MUST match the input in lighting, exposure, white balance, and brightness.
Do not re-light or brighten. Begin motion only after frame 0.
The input is not a loose reference — it is the precise opening frame.
```

### 2) Character + Look (매 씬 동일)

```text
[Character Lock 전문 또는 압축]
[Look Lock 전문 또는 압축]
```

### 3) Handoff state

```text
Continue from this exact state:
- position / facing / gaze / pose / hands / expression
- camera + camera_motion (same as previous end)
- lighting + exposure_notes
- active_motion: ...
```

### 4) Timeline

```text
0–2s: ONLY continue active_motion (no new story beat).
2–7s: main action (single motor skill).
7–9s: prepare handoff; stabilize camera and exposure; no new lights.
9–10s: settle into scene_end_type pose (hold | plant-feet | gesture).
        Clear face, no blur, no fade, no bloom ramp.
```

마지막 씬:

```text
7–10s: emotional ending hold 1–2s. No next-scene handoff requirement.
```

### 5) Handoff goal

```text
Final frame: stable, face visible, scene_end_type={hold|plant-feet|...},
camera settled, exposure same as Look Lock, no fade-out.
```

### 6) Negative

```text
character redesign, face morph, outfit change, extra characters,
teleport, hard cut, whip pan, fade out, end-frame blur,
relight, auto-exposure, HDR boost, bloom spike,
text, subtitles, logo
```

---

## 7.3 짧은 I2V 한 줄 (도구 제한 시)

```text
Same character continues [active_motion], then [main action],
camera [same move], lighting unchanged, ends in a stable [hold/plant-feet]
ready for the next shot. No cut, no redesign, no relight.
```

---

## 7.4 Scene 01 이미지 프롬프트 요령

- 9:16 구도 명시  
- Character Lock 반영  
- Look Lock 노출  
- 전신/얼굴 명확, 여백  
- 텍스트·워터마크 금지  
- 이후 I2V에 유리한 **단순한 실루엣** (과도한 잔무늬 지양)

---

## 7.5 실패 시 프롬프트 수정 방향

| 증상 | 수정 |
| --- | --- |
| 얼굴 변화 | 동작 단순화, 새 외형 서술 금지, lock 강화 |
| 배경 점프 | 배경 구조 명시, “new place” 제거, 이동 과정 삽입 |
| frame0부터 화면 변경 | 블록1 강화, relight 금지 |
| 동작 끊김 | 0–2s에 이전 active_motion 복붙 |
| 말미 불안정 | 마지막 1초 큰 동작 제거, 0.5s hold, 페이드 금지 |
| 밝기 점프 | Look Lock, frame0 문장, 후반 bloom 금지 |
| 보행 어색 | hold/plant-feet 인계, walk peak 금지 |

전체 playbook: [11-failure-playbook.md](11-failure-playbook.md).
