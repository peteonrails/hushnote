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
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MEETING_DIR="${OUTPUT_DIR}/${DATE}/meeting_${TIMESTAMP}"
OUTPUT_FILE="${MEETING_DIR}/meeting_${TIMESTAMP}.wav"

# Parse arguments
DURATION=""
TITLE=""
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
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-d DURATION] [-o OUTPUT_FILE] [-t TITLE]"
            echo "  -d, --duration    Recording duration (e.g., 3600 for 1 hour)"
            echo "  -o, --output      Output file path (default: ./recordings/meeting_TIMESTAMP.wav)"
            echo "  -t, --title       Meeting title"
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

# Determine audio source.
# AUDIO_SOURCE env var overrides everything.
# AUDIO_SOURCE_TYPE controls what to capture:
#   "microphone" (default) - default PulseAudio/PipeWire source (mic)
#   "monitor"              - monitor of default sink (captures output audio,
#                            needed for meeting audio on BT headsets)
if [ -n "${AUDIO_SOURCE:-}" ]; then
    RECORD_SOURCE="$AUDIO_SOURCE"
elif [ "${AUDIO_SOURCE_TYPE:-microphone}" = "monitor" ]; then
    RECORD_SOURCE="$(pactl get-default-sink).monitor"
else
    RECORD_SOURCE="$(pactl get-default-source)"
fi

echo "Recording audio..." >&2
echo "Output file: $OUTPUT_FILE" >&2
echo "Audio source: $RECORD_SOURCE" >&2
if [ -n "$DURATION" ]; then
    echo "Duration: ${DURATION}s" >&2
fi
echo "" >&2
echo "Press Ctrl+C to stop recording" >&2

# RECORD_BACKEND controls the recording tool:
#   "ffmpeg" (default) - ffmpeg with PulseAudio compat layer
#   "pw-record"        - pw-record, talks directly to PipeWire graph;
#                        required for BT headsets in HSP/HFP mode where
#                        ffmpeg -f pulse captures silence
RECORD_BACKEND="${RECORD_BACKEND:-ffmpeg}"

if [ "$RECORD_BACKEND" = "pw-record" ]; then
    PW_CMD="pw-record --target $RECORD_SOURCE --rate 16000 --channels 1 --format s16"
    if [ -n "$DURATION" ]; then
        PW_CMD="timeout $DURATION $PW_CMD"
    fi
    PW_CMD="$PW_CMD $OUTPUT_FILE"
    set +e
    eval $PW_CMD >&2
    ffmpeg_exit_code=$?
    set -e
else
    FFMPEG_CMD="ffmpeg -f pulse -i $RECORD_SOURCE"
    if [ -n "$DURATION" ]; then
        FFMPEG_CMD="$FFMPEG_CMD -t $DURATION"
    fi
    FFMPEG_CMD="$FFMPEG_CMD -ar 16000 -ac 1 -c:a pcm_s16le $OUTPUT_FILE"
    set +e
    eval $FFMPEG_CMD >&2
    ffmpeg_exit_code=$?
    set -e
fi

# Always output filename if file was created, even if interrupted
if [ -f "$OUTPUT_FILE" ]; then
    echo "" >&2
    echo "Recording saved to: $OUTPUT_FILE" >&2

    # Prompt for title if not provided
    if [ -z "$TITLE" ]; then
        echo "" >&2
        read -p "Meeting title (optional): " TITLE </dev/tty
    fi

    # Create metadata file
    meeting_dir=$(dirname "$OUTPUT_FILE")
    base_name=$(basename "$OUTPUT_FILE" .wav)
    metadata_file="${meeting_dir}/${base_name}_metadata.json"

    # Generate metadata JSON
    cat > "$metadata_file" << EOF
{
  "title": "${TITLE}",
  "timestamp": "${TIMESTAMP}",
  "date": "${DATE}",
  "audio_file": "$(basename "$OUTPUT_FILE")",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "local_recording"
}
EOF

    if [ -n "$TITLE" ]; then
        echo "Title: $TITLE" >&2
    fi

    # Output only the filename to stdout (for script capture)
    echo "$OUTPUT_FILE"
else
    echo "" >&2
    echo "Error: Recording file was not created" >&2
    exit 1
fi
