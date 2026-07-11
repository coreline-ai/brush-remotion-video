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
├── capture-manifest.json   # [{sceneId, frame, file, note?}, ...]
├── contact-sheet.png       # 전 캡처 콘택트시트
└── *.png                   # 씬별 스틸
```

manifest가 없으면 먼저 생성한다:

```bash
cd /Users/hwanchoi/project_202606/brush_remotion_video
python3 bin/qa.py <projectId>              # 씬별 start/mid/end 기본 캡처
python3 bin/qa.py <projectId> --frames 120 240   # 특정 프레임 커스텀
```

## 리뷰 워크플로

1. contact-sheet.png와 캡처를 보고 씬별 이슈를 확인한다 — 점검 항목:
   - 드로잉: 커버리지 공백, develop 타이밍, 붓 커서 이상
   - 연출: 자막 싱크/겹침, topTitle 위치·색, 이펙트 과다
   - 위젯: 겹침, 자막 밴드 침범, 여백 <90px
2. 이슈를 **scene-fix-request JSON**으로 정리한다 — 스키마: [references/scene-fix-request-schema.md](references/scene-fix-request-schema.md)
3. 수정 적용: 이슈 유형에 따라 `data/{projectId}/props.json`(연출·위젯) 또는
   project.yaml(배경·씬 구성)을 고치고 해당 스테이지부터 재빌드:

   ```bash
   python3 bin/build.py <project.yaml> --from render   # props만 고쳤을 때
   python3 bin/build.py <project.yaml> --from routes   # 배경을 다시 그렸을 때
   ```

4. 재빌드 후 bin/qa.py를 다시 실행해 동일 프레임을 재캡처, 수정 전후를 비교한다.
