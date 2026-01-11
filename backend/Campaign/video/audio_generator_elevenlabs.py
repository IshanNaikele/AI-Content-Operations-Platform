import os
import re
import json
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Use v1beta1 to access time_pointing features
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.oauth2 import service_account
# Import Path Manager from root
from  config import DATA_ROOT
load_dotenv()

# --- 1. Pydantic Models (KEPT TO PRESERVE PIPELINE) ---

class Timestamp(BaseModel):
    word: str
    start: float
    end: float

class AudioTimestampOutput(BaseModel):
    timestamps: List[Timestamp]
    audio_file_path: Optional[str] = None

# --- 2. Credentials Logic (From your current Google Code) ---

def get_google_credentials():
    try:
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not found in .env")
        service_account_info = json.loads(service_account_json)
        return service_account.Credentials.from_service_account_info(service_account_info)
    except Exception as e:
        print(f"❌ Credentials Error: {e}")
        return None

# --- 3. Main Corrected Function ---

def generate_audio_and_timestamps(
    full_narration_text: str = None, 
    google_client: texttospeech.TextToSpeechClient = None,
    output_audio_path: Optional[str] = None,
    voice_name: str = "en-US-Neural2-F",
    # --- BACKWARD COMPATIBILITY CATCHERS ---
    text: str = None,   # Catches the old 'text' arg
    client = None,      # Catches the old 'client' arg
    **kwargs            # Catches any other stray ElevenLabs args
) -> AudioTimestampOutput:
    
    # Use whichever argument was provided
    final_text = full_narration_text or text
    
    # If the pipeline passed the ElevenLabs client by mistake, 
    # we ignore it and use our own Google client.
    final_client = google_client if google_client else get_default_google_client()

    if not final_text:
        raise ValueError("No narration text provided.")
    if not final_client:
        raise ValueError("Google TTS client not initialized. Check .env")

    # PREPARE SSML
    words = final_text.split()
    ssml_parts = ["<speak>"]
    for i, word in enumerate(words):
        ssml_parts.append(f"{word} <mark name='{i}'/>")
    ssml_parts.append("</speak>")
    ssml_string = " ".join(ssml_parts)

    try:
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_string)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3,speaking_rate=0.85)

        response = final_client.synthesize_speech(
            request=texttospeech.SynthesizeSpeechRequest(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
                enable_time_pointing=[texttospeech.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
            )
        )

        # PROCESS TIMESTAMPS
        timestamps_list = []
        last_time = 0.0
        for timepoint in response.timepoints:
            idx = int(timepoint.mark_name)
            current_time = timepoint.time_seconds
            clean_word = re.sub(r'[^\w\s]', '', words[idx])
            timestamps_list.append(Timestamp(word=clean_word, start=round(last_time, 2), end=round(current_time, 2)))
            last_time = current_time

        # 3. SAVE AUDIO (Critical: output_audio_path must be campaign-specific)
        saved_path_str = None
        if output_audio_path:
            out_path = Path(output_audio_path)
            # Create parents (e.g., media/campaign/{id}/LONG_FORM/) if they don't exist
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(out_path, "wb") as out:
                out.write(response.audio_content)
            saved_path_str = str(out_path)
            print(f"✅ Audio saved to: {saved_path_str}")

        return AudioTimestampOutput(
            timestamps=timestamps_list,
            audio_file_path=saved_path_str
        )

    except Exception as e:
        raise RuntimeError(f"Google TTS Pipeline Error: {e}")

# --- 4. Initialization Helper ---

def get_tts_client():
    creds = get_google_credentials()
    if creds:
        return texttospeech.TextToSpeechClient(credentials=creds)
    return None


def get_default_google_client():
    """Self-contained credential loader for the pipeline."""
    try:
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON missing from .env")
        
        service_account_info = json.loads(service_account_json)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        return texttospeech.TextToSpeechClient(credentials=creds)
    except Exception as e:
        print(f"❌ Google TTS Auth Error: {e}")
        return None