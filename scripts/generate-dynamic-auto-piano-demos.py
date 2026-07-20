#!/usr/bin/env python3
"""Create three energetic, auto-engine piano listening demos."""
from __future__ import annotations
import array, hashlib, html, json, math, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'piano-auto-dynamic-3-demo'
PROJECTS=ROOT/'projects'/'piano-bgm'
SOURCES=ROOT/'output'/'original-audio'/'piano-bgm'
PYTHON=ROOT/'pipeline'/'.venv'/'bin'/'python'
CLI=ROOT/'bin'/'piano-bgm.py'
SAMPLES=[
 ('cinematic-charge','시네마틱 차지','cinematic-piano','C-minor',96,'강하게 시작해 넓은 옥타브와 상승하는 아르페지오로 전진하는 피아노','dynamic cinematic charge, solo grand piano, urgent rise, wide octaves, driving arpeggios, no vocals','grand determined rise'),
 ('game-run','게임 퀘스트 런','game-bgm-piano','E-minor',122,'빠른 6/8 오스티나토와 짧은 훅으로 달려가는 모험 피아노','energetic game quest piano, fast 6/8 ostinato, memorable hook, no vocals','bright heroic pursuit'),
 ('film-finale','영화 피날레','film-ost-piano','D-major',108,'노래형 선율이 앞으로 치고 나가며 힘 있게 종지하는 피아노','powerful film finale piano, singing melody, rising cadence, no vocals','triumphant emotional finale'),
]

def run(capture=False,*cmd):
 r=subprocess.run(list(cmd),cwd=ROOT,text=True,check=True,capture_output=capture)
 return r.stdout if capture else ''
