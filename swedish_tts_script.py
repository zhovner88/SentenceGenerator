#!/usr/bin/env python3
"""
Anki Swedish TTS Automation Script
Automatically generates Swedish audio for Anki cards using OpenAI TTS API
"""

import requests
import hashlib
import argparse
import re
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm

# Configuration
ANKI_CONNECT_URL = "http://localhost:8765"
OPENAI_API_KEY = "YOUR_KEY" #Set your OpenAI API keyY
DECK_NAME = "About me"  # Set your deck name or leave as None for all decks
ANKI_MEDIA_PATH = "/Users/denyszhovnerovych/Library/Application Support/Anki2/User 1/collection.media"  # Usually ~/.local/share/Anki2/User 1/collection.media/
TEST_MODE = False  # Set to True to process only first card for testing
DEBUG_MODE = True  # Set to False for minimal output (only progress bar and counts)

# TTS Settings
TTS_MODEL = "gpt-4o-mini-tts"  # New model with better quality
TTS_VOICE = "alloy"  # Choose from: alloy, echo, fable, onyx, nova, shimmer, coral
TTS_INSTRUCTIONS = "Speak clearly and at a moderate pace. I'm learning swedish. Focus on pronunciation."  # Optional instructions for speech generation (leave empty for natural speech)
TTS_FORMAT = "mp3"  # Choose from: mp3, opus, aac, flac, wav, pcm
TTS_SPEED = 0.90  # Speed of generated audio (0.25 to 4.0, default: 1.0)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def anki_request(action, params=None):
    """Make a request to AnkiConnect"""
    payload = {
        "action": action,
        "version": 6,
        "params": params or {}
    }
    
    response = requests.post(ANKI_CONNECT_URL, json=payload)
    result = response.json()
    
    if result.get("error"):
        raise Exception(f"AnkiConnect error: {result['error']}")
    
    return result["result"]

def generate_audio_filename(text):
    """Generate a unique filename for the audio based on text content"""
    # Clean text and extract first few words
    clean_text = clean_html_tags(text).lower()
    # Remove non-alphanumeric characters and split into words
    words = re.sub(r'[^a-züöäéèêëàáâäòóôöùúûü\s]', '', clean_text).split()
    # Take first 3 words and limit each word to 10 characters
    text_part = '_'.join([word[:10] for word in words[:3]])
    # Ensure we have some text part
    if not text_part:
        text_part = "swedish"
    
    # Generate hash for uniqueness
    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    file_extension = TTS_FORMAT if TTS_FORMAT != "pcm" else "wav"  # PCM needs .wav extension
    
    return f"swedish_{text_part}_{text_hash}.{file_extension}"

def clean_html_tags(text):
    """Remove HTML tags and clean text for TTS"""
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def generate_swedish_audio(text):
    """Generate Swedish audio using OpenAI TTS API"""
    # Clean HTML tags from text
    clean_text = clean_html_tags(text)
    if DEBUG_MODE:
        print(f"Cleaned text for TTS: {clean_text}")
    
    try:
        # Use new API with separate instructions parameter
        if TTS_INSTRUCTIONS:
            response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=TTS_VOICE,
                input=clean_text,
                instructions=TTS_INSTRUCTIONS,
                response_format=TTS_FORMAT,
                speed=TTS_SPEED
            )
        else:
            response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=TTS_VOICE,
                input=clean_text,
                response_format=TTS_FORMAT,
                speed=TTS_SPEED
            )
        
        return response.content
    except Exception as e:
        print(f"Error generating audio for '{clean_text}': {e}")
        return None

def save_audio_to_anki_media(audio_content, filename):
    """Save audio file to Anki's media directory"""
    media_path = Path(ANKI_MEDIA_PATH) / filename
    
    try:
        with open(media_path, 'wb') as f:
            f.write(audio_content)
        return True
    except Exception as e:
        print(f"Error saving audio file {filename}: {e}")
        return False

