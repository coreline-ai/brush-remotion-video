#!/usr/bin/env python3
"""Render a deterministic, project-owned 10 minute melodic piano nocturne.

This is intentionally a composition, not a drone or frequency-tone generator:
an original D-major/B-minor motif is voiced across 20 evolving 30-second phrases.
It uses only local NumPy synthesis (no samples, loops, or network assets).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import wave
from datetime import datetime
from pathlib import Path

import numpy as np


SR = 48_000
SECONDS = 600.0
TEMPO = 64.0
BEAT = 60.0 / TEMPO
BAR = BEAT * 4
PHRASE = BAR * 8
TAIL = 5.0
RNG = np.random.default_rng(20260717)

# Eight-bar harmonic paths.  The melody is generated from the chord tones and
# original motif contours below, so a 10-minute file is not a short loop copied
# hundreds of times.
PROGRESSIONS = (
    ((50, 54, 57, 61, 64), (47, 50, 54, 57, 61), (43, 47, 50, 54, 57), (45, 49, 52, 57, 61),
     (50, 54, 57, 61, 64), (45, 49, 52, 57, 61), (52, 55, 59, 62, 66), (50, 54, 57, 61, 64)),
    ((47, 50, 54, 57, 61), (43, 47, 50, 54, 57), (50, 54, 57, 61, 64), (45, 49, 52, 57, 61),
     (47, 50, 54, 57, 61), (52, 55, 59, 62, 66), (45, 49, 52, 57, 61), (50, 54, 57, 61, 64)),
    ((43, 47, 50, 54, 57), (50, 54, 57, 61, 64), (47, 50, 54, 57, 61), (45, 49, 52, 57, 61),
     (43, 47, 50, 54, 57), (52, 55, 59, 62, 66), (45, 49, 52, 57, 61), (50, 54, 57, 61, 64)),
)

# Original, scale-aware contours.  -1 means breath/rest.  Values are indices
# into a chord-scale palette constructed for each bar.
MOTIFS = (
    (2, 4, 5, 4, 2, 1, 0, -1),
    (4, 5, 7, 5, 4, 2, 1, -1),
    (2, 1, 2, 4, 5, 4, 2, 0),
    (5, 4, 2, 1, 2, 4, 5, -1),
    (7, 5, 4, 2, 4, 5, 2, 0),
)


def midi_frequency(midi: int, cents: float = 0.0) -> float:
    return 440.0 * 2 ** ((midi - 69 + cents / 100.0) / 12.0)


def add_piano_note(
    buffer: np.ndarray,
    start: float,
    midi: int,
    held: float,
    velocity: float,
    *,
    pan: float | None = None,
) -> None:
    """Add a softly voiced, pedal-sustained procedural piano note."""
    index = int(round(start * SR))
    if index >= len(buffer):
        return
    skipped = max(0, -index)
    index = max(0, index)
    decay = 2.6 if midi >= 60 else 3.5
    total_length = int(round((held + TAIL) * SR))
    length = min(len(buffer) - index, total_length - skipped)
    if length <= 8:
        return
    t = (np.arange(length, dtype=np.float32) + skipped) / SR
    freq = midi_frequency(midi, float(RNG.uniform(-1.8, 1.8)))
    tone = np.zeros(length, dtype=np.float32)
    # Mild inharmonicity and a subdued felt-piano harmonic profile.
    for partial, gain in ((1.0, 1.0), (2.001, 0.31), (3.006, 0.15), (4.014, 0.075), (5.025, 0.035)):
        tone += gain * np.sin(2 * math.pi * freq * partial * t + partial * 0.031)
    # Small hammer attack; deliberately quiet to avoid clicks.
    attack = np.minimum(1.0, t / 0.012)
    natural = 0.78 * np.exp(-t / decay) + 0.22 * np.exp(-t / (decay * 2.8))
    release_at = max(0.08, held)
    release = np.where(t <= release_at, 1.0, np.exp(-(t - release_at) / 1.45))
    envelope = attack * natural * release
    tone *= envelope * velocity
    # Piano keyboard placement: lower notes left, upper notes right.
    placement = pan if pan is not None else float(np.clip(0.50 + (midi - 60) / 58, 0.12, 0.88))
    left = math.cos(placement * math.pi / 2)
    right = math.sin(placement * math.pi / 2)
    buffer[index:index + length, 0] += tone * left
    buffer[index:index + length, 1] += tone * right


def palette_for(chord: tuple[int, ...]) -> list[int]:
    """Voiced scale palette around the chord for a lyrical right hand."""
    root = chord[0] + 24
    candidates = [root + offset for offset in (0, 2, 4, 5, 7, 9, 11, 12, 14)]
    # Keep the chord tones prominent but retain passing tones for a singable line.
    chord_tones = {m + 24 for m in chord}
    return sorted(set(candidates + list(chord_tones)))


def add_bar(buffer: np.ndarray, at: float, chord: tuple[int, ...], motif: tuple[int, ...],
            phrase_index: int, bar_index: int, energy: float) -> None:
    """Write left-hand broken chords plus a varying, breathing melody."""
    root, third, fifth, seventh, ninth = chord
    # Left hand: root pulse followed by soft broken voicing.  Durations overlap
    # under the virtual sustain pedal, which keeps the harmony musical.
    bass_velocity = 0.048 * energy
    add_piano_note(buffer, at, root - 12, BAR * 0.86, bass_velocity, pan=0.19)
    left_pattern = (fifth - 12, third, ninth, fifth, seventh, third, ninth, fifth)
    for step, note in enumerate(left_pattern):
        jitter = float(RNG.uniform(-0.018, 0.018))
        velocity = (0.030 + (0.008 if step in (0, 4) else 0.0)) * energy
        add_piano_note(buffer, at + step * (BEAT / 2) + jitter, note, BEAT * 1.45, velocity)

    palette = palette_for(chord)
    motif_variant = list(motif)
    # Every second phrase answers instead of mechanically replaying the theme.
    if phrase_index % 3 == 1 and bar_index in (2, 6):
        motif_variant = motif_variant[::-1]
    if phrase_index % 5 == 4 and bar_index == 7:
        motif_variant[-2:] = [3, -1]
    for step, degree in enumerate(motif_variant):
        if degree < 0:
            continue
        note = palette[degree % len(palette)]
        # A phrase-level octave lift creates a gentle arch at minutes 3-7.
        if 6 <= phrase_index <= 13 and step in (2, 3, 4):
            note += 12
        start = at + step * (BEAT / 2) + float(RNG.uniform(-0.024, 0.024))
        duration = BEAT * (0.72 if step in (1, 5) else 1.16)
        accent = 0.012 if step in (0, 4) else 0.0
        velocity = (0.052 + accent + float(RNG.uniform(-0.006, 0.005))) * energy
        add_piano_note(buffer, start, note, duration, velocity)


def phrase_energy(index: int) -> float:
    # 20 phrases: delicate opening -> full centre -> gentle ending.
    position = index / 19
    return float(0.74 + 0.30 * math.sin(math.pi * position) + 0.04 * math.sin(index * 1.7))


def render_phrase(index: int) -> np.ndarray:
    """Render exactly one 30-second phrase plus tail for stream-safe overlap."""
    samples = int(round((PHRASE + TAIL) * SR))
    result = np.zeros((samples, 2), dtype=np.float32)
    progression = PROGRESSIONS[index % len(PROGRESSIONS)]
    motif_base = MOTIFS[index % len(MOTIFS)]
    energy = phrase_energy(index)
    for bar_index, chord in enumerate(progression):
        rotated = motif_base[bar_index % 2:] + motif_base[:bar_index % 2]
        add_bar(result, bar_index * BAR, chord, rotated, index, bar_index, energy)

    # A modest room response, independent of any external sample/IR.
    for delay, wet in ((0.19, 0.16), (0.37, 0.105), (0.59, 0.065)):
        offset = int(delay * SR)
        result[offset:] += result[:-offset] * wet
    # Phrase-boundary dynamic envelope; the overlap carry handles decay.
    local = np.arange(samples, dtype=np.float32) / SR
    fade_in = np.clip(local / 0.35, 0.0, 1.0)
    result *= fade_in[:, None]
    return result


def render(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    phrase_count = round(SECONDS / PHRASE)
    if not math.isclose(phrase_count * PHRASE, SECONDS):
        raise RuntimeError("duration must contain a whole number of phrases")
    carry = np.zeros((int(TAIL * SR), 2), dtype=np.float32)
    peak = 0.0
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        for phrase_index in range(phrase_count):
            phrase = render_phrase(phrase_index)
            phrase[:len(carry)] += carry
            main = phrase[:int(round(PHRASE * SR))]
            carry = phrase[int(round(PHRASE * SR)):]
            # End only: a gentle 20-second diminuendo avoids an abrupt finish.
            if phrase_index == phrase_count - 1:
                t = np.arange(len(main), dtype=np.float32) / SR
                end = np.clip((PHRASE - t) / 18.0, 0.0, 1.0)
                main *= end[:, None]
            peak = max(peak, float(np.max(np.abs(main))))
            wav.writeframes((np.clip(main, -0.98, 0.98) * 32767).astype("<i2").tobytes())
    if peak <= 0:
        raise RuntimeError("silent render")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def encode_master(source: Path, target: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
         "-af", "loudnorm=I=-18:LRA=7:TP=-1.5", "-ar", "48000", "-ac", "2",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(target)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a 10-minute original melodic sleep-piano track.")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = args.out_dir / "sleep-piano-nocturne-10m-raw.wav"
    master = args.out_dir / "sleep-piano-nocturne-10m.m4a"
    manifest = args.out_dir / "sleep-piano-nocturne-10m-origin.json"
    render(raw)
    if abs(probe(raw) - SECONDS) > 0.01:
        raise RuntimeError("raw duration mismatch")
    encode_master(raw, master)
    duration = probe(master)
    if abs(duration - SECONDS) > 0.08:
        raise RuntimeError(f"encoded duration mismatch: {duration}")
    manifest.write_text(json.dumps({
        "title": "Quiet Window — Original Sleep Piano Nocturne",
        "durationSeconds": duration,
        "sampleRate": SR,
        "channels": 2,
        "format": "AAC-LC 192 kbps in M4A",
        "composition": "20 evolving 30-second phrases; original D-major/B-minor piano motifs",
        "source": "local NumPy procedural piano synthesis; no external samples, loops, or network assets",
        "createdAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rawSha256": sha256(raw),
        "masterSha256": sha256(master),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"master": str(master), "manifest": str(manifest), "duration": duration}, ensure_ascii=False))


if __name__ == "__main__":
    main()
