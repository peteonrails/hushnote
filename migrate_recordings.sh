#!/bin/bash

# Migration script to move old flat recordings into new date/meeting directory structure
# Usage: ./migrate_recordings.sh [recordings_dir]

set -euo pipefail

RECORDINGS_DIR="${1:-./recordings}"

if [ ! -d "$RECORDINGS_DIR" ]; then
    echo "Error: Recordings directory not found: $RECORDINGS_DIR"
    exit 1
fi

echo "Migrating recordings from flat structure to date/meeting subdirectories..."
echo "Recordings directory: $RECORDINGS_DIR"
echo ""

migrated_count=0
skipped_count=0

# Find all .wav files in the root of recordings directory (not in subdirectories)
for wav_file in "$RECORDINGS_DIR"/meeting_*.wav; do
    if [ ! -f "$wav_file" ]; then
        continue
    fi

    # Extract timestamp from filename: meeting_YYYYMMDD_HHMMSS.wav
    filename=$(basename "$wav_file")
    if [[ $filename =~ meeting_([0-9]{8})_([0-9]{6})\.wav ]]; then
        date_part="${BASH_REMATCH[1]}"
        timestamp="${BASH_REMATCH[1]}_${BASH_REMATCH[2]}"

        # Create date directory
        date_dir="$RECORDINGS_DIR/$date_part"
        mkdir -p "$date_dir"

        # Create meeting directory
        meeting_dir="$date_dir/meeting_$timestamp"

        if [ -d "$meeting_dir" ]; then
            echo "Skipping $filename (target directory already exists)"
            skipped_count=$((skipped_count + 1))
            continue
        fi

        mkdir -p "$meeting_dir"

        # Move all related files (same base name)
        base="${wav_file%.*}"
        base_name=$(basename "$base")

        moved_files=""
        for file in "$RECORDINGS_DIR/$base_name".*; do
            if [ -f "$file" ]; then
                mv "$file" "$meeting_dir/"
                moved_files="$moved_files $(basename "$file")"
            fi
        done

        echo "✓ Migrated: $filename → $date_part/meeting_$timestamp/"
        echo "  Files moved:$moved_files"
        migrated_count=$((migrated_count + 1))
    else
        echo "⚠ Skipping: $filename (doesn't match expected pattern)"
        skipped_count=$((skipped_count + 1))
    fi
done

echo ""
echo "Migration complete!"
echo "  Migrated: $migrated_count meeting(s)"
echo "  Skipped:  $skipped_count file(s)"

if [ $migrated_count -gt 0 ]; then
    echo ""
    echo "You can now use './hushnote list' to see your migrated recordings."
fi
