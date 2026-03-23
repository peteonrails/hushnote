# HushNote

**Privacy-first meeting transcription and voice-to-text tool for Linux**

HushNote is a local-only, offline-capable voice transcription and meeting summarization tool. All processing happens on your machine using local AI models — no cloud services, no data sharing, complete privacy.

> **This is the actively maintained fork.** The [original repository](https://github.com/peteonrails/hushnote) is no longer active. This fork adds faster-whisper, PipeWire support, configurable audio sources, language detection, and more.

## Features

- **🎙️ Audio Recording**: Capture system audio, microphone, or both simultaneously via PulseAudio/PipeWire
- **📝 Speech-to-Text Transcription**: Convert audio to text using faster-whisper (offline, GPU-accelerated)
- **👥 Speaker Diarization**: Identify who spoke when with interactive speaker labeling
- **🤖 AI Summarization**: Generate meeting notes, action items, and summaries using Ollama
- **🔒 100% Private**: All processing happens locally — no internet required after setup
- **⚡ GPU Acceleration**: AMD ROCm and NVIDIA CUDA supported
- **📊 Multiple Output Formats**: TXT, JSON, SRT, VTT for transcripts; Markdown for summaries

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

# Create and activate a virtual environment
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

### System dependencies

**Arch/CachyOS:**
```bash
# PulseAudio
yay -S ffmpeg pulseaudio-utils python

# PipeWire
yay -S ffmpeg pipewire-pulse python
```

## Configuration

Copy `.hushnoterc.example` to `.hushnoterc` and edit to your needs:

```bash
cp .hushnoterc.example .hushnoterc
```

`.hushnoterc` is sourced at startup and ignored by git (personal paths and secrets stay local). The example file documents every available option with defaults and comments.

### Whisper Models

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `tiny` | 75 MB | ~10-20x realtime | Testing |
| `base` | 150 MB | ~5-10x realtime | Balanced (default) |
| `small` | 500 MB | ~2-5x realtime | Better accuracy |
| `medium` | 1.5 GB | ~1-2x realtime | Professional |
| `large-v3` | 3 GB | ~0.5-1x realtime | Maximum accuracy |

Models download automatically on first use.

## Usage

```
Commands:
    record              Start recording (stop with Ctrl+C)
    transcribe FILE     Transcribe an audio file
    summarize FILE      Summarize a transcription
    diarize FILE        Identify speakers in an audio file
    label FILE          Label speakers interactively
    apply-labels FILE   Apply labels to create final transcript
    full                Complete workflow: record, transcribe, summarize
    process FILE        Process an existing recording
    process-last        Process the most recent recording
    list                List all recordings

Options:
    -d, --duration SEC    Recording duration (default: manual stop with Ctrl+C)
    -m, --model MODEL     Whisper model (tiny|base|small|medium|large-v3)
    -l, --language LANG   Language code, e.g. nl, en (default: auto-detect)
    -o, --ollama MODEL    Ollama model for summarization
    -f, --format FMT      Output format (txt|json|srt|vtt|md)
    -s, --speakers NUM    Number of speakers (for diarization)
    -t, --title TITLE     Meeting title (prompted if not provided)
    --diarize             Enable speaker diarization in full workflow
    --timeout SECS        Kill processing after SECS seconds (default: 7200)
```

### Common workflows

```bash
# Record a meeting (Ctrl+C to stop, then transcribe and summarize automatically)
./hushnote full

# Full workflow with speaker diarization
./hushnote full --diarize --speakers 2

# Process a recording you already have
./hushnote process recordings/meeting.wav

# Process the most recent recording
./hushnote process-last

# List all recordings and their status
./hushnote list
```

See [DIARIZATION.md](DIARIZATION.md) for the full speaker diarization guide.

## Output

Recordings are organized by date and meeting:

```
~/meeting-notes/
└── 20260310/
    └── meeting_20260310_090012/
        ├── meeting_20260310_090012.mp3          # compressed audio
        ├── meeting_20260310_090012.txt          # transcription
        ├── meeting_20260310_090012_summary.md   # meeting summary
        └── meeting_20260310_090012_metadata.json
```

## Troubleshooting

**No audio captured:**
```bash
pactl list sources short
pactl set-default-source YOUR_SOURCE_NAME
./record_audio.sh -d 5   # test with a 5-second recording
```

**Ollama not responding:**
```bash
systemctl status ollama
ollama list
```

**GPU out of memory:** HushNote automatically falls back to CPU if CUDA OOM occurs during model load or transcription.

## License

MIT — see LICENSE file.

## Credits

Built on top of [faster-whisper](https://github.com/guillaumekln/faster-whisper), [Ollama](https://ollama.ai), [pyannote.audio](https://github.com/pyannote/pyannote-audio), and [ffmpeg](https://ffmpeg.org).
