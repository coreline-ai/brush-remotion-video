"""Qwen3-TTS CustomVoice protocol v1 worker.

Base reference-clone worker와 별도 process로 동작한다. CustomVoice는 official
speaker + instruction만 수용하며 reference audio를 절대 받지 않는다.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
import traceback
import wave
from pathlib import Path
from typing import Any, Callable

import numpy as np

from ..tts_contract import ENGINE_MODEL_IDS, MODEL_REVISIONS, QWEN3_CUSTOMVOICE_SPEAKERS, resolve_local_snapshot
from .qwen3_worker import (
    ERROR_CODES,
    GENERATION_TIMEOUT_SEC,
    PROTOCOL_VERSION,
    SHUTDOWN_GRACE_SEC,
    STARTUP_TIMEOUT_SEC,
    WorkerProtocolError,
    _emit,
    _load_model,
    _relative_output_dir,
)

ENGINE_ID = "qwen3-customvoice"
LANGUAGE = "Korean"


def _validate_request(request: Any, root: Path) -> tuple[str, list[dict[str, str]], Path, str, str]:
    if not isinstance(request, dict):
        raise WorkerProtocolError("INVALID_REQUEST", "request는 JSON object여야 함")
    if request.get("protocolVersion") != PROTOCOL_VERSION:
        raise WorkerProtocolError("PROTOCOL_ERROR", "protocolVersion 불일치")
    request_id = request.get("requestId")
    if not isinstance(request_id, str) or not request_id.strip():
        raise WorkerProtocolError("INVALID_REQUEST", "requestId가 없음")
    if request.get("engine") != ENGINE_ID:
        raise WorkerProtocolError("INVALID_REQUEST", "engine이 qwen3-customvoice가 아님")
    if request.get("modelRevision") != MODEL_REVISIONS[ENGINE_ID]:
        raise WorkerProtocolError("MODEL_MISSING", "Qwen CustomVoice model revision 불일치")
    if request.get("language") != LANGUAGE:
        raise WorkerProtocolError("INVALID_REQUEST", "language는 Korean이어야 함")
    speaker = request.get("speaker")
    if speaker not in QWEN3_CUSTOMVOICE_SPEAKERS:
        raise WorkerProtocolError("INVALID_REQUEST", f"지원하지 않는 CustomVoice speaker: {speaker!r}")
    instruction = request.get("instruction")
    if not isinstance(instruction, str) or not instruction.strip():
        raise WorkerProtocolError("INVALID_REQUEST", "CustomVoice instruction은 비어 있지 않은 문자열이어야 함")
    if len(instruction) > 600:
        raise WorkerProtocolError("INVALID_REQUEST", "CustomVoice instruction은 600자를 넘을 수 없음")
    if "reference" in request or "xVectorOnlyMode" in request:
        raise WorkerProtocolError("INVALID_REQUEST", "CustomVoice는 reference/xVectorOnlyMode를 사용하지 않음")
    sentences = request.get("sentences")
    if not isinstance(sentences, list) or not sentences:
        raise WorkerProtocolError("INVALID_REQUEST", "sentences가 비어 있음")
    ids: list[str] = []
    normalized: list[dict[str, str]] = []
    for sentence in sentences:
        if not isinstance(sentence, dict) or not isinstance(sentence.get("id"), str):
            raise WorkerProtocolError("INVALID_REQUEST", "sentence id가 없음")
        if sentence["id"] in ids:
            raise WorkerProtocolError("PROTOCOL_ERROR", "sentence id 중복")
        if not isinstance(sentence.get("text"), str) or not sentence["text"].strip():
            raise WorkerProtocolError("INVALID_REQUEST", "sentence text가 비어 있음")
        ids.append(sentence["id"])
        normalized.append({"id": sentence["id"], "text": sentence["text"]})
    output_dir = _relative_output_dir(request.get("outputDir"), root)
    return request_id, normalized, output_dir, speaker, instruction.strip()


def _write_outputs(*, sentences: list[dict[str, str]], wavs: Any, sample_rate: Any, output_dir: Path) -> list[dict[str, Any]]:
    if not isinstance(wavs, (list, tuple)) or len(wavs) != len(sentences):
        raise WorkerProtocolError("PROTOCOL_ERROR", "Qwen CustomVoice output sentence 수 불일치")
    try:
        sample_rate = int(sample_rate)
    except (TypeError, ValueError) as exc:
        raise WorkerProtocolError("PROTOCOL_ERROR", "Qwen CustomVoice sample rate가 유효하지 않음") from exc
    if sample_rate <= 0:
        raise WorkerProtocolError("PROTOCOL_ERROR", "Qwen CustomVoice sample rate가 양수가 아님")
    outputs: list[dict[str, Any]] = []
    for index, (sentence, wav) in enumerate(zip(sentences, wavs, strict=True)):
        if hasattr(wav, "detach"):
            wav = wav.detach().cpu().numpy()
        array = np.asarray(wav, dtype=np.float32).reshape(-1)
        if array.size == 0 or not np.isfinite(array).all() or float(np.max(np.abs(array))) > 1.0 + 1e-6:
            raise WorkerProtocolError("MODEL_ERROR", f"sentence {sentence['id']} waveform이 유효하지 않음")
        filename = f"sentence-{index:04d}.wav"
        destination = output_dir / filename
        temporary = output_dir / f".{filename}.tmp"
        with wave.open(str(temporary), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes((np.clip(array, -1.0, 1.0) * 32767).astype("<i2").tobytes())
        temporary.replace(destination)
        outputs.append({
            "id": sentence["id"], "filename": filename,
            "sampleRate": sample_rate, "durationSec": len(array) / sample_rate,
        })
    return outputs


def handle_request(model: Any, request: dict[str, Any], work_root: str | Path) -> dict[str, Any]:
    root = Path(work_root).resolve()
    request_id, sentences, output_dir, speaker, instruction = _validate_request(request, root)
    try:
        # model/tokenizer progress stdout은 protocol JSON과 분리한다.
        with contextlib.redirect_stdout(sys.stderr):
            wavs, sample_rate = model.generate_custom_voice(
                text=[sentence["text"] for sentence in sentences],
                speaker=[speaker.lower().replace(" ", "_")] * len(sentences),
                language=[LANGUAGE] * len(sentences),
                instruct=[instruction] * len(sentences),
                non_streaming_mode=True,
                max_new_tokens=2048,
            )
    except MemoryError as exc:
        raise WorkerProtocolError("OOM", "Qwen CustomVoice model memory 부족") from exc
    except Exception as exc:
        raise WorkerProtocolError("MODEL_ERROR", f"{type(exc).__name__}: {exc}") from exc
    return {
        "protocolVersion": PROTOCOL_VERSION, "requestId": request_id, "ok": True,
        "outputs": _write_outputs(sentences=sentences, wavs=wavs, sample_rate=sample_rate, output_dir=output_dir),
    }


def run_worker(
    *,
    model_dir: str | Path,
    work_root: str | Path,
    device: str = "cpu",
    model_loader: Callable[[Path, str], Any] = _load_model,
) -> int:
    try:
        snapshot = resolve_local_snapshot(
            ENGINE_MODEL_IDS[ENGINE_ID], MODEL_REVISIONS[ENGINE_ID], explicit_dir=model_dir,
        )
        with contextlib.redirect_stdout(sys.stderr):
            model = model_loader(snapshot, device)
    except WorkerProtocolError as exc:
        _emit({"protocolVersion": PROTOCOL_VERSION, "ready": False,
               "error": {"code": exc.code, "message": str(exc), "retryable": exc.retryable}})
        return 1
    except FileNotFoundError as exc:
        _emit({"protocolVersion": PROTOCOL_VERSION, "ready": False,
               "error": {"code": "MODEL_MISSING", "message": str(exc), "retryable": False}})
        return 1
    except MemoryError:
        _emit({"protocolVersion": PROTOCOL_VERSION, "ready": False,
               "error": {"code": "OOM", "message": "Qwen CustomVoice model memory 부족", "retryable": False}})
        return 1
    except Exception as exc:
        _emit({"protocolVersion": PROTOCOL_VERSION, "ready": False,
               "error": {"code": "MODEL_ERROR", "message": f"{type(exc).__name__}: {exc}", "retryable": False}})
        return 1

    _emit({"protocolVersion": PROTOCOL_VERSION, "ready": True, "modelRevision": MODEL_REVISIONS[ENGINE_ID]})
    for line in sys.stdin:
        request: Any = None
        try:
            request = json.loads(line)
            if isinstance(request, dict) and request.get("command") == "cancel":
                response = {
                    "protocolVersion": PROTOCOL_VERSION, "requestId": request.get("requestId"), "ok": False,
                    "error": {"code": "CANCELLED", "message": "worker 취소 요청", "retryable": False},
                }
                _emit(response)
                break
            response = handle_request(model, request, work_root)
        except json.JSONDecodeError as exc:
            response = {"protocolVersion": PROTOCOL_VERSION, "ok": False,
                        "error": {"code": "PROTOCOL_ERROR", "message": str(exc), "retryable": False}}
        except WorkerProtocolError as exc:
            response = {"protocolVersion": PROTOCOL_VERSION,
                        "requestId": request.get("requestId") if isinstance(request, dict) else None,
                        "ok": False,
                        "error": {"code": exc.code, "message": str(exc), "retryable": exc.retryable}}
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            response = {"protocolVersion": PROTOCOL_VERSION, "ok": False,
                        "error": {"code": "MODEL_ERROR", "message": f"{type(exc).__name__}: {exc}", "retryable": False}}
        _emit(response)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--work-root", required=True)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    return run_worker(model_dir=args.model_dir, work_root=args.work_root, device=args.device)


if __name__ == "__main__":
    raise SystemExit(main())
