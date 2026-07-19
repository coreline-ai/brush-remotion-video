#!/usr/bin/env python3
"""QA and provenance for six one-minute sampled-piano healing miniatures."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects/sampled-piano-healing-miniatures"
OUT = ROOT / "output/original-audio/sampled-piano-healing-miniatures"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1_048_576), b""):
            value.update(block)
    return value.hexdigest()


def command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def probe(path: Path) -> dict:
    result = json.loads(command("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)).stdout)
    stream = next(item for item in result["streams"] if item["codec_type"] == "audio")
    return {"codec": stream["codec_name"], "sampleRateHz": int(stream["sample_rate"]), "channels": stream["channels"], "bitsPerRawSample": int(stream.get("bits_per_raw_sample") or stream.get("bits_per_sample") or 0), "durationSec": float(result["format"]["duration"])}


def loudness(path: Path) -> dict:
    result = command("ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "loudnorm=I=-20:LRA=7:TP=-1.5:print_format=json", "-f", "null", "-")
    payloads = re.findall(r"\{\s*\"input_i\".*?\}", result.stderr, re.S)
    if not payloads:
        raise RuntimeError(f"No loudness block: {path}")
    value = json.loads(payloads[-1])
    return {"integratedLufs": float(value["input_i"]), "truePeakDbtp": float(value["input_tp"]), "lra": float(value["input_lra"])}


def main() -> None:
    collection = json.loads((PROJECT / "collection.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "assets/instruments/catalog.json").read_text(encoding="utf-8"))["instruments"][0]
    tracks, failures = [], []
    genres = set()
    for record in collection["tracks"]:
        ident = record["id"]
        composition = PROJECT / ident / "composition.json"
        master = OUT / ident / f"{ident}-1m-44k16.wav"
        raw = OUT / ident / "raw-48k24.wav"
        render = OUT / ident / "render-report.json"
        meta, render_data = json.loads(composition.read_text(encoding="utf-8")), json.loads(render.read_text(encoding="utf-8"))
        technical, raw_technical, measured = probe(master), probe(raw), loudness(master)
        genres.add(meta["genre"])
        valid = (meta["durationSec"] == 60 and abs(meta["bars"] * meta["barDurationSec"] - 60) < 1e-5 and technical["codec"] == "pcm_s16le" and technical["sampleRateHz"] == 44100 and technical["channels"] == 2 and technical["bitsPerRawSample"] == 16 and abs(technical["durationSec"] - 60) < .01 and raw_technical["codec"] == "pcm_s24le" and raw_technical["sampleRateHz"] == 48000 and render_data["uniqueSampleCount"] >= 10 and measured["truePeakDbtp"] <= -.5)
        if not valid:
            failures.append(ident)
        entry = {"schemaVersion": 2, "id": ident, "title": meta["title"], "genre": meta["genre"], "musicalProfile": {field: meta[field] for field in ("tempoBpm", "tempoUnit", "timeSignature", "groove", "keyCenter", "harmony", "form")}, "noteCount": len(meta["notes"]), "source": "original note-event composition rendered from local piano samples only", "instrument": {"id": catalog["id"], "license": catalog["license"], "archiveSha256": catalog["acquisition"]["archiveSha256"]}, "compositionSha256": digest(composition), "rendererSha256": digest(ROOT / "scripts/render-sampled-piano.py"), "rawSha256": digest(raw), "masterSha256": digest(master), "render": render_data, "rawTechnical": raw_technical, "technical": technical, "loudness": measured, "masterFile": str(master)}
        (OUT / ident / "provenance.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tracks.append(entry)
    diversity = {"uniqueGenres": len(genres) == len(tracks), "sixTracks": len(tracks) == 6}
    if not all(diversity.values()):
        failures.append("style-diversity")
    report = {"schemaVersion": 2, "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"), "collection": collection["collection"], "verdict": "PASS" if not failures else "FAIL", "failures": failures, "styleDiversity": diversity, "tracks": tracks}
    (OUT / "collection-qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    attribution = catalog["license"]["attributionText"]
    lines = ["# Healing/new-age piano miniatures — YouTube attribution", "", attribution, f"Changes: {catalog['license']['modificationNotice']}", ""]
    lines.extend(f"- {entry['title']} ({entry['genre']}) — original composition; {entry['masterFile']}" for entry in tracks)
    (OUT / "youtube-description.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": report["verdict"], "styleDiversity": diversity, "tracks": [{"id": item["id"], "technical": item["technical"], "loudness": item["loudness"], "sampleCount": item["render"]["uniqueSampleCount"]} for item in tracks]}, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
