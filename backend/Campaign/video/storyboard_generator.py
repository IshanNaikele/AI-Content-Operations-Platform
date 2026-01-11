import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
from fastapi import HTTPException
import re
import math
# --- Import PRODUCTION Models for Type Hinting and Input ---
# Removed all Mock imports
from Campaign.video.video_bible_generator import VideoBibleOutput
from .audio_generator_elevenlabs import AudioTimestampOutput, Timestamp 
from Campaign.research_analysis import ResearchAnalysis 

# --- 1. Pydantic Models for Storyboard Output (Modified for LLM Output) ---

class SceneDraft(BaseModel):
    """
    The intermediate model for the LLM's output. The LLM only needs to provide 
    the creative content and the word indices for segmentation.
    """
    scene_id: int
    start_word_index: int     # NEW: Start index of the word array
    end_word_index: int       # NEW: End index of the word array (inclusive)
    high_level_concept: str   # e.g., "product intro beauty shot"
    visual_prompt_draft: str  # Detailed instructions for the video LLM
    continuity_note_to_next_scene: str # Critical instruction for smooth stitching

class StoryboardLLMOutput(BaseModel):
    """The root object for the LLM's raw response."""
    scene_drafts: List[SceneDraft]

class Scene(BaseModel):
    """
    The FINAL model for a single video scene. Timing and text are computed 
    and added by Python after the LLM response.
    """
    scene_id: int
    start: float              # Added by Python
    end: float                # Added by Python
    narration_text: str       # Added by Python
    high_level_concept: str
    visual_prompt_draft: str
    continuity_note_to_next_scene: str

class StoryboardOutput(BaseModel):
    """The final structured output containing all video scenes."""
    scenes: List[Scene]


# --- 2. Utility Function: Reconstruct Text and Find Time (Simplified Logic) ---

def reconstruct_and_find_time(full_text: str,timestamps: List[Timestamp], start_idx: int, end_idx: int) -> Tuple[str, float, float]:
    """
    Reconstructs the narration text for a scene and finds its precise start/end time.
    Uses the indices provided by the LLM output.
    
    Returns: (narration_text, start_time, end_time)
    """
    
    # Ensure indices are within bounds
    if not timestamps or start_idx >= len(timestamps) or end_idx < start_idx:
        return "", 0.0, 0.0

    # The slice is inclusive of the end index (end_idx + 1)
    # We take min with len(timestamps) to safely handle the final word/out-of-bounds error
    scene_timestamps = timestamps[start_idx : min(end_idx + 1, len(timestamps))]
    
    if not scene_timestamps:
        return "", 0.0, 0.0

    narration_text = " ".join([t.word for t in scene_timestamps])
    
    # Clean up common punctuation spacing issues created by TTS processing
    # This is a necessary evil if the TTS output still includes this artifact.
    original_script_words = full_text.split()
    scene_words = original_script_words[start_idx : min(end_idx + 1, len(original_script_words))]
    narration_text = " ".join(scene_words)
    
    start_time = scene_timestamps[0].start
    end_time = scene_timestamps[-1].end
    
    return narration_text, start_time, end_time


# --- 3. Modular Function: System Prompt for Gemini (The Scene Planner) ---

def get_storyboard_system_for_gemini(target_scenes: int, total_duration: float) -> str:
    """
    Returns the system prompt for generating the storyboard and visual prompts, 
    requiring the LLM to output word indices only.
    """
    return """
You are a world-class **Video Storyboard Artist and Generative Video Prompt Engineer**.
Your task is to take the full narration and the word-level timing data, then divide it 
into logical, visually distinct scenes.
The audio is exactly {total_duration:.2f} seconds long.
GOAL: Divide the provided narration into EXACTLY {target_scenes} scenes.
Your output MUST be a single JSON object that **strictly conforms** to the specified SCHEMA. 
Do not include any other text, reasoning, or markdown outside the JSON block.

---
CRITICAL INSTRUCTIONS:
1.  **Scene Segmentation:** Divide the full narration text into {target_scenes} scenes. Break scenes only at natural narrative or concept breaks (periods, major punctuation, or a shift in focus).
2.  **Max Duration Constraint  :** Each scene MUST correspond to a segment of the audio that is **4.0 seconds or less in duration**. Choose indices carefully to respect this limit.Be very strict and each clip must be 4 sec or less than it.These is a very critical condition that you have to follow .
3.  **Output Indices:** For each scene, you MUST specify the integer 'start_word_index' and 'end_word_index' that define the segment of the narration. The indices are provided in the input timing data (starting from 0).
4.  **Visual Continuity:** The most important constraint is continuity. For *every scene*, generate a 'continuity_note_to_next_scene' that explicitly tells the next generative video model how the current clip should end (e.g., matching color, specific camera movement, close-up subject) to ensure a seamless transition to the subsequent scene.
5.  **Visual Prompt Draft:** Generate a detailed 'visual_prompt_draft' for each scene. This must synthesize the Narration's Content, the Video Bible's Aesthetic, and the Constraints.
---
SCHEMA (MUST BE FOLLOWED):
{
  "scene_drafts": [
    {
      "scene_id": "integer",
      "start_word_index": "integer", 
      "end_word_index": "integer", 
      "high_level_concept": "string",
      "visual_prompt_draft": "string",
      "continuity_note_to_next_scene": "string"
    }
  ]
}
"""