def duration(p): return float(run(True,'ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)).strip())
def metrics(p):
 t=Path('/private/tmp')/(p.stem+'.f32')
 try:
  run(False,'ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p),'-f','f32le','-acodec','pcm_f32le',str(t))
  x=array.array('f');x.frombytes(t.read_bytes());peak=max(map(abs,x),default=0)
  return {'decodedPeakDbfs':round(20*math.log10(max(peak,1e-12)),2),'clippingSamples':sum(abs(v)>=.999 for v in x)}
 finally:t.unlink(missing_ok=True)
def page(entries):
 cards=''.join(f'''<article class="card"><div class="header"><span>{e['index']:02}</span><div><small>{html.escape(e['preset'])}</small><h2>{html.escape(e['label'])}</h2></div></div><p>{html.escape(e['description'])}</p><audio controls preload="metadata" src="{e['file']}"></audio><em>{e['tempo']} BPM · 10초 데모 · 피크 {e['decodedPeakDbfs']:.2f} dBFS · 무클리핑</em></article>''' for e in entries)
 return f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>역동적 자동 피아노 3종</title><style>:root{{--ink:#eff5fb;--sub:#b5c7d8;--line:#35546e;--hot:#ffcb6f}}*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;color:var(--ink);background:radial-gradient(circle at 75% 0,#70462a,transparent 42%),linear-gradient(135deg,#101927,#19334a);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}}header{{padding:60px max(24px,8vw) 35px;border-bottom:1px solid var(--line)}}h1{{font-size:clamp(34px,6vw,63px);letter-spacing:-.06em;line-height:1.08;margin:0}}header p{{max-width:800px;color:var(--sub);font-size:17px}}main{{width:min(1040px,calc(100vw - 36px));margin:30px auto 65px}}.notice{{padding:17px 21px;border:1px solid #82633d;border-radius:16px;background:#241d17;color:#f2d7a7}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px;margin-top:20px}}.card{{padding:22px;border:1px solid var(--line);border-radius:20px;background:#14263a;box-shadow:0 16px 36px #0004}}.header{{display:flex;gap:12px;align-items:start}}.header>span{{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:#70462a;color:#ffe0a4;font-weight:900}}small{{font-weight:900;color:var(--hot);letter-spacing:.07em}}h2{{font-size:23px;letter-spacing:-.04em;margin:0}}.card p{{min-height:76px;color:var(--sub);font-size:14px}}audio{{width:100%;height:42px}}em{{display:block;color:#88a8c0;font-size:12px;font-style:normal;margin-top:10px}}button{{margin-top:16px;padding:10px 15px;border:1px solid #6a91ab;border-radius:99px;background:#27536d;color:white;font:inherit;font-weight:800;cursor:pointer}}footer{{padding:0 24px 42px;text-align:center;color:#89a3b6;font-size:13px}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}.card p{{min-height:0}}}}</style><body><header><h1>박진감 넘치는<br><b>역동 피아노 3종</b></h1><p>신규 <code>engine: auto</code> 요청으로 20초 원본을 먼저 생성·기술 검수하고, 전개가 시작되는 2초 지점부터 10초씩 발췌했습니다.</p><button id="all">3개 연속 듣기</button><button id="stop">정지</button></header><main><section class="notice">현재 Stable Audio 3 MLX 런타임이 준비되지 않아 자동 엔진이 로컬 피아노 sample-score 공식 폴백을 선택했습니다. 세 원본 모두 기술 QA를 통과했으며 사람 청취 승인은 아직 필요합니다.</section><section class="grid">{cards}</section></main><footer>생성 BGM 후보는 청취 승인 전 최종 유튜브 납품·Content ID 등록 대상이 아닙니다.</footer><script>const a=[...document.querySelectorAll('audio')];function s(){{a.forEach(x=>{{x.pause();x.currentTime=0;x.onended=null}})}}stop.onclick=s;all.onclick=()=>{{s();let i=0;const n=()=>{{if(i<a.length){{let x=a[i++];x.onended=n;x.play().catch(n)}}}};n()}};</script></body></html>'''

def main():
 OUT.mkdir(parents=True,exist_ok=True);entries=[]
 for i,(slug,label,preset,key,tempo,description,prompt,mood) in enumerate(SAMPLES,1):
  pid=f'auto-piano-dynamic-{slug}'
  req={'projectId':pid,'kind':'piano-bgm','durationSec':20,'preset':preset,'mood':mood,'purpose':'featured','engine':'auto','prompt':prompt,'negativePrompt':'vocals, singing, speech, distorted piano, harsh clipping, noise','cfg':2.2,'steps':8,'key':key,'tempoBpm':tempo,'seed':2026072100+i,'output':{'distribution':'local','preview':False}}
  rfile=OUT/'requests'/f'{slug}.json';rfile.parent.mkdir(parents=True,exist_ok=True);rfile.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n')
  print(f'[{i}/3] {preset} · {tempo} BPM',flush=True)
  result=json.loads(run(True,str(PYTHON),str(CLI),'--projects-root',str(PROJECTS),'--output-root',str(SOURCES),'build','--request',str(rfile),'--force'))
  (OUT/'build-results').mkdir(exist_ok=True);(OUT/'build-results'/f'{slug}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  qa=result.get('qa') or {}
  if not qa.get('technicalPassed'):raise RuntimeError(f'{slug}: technical QA failed {qa}')
  src=SOURCES/pid/f'{pid}-44k16.wav';dst=OUT/f'{i:02d}-{slug}.m4a'
  run(False,'ffmpeg','-hide_banner','-loglevel','error','-y','-ss','2','-i',str(src),'-t','10','-af','afade=t=in:st=0:d=0.12,afade=t=out:st=9.45:d=0.55','-ar','44100','-ac','2','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dst))
  q=metrics(dst)
  if q['clippingSamples']:raise RuntimeError(f'{slug}: clip {q}')
  entries.append({'index':i,'slug':slug,'label':label,'preset':preset,'tempo':tempo,'description':description,'file':dst.name,'durationSec':duration(dst),**q,'source':str(src),'technicalQa':qa,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
  print(f"  PASS {dst.name}: {entries[-1]['durationSec']:.2f}s, peak {q['decodedPeakDbfs']:.2f}dBFS",flush=True)
 manifest={'title':'박진감 넘치는 역동 피아노 3종','createdAt':datetime.now(timezone.utc).isoformat(),'requestEngine':'auto','actualEngine':'sample-score official fallback; Stable Audio MLX not configured','sourceDurationSec':20,'clipStartSec':2,'demoDurationSec':10,'entries':entries,'status':'technical PASS; human listening pending'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (OUT/'index.html').write_text(page(entries),encoding='utf-8')
 print('DONE',OUT/'index.html')
if __name__=='__main__':main()
