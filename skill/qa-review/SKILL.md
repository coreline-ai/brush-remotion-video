---
name: brush-qa-review
description: >-
  brush_remotion_video로 만든 영상의 씬별 QA 리뷰 스킬. bin/qa.py가 생성한
  capture-manifest.json + 씬 캡처를 근거로 씬별 이슈를 정리하고,
  scene-fix-request JSON과 수정 실행(해당 스테이지 재빌드)까지 잇는다.
  구 scene-qa-json-builder의 후속 — 스코프가 new-video-gen이 아니라 이 리포다.
---

# brush-qa-review — 씬별 QA 리뷰 & 수정 요청

**실행 대상 리포**: `/Users/hwanchoi/project_202606/brush_remotion_video`
이 스킬은 코드를 내장하지 않는다. QA 산출물의 계약(capture-manifest)만 정의한다.

## 입력 계약 (bin/qa.py 산출물)

```
data/{projectId}/qa/
├── capture-manifest.json   # {projectId, props, captures: [{frame, file, label}]}
├── contact-sheet.png       # 전 캡처 콘택트시트
├── gallery.html            # 씬 갤러리 카드뷰 (캡처+메타+수정 체크박스)
└── *.png                   # 씬별 스틸
```

manifest가 없으면 먼저 생성한다:

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
python3 bin/qa.py <projectId>              # 씬별 start/mid/end 기본 캡처
python3 bin/qa.py <projectId> --frames 120 240   # 특정 프레임 커스텀
```

## 리뷰 워크플로

0. **gallery.html을 브라우저로 연다** (상대경로라 폴더째 옮겨도 열림) —
   씬 카드에서 캡처를 클릭해 확대 확인하고, 이슈 유형(드로잉/자막/타이틀/위젯/오디오)을
   체크 + 메모 입력 후 상단 버튼으로 **scene-fix-request JSON 초안을 복사**한다.
   초안의 severity/fix 필드는 스키마 문서를 참고해 다듬는다.
1. (수동 검토 시) contact-sheet.png와 캡처를 보고 씬별 이슈를 확인한다 — 점검 항목:
   - 드로잉: 커버리지 공백, develop 타이밍, 붓 커서 이상
   - 연출: 자막 싱크/겹침, topTitle 위치·색, 이펙트 과다
   - 위젯: 겹침, 자막 밴드 침범, 여백 <90px
   - 전환/완성: 씬 경계 잔상 하드컷, develop 밝기 펄스, 결손 프레임 —
     메커니즘·처방은 [transition-checklist](../_shared/references/transition-checklist.md)
     (씬 end 캡처와 다음 씬 start 캡처를 나란히 비교하면 A계열이 보인다)
     일반 brush는 고정 mid/end 대신 draw-end·develop-end·settle-end·hold 캡처와
     `completion-report.json`의 luma/saturation 단조성도 함께 확인한다.
   - 오디오: 이어폰·노트북 스피커에서 내레이션 가독성, BGM 과소/과다, 덕킹 펌핑,
     페이드 시작/종료, playlist 전환의 무음 틈·클릭을 직접 청취한다.
     `format: youtube|shorts`의 license manifest에 `source: pixabay`가 있으면 즉시 FAIL하고 업로드를 보류한다.
   - TTS: `data/{projectId}/tts/voice-manifest.json`의 canonical ID, pack/package/model,
     components, speed, catalog/style SHA-256, AI 합성 음성 고지를 확인한다.
2. 이슈를 **scene-fix-request JSON**으로 정리한다 — 스키마: [references/scene-fix-request-schema.md](references/scene-fix-request-schema.md)
3. 수정 적용: 이슈 유형에 따라 `data/{projectId}/props.json`(연출·위젯) 또는
   project.yaml(배경·씬 구성)을 고치고 해당 스테이지부터 재빌드:

   ```bash
   python3 bin/build.py <project.yaml> --from render   # props만 고쳤을 때
   python3 bin/build.py <project.yaml> --from routes   # 배경을 다시 그렸을 때
   python3 bin/build.py <project.yaml> --from mix --audit  # BGM·덕킹만 고쳤을 때
   ```

4. 재빌드 후 bin/qa.py를 다시 실행해 동일 프레임을 재캡처, 수정 전후를 비교한다.
5. 리뷰에서 **반복될 수 있는 갭**(규칙 부재·프리셋 결함)이 보이면 `FIELD-LOG.md`에 기록하고
   해당 문서/검증기에 환류한다 — 같은 지적을 두 번 하지 않기 위한 규칙.
