"""최종 영상 업로드용 제목·설명·저작자 표시 산출물."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def write_delivery_package(out_dir: str | Path, *, project_id: str, video: str | Path,
                           title: str, asset: dict | None = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    video_path = Path(video).resolve()
    attribution = ""
    if asset is not None:
        license_info = asset.get("license") or {}
        attribution = str(license_info.get("attributionText") or "").strip()
        if license_info.get("attributionRequired") and not attribution:
            raise ValueError("저작자 표시 필수 음원의 attributionText가 비어 있음")

    description_lines = [title, ""]
    if attribution:
        description_lines += ["음악 출처 / Music Credit", "", attribution, ""]
    description = "\n".join(description_lines).rstrip() + "\n"
    upload_notes = (
        "YouTube Studio > 세부정보 > 설명에 youtube-description.txt 내용을 붙여 넣으세요.\n"
        "영상 전체를 CC BY로 재배포할 의도가 없다면 업로드의 라이선스 설정은 "
        "표준 YouTube 라이선스로 유지하세요.\n"
        "MP4 metadata는 설명란 저작자 표시를 대신하지 않습니다.\n"
    )

    (out / "youtube-title.txt").write_text(title + "\n", encoding="utf-8")
    (out / "youtube-description.txt").write_text(description, encoding="utf-8")
    (out / "ATTRIBUTION.txt").write_text((attribution + "\n") if attribution else "", encoding="utf-8")
    (out / "UPLOAD-NOTES.txt").write_text(upload_notes, encoding="utf-8")
    manifest = {
        "schemaVersion": 1,
        "projectId": project_id,
        "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "video": str(video_path),
        "title": title,
        "assetId": asset.get("id") if asset else None,
        "files": ["youtube-title.txt", "youtube-description.txt", "ATTRIBUTION.txt", "UPLOAD-NOTES.txt"],
    }
    manifest_path = out / "delivery-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"directory": str(out), "manifest": str(manifest_path), **manifest}

