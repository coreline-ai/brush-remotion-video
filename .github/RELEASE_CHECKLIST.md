# v0.1.0 공개 릴리스 체크리스트

## 저장소 메타데이터

- Description: `project.yaml로 붓·펜 드로잉 영상, TTS, BGM 믹싱과 QA까지 자동화하는 Remotion 제작 시스템`
- Topics: `remotion`, `video-generation`, `drawing-animation`, `text-to-speech`, `video-qa`, `typescript`, `python`
- Default branch: `main`
- License display: custom proprietary license (`LICENSE`)

## 자동 게이트

- [ ] GitHub Actions `CI` 전체 PASS
- [ ] `python3 scripts/check-public-tree.py`
- [ ] `python3 bin/voice-assets.py validate`
- [ ] `python3 bin/skill-catalog.py check`
- [ ] `python3 bin/camera-prompt-catalog.py check`
- [ ] `npm run check-schema && npm run typecheck && npm test`
- [ ] `pipeline/.venv/bin/pytest -q`

## 수동 게이트

- [ ] BGM 이어폰 5항목 승인
- [ ] BGM 스피커 5항목 승인
- [ ] `python3 bin/bgm-assets.py gate` PASS
- [ ] 라이선스·제3자 notice 최종 소유자 검토
- [ ] 대표 pen-brush 영상과 음성 청취 페이지 확인

## 릴리스

- [ ] `CHANGELOG.md`의 `0.1.0` 내용 확인
- [ ] `v0.1.0` annotated tag 생성
- [ ] GitHub Release 생성
- [ ] 새 clone에서 Quick Start 실행
