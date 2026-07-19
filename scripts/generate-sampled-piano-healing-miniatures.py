#!/usr/bin/env python3
"""Write six original one-minute piano pieces for distinct healing/new-age styles.

Only note events are produced. No finished recording, loop, or online audio is read.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

DURATION = 60.0


def event(start, midi, hold, velocity, gain, part):
    return {"startSec": round(start, 6), "midi": int(max(21, min(108, midi))),
            "holdSec": round(max(0.06, hold), 6), "velocity": int(max(1, min(127, velocity))),
            "gain": round(gain, 4), "part": part}


def put(notes, start, tones, hold, velocity, gain, part):
    for tone in tones:
        notes.append(event(start, tone, hold, velocity, gain, part))


def piece(ident, title, tempo, unit, meter, genre, groove, key, harmony, form, seed, bars, bar_sec, notes):
    assert abs(bars * bar_sec - DURATION) < 1e-7
    assert notes and all(0 <= n["startSec"] < DURATION and n["holdSec"] > 0 for n in notes)
    return {"schemaVersion": 2, "id": ident, "title": title, "durationSec": DURATION,
            "tempoBpm": tempo, "tempoUnit": unit, "timeSignature": meter, "genre": genre,
            "groove": groove, "keyCenter": key, "harmony": harmony, "form": form,
            "seed": seed, "bars": bars, "barDurationSec": round(bar_sec, 9),
            "instrumentation": "solo acoustic grand piano samples only", "notes": sorted(notes, key=lambda n: (n["startSec"], n["midi"]))}


def new_age() -> dict:
    # 68 BPM 4/4 -> exactly 17 bars in 60 seconds.
    bpm, beat, bars, seed = 68, 60 / 68, 17, 1168
    rng, notes = random.Random(seed), []
    changes = [(55, (0, 4, 7)), (62, (0, 4, 7)), (64, (0, 3, 7)), (60, (0, 4, 7)), (55, (0, 4, 7)), (62, (0, 4, 7)), (57, (0, 3, 7)), (60, (0, 4, 7))]
    g_major = (0, 2, 4, 5, 7, 9, 11)
    for bar in range(bars):
        at = bar * 4 * beat
        root, shape = changes[bar % len(changes)]
        # The right hand grows from the arpeggio, rather than sitting as a separate layer.
        steps = (root - 24, root - 12 + shape[1], root - 12 + shape[2], root + shape[1], root + shape[2])
        for i, tone in enumerate(steps):
            put(notes, at + (0.00, .72, 1.45, 2.23, 3.04)[i] * beat, (tone,), .92 * beat,
                38 + i * 2 + rng.randint(-2, 2), .088, "interwoven-arpeggio")
        if bar % 2 == 0:
            for i, degree in enumerate((2, 4, 5, 4)):
                tone = 72 + g_major[(degree + bar // 4) % len(g_major)] + (12 if i == 2 else 0)
                put(notes, at + (.36 + i * .76) * beat, (tone,), (.56 if i < 3 else 1.18) * beat,
                    48 + rng.randint(-2, 3), .112, "new-age-melody")
    return piece("new-age-horizon", "빛의 수평선", bpm, "quarter-note", "4/4", "뉴에이지", "흐르는 아르페지오", "G major", "맑은 I–V–vi–IV 순환", "A–A′–B–return", seed, bars, 4 * beat, notes)


def ambient_piano() -> dict:
    # 48 BPM 4/4 -> 12 spacious five-second bars.
    bpm, beat, bars, seed = 48, 1.25, 12, 2048
    rng, notes = random.Random(seed), []
    colors = [(50, (0, 7, 14)), (57, (0, 7, 16)), (53, (0, 7, 14)), (48, (0, 7, 16)), (50, (0, 9, 16)), (45, (0, 7, 14))]
    for bar in range(bars):
        at = bar * 4 * beat
        root, color = colors[(bar // 2) % len(colors)]
        put(notes, at, (root - 12,), 3.3 * beat, 29 + rng.randint(-1, 2), .085, "low-resonance")
        put(notes, at + .44 * beat, (root + color[1],), 2.5 * beat, 32 + rng.randint(-1, 2), .075, "space-tone")
        # Alternate bars have silence in the middle; this is intentionally not a steady accompaniment.
        if bar % 2 == 0:
            put(notes, at + 2.42 * beat, (root + color[2],), 1.95 * beat, 35 + rng.randint(-2, 2), .100, "high-reflection")
        if bar in (3, 7, 11):
            put(notes, at + 3.18 * beat, (root + 12, root + color[1]), 1.05 * beat, 31, .060, "distant-chord")
    return piece("ambient-piano-reflection", "물결의 반사", bpm, "quarter-note", "4/4", "앰비언트 피아노", "긴 잔향과 비대칭 여백", "D minor / F major", "open fifth·added ninth 색채", "slowly opening space", seed, bars, 4 * beat, notes)


def sleep_piano() -> dict:
    # 60 BPM 3/4 -> 20 bars, a piano lullaby rather than a drone.
    bpm, beat, bars, seed = 60, 1.0, 20, 3060
    rng, notes = random.Random(seed), []
    changes = [(60, (0, 4, 7)), (57, (0, 3, 7)), (65, (0, 4, 7)), (67, (0, 4, 7)), (60, (0, 4, 7))]
    c_major = (0, 2, 4, 5, 7, 9, 11)
    for bar in range(bars):
        at = bar * 3 * beat
        root, shape = changes[bar % len(changes)]
        put(notes, at, (root - 24,), 1.35, 31 + rng.randint(-2, 2), .085, "lullaby-bass")
        put(notes, at + 1, (root - 12 + shape[2],), .90, 34 + rng.randint(-2, 2), .078, "lullaby-rock")
        put(notes, at + 2, (root - 12 + shape[1],), .90, 33 + rng.randint(-2, 2), .078, "lullaby-rock")
        melody = (4, 2, 0) if bar % 4 < 2 else (2, 4, 5)
        for i, degree in enumerate(melody):
            if bar % 5 == 4 and i == 1:
                continue
            tone = 72 + c_major[(degree + (bar // 5) * 2) % len(c_major)]
            put(notes, at + (.18 + i * .86), (tone,), .68 if i < 2 else 1.05, 40 + rng.randint(-2, 2), .100, "lullaby-voice")
    return piece("sleep-piano-cradle", "달빛 요람", bpm, "quarter-note", "3/4", "수면 피아노", "3박자 자장가 흐름", "C major / A minor", "단순 장·단조 자장가 종지", "lullaby verses–soft return", seed, bars, 3 * beat, notes)


def meditation_piano() -> dict:
    # 40 BPM 4/4 -> 10 six-second bars; no frequency/drone assertion, only sparse piano intervals.
    bpm, beat, bars, seed = 40, 1.5, 10, 4040
    rng, notes = random.Random(seed), []
    sequence = [(50, 57), (53, 60), (57, 64), (50, 57), (48, 55)]
    for bar in range(bars):
        at = bar * 4 * beat
        low, high = sequence[bar % len(sequence)]
        put(notes, at, (low - 12, low + 7), 2.35 * beat, 28 + rng.randint(-1, 2), .080, "meditation-fifth")
        put(notes, at + 1.42 * beat, (high + 12,), 1.85 * beat, 32 + rng.randint(-1, 2), .095, "meditation-bell-tone")
        if bar % 2 == 1:
            put(notes, at + 3.02 * beat, (high + 5,), .92 * beat, 29, .072, "meditation-release")
    return piece("meditation-piano-still", "고요의 중심", bpm, "quarter-note", "4/4", "명상 피아노", "열린 5도와 긴 호흡", "D minor", "open fifths와 느린 상행 응답", "breath–pause–breath", seed, bars, 4 * beat, notes)


def lofi_piano() -> dict:
    # 80 BPM 4/4 -> 20 bars; piano-only lo-fi harmony and laid-back syncopation.
    bpm, beat, bars, seed = 80, .75, 20, 5080
    rng, notes = random.Random(seed), []
    # root, 3rd, 7th, 9th: deliberately jazzier than the other five pieces.
    chords = [(57, (4, 10, 14)), (62, (3, 10, 14)), (55, (4, 10, 14)), (60, (4, 11, 14)), (57, (4, 10, 14)), (64, (3, 10, 14)), (62, (3, 10, 14)), (67, (4, 10, 14))]
    for bar in range(bars):
        at = bar * 4 * beat
        root, colors = chords[(bar + bar // 8) % len(chords)]
        put(notes, at, (root - 24,), 1.35 * beat, 42 + rng.randint(-2, 2), .092, "lofi-bass")
        put(notes, at + 2.48 * beat, (root - 19,), .68 * beat, 37 + rng.randint(-2, 2), .080, "lofi-late-bass")
        voicing = tuple(root + x + 12 for x in colors)
        for pos, hold in ((.66, .44), (1.72, .38), (3.10, .56)):
            put(notes, at + pos * beat, voicing, hold * beat, 44 + rng.randint(-2, 3), .062, "lofi-chop")
        if bar % 2 == 0:
            for i, pos in enumerate((.28, 1.02, 1.62, 2.82, 3.46)):
                tone = (69, 72, 76, 74, 71)[(i + bar // 4) % 5] + (12 if i == 3 else 0)
                put(notes, at + pos * beat, (tone,), (.42 if i != 4 else .78) * beat, 46 + rng.randint(-2, 3), .105, "lofi-hook")
    return piece("lofi-piano-window", "창가의 느린 오후", bpm, "quarter-note", "4/4", "로파이 피아노", "느슨한 당김음 코드 컴핑", "A minor / C major", "m7·maj7·9th 코드", "loop-like motif with changing harmony", seed, bars, 4 * beat, notes)


def minimal_ambient() -> dict:
    # 60 BPM, dotted-quarter unit: 30 6/8 bars of two seconds each.
    bpm, dotted, bars, seed = 60, 1.0, 30, 6060
    rng, notes = random.Random(seed), []
    cells = [(60, 67, 72), (57, 64, 69), (53, 60, 67), (55, 62, 69)]
    for bar in range(bars):
        at = bar * 2 * dotted
        root, mid, high = cells[(bar // 5) % len(cells)]
        put(notes, at, (root - 24,), 1.35 * dotted, 30 + rng.randint(-1, 2), .082, "minimal-pulse")
        if bar % 3 != 1:
            put(notes, at + .5 * dotted, (mid,), .92 * dotted, 33 + rng.randint(-1, 2), .078, "minimal-cell")
        if bar % 5 in (0, 4):
            put(notes, at + 1.22 * dotted, (high + (12 if bar >= 15 else 0),), .68 * dotted, 36 + rng.randint(-2, 2), .098, "minimal-shift")
    return piece("minimal-ambient-tide-mini", "작은 조수의 방", bpm, "dotted-quarter", "6/8", "미니멀 앰비언트", "반복 세포의 느린 이동", "C major / A minor", "5마디마다 이동하는 열린 음정", "cell–shift–cell–dissolve", seed, bars, 2 * dotted, notes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args()
    tracks = [new_age(), ambient_piano(), sleep_piano(), meditation_piano(), lofi_piano(), minimal_ambient()]
    args.out_root.mkdir(parents=True, exist_ok=True)
    index = []
    for track in tracks:
        folder = args.out_root / track["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "composition.json").write_text(json.dumps(track, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        item = {key: track[key] for key in ("id", "title", "genre", "tempoBpm", "tempoUnit", "timeSignature", "groove", "keyCenter", "form")}
        item["noteCount"] = len(track["notes"])
        index.append(item)
    (args.out_root / "collection.json").write_text(json.dumps({"schemaVersion": 2, "durationSec": DURATION, "collection": "healing-new-age-piano-miniatures", "tracks": index}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
