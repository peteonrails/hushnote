# HushNote

**Privacy-first meeting transcription and voice-to-text tool for Linux**

HushNote is a local-only, offline-capable voice transcription and meeting summarization tool. All processing happens on your machine using local AI models—no cloud services, no data sharing, complete privacy.

## Features

### Current Capabilities

- **🎙️ Audio Recording**: Capture system audio and microphone input using PulseAudio/PipeWire
- **📝 Speech-to-Text Transcription**: Convert audio to text using faster-whisper (offline)
- **🤖 AI Summarization**: Generate meeting notes, action items, and summaries using Ollama
- **🔒 100% Private**: All processing happens locally on your machine
- **⚡ GPU Acceleration**: Support for AMD ROCm and NVIDIA CUDA
- **📊 Multiple Output Formats**: TXT, JSON, SRT, VTT for transcripts; Markdown, JSON for summaries
- **🎯 Flexible Model Selection**: Choose Whisper model size and Ollama model based on your needs
- **🔄 Complete Workflow**: Single command to record, transcribe, and summarize meetings

### Use Cases

- **Meeting Notes**: Record meetings and automatically generate summaries with action items
- **Interview Transcription**: Convert interviews to searchable text
- **Lecture Notes**: Transcribe educational content for study
- **Documentation**: Create written records of verbal discussions
- **Accessibility**: Generate captions and transcripts for audio content

## Privacy & Security

✅ **Zero External Services**: No API calls, no cloud uploads, no telemetry
✅ **Local Processing**: Whisper and Ollama run entirely on your hardware
✅ **No Internet Required**: Works completely offline after initial setup
✅ **Your Data Stays Yours**: Recordings never leave your machine
✅ **Open Source**: Fully auditable code

## Installation

### System Requirements

- Linux (tested on CachyOS/Arch)
- Python 3.10+
- ffmpeg
- PulseAudio or PipeWire
- Ollama (for summarization)
- 4GB+ RAM (8GB+ recommended for larger models)
- Optional: GPU with ROCm or CUDA for acceleration

### Quick Install

```bash
# Clone the repository
git clone https://github.com/peteonrails/hushnote.git
cd hushnote

# Install system dependencies (Arch/CachyOS)
yay -S ffmpeg pulseaudio-utils python

# Or for PipeWire
yay -S ffmpeg pipewire-pulse python

# Create Python virtual environment
python -m venv venv

# Install Python dependencies
./venv/bin/pip install -r requirements.txt

# Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b  # or any other model

# Make scripts executable (already done in repo)
chmod +x hushnote record_audio.sh transcribe.py summarize.py

# Test installation
./hushnote --help
```

## Quick Start

### Record, Transcribe, and Summarize a Meeting

```bash
# Complete workflow (stop with Ctrl+C when done)
./hushnote full

# Or with a fixed duration (1 hour)
./hushnote full -d 3600
```

### Record Only

```bash
# Record until Ctrl+C
./hushnote record

# Record for 30 minutes
./hushnote record -d 1800
```

### Transcribe Existing Audio

```bash
# Basic transcription
./hushnote transcribe recording.wav

# With specific model and format
./hushnote transcribe recording.wav -m small -f srt
```

### Summarize Existing Transcription

```bash
# Generate meeting summary
./hushnote summarize transcript.txt

# Use specific Ollama model
./hushnote summarize transcript.txt -o qwen2.5:14b
```

### List Recordings

```bash
./hushnote list
```

## Usage

```
Usage: ./hushnote [COMMAND] [OPTIONS]

Commands:
    record              Start recording a meeting
    transcribe FILE     Transcribe an audio file
    summarize FILE      Summarize a transcription
    full               Complete workflow: record, transcribe, and summarize
    list               List all recordings

Options:
    -d, --duration SEC  Recording duration in seconds
    -m, --model MODEL   Whisper model size (tiny|base|small|medium|large-v3)
    -o, --ollama MODEL  Ollama model for summarization
    -f, --format FMT    Output format (txt|json|srt|vtt|md)
    -h, --help          Show help

Environment Variables:
    RECORDINGS_DIR      Directory for recordings (default: ./recordings)
    WHISPER_MODEL       Default Whisper model (default: base)
    OLLAMA_MODEL        Default Ollama model (default: llama3.1:8b)
    OLLAMA_URL          Ollama API URL (default: http://localhost:11434)
```

