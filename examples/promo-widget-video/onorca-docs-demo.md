# Orca Docs Promo Demo

`onorca-docs-demo.json`은 `promo-widget-video`의 `PromoScene`용 30초 데모 props다.

- 내용 근거: <https://www.onorca.dev/docs>, 2026-07-19 확인.
- 화면·로고·문구를 복제하지 않았으며, 공개 문서의 기능 흐름을 독립적인 모션그래픽으로 요약한다.
- 화면: `promo-widget-video`의 `heroTitle`, `nodeGraph`, `flowDiagram`, `terminal`, `checklistPanel`, `marquee` 등을 사용한다.
- 오디오: `../piano-bgm/onorca-docs-focus-30s.yaml`로 `piano-bgm`의 로컬 피아노 BGM을 만든다.

## 재현

```bash
# 1. 30초 Full-HD 무음 렌더
npx remotion render src/index.ts PromoScene output/onorca-docs-demo/onorca-docs-demo.mp4 \
  --props=examples/promo-widget-video/onorca-docs-demo.json \
  --public-dir=output/onorca-docs-demo/empty-public --codec=h264 --crf=18 --muted

# 2. piano-bgm의 master-48k24.wav를 영상에 AAC로 결합
ffmpeg -y -i output/onorca-docs-demo/onorca-docs-demo.mp4 \
  -i output/onorca-docs-demo/piano-output/onorca-docs-focus-30s/master-48k24.wav \
  -filter:a 'volume=0.65,afade=t=in:st=0:d=0.8,afade=t=out:st=28.8:d=1.2' \
  -c:v copy -c:a aac -b:a 192k -shortest output/onorca-docs-demo/onorca-docs-demo-final.mp4
```

`piano-bgm` 출력의 `qa.json`은 기술 검증 후에도 사람 청취 승인을 별도로 요구한다.

이 데모는 Orca 또는 Lovecast Inc.의 공식 광고물이 아니다.