def get_cards_needing_audio():
    """Get cards that have Swedish text but no audio"""
    # Build query
    query = '"Swedish sentence audio:" deck:"' + DECK_NAME + '"' if DECK_NAME else '"Swedish sentence audio:"'
    if DEBUG_MODE:
        print(f"DEBUG: Using query: {query}")
    
    note_ids = anki_request("findNotes", {"query": query})
    if DEBUG_MODE:
        print(f"DEBUG: Found {len(note_ids)} note IDs")
    
    if not note_ids:
        print("No cards found that need audio generation.")
        if DEBUG_MODE:
            # Let's try a broader search to see what's available
            print("DEBUG: Trying broader search...")
            all_deck_query = f'deck:"{DECK_NAME}"' if DECK_NAME else "*"
            all_notes = anki_request("findNotes", {"query": all_deck_query})
            print(f"DEBUG: Total cards in deck: {len(all_notes)}")
            
            if all_notes:
                # Check field names of first card
                sample_info = anki_request("notesInfo", {"notes": all_notes[:1]})
                if sample_info:
                    print("DEBUG: Available fields in first card:")
                    for field_name in sample_info[0]["fields"]:
                        print(f"  - {field_name}")
        return []
    
    print(f"Found {len(note_ids)} cards in deck '{DECK_NAME}' that might need audio processing.")
    
    notes_info = anki_request("notesInfo", {"notes": note_ids})
    
    cards_needing_audio = []
    for note in notes_info:
        try:
            swedish_text = note["fields"]["Swedish Example"]["value"].strip()
            audio_field = note["fields"]["Swedish sentence audio"]["value"].strip()
            
            # Skip if no Swedish text or audio already exists
            if not swedish_text or audio_field:
                continue
                
            cards_needing_audio.append({
                "note_id": note["noteId"],
                "swedish_text": swedish_text
            })
        except KeyError as e:
            if DEBUG_MODE:
                print(f"DEBUG: Missing field {e} in note {note['noteId']}")
                print(f"DEBUG: Available fields: {list(note['fields'].keys())}")
    
    return cards_needing_audio

def update_card_with_audio(note_id, audio_filename):
    """Update Anki card with the generated audio"""
    audio_tag = f"[sound:{audio_filename}]"
    
    anki_request("updateNoteFields", {
        "note": {
            "id": note_id,
            "fields": {
                "Swedish sentence audio": audio_tag
            }
        }
    })

def process_cards(test_mode=False):
    """Main processing function"""
    print(f"Fetching cards that need audio from deck: {DECK_NAME}...")
    cards = get_cards_needing_audio()
    
    if not cards:
        return
    
    total_cards = len(cards)
    if test_mode:
        cards = cards[:1]
        print(f"\nTEST MODE: Processing only first 1 card out of {total_cards} total cards")
    else:
        print(f"Found {total_cards} cards needing audio generation.")
    
    processed = 0
    errors = 0
    
    # Create progress bar
    progress_bar = tqdm(cards, desc="Processing cards", unit="card")
    
    for card in progress_bar:
        current_text = card['swedish_text'][:50] + "..." if len(card['swedish_text']) > 50 else card['swedish_text']
        if DEBUG_MODE:
            progress_bar.set_description(f"Processing: {current_text}")
            print(f"\nCurrently processing: {card['swedish_text']}")
        else:
            # Clean progress display for non-debug mode
            progress_bar.set_description(f"Processing card {progress_bar.n + 1}/{len(cards)}")
        
        # Generate audio
        audio_content = generate_swedish_audio(card['swedish_text'])
        if not audio_content:
            errors += 1
            if DEBUG_MODE:
                print(f"Failed to generate audio for: {card['swedish_text']}")
            continue
        
        # Generate filename and save
        filename = generate_audio_filename(card['swedish_text'])
        if not save_audio_to_anki_media(audio_content, filename):
            errors += 1
            if DEBUG_MODE:
                print(f"Failed to save audio file for: {card['swedish_text']}")
            continue
        
        # Update Anki card
        try:
            update_card_with_audio(card['note_id'], filename)
            processed += 1
            if DEBUG_MODE:
                print(f"Successfully processed: {card['swedish_text']}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error updating card: {e}")
            errors += 1
    
    print(f"\nCompleted! Processed: {processed}/{len(cards)}, Errors: {errors}")
    if test_mode:
        print(f"Total cards in library: {total_cards}")

def main():
    """Main function with error handling"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Swedish TTS for Anki cards')
    parser.add_argument('--test', action='store_true', help='Run in test mode (process only first 1 card)')
    args = parser.parse_args()
    
    try:
        # Test AnkiConnect connection
        anki_request("version")
        print("Connected to AnkiConnect")
        
        # Test OpenAI API (optional quick test)
        print("OpenAI API key configured")
        
        # Use command line flag or configuration setting
        test_mode = args.test or TEST_MODE
        
        if test_mode and DEBUG_MODE:
            print("\nRunning in TEST MODE")
        
        # Process cards
        process_cards(test_mode=test_mode)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure:")
        print("1. Anki is running with AnkiConnect add-on enabled")
        print("2. OpenAI API key is valid")
        print("3. Anki media path is correct")

if __name__ == "__main__":
    main()