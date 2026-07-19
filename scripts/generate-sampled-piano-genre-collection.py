#!/usr/bin/env python3
"""Create five deterministic, original 10-minute piano works with distinct genres.

This writes note-event JSON only. It never reads or reuses a finished recording,
MIDI file, loop, or online audio. The companion renderer plays local piano WAV
samples selected through the Noct-Salamander SFZ mapping.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Iterable

DURATION = 600.0


def ev(start: float, midi: int, hold: float, velocity: int, gain: float, part: str) -> dict:
    return {
        "startSec": round(start, 6),
        "midi": int(max(21, min(108, midi))),
        "holdSec": round(max(0.04, hold), 6),
        "velocity": int(max(1, min(127, velocity))),
        "gain": round(gain, 4),
        "part": part,
    }


def add(notes: list[dict], start: float, pitches: Iterable[int], hold: float, velocity: int,
        gain: float, part: str) -> None:
    for pitch in pitches:
        notes.append(ev(start, pitch, hold, velocity, gain, part))


def triad(root: int, quality: str, *, extended: bool = False) -> tuple[int, ...]:
    third = 3 if quality.startswith("m") else 4
    if quality == "dim":
        third, fifth = 3, 6
    else:
        fifth = 7
    tones = [root, root + third, root + fifth]
    if extended:
        if quality in ("7", "m7", "m9", "m11"):
            tones.append(root + 10)
        elif quality in ("maj7", "maj9", "6"):
            tones.append(root + (9 if quality == "6" else 11))
        if quality in ("9", "maj9", "m9", "13"):
            tones.append(root + 14)
        if quality in ("13", "m11"):
            tones.append(root + (21 if quality == "13" else 17))
    return tuple(tones)


def meta(ident: str, title: str, tempo: int, signature: str, tempo_unit: str,
         groove: str, key: str, harmony: str, form: str, image: str, seed: int,
         notes: list[dict], bars: int, bar_sec: float) -> dict:
    assert abs(bars * bar_sec - DURATION) < 1e-7, (ident, bars * bar_sec)
    assert notes and all(0 <= x["startSec"] < DURATION and x["holdSec"] > 0 for x in notes)
    return {
        "schemaVersion": 2,
        "id": ident,
        "title": title,
        "durationSec": DURATION,
        "tempoBpm": tempo,
        "tempoUnit": tempo_unit,
        "timeSignature": signature,
        "bars": bars,
        "barDurationSec": round(bar_sec, 9),
        "seed": seed,
        "genre": groove.split(" — ")[0],
        "groove": groove,
        "keyCenter": key,
        "harmony": harmony,
        "form": form,
        "imageReference": image,
        "notes": sorted(notes, key=lambda x: (x["startSec"], x["midi"], x["part"])),
    }


def neo_classical() -> dict:
    """D major 4/4: continuous classical arpeggio and a repeating transformed motif."""
    tempo, beat, bars, seed = 60, 1.0, 150, 6101
    rng, notes = random.Random(seed), []
    # I–V–vi–IV, then nearby chromatic color for the later development sections.
    progression = [(62, "M"), (69, "M"), (71, "m"), (67, "M"), (64, "m"), (69, "M"), (67, "M"), (62, "M")]
    motif = [2, 4, 5, 4, 2, 1, 0, 2]
    d_major = [0, 2, 4, 5, 7, 9, 11]
    for bar in range(bars):
        at, section = bar * 4 * beat, bar // 16
        root, quality = progression[(bar + section * 2) % len(progression)]
        chord = triad(root, quality)
        # Sixteenth-note pattern is deliberately classical rather than a sleepy broken chord.
        arpeggio = (chord[0] - 24, chord[2] - 12, chord[1] - 12, chord[2] - 12,
                    chord[0] - 12, chord[1] - 12, chord[2] - 12, chord[1],
                    chord[0] - 12, chord[1] - 12, chord[2] - 12, chord[1],
                    chord[0] - 12, chord[2] - 12, chord[1] - 12, chord[2])
        for i, pitch in enumerate(arpeggio):
            add(notes, at + i * 0.25, (pitch,), 0.42, 38 + (i % 4) * 2 + rng.randint(-2, 2), 0.075, "arpeggio")
        if bar % 2 == 0:
            transform = (section * 2 + (bar // 8)) % len(d_major)
            for i, degree in enumerate(motif):
                pitch = 74 + d_major[(degree + transform) % len(d_major)]
                if i in (2, 3):
                    pitch += 12
                add(notes, at + (0.3 + i * 0.43) * beat, (pitch,), 0.6 if i < 7 else 1.15,
                    47 + (section % 3) * 3 + rng.randint(-3, 3), 0.105, "motif")
        if bar % 8 == 7:
            add(notes, at + 3.1, (root + 12, root + 16, root + 19), 0.7, 44, 0.065, "cadence")
    return meta("neo-classical-dawn", "새벽의 유리정원", tempo, "4/4", "quarter-note",
                "네오클래식 — 16분 아르페지오와 변주 모티프", "D major",
                "D장조의 I–V–vi–IV 중심 순환, 중간부 근접조 변주", "A–A′–B–A″–coda",
                "projects/star-seed-fairy-tale-100s/", seed, notes, bars, 4.0)


def jazz_ballad() -> dict:
    """F major/D minor swing ballad: rootless extended voicings, ii–V–I answers."""
    tempo, beat, bars, seed = 72, 60 / 72, 180, 7202
    rng, notes = random.Random(seed), []
    # Roots / chord symbols. Extended voicing is intentionally not a triad progression.
    changes = [(62, "m9"), (67, "13"), (60, "maj9"), (69, "m7"),
               (62, "m9"), (67, "13"), (60, "6"), (60, "maj9"),
               (64, "m7"), (69, "13"), (62, "m9"), (67, "13"),
               (60, "maj9"), (65, "7"), (70, "maj9"), (67, "13")]
    f_scale = [0, 2, 4, 5, 7, 9, 10]
    swing = [0.0, 2 / 3, 1.0, 1 + 2 / 3, 2.0, 2 + 2 / 3, 3.0, 3 + 2 / 3]
    for bar in range(bars):
        at, section = bar * 4 * beat, bar // 24
        root, quality = changes[(bar + section * 3) % len(changes)]
        chord = triad(root, quality, extended=True)
        # Rootless left-hand shell: 3rd, 7th, color, with sparse anticipated comping.
        shell = tuple(p + 12 for p in chord[1:])
        add(notes, at + 0.0 * beat, (root - 24,), 1.25 * beat, 39 + rng.randint(-2, 2), 0.09, "walking-root")
        add(notes, at + 1.0 * beat, shell[:3], 0.85 * beat, 43 + rng.randint(-3, 3), 0.062, "rootless-voicing")
        add(notes, at + (2 + 2 / 3) * beat, (root - 19,), 0.92 * beat, 37 + rng.randint(-2, 2), 0.085, "walking-fifth")
        if bar % 2:
            add(notes, at + (3 + 2 / 3) * beat, shell, 0.7 * beat, 45 + rng.randint(-2, 3), 0.06, "anticipated-comp")
        # Long-short swing melody; the melodic degree is altered every eight bars.
        phrase_shift = (section + bar // 8) % len(f_scale)
        for i, pos in enumerate(swing):
            if i in (1, 4) and bar % 3 == 0:
                continue
            degree = (i * 2 + phrase_shift + (bar % 4)) % len(f_scale)
            pitch = 72 + f_scale[degree] + (12 if i in (3, 6) else 0)
            # Outline guide tones on the cadence bars to make the harmony audible.
            if bar % 4 == 3 and i in (0, 3):
                pitch = chord[1] + 24 if i == 0 else chord[-1] + 12
            add(notes, at + pos * beat, (pitch,), (0.52 if i % 2 == 0 else 0.27) * beat,
                46 + (i % 3) * 3 + rng.randint(-3, 3), 0.105, "swing-melody")
        if bar % 16 == 15:
            add(notes, at + 3.0 * beat, tuple(p + 12 for p in chord[1:4]), 1.35 * beat, 48, 0.07, "turnaround")
    return meta("jazz-ballad-afterglow", "잔광의 재즈 발라드", tempo, "4/4", "quarter-note",
                "재즈 발라드 — 늦은 8분 스윙과 ii–V–I 보이싱", "F major / D minor",
                "ii–V–I와 7th·9th·13th 확장 화음, rootless comping", "head–chorus variations–bridge–head–tag",
                "output/cosmic-random-brush-v05-ink-60-final-contact-sheet.jpg", seed, notes, bars, 4 * beat)


def bossa_nova() -> dict:
    """A major 4/4: syncopated bass + short chord comping, no percussion layer."""
    tempo, beat, bars, seed = 80, 0.75, 200, 8303
    rng, notes = random.Random(seed), []
    changes = [(57, "maj7"), (66, "m7"), (59, "m7"), (64, "7"),
               (57, "maj7"), (61, "m7"), (66, "m7"), (64, "7"),
               (62, "m7"), (67, "7"), (61, "m7"), (64, "7"),
               (57, "maj7"), (66, "m7"), (59, "m7"), (57, "6")]
    a_major = [0, 2, 4, 5, 7, 9, 11]
    for bar in range(bars):
        at, section = bar * 4 * beat, bar // 20
        root, quality = changes[(bar + (section // 2) * 4) % len(changes)]
        chord = triad(root, quality, extended=True)
        # Brazilian piano bass has root downbeat and syncopated fifth/approach note.
        add(notes, at, (root - 24,), 0.74 * beat, 47 + rng.randint(-2, 2), 0.095, "bossa-bass")
        add(notes, at + 1.5 * beat, (root - 12,), 0.54 * beat, 42 + rng.randint(-2, 2), 0.085, "bossa-bass")
        add(notes, at + 2.5 * beat, (root - 19,), 0.86 * beat, 44 + rng.randint(-2, 2), 0.088, "bossa-fifth")
        # Staccato offbeat voicings distinguish it from sustained ballad texture.
        voicing = tuple(p + 12 for p in chord[1:])
        for pos, length, accent in ((0.75, 0.38, 0), (1.75, 0.31, 2), (2.75, 0.42, 1), (3.5, 0.28, 3)):
            add(notes, at + pos * beat, voicing, length * beat, 48 + accent + rng.randint(-2, 2), 0.060, "bossa-comp")
        # An eight-bar melodic sentence with syncopated entrances.
        if bar % 2 == 0:
            for i, pos in enumerate((0.25, 0.75, 1.25, 2.0, 2.75, 3.25)):
                degree = (section * 2 + bar // 2 + (i * (2 if i < 3 else 1))) % len(a_major)
                pitch = 73 + a_major[degree] + (12 if i in (3, 5) else 0)
                add(notes, at + pos * beat, (pitch,), (0.55 if i in (0, 3) else 0.32) * beat,
                    52 + (i % 3) * 2 + rng.randint(-2, 3), 0.095, "bossa-melody")
        if bar % 16 == 15:
            add(notes, at + 3.4 * beat, (root + 12, root + 16, root + 19, root + 23), 0.5 * beat, 52, 0.055, "bossa-cadence")
    return meta("bossa-piano-veranda", "베란다의 보사노바", tempo, "4/4", "quarter-note",
                "보사노바 피아노 — 당김음 베이스와 오프비트 컴핑", "A major",
                "maj7·m7·dominant 7th 중심의 라틴 순환", "intro–A–A′–middle eight–A″–outro",
                "output/africa-pen-60/", seed, notes, bars, 4 * beat)


def drama_ballad() -> dict:
    """K-drama ballad: a narrative long melody and controlled final crescendo."""
    tempo, beat, bars, seed = 64, 60 / 64, 160, 9404
    rng, notes = random.Random(seed), []
    changes = [(58, "M"), (65, "M"), (67, "m"), (63, "M"),
               (58, "M"), (65, "M"), (70, "m"), (65, "M"),
               (67, "m"), (63, "M"), (58, "M"), (65, "M"),
               (55, "m"), (63, "M"), (65, "M"), (58, "M")]
    bb_major = [0, 2, 4, 5, 7, 9, 11]
    for bar in range(bars):
        at = bar * 4 * beat
        # Intro 0–15; verse 16–47; prechorus 48–63; chorus 64–111; bridge 112–127; final 128–159.
        if bar < 16: section, energy = "intro", 0.62
        elif bar < 48: section, energy = "verse", 0.76
        elif bar < 64: section, energy = "prechorus", 0.92
        elif bar < 112: section, energy = "chorus", 1.16
        elif bar < 128: section, energy = "bridge", 0.82
        else: section, energy = "final-chorus", 1.25
        root, quality = changes[(bar + (4 if section == "bridge" else 0)) % len(changes)]
        chord = triad(root, quality)
        # Narrative broken left-hand chord: density and octave widen toward chorus.
        low = root - 24 if section in ("intro", "verse", "bridge") else root - 31
        for i, pitch in enumerate((low, chord[2] - 19, chord[1] - 12, chord[2] - 12)):
            add(notes, at + i * beat, (pitch,), 1.36 * beat, int((34 + i * 2) * energy) + rng.randint(-2, 2), 0.088, "ballad-broken-chord")
        if section in ("chorus", "final-chorus") and bar % 2 == 1:
            add(notes, at + 2.6 * beat, (root - 12, chord[1], chord[2]), 1.1 * beat,
                int(44 * energy), 0.055, "chorus-support")
        # Long singing line; final chorus rises an octave every fourth phrase.
        phrase = (bar // 4) % 8
        degrees = (0, 2, 4, 5, 4, 2, 1, 0) if phrase % 2 == 0 else (2, 4, 5, 6, 5, 4, 2, 1)
        positions = (0.22, 0.72, 1.22, 1.82, 2.20, 2.68, 3.18)
        for i, pos in enumerate(positions):
            if section == "intro" and i > 3:
                continue
            degree = degrees[(i + phrase) % len(degrees)]
            pitch = 70 + bb_major[degree]
            if i in (2, 4) or section in ("chorus", "final-chorus") and i in (1, 5):
                pitch += 12
            if section == "final-chorus" and bar % 8 in (6, 7) and i >= 4:
                pitch += 12
            length = (0.42 if i < 5 else 0.75) * beat
            add(notes, at + pos * beat, (pitch,), length, int((43 + (i % 3) * 3) * energy) + rng.randint(-3, 3), 0.115, "singing-melody")
        if bar in (63, 111, 159):
            add(notes, at + 3.0 * beat, (root + 12, root + 16, root + 19), 1.5 * beat, int(52 * energy), 0.065, "drama-cadence")
    return meta("drama-ballad-letter", "보내지 못한 편지", tempo, "4/4", "quarter-note",
                "K-드라마 발라드 — 노래형 선율과 후반 다이내믹 상승", "B♭ major / G minor",
                "장·단조 교차 발라드 진행과 종지 확장", "intro–verse–pre-chorus–chorus–bridge–final chorus–coda",
                "projects/storybook-rain-cloud-100s/", seed, notes, bars, 4 * beat)


def minimal_ambient() -> dict:
    """6/8 minimal piano: deliberately sparse, slowly shifting cells and silence."""
    tempo, dotted, bars, seed = 54, 60 / 54, 270, 10505
    rng, notes = random.Random(seed), []
    # Two dotted-quarter beats per 6/8 bar. 270 * 2 * 60/54 == 600 seconds exactly.
    cells = [(60, (0, 7, 12)), (57, (0, 7, 12)), (65, (0, 7, 11)), (62, (0, 7, 12)),
             (60, (0, 4, 11)), (55, (0, 7, 12)), (57, (0, 3, 10)), (60, (0, 7, 12))]
    for bar in range(bars):
        at, section = bar * 2 * dotted, bar // 30
        root, cell = cells[(bar // 3 + section) % len(cells)]
        # A single low pulse, a high answer, and intentionally omitted cells make the room feel large.
        add(notes, at, (root - 24,), 1.55 * dotted, 32 + rng.randint(-2, 2), 0.08, "ambient-pulse")
        if bar % 3 != 1:
            add(notes, at + 0.42 * dotted, (root + cell[1],), 1.12 * dotted, 35 + rng.randint(-2, 2), 0.075, "ambient-ostinato")
        if bar % 4 in (0, 3):
            high = root + 12 + cell[2] + (12 if section % 3 == 2 else 0)
            add(notes, at + 1.16 * dotted, (high,), 1.55 * dotted, 38 + rng.randint(-3, 2), 0.10, "ambient-answer")
        if bar % 12 == 11:
            add(notes, at + 1.58 * dotted, (root + 7, root + 12), 0.75 * dotted, 33, 0.06, "ambient-shift")
        # Every 30 bars, a small octave echo marks a formal change without becoming a chorus.
        if bar % 30 == 29:
            add(notes, at + 0.9 * dotted, (root + 24,), 1.0 * dotted, 40, 0.085, "ambient-marker")
    return meta("minimal-ambient-tide", "고요한 조수의 방", tempo, "6/8", "dotted-quarter",
                "미니멀 앰비언트 피아노 — 6/8 여백과 느린 오스티나토 변화", "C major / A minor",
                "C장조·A단조 인접 화음의 느린 세포 이동", "opening cell–gradual shifts–open middle–return–dissolve",
                "output/deepsea-light-v01-60-final-contact-sheet.jpg", seed, notes, bars, 2 * dotted)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args()
    pieces = [neo_classical(), jazz_ballad(), bossa_nova(), drama_ballad(), minimal_ambient()]
    args.out_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for piece in pieces:
        target = args.out_root / piece["id"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "composition.json").write_text(json.dumps(piece, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows.append({key: piece[key] for key in ("id", "title", "durationSec", "tempoBpm", "tempoUnit", "timeSignature", "genre", "groove", "keyCenter", "form")})
        rows[-1]["noteCount"] = len(piece["notes"])
    manifest = {"schemaVersion": 2, "durationSec": DURATION, "collection": "genre-distinct-sampled-piano", "tracks": rows}
    (args.out_root / "collection.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
