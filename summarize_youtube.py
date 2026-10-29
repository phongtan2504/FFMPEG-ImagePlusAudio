#!/usr/bin/env python3
"""
Summarize a YouTube video's transcript locally using Ollama.

Requirements:
    pip install youtube-transcript-api ollama
    Ollama running locally with a model pulled, e.g.: ollama pull llama3.1

Usage:
    python summarize_youtube.py https://www.youtube.com/watch?v=VIDEO_ID --model llama3.1
    python summarize_youtube.py VIDEO_ID
"""

import argparse
import re
import sys
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
)
import ollama

# youtube-transcript-api >=1.0 uses an instance-based API instead of static methods
ytt_api = YouTubeTranscriptApi()


def extract_video_id(url_or_id: str) -> str:
    if re.fullmatch(r"[\w-]{11}", url_or_id):
        return url_or_id
    match = re.search(r"(?:v=|youtu\.be/|embed/)([\w-]{11})", url_or_id)
    if match:
        return match.group(1)
    sys.exit(f"Could not extract a video ID from: {url_or_id}")


def fetch_transcript(video_id: str, lang: str = "en") -> str:
    print(f"Fetching transcript for video {video_id} ...")
    try:
        fetched = ytt_api.fetch(video_id, languages=[lang])
    except NoTranscriptFound:
        # fall back to whatever's available (e.g. auto-generated in another language)
        print(f"No '{lang}' transcript found, trying any available language...")
        transcript_list = ytt_api.list(video_id)
        transcript = next(iter(transcript_list))
        fetched = transcript.fetch()
    except TranscriptsDisabled:
        sys.exit("Transcripts are disabled for this video.")

    lines = [f"[{seg.start:8.1f}s] {seg.text.strip()}" for seg in fetched]
    return "\n".join(lines)


def chunk_text(text: str, max_chars: int = 12000):
    lines = text.split("\n")
    chunks, current = [], []
    size = 0
    for line in lines:
        if size + len(line) > max_chars and current:
            chunks.append("\n".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


def ollama_summarize(text: str, model: str, instruction: str) -> str:
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": f"{instruction}\n\n{text}"}],
    )
    return resp["message"]["content"]


def summarize_transcript(transcript: str, model: str) -> str:
    chunks = chunk_text(transcript)
    print(f"Transcript split into {len(chunks)} chunk(s) for summarization")

    if len(chunks) == 1:
        return ollama_summarize(
            chunks[0], model,
            "Summarize this meeting transcript. Include key decisions, "
            "action items (with owners if mentioned), and open questions."
        )

    partial_summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"Summarizing chunk {i}/{len(chunks)}...")
        partial_summaries.append(
            ollama_summarize(
                chunk, model,
                "Summarize this portion of a meeting transcript concisely, "
                "noting key points, decisions, and action items."
            )
        )

    combined = "\n\n".join(
        f"--- Part {i+1} ---\n{s}" for i, s in enumerate(partial_summaries)
    )
    print("Combining chunk summaries into final summary...")
    return ollama_summarize(
        combined, model,
        "These are summaries of consecutive parts of one meeting. Combine them "
        "into a single coherent summary with: overview, key decisions, action "
        "items (with owners if mentioned), and open questions."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="YouTube URL or video ID")
    parser.add_argument("--model", default="llama3.1", help="Ollama model name")
    parser.add_argument("--lang", default="en", help="Preferred transcript language")
    parser.add_argument("--keep-transcript", action="store_true",
                         help="Save full transcript to a .txt file")
    args = parser.parse_args()

    video_id = extract_video_id(args.video)
    transcript = fetch_transcript(video_id, args.lang)

    if args.keep_transcript:
        transcript_path = Path(f"{video_id}.transcript.txt")
        transcript_path.write_text(transcript)
        print(f"Transcript saved to {transcript_path}")

    summary = summarize_transcript(transcript, args.model)

    summary_path = Path(f"{video_id}.summary.md")
    summary_path.write_text(summary)
    print(f"\nSummary saved to {summary_path}\n")
    print(summary)


if __name__ == "__main__":
    main()