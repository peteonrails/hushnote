#!/usr/bin/env python3

"""
Merge diarization and transcription results
Combines speaker segments with transcribed text by matching timestamps
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def load_json(file_path: str) -> dict:
    """Load JSON file"""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


def find_speaker_at_time(timestamp: float, speaker_segments: list) -> str:
    """
    Find which speaker was talking at a given timestamp

    Args:
        timestamp: Time in seconds
        speaker_segments: List of speaker segments with start/end times

    Returns:
        Speaker ID or "UNKNOWN"
    """
    for segment in speaker_segments:
        if segment["start"] <= timestamp <= segment["end"]:
            return segment["speaker_id"]

    # If no exact match, find closest segment
    min_distance = float('inf')
    closest_speaker = "UNKNOWN"

    for segment in speaker_segments:
        # Check distance to segment
        if timestamp < segment["start"]:
            distance = segment["start"] - timestamp
        elif timestamp > segment["end"]:
            distance = timestamp - segment["end"]
        else:
            distance = 0

        if distance < min_distance:
            min_distance = distance
            closest_speaker = segment["speaker_id"]

    return closest_speaker


def merge_diarization_transcription(
    diarization: dict,
    transcription: dict
) -> dict:
    """
    Merge diarization speaker info with transcription text

    Args:
        diarization: Speaker segments from diarize.py
        transcription: Transcription segments from transcribe.py

    Returns:
        Merged data with speaker + text for each segment
    """
    print("Merging diarization with transcription...", file=sys.stderr)

    speaker_segments = diarization["segments"]
    transcription_segments = transcription["segments"]

    merged_segments = []

    for trans_seg in transcription_segments:
        # Find speaker at the start of this transcription segment
        timestamp = trans_seg["start"]
        speaker_id = find_speaker_at_time(timestamp, speaker_segments)

        merged_seg = {
            "speaker_id": speaker_id,
            "start": trans_seg["start"],
            "end": trans_seg["end"],
            "text": trans_seg["text"]
        }
        merged_segments.append(merged_seg)

    # Calculate speaker statistics with text
    speaker_stats = {}
    for seg in merged_segments:
        speaker = seg["speaker_id"]
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                "total_time": 0.0,
                "segment_count": 0,
                "word_count": 0
            }

        speaker_stats[speaker]["total_time"] += (seg["end"] - seg["start"])
        speaker_stats[speaker]["segment_count"] += 1
        speaker_stats[speaker]["word_count"] += len(seg["text"].split())

    result = {
        "version": "1.0",
        "audio_file": diarization.get("audio_file"),
        "audio_path": diarization.get("audio_path"),
        "duration": transcription.get("duration", diarization.get("duration")),
        "language": transcription.get("language"),
        "diarization_model": diarization.get("diarization_model"),
        "transcription_model": "faster-whisper",
        "num_speakers": diarization.get("num_speakers"),
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "segments": merged_segments,
        "speaker_stats": speaker_stats,
        "labels": {},
        "source": "merged"
    }

    print(f"Merged {len(merged_segments)} segments", file=sys.stderr)
    print(f"Speakers detected: {len(speaker_stats)}", file=sys.stderr)

    return result


def save_merged(result: dict, output_file: str):
    """Save merged results to JSON file"""
    output_path = Path(output_file)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"\nMerged data saved to: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Merge diarization and transcription results"
    )
    parser.add_argument("diarization_file",
                       help="Path to diarization JSON file (_speakers.json)")
    parser.add_argument("transcription_file",
                       help="Path to transcription JSON file (.json)")
    parser.add_argument("-o", "--output",
                       help="Output file (default: audio_file_diarized.json)")

    args = parser.parse_args()

    # Load input files
    diarization = load_json(args.diarization_file)
    transcription = load_json(args.transcription_file)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Use transcription file as base name
        trans_path = Path(args.transcription_file)
        output_file = trans_path.parent / f"{trans_path.stem}_diarized.json"

    # Merge the data
    try:
        result = merge_diarization_transcription(diarization, transcription)

        # Save results
        save_merged(result, output_file)

        print(f"\nNext step:", file=sys.stderr)
        print(f"  ./hushnote label {output_file}", file=sys.stderr)

    except Exception as e:
        print(f"Error during merge: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
