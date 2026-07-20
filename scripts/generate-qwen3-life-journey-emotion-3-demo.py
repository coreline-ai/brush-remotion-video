#!/usr/bin/env python3
"""Generate three restrained, poignant Qwen3 CustomVoice life-journey demos."""
from __future__ import annotations

import array
import hashlib
import html
import json
import math
import os
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("BRUSHVID_QWEN_PYTHON", str(ROOT / ".tts-runtimes" / "qwen" / "bin" / "python"))
sys.path.insert(0, str(ROOT / "pipeline"))
from brushvid.tts_engines.qwen import QwenCustomVoiceAdapter  # noqa: E402

OUT = ROOT / "output" / "qwen3-life-journey-emotion-3-demo"
RAW = OUT / "raw-native"
TEXT = (
    "돌아보면, 삶은 우리가 알지 못한 사이에도 조용히 흘러가고 있었습니다. "
    "붙잡고 싶었던 순간은 계절이 되었고, 잊었다고 믿었던 마음은 어느 날의 빛 속에서 다시 우리를 찾아옵니다. "
    "그래도 우리는 지나온 모든 날의 온기를 품고, 오늘을 향해 천천히 걸어갑니다."
)
TONES = [
    {
        "id": "restrained-ache", "name": "01 · 억누른 먹먹함", "speed": 0.84,
        "short": "울지 않지만 마음이 잠기는, 담담한 회상",
        "instruction": (
            "따뜻하고 깊은 한국어 여성 내레이션입니다. 한 사람의 긴 삶을 조용히 돌아보며, "
            "울음을 꾹 참고 마음속으로만 삼키는 듯 읽어 주세요. 속도는 느리지만 처지지 않게, "
            "문장 사이에는 짧고 자연스러운 숨을 두고, 끝맺음은 낮고 부드럽게 내려 주세요. "
            "감정을 과장하거나 드라마처럼 연기하지 마세요."
        ),
    },
    {
        "id": "fading-seasons", "name": "02 · 지나간 계절의 여운", "speed": 0.86,
        "short": "기억이 천천히 되살아나는, 맑고 긴 여운",
        "instruction": (
            "맑지만 가슴 한편이 먹먹한 한국어 여성 나레이션입니다. 오래된 사진을 천천히 넘기며 "
            "지나간 계절과 사람을 떠올리듯 읽어 주세요. 중요한 단어 앞에서는 아주 짧게 숨을 고르고, "
            "따뜻한 미소와 아쉬움이 함께 느껴지게 하되 슬픔을 밀어붙이지 마세요. "
            "영화 예고편처럼 웅장하거나 인위적인 억양은 피하세요."
        ),
    },
    {
        "id": "quiet-forward", "name": "03 · 조용히 앞으로", "speed": 0.85,
        "short": "지나온 날을 품고 내일로 가는 잔잔한 희망",
        "instruction": (
            "성숙하고 다정한 한국어 여성 내레이션입니다. 힘들었던 시간을 충분히 이해하는 사람이 "
            "곁에서 낮은 목소리로 건네는 말처럼 읽어 주세요. 마음을 울리되 눈물에 기대지 말고, "
            "마지막 문장에는 아주 작고 따뜻한 희망을 남겨 주세요. 호흡은 느리고 자연스럽게, "
            "모든 표현은 절제되고 진실하게 유지하세요."
        ),
    },
]
TARGET_LUFS, TARGET_TRUE_PEAK = -18.0, -4.0


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples.astype(np.float32).reshape(-1), -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sample_rate); f.writeframes(pcm.tobytes())


def duration(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], text=True).strip())


def metrics(path: Path) -> dict:
    temp = path.with_suffix(".qa.f32")
    try:
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le", str(temp)])
        values = array.array("f"); values.frombytes(temp.read_bytes())
        peak = max((abs(x) for x in values), default=0.0)
        active = [x for x in values if abs(x) > 0.002]
        rms = math.sqrt(sum(x*x for x in active) / len(active)) if active else 0.0
        return {"decodedPeakDbfs": round(20 * math.log10(max(peak, 1e-12)), 2), "activeRmsDbfs": round(20 * math.log10(max(rms, 1e-12)), 2), "clippingSamples": sum(abs(x) >= 0.999 for x in values)}
    finally:
        temp.unlink(missing_ok=True)


