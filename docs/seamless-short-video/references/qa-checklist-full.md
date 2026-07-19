# QA 체크리스트 (인쇄·복붙용)

프로젝트: ____________  씬: ____________  일시: ____________

## Hard (자동)

- [ ] start sha256 == prev handoff (N≥2)
- [ ] duration OK
- [ ] aspect/resolution OK
- [ ] handoff blur OK
- [ ] frame0 \|ΔY\| ≤ 4
- [ ] frame0 MAE ≤ 8

## Soft (사람)

- [ ] 얼굴 일관
- [ ] 의상·소품
- [ ] 포즈 연결
- [ ] 이동 방향
- [ ] 배경 연속
- [ ] 카메라 연속
- [ ] 신체 변형 없음
- [ ] 시작≈start_image
- [ ] 종료 안정 / 결말 hold
- [ ] 보행 위상 (해당 시)
- [ ] 노출 Look Lock

## 결정

- [ ] PASS  
- [ ] RETRY (횟수: __ / 3)  
- [ ] WAIVE (사유: ________________)

메모:
