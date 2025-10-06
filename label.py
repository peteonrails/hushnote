#!/usr/bin/env python3

"""
Interactive speaker labeling
Shows actual quotes from each speaker and prompts user to identify them
"""

import argparse
import json
import sys
import random
from pathlib import Path
from datetime import datetime, timezone


def load_diarized_json(file_path: str) -> dict:
    """Load diarized JSON file"""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text())

    if "segments" not in data or not data["segments"]:
        print("Error: No segments found in file", file=sys.stderr)
        print("Make sure you've run diarization and transcription first", file=sys.stderr)
        sys.exit(1)

    # Check if segments have text
    if "text" not in data["segments"][0]:
        print("Error: Segments don't contain transcribed text", file=sys.stderr)
        print("Make sure you've merged diarization with transcription", file=sys.stderr)
        sys.exit(1)

    return data


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def get_speaker_samples(data: dict, speaker_id: str, num_samples: int = 3, random_samples: bool = False) -> list:
    """
    Get sample quotes from a speaker

    Args:
        data: Diarized data with segments
        speaker_id: Speaker to get samples for
        num_samples: Number of sample quotes to return
        random_samples: If True, get random samples instead of beginning/middle/end

    Returns:
        List of sample segments with text
    """
    speaker_segments = [
        seg for seg in data["segments"]
        if seg["speaker_id"] == speaker_id and seg["text"].strip()
    ]

    if not speaker_segments:
        return []

    if random_samples:
        # Get random samples
        if len(speaker_segments) <= num_samples:
            return speaker_segments
        return random.sample(speaker_segments, num_samples)
    else:
        # Get samples from beginning, middle, and end
        samples = []
        if len(speaker_segments) >= num_samples:
            # First quote
            samples.append(speaker_segments[0])
            # Middle quote
            samples.append(speaker_segments[len(speaker_segments) // 2])
            # Last quote (or near end)
            samples.append(speaker_segments[-1])
        else:
            # Just return what we have
            samples = speaker_segments[:num_samples]

        return samples


def display_quotes(samples: list, max_length: int = 100):
    """Display quote samples with timestamps"""
    if not samples:
        print("  (No quotes available)")
        return

    print("Sample quotes:")
    for sample in samples:
        timestamp = format_time(sample["start"])
        text = sample["text"].strip()
        # Truncate long quotes
        if len(text) > max_length:
            text = text[:max_length] + "..."
        print(f"  [{timestamp}] \"{text}\"")


def interactive_label_speakers(data: dict) -> dict:
    """
    Interactively prompt user to label each speaker

    Args:
        data: Diarized data with segments

    Returns:
        Updated data with labels
    """
    # Get unique speakers
    speakers = sorted(set(seg["speaker_id"] for seg in data["segments"]))

    if not speakers:
        print("Error: No speakers found in data", file=sys.stderr)
        sys.exit(1)

    print("\nHushNote Speaker Labeling")
    print("═" * 70)
    print(f"\nFound {len(speakers)} speaker(s) in {data.get('audio_file', 'audio')}")
    print()

    labels = data.get("labels", {})

    for speaker_id in speakers:
        print("─" * 70)

        # Get speaker stats
        stats = data.get("speaker_stats", {}).get(speaker_id, {})
        total_time = stats.get("total_time", 0)
        segment_count = stats.get("segment_count", 0)

        print(f"{speaker_id} ({format_time(total_time)}, {segment_count} segments)")
        print()

        # Get initial sample quotes
        samples = get_speaker_samples(data, speaker_id, num_samples=3)
        display_quotes(samples)
        print()

        # Prompt for name
        while True:
            try:
                prompt = f"Who is {speaker_id}? (or 'm' for more quotes) "
                response = input(prompt).strip()

                if response.lower() == 'm':
                    # Show more random quotes
                    print()
                    samples = get_speaker_samples(data, speaker_id, num_samples=5, random_samples=True)
                    display_quotes(samples)
                    print()
                    continue

                if response:
                    labels[speaker_id] = {
                        "name": response,
                        "email": None,
                        "role": None,
                        "source": "manual",
                        "labeled_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    }
                    print(f"✓ Labeled as \"{response}\"")
                    break
                else:
                    # Allow skipping
                    skip = input("Skip this speaker? (y/n) ").strip().lower()
                    if skip == 'y':
                        labels[speaker_id] = {
                            "name": speaker_id,
                            "email": None,
                            "role": None,
                            "source": "skipped",
                            "labeled_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        }
                        print(f"⊘ Skipped, will use {speaker_id}")
                        break

            except (KeyboardInterrupt, EOFError):
                print("\n\nLabeling interrupted", file=sys.stderr)
                sys.exit(1)

        print()

    print("─" * 70)
    print("✓ All speakers labeled!")
    print()

    # Update data with labels
    data["labels"] = labels

    return data


def save_labeled(data: dict, output_file: str):
    """Save labeled results to JSON file"""
    output_path = Path(output_file)
    output_path.write_text(json.dumps(data, indent=2))
    print(f"Saved to: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Interactively label speakers with their names"
    )
    parser.add_argument("diarized_file",
                       help="Path to diarized JSON file (_diarized.json)")
    parser.add_argument("-o", "--output",
                       help="Output file (default: input_file_labeled.json)")
    parser.add_argument("--non-interactive", action="store_true",
                       help="Skip interactive prompts (for testing)")

    args = parser.parse_args()

    # Load diarized data
    data = load_diarized_json(args.diarized_file)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.diarized_file)
        # Replace _diarized.json with _speakers_labeled.json
        if input_path.stem.endswith("_diarized"):
            base_name = input_path.stem.replace("_diarized", "")
            output_file = input_path.parent / f"{base_name}_speakers_labeled.json"
        else:
            output_file = input_path.parent / f"{input_path.stem}_labeled.json"

    # Label speakers
    try:
        if args.non_interactive:
            print("Non-interactive mode: skipping speaker labeling", file=sys.stderr)
        else:
            data = interactive_label_speakers(data)

        # Save results
        save_labeled(data, output_file)

        print("\nNext step:", file=sys.stderr)
        print(f"  ./hushnote apply-labels {output_file}", file=sys.stderr)

    except Exception as e:
        print(f"Error during labeling: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
