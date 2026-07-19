#!/usr/bin/env python3
"""Create five original 30-second film/game piano miniatures as note events only."""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path

DURATION = 30.0


def note(start, midi, hold, velocity, gain, part):
    return {"startSec": round(start, 6), "midi": int(max(21, min(108, midi))), "holdSec": round(max(.05, hold), 6), "velocity": int(max(1, min(127, velocity))), "gain": round(gain, 4), "part": part}


def put(notes, start, tones, hold, velocity, gain, part):
    for tone in tones:
        notes.append(note(start, tone, hold, velocity, gain, part))


def build(ident, title, bpm, unit, meter, genre, groove, key, harmony, form, seed, bars, bar_sec, notes):
    assert abs(bars * bar_sec - DURATION) < 1e-7
    assert notes and all(0 <= x['startSec'] < DURATION and x['holdSec'] > 0 for x in notes)
    return {"schemaVersion": 2, "id": ident, "title": title, "durationSec": DURATION, "tempoBpm": bpm, "tempoUnit": unit, "timeSignature": meter, "genre": genre, "groove": groove, "keyCenter": key, "harmony": harmony, "form": form, "seed": seed, "bars": bars, "barDurationSec": round(bar_sec, 9), "instrumentation": "solo acoustic grand piano samples only", "notes": sorted(notes, key=lambda x:(x['startSec'], x['midi']))}


def cinematic():
    # 56 BPM in 4/4 gives exactly seven 30/7-second bars.
    bpm, beat, bars, seed = 56, 60 / 56, 7, 7156
    rng, notes = random.Random(seed), []
    changes = [(48, (0, 3, 7)), (44, (0, 3, 7)), (41, (0, 3, 7)), (43, (0, 4, 7)), (48, (0, 3, 7)), (51, (0, 4, 7)), (48, (0, 3, 7))]
    for bar, (root, shape) in enumerate(changes):
        at, energy = bar * 4 * beat, .72 + bar * .06
        put(notes, at, (root - 24, root - 12), 2.1 * beat, int(35 * energy) + rng.randint(-2, 2), .09, "cinematic-octave")
        for i, tone in enumerate((root + shape[1], root + shape[2], root + 12, root + 12 + shape[1])):
            put(notes, at + (.56 + i * .66) * beat, (tone,), .8 * beat, int((38 + i * 2) * energy) + rng.randint(-2, 2), .082, "rising-figure")
        motif = (67, 70, 72, 75) if bar < 4 else (72, 75, 79, 84)
        for i, tone in enumerate(motif):
            if bar == 0 and i > 1: continue
            put(notes, at + (.28 + i * .79) * beat, (tone,), (.48 if i < 3 else 1.12) * beat, int((44 + i * 2) * energy) + rng.randint(-2, 2), .115, "cinematic-theme")
    return build("cinematic-piano-rise", "새벽 이전의 장면", bpm, "quarter-note", "4/4", "시네마틱 피아노", "점층 아르페지오와 넓은 옥타브", "C minor", "minor progression with rising final cadence", "whisper–rise–arrival", seed, bars, 4 * beat, notes)


