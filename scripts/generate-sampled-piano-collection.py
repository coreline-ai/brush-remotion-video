#!/usr/bin/env python3
"""Write five deterministic, original 10-minute piano compositions as note events."""
from __future__ import annotations
import argparse, json, random
from pathlib import Path

DURATION = 600.0
THEMES = (
  ("star-seed", "별씨앗의 밤", 58, 62, "major", 1101, "D major; star-seed fairy-tale imagery"),
  ("rain-cloud", "창가의 빗구름", 54, 55, "major", 2202, "G major/E minor; rain-cloud storybook imagery"),
  ("deepsea-light", "심해의 푸른 등불", 52, 64, "minor", 3303, "C# minor/E major; deepsea light imagery"),
  ("cosmic-ink", "먹빛 성운", 56, 59, "minor", 4404, "B minor; cosmic ink brush imagery"),
  ("africa-dusk", "황금 초원의 저녁", 60, 57, "pentatonic", 5505, "A major; Africa watercolor dusk imagery"),
)
SCALES = {"major": (0,2,4,5,7,9,11), "minor": (0,2,3,5,7,8,10), "pentatonic": (0,2,4,7,9)}
PROGRESSIONS = {
 "major": ((0,"M"),(4,"M"),(5,"m"),(3,"M"),(0,"M"),(5,"m"),(1,"m"),(4,"M")),
 "minor": ((0,"m"),(5,"M"),(2,"M"),(6,"M"),(0,"m"),(3,"m"),(6,"M"),(4,"M")),
 "pentatonic": ((0,"M"),(4,"M"),(1,"m"),(3,"M"),(0,"M"),(1,"m"),(4,"M"),(0,"M")),
}
MOTIFS = ((0,2,4,2),(4,2,1,0),(2,4,5,4),(0,1,2,4),(4,5,4,2))

def note(start, midi, hold, velocity, gain):
    return {"startSec": round(start,6), "midi": int(max(21,min(108,midi))), "holdSec": round(hold,6), "velocity": int(max(1,min(127,velocity))), "gain": round(gain,4)}

def make_theme(spec):
    ident, title, bpm, tonic, mode, seed, image_note = spec
    beat, bar = 60/bpm, 240/bpm
    bars = round(DURATION/bar)
    assert abs(bars*bar-DURATION) < 1e-8
    scale, progression, rng, notes = SCALES[mode], PROGRESSIONS[mode], random.Random(seed), []
    for b in range(bars):
        section, at = b//10, b*bar
        degree, quality = progression[(b + section*3 + (section//4)) % len(progression)]
        root = tonic + scale[degree % len(scale)]
        chord = (0,4,7) if quality == "M" else (0,3,7)
        energy = 0.76 + 0.18*(1-abs((b/(bars-1))*2-1))
        # Four soft left-hand notes; register is limited to avoid a boomy bed.
        for step, interval in enumerate((0,7,12,7)):
            notes.append(note(at+step*beat, root-19+interval, beat*1.65, int((34+(step==0)*5)*energy+rng.randint(-2,2)), 0.105))
        motif = MOTIFS[(section + b//3) % len(MOTIFS)]
        # Phrase answers vary with section index; no 60-second audio loop is repeated.
        for step, degree_index in enumerate(motif):
            if (b+step+section) % 11 == 0: continue
            octave = 12 if step in (1,2) else 0
            melodic = tonic + 12 + scale[(degree+degree_index+section)%len(scale)] + octave
            notes.append(note(at+(0.45+step*0.83)*beat, melodic, beat*(0.92 if step<3 else 1.35), int((46+step*3)*energy+rng.randint(-3,3)), 0.13))
        if b % 5 == 4:
            notes.append(note(at+3.35*beat, root+19, beat*0.55, int(43*energy), 0.105))
    return {"schemaVersion":1,"id":ident,"title":title,"durationSec":DURATION,"tempoBpm":bpm,"seed":seed,"imageReference":image_note,"notes":notes}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-root',type=Path,required=True); a=ap.parse_args()
    rows=[]
    for spec in THEMES:
        data=make_theme(spec); d=a.out_root/data['id']; d.mkdir(parents=True,exist_ok=True)
        (d/'composition.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        rows.append({"id":data['id'],"durationSec":data['durationSec'],"tempoBpm":data['tempoBpm'],"noteCount":len(data['notes'])})
    (a.out_root/'collection.json').write_text(json.dumps({"schemaVersion":1,"durationSec":DURATION,"tracks":rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__': main()
