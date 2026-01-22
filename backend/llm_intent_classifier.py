# llm_intent_classifier.py

import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel,Field
from google import genai
from google.genai import types
from openai import OpenAI
# Import ResearchQueries model needed for ContentStrategy
from Campaign.campaign_tavily_search import ResearchQueries

# --- Pydantic Models (Copied from original for self-containment/clean imports) ---
class ContentStrategy(BaseModel):
    intent: str
    keywords: List[str]
    content_summary: str
    requires_research: bool
    research_queries: Optional[ResearchQueries] = None
    image_count: int = 3
    duration_seconds: int = 30
    music_search_query: str = Field(
        ..., 
        description="2-3 word search query for royalty-free music library"
    )

# --- End Pydantic Models ---


def get_strategy_system_prompt() -> str:
    """Returns the system prompt for intent classification and strategy generation."""
    return """
You are a world-class content strategist and planner. Your task is to analyze a user's topic 
and return a single JSON object that MUST strictly conform to the specified schema. 
Do not include any extra keys or text outside the JSON block. 

The JSON object must have these keys: 'intent', **'keywords', **'content_summary', 
'requires_research', and **'research_queries'. 

1. 'intent': Must be **'campaign' (for business/marketing) or 'image' (for personal visualization). 
2. 'keywords': A JSON list of 2-4 relevant strings. 
3. 'content_summary': A concise sentence summarizing the strategic goal. 
4. 'requires_research': A boolean (true/false) based on the intent. 
5. 'research_queries': 
    - IF intent is 'campaign' and 'requires_research' is true: This MUST be a JSON OBJECT containing 5 keys: 'product', 'audience', 'colors', 'competitors', and 'strategy'. Each value is a detailed search query string. 
    - IF intent is 'image' or 'requires_research' is false: This MUST be the JSON value null.
6. **'image_count'**: **Determine the number of key marketing images required (1 to 5).** Check the user's topic for an explicit number (e.g., "Generate 5 images"). If found, use that number. Otherwise, default to **3**.
7. **'duration_seconds'**: **Determine the video duration required in SECONDS (integer).** Check the user's topic (e.g., "30s", "1 min"). If found, convert it to seconds. If no duration is found, default to **60**.The minimum allowed duration is 60 seconds (1 minutes).The maximum allowed duration is 180 seconds (3 minutes).
8. 'music_search_query': **CRITICAL - This is used to search a royalty-free music library.**
   Generate a 2-3 word search query that will find suitable background music.
   
   **Music Query Guidelines:**
   - Use simple, descriptive terms that a music library would understand
   - Focus on mood/genre/style rather than specific songs or artists
   - Examples of GOOD queries:
     * "upbeat corporate" (for business content)
     * "cinematic ambient" (for dramatic content)
     * "lofi hip hop" (for relaxed content)
     * "uplifting acoustic" (for positive, natural feeling)
     * "electronic energetic" (for dynamic tech content)
     * "peaceful piano" (for calm, emotional content)
   
   - Examples of BAD queries (too specific or wrong format):
     * "happy birthday music" ❌ (too specific)
     * "Song by Artist Name" ❌ (no artist names)
     * "music for my video" ❌ (too vague)
   
   **Match the query to content mood:**
   - Corporate/Business → "upbeat corporate", "professional background"
   - Technology/Innovation → "electronic ambient", "futuristic synth"
   - Lifestyle/Wellness → "acoustic calm", "peaceful meditation"
   - Sports/Energy → "energetic rock", "intense electronic"
   - Emotional/Storytelling → "cinematic piano", "emotional strings"

Example for 'campaign' intent:
{
  "intent": "campaign",
  "keywords": ["eco-friendly bottle", "green marketing"],
  "content_summary": "Advertising eco-friendly water bottle focusing on branding and visuals.",
  "requires_research": true,
  "research_queries": {
    "product": "eco-friendly water bottle product overview benefits market positioning",
    "audience": "eco-friendly products target audience demographics interests behaviors",
    "colors": "eco-friendly product color palette brand design trends green sustainability",
    "competitors": "eco-friendly bottle competitors branding color schemes ad design",
    "strategy": "eco-friendly brand marketing strategy best performing ad concepts"
  },
  "image_count": 3,
  "duration_seconds": 60,
  "music_search_query":"uplifting acoustic"
}
"""

def classify_and_strategize(topic: str, gemini_client: OpenAI) -> ContentStrategy:
    """Calls the first LLM to determine intent and initial strategy."""
    strategy_system_prompt = get_strategy_system_prompt()
    user_topic_prompt = f"Analyze the following topic and generate the content strategy JSON: {topic}"

    # Use a validated model name (e.g., gemini-2.0-flash)
    try:
        response = gemini_client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": strategy_system_prompt},
                {"role": "user", "content": user_topic_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        print("\n--- LLM Intent Classifier JSON Response ---")
        print(response.choices[0].message.content)
        print("-------------------------------------------\n")

        llm_output_data = json.loads(response.choices[0].message.content)
        return ContentStrategy(**llm_output_data)

    except Exception as e:
        print(f"Error during Intent Classification: {e}")
        # Return a fallback strategy if LLM fails
        return ContentStrategy(
            intent="image",
            keywords=["error", "fallback"],
            content_summary="Error in classification, falling back to basic image intent.",
            requires_research=False,
            music_search_query="peaceful piano"
        )