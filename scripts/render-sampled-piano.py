#!/usr/bin/env python3
"""Render original note events with a local Noct-Salamander SFZ/WAV piano."""
from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

OUTPUT_SR = 48_000
SAMPLE_RE = re.compile(r"(\w+)=([^\s]+)")


@dataclass(frozen=True)
class Region:
    key: int
    low_velocity: int
    high_velocity: int
    keycenter: int
    tune_cents: float
    volume_db: float
    sample: Path


def parse_sfz(path: Path, sample_dir: Path) -> list[Region]:
    """Parse only the note/velocity regions required by this renderer."""
    regions: list[Region] = []
    group_tune = 0.0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("<group>"):
            fields = dict(SAMPLE_RE.findall(line))
            group_tune = float(fields.get("tune", "0"))
            continue
        if not line.startswith("<region>"):
            continue
        fields = dict(SAMPLE_RE.findall(line))
        required = ("sample", "lokey", "hikey", "lovel", "pitch_keycenter")
        if any(name not in fields for name in required):
            continue
        if fields["lokey"] != fields["hikey"]:
            continue
        sample = sample_dir / Path(fields["sample"].replace("\\", "/")).name
        regions.append(Region(
            key=int(fields["lokey"]), low_velocity=int(fields["lovel"]),
            high_velocity=int(fields.get("hivel", "127")),
            keycenter=int(fields["pitch_keycenter"]), tune_cents=group_tune,
            volume_db=float(fields.get("volume", "0")), sample=sample,
        ))
    if not regions:
        raise ValueError(f"연주 가능한 region 없음: {path}")
    return regions


def select_region(regions: list[Region], midi: int, velocity: int) -> Region:
    if not 21 <= midi <= 108:
        raise ValueError(f"MIDI note 범위 밖: {midi}")
    if not 1 <= velocity <= 127:
        raise ValueError(f"velocity 범위 밖: {velocity}")
    choices = [r for r in regions if r.key == midi and r.low_velocity <= velocity <= r.high_velocity]
    if len(choices) != 1:
        raise ValueError(f"region 선택 실패: midi={midi}, velocity={velocity}, matches={len(choices)}")
    if not choices[0].sample.is_file():
        raise FileNotFoundError(f"샘플 파일 없음: {choices[0].sample}")
    return choices[0]


def _ratio_resample(audio: np.ndarray, ratio: float) -> np.ndarray:
    """Change sample playback speed by ratio while retaining the sampled timbre."""
    fraction = Fraction(1.0 / ratio).limit_denominator(8192)
    return resample_poly(audio, fraction.numerator, fraction.denominator, axis=0).astype(np.float32)


@lru_cache(maxsize=64)
def load_source(sample_path: str) -> np.ndarray:
    """Read and rate-normalize source WAV once; long renders reuse this cache."""
    audio, source_sr = sf.read(sample_path, dtype="float32", always_2d=True)
    if source_sr != OUTPUT_SR:
        ratio = Fraction(OUTPUT_SR, source_sr).limit_denominator(8192)
        audio = resample_poly(audio, ratio.numerator, ratio.denominator, axis=0).astype(np.float32)
    return audio


def load_note(region: Region, midi: int, hold_sec: float) -> np.ndarray:
    audio = load_source(str(region.sample)).copy()
    speed = 2 ** ((midi - region.keycenter + region.tune_cents / 100.0) / 12.0)
    audio = _ratio_resample(audio, speed)
    # Natural sample decay is preserved; this only gives the key release a soft end.
    release_sec, tail_sec = 1.35, 3.8
    keep = min(len(audio), int(round((hold_sec + tail_sec) * OUTPUT_SR)))
    audio = audio[:keep].copy()
    release_start = min(len(audio), int(round(hold_sec * OUTPUT_SR)))
    if release_start < len(audio):
        fade_len = min(len(audio) - release_start, int(round(release_sec * OUTPUT_SR)))
        if fade_len:
            fade = np.cos(np.linspace(0, math.pi / 2, fade_len, endpoint=True)) ** 0.7
            audio[release_start:release_start + fade_len] *= fade[:, None]
        if release_start + fade_len < len(audio):
            audio[release_start + fade_len:] = 0
    return audio * (10 ** (region.volume_db / 20.0))


def render(composition: dict, regions: list[Region]) -> tuple[np.ndarray, dict]:
    duration = float(composition["durationSec"])
    if duration <= 0:
        raise ValueError("durationSec는 0보다 커야 함")
    notes = composition["notes"]
    buffer = np.zeros((int(round(duration * OUTPUT_SR)), 2), dtype=np.float32)
    selected: list[dict] = []
    for event in notes:
        start, midi = float(event["startSec"]), int(event["midi"])
        hold, velocity = float(event["holdSec"]), int(event["velocity"])
        if start < 0 or hold <= 0 or start >= duration:
            raise ValueError(f"잘못된 note event: {event}")
        region = select_region(regions, midi, velocity)
        tone = load_note(region, midi, hold) * float(event.get("gain", 1.0))
        index = int(round(start * OUTPUT_SR))
        length = min(len(tone), len(buffer) - index)
        buffer[index:index + length] += tone[:length]
        selected.append({"midi": midi, "velocity": velocity, "sample": region.sample.name})
    peak = float(np.max(np.abs(buffer))) if len(buffer) else 0.0
    if peak <= 0:
        raise ValueError("무음 렌더 결과")
    if peak > 0.90:
        buffer *= 0.90 / peak
    return buffer, {"noteCount": len(notes), "peakBeforeGuard": peak, "peakAfterGuard": float(np.max(np.abs(buffer))), "uniqueSampleCount": len({x["sample"] for x in selected}), "samplePreview": selected[:12]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument-root", type=Path, required=True)
    ap.add_argument("--sfz", type=Path, required=True)
    ap.add_argument("--composition", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sample_dir = args.instrument_root / "48khz24bit"
    regions = parse_sfz(args.sfz, sample_dir)
    composition = json.loads(args.composition.read_text(encoding="utf-8"))
    audio, summary = render(composition, regions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(args.out, audio, OUTPUT_SR, subtype="PCM_24")
    print(json.dumps({"out": str(args.out), "sampleRateHz": OUTPUT_SR, "channels": 2,
                      "regions": len(regions), **summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
