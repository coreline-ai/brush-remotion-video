# scene_end_type 예시

## hold (권장 인계)

```yaml
scene_end_type: hold
body_pose: 양발 착지, 상체 안정, 시선 목표 고정
active_motion: 거의 정지 (호흡·미세 흔들림만)
camera_motion: settle / 정지
```

프롬프트 말미:

```text
Final 0.5s: hold a clear stable pose, face visible, no walk cycle,
no fade, exposure unchanged.
```

## plant-feet

```yaml
scene_end_type: plant-feet
body_pose: 무게 이동 완료, 다음 한 보 직전
active_motion: 정지에 가까운 준비
```

## gesture

```yaml
scene_end_type: gesture
body_pose: 발 고정, 한 손 소폭 이동 후 안정
```

## walk (경계 비권장)

```yaml
scene_end_type: walk
# 가능하면 씬 내부에서만 사용. 경계 handoff는 hold/plant-feet로 바꿀 것.
```
