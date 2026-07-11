"""props.py 테스트 — TC-3.3(jsonschema 검증 + schemaVersion=1)."""
import jsonschema
import pytest

from brushvid.props import SCHEMA_PATH, build_props, build_scene, validate_props


def test_tc_3_3_props_validate():
    """TC-3.3: 빌더 출력이 jsonschema 검증 통과 + schemaVersion=1."""
    scene = build_scene("scene-01", "demo/routes.json", 300,
                        cues=[{"text": "안녕", "from": 30, "to": 90}],
                        top_title={"lines": ["첫 줄"], "enterAt": 10})
    props = build_props("demo-project", [scene], audio="demo/audio.mp3")
    validated = validate_props(props)
    assert validated["schemaVersion"] == 1
    assert validated["projectId"] == "demo-project"
    assert validated["scenes"][0]["routes"] == "demo/routes.json"


def test_tc_3_3_schema_is_consumed_not_defined():
    """스키마 파일은 리포의 schema/render-props.schema.json 을 소비한다."""
    assert SCHEMA_PATH.name == "render-props.schema.json"
    assert SCHEMA_PATH.is_file()


def test_invalid_props_rejected():
    """스키마 위반(scenes 비움, 잘못된 format)은 ValidationError."""
    with pytest.raises(jsonschema.ValidationError):
        validate_props({"schemaVersion": 1, "projectId": "x", "scenes": []})
    scene = build_scene("s1", None, 100)
    bad = build_props("x", [scene], fmt="youtub")
    with pytest.raises(jsonschema.ValidationError):
        validate_props(bad)


def test_golden_single_props_pass():
    """기존 golden-single props 도 같은 스키마를 통과한다 (회귀 가드)."""
    import json
    golden = SCHEMA_PATH.parent.parent / "data" / "golden-single" / "props.json"
    validate_props(json.loads(golden.read_text(encoding="utf-8")))
