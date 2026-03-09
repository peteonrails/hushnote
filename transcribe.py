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

# libcublas is bundled with Ollama on some systems and not on the system path
_CUDA_LIBS = os.environ.get("CUDA_LIBS", "")
if _CUDA_LIBS and _CUDA_LIBS not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = _CUDA_LIBS + ":" + os.environ.get("LD_LIBRARY_PATH", "")

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Error: faster-whisper not installed", file=sys.stderr)
    print("Install with: pip install faster-whisper", file=sys.stderr)
    sys.exit(1)


def _unload_ollama():
    """Unload Ollama models to free VRAM. Only called when UNLOAD_OLLAMA=1."""
    import urllib.request
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    try:
        req = urllib.request.Request(f"{url}/api/ps")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        for m in data.get("models", []):
            payload = json.dumps({"model": m["name"], "keep_alive": 0}).encode()
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{url}/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                ),
                timeout=10,
            )
            print(f"Unloaded Ollama model: {m['name']}", file=sys.stderr)
    except Exception:
        pass


def transcribe_audio(
    audio_file: str,
    model_size: str = "base",
    device: str = "auto",
    language: str = None,
    output_format: str = "txt"
) -> dict:
    """
    Transcribe an audio file using faster-whisper

    Args:
        audio_file: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
        device: Device to use (cpu, cuda, auto)
        language: Language code (None for auto-detect)
        output_format: Output format (txt, json, srt, vtt)

    Returns:
        dict with transcription results
    """
    if os.environ.get("UNLOAD_OLLAMA") == "1":
        _unload_ollama()

    # Determine device
    if device == "auto":
        device = "cuda"

    compute_type = "float16" if device == "cuda" else "int8"

    print(f"Loading Whisper model: {model_size} on {device}", file=sys.stderr)
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "CUDA" in str(e):
            print("GPU unavailable, falling back to CPU", file=sys.stderr)
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        else:
            raise

    print(f"Transcribing: {audio_file}", file=sys.stderr)
    kwargs = {"beam_size": 5}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(str(audio_file), **kwargs)
    print(f"Detected language: {info.language}", file=sys.stderr)

    # Reformat segments to match our expected format
    all_segments = []
    for segment in segments:
        all_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })

    return {
        "language": info.language,
        "segments": all_segments,
        "text": " ".join(s["text"] for s in all_segments)
    }


def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def save_transcription(result: dict, output_file: str, format: str):
    """Save transcription in specified format"""
    output_path = Path(output_file)

    if format == "txt":
        output_path.write_text(result["text"])

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
    parser.add_argument("-m", "--model", default="base",
                       choices=["tiny", "base", "small", "medium", "large-v3"],
                       help="Whisper model size (default: base)")
    parser.add_argument("-d", "--device", default="auto",
                       choices=["cpu", "cuda", "auto"],
                       help="Device to use (default: auto)")
    parser.add_argument("-l", "--language", default=None,
                       help="Language code (default: auto-detect)")
    parser.add_argument("-f", "--format", default="txt",
                       choices=["txt", "json", "srt", "vtt"],
                       help="Output format (default: txt)")
    parser.add_argument("-o", "--output",
                       help="Output file (default: audio_file.txt)")

    args = parser.parse_args()

    # Check if audio file exists
    if not Path(args.audio_file).exists():
        print(f"Error: Audio file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        audio_path = Path(args.audio_file)
        output_file = audio_path.with_suffix(f".{args.format}")

    # Transcribe
    try:
        result = transcribe_audio(
            args.audio_file,
            model_size=args.model,
            device=args.device,
            language=args.language,
            output_format=args.format
        )

        # Save results
        save_transcription(result, output_file, args.format)

        # Print summary
        print(f"\nTranscription complete!", file=sys.stderr)
        print(f"Segments: {len(result['segments'])}", file=sys.stderr)

    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
