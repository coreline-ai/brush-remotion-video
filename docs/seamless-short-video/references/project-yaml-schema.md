# project.yaml 필드 레퍼런스 (초안)

기계 검증 초안: [`schema/seamless-project.schema.json`](../../../schema/seamless-project.schema.json)  
(additionalProperties 허용 — 운영 중 필드 확장 여유)

## project

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | yes | 프로젝트 ID |
| name | string | no | 표시 제목 |
| total_duration | number | yes | 초 |
| scene_count | int | yes | 1~18 |
| scene_duration | number | yes | 보통 10 |
| aspect_ratio | string | yes | `9:16` / `16:9` |
| transition_mode | string | yes | `last_frame_match_cut` \| `smooth_cross_dissolve` |
| dialogue | bool | no | 기본 false |
| status | string | no | 상태 머신 값 |

## generator

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | string | grok-imagine, manual-upload, … |
| max_duration_sec | number | 6 또는 10 등 |
| aspect | string | |
| supports_exact_start_frame | enum | true \| partial \| unknown |

## character_lock / look_lock

| 필드 | 설명 |
| --- | --- |
| path | md 경로 |
| reference | 이미지 경로 (character) |

## scenes[]

| 필드 | 설명 |
| --- | --- |
| id | scene_01 … |
| start_image | 상대 경로 |
| start_image_source | N≥2: prev handoff 경로 |
| source_video | mp4 |
| handoff_frame | png |
| scene_end_type | hold \| plant-feet \| gesture \| walk |
| qa_status | pending \| handoff_ready \| passed \| failed |
| handoff_meta | t, blur, duration, warning |

## retry

| 필드 | 기본 |
| --- | --- |
| max_per_scene | 3 |
| immutable_completed | true |

## gates

| 필드 | 권장 기본 |
| --- | --- |
| max_frame0_delta_y | 4 |
| max_frame0_mae | 8 |
| min_handoff_blur | 40 |
| duration_tol_sec | 0.6 |