# --- 4. Main Storyboard Generation Function (Corrected Logic) ---

def generate_storyboard(
    full_narration_text: str,
    timestamps_output: AudioTimestampOutput, # Used real production type
    video_bible_output: VideoBibleOutput,    # Used real production type
    analysis_brief: ResearchAnalysis,        # Used real production type
    gemini_client: genai.Client,
) -> StoryboardOutput:
    """
    Generates a detailed, continuity-aware storyboard using Gemini and post-processes 
    it in Python to insert accurate timing data.
    """
    
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized.")
    
    total_duration = timestamps_output.timestamps[-1].end
    if total_duration <= 30:
        dynamic_max_tokens = 8192
    elif total_duration <= 60:
        dynamic_max_tokens = 8192
    elif total_duration <= 120:
        dynamic_max_tokens = 65536 
    else:
         
        dynamic_max_tokens = 65536 

    print(f"🎬 Video Duration: {total_duration:.2f}s | Setting Max Tokens to: {dynamic_max_tokens}")

    target_count = max(1, math.ceil(total_duration / 3.5))
    llm_system_prompt = get_storyboard_system_for_gemini(target_count, total_duration)
    # A. Calculate Target Scene Count (Standard is ~3.5s per scene)
     
    # 2. Construct the full prompt payload for Gemini
    timestamp_data_list = "\n".join(
        f"{i} : {t.word} : {t.start} : {t.end}" 
        for i, t in enumerate(timestamps_output.timestamps)
    )
    print(timestamp_data_list)
    # Pass all raw data that the LLM needs to make decisions on scene breaks and visuals
    llm_user_prompt = f"""
Analyze the following data to create the continuity-focused Storyboard JSON.

FULL NARRATION TEXT: {full_narration_text}
    
--- TIMING DATA (Word Index : Word : Start Time : End Time) ---
{timestamp_data_list}
    
--- GLOBAL VIDEO AESTHETICS (for style/mood of visuals) ---
{video_bible_output.model_dump_json(indent=2)}
    
--- CONTENT GUIDELINES (for scene focus/value) ---
{analysis_brief.model_dump_json(indent=2)}
"""
    print(llm_user_prompt)
    total_duration = timestamps_output.timestamps[-1].end
 
    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[llm_system_prompt, llm_user_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", 
                temperature=0.4,
                max_output_tokens=dynamic_max_tokens
            )
        )
        
        raw_json_text = response.text.strip()
        llm_draft_output = StoryboardLLMOutput.model_validate_json(raw_json_text)
        
        # 4. POST-PROCESSING: Calculate precise timing and narration in Python
        final_scenes: List[Scene] = []
        
        for draft in llm_draft_output.scene_drafts:
            # Python calculates the precise timing using the LLM's provided indices
            narration, start_time, end_time = reconstruct_and_find_time(
                full_text=full_narration_text,
                timestamps=timestamps_output.timestamps, 
                start_idx=draft.start_word_index, 
                end_idx=draft.end_word_index
            )
            duration = end_time - start_time
            # if duration <= 0.05: 
            #     raise ValueError(
            #         f"Scene {draft.scene_id} segmentation failure: Calculated duration is {duration:.2f}s. "
            #         "The LLM failed to choose distinct start/end indices."
            #     )
            
            # if duration > 8.0: 
            #     raise ValueError(
            #         f"Scene {draft.scene_id} segmentation failure: Duration ({duration:.2f}s) exceeds the 5.0 second maximum clip length."
            #     )
            
            # Create the final, timed Scene object
            final_scene = Scene(
                scene_id=draft.scene_id,
                start=start_time,
                end=end_time,
                narration_text=narration,
                high_level_concept=draft.high_level_concept,
                visual_prompt_draft=draft.visual_prompt_draft,
                continuity_note_to_next_scene=draft.continuity_note_to_next_scene
            )
            final_scenes.append(final_scene)
            
        return StoryboardOutput(scenes=final_scenes)
        
    except ValidationError as e:
        # Handle Pydantic validation error of the LLM's *draft* output
        raise ValueError(f"LLM output validation failed in storyboard creation: {e}. Raw output: {raw_json_text if 'raw_json_text' in locals() else 'N/A'}")
    except Exception as e:
        raise ValueError(f"Gemini API or JSON generation failed during Storyboard creation: {e}. Raw output: {raw_json_text if 'raw_json_text' in locals() else 'N/A'}")