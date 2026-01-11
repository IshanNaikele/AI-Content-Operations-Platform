import json
from typing import List, Dict, Any , Tuple
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
from fastapi import HTTPException
import re

# --- Import your existing models for type hinting ---
# NOTE: In a real system, you would import these:
from Campaign.research_analysis import ResearchAnalysis 
from .video_bible_generator import  VideoBibleOutput 

# --- 1. Pydantic Model for Script Output ---

class ScriptOutput(BaseModel):
    """The final structured output for the video script."""
    video_title: str
    full_narration: str
    target_word_count: int
    estimated_duration_s: int


# --- 2. Modular Function: Word Count Calculation ---

def calculate_target_word_count_from_seconds(total_seconds: int) -> int:
    """
    Calculates the required word count based on a 150 WPM rate (2.5 WPS).
    """
    # Standard speaking rate: 2.5 Words Per Second (WPS)
    WPS = 2.5
    return int(total_seconds * WPS)

# --- 3. Modular Function: System Prompt for Gemini ---

def get_script_system_for_gemini(word_count: int) -> str:
    """Returns the system prompt for generating the full video narration script."""
    return f"""
You are a world-class **Scriptwriter and Copywriter** specializing in short, compelling video advertisements and brand content.
Your task is to analyze the provided Strategic Brief and Video Bible to create a single, cohesive, and powerful narration script.

Your output MUST be a single JSON object that **strictly conforms** to the specified SCHEMA. Do not include any other text, reasoning, or markdown outside the JSON block.

---
INSTRUCTIONS:
1.  **Word Count is CRITICAL:** The generated 'full_narration' must have a word count that is **extremely close to {word_count} words (max +/- 5 words tolerance)** to ensure it fits the required video duration at a conversational 150 WPM pace.
2.  **Sentence Length  :** The script must consist of short, punchy sentences, **not exceeding 10-15 words per sentence**, to ensure that each resulting audio clip can be segmented into a maximum duration of 5.0 seconds. Avoid run-on sentences or lengthy descriptions.
3.  **Aesthetic Integration:** The tone, vocabulary, and rhythm of the script must strongly align with the 'mood', 'visual_style', and 'camera_style' defined in the VIDEO BIBLE. (e.g., if mood is 'premium' and 'calm', the language should be elegant and flowing, not frenetic).
4.  **Content Focus:** The script must use the 'video_content_concept' as its core idea and naturally lead to the 'primary_call_to_action' from the STRATEGIC BRIEF.
5.  **Formatting:** The 'full_narration' should be plain text (no line breaks, no scene cues, no markdown formatting like bolding or italics), ready to be fed directly into a Text-to-Speech engine.
---
SCHEMA:
{{
  "video_title": "string",
  "full_narration": "string",
  "target_word_count": "integer",
  "estimated_duration_s": "integer"
}}
"""

# --- 4. Main Generation Function ---

def generate_video_script(
    video_bible_output: VideoBibleOutput , # Use VideoBibleOutput in your production code
    analysis_brief: ResearchAnalysis , # Use ResearchAnalysis in your production code
    duration_seconds: int,
    gemini_client: genai.Client,
    original_topic: str = ""
) -> ScriptOutput:
    """
    Generates the full narration script, controlling for word count based on duration.
    """
    
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized.")

    # Calculate target word count based on input duration (simplified logic)
    target_wc = calculate_target_word_count_from_seconds(duration_seconds)
    total_s = duration_seconds
    
    llm_system_prompt = get_script_system_for_gemini(target_wc)
    
    # 2. Construct the full prompt payload for Gemini
    llm_user_prompt = f"""
    Generate the full narration script. Adhere strictly to the word count constraint of {target_wc} words.

    ORIGINAL USER TOPIC: {original_topic}
    VIDEO DURATION REQUESTED: {total_s} seconds
    
    --- STRATEGIC CONTENT (for content/CTA) ---
    {analysis_brief.model_dump_json(indent=2)}
    
    --- GLOBAL VIDEO AESTHETICS (for tone/style) ---
    {video_bible_output.model_dump_json(indent=2)}
"""
    
    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=[llm_system_prompt, llm_user_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                temperature=0.7 # Higher temperature for creative scriptwriting
            )
        )
        
        raw_json_text = response.text.strip()
        output_data = json.loads(raw_json_text)
        
        # Add the target and duration to the final Pydantic model for verification/tracking
        output_data['target_word_count'] = target_wc
        output_data['estimated_duration_s'] = total_s
        
        return ScriptOutput(**output_data)
        
    except Exception as e:
        raise ValueError(f"Gemini API or JSON generation failed during script creation: {e}. Raw output: {raw_json_text if 'raw_json_text' in locals() else 'N/A'}")