def film_ost():
    # 60 BPM 3/4: ten emotional waltz bars.
    bpm, beat, bars, seed = 60, 1.0, 10, 8160
    rng, notes = random.Random(seed), []
    changes = [(62,(0,4,7)), (69,(0,4,7)), (71,(0,3,7)), (67,(0,4,7)), (64,(0,3,7)), (69,(0,4,7)), (62,(0,4,7)), (57,(0,3,7)), (67,(0,4,7)), (62,(0,4,7))]
    scale = (0, 2, 4, 5, 7, 9, 11)
    for bar, (root, shape) in enumerate(changes):
        at = bar * 3 * beat
        put(notes, at, (root - 24,), 1.32, 34 + rng.randint(-2, 2), .09, "ost-bass")
        put(notes, at + 1, (root - 12 + shape[1], root - 12 + shape[2]), .66, 38 + rng.randint(-2, 2), .065, "ost-waltz")
        put(notes, at + 2, (root + shape[1],), .72, 39 + rng.randint(-2, 2), .075, "ost-waltz")
        for i, degree in enumerate((2, 4, 5)):
            tone = 74 + scale[(degree + bar // 3) % len(scale)] + (12 if bar >= 6 and i == 2 else 0)
            put(notes, at + (.16 + i * .79), (tone,), .55 if i < 2 else 1.05, 45 + rng.randint(-2, 3), .112, "ost-vocal-theme")
    return build("film-ost-memory", "기억의 엔딩 크레딧", bpm, "quarter-note", "3/4", "영화 OST풍", "서정적인 3박자 선율", "D major / B minor", "lyrical major-minor film cadence", "opening–memory–lift–resolve", seed, bars, 3 * beat, notes)


def game_bgm():
    # 60 dotted-quarter BPM, 6/8: fifteen compact two-second gameplay bars.
    bpm, dotted, bars, seed = 60, 1.0, 15, 9060
    rng, notes = random.Random(seed), []
    changes = [(52, (0,3,7)), (55,(0,3,7)), (48,(0,4,7)), (50,(0,3,7)), (52,(0,3,7))]
    for bar in range(bars):
        at = bar * 2 * dotted
        root, shape = changes[(bar // 3) % len(changes)]
        for i, tone in enumerate((root - 12, root + shape[2], root + 12 + shape[1], root + 12 + shape[2], root + 12 + shape[1], root + 19)):
            put(notes, at + i / 3, (tone,), .29, 39 + (i % 3) * 2 + rng.randint(-2, 2), .084, "game-ostinato")
        if bar % 2 == 0:
            for i, tone in enumerate((76, 79, 83, 79)):
                put(notes, at + (.18 + i * .45), (tone + (12 if bar in (8, 12) and i == 2 else 0),), .34, 48 + rng.randint(-2, 3), .108, "game-hook")
    return build("game-bgm-quest", "작은 퀘스트의 길", bpm, "dotted-quarter", "6/8", "게임 BGM풍", "6/8 오스티나토와 짧은 훅", "E minor", "minor adventure loop with clear checkpoints", "explore–checkpoint–explore", seed, bars, 2 * dotted, notes)


def fantasy():
    # 72 BPM 3/4: twelve 2.5-second bars.
    bpm, beat, bars, seed = 72, 60 / 72, 12, 10072
    rng, notes = random.Random(seed), []
    # D Lydian color: G# is a deliberate raised fourth.
    roots = (62, 69, 64, 62, 59, 64, 69, 62, 64, 69, 62, 62)
    lydian = (0, 2, 4, 6, 7, 9, 11)
    for bar, root in enumerate(roots):
        at = bar * 3 * beat
        put(notes, at, (root - 24,), 1.4 * beat, 31 + rng.randint(-2, 2), .085, "fantasy-root")
        put(notes, at + .84 * beat, (root - 12 + 7, root + 6), .74 * beat, 35 + rng.randint(-2, 2), .065, "fantasy-glimmer")
        for i, degree in enumerate((0, 2, 3, 4, 6)):
            tone = 78 + lydian[(degree + bar // 3) % len(lydian)] + (12 if i == 3 and bar > 5 else 0)
            put(notes, at + (.12 + i * .52) * beat, (tone,), .38 * beat, 42 + rng.randint(-2, 3), .103, "fantasy-spark")
    return build("fantasy-piano-starlight", "별빛 도서관", bpm, "quarter-note", "3/4", "판타지 피아노", "리디안 고음 음형", "D Lydian", "raised-fourth fantasy color", "portal–flight–landing", seed, bars, 3 * beat, notes)


def mystery_horror():
    # 48 BPM 4/4: six sparse five-second bars, with silence and controlled dissonance.
    bpm, beat, bars, seed = 48, 1.25, 6, 1148
    rng, notes = random.Random(seed), []
    structures = [(37, 43, 68), (40, 46, 71), (37, 44, 69), (35, 42, 66), (37, 43, 73), (32, 38, 68)]
    for bar, (low, tritone, high) in enumerate(structures):
        at = bar * 4 * beat
        put(notes, at, (low,), 1.75 * beat, 27 + rng.randint(-1, 2), .09, "horror-low")
        put(notes, at + .88 * beat, (tritone,), 1.18 * beat, 30 + rng.randint(-1, 2), .082, "horror-tritone")
        if bar != 2:
            put(notes, at + 2.42 * beat, (high,), .62 * beat, 34 + rng.randint(-2, 2), .108, "horror-question")
        if bar in (1, 4):
            put(notes, at + 3.35 * beat, (high + 1,), .30 * beat, 29, .070, "horror-semitone")
    return build("mystery-horror-piano-door", "닫힌 문 너머", bpm, "quarter-note", "4/4", "미스터리·호러 피아노", "낮은 간격·트라이톤·침묵", "C# minor / chromatic", "sparse minor seconds and tritone tension", "question–silence–question", seed, bars, 4 * beat, notes)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out-root', type=Path, required=True); args = parser.parse_args()
    tracks = [cinematic(), film_ost(), game_bgm(), fantasy(), mystery_horror()]
    args.out_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for track in tracks:
        target = args.out_root / track['id']; target.mkdir(parents=True, exist_ok=True)
        (target / 'composition.json').write_text(json.dumps(track, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        row = {key: track[key] for key in ('id','title','genre','tempoBpm','tempoUnit','timeSignature','groove','keyCenter','form')}; row['noteCount'] = len(track['notes']); rows.append(row)
    (args.out_root / 'collection.json').write_text(json.dumps({'schemaVersion':2,'durationSec':DURATION,'collection':'film-game-sampled-piano-shorts','tracks':rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(rows, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
