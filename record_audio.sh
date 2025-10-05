#!/bin/bash

# Audio recording script for meetings
# Records system audio and microphone to a WAV file

set -euo pipefail

# Check for dependencies
if ! command -v pactl &> /dev/null; then
    echo "Error: pactl not found. Install pulseaudio-utils or pipewire-pulse"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg not found. Install ffmpeg"
    exit 1
fi

# Configuration
OUTPUT_DIR="${RECORDINGS_DIR:-./recordings}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/meeting_${TIMESTAMP}.wav"

# Parse arguments
DURATION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-d DURATION] [-o OUTPUT_FILE]"
            echo "  -d, --duration    Recording duration (e.g., 3600 for 1 hour)"
            echo "  -o, --output      Output file path (default: ./recordings/meeting_TIMESTAMP.wav)"
            echo ""
            echo "Environment variables:"
            echo "  RECORDINGS_DIR    Directory for recordings (default: ./recordings)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Get default audio source (microphone)
DEFAULT_SOURCE=$(pactl get-default-source)

echo "Recording audio..." >&2
echo "Output file: $OUTPUT_FILE" >&2
echo "Audio source: $DEFAULT_SOURCE" >&2
if [ -n "$DURATION" ]; then
    echo "Duration: ${DURATION}s" >&2
fi
echo "" >&2
echo "Press Ctrl+C to stop recording" >&2

# Build ffmpeg command
FFMPEG_CMD="ffmpeg -f pulse -i $DEFAULT_SOURCE"

if [ -n "$DURATION" ]; then
    FFMPEG_CMD="$FFMPEG_CMD -t $DURATION"
fi

FFMPEG_CMD="$FFMPEG_CMD -ar 16000 -ac 1 -c:a pcm_s16le $OUTPUT_FILE"

# Start recording
eval $FFMPEG_CMD >&2

echo "" >&2
echo "Recording saved to: $OUTPUT_FILE" >&2

# Output only the filename to stdout (for script capture)
echo "$OUTPUT_FILE"
