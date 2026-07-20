#!/usr/bin/env python3
"""Build 10-second listening excerpts for every auto piano BGM preset.

The BGM contract requires source requests to be at least 15 seconds. This tool
first creates a full 15-second, technically-checked candidate through
``bin/piano-bgm.py build --engine auto`` and then makes a clearly labeled
10-second listening excerpt. It never represents pending candidates as final
licensed delivery.
"""
from __future__ import annotations

import array
import hashlib
import html
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'piano-auto-genre-demo'
PROJECTS = ROOT / 'projects' / 'piano-bgm'
SOURCES = ROOT / 'output' / 'original-audio' / 'piano-bgm'
PYTHON = ROOT / 'pipeline' / '.venv' / 'bin' / 'python'
CLI = ROOT / 'bin' / 'piano-bgm.py'
SOURCE_SECONDS = 15
SOURCE_SECONDS_BY_PRESET = {'mystery-horror-piano': 30}
DEMO_SECONDS = 10
GENRES = [
    ('new-age', '뉴에이지', '흐르는 아르페지오와 맑은 응답 선율', 'clear gentle morning', 'background'),
    ('ambient-piano', '앰비언트 피아노', '긴 여백과 낮은 음 밀도', 'quiet open air', 'background'),
    ('sleep-piano', '수면 피아노', '3/4 자장가와 부드러운 해결', 'warm bedtime', 'background'),
    ('meditation-piano', '명상 피아노', '열린 5도와 느린 호흡', 'still grounded calm', 'background'),
    ('lofi-piano', '로파이 피아노', '7th·9th 화성과 느슨한 컴핑', 'soft late afternoon', 'background'),
    ('minimal-ambient', '미니멀 앰비언트', '6/8 반복 세포의 점진 변화', 'patient spacious motion', 'background'),
    ('cinematic-piano', '시네마틱 피아노', '넓은 옥타브와 점층 구조', 'hopeful cinematic rise', 'featured'),
    ('film-ost-piano', '영화 OST 피아노', '노래형 선율과 명확한 종지', 'tender film ending', 'featured'),
    ('game-bgm-piano', '게임 BGM 피아노', '6/8 오스티나토와 짧은 훅', 'adventurous gentle quest', 'featured'),
    ('fantasy-piano', '판타지 피아노', 'Lydian 색채와 고음 장식', 'luminous magical garden', 'featured'),
    ('mystery-horror-piano', '미스터리·호러 피아노', '선언된 반음·트라이톤과 침묵', 'quiet moonlit mystery', 'featured'),
]


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=capture)
    return result.stdout if capture else ''


def duration(path: Path) -> float:
    value = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(path)], capture=True).strip()
    return float(value)


def metrics(path: Path) -> dict:
    temp = Path('/private/tmp') / f'.{path.stem}.f32'
    try:
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(path), '-f', 'f32le', '-acodec', 'pcm_f32le', str(temp)])
        values = array.array('f'); values.frombytes(temp.read_bytes())
        peak = max((abs(x) for x in values), default=0.0)
        return {
            'decodedPeakDbfs': round(20 * math.log10(max(peak, 1e-12)), 2),
            'clippingSamples': sum(abs(x) >= .999 for x in values),
        }
    finally:
        temp.unlink(missing_ok=True)


def tag(preset: str) -> str:
    return f'auto-piano-genre-{preset}'