def page(entries: list[dict]) -> str:
    cards = []
    for entry in entries:
        cards.append(f'''<article class="card"><div class="num">{entry["number"]}</div><div><span>Qwen3 CustomVoice · Sohee · {entry["speed"]:.2f}×</span><h2>{html.escape(entry["name"])}</h2><p class="tagline">{html.escape(entry["short"])}</p></div><audio controls preload="metadata" src="{html.escape(entry["file"])}"></audio><p class="instruction"><b>연출 지시</b><br>{html.escape(entry["instruction"])}</p><small>{entry["durationSec"]:.2f}초 · {entry["decodedPeakDbfs"]:.2f} dBFS peak · clipping 0 · AI 합성 음성</small></article>''')
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>인생의 여정 · 먹먹한 Qwen3 내레이션 3종</title><style>
:root{{--bg:#10151e;--panel:#172230;--line:#344b62;--text:#eef4f6;--muted:#b3c2cc;--peach:#efb889;--mint:#a2e1c9}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(900px 540px at 10% -10%,#4a5260,transparent 60%),linear-gradient(135deg,#0e141e,#182534);color:var(--text);font:16px/1.7 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}header{{padding:68px max(24px,8vw) 42px;border-bottom:1px solid var(--line)}}main{{width:min(940px,calc(100vw - 36px));margin:0 auto 72px}}h1{{margin:0;max-width:800px;font-size:clamp(32px,5.8vw,66px);line-height:1.12;letter-spacing:-.065em}}em{{color:var(--peach);font-style:normal}}header p{{max-width:780px;color:var(--muted);font-size:17px}}.actions{{display:flex;gap:9px;flex-wrap:wrap;margin-top:24px}}button,a{{border:1px solid #5b7c91;border-radius:999px;padding:10px 15px;background:#203a4b;color:#efffff;text-decoration:none;font:inherit;font-weight:800;cursor:pointer}}button:hover,a:hover{{background:#2d5b70}}.script{{margin:28px 0;padding:22px 25px;border-left:3px solid var(--peach);background:#182330;border-radius:4px 16px 16px 4px;color:#d2dfe4}}.card{{position:relative;margin:22px 0;padding:27px 27px 23px 80px;border:1px solid var(--line);border-radius:21px;background:linear-gradient(135deg,#1a2736,#14202d)}}.num{{position:absolute;left:24px;top:28px;display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:#463b39;color:#ffdab0;font-weight:900}}.card span{{font-size:12px;font-weight:900;letter-spacing:.07em;color:var(--mint)}}h2{{margin:2px 0;font-size:clamp(24px,3.2vw,36px);letter-spacing:-.04em}}.tagline{{margin:0 0 16px;color:var(--muted)}}audio{{width:100%}}.instruction{{margin:17px 0 9px;padding:14px 15px;background:#101c29;color:#c4d2da;font-size:14px;border-radius:11px}}small{{color:#91a8b7;font-size:12px}}footer{{text-align:center;padding:0 22px 44px;color:#8fa5b4;font-size:13px}}@media(max-width:560px){{.card{{padding:73px 18px 20px}}.num{{left:18px;top:20px}}header{{padding-top:45px}}}}
</style></head><body><header><h1>지나온 날을 품고<br><em>오늘로 걸어가는</em> 목소리</h1><p>인생이 흘러가는 여정에 맞춰, 감정을 밀어붙이지 않고도 마음에 오래 남는 세 가지 Sohee 내레이션을 만들었습니다. 같은 대본·BGM 없음·실제 Qwen3 CustomVoice 모델만 사용했습니다.</p><div class="actions"><button id="play">3개 순서대로 듣기</button><button id="stop">정지</button><a href="manifest.json">manifest</a></div></header><main><section class="script"><b>공통 대본</b><br>{html.escape(TEXT)}</section>{''.join(cards)}</main><footer>기술 통과는 무클리핑·고정 모델·speaker/instruction 기록을 뜻합니다. 최종 감성 판단은 청취 후 진행합니다.</footer><script>const a=[...document.querySelectorAll('audio')];function stop(){{a.forEach(x=>{{x.pause();x.currentTime=0;x.onended=null}})}}document.querySelector('#stop').onclick=stop;document.querySelector('#play').onclick=()=>{{stop();let i=0;const next=()=>{{if(i<a.length){{a[i].onended=next;a[i++].play().catch(next)}}}};next()}};</script></body></html>'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True); RAW.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, tone in enumerate(TONES, 1):
        print(f"\n=== {tone['id']} native CustomVoice generation ===", flush=True)
        adapter = QwenCustomVoiceAdapter(speaker="Sohee", instruction=tone["instruction"], work_root=RAW / f".{tone['id']}-work")
        try:
            result = adapter.synthesize_batch([TEXT], voice="Sohee", language="ko", speed=tone["speed"])[0]
        finally:
            adapter.close()
        raw = RAW / f"{tone['id']}.wav"; write_wav(raw, result.samples, result.sample_rate)
        final = OUT / f"{index:02d}-{tone['id']}.m4a"
        mastered_duration = duration(raw) / tone["speed"]
        fade_out_start = max(0.0, mastered_duration - 0.12)
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), "-af", ",".join([
            f"atempo={tone['speed']:.3f}", "highpass=f=45", "lowpass=f=16500", f"loudnorm=I={TARGET_LUFS}:LRA=7:TP={TARGET_TRUE_PEAK}:dual_mono=true", "afade=t=in:st=0:d=0.12", f"afade=t=out:st={fade_out_start:.3f}:d=0.12",
        ]), "-ar", "44100", "-ac", "1", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)])
        qa = metrics(final)
        if qa["clippingSamples"] != 0:
            raise RuntimeError(f"QUALITY_GATE_FAILED: clipping in {final}")
        entries.append({
            "number": f"0{index}", **tone, "file": final.name, "durationSec": round(duration(final), 3),
            "sha256": hashlib.sha256(final.read_bytes()).hexdigest(), **qa,
            "model": result.metadata["model"], "modelRevision": result.metadata["modelRevision"], "speaker": "Sohee",
            "appliedSpeed": tone["speed"], "speedAppliedBy": "ffmpeg-atempo", "aiDisclosure": result.metadata["aiDisclosure"],
        })
        print(f"PASS {final.name}: {entries[-1]['durationSec']:.2f}s / peak {qa['decodedPeakDbfs']:.2f} dBFS", flush=True)
    manifest = {"kind": "qwen3-life-journey-emotion-3-demo", "createdAt": datetime.now(timezone.utc).isoformat(), "status": "PENDING_USER_LISTENING", "sharedText": TEXT, "model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "modelRevision": "0c0e3051f131929182e2c023b9537f8b1c68adfe", "speaker": "Sohee", "audioNormalization": {"lufs": TARGET_LUFS, "truePeakDbtp": TARGET_TRUE_PEAK}, "aiDisclosure": "이 페이지의 세 음성은 모두 Qwen3-TTS CustomVoice(Sohee) AI 합성 음성입니다.", "demos": entries}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "index.html").write_text(page(entries), encoding="utf-8")
    print(f"DONE: {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
