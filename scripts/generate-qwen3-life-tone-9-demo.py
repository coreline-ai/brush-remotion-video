#!/usr/bin/env python3
"""Create a 3-tone × 3-life-line Qwen3 listening page and detailed manifest."""
from __future__ import annotations

import array
import hashlib
import html
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "qwen3-life-tone-9-demo"
RAW = OUT / "raw-native"
RUNNER = ROOT / "scripts" / "render-qwen3-life-tone.py"
QWEN_PY = ROOT / ".tts-runtimes" / "qwen" / "bin" / "python"
TARGET_LUFS = -18.0
TARGET_TRUE_PEAK = -4.0
ITEMS = [
    {"id": "01", "title": "삶의 속도", "text": "삶은 꼭 서두르지 않아도 됩니다. 오늘의 숨을 고르고, 내 마음의 속도를 다시 듣는 시간이면 충분합니다."},
    {"id": "02", "title": "조용한 성장", "text": "잘되지 않는 날에도 우리는 조금씩 자랍니다. 창가에 머문 빛처럼, 작은 평온은 조용히 곁에 남아 있습니다."},
    {"id": "03", "title": "하루의 안부", "text": "하루가 저물면 애쓴 나에게 가만히 말해 주세요. 여기까지도 충분했고, 내일은 또 천천히 시작하면 된다고요."},
]
TONES = [
    {
        "id": "sohee-neutral", "name": "Sohee 담백형", "engine": "qwen3-customvoice", "speaker": "Sohee", "speed": 0.90,
        "instruction": "따뜻하고 맑은 한국어 여성 목소리로, 숨을 고르듯 차분하고 담백하게 읽어 주세요. 감정을 과장하지 말고 문장 끝은 부드럽고 자연스럽게 내려 주세요.",
        "description": "과장 없이 또렷하고 안정적으로 설명하는 톤",
    },
    {
        "id": "sohee-emotional", "name": "Sohee 감성 내레이션형", "engine": "qwen3-customvoice", "speaker": "Sohee", "speed": 0.88,
        "instruction": "따뜻하고 부드러운 한국어 여성 내레이션으로, 삶의 장면을 조용히 회상하듯 깊고 다정하게 읽어 주세요. 느린 호흡과 잔잔한 여운을 살리되 과장된 연기는 피하세요.",
        "description": "삶을 회상하듯 부드러운 여운을 남기는 톤",
    },
    {
        "id": "base-reference", "name": "현재 Base 복제형", "engine": "qwen3-base", "speed": 0.98,
        "description": "기존 60씬 프로젝트의 reference clone 설정과 같은 기준선",
    },
]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path),
    ], text=True).strip())


def decoded_metrics(path: Path) -> dict:
    temp = path.with_suffix(".qa.f32")
    try:
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le", str(temp)])
        values = array.array("f"); values.frombytes(temp.read_bytes())
        peak = max((abs(value) for value in values), default=0.0)
        active = [value for value in values if abs(value) > 0.002]
        rms = math.sqrt(sum(value * value for value in active) / len(active)) if active else 0.0
        return {
            "decodedPeakLinear": round(peak, 7),
            "decodedPeakDbfs": round(20 * math.log10(max(peak, 1e-12)), 2),
            "activeRmsDbfs": round(20 * math.log10(max(rms, 1e-12)), 2),
            "clippingSamples": sum(abs(value) >= 0.999 for value in values),
        }
    finally:
        temp.unlink(missing_ok=True)


def render_html(entries: list[dict], tone_meta: dict[str, dict]) -> str:
    sections = []
    for tone in TONES:
        tone_entries = [entry for entry in entries if entry["toneId"] == tone["id"]]
        rows = "".join(f'''<article class="sample"><div class="sample-top"><span>{e["sampleId"]}</span><div><h3>{html.escape(e["title"])}</h3><p>{html.escape(e["text"])}</p></div></div><audio controls preload="metadata" src="{html.escape(e["file"])}"></audio><small>{e["durationSec"]:.2f}초 · peak {e["decodedPeakDbfs"]:.2f} dBFS · clipping 0</small></article>''' for e in tone_entries)
        meta = tone_meta[tone["id"]]["metadata"]
        detail = f"CustomVoice · speaker Sohee · speed {tone['speed']:.2f}×" if tone["engine"] == "qwen3-customvoice" else "Base clone · 기존 reference pair · speed 0.98×"
        instruction = tone.get("instruction", "명시적 AI reference audio/transcript pair · xVectorOnlyMode=false")
        sections.append(f'''<section class="tone"><div class="tone-head"><div><span class="tag">{html.escape(tone["engine"])}</span><h2>{html.escape(tone["name"])}</h2><p>{html.escape(tone["description"])}</p></div><span class="pass">TECH PASS</span></div><div class="meta"><b>{html.escape(detail)}</b><br>{html.escape(instruction)}</div><div class="samples">{rows}</div></section>''')
    scripts = "".join(f"<li><b>{x['id']}. {html.escape(x['title'])}</b> — {html.escape(x['text'])}</li>" for x in ITEMS)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Qwen3 Sohee 톤 비교 · 9개</title><style>
