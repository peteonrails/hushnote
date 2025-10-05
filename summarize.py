#!/home/pete/workspace/transcription/venv/bin/python3

"""
Meeting summarization script using Ollama
Takes transcription text and generates meeting notes, summaries, and action items
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not installed", file=sys.stderr)
    print("Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


DEFAULT_OLLAMA_URL = "http://localhost:11434"

SUMMARY_PROMPT = """You are an AI assistant that creates concise meeting summaries. Analyze the following meeting transcription and provide:

1. **Meeting Summary**: A brief 2-3 sentence overview of the meeting
2. **Key Discussion Points**: Bullet points of main topics discussed
3. **Action Items**: Specific tasks or follow-ups identified (if any)
4. **Decisions Made**: Key decisions or conclusions reached (if any)
5. **Participants**: List any identifiable participants or speakers (if mentioned)

Transcription:
{transcription}

Please format your response in markdown."""

ACTION_ITEMS_PROMPT = """Extract all action items and tasks from this meeting transcription. For each action item, identify:
- The task/action
- Who is responsible (if mentioned)
- Any deadlines or timeframes (if mentioned)

Transcription:
{transcription}

Format as a markdown checklist with details."""


def query_ollama(prompt: str, model: str = "llama3.1:8b", ollama_url: str = DEFAULT_OLLAMA_URL) -> str:
    """
    Query Ollama API for text generation

    Args:
        prompt: The prompt to send
        model: Model name to use
        ollama_url: Ollama API URL

    Returns:
        Generated text response
    """
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=300  # 5 minute timeout
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"Error querying Ollama: {e}", file=sys.stderr)
        sys.exit(1)


def load_transcription(file_path: str) -> str:
    """Load transcription from file (supports .txt, .json)"""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: Transcription file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if path.suffix == ".json":
        data = json.loads(path.read_text())
        return data.get("text", "")
    else:
        return path.read_text()


def summarize_meeting(
    transcription: str,
    model: str,
    ollama_url: str,
    include_action_items: bool = True
) -> dict:
    """
    Generate meeting summary and action items

    Args:
        transcription: Meeting transcription text
        model: Ollama model name
        ollama_url: Ollama API URL
        include_action_items: Whether to extract action items separately

    Returns:
        dict with summary and action items
    """
    print(f"Generating meeting summary using {model}...", file=sys.stderr)

    # Generate main summary
    summary = query_ollama(
        SUMMARY_PROMPT.format(transcription=transcription),
        model=model,
        ollama_url=ollama_url
    )

    result = {"summary": summary}

    # Extract action items if requested
    if include_action_items:
        print("Extracting action items...", file=sys.stderr)
        action_items = query_ollama(
            ACTION_ITEMS_PROMPT.format(transcription=transcription),
            model=model,
            ollama_url=ollama_url
        )
        result["action_items"] = action_items

    return result


def save_summary(result: dict, output_file: str, format: str):
    """Save summary in specified format"""
    output_path = Path(output_file)

    if format == "txt" or format == "md":
        lines = ["# Meeting Summary\n"]
        lines.append(result["summary"])

        if "action_items" in result:
            lines.append("\n\n# Action Items\n")
            lines.append(result["action_items"])

        output_path.write_text("\n".join(lines))

    elif format == "json":
        output_path.write_text(json.dumps(result, indent=2))

    print(f"Summary saved to: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Summarize meeting transcription using Ollama")
    parser.add_argument("transcription_file", help="Path to transcription file (.txt or .json)")
    parser.add_argument("-m", "--model", default="llama3.1:8b",
                       help="Ollama model to use (default: llama3.1:8b)")
    parser.add_argument("-u", "--ollama-url", default=DEFAULT_OLLAMA_URL,
                       help=f"Ollama API URL (default: {DEFAULT_OLLAMA_URL})")
    parser.add_argument("-f", "--format", default="md",
                       choices=["txt", "md", "json"],
                       help="Output format (default: md)")
    parser.add_argument("-o", "--output",
                       help="Output file (default: transcription_file_summary.md)")
    parser.add_argument("--no-action-items", action="store_true",
                       help="Skip action items extraction")

    args = parser.parse_args()

    # Load transcription
    transcription = load_transcription(args.transcription_file)

    if not transcription.strip():
        print("Error: Transcription is empty", file=sys.stderr)
        sys.exit(1)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        trans_path = Path(args.transcription_file)
        suffix = ".md" if args.format == "md" else f".{args.format}"
        output_file = trans_path.with_name(f"{trans_path.stem}_summary{suffix}")

    # Generate summary
    try:
        result = summarize_meeting(
            transcription,
            model=args.model,
            ollama_url=args.ollama_url,
            include_action_items=not args.no_action_items
        )

        # Save results
        save_summary(result, output_file, args.format)

        print("\nSummarization complete!", file=sys.stderr)

    except Exception as e:
        print(f"Error during summarization: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
