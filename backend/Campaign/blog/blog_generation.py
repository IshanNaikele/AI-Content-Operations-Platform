import requests
import uuid
import os
from typing import Optional, Tuple
from fastapi import HTTPException
from groq import Groq
from google import genai
from google.genai import types

# 1. Absolute Import for the CampaignPathManager
from  config import CampaignPathManager
from Campaign.blog.blog_prompt_generator import BlogPromptOutput
 
 
 
 
 
# --- New Function for Image Generation ---
def generate_blog_image(image_prompt: str, campaign_id: str) -> tuple[str, Optional[str]]:
    """
    Generates a single blog hero image using the Fireworks AI FLUX.1 model.
    Returns BOTH the URL path and local file path.
    
    Returns:
        tuple: (url_path, local_file_path)
    """
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    if not FIREWORKS_API_KEY:
        raise HTTPException(status_code=500, detail="Fireworks API key not available for image generation.")

    # 2. Use CampaignPathManager for isolated storage
    paths = CampaignPathManager.get_campaign_paths(campaign_id)
    image_folder = paths["blog_assets"]

    image_filename = f"blog_hero_{uuid.uuid4().hex[:8]}.jpeg"
    local_file_path = os.path.join(image_folder, image_filename)  # ⭐ Full local path
    
    API_URL = "https://api.fireworks.ai/inference/v1/workflows/accounts/fireworks/models/flux-1-schnell-fp8/text_to_image"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "image/jpeg",
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
    }
    
    # We use a standard blog hero aspect ratio (16:9)
    payload = {
        "prompt": image_prompt,
        "width": 1024,
        "height": 576, 
        "sampler": "dpm++ sde"
    }
    print(f"DEBUG: Generating blog image with prompt: {image_prompt[:80]}...")
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            with open(local_file_path, "wb") as f:
                f.write(response.content)
            
            # ⭐ Return BOTH url_path (for frontend) and local_file_path (for WordPress upload)
            url_path = f"/media/campaign/{campaign_id}/blog/assets/{image_filename}"
            print(f"✅ Blog Image saved: {local_file_path}")
            return (url_path, local_file_path)
        else:
            print(f"ERROR: Image API failed: {response.text}")
            # Return error tuple
            error_msg = f"Image generation failed: API error {response.status_code}"
            return (error_msg, None)
            
    except requests.exceptions.Timeout:
        return ("Image generation failed: Timeout", None)
    except Exception as e:
        return (f"Image generation failed: {str(e)}", None)
    
def generate_final_blog_content(blog_prompt_data: BlogPromptOutput, groq_client: Groq) -> str:
    """
    Generates final blog content using Groq (simple & minimal).
    
    Args:
        blog_prompt_data: The BlogPromptOutput model containing the finalized prompt.
        groq_client: The initialized Groq client.

    Returns:
        The generated text content of the blog post.
    """
    
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq Client not initialized.")
    
    final_prompt = blog_prompt_data.final_prompt
    word_count = blog_prompt_data.word_count
    enhanced_prompt = f"STRICTLY ADHERE TO {word_count} WORDS. Instructions: {final_prompt}"
    system_instruction = """You are a professional copywriter. Write elegant marketing copy for premium brands.
Focus on: sensory experience, quality, customer satisfaction, brand excellence.
Style: Warm, sophisticated. Format: Clean prose only."""
    print(f"\n--- Generating blog with Groq ---")
    print(f"Word Count: {word_count} words")
    print(f"Enhanced Prompt: {enhanced_prompt[:]}...")
    print(f"\n--- Generating blog with Groq ---")
    
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        
        if content and content.strip():
            return content.strip()
        else:
            raise HTTPException(status_code=500, detail="Groq returned empty content.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")
    

def generate_blog_image_premium(
    image_prompt: str, 
    campaign_id: str, 
    gemini_client: genai.Client
) -> tuple[str, Optional[str]]:
    """
    Generates a single blog hero image using Gemini's Nano Banana (Imagen 3) model.
    Returns BOTH the URL path and local file path. Optimized for Premium users.
    
    Returns:
        tuple: (url_path, local_file_path)
    """
    try:
        # Ensure the image folder exists
        paths = CampaignPathManager.get_campaign_paths(campaign_id)
        image_folder = paths["blog_assets"]

        image_filename = f"blog_hero_premium_{uuid.uuid4().hex[:8]}.png"
        local_file_path = os.path.join(image_folder, image_filename)
        
        print(f"DEBUG [Premium]: Generating Nano Banana Blog Hero: {image_prompt[:80]}...")

        # Call the native Gemini Image Generation model (Nano Banana)
        # Note: We pass the prompt directly. Nano Banana handles aspect ratios 
        # based on prompt description or model defaults.
        response = gemini_client.models.generate_content(
            model='gemini-3-pro-image-preview', 
            contents=image_prompt,
            config=types.GenerateContentConfig(
                candidate_count=1,
                # Optionally add aspect ratio instructions here if your SDK version supports it
            )
        )

        # Gemini returns images as byte data within parts
        image_part = response.candidates[0].content.parts[0]
        
        if image_part.inline_data:
            with open(local_file_path, "wb") as f:
                f.write(image_part.inline_data.data)
            
            # Return url_path (for frontend) and local_file_path (for WordPress upload)
            url_path = f"/media/campaign/{campaign_id}/blog/assets/{image_filename}"
            print(f"✅ Premium Blog Image saved: {local_file_path}")
            
            return (url_path, local_file_path)
        else:
            print("ERROR: No image data returned from Nano Banana.")
            return ("Premium image generation failed: No data", None)

    except Exception as e:
        print(f"❌ [Nano Banana Error]: {str(e)}")
        return (f"Premium image generation failed: {str(e)}", None)