import requests
import uuid
import os
from typing import Optional, Tuple
from fastapi import HTTPException 
from  config import CampaignPathManager
from Campaign.blog.blog_prompt_generator import BlogPromptOutput
from utils.ai_helpers import generate_cloudflare_image,openrouter_chat_completion

# --- New Function for Image Generation ---
def generate_blog_image(image_prompt: str, campaign_id: str) -> tuple[str, Optional[str]]:
    """
    Generates a single blog hero image using the Fireworks AI FLUX.1 model.
    Returns BOTH the URL path and local file path.
    
    Returns:
        tuple: (url_path, local_file_path)
    """
    paths = CampaignPathManager.get_campaign_paths(campaign_id)
    image_folder = paths["blog_assets"]

    image_filename = f"blog_hero_{uuid.uuid4().hex[:8]}.jpeg"
    local_file_path = os.path.join(image_folder, image_filename)
    
    try:
        saved_path = generate_cloudflare_image(
            prompt=image_prompt,
            output_path=local_file_path,
            width=1024,
            height=576,
            key_num=1
        )
        
        url_path = f"/media/campaign/{campaign_id}/blog/assets/{image_filename}"
        print(f"✅ Blog Image saved: {local_file_path}")
        return (url_path, local_file_path)
        
    except Exception as e:
        return (f"Image generation failed: {str(e)}", None)
    
def generate_final_blog_content(blog_prompt_data: BlogPromptOutput) -> str:
    """
    Generates final blog content using OpenRouter fallback list.
    
    Args:
        blog_prompt_data: The BlogPromptOutput model containing the finalized prompt.

    Returns:
        The generated text content of the blog post.
    """
    final_prompt = blog_prompt_data.final_prompt
    word_count = blog_prompt_data.word_count
    enhanced_prompt = f"STRICTLY ADHERE TO {word_count} WORDS. Instructions: {final_prompt}"
    system_instruction = """You are a professional copywriter. Write elegant marketing copy for premium brands.
Focus on: sensory experience, quality, customer satisfaction, brand excellence.
Style: Warm, sophisticated. Format: Clean prose only."""

    print(f"\n--- Generating blog with OpenRouter ---")
    print(f"Word Count: {word_count} words")
    print(f"Enhanced Prompt: {enhanced_prompt[:]}...")

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": enhanced_prompt}
    ]

    try:
        response = openrouter_chat_completion(messages, temperature=0.7)
        if not response.choices or response.choices[0] is None:
            raise RuntimeError("OpenRouter returned empty choices for blog generation")
        content = response.choices[0].message.content

        if content and content.strip():
            return content.strip()
        else:
            raise HTTPException(status_code=500, detail="OpenRouter returned empty content.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenRouter API error: {str(e)}")
    

def generate_blog_image_premium(
    image_prompt: str, 
    campaign_id: str 
) -> tuple[str, Optional[str]]:
    """
    Generates a single blog hero image using Gemini's Nano Banana (Imagen 3) model.
    Returns BOTH the URL path and local file path. Optimized for Premium users.
    
    Returns:
        tuple: (url_path, local_file_path)
    """
    try:
        paths = CampaignPathManager.get_campaign_paths(campaign_id)
        image_folder = paths["blog_assets"]

        image_filename = f"blog_hero_premium_{uuid.uuid4().hex[:8]}.png"
        local_file_path = os.path.join(image_folder, image_filename)
        
        saved_path = generate_cloudflare_image(
            prompt=image_prompt,
            output_path=local_file_path,
            width=1024,
            height=576,
            key_num=1
        )
        
        url_path = f"/media/campaign/{campaign_id}/blog/assets/{image_filename}"
        print(f"✅ Premium Blog Image saved: {local_file_path}")
        
        return (url_path, local_file_path)
        
    except Exception as e:
        print(f"❌ [Cloudflare Blog Image Error]: {str(e)}")
        return (f"Premium image generation failed: {str(e)}", None)