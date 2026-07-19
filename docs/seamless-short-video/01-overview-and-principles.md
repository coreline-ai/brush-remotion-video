# 01. 개요와 원칙

## 1.1 목적

캐릭터와 이야기 콘셉트를 입력하면 약 30~60초 분량의 **연속형 숏폼**을 제작한다.

```text
캐릭터·스토리 입력
→ N초 스토리 구성 (기본 30s=3씬 또는 60s=6씬)
→ 10초 단위 장면 분할
→ 첫 장면 시작 이미지 생성
→ 10초 Image-to-Video 생성
→ 영상 마지막 정상 프레임 추출
→ 추출 프레임 = 다음 영상 시작 이미지
→ 반복
→ 연속성 QA → Match Cut 결합 → 편집 가이드
```

이 스킬의 핵심은 “예쁜 프롬프트 작성”이 아니라 **인계 규칙의 강제 관리**다.

## 1.2 brush_remotion_video와의 관계

| | seamless-short-video | brush / pen / storybook |
| --- | --- | --- |
| 엔진 | Image-to-Video 연쇄 | Remotion 프레임 합성 |
| 연속성 | last frame 픽셀 + 상태 + 동작 | 고정 소스 이미지·routes |
| 진입점 | `bin/seamless-short.py` | `bin/build.py` |
| 코드 공유 | 없음 (별도 제품 라인) | Remotion `src/` |

렌더러·drawing.profile에 억지로 합치지 않는다. 카탈로그상 **production / specialized** 형제 스킬로 둔다.

## 1.3 제작 원칙

### P1. Last Frame Handoff

장면마다 독립 이미지를 새로 만들어 I2V하지 않는다.  
Scene 1을 제외한 모든 장면의 start image는 **이전 영상의 Last Usable Frame**이다.

### P2. 이미지 단독 인계 금지

픽셀만 넘기면 부족하다. 반드시 함께 넘긴다.

1. 마지막 정상 프레임 이미지  
2. observed_end_state (자세·시선·카메라·조명·active_motion)  
3. 동작 진행 방향 (동작 Overlap)

### P3. Start image 제공 ≠ frame0 보장

I2V 모델은 입력 이미지를 **재조명·재구성**할 수 있다 (`supports_exact_start_frame: partial`).  
따라서 handoff 복사 성공만으로 연속성을 선언하지 않고, **생성 영상 frame0 vs start_image**를 측정 게이트로 검증한다.  
(파일럿: 10s 경계 meanY +11 — [10-pilot-lessons-lulu-30s.md](10-pilot-lessons-lulu-30s.md))

### P4. 순차 확정

처음부터 고정 프롬프트 N개를 확정하지 않는다.

```text
전체 계획 N씬 → Scene k 생성 → handoff·관측 → Scene k+1 프롬프트 확정 → …
```

QA 통과 전 다음 프롬프트 확정 금지. Completed scene은 immutable.

### P5. 반자동화 경계

- **자동:** 계획·프롬프트·handoff 추출·해시 검증·concat·리포트  
- **수동/외부:** I2V UI 업로드·생성·다운로드·소프트 QA 판정  
- **비포함(v1):** 브라우저 UI 자동화

### P6. 얇은 스킬

실행 코드는 리포 CLI에만 둔다. 스킬 폴더는 워크플로·계약 문서만 담는다 (코드 사본 0).  
본 `docs/seamless-short-video/`가 상세 사양의 원천이다.

## 1.4 v1 / v0.2 스코프

### 포함

- Character Lock + Look Lock  
- 3×10s(30s) 또는 6×10s(60s), 9:16  
- 6블록 프롬프트 + 노출/보행 강화  
- handoff CLI, verify, concat  
- Hard/Soft QA (frame0 노출 게이트 포함 — 구현 단계별)  
- Exact match-cut / 선택적 Smooth  
- silent visual (대사·BGM 후처리)

### 제외 (후속)

- 브라우저 자동화  
- 립싱크·본편 BGM 덕킹 통합  
- 다중 주연  
- Remotion drawing 연동  
- VLM 완전 자동 observed_end_state (반자동 권장)

## 1.5 기본값

| 항목 | 기본 |
| --- | --- |
| 전체 길이 | 30초 (데모) / 요청 시 60초 |
| 장면 수 | 3 또는 6 |
| 장면 길이 | 10초 |
| 화면비 | 9:16 |
| 전환 | `last_frame_match_cut` |
| 대사 | 없음 |
| 주연 | 1명 |
| 재시도 | 장면당 최대 3 |

입력 부족 시 임의 확장하지 않고 보수 기본값을 적용한 뒤 **가정을 명시**한다.
