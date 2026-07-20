#!/usr/bin/env python3
"""Engine-local renderer for the 3-engine × 3-line calm-life TTS demo.

Run this script with each engine's own interpreter. It never substitutes an engine
or disables a model quality component; a failed native engine is a hard failure.
"""
from __future__ import annotations

import json
import os
import sys
import wave
from pathlib import Path
from types import ModuleType
import importlib.machinery

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(np.asarray(samples, dtype=np.float32).reshape(-1), -1.0, 1.0) * 32767.0).astype('<i2')
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm.tobytes())


def melo_mecab_compat() -> None:
    try:
        import MeCab  # noqa: F401
        return
    except ModuleNotFoundError:
        pass
    try:
        import mecab
    except ImportError as exc:
        raise RuntimeError('Melo Korean runtime needs python-mecab-ko') from exc

    class Tagger:
        def __init__(self, *_args, **_kwargs):
            self._mecab = mecab.MeCab()

        def parse(self, _sentence: str) -> str:
            raise RuntimeError('This Melo runtime is Korean-only; Japanese parsing is unavailable')

    module = ModuleType('MeCab')
    module.__spec__ = importlib.machinery.ModuleSpec('MeCab', loader=None)
    module.Tagger = Tagger
    sys.modules['MeCab'] = module


def render_supertonic(items: list[dict], out_dir: Path, speed: float) -> dict:
    import supertonic

    tts = supertonic.TTS(auto_download=True)
    # F5 is the native female style listed for calm/healing narration. No style-vector
    # zeroing or synthetic fallback is used.
    style = tts.get_voice_style('F5')
    entries = []
    for item in items:
        samples, _ = tts.synthesize(
            item['text'], voice_style=style, lang='ko', total_steps=8, speed=speed,
        )
        wav = out_dir / f"supertonic-{item['id']}.wav"
        write_wav(wav, samples, 44_100)
        entries.append({'id': item['id'], 'rawWav': wav.name, 'nativeSampleRate': 44_100})
    return {
        'engine': 'supertonic', 'label': 'Supertonic · F5',
        'model': 'supertonic-3', 'packageVersion': getattr(supertonic, '__version__', 'unknown'),
        'voice': 'F5', 'qualityGate': 'PASS: Supertonic native female F5 style, 8 inference steps; no fallback.',
        'entries': entries,
    }


def render_melo(items: list[dict], out_dir: Path, speed: float) -> dict:
    melo_mecab_compat()
    from melo.api import TTS

    revision = '0207e5adfc90129a51b6b03d89be6d84360ed323'
    snapshot = Path(os.environ.get('HF_HOME', str(Path.home() / '.cache' / 'huggingface'))) / 'hub' / 'models--myshell-ai--MeloTTS-Korean' / 'snapshots' / revision
    config, checkpoint = snapshot / 'config.json', snapshot / 'checkpoint.pth'
    if not (config.is_file() and checkpoint.is_file()):
        raise RuntimeError(f'Melo pinned model files are missing: {snapshot}')
    tts = TTS(language='KR', device='cpu', use_hf=False, config_path=str(config), ckpt_path=str(checkpoint))
    if bool(getattr(tts.hps.data, 'disable_bert', False)):
        raise RuntimeError('QUALITY_GATE_FAILED: Melo contextual Korean BERT is disabled')
    speakers = getattr(tts.hps.data, 'spk2id', {})
    if 'KR' not in speakers:
        raise RuntimeError(f'QUALITY_GATE_FAILED: Korean speaker KR missing: {sorted(speakers)}')
    sample_rate = int(tts.hps.data.sampling_rate)
    entries = []
    for item in items:
        samples = tts.tts_to_file(item['text'], speakers['KR'], output_path=None, speed=speed, quiet=True)
        wav = out_dir / f"melo-ko-{item['id']}.wav"
        write_wav(wav, samples, sample_rate)
        entries.append({'id': item['id'], 'rawWav': wav.name, 'nativeSampleRate': sample_rate})
    return {
        'engine': 'melo-ko', 'label': 'Melo Korean · KR',
        'model': 'myshell-ai/MeloTTS-Korean', 'modelRevision': revision,
        'voice': 'kr-default', 'speaker': 'KR', 'contextualBert': 'kykim/bert-kor-base enabled',
        'qualityGate': 'PASS: pinned official Korean model, KR speaker and contextual BERT enabled; no fallback.',
        'entries': entries,
    }


def render_qwen(items: list[dict], out_dir: Path, speed: float) -> dict:
    sys.path.insert(0, str(ROOT / 'pipeline'))
    from brushvid.tts_engines.qwen import QwenAdapter

    reference_dir = ROOT / 'projects' / 'seoyun-a-day-60-qwen-fullscreen' / 'inputs' / 'voices'
    reference = {'audio': reference_dir / 'seoyun-f1-reference.wav', 'transcript': reference_dir / 'seoyun-f1-reference.txt'}
    if not all(path.is_file() and not path.is_symlink() for path in reference.values()):
        raise RuntimeError('Qwen reference pair is missing or invalid')
    adapter = QwenAdapter(reference=reference, work_root=out_dir / '.qwen-work')
    try:
        results = adapter.synthesize_batch([item['text'] for item in items], voice='seoyun-f1-reference', language='ko', speed=speed)
    finally:
        # synthesize_batch itself closes; this makes a pre-generation failure clean up too.
        adapter.close()
    if len(results) != len(items):
        raise RuntimeError('Qwen output count mismatch')
    entries = []
    for item, result in zip(items, results, strict=True):
        wav = out_dir / f"qwen3-base-{item['id']}.wav"
        write_wav(wav, result.samples, result.sample_rate)
        entries.append({'id': item['id'], 'rawWav': wav.name, 'nativeSampleRate': result.sample_rate})
    return {
        'engine': 'qwen3-base', 'label': 'Qwen3 TTS · Reference clone',
        'model': 'Qwen/Qwen3-TTS-12Hz-1.7B-Base', 'modelRevision': 'fd4b254389122332181a7c3db7f27e918eec64e3',
        'voice': 'seoyun-f1-reference', 'referenceVoice': 'existing project AI reference pair',
        'xVectorOnlyMode': False,
        'qualityGate': 'PASS: local Qwen 1.7B + explicit reference audio/transcript pair + xVectorOnlyMode=false.',
        'entries': entries,
    }


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit('usage: tts-life-demo-engine.py ENGINE JOBS_JSON OUT_DIR SPEED')
    engine, jobs_path, out_path, speed_raw = sys.argv[1:]
    items = json.loads(Path(jobs_path).read_text(encoding='utf-8'))['items']
    out_dir = Path(out_path); out_dir.mkdir(parents=True, exist_ok=True)
    speed = float(speed_raw)
    if engine == 'supertonic':
        result = render_supertonic(items, out_dir, speed)
    elif engine == 'melo-ko':
        result = render_melo(items, out_dir, speed)
    elif engine == 'qwen3-base':
        result = render_qwen(items, out_dir, speed)
    else:
        raise SystemExit(f'unsupported engine: {engine}')
    (out_dir / f'{engine}-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'status': 'PASS', 'entries': len(result['entries'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
