# personal_image_generator.py

import os
import json
import requests
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ValidationError 
from fastapi import HTTPException 
from utils.ai_helpers import openrouter_chat_completion, generate_cloudflare_image
# --- Pydantic Models (Copied from original for self-containment/clean imports) ---
class RefinedImageDetail(BaseModel):
    """Details for a single, refined image prompt variation."""
    prompt: str
    style_keywords: List[str]
    aspect_ratio: str
    negative_prompt: str

class RefinedImageOutput(BaseModel):
    """The full output model for the image refinement LLM call."""
    count: int
    prompts: List[RefinedImageDetail]
# --- End Pydantic Models ---


def sanitize_topic_for_filename(topic: str) -> str:
    """Sanitizes and shortens a topic string for use in a filename."""
    # Convert to lowercase
    s = topic.lower()
    # Replace non-alphanumeric characters (except spaces/hyphens) with nothing
    s = re.sub(r'[^\w\s-]', '', s).strip()
    # Replace spaces and hyphens with underscores
    s = re.sub(r'[-\s]+', '_', s)
    # Truncate to a manageable length (e.g., first 20 characters) and remove trailing underscores
    return s[:20].strip('_')

# Add this new function to personal_image_generator.py

def map_ratio_to_dimensions(ratio_str: str) -> Dict[str, int]:
    """Maps common aspect ratio strings to fixed pixel dimensions."""
    ratio_map = {
        "16:9": {"width": 1024, "height": 576},     # Common landscape
        "4:3": {"width": 1024, "height": 768},      # Older landscape/monitor
        "1:1": {"width": 1024, "height": 1024},     # Square (your current default)
        "2:3": {"width": 768, "height": 1152},      # Portrait
        # Add more ratios as supported by the FLUX model if needed
    }
    
    # Clean the string for matching
    cleaned_ratio = ratio_str.strip().replace(" ", "").lower()
    
    # Return mapped dimensions or default to 1:1 if not found
    return ratio_map.get(cleaned_ratio, {"width": 1024, "height": 1024})


def generate_image_prompt(topic: str ) -> RefinedImageOutput:
    """Calls the second LLM to refine an image topic into a detailed list of prompts."""
    
    # System Prompt Logic: Instruct the LLM to handle counting and variation
    image_prompt_system = f"""
You are an expert AI image prompt engineer. Your task is to take a user's short, vague description 
and transform it into a single, highly detailed, photorealistic prompt that maximizes quality 
in modern text-to-image models (like Midjourney or Stable Diffusion).

**COUNTING RULE:**
1. Parse the user's input for a desired number of images (e.g., '2 images', '5 photos').
2. If a number is found, use that number.
3. If NO number is specified, *default to generating 3 images*.
4. The maximum number of images you can generate is 5, and the minimum is 1.

The final output MUST be a JSON object with two top-level keys: *'count'* (the number of prompts generated) and *'prompts'* (a list of distinct prompt objects).
The length of the 'prompts' list MUST exactly match the 'count' value.

Each prompt object in the list MUST adhere to the following schema:
1. 'prompt': MUST be a single, long, descriptive string incorporating subject, lighting, mood, and composition. Ensure the prompt is distinct from the others in the list (e.g., change the time of day, angle, or style modifier for each prompt).Must have the desired ratio .
2. 'style_keywords': A list of technical modifiers (e.g., 'cinematic lighting', 'octane render', '8k', 'photorealistic').
3. 'aspect_ratio': Select the best ratio (e.g., '16:9', '1:1', '2:3').
4. 'negative_prompt': A comma-separated list of common artifacts to exclude (e.g., 'bad anatomy, cropped, ugly, watermark, blurry').

User Input: "{topic}"
"""
    
    image_response = openrouter_chat_completion(
    messages=[
        {"role": "system", "content": image_prompt_system}
    ],
    temperature=0.9,
    response_format={"type": "json_object"},
    stage="image_prompt"
)

    try:
        if not image_response.choices or image_response.choices[0] is None:
            raise RuntimeError("OpenRouter returned empty choices for image prompt generation")
        
        image_prompt_data = json.loads(image_response.choices[0].message.content)
        return RefinedImageOutput(**image_prompt_data)
    except Exception as e:
        print(f"DEBUG: Failed to parse LLM output: {e}")
        
        # Safe raw output extraction — no .text on ChatCompletion
        if image_response and image_response.choices and image_response.choices[0]:
            raw_output = image_response.choices[0].message.content
        else:
            raw_output = str(image_response)
        print(f"DEBUG: Raw LLM Output: {raw_output}")
        
        raise RuntimeError(f"Failed to parse image prompt generation: {e}")


def generate_image(prompt: str, image_filename: str, image_folder: str,width: int, height: int) -> str:
    """
    Generates an image using Fireworks AI FLUX.1-schnell-fp8 model.
    Returns the URL path to the stored image.
    """
    file_path = os.path.join(image_folder, image_filename)
    
    try:
        saved_path = generate_cloudflare_image(
            prompt=prompt,
            output_path=file_path,
            width=width,
            height=height,
            key_num=1
        )
        
        # Return URL path for frontend (media is mounted at /media)
        return f"/{image_folder}/{image_filename}"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")
    
def generate_image_nano_banana(
    prompt: str, 
    image_filename: str, 
    image_folder: str, 
    width: int, 
    height: int,  
) -> str:
    """
    Generates an image using Gemini's native 'Nano Banana' (Imagen 3) model.
    Optimized for Premium users.
    """
    try:
        # Create the full path for storage
        file_path = os.path.join(image_folder, image_filename)
        
        print(f"DEBUG [Premium]: Generating Nano Banana image: {width}x{height}")

        # Call the native Gemini Image Generation model
        # Note: model name 'imagen-3' or 'gemini-3-pro-image-preview' depending on your API settings
        response = gemini_client.models.generate_content(
            model='gemini-3-pro-image-preview', 
            contents=prompt,
            config=types.GenerateContentConfig(
                # Passing dimensions to the model
                # Note: Some versions use specific 'aspect_ratio' strings instead of pixels
                candidate_count=1,
            )
        )

        # Gemini returns images as byte data within parts
        image_part = response.candidates[0].content.parts[0]
        
        if image_part.inline_data:
            with open(file_path, "wb") as f:
                f.write(image_part.inline_data.data)
            
            return f"/{image_folder}/{image_filename}"
        else:
            raise ValueError("No image data returned from Nano Banana.")

    except Exception as e:
        print(f"❌ [Nano Banana Error]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Premium image generation failed: {e}")
    
 