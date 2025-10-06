#!/bin/bash

# Audio compression script
# Converts WAV files to MP3 format using ffmpeg

set -euo pipefail

# Check for dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg not found. Install ffmpeg" >&2
    exit 1
fi

print_usage() {
    cat << EOF
Usage: $0 <audio_file.wav> [OPTIONS]

Convert WAV audio file to MP3 format

Options:
    --bitrate RATE    MP3 bitrate (default: 128k)
    --delete-wav      Delete original WAV file after compression
    -h, --help        Show this help message

Examples:
    # Convert to MP3
    $0 recording.wav

    # Convert with higher quality
    $0 recording.wav --bitrate 192k

    # Convert and delete original
    $0 recording.wav --delete-wav
EOF
}

# Parse arguments
if [ $# -eq 0 ]; then
    print_usage
    exit 1
fi

WAV_FILE=""
BITRATE="128k"
DELETE_WAV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        --bitrate)
            BITRATE="$2"
            shift 2
            ;;
        --delete-wav)
            DELETE_WAV=true
            shift
            ;;
        *)
            if [ -z "$WAV_FILE" ]; then
                WAV_FILE="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate input file
if [ -z "$WAV_FILE" ]; then
    echo "Error: No audio file specified" >&2
    exit 1
fi

if [ ! -f "$WAV_FILE" ]; then
    echo "Error: File not found: $WAV_FILE" >&2
    exit 1
fi

# Check if file is actually a WAV
if [[ ! "$WAV_FILE" =~ \.wav$ ]]; then
    echo "Warning: File doesn't have .wav extension: $WAV_FILE" >&2
fi

# Determine output file
OUTPUT_FILE="${WAV_FILE%.wav}.mp3"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Warning: Output file already exists: $OUTPUT_FILE" >&2
    echo "Skipping compression" >&2
    exit 0
fi

echo "Compressing audio file..." >&2
echo "Input:  $WAV_FILE" >&2
echo "Output: $OUTPUT_FILE" >&2
echo "Bitrate: $BITRATE" >&2

# Get original file size
original_size=$(du -h "$WAV_FILE" | cut -f1)

# Convert to MP3
ffmpeg -i "$WAV_FILE" -codec:a libmp3lame -b:a "$BITRATE" -y "$OUTPUT_FILE" 2>&1 | grep -v "^size=" || true

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Compression failed" >&2
    exit 1
fi

# Get compressed file size
compressed_size=$(du -h "$OUTPUT_FILE" | cut -f1)

echo "" >&2
echo "Compression complete!" >&2
echo "Original:   $original_size" >&2
echo "Compressed: $compressed_size" >&2

# Calculate compression ratio
original_bytes=$(stat -c%s "$WAV_FILE")
compressed_bytes=$(stat -c%s "$OUTPUT_FILE")
if command -v bc &> /dev/null; then
    ratio=$(echo "scale=1; $original_bytes / $compressed_bytes" | bc)
    echo "Ratio: ${ratio}x smaller" >&2
else
    # Fallback without bc
    ratio=$((original_bytes / compressed_bytes))
    echo "Ratio: ~${ratio}x smaller" >&2
fi

# Delete WAV if requested
if [ "$DELETE_WAV" = true ]; then
    echo "" >&2
    echo "Deleting original WAV file..." >&2
    rm "$WAV_FILE"
    echo "Deleted: $WAV_FILE" >&2
fi

# Output the MP3 filename to stdout (for script capture)
echo "$OUTPUT_FILE"
