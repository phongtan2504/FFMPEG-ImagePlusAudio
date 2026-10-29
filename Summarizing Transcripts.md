# Summarizing Transcripts

There are two scripts that attempt to summarize the transcript of a meeting:

- `summarize_youtube.py` that takes a Youtube video_ID and then retrieves the automatically-generated transcribes, then feeds that file to Ollama 3.1 for a summary.

  It also preserves the YT transcript that can be processed by Claude (this seems to work well.)

- `summarize_meeting.py` that takes a local video recording, extracts the audio into a _.wav_ file, then uses `whisper-fast` to transcribe, then create the summary, again with Ollama 3.1.

  This seems to work, but the initial summary is far less detailed than the Claud summary from above.
  
The script files contain info about the packages that are required, and the command line options.

In a one-out-of-one test the YT transcript plus Claude summary is a better value.
