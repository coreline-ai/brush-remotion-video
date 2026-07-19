#!/usr/bin/env python3
"""Render a project-owned, soft 60-second rain ambience without external recordings."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48_000
DURATION = 60.0
SEED = 2026071904


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def soft_band_noise(rng: np.random.Generator, n: int, low: float, high: float) -> np.ndarray:
    """Broad, softly filtered rain bed; no recorded rain/loop/sample is read."""
    white = rng.standard_normal(n).astype(np.float32)
    sos = signal.butter(3, (low, high), btype="bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, white).astype(np.float32)


def smooth_envelope(rng: np.random.Generator, n: int) -> np.ndarray:
    # Slow intensity motion makes the bed breathe, but never becomes wind or thunder.
    count = int(math.ceil(DURATION / 1.6)) + 2
    anchors = 0.79 + rng.uniform(-0.12, 0.12, count)
    x = np.linspace(0, n - 1, count)
    envelope = np.interp(np.arange(n), x, anchors).astype(np.float32)
    return signal.sosfiltfilt(signal.butter(2, 0.32, fs=SR, output="sos"), envelope).astype(np.float32)


def add_drops(rng: np.random.Generator, buffer: np.ndarray) -> int:
    """Add restrained, non-ringing close droplets in stereo."""
    count = int(DURATION * 26)
    times = np.sort(rng.uniform(0.25, DURATION - 1.9, count))
    for start in times:
        length = int(rng.uniform(0.030, 0.115) * SR)
        idx = int(start * SR)
        t = np.arange(length, dtype=np.float32) / SR
        attack = 1.0 - np.exp(-t / 0.0025)
        decay = np.exp(-t / rng.uniform(0.018, 0.060))
        # A small noise-led impact plus a subdued body keeps drops natural, not bell-like.
        body_hz = rng.uniform(900.0, 2800.0)
        impact = rng.standard_normal(length).astype(np.float32) * 0.78
        body = np.sin(2 * np.pi * body_hz * t + rng.uniform(0, 2 * np.pi)).astype(np.float32) * 0.22
        hit = (impact + body) * attack * decay * rng.uniform(0.004, 0.012)
        pan = rng.uniform(0.16, 0.84)
        left, right = math.cos(pan * math.pi / 2), math.sin(pan * math.pi / 2)
        end = min(len(buffer), idx + length)
        buffer[idx:end, 0] += hit[:end - idx] * left
        buffer[idx:end, 1] += hit[:end - idx] * right
    return count


def decode_peak(path: Path) -> float:
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "pipe:1"],
        capture_output=True, check=True,
    )
    values = np.frombuffer(result.stdout, dtype="<f4")
    return float(np.max(np.abs(values))) if len(values) else 0.0


def loudness(path: Path) -> dict:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "loudnorm=I=-27:LRA=6:TP=-2:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    start, end = result.stderr.rfind("{"), result.stderr.rfind("}")
    data = json.loads(result.stderr[start:end + 1])
    return {"integratedLufs": float(data["input_i"]), "truePeakDbtp": float(data["input_tp"]), "lra": float(data["input_lra"])}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "output" / "original-audio" / "rain-ambience"
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "gentle-rain-window-60s-raw-48k24.wav"
    master = out / "gentle-rain-window-60s.m4a"
    manifest = out / "gentle-rain-window-60s-origin.json"
    rng = np.random.default_rng(SEED)
    n = int(DURATION * SR)

    common = soft_band_noise(rng, n, 520.0, 7_600.0)
    side = soft_band_noise(rng, n, 680.0, 8_500.0)
    env = smooth_envelope(rng, n)
    rain = np.empty((n, 2), dtype=np.float32)
    rain[:, 0] = (common * 0.88 + side * 0.18) * env
    rain[:, 1] = (common * 0.88 - side * 0.18) * env
    drops = add_drops(rng, rain)

    # Soft room diffusion and a 0.8-second entry/exit prevent clicks at playback boundaries.
    for delay_sec, wet in ((0.031, 0.12), (0.071, 0.075), (0.123, 0.040)):
        delay = int(delay_sec * SR)
        rain[delay:] += rain[:-delay] * wet
    rain = signal.sosfiltfilt(signal.butter(2, 8_800.0, btype="lowpass", fs=SR, output="sos"), rain, axis=0).astype(np.float32)
    fade = np.ones(n, dtype=np.float32)
    fade[:int(.8 * SR)] = np.sin(np.linspace(0, np.pi / 2, int(.8 * SR), endpoint=True)) ** 2
    fade[-int(1.4 * SR):] = np.cos(np.linspace(0, np.pi / 2, int(1.4 * SR), endpoint=True)) ** 2
    rain *= fade[:, None]
    peak_before = float(np.max(np.abs(rain)))
    rain *= min(1.0, 0.205 / max(peak_before, 1e-9))
    sf.write(raw, rain, SR, subtype="PCM_24")

    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw),
        "-ar", str(SR), "-ac", "2", "-c:a", "aac", "-b:a", "192k",
        "-metadata", "title=창가의 잔비", "-metadata", "artist=Codex Original Sound",
        "-movflags", "+faststart", str(master),
    ], check=True)
    decoded_peak = decode_peak(master)
    metrics = loudness(master)
    if decoded_peak > 0.25:
        raise RuntimeError(f"decoded peak too high: {decoded_peak}")
    manifest.write_text(json.dumps({
        "schemaVersion": 1,
        "title": "창가의 잔비 — Gentle Rain Window",
        "durationSeconds": DURATION,
        "sampleRateHz": SR,
        "format": "AAC-LC 192kbps M4A",
        "seed": SEED,
        "source": "local procedural synthesis only",
        "externalSamplesUsed": False,
        "thirdPartyLoopsUsed": False,
        "composition": "soft filtered rain bed, restrained stereo droplets, subtle room diffusion; no thunder, music, or voice",
        "dropCount": drops,
        "peakBeforeGain": peak_before,
        "decodedPeak": decoded_peak,
        "measured": metrics,
        "rawSha256": sha256(raw),
        "masterSha256": sha256(master),
        "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"master": str(master), "raw": str(raw), "manifest": str(manifest), "decodedPeak": decoded_peak, "measured": metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()
