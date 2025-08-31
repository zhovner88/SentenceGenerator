# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Anki Swedish TTS automation script that automatically generates Swedish audio for Anki flashcards using OpenAI's TTS API. The project consists of a single Python script that:

- Connects to Anki via AnkiConnect add-on
- Finds cards with Swedish text but no audio
- Generates Swedish pronunciation audio using OpenAI TTS
- Saves audio files to Anki's media directory
- Updates Anki cards with audio references

## Running the Script

```bash
# Normal mode - process all cards
python3 swedish_tts_script.py

# Test mode - process only first 3 cards
python3 swedish_tts_script.py --test
```

## Configuration

The script requires configuration of several constants at the top of `swedish_tts_script.py`:

- `ANKI_CONNECT_URL`: AnkiConnect endpoint (default: http://localhost:8765)
- `OPENAI_API_KEY`: OpenAI API key for TTS service
- `DECK_NAME`: Target Anki deck name (currently "Swedish Kelly A1")
- `ANKI_MEDIA_PATH`: Path to Anki's media directory

## Prerequisites

- Anki running with AnkiConnect add-on installed
- Valid OpenAI API key
- Python 3 with required libraries: `requests`, `openai`, `tqdm`, `pathlib`

Install dependencies:
```bash
pip install requests openai tqdm
```

## Architecture Notes

- Single-file script with clear separation of concerns
- Uses MD5 hash-based filename generation for audio files
- Implements error handling for API calls and file operations
- Processes cards in batch with progress reporting