"""
Subtitle Generation Service
Converts word-level timestamps into semantic SRT subtitle blocks.
Includes path sanitation for FFmpeg compatibility.
"""
import os
from pathlib import Path
from typing import List
from pydantic import BaseModel

# --- 1. Absolute Imports for Models ---
# Matches the Timestamp model used in audio_generator_elevenlabs.py
from Campaign.video.audio_generator_elevenlabs import Timestamp

# =============================================================================
# SRT FORMATTING LOGIC
# =============================================================================

def format_to_srt_time(seconds: float) -> str:
    """Converts seconds (float) to SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# =============================================================================
# CORE GENERATION LOGIC
# =============================================================================

def generate_srt(
    timestamps: List[Timestamp], 
    output_path: Path, 
    max_words: int = 8
) -> str:
    """
    Groups timestamps into semantic chunks and writes an SRT file.
    Saves to a campaign-specific directory to avoid parallel collisions.
    
    Args:
        timestamps: List of Timestamp objects.
        output_path: Absolute Path to save the captions.srt.
        max_words: Max words per subtitle line (smaller is better for Shorts).
    """
    srt_content = []
    current_chunk = []
    chunk_index = 1

    for i, ts in enumerate(timestamps):
        current_chunk.append(ts)
        
        # Semantic Break Detection:
        # 1. Word limit reached
        # 2. Punctuation signifies end of thought
        # 3. End of list
        has_punctuation = any(char in ts.word for char in [".", "!", "?", ";"])
        
        if len(current_chunk) >= max_words or has_punctuation or i == len(timestamps) - 1:
            start_time = format_to_srt_time(current_chunk[0].start)
            end_time = format_to_srt_time(current_chunk[-1].end)
            
            # Join words
            text = " ".join([w.word for w in current_chunk])
            
            # Create SRT block
            block = f"{chunk_index}\n{start_time} --> {end_time}\n{text}\n\n"
            srt_content.append(block)
            
            # Reset for next block
            current_chunk = []
            chunk_index += 1

    # Ensure the parent campaign directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(srt_content)
    
    print(f"✅ SRT Subtitles generated: {output_path}")
    return str(output_path.absolute())

# =============================================================================
# FFMPEG PATH SANITIZER
# =============================================================================

def get_ffmpeg_compatible_path(path: str) -> str:
    """
    Sanitizes absolute paths for FFmpeg's 'subtitles' filter.
    Handles Windows drive letters, backslashes, and SPACES.
    """
    import platform
    
    # Convert backslashes to forward slashes
    path = path.replace("\\", "/")
    
    # Handle Windows drive letter (C:, D:, etc.)
    if platform.system() == "Windows" and len(path) > 1 and path[1] == ":":
        # Escape ONLY the drive colon
        path = path[0] + "\\:" + path[2:]
    
    # Escape spaces for FFmpeg filter syntax
    path = path.replace(" ", "\\ ")
    
    return path