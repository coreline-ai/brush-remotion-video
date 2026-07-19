#!/usr/bin/env python3
"""Technical and musical-profile QA for the genre-distinct sampled piano collection."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=True)


def probe(path: Path) -> dict:
    payload = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)).stdout)
    audio = next(stream for stream in payload["streams"] if stream["codec_type"] == "audio")
    return {
        "codec": audio["codec_name"],
        "sampleRateHz": int(audio["sample_rate"]),
        "channels": int(audio["channels"]),
        "bitsPerRawSample": int(audio.get("bits_per_raw_sample") or audio.get("bits_per_sample") or 0),
        "durationSec": float(payload["format"]["duration"]),
    }


def loudness(path: Path) -> dict:
    output = run("ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                 "loudnorm=I=-20:LRA=7:TP=-1.5:print_format=json", "-f", "null", "-")
    blocks = re.findall(r"\{\s*\"input_i\".*?\}", output.stderr, re.S)
    if not blocks:
        raise RuntimeError(f"loudnorm JSON을 찾지 못함: {path}")
    payload = json.loads(blocks[-1])
    return {"integratedLufs": float(payload["input_i"]), "truePeakDbtp": float(payload["input_tp"]), "lra": float(payload["input_lra"])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=ROOT / "projects/sampled-piano-genre-collection")
    parser.add_argument("--output-root", type=Path, default=ROOT / "output/original-audio/sampled-piano-genre-collection")
    args = parser.parse_args()
    collection = json.loads((args.project_root / "collection.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "assets/instruments/catalog.json").read_text(encoding="utf-8"))["instruments"][0]
    tracks, failures = [], []
    expected_ids = [item["id"] for item in collection["tracks"]]
    metadata_sets = {field: set() for field in ("genre", "groove", "timeSignature", "form", "tempoBpm", "harmony")}

    for listed in collection["tracks"]:
        ident = listed["id"]
        composition = args.project_root / ident / "composition.json"
        raw = args.output_root / ident / "raw-48k24.wav"
        master = args.output_root / ident / f"{ident}-10m-44k16.wav"
        meta = json.loads(composition.read_text(encoding="utf-8"))
        technical, measured = probe(master), loudness(master)
        raw_technical = probe(raw)
        for field in metadata_sets:
            metadata_sets[field].add(meta[field])
        musical_profile = {field: meta[field] for field in ("genre", "groove", "timeSignature", "tempoBpm", "tempoUnit", "keyCenter", "harmony", "form", "bars", "barDurationSec")}
        valid_master = (
            technical["codec"] == "pcm_s16le" and technical["sampleRateHz"] == 44100
            and technical["channels"] == 2 and technical["bitsPerRawSample"] == 16
            and abs(technical["durationSec"] - 600.0) < 0.01 and measured["truePeakDbtp"] <= -0.5
        )
        valid_raw = raw_technical["codec"] == "pcm_s24le" and raw_technical["sampleRateHz"] == 48000 and raw_technical["channels"] == 2
        valid_composition = (
            meta["durationSec"] == 600.0 and abs(meta["bars"] * meta["barDurationSec"] - 600.0) < 1e-5
            and meta["id"] == ident and all(21 <= event["midi"] <= 108 and 1 <= event["velocity"] <= 127 and 0 <= event["startSec"] < 600 for event in meta["notes"])
        )
        if not (valid_master and valid_raw and valid_composition):
            failures.append(ident)
        item = {
            "schemaVersion": 2,
            "id": ident,
            "title": meta["title"],
            "durationSec": meta["durationSec"],
            "noteCount": len(meta["notes"]),
            "imageReference": meta["imageReference"],
            "musicalProfile": musical_profile,
            "instrument": {"id": catalog["id"], "archiveSha256": catalog["acquisition"]["archiveSha256"], "license": catalog["license"]},
            "compositionSha256": sha(composition),
            "rendererSha256": sha(ROOT / "scripts/render-sampled-piano.py"),
            "rawSha256": sha(raw),
            "masterSha256": sha(master),
            "rawTechnical": raw_technical,
            "technical": technical,
            "loudness": measured,
            "masterFile": str(master),
        }
        (args.output_root / ident / "provenance.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tracks.append(item)

    genre_diversity = {
        "uniqueGenre": len(metadata_sets["genre"]) == len(expected_ids),
        "uniqueGroove": len(metadata_sets["groove"]) == len(expected_ids),
        "uniqueForm": len(metadata_sets["form"]) == len(expected_ids),
        "uniqueTempo": len(metadata_sets["tempoBpm"]) == len(expected_ids),
        "uniqueHarmony": len(metadata_sets["harmony"]) == len(expected_ids),
        "atLeastTwoMeters": len(metadata_sets["timeSignature"]) >= 2,
    }
    if not all(genre_diversity.values()):
        failures.append("genre-diversity")
    report = {
        "schemaVersion": 2,
        "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "collection": collection["collection"],
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
        "genreDiversity": genre_diversity,
        "tracks": tracks,
    }
    (args.output_root / "collection-qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    attribution = catalog["license"]["attributionText"]
    change_note = catalog["license"]["modificationNotice"]
    lines = ["# Genre-distinct sampled piano collection — YouTube attribution", "", attribution, f"Changes: {change_note}", ""]
    for item in tracks:
        profile = item["musicalProfile"]
        lines.append(f"- {item['title']} ({profile['genre']}, {profile['timeSignature']}, {profile['tempoBpm']} {profile['tempoUnit']} BPM) — original composition; {item['masterFile']}")
    (args.output_root / "youtube-description.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {"verdict": report["verdict"], "genreDiversity": genre_diversity, "tracks": [{"id": x["id"], "technical": x["technical"], "loudness": x["loudness"]} for x in tracks]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
