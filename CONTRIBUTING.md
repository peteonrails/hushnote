# Contributing to HushNote

Thank you for your interest in contributing to HushNote! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Environment details**: OS, Python version, GPU (if applicable)
- **Logs or error messages** (use DEBUG=true for detailed output)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- Use a clear and descriptive title
- Provide detailed description of the proposed feature
- Explain why this enhancement would be useful
- Include examples of how it would work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/hushnote.git
cd hushnote

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `./venv/bin/activate` on some systems

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if any)
pip install -r requirements-dev.txt  # when available

# Make scripts executable
chmod +x hushnote record_audio.sh transcribe.py summarize.py
```

## Testing

Before submitting a PR, test your changes:

```bash
# Test basic recording (2 seconds)
./hushnote record -d 2

# Test transcription
./hushnote transcribe recordings/meeting_*.wav -m tiny

# Test summarization
./hushnote summarize recordings/meeting_*.txt -o llama3.2:1b

# Test full workflow
./hushnote full -d 5 -m tiny -o llama3.2:1b

# Enable debug mode for detailed output
DEBUG=true ./hushnote full -d 5 -m tiny
```

## Code Style

### Bash Scripts
- Use `set -euo pipefail` at the top
- Use meaningful variable names (UPPER_CASE for constants, lower_case for variables)
- Comment complex logic
- Redirect log messages to stderr (`>&2`)
- Use functions for reusable code

### Python Scripts
- Follow PEP 8 style guide
- Use type hints where appropriate
- Include docstrings for functions and classes
- Handle errors gracefully
- Print status messages to stderr, data to stdout

### General
- Keep lines under 100 characters when practical
- Use consistent indentation (4 spaces for Python, 4 spaces for bash)
- Add comments for non-obvious code
- Update documentation when changing functionality

## Project Structure

```
hushnote/
├── hushnote              # Main orchestration script
├── record_audio.sh       # Audio recording script
├── transcribe.py         # Transcription script (faster-whisper)
├── summarize.py          # Summarization script (Ollama)
├── requirements.txt      # Python dependencies
├── README.md             # Main documentation
├── LICENSE               # MIT License
├── CONTRIBUTING.md       # This file
└── recordings/           # Output directory (gitignored)
```

## Feature Development Priorities

### High Priority
1. **Voice-to-clipboard** - Quick voice note → clipboard integration
2. **Real-time streaming** - Live transcription to cursor position
3. **Waybar widget** - System tray/status bar integration
4. **Speaker diarization** - Multi-speaker identification

### Medium Priority
1. GUI application (Electron/Tauri)
2. Background service mode
3. Global hotkey support
4. Noise reduction preprocessing
5. Custom vocabulary support

### Low Priority (Nice to Have)
1. Mobile companion app
2. RESTful API
3. Search/indexing across transcriptions
4. Multi-language auto-detection

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
Add voice-to-clipboard feature

- Implement hotkey capture
- Add cliphist integration
- Update documentation
- Add usage examples
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description (wrap at 72 chars)
- Reference issues: `Fixes #123` or `Closes #456`

## Documentation

When adding features:
- Update README.md with usage examples
- Add inline code comments for complex logic
- Update help text in scripts (`--help`)
- Add entries to Future Features section if applicable

## Questions?

- Open a [Discussion](https://github.com/peteonrails/hushnote/discussions)
- Check existing [Issues](https://github.com/peteonrails/hushnote/issues)
- Read the [Wiki](https://github.com/peteonrails/hushnote/wiki) (when available)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to HushNote! 🎙️
