# Anki Swedish TTS Generator

Automatically generates Swedish audio for Anki flashcards using OpenAI's TTS API.

## Prerequisites

- Anki running with AnkiConnect add-on installed
- OpenAI API key
- Python 3 with dependencies:

```bash
pip install requests openai tqdm
```

## Configuration

Edit constants in `swedish_tts_script.py`:

- `OPENAI_API_KEY`: Your OpenAI API key
- `DECK_NAME`: Target Anki deck name
- `ANKI_MEDIA_PATH`: Path to Anki's media directory

## Usage

```bash
# Process all cards
python3 swedish_tts_script.py

# Test mode (first 3 cards only)
python3 swedish_tts_script.py --test
```