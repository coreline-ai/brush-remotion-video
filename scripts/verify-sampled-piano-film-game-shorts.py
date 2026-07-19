#!/usr/bin/env python3
"""Technical QA and provenance for five 30-second film/game piano shorts."""
from __future__ import annotations
import hashlib, json, re, subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'projects/sampled-piano-film-game-shorts'
OUT = ROOT / 'output/original-audio/sampled-piano-film-game-shorts'

def run(*args): return subprocess.run(args, check=True, text=True, capture_output=True)
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1_048_576), b''): h.update(b)
    return h.hexdigest()
def probe(p):
    d=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)).stdout)
    a=next(x for x in d['streams'] if x['codec_type']=='audio')
    return {'codec':a['codec_name'],'sampleRateHz':int(a['sample_rate']),'channels':a['channels'],'bitsPerRawSample':int(a.get('bits_per_raw_sample') or a.get('bits_per_sample') or 0),'durationSec':float(d['format']['duration'])}
def loudness(p):
    r=run('ffmpeg','-hide_banner','-nostats','-i',str(p),'-af','loudnorm=I=-20:LRA=7:TP=-1.5:print_format=json','-f','null','-')
    block=re.findall(r'\{\s*"input_i".*?\}',r.stderr,re.S)[-1]
    d=json.loads(block); return {'integratedLufs':float(d['input_i']),'truePeakDbtp':float(d['input_tp']),'lra':float(d['input_lra'])}
def main():
    manifest=json.loads((PROJECT/'collection.json').read_text())
    catalog=json.loads((ROOT/'assets/instruments/catalog.json').read_text())['instruments'][0]
    tracks=[]; failures=[]; genres=set()
    for row in manifest['tracks']:
        ident=row['id']; comp=PROJECT/ident/'composition.json'; raw=OUT/ident/'raw-48k24.wav'; master=OUT/ident/f'{ident}-30s-44k16.wav'; report=OUT/ident/'render-report.json'
        meta=json.loads(comp.read_text()); rendered=json.loads(report.read_text()); tech=probe(master); rawtech=probe(raw); loud=loudness(master); genres.add(meta['genre'])
        valid=(meta['durationSec']==30 and abs(meta['bars']*meta['barDurationSec']-30)<1e-5 and tech['codec']=='pcm_s16le' and tech['sampleRateHz']==44100 and tech['channels']==2 and tech['bitsPerRawSample']==16 and abs(tech['durationSec']-30)<.01 and rawtech['codec']=='pcm_s24le' and rawtech['sampleRateHz']==48000 and rendered['uniqueSampleCount']>=10 and loud['truePeakDbtp']<=-.5)
        if not valid: failures.append(ident)
        item={'schemaVersion':2,'id':ident,'title':meta['title'],'genre':meta['genre'],'musicalProfile':{x:meta[x] for x in ('tempoBpm','tempoUnit','timeSignature','groove','keyCenter','harmony','form')},'noteCount':len(meta['notes']),'source':'original note-event composition rendered from local piano samples only','instrument':{'id':catalog['id'],'archiveSha256':catalog['acquisition']['archiveSha256'],'license':catalog['license']},'compositionSha256':sha(comp),'rendererSha256':sha(ROOT/'scripts/render-sampled-piano.py'),'rawSha256':sha(raw),'masterSha256':sha(master),'render':rendered,'rawTechnical':rawtech,'technical':tech,'loudness':loud,'masterFile':str(master)}
        (OUT/ident/'provenance.json').write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n'); tracks.append(item)
    diversity={'fiveTracks':len(tracks)==5,'uniqueGenres':len(genres)==5}
    if not all(diversity.values()): failures.append('style-diversity')
    qa={'schemaVersion':2,'createdAt':datetime.now().astimezone().isoformat(timespec='seconds'),'collection':manifest['collection'],'verdict':'PASS' if not failures else 'FAIL','failures':failures,'styleDiversity':diversity,'tracks':tracks}
    (OUT/'collection-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    lines=['# Film/game piano shorts — YouTube attribution','',catalog['license']['attributionText'],f"Changes: {catalog['license']['modificationNotice']}",'']
    lines += [f"- {x['title']} ({x['genre']}) — original composition; {x['masterFile']}" for x in tracks]
    (OUT/'youtube-description.txt').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'verdict':qa['verdict'],'styleDiversity':diversity,'tracks':[{'id':x['id'],'technical':x['technical'],'loudness':x['loudness'],'sampleCount':x['render']['uniqueSampleCount']} for x in tracks]},ensure_ascii=False,indent=2))
    if failures: raise SystemExit(1)
if __name__=='__main__': main()
