# HushNote

**Privacy-first meeting transcription and voice-to-text tool for Linux**

HushNote is a local-only, offline-capable voice transcription and meeting summarization tool. All processing happens on your machine using local AI models — no cloud services, no data sharing, complete privacy.

> **This is the actively maintained fork.** The [original repository](https://github.com/peteonrails/hushnote) is no longer active. This fork adds faster-whisper, PipeWire support, configurable audio sources, silent tail trimming, status/catchup commands, post-summary hooks, and more.

## Features

- **🎙️ Audio Recording**: Capture system audio, microphone, or both simultaneously via PulseAudio/PipeWire
- **📝 Speech-to-Text Transcription**: Convert audio to text using faster-whisper (offline, GPU-accelerated, auto language detection)
- **✂️ Silent Tail Trimming**: Automatically detects and removes silent tails from recordings (e.g. when you forget to stop recording) using binary search — fast regardless of file length
- **👥 Speaker Diarization**: Identify who spoke when with interactive speaker labeling
- **🤖 AI Summarization**: Generate structured meeting notes using Ollama — summary, discussion points, decisions, and action items (only when genuinely present)
- **📋 Status & Catchup**: See which recordings are pending, partially processed, or complete; automatically process any that got missed
- **🔗 Post-Summary Hook**: Run any script after summarization completes — upload to Outline, Notion, a webhook, or anything else
- **🔒 100% Private**: All processing happens locally — no internet required after setup
- **⚡ GPU Acceleration**: AMD ROCm and NVIDIA CUDA supported, with automatic CPU fallback

## Installation

### System Requirements

- Linux (tested on CachyOS/Arch)
- Python 3.10+
- ffmpeg
- PulseAudio or PipeWire
- Ollama (for summarization)
- Optional: GPU with ROCm or CUDA

### Quick Install

```bash
git clone https://github.com/larsderidder/hushnote.git
cd hushnote

# Create a virtual environment
python -m venv venv

# Install core dependencies
./venv/bin/pip install -e .

# Install with speaker diarization support
./venv/bin/pip install -e '.[diarize]'

# For GPU-accelerated PyTorch (CUDA):
./venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# Test installation
./hushnote --help
```

**Arch/CachyOS system dependencies:**
```bash
yay -S ffmpeg pipewire-pulse python   # PipeWire
# or
yay -S ffmpeg pulseaudio-utils python  # PulseAudio
```

## Configuration

Copy `.hushnoterc.example` to `.hushnoterc` and edit to your needs:

```bash
cp .hushnoterc.example .hushnoterc
```

`.hushnoterc` is sourced at startup and ignored by git. The example file documents every available option with defaults and comments, including audio backend, Whisper model, Ollama model, silent tail trimming thresholds, and the post-summary hook.

### Whisper Models

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `tiny` | 75 MB | ~10-20x realtime | Testing |
| `base` | 150 MB | ~5-10x realtime | Balanced (default) |
| `small` | 500 MB | ~2-5x realtime | Better accuracy |
| `medium` | 1.5 GB | ~1-2x realtime | Professional |
| `large-v3` | 3 GB | ~0.5-1x realtime | Maximum accuracy |

Models download automatically on first use. Language is auto-detected by default.

## Usage

```
Commands:
    record              Start recording (stop with Ctrl+C)
    transcribe FILE     Transcribe an audio file
    summarize FILE      Summarize a transcription
    trim FILE           Detect and remove silent tail from an audio file
    diarize FILE        Identify speakers in an audio file
    label FILE          Label speakers interactively
    apply-labels FILE   Apply labels to create final transcript
    compress FILE       Compress WAV to MP3
    full                Complete workflow: record, compress, trim, transcribe, summarize
    process FILE        Process an existing recording (compress, trim, transcribe, summarize)
    process-last        Process the most recent recording
    list                List all recordings
    status              Show status of all recordings
    catchup             Process any unfinished recordings and run post-summary hook

Options:
    -d, --duration SEC      Recording duration (default: manual stop with Ctrl+C)
    -m, --model MODEL       Whisper model (tiny|base|small|medium|large-v3)
    -l, --language LANG     Language code, e.g. nl, en (default: auto-detect)
    -o, --ollama MODEL      Ollama model for summarization
    -f, --format FMT        Output format (txt|json|srt|vtt|md)
    -s, --speakers NUM      Number of speakers (for diarization)
    -t, --title TITLE       Meeting title (prompted if not provided)
    --diarize               Enable speaker diarization in full workflow
    --no-trim               Skip silent tail trimming
    --keep-untrimmed        Keep full MP3 alongside trimmed version (default: delete)
    --keep-trimmed          Keep trimmed MP3 after transcription (default: keep)
    --timeout SECS          Kill processing after SECS seconds (default: 7200)
```

### Common workflows

```bash
# Record a meeting, stop with Ctrl+C — automatically compresses, trims, transcribes, summarizes
./hushnote full

# Check status of all recordings
./hushnote status

# Process any recordings that were interrupted or missed
./hushnote catchup

# Process a recording you already have
./hushnote process recordings/meeting.wav

# Trim a recording manually (remove silent tail)
./hushnote trim recordings/meeting.mp3
```

See [DIARIZATION.md](DIARIZATION.md) for the full speaker diarization guide.

## Pipeline

The full recording workflow:

```
record → WAV
       → compress to MP3, delete WAV
       → trim silent tail → meeting_trimmed.mp3
       → transcribe trimmed MP3 → meeting.txt
       → summarize → meeting_summary.md
       → run POST_SUMMARY_HOOK (if set)
       → delete untrimmed MP3 (keep with --keep-untrimmed)
```

## Output

Recordings are organized by date and meeting:

```
~/meeting-notes/
└── 20260310/
    └── meeting_20260310_090012/
        ├── meeting_20260310_090012.mp3           # trimmed audio (kept by default)
        ├── meeting_20260310_090012.txt           # transcription
        ├── meeting_20260310_090012_summary.md    # meeting summary
        ├── meeting_20260310_090012_metadata.json # title, timestamp
        └── meeting_20260310_090012.hook_done     # written after hook runs
```

## Post-Summary Hook

Set `POST_SUMMARY_HOOK` in `.hushnoterc` to run a script after every summary is created. The script receives the summary file path as `$1`. On success, hushnote writes a `.hook_done` marker so `catchup` knows not to re-run it.

```bash
# In .hushnoterc:
POST_SUMMARY_HOOK="${HOME}/.local/bin/my-upload-script"
```

Use this to upload to Outline, Notion, a webhook, or any other destination. See `.hushnoterc.example` for details.

## Troubleshooting

**No audio captured:**
```bash
pactl list sources short
pactl set-default-source YOUR_SOURCE_NAME
./record_audio.sh -d 5   # test with a 5-second recording
```

**Wrong language detected:** faster-whisper samples the first 30 seconds for language detection. If your meeting starts with silence or a different language, set `WHISPER_LANGUAGE` in `.hushnoterc`.

**Ollama not responding:**
```bash
systemctl status ollama
ollama list
```

**GPU out of memory:** HushNote automatically falls back to CPU if CUDA OOM occurs during model load or transcription.

**Recording has a long silent tail:** Run `hushnote trim FILE` to detect and remove it. The binary search scans ~10 windows to find the content boundary regardless of file length.

## License

MIT. See LICENSE file.

## Credits

Built on top of [faster-whisper](https://github.com/guillaumekln/faster-whisper), [Ollama](https://ollama.ai), [pyannote.audio](https://github.com/pyannote/pyannote-audio), and [ffmpeg](https://ffmpeg.org).
