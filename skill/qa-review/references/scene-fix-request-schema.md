# scene-fix-request JSON 스키마

씬별 수정 요청을 구조화하는 포맷. 리뷰 결과를 이 형태로 저장하면(`data/{projectId}/qa/fix-request.json`)
다음 세션/에이전트가 그대로 수정을 실행할 수 있다.

```json
{
  "projectId": "my-video",
  "reviewedAt": "2026-07-11",
  "scenes": [
    {
      "sceneId": "scene-03",
      "issues": [
        {
          "kind": "subtitle",
          "severity": "high",
          "frame": 420,
          "problem": "자막이 배경 그림의 핵심 소재를 가림",
          "fix": "subtitleStyle.bottom을 42→28로 낮추거나 maxWidth 축소"
        }
      ]
    }
  ]
}
```

## 필드

- `kind`: `drawing`(리빌/커버리지) | `develop`(발현 타이밍) | `cursor`(붓) | `subtitle` | `title` | `effect` | `widget` | `audio` | `background`
- `severity`: `high`(재빌드 필수) | `mid`(권장) | `low`(선택)
- `frame`: 이슈가 보이는 프레임 (캡처와 대조용)
- `problem` / `fix`: 문제와 수정 방법 — fix는 props/yaml의 **구체 필드 경로**로 쓴다

## kind → 수정 위치 매핑

| kind | 수정 파일 | 재빌드 스테이지 |
|---|---|---|
| drawing, develop, cursor | props의 씬 리빌 필드 (faint/edgeFeather/developFrames/brushDynamics) | `--from render` |
| subtitle, title, effect, widget | props의 cues/topTitle/naturalEffects/widgets | `--from render` |
| background | project.yaml background 또는 배경 이미지 | `--from background` |
| audio | project.yaml input 또는 오디오 파일 | `--from mux` |
