#!/usr/bin/env python3
"""Render 9 calm Korean TTS listening demos: 3 native engines × 3 shared life lines."""
from __future__ import annotations

import array
import hashlib
import html
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'life-calm-tts-9-demo'
RAW = OUT / 'raw-native'
ENGINE_RUNNER = ROOT / 'scripts' / 'tts-life-demo-engine.py'
SPEED = 0.96
# Qwen's raw Korean cadence is measurably shorter than the other two native engines.
# 0.82× is a deliberate, still-natural narration compensation—not a fallback.
ENGINE_PLAYBACK_SPEED = {'supertonic': 0.96, 'melo-ko': 0.96, 'qwen3-base': 0.82}
TARGET_LUFS = -18.0
TARGET_TRUE_PEAK = -4.0
ITEMS = [
    {'id': '01', 'title': '삶의 속도', 'text': '삶은 꼭 서두르지 않아도 됩니다. 오늘의 숨을 고르고, 내 마음의 속도를 다시 듣는 시간이면 충분합니다.'},
    {'id': '02', 'title': '조용한 성장', 'text': '잘되지 않는 날에도 우리는 조금씩 자랍니다. 창가에 머문 빛처럼, 작은 평온은 조용히 곁에 남아 있습니다.'},
    {'id': '03', 'title': '하루의 안부', 'text': '하루가 저물면 애쓴 나에게 가만히 말해 주세요. 여기까지도 충분했고, 내일은 또 천천히 시작하면 된다고요.'},
]
ENGINES = [
    {'id': 'supertonic', 'name': 'Supertonic · F5', 'interpreter': ROOT / 'pipeline' / '.venv' / 'bin' / 'python', 'desc': '기본 F5 여성 음색 · 힐링/감성 내레이션'},
    {'id': 'melo-ko', 'name': 'Melo Korean · KR', 'interpreter': ROOT / '.tts-runtimes' / 'melo' / 'bin' / 'python', 'desc': '공식 한국어 KR 기본 화자 · 문맥 BERT 활성'},
    {'id': 'qwen3-base', 'name': 'Qwen3 TTS · Reference clone', 'interpreter': ROOT / '.tts-runtimes' / 'qwen' / 'bin' / 'python', 'desc': '기존 프로젝트 AI reference 기반 · 자연스러운 문장 연결'},
]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def duration(path: Path) -> float:
    text = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(path)], text=True).strip()
    return float(text)


