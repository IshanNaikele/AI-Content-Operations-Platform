# blog_prompt_generator.py (UPDATED)

import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator
from google import genai
from google.genai import types
from fastapi import HTTPException 

# Import the strategic brief model and initial strategy model
from Campaign.research_analysis import ResearchAnalysis 
from  llm_intent_classifier import ContentStrategy 

# --- Pydantic Model for Blog Output (NEW FIELD ADDED) ---

class BlogPromptOutput(BaseModel):
    """The structured output for the final blog generation prompt."""
    title: str
    target_audience: str
    tone: str
    word_count: int
    primary_keyword: str
    final_prompt: str
    visual_image_prompt: str # <--- NEW FIELD ADDED

# --- Modular Function: System Prompt for Gemini (UPDATED) ---

def get_blog_prompt_system_for_gemini() -> str:
    """Returns the system prompt for refining a strategy into a content generation prompt (optimized for Gemini)."""
    return """
You are a world-class **Content Strategist and Prompt Engineer**. Your task is to analyze the provided 
Strategic Brief and generate a concise, detailed JSON object for a separate LLM (the 'Writer') to produce 
a high-quality, SEO-friendly blog post and a single image generation prompt.

Your output MUST be a single JSON object that **strictly conforms** to the specified SCHEMA. Do not include any other text, reasoning, or markdown outside the JSON block.

---
INSTRUCTIONS:
1.  **Select Topic & Keywords:** Choose the *most compelling* topic idea from the input brief's 'blog_topic_ideas'. Use the first word of the topic, or the most important two words, as the 'primary_keyword'.
2.  **Define Audience & Tone:** Align the tone and style (e.g., authoritative, educational, aspirational) with the 'target_persona_summary' and 'primary_content_pillar'.
3.  **Generate Final Prompt:** Construct a single, powerful 'final_prompt' that contains ALL necessary instructions for the Writer LLM: word count, topic, brand's core value, CTA, and mandatory keyword integration.
4.  **Word Count:** Determine the word count based on the original user topic. If no number is explicitly mentioned, set the 'word_count' to 500 for a standard campaign blog.
5.  **Visual Image Prompt (NEW):** Create a single, highly detailed, photorealistic prompt (optimized for image models) that combines the 'packaging_or_physical_focus', the 'recommended_palette_names' (colors), and the 'mood_and_style' from the VISUAL BRIEF section. The image should feature the product in its recommended setting.
---
SCHEMA (NEW FIELD INCLUDED):
{
    "title": "string",
    "target_audience": "string",
    "tone": "string",
    "word_count": "integer", 
    "primary_keyword": "string", 
    "final_prompt": "string", 
    "visual_image_prompt": "string" 
}
"""

def generate_blog_prompt(analysis_brief: ResearchAnalysis, initial_strategy: ContentStrategy, gemini_client: genai.Client, original_topic: str = "") -> BlogPromptOutput:
    """
    Takes the strategic brief and generates a refined prompt for the blog writing LLM using the Gemini API.
    """
    
    if not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini Client is not initialized for blog prompt generation.")

    initial_keywords = initial_strategy.keywords 
    llm_system_prompt = get_blog_prompt_system_for_gemini()
    
    # 2. Construct the full prompt payload for Gemini
    # Pass all data for analysis, including the original topic for word count extraction.
    llm_user_prompt = f"""
    Analyze the following data to create the required JSON output:
    
    ORIGINAL USER TOPIC: {original_topic}
    STRATEGIC BRIEF: {analysis_brief.model_dump_json()}
    INITIAL KEYWORDS: {json.dumps(initial_keywords)}
"""
    
    # 3. Call the Gemini API
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash', # Use a fast model for this synthesis step
            contents=[llm_system_prompt, llm_user_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3)
        )
        
        raw_json_text = response.text.strip()
        
        output_data = json.loads(raw_json_text)
        
        return BlogPromptOutput(**output_data)
        
    except Exception as e:
        # Catch Gemini API errors, JSON parsing errors, etc.
        raise ValueError(f"Gemini API or JSON generation failed during prompt creation: {e}. Raw output: {raw_json_text if 'raw_json_text' in locals() else 'N/A'}")