:root{{--bg:#111723;--panel:#182434;--line:#35516b;--text:#edf4fa;--muted:#b6c6d4;--mint:#a5ebcf;--gold:#f4cc7d}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(1000px 600px at 5% -10%,#304e70,transparent 60%),linear-gradient(135deg,#0d1420,#172536);color:var(--text);font:16px/1.62 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}header{{padding:62px max(22px,7vw) 38px;border-bottom:1px solid var(--line)}}main{{width:min(1200px,calc(100vw - 36px));margin:0 auto 65px}}h1{{margin:0;font-size:clamp(30px,5vw,62px);line-height:1.08;letter-spacing:-.06em}}h1 em{{font-style:normal;color:var(--mint)}}header p{{max-width:850px;color:var(--muted);font-size:17px}}.buttons{{display:flex;gap:9px;flex-wrap:wrap;margin-top:23px}}button,a{{border:1px solid #5d849f;border-radius:999px;padding:10px 14px;background:#1b3a51;color:#e9fbff;text-decoration:none;font:inherit;font-weight:800;cursor:pointer}}button:hover,a:hover{{background:#275a79}}.intro{{margin:28px 0;padding:22px 25px;background:#142033dd;border:1px solid var(--line);border-radius:19px}}.intro p{{color:var(--muted);margin:7px 0}}ol{{margin:13px 0 0;padding-left:23px}}li{{margin:8px 0}}.tone{{margin:24px 0;padding:26px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,#1a2a3d,#142131)}}.tone-head{{display:flex;gap:16px;justify-content:space-between;align-items:start}}.tag{{font-size:12px;font-weight:900;letter-spacing:.08em;color:var(--gold)}}h2{{margin:3px 0;font-size:clamp(23px,3vw,33px);letter-spacing:-.04em}}.tone-head p{{margin:0;color:var(--muted)}}.pass{{border:1px solid #45836e;border-radius:999px;padding:5px 9px;font-size:12px;font-weight:900;color:var(--mint);white-space:nowrap}}.meta{{margin:16px 0 18px;padding:13px 15px;border-left:3px solid #77cdb1;background:#102032;color:#c7d9e8;font-size:14px}}.samples{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.sample{{padding:17px;border:1px solid #37536d;border-radius:16px;background:#101c2b}}.sample-top{{display:flex;gap:12px;align-items:start}}.sample-top>span{{display:grid;place-items:center;min-width:30px;height:30px;border-radius:9px;background:#2a4f64;font-weight:900}}h3{{margin:0;font-size:18px}}.sample p{{min-height:78px;margin:7px 0 12px;color:#c8d8e5;font-size:14px}}audio{{width:100%}}small{{display:block;color:#98afc0;font-size:12px;margin-top:7px}}footer{{text-align:center;color:#95aabb;padding:0 22px 42px;font-size:13px}}@media(max-width:840px){{.samples{{grid-template-columns:1fr}}.sample p{{min-height:0}}}}@media(max-width:500px){{.tone{{padding:18px}}.tone-head{{flex-direction:column}}}}
</style></head><body><header><h1><em>Qwen3 Sohee</em> · 3톤<br>같은 인생 묘사 9개 비교</h1><p>CustomVoice를 기존 Base 복제 엔진과 별도 추가했습니다. 각 톤은 같은 세 문장을 실제 고정 모델로 합성했고, 선택 전에는 어떤 톤도 60씬 기본값으로 쓰지 않습니다.</p><div class="buttons"><button id="all">9개 순서대로 듣기</button><button data-scene="01">문장 01 비교</button><button data-scene="02">문장 02 비교</button><button data-scene="03">문장 03 비교</button><button id="stop">정지</button><a href="manifest.json">전체 manifest</a></div></header><main><section class="intro"><b>청취 조건</b><p>동일 대본 · BGM 없음 · 44.1kHz mono AAC · loudness {TARGET_LUFS:.0f} LUFS · true peak {TARGET_TRUE_PEAK:.0f} dBTP · AI 합성 음성 고지를 포함합니다.</p><p><b>60씬 적용:</b> 아래 세 톤을 들은 뒤 선택된 하나만 `apply-qwen3-life-tone.py`로 기본 TTS 설정에 기록됩니다. 현재 상태는 <b>선택 대기</b>입니다.</p><ol>{scripts}</ol></section>{''.join(sections)}</main><footer>TECH PASS는 모델·speaker/instruction/reference·무클리핑 기술 검사 통과를 뜻합니다. 최종 음색 승인은 직접 청취 후 진행합니다.</footer><script>const a=[...document.querySelectorAll('audio')];function stop(){{a.forEach(x=>{{x.pause();x.currentTime=0;x.onended=null}})}}function play(xs){{stop();let i=0;const n=()=>{{if(i>=xs.length)return;let x=xs[i++];x.onended=n;x.play().catch(n)}};n()}}document.querySelector('#all').onclick=()=>play(a);document.querySelector('#stop').onclick=stop;document.querySelectorAll('[data-scene]').forEach(b=>b.onclick=()=>play(a.filter(x=>x.closest('.sample').querySelector('.sample-top>span').textContent===b.dataset.scene)));</script></body></html>'''


def main() -> None:
    if not QWEN_PY.is_file():
        raise SystemExit(f"Qwen runtime 없음: {QWEN_PY}")
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    jobs_path = OUT / "script.json"
    jobs_path.write_text(json.dumps({"items": ITEMS, "tones": TONES}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tone_meta: dict[str, dict] = {}
    for tone in TONES:
        print(f"\n=== {tone['id']} native generation ===", flush=True)
        run([str(QWEN_PY), str(RUNNER), tone["id"], str(jobs_path), str(RAW), str(tone["speed"])])
        meta = json.loads((RAW / f"{tone['id']}-result.json").read_text(encoding="utf-8"))
        if len(meta.get("entries", [])) != len(ITEMS) or not meta.get("qualityGate", "").startswith("PASS:"):
            raise RuntimeError(f"QUALITY_GATE_FAILED: {tone['id']}")
        tone_meta[tone["id"]] = meta

    entries = []
    for tone in TONES:
        meta = tone_meta[tone["id"]]
        by_id = {item["id"]: item for item in meta["entries"]}
        for item in ITEMS:
            raw = RAW / by_id[item["id"]]["rawWav"]
            final = OUT / f"{tone['id']}-{item['id']}.m4a"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), "-af", ",".join([
                f"atempo={tone['speed']:.3f}", "highpass=f=45", "lowpass=f=16500",
                f"loudnorm=I={TARGET_LUFS}:LRA=7:TP={TARGET_TRUE_PEAK}:dual_mono=true", "afade=t=in:st=0:d=0.025",
            ]), "-ar", "44100", "-ac", "1", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)])
            metrics = decoded_metrics(final)
            if metrics["clippingSamples"] or metrics["decodedPeakLinear"] >= 0.99:
                raise RuntimeError(f"QUALITY_GATE_FAILED: clipping in {final.name}: {metrics}")
            entries.append({
                "toneId": tone["id"], "tone": tone["name"], "engine": tone["engine"], "sampleId": item["id"],
                "title": item["title"], "text": item["text"], "file": final.name, "durationSec": round(duration(final), 3),
                "sha256": sha256(final), **metrics,
            })
            print(f"PASS {final.name}: {entries[-1]['durationSec']:.2f}s / {metrics['decodedPeakDbfs']:.2f} dBFS", flush=True)
    manifest = {
        "kind": "qwen3-life-tone-9-demo", "createdAt": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING_USER_LISTENING", "target60SceneProjects": [
            "projects/seoyun-a-day-60-qwen-fullscreen", "projects/seoyun-a-day-60-qwen-pen-brush-fullscreen",
        ],
        "sharedScripts": ITEMS, "tones": [{**tone, "model": tone_meta[tone["id"]]["metadata"].get("model"), "modelRevision": tone_meta[tone["id"]]["metadata"].get("modelRevision"), "speaker": tone_meta[tone["id"]]["metadata"].get("speaker"), "appliedSpeed": tone_meta[tone["id"]]["metadata"].get("speed"), "speedAppliedBy": "ffmpeg-atempo", "aiDisclosure": tone_meta[tone["id"]]["metadata"].get("aiDisclosure", "이 콘텐츠의 내레이션은 Qwen3 Base AI 합성 음성으로 제작되었습니다.")} for tone in TONES],
        "qualityPolicy": "Official pinned Qwen model only. No fallback. Technical PASS does not replace human listening approval.",
        "audioNormalization": {"lufs": TARGET_LUFS, "truePeakDbtp": TARGET_TRUE_PEAK, "clippingSamplesRequired": 0},
        "samples": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "index.html").write_text(render_html(entries, tone_meta), encoding="utf-8")
    print(f"DONE: {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