def decoded_metrics(path: Path) -> dict:
    temp = path.with_suffix('.qa.f32')
    try:
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(path), '-f', 'f32le', '-acodec', 'pcm_f32le', str(temp)])
        values = array.array('f'); values.frombytes(temp.read_bytes())
        peak = max((abs(value) for value in values), default=0.0)
        active = [value for value in values if abs(value) > 0.002]
        rms = math.sqrt(sum(value * value for value in active) / len(active)) if active else 0.0
        return {
            'decodedPeakLinear': round(peak, 7),
            'decodedPeakDbfs': round(20 * math.log10(max(peak, 1e-12)), 2),
            'activeRmsDbfs': round(20 * math.log10(max(rms, 1e-12)), 2),
            'clippingSamples': sum(abs(value) >= 0.999 for value in values),
        }
    finally:
        temp.unlink(missing_ok=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_html(entries: list[dict], engine_meta: dict) -> str:
    cards = []
    for engine in ENGINES:
        eid = engine['id']
        engine_entries = [entry for entry in entries if entry['engineId'] == eid]
        rows = []
        for entry in engine_entries:
            rows.append(f'''<article class="sample">
              <div class="sample-top"><span class="num">{entry['sampleId']}</span><div><h3>{html.escape(entry['title'])}</h3><p>{html.escape(entry['text'])}</p></div></div>
              <audio controls preload="metadata" src="{html.escape(entry['file'])}"></audio>
              <small>{entry['durationSec']:.2f}초 · {entry['decodedPeakDbfs']:.2f} dBFS peak · 무클리핑</small>
            </article>''')
        meta = engine_meta[eid]
        notes = {
            'supertonic': 'native F5 female style · 8 steps · 대체 음성 없음',
            'melo-ko': 'KR speaker · contextual BERT 활성 · 대체 음성 없음',
            'qwen3-base': '명시적 AI reference pair · xVectorOnlyMode=false · 대체 음성 없음',
        }[eid]
        cards.append(f'''<section class="engine" data-engine="{eid}"><div class="engine-heading"><div><span class="engine-tag">{html.escape(engine['name'])}</span><h2>{html.escape(engine['desc'])}</h2></div><span class="pass">QUALITY PASS</span></div><p class="engine-note">{html.escape(notes)}</p><div class="samples">{''.join(rows)}</div></section>''')
    script_rows=''.join(f'<li><b>{item["id"]}. {html.escape(item["title"])}</b> — {html.escape(item["text"])}</li>' for item in ITEMS)
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>삶을 조용히 말하는 TTS 9종</title>
<style>
:root{{--bg:#121b29;--panel:#182537;--panel2:#21334a;--line:#38516c;--text:#eff6fb;--muted:#b8c8d8;--mint:#9ee7ca;--gold:#f4ce83}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(900px 540px at 15% -5%,#385b78 0,transparent 62%),linear-gradient(135deg,#0d1623,#172536 56%,#101a27);color:var(--text);font:16px/1.62 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}header{{padding:64px max(22px,7vw) 38px;border-bottom:1px solid var(--line)}}main{{width:min(1200px,calc(100vw - 36px));margin:0 auto 72px}}h1{{max-width:900px;margin:0;font-size:clamp(31px,5.2vw,64px);letter-spacing:-.06em;line-height:1.08}}h1 em{{font-style:normal;color:var(--mint)}}header p{{max-width:860px;color:var(--muted);font-size:17px}}.toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}}button,a.button{{appearance:none;border:1px solid #58809f;border-radius:999px;padding:10px 15px;background:#1e4058;color:#eafeff;font:inherit;font-weight:800;cursor:pointer;text-decoration:none}}button:hover,a.button:hover{{background:#2b5e7d}}.intro{{margin:28px 0;padding:21px 24px;border:1px solid var(--line);border-radius:18px;background:#142133c9}}.intro p{{color:var(--muted);margin:7px 0}}ol{{margin:14px 0 0;padding-left:22px;color:#dce9f2}}li{{margin:9px 0}}.engine{{margin:24px 0;padding:25px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,#19293c,#152233)}}.engine-heading{{display:flex;align-items:start;justify-content:space-between;gap:20px}}.engine-tag{{color:var(--gold);font-weight:900;font-size:13px;text-transform:uppercase;letter-spacing:.08em}}h2{{margin:4px 0 0;font-size:clamp(22px,3vw,32px);letter-spacing:-.035em}}.pass{{padding:5px 9px;border:1px solid #3c806d;border-radius:999px;color:var(--mint);font-size:12px;font-weight:900;white-space:nowrap}}.engine-note{{color:var(--muted);font-size:14px;margin:12px 0 18px}}.samples{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.sample{{padding:17px;border:1px solid #35516c;border-radius:16px;background:#101c2c}}.sample-top{{display:flex;align-items:start;gap:12px}}.num{{display:grid;place-items:center;flex:0 0 31px;height:31px;border-radius:10px;background:#294e62;color:#dff8ff;font-weight:900}}h3{{margin:0;font-size:18px;letter-spacing:-.02em}}.sample p{{min-height:78px;margin:7px 0 12px;color:#c9d9e6;font-size:14px;line-height:1.65}}audio{{width:100%;height:40px}}small{{display:block;margin-top:8px;color:#91a8bb;font-size:12px}}footer{{color:#93aabc;text-align:center;font-size:13px;padding:0 24px 44px}}@media(max-width:840px){{.samples{{grid-template-columns:1fr}}.sample p{{min-height:0}}header{{padding-top:44px}}}}@media(max-width:500px){{.engine{{padding:18px}}.engine-heading{{flex-direction:column;gap:8px}}}}
</style></head><body><header><h1><em>삶을 조용히 말하는</em><br>TTS 3종 × 3문장</h1><p>같은 세 문장을 세 가지 실제 엔진으로 읽은 9개 음성 데모입니다. 빠르지 않게, 다정하게, 인생을 설명하듯 읽도록 음량을 통일하고 Qwen3의 고유 발화 속도는 별도로 보정했습니다.</p><div class="toolbar"><button id="playAll">9개 순서대로 듣기</button><button data-scene="01">문장 01만 비교</button><button data-scene="02">문장 02만 비교</button><button data-scene="03">문장 03만 비교</button><button id="stopAll">모두 정지</button><a class="button" href="manifest.json">제작·검사 정보</a></div></header><main><section class="intro"><b>비교 조건</b><p>속도: Supertonic·Melo {ENGINE_PLAYBACK_SPEED['supertonic']:.2f}× / Qwen3 {ENGINE_PLAYBACK_SPEED['qwen3-base']:.2f}× · 음량 목표 {TARGET_LUFS:.0f} LUFS · true peak 목표 {TARGET_TRUE_PEAK:.0f} dBTP · BGM 없음 · AI 합성 음성입니다.</p><p>Qwen3는 기존 프로젝트의 AI reference audio/transcript pair를 사용했습니다. 실제 인물 음성을 쓸 때는 반드시 권리와 동의를 별도로 확인해야 합니다.</p><ol>{script_rows}</ol></section>{''.join(cards)}</main><footer>각 엔진의 정상 모델·필수 문맥/참조 조건을 유지해 생성했습니다. 사용 전 직접 들어보고 최종 음색을 선택해 주세요.</footer><script>
const all=[...document.querySelectorAll('audio')];
function stop(){{all.forEach(a=>{{a.pause();a.currentTime=0;a.onended=null}})}}
function play(list){{stop();let i=0;const next=()=>{{if(i>=list.length)return;const a=list[i++];a.onended=next;a.play().catch(()=>next())}};next()}}
document.getElementById('playAll').onclick=()=>play(all);
document.getElementById('stopAll').onclick=stop;
document.querySelectorAll('[data-scene]').forEach(b=>b.onclick=()=>play(all.filter(a=>a.closest('.sample').querySelector('.num').textContent===b.dataset.scene)));
</script></body></html>'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    jobs = OUT / 'script.json'; jobs.write_text(json.dumps({'items': ITEMS}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    engine_meta: dict[str, dict] = {}
    for engine in ENGINES:
        print(f"\n=== {engine['id']} native generation ===", flush=True)
        command = [str(engine['interpreter']), str(ENGINE_RUNNER), engine['id'], str(jobs), str(RAW), str(ENGINE_PLAYBACK_SPEED[engine['id']])]
        run(command)
        meta_path = RAW / f"{engine['id']}-result.json"
        engine_meta[engine['id']] = json.loads(meta_path.read_text(encoding='utf-8'))
        if len(engine_meta[engine['id']].get('entries', [])) != len(ITEMS) or not str(engine_meta[engine['id']].get('qualityGate', '')).startswith('PASS:'):
            raise RuntimeError(f"QUALITY_GATE_FAILED: {engine['id']}")

    entries: list[dict] = []
    for engine in ENGINES:
        eid = engine['id']; metadata = engine_meta[eid]
        by_id = {entry['id']: entry for entry in metadata['entries']}
        for item in ITEMS:
            raw = RAW / by_id[item['id']]['rawWav']
            final_name = f"{eid}-{item['id']}.m4a"
            final = OUT / final_name
            filters = []
            if eid == 'qwen3-base':
                filters.append(f"atempo={ENGINE_PLAYBACK_SPEED[eid]:.3f}")
            filters += ['highpass=f=45', 'lowpass=f=16500', f'loudnorm=I={TARGET_LUFS}:LRA=7:TP={TARGET_TRUE_PEAK}:dual_mono=true', 'afade=t=in:st=0:d=0.025']
            run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw), '-af', ','.join(filters), '-ar', '44100', '-ac', '1', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(final)])
            metric = decoded_metrics(final)
            if metric['clippingSamples'] != 0 or metric['decodedPeakLinear'] >= 0.99:
                raise RuntimeError(f"QUALITY_GATE_FAILED: clipping in {final.name}: {metric}")
            entries.append({
                'engineId': eid, 'engine': metadata['label'], 'sampleId': item['id'], 'title': item['title'], 'text': item['text'],
                'file': final_name, 'durationSec': round(duration(final), 3), 'sha256': sha256(final),
                **metric,
            })
            print(f"PASS {final_name}: {entries[-1]['durationSec']:.2f}s / peak {metric['decodedPeakDbfs']:.2f} dBFS", flush=True)

    manifest = {
        'title': '삶을 조용히 말하는 TTS 3종 × 3문장', 'createdAt': datetime.now(timezone.utc).isoformat(),
        'comparison': {'engines': 3, 'samples': 9, 'sharedScripts': ITEMS, 'enginePlaybackSpeed': ENGINE_PLAYBACK_SPEED, 'loudnessTargetLufs': TARGET_LUFS, 'truePeakTargetDbtp': TARGET_TRUE_PEAK, 'bgm': 'none'},
        'qualityPolicy': 'Native engine only; required contextual/reference conditions enabled; no degraded fallback; decoded clipping must be zero.',
        'engines': engine_meta, 'samples': entries,
        'aiDisclosure': '이 페이지의 아홉 음성은 모두 AI 합성 음성입니다. Qwen3 reference의 권리·동의 범위는 실제 제작에서 별도 확인해야 합니다.',
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'index.html').write_text(render_html(entries, engine_meta), encoding='utf-8')
    print(f"\nDONE: {OUT / 'index.html'}")


if __name__ == '__main__':
    main()
