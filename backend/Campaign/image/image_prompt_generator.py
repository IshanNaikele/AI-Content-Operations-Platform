# image_prompt_generator.py

import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from fastapi import HTTPException

# Import the research analysis model for input
from Campaign.research_analysis import ResearchAnalysis

# --- Pydantic Model for Image Prompt Output ---

class GeneratedImagePrompt(BaseModel):
    """A single structured output for one image generation prompt."""
    prompt_id: int
    variation_description: str
    image_prompt: str

class ImagePromptListOutput(BaseModel):
    """The structured output containing a list of image prompts."""
    image_count: int
    prompts: List[GeneratedImagePrompt]

# --- Modular Function: System Prompt for Gemini ---

def get_image_prompt_system_for_gemini() -> str:
    """
    Returns the system prompt for generating a list of image generation prompts
    based on the strategic brief and a desired image count (optimized for Gemini).
    """
    return """
You are a world-class **Visual Content Strategist and Prompt Engineer**. Your task is to analyze the
provided STRATEGIC BRIEF and the requested IMAGE COUNT to generate a list of high-quality, 
photorealistic image prompts (optimized for DALL-E/Midjourney/Stable Diffusion) for a content piece.

Your output MUST be a single JSON object that **strictly conforms** to the specified SCHEMA. Do not include
any other text, reasoning, or markdown outside the JSON block.
The image should be fascinating & visually appealing .
---
INSTRUCTIONS:
1.  **Determine Image Count:** The required number of images is passed explicitly in the user prompt (REQUIRED IMAGE COUNT: X). Use this number. The range is 1 to 5.
2.  **Core Visual Strategy:** All prompts must integrate the 'packaging_or_physical_focus', 'recommended_palette_names' (colors), and 'mood_and_style' from the VISUAL BRIEF section of the input data.
3.  **Ensure Variation:** Generate unique 'variation_description' and corresponding 'image_prompt' for each required image.
    * **Variation Strategy:** Focus on different angles (e.g., close-up, wide shot), different elements of the setting/product usage, or slight variations in mood/lighting while maintaining the core visual style.
    * **Mandatory Inclusion:** The product must be the central focus in a realistic, contextually relevant setting.
4.  **Prompt Quality:** Each 'image_prompt' must be detailed, descriptive, and photorealistic.
5.  **Vagueness:** The image should be consistent and should feel like real and not the dummy one .Ex Human with one hand missing ,with no face .
---
SCHEMA:
{
    "image_count": "integer",
    "prompts": [
        {
            "prompt_id": "integer (1 to image_count)",
            "variation_description": "string (e.g., Close-up product shot, Wide-angle lifestyle shot)",
            "image_prompt": "string (The highly detailed, photorealistic image generation prompt)"
        }
    ]
}
"""
 

def generate_image_prompts(analysis_brief: ResearchAnalysis, gemini_client: genai.Client,required_image_count: int) -> ImagePromptListOutput:
    """
    Generates a list of image prompts using the Gemini API based on the strategic brief.
    """
    
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized for image prompt generation.")
    
    # 1. Determine the image count based on the topic (enforces constraints)
    image_count: int = required_image_count
    
    llm_system_prompt: str = get_image_prompt_system_for_gemini()
    
    # 2. Construct the full prompt payload for Gemini
    llm_user_prompt: str = f"""
    Analyze the following data to create the required JSON output:
    
    **REQUIRED IMAGE COUNT:** {image_count}
    **STRATEGIC BRIEF:** {analysis_brief.model_dump_json()}
"""
    
    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash', # Use a fast model for this synthesis step
            contents=[llm_system_prompt, llm_user_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7) # Higher temperature for creative variations
        )
        
        raw_json_text: str = response.text.strip()
        
        # Validation and Parsing
        output_data: Dict[str, Any] = json.loads(raw_json_text)
        
        return ImagePromptListOutput(**output_data)
        
    except Exception as e:
        # Catch Gemini API errors, JSON parsing errors, etc.
        raise ValueError(f"Gemini API or JSON generation failed during image prompt creation: {e}. Raw output: {raw_json_text if 'raw_json_text' in locals() else 'N/A'}")