## Configuration

### Whisper Models

Choose based on accuracy vs. speed tradeoff:

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `tiny` | 75 MB | ~10-20x realtime | Basic | Quick drafts, testing |
| `base` | 150 MB | ~5-10x realtime | Good | **Default, balanced** |
| `small` | 500 MB | ~2-5x realtime | Better | Accurate transcription |
| `medium` | 1.5 GB | ~1-2x realtime | High | Professional use |
| `large-v3` | 3 GB | ~0.5-1x realtime | Best | Maximum accuracy |

Models download automatically on first use.

### Ollama Models

Popular models for summarization:

- `llama3.1:8b` - Balanced performance (default)
- `llama3.2:1b` - Fastest, basic summaries
- `mistral:7b` - Good quality, fast
- `qwen2.5:14b` - Better quality
- `mixtral:8x7b` - Best quality (slower)

Install models: `ollama pull model-name`

### GPU Acceleration

**AMD (ROCm):**
```bash
./venv/bin/pip install faster-whisper[gpu]
./transcribe.py audio.wav -d cuda
```

**NVIDIA (CUDA):**
```bash
./venv/bin/pip install faster-whisper[gpu]
./transcribe.py audio.wav -d cuda
```

### Audio Source Selection

```bash
# List available audio sources
pactl list sources short

# Set default microphone
pactl set-default-source SOURCE_NAME
```

## Examples

### Professional Meeting Recording

```bash
# High-quality recording with best summarization
./hushnote full -m medium -o mixtral:8x7b
```

### Quick Voice Note

```bash
# Fast transcription to clipboard
./hushnote record -d 60
./hushnote transcribe recordings/meeting_*.wav -m tiny
```

### Interview with Timestamps

```bash
# Record interview
./hushnote record -o interview.wav

# Generate subtitle file
./hushnote transcribe interview.wav -m small -f srt
```

### Batch Processing

```bash
# Transcribe multiple files
for file in recordings/*.wav; do
    ./hushnote transcribe "$file" -m base
done
```

## Output Files

HushNote organizes files predictably:

```
recordings/
├── meeting_20251005_143022.wav          # Audio recording
├── meeting_20251005_143022.txt          # Transcription (text)
├── meeting_20251005_143022.json         # Transcription (with metadata)
├── meeting_20251005_143022.srt          # Subtitles
└── meeting_20251005_143022_summary.md   # Meeting summary
```

## Sample Output

### Transcription (TXT)
```
This is a sample transcription of the meeting audio. The Whisper model
processes the audio and converts speech to text with high accuracy.
```

### Summary (Markdown)
```markdown
# Meeting Summary

## Summary
Discussion of Q4 project goals and resource allocation. Team agreed on
timeline and deliverables for the upcoming sprint.

## Key Discussion Points
- Project timeline needs acceleration
- Additional resources required for frontend development
- Database migration scheduled for next week

## Action Items
- [ ] John to hire 2 frontend developers by end of month
- [ ] Sarah to prepare migration runbook by Friday
- [ ] Team to review architecture docs before Monday standup

## Decisions Made
- Approved budget increase for contractor hiring
- Selected PostgreSQL for new database backend
- Weekly sync meetings moved to Tuesdays at 2pm
```

## Future Features

### Voice-to-Text Clipboard Integration
Real-time voice transcription to clipboard for instant pasting:

```bash
# Capture voice, transcribe, copy to clipboard
./hushnote voice-to-clipboard

# Or with hotkey binding
./hushnote voice-to-clipboard --hotkey "Super+Alt+V"
```

**Planned capabilities:**
- Press hotkey to start recording
- Speak naturally
- Release hotkey to stop
- Transcribed text automatically copied to clipboard (cliphist)
- Paste anywhere with Ctrl+V
- Ideal for: emails, documents, chat messages, code comments

### Real-Time Streaming Transcription
Live transcription that streams directly to cursor position:

```bash
# Stream transcription in real-time
./hushnote stream-to-cursor
```

