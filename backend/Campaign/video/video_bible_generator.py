import json
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
from fastapi import HTTPException 

# --- Import your existing models for type hinting ---
# Assuming these files are in the same environment:
from Campaign.research_analysis import ResearchAnalysis 
from  llm_intent_classifier import ContentStrategy # Used for keywords

 
# --- 1. Pydantic Model for Video Bible Output ---

class ProductConstraints(BaseModel):
    """Specific rules the video must follow regarding the product."""
    color_cannot_change: bool
    logo_visible: bool
    # Add other constraints if needed (e.g., must feature specific object, aspect ratio)

class VideoBible(BaseModel):
    """The global identity and constraints for the video."""
    color_palette: List[str]
    lighting_style: str
    camera_style: str
    mood: str
    visual_style: str
    product_constraints: ProductConstraints

class VideoBibleOutput(BaseModel):
    """The root object for the final output."""
    video_bible: VideoBible


# --- 2. Modular Function: System Prompt for Gemini ---

def get_video_bible_system_for_gemini() -> str:
    """Returns the system prompt for generating the global video identity."""
    return """
You are a world-class **Video Director and Aesthetic Consultant**. Your task is to analyze the provided 
Strategic Brief and generate a concise, detailed JSON object called "video_bible" that defines 
the global aesthetic identity and constraints for a video.

Your output MUST be a single JSON object that **strictly conforms** to the specified SCHEMA. 
Do not include any other text, reasoning, or markdown outside the JSON block.

---
INSTRUCTIONS:
1.  **Aesthetic Synthesis:** Use the 'visual_brief' and 'brand_strategy' sections to determine the look and feel.
    * **Color Palette:** Use 3-5 HEX color codes that best represent the 'recommended_palette_names'. (e.g., ["#RRGGBB", ...])
    * **Mood:** Translate the 'mood_and_style' and 'target_persona_summary' into a single, strong emotional atmosphere (e.g., "Calm, Elegant, Premium").
    * **Lighting & Camera:** Infer a professional lighting and camera technique that supports the 'mood_and_style' (e.g., "soft warm diffused light," "slow cinematic pans").
2.  **Visual Style:** Provide a concise description of the overall visual execution (e.g., "pastel minimalism with gentle gradients").
3.  **Product Constraints:** Set boolean constraints based on the `packaging_or_physical_focus` and the overall brand value.
    * Assume `logo_visible` is **true** unless the brand is highly secretive.
    * Assume `color_cannot_change` is **true** if the product color is a core part of the value proposition.
---
SCHEMA (MUST BE FOLLOWED):
{
    "video_bible": {
        "color_palette": ["string"],
        "lighting_style": "string",
        "camera_style": "string",
        "mood": "string",
        "visual_style": "string",
        "product_constraints": {
            "color_cannot_change": "boolean",
            "logo_visible": "boolean"
        }
    }
}
"""

# --- 3. Main Generation Function ---

def generate_video_bible(
    analysis_brief:  ResearchAnalysis, # Use ResearchAnalysis in your production code
    initial_keywords: List[str],
    gemini_client: genai.Client,
    original_topic: str = ""
) -> VideoBibleOutput:
    """
    Generates the Video Bible (global constraints and aesthetics) using the Gemini API.
    """
    
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized.")

    llm_system_prompt = get_video_bible_system_for_gemini()
    
    # 2. Construct the full prompt payload for Gemini
    # Pass all relevant data for aesthetic analysis.
    llm_user_prompt = f"""
    Analyze the following data to create the required JSON output:
    
    ORIGINAL USER TOPIC: {original_topic}
    STRATEGIC BRIEF: {analysis_brief.model_dump_json(indent=2)}
    INITIAL KEYWORDS: {json.dumps(initial_keywords)}
"""
    
    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash', # Fast and reliable for JSON synthesis
            contents=[llm_system_prompt, llm_user_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3)
        )
        
        raw_json_text = response.text.strip()
        
        output_data = json.loads(raw_json_text)
        
        # Pydantic validation guarantees correct output schema
        return VideoBibleOutput(**output_data)
        
    except Exception as e:
        # Catch Gemini API errors, JSON parsing errors, etc.
        raise ValueError(f"Gemini API or JSON generation failed during Video Bible creation: {e}. Raw output: {raw_json_text if 'raw_json_text' in locals() else 'N/A'}")

 