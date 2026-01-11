# research_analysis.py

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

# --- 1. Pydantic Models for Synthesis Output ---

class BrandStrategy(BaseModel):
    """Core strategic components derived from research."""
    product_name_suggestion: str
    core_value_proposition: str
    target_persona_summary: str

class ContentGuidelines(BaseModel):
    """Actionable direction for written and video content."""
    primary_content_pillar: str
    blog_topic_ideas: List[str]
    video_content_concept: str
    primary_call_to_action: str 
     

class VisualBrief(BaseModel):
    """Specific instructions for designers and image generation LLMs."""
    recommended_palette_names: List[str]
    mood_and_style: str
    visual_concept_notes: str
    packaging_or_physical_focus: str

class ResearchAnalysis(BaseModel):
    """The final, synthesized strategic brief model."""
    brand_strategy: BrandStrategy
    content_guidelines: ContentGuidelines
    visual_brief: VisualBrief

# --- 2. System Prompt Definition (JSON Structure Included) ---

def get_analysis_system_prompt(topic: str) -> str:
    """
    Returns the general system prompt for synthesizing raw research into a strategy brief.
    The prompt is customized with the user's topic to maintain focus.
    """
    return f"""
You are a world-class *Brand Strategist* and *Market Analyst* specializing in launching new products and campaigns. 
Your task is to analyze raw market research data (Tavily snippets) related to the user's goal: "{topic}".

*Synthesize all the raw snippets into a highly focused, actionable strategic brief.*
Your output MUST be a single JSON object that *strictly conforms* to the specified SCHEMA.
Do not include any raw links or snippets in your final output.

---
*SCHEMA (MUST BE FOLLOWED)*
{{
  "brand_strategy": {{
    "product_name_suggestion": "string",
    "core_value_proposition": "string", 
    "target_persona_summary": "string",
    "price_positioning": "string or null" 
  }},
  "content_guidelines": {{
    "primary_content_pillar": "string",
    "blog_topic_ideas": [
      "string",
      "string",
      "string"
    ],
    "video_content_concept": "string",
    "primary_call_to_action": "string",
  }},
  "visual_brief": {{
    "recommended_palette_names": [
      "string",
      "string",
      "string"
    ],
    "mood_and_style": "string",
    "visual_concept_notes": "string",
    "packaging_or_physical_focus": "string" 
  }}
}}
---

*STRATEGIC INSTRUCTIONS:*
1.  *Focus:* Base all synthesis directly on the user's topic ("{topic}") and the provided research snippets.
2.  *Target Persona:* Clearly define the primary customer (demographics, values, habits) found in the research.
3.  *Core Value:* Identify the unique selling proposition (USP) that differentiates the user's product/campaign from competitors.
4.  *Price Positioning (CONDITIONAL):* Fill the price_positioning field ONLY if the raw research explicitly mentions price, cost, premium status, budget focus, or affordability. If the information is not present or cannot be inferred with confidence, use the JSON value *null* for this field.
5.  *Visuals:* Infer the necessary aesthetic, color palette, and physical attributes (e.g., packaging, product shape) based on the findings.
6.  *Product Name:*  It should be Unique and relevent to the user topic .If user has provided the brand then use that one otherwise get it through the research and make it unique,impressive & attention seeking.
"""

# --- 3. Main Analysis Function ---

def perform_research_analysis(topic: str, raw_research_results: List[Dict[str, Any]], gemini_client: genai.Client) -> ResearchAnalysis:
    """
    Passes the user's topic and raw research snippets to Gemini for strategic synthesis.
    
    Args:
        topic: The user's original goal (e.g., "Launch a sustainable coffee brand").
        raw_research_results: List of Tavily search results (queries and snippets).
        gemini_client: Initialized Gemini client.

    Returns:
        A ResearchAnalysis Pydantic model instance.
    """
    
    analysis_system_prompt = get_analysis_system_prompt(topic)
    
    # Format the raw research for the LLM input
    formatted_research = "--- RAW RESEARCH DATA ---\n"
    for item in raw_research_results:
        formatted_research += f"QUERY: {item.get('query', 'N/A')}\n"
        for result in item.get('results', []):
            snippet = result.get('content_snippet', 'No snippet')
            formatted_research += f"SNIPPET: {snippet[:500]}...\n"
        formatted_research += "---------------------------\n"
        
    user_prompt = f"Product Launch Goal: {topic}\n\n{formatted_research}"

    print("\n--- Sending Raw Data to Gemini for Analysis ---")

    response = gemini_client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[analysis_system_prompt, user_prompt],
        
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.5)
    )
    
    print("\n--- LLM Synthesis JSON Response (Raw) ---")
    print(response.text)
    print("-----------------------------------------\n")

    try:
        analysis_data = json.loads(response.text)
        return ResearchAnalysis(**analysis_data)
    except ValidationError as e:
        # Pydantic validation error (schema mismatch)
        raise e
    except Exception as e:
        # General decoding or parsing error
        raise ValueError(f"Analysis LLM returned invalid JSON or structure: {e}. Raw output: {response.text}")