**Planned capabilities:**
- Real-time speech-to-text streaming
- Text appears at cursor as you speak
- Works in any application
- Streaming API via named pipe for GUI integration
- Low-latency (~100-500ms)
- Ideal for: live note-taking, writing assistance, accessibility

### GUI Applications

**Waybar Widget:**
- Click to toggle recording
- Visual indicator when recording/processing
- Quick access to recent transcriptions
- Status display (model loaded, ready, processing)
- Settings menu for model selection

**System Tray Integration:**
- Global hotkey support
- Background service mode
- Notification on transcription complete
- Quick copy/paste options

**Standalone GUI:**
- Electron or Tauri-based desktop app
- Drag-and-drop audio file processing
- Live waveform visualization
- Edit transcriptions inline
- Export in multiple formats
- Search across all transcriptions

### Advanced Features (Roadmap)

- **Speaker Diarization**: Identify and label different speakers
- **Multi-language Support**: Auto-detect and transcribe multiple languages
- **Custom Vocabulary**: Add domain-specific terms for better accuracy
- **Noise Reduction**: Pre-process audio to improve transcription quality
- **Timestamps & Chapters**: Automatic chapter markers for long recordings
- **Integration APIs**: RESTful API for third-party integration
- **Mobile Companion**: Android/Linux mobile app for on-the-go recording
- **Live Streaming**: Transcribe Zoom/Teams meetings in real-time
- **Search & Index**: Full-text search across all transcriptions

## Performance

Typical performance on modern hardware (Ryzen 7/i7, 16GB RAM):

| Task | Model | Duration | Processing Time |
|------|-------|----------|-----------------|
| Transcription | tiny | 1 hour | ~3-6 minutes |
| Transcription | base | 1 hour | ~6-12 minutes |
| Transcription | small | 1 hour | ~12-30 minutes |
| Summarization | llama3.1:8b | 1 hour transcript | ~1-2 minutes |

With GPU acceleration, transcription is 3-5x faster.

## Troubleshooting

### "Error: faster-whisper not found"
```bash
# Make sure you're using the virtual environment
./venv/bin/pip install faster-whisper
```

### "Recording failed" or no audio captured
```bash
# Check audio sources
pactl list sources short

# Set default source
pactl set-default-source YOUR_SOURCE_NAME

# Test with direct recording
./record_audio.sh -d 5
```

### Ollama connection errors
```bash
# Check if Ollama is running
systemctl status ollama

# Or start manually
ollama serve

# Verify models are installed
ollama list
```

### Slow transcription
- Use a smaller Whisper model (`tiny` or `base`)
- Enable GPU acceleration if available
- Close other resource-intensive applications

### Python 3.13 compatibility issues
Faster-whisper works with Python 3.13. If you encounter issues with other packages, use Python 3.11 or 3.12.

## Architecture

```
┌─────────────────┐
│  Audio Input    │ (PulseAudio/PipeWire)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  record_audio   │ (ffmpeg)
│     .sh         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   .wav file     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  transcribe.py  │ (faster-whisper)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ .txt/.json/.srt │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  summarize.py   │ (Ollama)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  summary.md     │
└─────────────────┘
```

## Contributing

Contributions welcome! Areas of interest:

- GUI development (Waybar widget, system tray, desktop app)
- Real-time streaming transcription
- Speaker diarization
- Multi-language support
- Performance optimization
- Documentation improvements
- Testing on different Linux distributions

Please open an issue before starting major work.

## License

MIT License - see LICENSE file for details

## Credits

HushNote is built on top of excellent open-source projects:

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Fast Whisper implementation
- [Whisper](https://github.com/openai/whisper) - OpenAI's speech recognition model
- [Ollama](https://ollama.ai) - Local LLM runtime
- [ffmpeg](https://ffmpeg.org) - Audio processing

## Support

- **Issues**: [GitHub Issues](https://github.com/peteonrails/hushnote/issues)
- **Discussions**: [GitHub Discussions](https://github.com/peteonrails/hushnote/discussions)
- **Documentation**: [Wiki](https://github.com/peteonrails/hushnote/wiki)

---

**HushNote** - Because your words are your business. 🤫
