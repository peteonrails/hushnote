#!/usr/bin/env python3

"""
Apply speaker labels to create final transcript
Takes labeled diarization data and outputs formatted text with speaker names
"""

import argparse
import json
import sys
from pathlib import Path


def load_labeled_json(file_path: str) -> dict:
    """Load labeled diarization JSON file"""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text())

    if "segments" not in data or not data["segments"]:
        print("Error: No segments found in file", file=sys.stderr)
        sys.exit(1)

    return data


def get_speaker_name(speaker_id: str, labels: dict) -> str:
    """
    Get speaker name from labels, fallback to speaker_id

    Args:
        speaker_id: Raw speaker ID (e.g., SPEAKER_00)
        labels: Dictionary of speaker labels

    Returns:
        Speaker name or speaker_id if not labeled
    """
    if speaker_id in labels:
        return labels[speaker_id].get("name", speaker_id)
    return speaker_id


def apply_labels_to_transcript(data: dict, format: str = "txt") -> str:
    """
    Apply speaker labels to segments and format as text

    Args:
        data: Labeled diarization data
        format: Output format (txt, md, json, srt, vtt)

    Returns:
        Formatted transcript string
    """
    segments = data["segments"]
    labels = data.get("labels", {})

    if format == "txt" or format == "md":
        lines = []
        current_speaker = None

        for seg in segments:
            speaker_id = seg["speaker_id"]
            speaker_name = get_speaker_name(speaker_id, labels)
            text = seg["text"].strip()

            if not text:
                continue

            # Group consecutive segments from same speaker
            if speaker_name != current_speaker:
                if format == "md":
                    lines.append(f"\n**{speaker_name}**: {text}")
                else:
                    lines.append(f"\n[{speaker_name}] {text}")
                current_speaker = speaker_name
            else:
                # Continue previous speaker
                lines.append(text)

        return " ".join(lines).strip()

    elif format == "json":
        # JSON output with speaker names
        output_segments = []
        for seg in segments:
            speaker_id = seg["speaker_id"]
            speaker_name = get_speaker_name(speaker_id, labels)

            output_segments.append({
                "speaker": speaker_name,
                "speaker_id": speaker_id,
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"]
            })

        return json.dumps({
            "audio_file": data.get("audio_file"),
            "duration": data.get("duration"),
            "language": data.get("language"),
            "num_speakers": data.get("num_speakers"),
            "segments": output_segments,
            "labels": labels
        }, indent=2)

    elif format == "srt":
        # SRT subtitle format with speaker names
        lines = []
        for i, seg in enumerate(segments, 1):
            speaker_id = seg["speaker_id"]
            speaker_name = get_speaker_name(speaker_id, labels)
            text = seg["text"].strip()

            if not text:
                continue

            # Format timestamps
            start_time = format_srt_timestamp(seg["start"])
            end_time = format_srt_timestamp(seg["end"])

            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(f"[{speaker_name}] {text}")
            lines.append("")

        return "\n".join(lines)

    elif format == "vtt":
        # WebVTT format with speaker names
        lines = ["WEBVTT", ""]

        for seg in segments:
            speaker_id = seg["speaker_id"]
            speaker_name = get_speaker_name(speaker_id, labels)
            text = seg["text"].strip()

            if not text:
                continue

            # Format timestamps
            start_time = format_vtt_timestamp(seg["start"])
            end_time = format_vtt_timestamp(seg["end"])

            lines.append(f"{start_time} --> {end_time}")
            lines.append(f"[{speaker_name}] {text}")
            lines.append("")

        return "\n".join(lines)

    else:
        raise ValueError(f"Unsupported format: {format}")


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    """Format seconds to WebVTT timestamp (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def save_transcript(content: str, output_file: str):
    """Save transcript to file"""
    output_path = Path(output_file)
    output_path.write_text(content)
    print(f"Transcript saved to: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Apply speaker labels to create final transcript"
    )
    parser.add_argument("labeled_file",
                       help="Path to labeled JSON file (_speakers_labeled.json)")
    parser.add_argument("-f", "--format", default="txt",
                       choices=["txt", "md", "json", "srt", "vtt"],
                       help="Output format (default: txt)")
    parser.add_argument("-o", "--output",
                       help="Output file (default: audio_file.txt)")

    args = parser.parse_args()

    # Load labeled data
    data = load_labeled_json(args.labeled_file)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Get base name from audio file in data
        audio_file = data.get("audio_file", "transcript")
        base_name = Path(audio_file).stem
        labeled_path = Path(args.labeled_file)
        output_file = labeled_path.parent / f"{base_name}.{args.format}"

    # Apply labels and format
    try:
        print(f"Applying labels to transcript...", file=sys.stderr)
        transcript = apply_labels_to_transcript(data, format=args.format)

        # Save result
        save_transcript(transcript, output_file)

        print(f"\nTranscript complete!", file=sys.stderr)

        # Show next step
        if args.format in ["txt", "md"]:
            print(f"\nNext step:", file=sys.stderr)
            print(f"  ./hushnote summarize {output_file}", file=sys.stderr)

    except Exception as e:
        print(f"Error applying labels: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
