#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    [[ "$haystack" == *"$needle"* ]] || fail "expected output to contain: $needle\n$haystack"
}

make_hushnote_copy() {
    local workdir="$1"
    mkdir -p "$workdir/app"
    cp "$ROOT_DIR/hushnote" "$workdir/app/hushnote"
    chmod +x "$workdir/app/hushnote"
}

make_meeting() {
    local recordings_dir="$1"
    local date="$2"
    local name="$3"
    local age="$4"
    local dir_age="${5:-0}"

    local meeting_dir="$recordings_dir/$date/$name"
    mkdir -p "$meeting_dir"
    printf 'audio' > "$meeting_dir/$name.wav"
    touch -d "$age" "$meeting_dir/$name.wav"
    touch -d "$dir_age" "$meeting_dir"
}

run_catchup() {
    local app_dir="$1"
    local recordings_dir="$2"
    shift 2
    RECORDINGS_DIR="$recordings_dir" "$app_dir/hushnote" catchup --dry-run "$@" 2>&1
}

test_min_age_skips_young_audio() {
    local tmp
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN
    make_hushnote_copy "$tmp"
    make_meeting "$tmp/recordings" 20260527 meeting_20260527_090000 now now

    local output
    output=$(run_catchup "$tmp/app" "$tmp/recordings" --min-age 300)

    assert_contains "$output" "Skipping young recording"
    assert_contains "$output" "would process: 0"
}

test_min_age_allows_old_audio() {
    local tmp
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN
    make_hushnote_copy "$tmp"
    make_meeting "$tmp/recordings" 20260527 meeting_20260527_090000 '10 minutes ago' now

    local output
    output=$(run_catchup "$tmp/app" "$tmp/recordings" --min-age 300)

    assert_contains "$output" "Needs processing"
    assert_contains "$output" "would process: 1"
}

test_recent_days_skips_old_meeting_dirs() {
    local tmp
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN
    make_hushnote_copy "$tmp"
    make_meeting "$tmp/recordings" 20260522 meeting_20260522_090000 '5 days ago' '5 days ago'

    local output
    output=$(run_catchup "$tmp/app" "$tmp/recordings" --recent-days 3 --min-age 300)

    assert_contains "$output" "would process: 0"
}

test_lock_file_skips_when_another_run_is_active() {
    local tmp
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN
    make_hushnote_copy "$tmp"
    make_meeting "$tmp/recordings" 20260527 meeting_20260527_090000 '10 minutes ago' now

    local lock_file="$tmp/catchup.lock"
    exec 9>"$lock_file"
    flock -n 9

    local output
    output=$(run_catchup "$tmp/app" "$tmp/recordings" --lock-file "$lock_file")

    assert_contains "$output" "another catchup run is active"
}

test_environment_defaults_are_used() {
    local tmp
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN
    make_hushnote_copy "$tmp"
    make_meeting "$tmp/recordings" 20260527 meeting_20260527_090000 now now

    local output
    output=$(
        RECORDINGS_DIR="$tmp/recordings" \
        HUSHNOTE_CATCHUP_DAYS=3 \
        HUSHNOTE_CATCHUP_MIN_AGE=300 \
        "$tmp/app/hushnote" catchup --dry-run 2>&1
    )

    assert_contains "$output" "Skipping young recording"
    assert_contains "$output" "would process: 0"
}

test_active_pattern_skips_when_matching_process_exists() {
    local tmp
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN
    make_hushnote_copy "$tmp"
    make_meeting "$tmp/recordings" 20260527 meeting_20260527_090000 '10 minutes ago' now

    bash -c 'exec -a hushnote_test_active_sleep sleep 30' &
    local sleeper=$!
    trap 'kill "$sleeper" 2>/dev/null || true; rm -rf "$tmp"' RETURN

    local output
    output=$(run_catchup "$tmp/app" "$tmp/recordings" --active-pattern '^hushnote_test_active_sleep')

    kill "$sleeper" 2>/dev/null || true
    assert_contains "$output" "hushnote is active, skipping catchup"
}

for test_name in \
    test_min_age_skips_young_audio \
    test_min_age_allows_old_audio \
    test_recent_days_skips_old_meeting_dirs \
    test_lock_file_skips_when_another_run_is_active \
    test_environment_defaults_are_used \
    test_active_pattern_skips_when_matching_process_exists; do
    "$test_name"
    echo "ok - $test_name"
done
