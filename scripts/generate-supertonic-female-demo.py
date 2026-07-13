#!/usr/bin/env python3
"""Generate ten 10-second Korean female Supertonic voice demos.

Run with the project TTS environment:
  pipeline/.venv/bin/python scripts/generate-supertonic-female-demo.py

Supertonic ships five female presets (F1-F5). Samples 6-10 are deterministic
female-only style-vector blends so the demo exposes ten distinct choices without
mixing in any male voice vectors.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import subprocess
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import supertonic

from brushvid.voice_presets import build_voice_style, catalog_sha256, load_catalog


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "supertonic-female-voices-10x10s"
SR = 44_100
TOTAL_SEC = 10.0
LEAD_SEC = 0.18
TAIL_GUARD_SEC = 0.08
BASE_SPEED = 1.10
TEXT = (
    "안녕하세요. 수퍼토닉 여성 목소리 데모입니다. "
    "같은 문장을 들으며 음색과 속도, 전달력을 편안하게 비교해 보세요."
)
CATALOG = load_catalog()
VOICE_SPECS = [
    {"id": v["id"], "label": v["displayName"], "mix": v["components"],
     "recommendedSpeed": v["recommendedSpeed"]}
    for v in CATALOG["voices"]
]
VOICE_CHARACTERISTICS = {
    v["id"]: {
        "badge": v["badge"], "pitch": v["pitch"], "pace": v["pace"],
        "pitch_hz": v["pitchHz"], "summary": v["summary"],
        "use": " · ".join(v["useCases"]),
    }
    for v in CATALOG["voices"]
}


def write_wav(path: Path, audio: np.ndarray) -> None:
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(pcm.tobytes())


def dbfs(value: float) -> float:
    return 20.0 * math.log10(max(value, 1e-12))


def normalize_speech(audio: np.ndarray) -> tuple[np.ndarray, float, float]:
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    audio = audio - float(np.mean(audio))
    fade = min(len(audio) // 2, round(0.025 * SR))
    if fade:
        ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
        audio[:fade] *= ramp
        audio[-fade:] *= ramp[::-1]

    active = np.abs(audio) > 0.002
    active_rms = float(np.sqrt(np.mean(np.square(audio[active])))) if np.any(active) else 0.0
    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    target_rms = 10 ** (-20.0 / 20.0)
    peak_ceiling = 10 ** (-1.5 / 20.0)
    rms_gain = target_rms / max(active_rms, 1e-9)
    peak_gain = peak_ceiling / max(peak, 1e-9)
    audio *= min(rms_gain, peak_gain)

    active = np.abs(audio) > 0.002
    final_rms = float(np.sqrt(np.mean(np.square(audio[active])))) if np.any(active) else 0.0
    final_peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    return audio, dbfs(final_peak), dbfs(final_rms)


def mix_style(styles: dict[str, supertonic.Style], weights: dict[str, float]) -> supertonic.Style:
    total = sum(weights.values())
    ttl = sum(styles[name].ttl * (weight / total) for name, weight in weights.items())
    dp = sum(styles[name].dp * (weight / total) for name, weight in weights.items())
    return supertonic.Style(np.asarray(ttl, dtype=np.float32), np.asarray(dp, dtype=np.float32))


def encode_mp3(wav_path: Path, mp3_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "192k", str(mp3_path),
        ],
        check=True,
    )


def render_html(entries: list[dict]) -> str:
    cards = []
    table_rows = []
    for entry in entries:
        mix = " + ".join(f"{name} {weight:.0%}" for name, weight in entry["mix"].items())
        feature = VOICE_CHARACTERISTICS[entry["id"]]
        cards.append(f"""
        <article class="voice-card">
          <div class="number">{entry['id'][-2:]}</div>
          <div class="voice-main">
            <div class="title-row"><h2>{html.escape(entry['label'])}</h2><span class="badge">{html.escape(feature['badge'])}</span></div>
            <p class="metrics">{html.escape(mix)} · 음높이 {feature['pitch']}({feature['pitch_hz']}Hz) · 속도 {feature['pace']} · 발화 {entry['speechDurationSec']:.2f}초</p>
            <p class="trait">{html.escape(feature['summary'])}</p>
            <p class="use"><b>추천:</b> {html.escape(feature['use'])}</p>
            <audio controls preload="metadata" src="{html.escape(entry['mp3'])}"></audio>
            <div class="links"><a href="{html.escape(entry['mp3'])}">MP3 열기</a><a href="{html.escape(entry['wav'])}">WAV 열기</a></div>
          </div>
        </article>""")
        table_rows.append(f"""
          <tr>
            <th>{html.escape(entry['label'])}</th>
            <td>{html.escape(feature['summary'])}</td>
            <td>{entry['speechDurationSec']:.2f}초</td>
            <td>{html.escape(feature['use'])}</td>
          </tr>""")

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Supertonic 여성 보이스 10종 · 10초 데모</title>
<style>
:root{{--paper:#f5f0e7;--ink:#182235;--muted:#6a7280;--line:#d9cfbe;--gold:#c8922d;--navy:#263b68}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(145deg,#faf7f1,#eee7dc);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}}
header{{padding:54px max(24px,6vw) 36px;background:#172238;color:white;border-bottom:5px solid var(--gold)}}
h1{{margin:0 0 12px;font-size:clamp(32px,5vw,58px);letter-spacing:-.04em}} header p{{max-width:920px;margin:8px 0;color:#dbe2ef;font-size:18px;line-height:1.7}}
.toolbar{{display:flex;gap:12px;flex-wrap:wrap;margin-top:24px}} button,.toplink{{border:0;border-radius:999px;padding:12px 18px;background:var(--gold);color:#142036;font-weight:800;font-size:15px;cursor:pointer;text-decoration:none}}
main{{width:min(1160px,92vw);margin:34px auto 70px}} .script{{background:#fffaf1;border:1px solid var(--line);border-radius:18px;padding:20px 24px;margin-bottom:22px;box-shadow:0 10px 30px #4d40251a}}
.script b{{color:var(--navy)}} .section-title{{margin:38px 0 16px;font-size:30px;letter-spacing:-.03em}} .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.voice-card{{position:relative;display:flex;gap:18px;align-items:flex-start;background:#fff;border:1px solid var(--line);border-radius:20px;padding:22px;box-shadow:0 10px 32px #3a302119}}
.number{{display:grid;place-items:center;flex:0 0 48px;height:48px;border-radius:15px;background:#e8dfcf;color:var(--navy);font-size:20px;font-weight:900}}
.voice-main{{min-width:0;flex:1}} .title-row{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}} h2{{margin:2px 0 6px;font-size:22px}} .badge{{display:inline-flex;padding:5px 9px;border-radius:999px;background:#f5e6bd;color:#62450b;font-size:12px;font-weight:900}}
.voice-main p{{margin:0 0 12px}} .metrics{{color:var(--muted);font-size:13px}} .trait{{color:var(--ink);font-size:15px;line-height:1.65}} .use{{padding:9px 11px;border-radius:10px;background:#f3f5f9;color:#40506b;font-size:13px}} audio{{display:block;width:100%;height:42px}}
.guide{{overflow:auto;background:white;border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 30px #4d40251a}} table{{width:100%;border-collapse:collapse;min-width:860px}} th,td{{padding:15px 16px;border-bottom:1px solid #ece5da;text-align:left;vertical-align:top;line-height:1.5}} thead th{{background:#202e4a;color:white;font-size:13px}} tbody th{{white-space:nowrap;color:var(--navy)}} tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
.picks{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}} .pick{{background:#202e4a;color:white;border-radius:15px;padding:16px}} .pick b{{display:block;color:#f0c76c;margin-bottom:6px}} .pick span{{font-size:14px;color:#e1e7f1}}
.links{{display:flex;gap:12px;margin-top:12px}} .links a{{color:var(--navy);font-size:13px;font-weight:800}} footer{{text-align:center;color:var(--muted);padding:0 20px 40px}}
@media(max-width:760px){{.grid,.picks{{grid-template-columns:1fr}} header{{padding-top:38px}} .voice-card{{padding:18px}}}}
</style>
</head>
<body>
<header>
  <h1>Supertonic 여성 보이스 10종</h1>
  <p>한국어 동일 대본 · 샘플당 정확히 10초 · F1-F5 기본 보이스와 여성 보이스끼리만 혼합한 추가 5종입니다.</p>
  <div class="toolbar"><button id="playAll">10개 순서대로 듣기</button><button id="stopAll">모두 정지</button><a class="toplink" href="manifest.json">검사 결과 JSON</a></div>
</header>
<main>
  <section class="script"><b>공통 대본</b><br>{html.escape(TEXT)}</section>
  <h2 class="section-title">빠른 선택</h2>
  <section class="picks">
    <div class="pick"><b>기본 범용</b><span>female-01 · F1</span></div>
    <div class="pick"><b>밝은 쇼츠</b><span>female-07 · F2+F4</span></div>
    <div class="pick"><b>교육·전문 해설</b><span>female-09 · F4+F1</span></div>
    <div class="pick"><b>동화·감성</b><span>female-08 · F3+F5</span></div>
    <div class="pick"><b>힐링·명상</b><span>female-05 · F5</span></div>
    <div class="pick"><b>장편 다큐</b><span>female-06 · F1+F3</span></div>
  </section>
  <h2 class="section-title">10종 특징 비교</h2>
  <section class="guide"><table><thead><tr><th>보이스</th><th>음색 특징</th><th>발화 길이</th><th>추천 용도</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table></section>
  <h2 class="section-title">직접 듣고 비교하기</h2>
  <section class="grid">{''.join(cards)}</section>
</main>
<footer>voice pack {CATALOG['voicePackVersion']} · Supertonic 1.3.1 · supertonic-3 · ko · steps 8 · speed 1.10 · AI 합성 음성</footer>
<script>
const players=[...document.querySelectorAll('audio')];
document.getElementById('playAll').onclick=()=>{{let i=0;players.forEach(a=>{{a.pause();a.currentTime=0}});const next=()=>{{if(i>=players.length)return;const a=players[i++];a.onended=next;a.play()}};next()}};
document.getElementById('stopAll').onclick=()=>players.forEach(a=>{{a.pause();a.currentTime=0}});
</script>
</body>
</html>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tts = supertonic.TTS(auto_download=True)
    entries: list[dict] = []
    max_speech_sec = TOTAL_SEC - LEAD_SEC - TAIL_GUARD_SEC

    for spec in VOICE_SPECS:
        style, voice_metadata = build_voice_style(tts, spec["id"], catalog=CATALOG)
        speed = spec["recommendedSpeed"]
        speech = np.empty(0, dtype=np.float32)
        for _ in range(3):
            wav, _duration = tts.synthesize(
                TEXT, voice_style=style, lang="ko", total_steps=8, speed=speed,
            )
            speech = np.asarray(wav, dtype=np.float32).reshape(-1)
            speech_sec = len(speech) / SR
            if speech_sec <= max_speech_sec:
                break
            speed *= (speech_sec / max_speech_sec) * 1.01
        if len(speech) / SR > max_speech_sec:
            raise RuntimeError(f"{spec['label']}: 10초 안에 합성 음성이 들어오지 않음")

        speech, peak_dbfs, active_rms_dbfs = normalize_speech(speech)
        canvas = np.zeros(round(TOTAL_SEC * SR), dtype=np.float32)
        start = round(LEAD_SEC * SR)
        canvas[start:start + len(speech)] = speech

        stem = spec["id"]
        wav_path = OUT / f"{stem}.wav"
        mp3_path = OUT / f"{stem}.mp3"
        write_wav(wav_path, canvas)
        encode_mp3(wav_path, mp3_path)

        pcm_peak = float(np.max(np.abs(canvas)))
        clipped = int(np.count_nonzero(np.abs(canvas) >= 0.99999))
        entry = {
            **spec,
            "speed": round(speed, 6),
            "speechDurationSec": round(len(speech) / SR, 6),
            "totalDurationSec": TOTAL_SEC,
            "leadSec": LEAD_SEC,
            "peakDbfs": round(dbfs(pcm_peak), 4),
            "activeRmsDbfs": round(active_rms_dbfs, 4),
            "clippedSamples": clipped,
            "wav": wav_path.name,
            "mp3": mp3_path.name,
            "sha256": hashlib.sha256(wav_path.read_bytes()).hexdigest(),
            "voiceMetadata": voice_metadata,
        }
        entries.append(entry)
        print(f"[{spec['id']}/10] {spec['label']}: speech={entry['speechDurationSec']:.2f}s peak={entry['peakDbfs']:.2f}dBFS")

    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "engine": "Supertonic",
        "packageVersion": getattr(supertonic, "__version__", "unknown"),
        "model": "supertonic-3",
        "language": "ko",
        "sampleRate": SR,
        "sampleDurationSec": TOTAL_SEC,
        "text": TEXT,
        "voiceCount": len(entries),
        "voicePackVersion": CATALOG["voicePackVersion"],
        "catalogSha256": catalog_sha256(CATALOG),
        "femaleOnly": True,
        "aiDisclosure": CATALOG["aiDisclosure"],
        "notes": "female-01..05 are built-in F1-F5; female-06..10 are deterministic blends of female-only style vectors.",
        "voices": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "index.html").write_text(render_html(entries), encoding="utf-8")
    print(f"DONE: {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
