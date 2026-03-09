#!/usr/bin/env python3

"""
Transcription script using faster-whisper
Transcribes audio files to text with timestamps
"""

import argparse
import json
import os
import sys
from pathlib import Path

# libcublas lives inside Ollama's dir on this system; set before importing ctranslate2
_CUDA_LIBS = "/usr/local/lib/ollama/cuda_v12"
if _CUDA_LIBS not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = _CUDA_LIBS + ":" + os.environ.get("LD_LIBRARY_PATH", "")

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Error: faster-whisper not installed", file=sys.stderr)
    print("Install with: pip install faster-whisper", file=sys.stderr)
    sys.exit(1)


def unload_ollama(ollama_url: str = "http://localhost:11434"):
    """Unload Ollama models to free VRAM before loading Whisper."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{ollama_url}/api/ps")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        for m in data.get("models", []):
            payload = json.dumps({"model": m["name"], "keep_alive": 0}).encode()
            req = urllib.request.Request(
                f"{ollama_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
            print(f"Unloaded Ollama model: {m['name']}", file=sys.stderr)
    except Exception:
        pass


def transcribe_audio(
    audio_file: str,
    model_size: str = "base",
    device: str = "auto",
    language: str = None,
    output_format: str = "txt",
    ollama_url: str = "http://localhost:11434",
) -> dict:
    """
    Transcribe an audio file using faster-whisper.

    Args:
        audio_file: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
        device: Device to use (cpu, cuda, auto)
        language: Language code (None for auto-detect)
        output_format: Output format (txt, json, srt, vtt)
        ollama_url: Ollama API base URL

    Returns:
        dict with transcription results
    """
    if device == "auto":
        unload_ollama(ollama_url)
        try:
            model = WhisperModel(model_size, device="cuda", compute_type="float16")
            print(f"Loading Whisper model: {model_size} on cuda", file=sys.stderr)
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print("GPU OOM, falling back to CPU...", file=sys.stderr)
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
            else:
                raise
    elif device == "cuda":
        unload_ollama(ollama_url)
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        print(f"Loading Whisper model: {model_size} on cuda", file=sys.stderr)
    else:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"Loading Whisper model: {model_size} on cpu", file=sys.stderr)

    print(f"Transcribing: {audio_file}", file=sys.stderr)

    kwargs = {"beam_size": 5}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(str(audio_file), **kwargs)
    print(f"Detected language: {info.language} ({info.language_probability:.0%})", file=sys.stderr)

    all_segments = []
    full_text_parts = []
    print("Transcribing", end="", flush=True, file=sys.stderr)
    for seg in segments:
        all_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        full_text_parts.append(seg.text.strip())
        print(".", end="", flush=True, file=sys.stderr)
    print(" done.", file=sys.stderr)

    return {
        "language": info.language,
        "segments": all_segments,
        "text": " ".join(full_text_parts),
    }


def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def save_transcription(result: dict, output_file: str, format: str):
    """Save transcription in the specified format."""
    output_path = Path(output_file)

    if format == "txt":
        lines = []
        for seg in result["segments"]:
            mins = int(seg["start"] // 60)
            secs = seg["start"] % 60
            lines.append(f"[{mins:02d}:{secs:05.2f}] {seg['text']}")
        output_path.write_text("\n".join(lines))

    elif format == "json":
        output_path.write_text(json.dumps(result, indent=2))

    elif format == "srt":
        lines = []
        for i, seg in enumerate(result["segments"], 1):
            lines.append(str(i))
            lines.append(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}")
            lines.append(seg["text"])
            lines.append("")
        output_path.write_text("\n".join(lines))

    elif format == "vtt":
        lines = ["WEBVTT", ""]
        for seg in result["segments"]:
            lines.append(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}")
            lines.append(seg["text"])
            lines.append("")
        output_path.write_text("\n".join(lines))

    print(f"Transcription saved to: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using faster-whisper")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument(
        "-m", "--model", default="base",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size (default: base)",
    )
    parser.add_argument(
        "-d", "--device", default="auto",
        choices=["cpu", "cuda", "auto"],
        help="Device to use (default: auto)",
    )
    parser.add_argument("-l", "--language", default=None,
                        help="Language code (default: auto-detect)")
    parser.add_argument(
        "-f", "--format", default="txt",
        choices=["txt", "json", "srt", "vtt"],
        help="Output format (default: txt)",
    )
    parser.add_argument("-o", "--output", help="Output file (default: audio_file.txt)")

    args = parser.parse_args()

    if not Path(args.audio_file).exists():
        print(f"Error: Audio file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    output_file = args.output or str(Path(args.audio_file).with_suffix(f".{args.format}"))

    try:
        result = transcribe_audio(
            args.audio_file,
            model_size=args.model,
            device=args.device,
            language=args.language,
            output_format=args.format,
        )
        save_transcription(result, output_file, args.format)
        print(f"\nTranscription complete! Segments: {len(result['segments'])}", file=sys.stderr)

    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
