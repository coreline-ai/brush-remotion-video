#!/usr/bin/env python3
"""Write provenance and technical QA for the five sampled-piano masters."""
from __future__ import annotations
import hashlib, json, re, subprocess
from datetime import datetime
from pathlib import Path

IDS=("star-seed","rain-cloud","deepsea-light","cosmic-ink","africa-dusk")
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/original-audio/sampled-piano-collection'

def sha(p: Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def run(*args): return subprocess.run(args,capture_output=True,text=True,check=True)
def probe(p:Path):
 d=json.loads(run('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)).stdout)
 a=next(s for s in d['streams'] if s['codec_type']=='audio')
 return {'codec':a['codec_name'],'sampleRateHz':int(a['sample_rate']),'channels':a['channels'],'bitsPerRawSample':int(a.get('bits_per_raw_sample') or a.get('bits_per_sample') or 0),'durationSec':float(d['format']['duration'])}
def loudness(p:Path):
 r=run('ffmpeg','-hide_banner','-nostats','-i',str(p),'-af','loudnorm=I=-20:LRA=7:TP=-1.5:print_format=json','-f','null','-')
 m=re.findall(r'\{\s*"input_i".*?\}',r.stderr,re.S)
 if not m: raise RuntimeError('loudnorm JSON not found')
 d=json.loads(m[-1]); return {'integratedLufs':float(d['input_i']),'truePeakDbtp':float(d['input_tp']),'lra':float(d['input_lra'])}
def main():
 catalog=json.loads((ROOT/'assets/instruments/catalog.json').read_text())['instruments'][0]
 tracks=[]; failures=[]
 for ident in IDS:
  comp=ROOT/'projects/sampled-piano-collection'/ident/'composition.json'
  raw=OUT/ident/'raw-48k24.wav'; master=OUT/ident/f'{ident}-10m-44k16.wav'
  meta=json.loads(comp.read_text()); technical=probe(master); measured=loudness(master)
  ok=(technical['codec']=='pcm_s16le' and technical['sampleRateHz']==44100 and technical['channels']==2 and technical['bitsPerRawSample']==16 and abs(technical['durationSec']-600)<.01 and measured['truePeakDbtp']<=-0.5)
  if not ok: failures.append(ident)
  item={'schemaVersion':1,'id':ident,'title':meta['title'],'imageReference':meta['imageReference'],'durationSec':meta['durationSec'],'tempoBpm':meta['tempoBpm'],'seed':meta['seed'],'noteCount':len(meta['notes']),'instrument':{'id':catalog['id'],'archiveSha256':catalog['acquisition']['archiveSha256'],'license':catalog['license']},'compositionSha256':sha(comp),'rendererSha256':sha(ROOT/'scripts/render-sampled-piano.py'),'rawSha256':sha(raw),'masterSha256':sha(master),'technical':technical,'loudness':measured,'masterFile':str(master)}
  (OUT/ident/'provenance.json').write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
  tracks.append(item)
 report={'schemaVersion':1,'createdAt':datetime.now().astimezone().isoformat(timespec='seconds'),'verdict':'PASS' if not failures else 'FAIL','failures':failures,'tracks':tracks}
 (OUT/'collection-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 attribution=catalog['license']['attributionText']; changes=catalog['license']['modificationNotice']
 lines=['# Sampled Piano Collection — YouTube attribution','',attribution,f'Changes: {changes}','',*['- '+x['title']+' — original MIDI composition; '+x['masterFile'] for x in tracks]]
 (OUT/'youtube-description.txt').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'verdict':report['verdict'],'tracks':[{k:x[k] for k in ('id','technical','loudness','masterSha256')} for x in tracks]},ensure_ascii=False,indent=2))
 if failures: raise SystemExit(1)
if __name__=='__main__': main()