def render_html(entries: list[dict]) -> str:
    cards = []
    for index, entry in enumerate(entries, 1):
        cards.append(f'''<article class="card">
          <div class="top"><span class="number">{index:02}</span><div><span class="preset">{html.escape(entry['preset'])}</span><h2>{html.escape(entry['label'])}</h2></div></div>
          <p>{html.escape(entry['contract'])}</p>
          <audio controls preload="metadata" src="{html.escape(entry['file'])}"></audio>
          <small>10초 청취 발췌 · 원본 {entry['sourceDurationSec']:.0f}초 기술 QA 통과 · 피크 {entry['decodedPeakDbfs']:.2f} dBFS</small>
        </article>''')
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>자동 피아노 BGM · 11장르 10초 데모</title>
<style>
:root{{--paper:#f4f0e9;--ink:#1c2636;--muted:#607084;--line:#d9d0c1;--blue:#274c67;--gold:#b77b26}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 70% -20%,#f9e6be 0,transparent 40%),linear-gradient(145deg,#fbfaf7,#e9eef2);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}header{{padding:58px max(22px,7vw) 36px;background:linear-gradient(128deg,#173246,#2d5b72);color:#f8fbfd}}h1{{margin:0;font-size:clamp(31px,5vw,58px);letter-spacing:-.055em;line-height:1.12}}header p{{max-width:900px;color:#d3e4ec;font-size:17px}}.toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin-top:23px}}button,a.button{{border:1px solid #87afc1;border-radius:999px;padding:10px 15px;background:#22485e;color:white;font:inherit;font-weight:800;cursor:pointer;text-decoration:none}}button:hover,a.button:hover{{background:#356a83}}main{{width:min(1180px,calc(100vw - 36px));margin:28px auto 70px}}.notice{{padding:19px 22px;border:1px solid #dbbf8d;border-radius:16px;background:#fff8e8;color:#644719}}.notice b{{color:#85580f}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:20px}}.card{{padding:20px;border:1px solid var(--line);border-radius:19px;background:#fff;box-shadow:0 10px 28px #24344413}}.top{{display:flex;gap:12px;align-items:start}}.number{{display:grid;place-items:center;flex:0 0 38px;height:38px;border-radius:12px;background:#e8eff3;color:#24495f;font-weight:900}}.preset{{font-size:12px;color:#527288;font-weight:900;letter-spacing:.06em}}h2{{margin:1px 0 0;font-size:22px;letter-spacing:-.035em}}.card p{{min-height:53px;color:var(--muted);font-size:14px}}audio{{display:block;width:100%;height:40px}}small{{display:block;margin-top:9px;color:#7a8996;font-size:12px}}footer{{padding:0 20px 42px;color:#70808c;text-align:center;font-size:13px}}@media(max-width:850px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:580px){{.grid{{grid-template-columns:1fr}}header{{padding-top:42px}}.card p{{min-height:0}}}}
</style></head><body><header><h1>자동 피아노 BGM<br>11장르 · 10초 연주 데모</h1><p>신규 <code>engine: auto</code> 요청으로 각 장르의 최소 15초 원본(미스터리·호러는 QA 다양성을 위해 30초)을 먼저 생성·기술 검수한 뒤, 첫 10초를 청취용으로 발췌했습니다.</p><div class="toolbar"><button id="all">11개 순서대로 듣기</button><button id="stop">모두 정지</button><a class="button" href="genre-manifest.json">제작·QA 정보</a></div></header><main><section class="notice"><b>현재 자동 엔진 결과:</b> 이 환경에는 Stable Audio 3 MLX 런타임이 설정되어 있지 않아, <code>engine: auto</code>가 검증된 로컬 Noct-Salamander 피아노 sample-score 엔진으로 폴백했습니다. 품질 저하용 가짜 대체가 아니라 자동 정책의 공식 결정적 폴백이며, 각 원본은 기술 QA를 통과했지만 사람 청취 승인은 아직 필요합니다.</section><section class="grid">{''.join(cards)}</section></main><footer>AI/생성 BGM 후보는 사람 청취 승인 전 최종 유튜브 납품 또는 Content ID 등록 대상이 아닙니다.</footer><script>const a=[...document.querySelectorAll('audio')];function stop(){{a.forEach(x=>{{x.pause();x.currentTime=0;x.onended=null}})}}document.getElementById('stop').onclick=stop;document.getElementById('all').onclick=()=>{{stop();let i=0;const n=()=>{{if(i>=a.length)return;const x=a[i++];x.onended=n;x.play().catch(n)}};n()}};</script></body></html>'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for offset, (preset, label, contract, mood, purpose) in enumerate(GENRES, 1):
        project_id = tag(preset)
        source_seconds = SOURCE_SECONDS_BY_PRESET.get(preset, SOURCE_SECONDS)
        request = {
            'projectId': project_id, 'kind': 'piano-bgm', 'durationSec': source_seconds,
            'preset': preset, 'mood': mood, 'purpose': purpose, 'engine': 'auto',
            'seed': 2026072000 + offset, 'output': {'distribution': 'local', 'preview': False},
        }
        request_file = OUT / 'requests' / f'{preset}.json'; request_file.parent.mkdir(parents=True, exist_ok=True)
        request_file.write_text(json.dumps(request, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'[{offset}/{len(GENRES)}] {preset}: auto build', flush=True)
        stdout = run([str(PYTHON), str(CLI), '--projects-root', str(PROJECTS), '--output-root', str(SOURCES), 'build', '--request', str(request_file), '--force'], capture=True)
        result = json.loads(stdout)
        result_path = OUT / 'build-results' / f'{preset}.json'; result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        qa = result.get('qa') or {}
        if qa.get('technicalPassed') is not True:
            raise RuntimeError(f'{preset}: technical QA not passed: {qa}')
        source = SOURCES / project_id / f'{project_id}-44k16.wav'
        if not source.is_file():
            raise RuntimeError(f'{preset}: delivery missing: {source}')
        final = OUT / f'{offset:02d}-{preset}.m4a'
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source), '-t', str(DEMO_SECONDS),
             '-af', 'afade=t=in:st=0:d=0.15,afade=t=out:st=9.45:d=0.55', '-ar', '44100', '-ac', '2',
             '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(final)])
        m = metrics(final)
        if m['clippingSamples'] != 0:
            raise RuntimeError(f'{preset}: clipping detected: {m}')
        entries.append({
            'index': offset, 'preset': preset, 'label': label, 'contract': contract, 'mood': mood, 'purpose': purpose,
            'requestEngine': 'auto', 'actualEngine': 'sample-score', 'sourceDurationSec': duration(source),
            'file': final.name, 'durationSec': duration(final), **m,
            'sha256': hashlib.sha256(final.read_bytes()).hexdigest(), 'technicalQa': qa,
            'sourceDelivery': str(source), 'buildResult': str(result_path),
        })
        print(f"  PASS {final.name}: {entries[-1]['durationSec']:.2f}s, {m['decodedPeakDbfs']:.2f}dBFS", flush=True)
    manifest = {
        'title': '자동 피아노 BGM · 11장르 10초 연주 데모', 'generatedAt': datetime.now(timezone.utc).isoformat(),
        'requestEngine': 'auto', 'stableAudioRuntime': 'unavailable (STABLE_AUDIO_3_MLX_ROOT not configured)',
        'actualEngine': 'sample-score (official auto fallback)', 'sourceDurationSec': {'default': SOURCE_SECONDS, 'overrides': SOURCE_SECONDS_BY_PRESET},
        'demoDurationSec': DEMO_SECONDS, 'technicalQa': 'PASS for all source candidates; human listening remains pending',
        'entries': entries,
    }
    (OUT / 'genre-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'index.html').write_text(render_html(entries), encoding='utf-8')
    print(f'DONE: {OUT / "index.html"}')


if __name__ == '__main__':
    main()
