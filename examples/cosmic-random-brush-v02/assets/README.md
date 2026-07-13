# cosmic-random-brush v0.2 validation assets

대표 6씬에서 같은 브러싱 계약을 검증하기 위한 프로젝트 로컬 입력 이미지다.

- `scene-01`은 v0.1 승인 source의 byte-identical 사본이다.
- `scene-02..06`은 NASA Image and Video Library 원본을 1920×1080으로 비파괴 리샘플링했다.
- 장면 제목, NASA ID, 원본 URL, 크레딧, 원본/정규화 SHA-256은 `manifest.json`에 있다.
- 이 검증본은 NASA의 검토·승인·보증을 의미하지 않는다.
- 공개 또는 상업 배포 전 [NASA Images and Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)와 원본별 제3자 크레딧을 다시 확인한다.

재생성:

```bash
pipeline/.venv/bin/python scripts/prepare-cosmic-v02-assets.py
```
