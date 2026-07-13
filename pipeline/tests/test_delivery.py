import json

import pytest

from brushvid.delivery import write_delivery_package


def test_delivery_package_contains_cc_attribution_and_upload_note(tmp_path):
    video = tmp_path / "final.mp4"
    video.write_bytes(b"video")
    asset = {"id": "cc-track", "license": {
        "attributionRequired": True,
        "attributionText": "Track by Artist\nLicense: https://creativecommons.org/licenses/by/4.0/\nChanges: trimmed.",
    }}
    result = write_delivery_package(tmp_path / "delivery", project_id="demo", video=video,
                                    title="도시의 빛을 그리다", asset=asset)
    out = tmp_path / "delivery"
    assert "Track by Artist" in (out / "youtube-description.txt").read_text(encoding="utf-8")
    assert "표준 YouTube 라이선스" in (out / "UPLOAD-NOTES.txt").read_text(encoding="utf-8")
    assert json.loads((out / "delivery-manifest.json").read_text())["assetId"] == "cc-track"
    assert result["title"] == "도시의 빛을 그리다"


def test_delivery_package_rejects_missing_required_attribution(tmp_path):
    video = tmp_path / "final.mp4"
    video.write_bytes(b"video")
    with pytest.raises(ValueError, match="attributionText"):
        write_delivery_package(tmp_path / "delivery", project_id="demo", video=video,
                               title="Demo", asset={"id": "bad", "license": {"attributionRequired": True}})
