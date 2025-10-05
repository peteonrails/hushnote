#!/usr/bin/env python3

"""
Speaker diarization script using pyannote.audio
Identifies who spoke when in an audio file
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from pyannote.audio import Pipeline
except ImportError:
    print("Error: pyannote.audio not installed", file=sys.stderr)
    print("Install with: pip install pyannote.audio", file=sys.stderr)
    sys.exit(1)


def diarize_audio(
    audio_file: str,
    num_speakers: int = None,
    min_speakers: int = None,
    max_speakers: int = None,
    hf_token: str = None
) -> dict:
    """
    Perform speaker diarization on an audio file

    Args:
        audio_file: Path to audio file
        num_speakers: Exact number of speakers (optional)
        min_speakers: Minimum number of speakers (optional)
        max_speakers: Maximum number of speakers (optional)
        hf_token: HuggingFace API token for model access

    Returns:
        dict with diarization results
    """
    print(f"Loading diarization model...", file=sys.stderr)

    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=hf_token
        )
    except Exception as e:
        print(f"\nError loading model: {e}", file=sys.stderr)
        print("\nYou may need to:", file=sys.stderr)
        print("1. Create a HuggingFace account at https://huggingface.co/join", file=sys.stderr)
        print("2. Accept pyannote conditions at https://huggingface.co/pyannote/speaker-diarization-3.1", file=sys.stderr)
        print("3. Create an access token at https://huggingface.co/settings/tokens", file=sys.stderr)
        print("4. Set HF_TOKEN environment variable or use --hf-token flag", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing speakers in: {audio_file}", file=sys.stderr)

    # Build diarization parameters
    params = {}
    if num_speakers is not None:
        params["num_speakers"] = num_speakers
    if min_speakers is not None:
        params["min_speakers"] = min_speakers
    if max_speakers is not None:
        params["max_speakers"] = max_speakers

    # Run diarization
    diarization_output = pipeline(audio_file, **params)

    # Process results
    segments = []
    speaker_stats = {}

    # DiarizeOutput has speaker_diarization attribute (Annotation object)
    diarization = diarization_output.speaker_diarization

    # Iterate over diarization results
    for turn, track, speaker in diarization.itertracks(yield_label=True):
        seg = {
            "speaker_id": speaker,
            "start": turn.start,
            "end": turn.end,
            "duration": turn.end - turn.start
        }
        segments.append(seg)

        # Update speaker statistics
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                "total_time": 0.0,
                "segment_count": 0
            }
        speaker_stats[speaker]["total_time"] += seg["duration"]
        speaker_stats[speaker]["segment_count"] += 1

    # Get audio duration
    duration = max(seg["end"] for seg in segments) if segments else 0

    result = {
        "version": "1.0",
        "audio_file": str(Path(audio_file).name),
        "audio_path": str(Path(audio_file).absolute()),
        "duration": duration,
        "diarization_model": "pyannote/speaker-diarization-3.1",
        "num_speakers": len(speaker_stats),
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "segments": segments,
        "speaker_stats": speaker_stats,
        "labels": {},
        "source": "local_diarization"
    }

    print(f"\nDiarization complete!", file=sys.stderr)
    print(f"Detected {len(speaker_stats)} speaker(s)", file=sys.stderr)
    print(f"Total segments: {len(segments)}", file=sys.stderr)

    for speaker, stats in sorted(speaker_stats.items()):
        print(f"  {speaker}: {stats['total_time']:.1f}s ({stats['segment_count']} segments)", file=sys.stderr)

    return result


def save_diarization(result: dict, output_file: str):
    """Save diarization results to JSON file"""
    output_path = Path(output_file)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\nDiarization saved to: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Perform speaker diarization using pyannote.audio"
    )
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("-s", "--speakers", type=int,
                       help="Expected number of speakers")
    parser.add_argument("--min-speakers", type=int,
                       help="Minimum number of speakers")
    parser.add_argument("--max-speakers", type=int,
                       help="Maximum number of speakers")
    parser.add_argument("-o", "--output",
                       help="Output file (default: audio_file_speakers.json)")
    parser.add_argument("--hf-token",
                       help="HuggingFace API token (or set HF_TOKEN env var)")

    args = parser.parse_args()

    # Check if audio file exists
    if not Path(args.audio_file).exists():
        print(f"Error: Audio file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    # Get HuggingFace token
    import os
    hf_token = args.hf_token or os.getenv("HF_TOKEN")

    if not hf_token:
        print("Warning: No HuggingFace token provided", file=sys.stderr)
        print("Set HF_TOKEN environment variable or use --hf-token flag", file=sys.stderr)
        print("Required for first-time model download", file=sys.stderr)
        print("", file=sys.stderr)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        audio_path = Path(args.audio_file)
        output_file = audio_path.parent / f"{audio_path.stem}_speakers.json"

    # Run diarization
    try:
        result = diarize_audio(
            args.audio_file,
            num_speakers=args.speakers,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
            hf_token=hf_token
        )

        # Save results
        save_diarization(result, output_file)

        print(f"\nNext step:", file=sys.stderr)
        print(f"  1. Transcribe the audio: ./hushnote transcribe {args.audio_file}", file=sys.stderr)
        print(f"  2. Then label speakers with their names", file=sys.stderr)

    except Exception as e:
        print(f"Error during diarization: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
