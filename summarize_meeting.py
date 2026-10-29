#!/usr/bin/env python3
"""
Summarize a long meeting video/audio file locally using faster-whisper + Ollama.

Requirements:
    pip install faster-whisper ollama
    ffmpeg installed and on PATH
    Ollama running locally with a model pulled, e.g.: ollama pull llama3.1

Usage:
    python summarize_meeting.py meeting.mp4 --model llama3.1
"""

import argparse
import subprocess
import sys
from pathlib import Path

from faster_whisper import WhisperModel
import ollama


def extract_audio(video_path: Path, audio_path: Path):
    print(f"Extracting audio -> {audio_path}")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
            str(audio_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def transcribe(audio_path: Path, whisper_size: str = "medium") -> str:
    print(f"Transcribing with whisper ({whisper_size}) ... this can take a while")
    model = WhisperModel(whisper_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), beam_size=5)
    print(f"Detected language: {info.language}")

    lines = []
    for seg in segments:
        ts = f"[{seg.start:8.1f}s]"
        lines.append(f"{ts} {seg.text.strip()}")
        print(f"\r  ...{seg.end:.0f}s transcribed", end="", flush=True)
    print()
    return "\n".join(lines)


def chunk_text(text: str, max_chars: int = 12000):
    """Split transcript into chunks roughly max_chars long, on line boundaries."""
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

    # Map step: summarize each chunk
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

    # Reduce step: combine partial summaries
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
    parser.add_argument("video", type=Path, help="Path to video/audio file")
    parser.add_argument("--model", default="llama3.1", help="Ollama model name")
    parser.add_argument("--whisper-size", default="medium",
                         choices=["tiny", "base", "small", "medium", "large-v3"],
                         help="Whisper model size (bigger = more accurate, slower)")
    parser.add_argument("--keep-transcript", action="store_true",
                         help="Save full transcript to a .txt file")
    args = parser.parse_args()

    if not args.video.exists():
        sys.exit(f"File not found: {args.video}")

    audio_path = args.video.with_suffix(".wav")
    extract_audio(args.video, audio_path)

    transcript = transcribe(audio_path, args.whisper_size)

    if args.keep_transcript:
        transcript_path = args.video.with_suffix(".transcript.txt")
        transcript_path.write_text(transcript)
        print(f"Transcript saved to {transcript_path}")

    summary = summarize_transcript(transcript, args.model)

    summary_path = args.video.with_suffix(".summary.md")
    summary_path.write_text(summary)
    print(f"\nSummary saved to {summary_path}\n")
    print(summary)

    audio_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()