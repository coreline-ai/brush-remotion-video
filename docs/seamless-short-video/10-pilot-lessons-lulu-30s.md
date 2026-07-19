# 10. 파일럿 교훈 — seamless-lulu-star-walk-30s

## 10.1 개요

| 항목 | 값 |
| --- | --- |
| projectId | `seamless-lulu-star-walk-30s` |
| 제목 | 별빛 루루의 첫 산책 |
| 구성 | 3 × 10s ≈ 30.1s, 720×1280, 9:16 |
| 생성기 | grok-imagine I2V, start lock: partial |
| 전환 | last_frame_match_cut + drop-last-frame |
| 대사/BGM | 없음 |
| 경로 | `projects/seamless-lulu-star-walk-30s/` |
| 산출 | `output/seamless-lulu-star-walk-30s.mp4` |

### 스토리 뼈대

1. 달빛 정원 소개·반딧불이 발견  
2. 돌길 추적  
3. 언덕·결말 hold  

---

## 10.2 통과한 것

| 항목 | 결과 |
| --- | --- |
| start sha == prev handoff | scene_02·03 **True** |
| duration ~10.04s ×3 | OK |
| handoff blur | 212 / 290 / 223 (min 40 상회) |
| CLI verify | PASS |
| concat | 30.1s 720×1280 |

→ **파일 인계 파이프라인 자체는 동작**.  
끊김은 “파일을 안 이어서”가 아니라 **I2V 재해석·동작 샘플링** 문제.

---

## 10.3 이슈 A — ~10s 밝기 점프

### 사용자 체감

10초 지점에서 화면 밝기가 바뀜. 마지막 이미지로 다음 영상을 만든 것 같은데 어색함.

### 실측 (mean luma Y, Rec.709)

| 비교 | A | B | Δ |
| --- | --- | --- | --- |
| S1 near-end vs S2 first | 112.0 | 123.5 | **+11.5** |
| S2 start/handoff vs S2 frame0 | 112.4 | 123.5 | **+11.1** |
| final t=9.95 vs t=10.05 | 112.7 | 123.5 | **+10.8** |

부가:

- S1 내부: first Y **90** → end **112** (후반 자체 밝아짐)  
- mean \|RGB\| start vs frame0 ≈ **11.4**  
- sky/ground 모두 +11~13 → 국소 버그가 아닌 **전체 재노출**

### 결론

```text
handoff 복사 성공 + I2V frame0 재조명 = 밝기 점프
```

### 환류 (문서·스킬)

- Look Lock 도입 ([04](04-look-lock-and-exposure.md))  
- frame0 ΔY/MAE hard gate  
- 후반 1s 노출 안정·bloom 금지  
- grade-match feather 후처리  
- generator `supports_exact_start_frame: partial` 명시  

---

## 10.4 이슈 B — ~20s 걷기 부자연

### 사용자 체감

20초 지점 보행이 부자연스러움.

### 실측

| 비교 | ΔY | mean\|RGB\| |
| --- | --- | --- |
| S2 near-end vs S3 first | **−1.0** | **2.9** |
| S3 start vs S3 frame0 | −0.8 | 2.3 |

→ 밝기 문제는 **아님**. 모션/보행 위상 불연속.

### 결론

```text
보행 중 handoff + 다음 씬 초반 새 연출 = 걸음 리셋
```

### 환류

- scene_end_type: hold / plant-feet 권장, walk peak 금지 ([05](05-motion-and-walk-handoff.md))  
- 0–2s overlap only, 문장 복붙  
- 걷기를 경계가 아닌 씬 내부에 배치하는 스토리 패턴  
- 편집 보조: 0.5s overlap, speed ramp  

---

## 10.5 일반화된 교훈

1. **세 인계(이미지·상태·동작)만으로는 부족** — frame0·노출·보행 위상이 네 번째 축.  
2. Hard gate를 “파일 존재/해시”에만 두면 사용자가 보는 점프를 못 막음.  
3. 같은 컷이어도 증상별로 처방이 갈림 (밝기 vs 모션).  
4. Exact match-cut + partial lock 생성기 = 재생성 예산(3~5 후보)이 운영 기본값.  
5. 데모 soft QA를 건너뛰면 파이프라인 PASS와 체감 FAIL이 어긋남.

### → 전 영상 공통 표준으로 고정

위 교훈의 **운영 규칙·처방 표**는 파일럿 전용이 아니라  
**[13-common-remediation-standard.md](13-common-remediation-standard.md)** 에 원인 클래스(C-EXP, C-MOT …)로 승격했다.  
이후 모든 seamless 영상은 13번 문서를 따른다.

---

## 10.6 리마스터 권장 순서 (이 프로젝트)

1. S2 재생성: Look Lock + frame0 게이트 (ΔY≤4)  
2. 통과 시 S2 handoff 재추출  
3. S2 엔딩 plant-feet/hold 로 재연출  
4. S3 0–2s overlap only 재생성  
5. verify + concat  
6. 필요 시 grade-match / 0.25s dissolve  

---

## 10.7 FIELD-LOG 환류 문안 (복붙용)

```markdown
## 2026-07-17 · seamless-lulu-star-walk-30s (seamless-short-video)
- **발견**: 10s 밝기 점프; 20s 보행 부자연
- **원인**: (10s) I2V frame0 재조명 ΔY≈+11, start 해시는 일치
           (20s) 보행 위상 리셋, 밝기 ΔY≈0
- **수정 방향**: Look Lock + frame0 gate + hold/plant-feet 인계
- **환류**: docs/seamless-short-video/04, 05, 08, 10 및 스킬 참조 갱신
```
