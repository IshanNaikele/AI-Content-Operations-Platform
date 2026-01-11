import os
import requests
import uuid
from typing import Tuple, Optional, List, Dict, Any
from fastapi import HTTPException 
from google import genai
from google.genai import types

# 1. Absolute Imports from the root to handle new folder structure
from config import CampaignPathManager
from Campaign.image.image_prompt_generator import ImagePromptListOutput, GeneratedImagePrompt

# =============================================================================
# CORE IMAGE GENERATION (Standard - Fireworks AI)
# =============================================================================

def generate_single_image(image_prompt: str, campaign_id: str, filename_prefix: str = "ad_asset") -> Tuple[str, Optional[str]]:
    """
    Generates a single image using Fireworks AI and saves it to a unique campaign folder.
    """
    FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
    if not FIREWORKS_API_KEY:
        raise ValueError("Fireworks API key not available for image generation.")

    # 2. Use Path Manager for isolated storage
    paths = CampaignPathManager.get_campaign_paths(campaign_id)
    image_folder = paths["base"] / "images"
    os.makedirs(image_folder, exist_ok=True)

    image_filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.jpeg"
    local_file_path = str(image_folder / image_filename)
    
    API_URL = "https://api.fireworks.ai/inference/v1/workflows/accounts/fireworks/models/flux-1-schnell-fp8/text_to_image"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "image/jpeg",
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
    }
    
    payload = {
        "prompt": image_prompt,
        "width": 1024,
        "height": 1024, 
        "sampler": "dpm++ sde"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90) 
        if response.status_code == 200:
            with open(local_file_path, "wb") as f:
                f.write(response.content)
            
            # 3. Dynamic URL Path relative to /media mount
            url_path = f"/media/campaign/{campaign_id}/images/{image_filename}"
            print(f"✅ Ad Asset saved: {local_file_path}")
            return (url_path, local_file_path)
        else:
            return (f"API error {response.status_code}", None)
    except Exception as e:
        return (f"Image generation failed: {str(e)}", None)

# =============================================================================
# ORCHESTRATOR (Standard)
# =============================================================================

def generate_all_ad_images(image_prompt_list: ImagePromptListOutput, campaign_id: str) -> List[Dict[str, Any]]:
    """Iterates through prompts and saves to campaign-specific folder."""
    generated_assets = []
    print(f"\n--- Generating {image_prompt_list.image_count} Assets for Campaign: {campaign_id} ---")
    
    for prompt_data in image_prompt_list.prompts:
        filename_prefix = f"ad_asset_{prompt_data.prompt_id}"
        url_path, local_path = generate_single_image(
            image_prompt=prompt_data.image_prompt,
            campaign_id=campaign_id,
            filename_prefix=filename_prefix
        )
        
        generated_assets.append({
            "prompt_id": prompt_data.prompt_id,
            "variation_description": prompt_data.variation_description,
            "image_url": url_path,
            "local_path": local_path,
        })
    return generated_assets

# =============================================================================
# CORE IMAGE GENERATION (Premium - Imagen 3)
# =============================================================================

def generate_single_image_premium(
    image_prompt: str, 
    campaign_id: str, 
    gemini_client: genai.Client,
    filename_prefix: str = "premium_ad_asset"
) -> Tuple[str, Optional[str]]:
    """Generates high-fidelity image using Imagen 3 via Gemini."""
    try:
        paths = CampaignPathManager.get_campaign_paths(campaign_id)
        image_folder = paths["base"] / "images"
        os.makedirs(image_folder, exist_ok=True)

        image_filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
        local_file_path = str(image_folder / image_filename)

        # 4. Correct model name for Imagen 3
        response = gemini_client.models.generate_content(
            model='imagen-3.0-generate-001', 
            contents=image_prompt
        )

        image_part = response.candidates[0].content.parts[0]
        if image_part.inline_data:
            with open(local_file_path, "wb") as f:
                f.write(image_part.inline_data.data)
            
            url_path = f"/media/campaign/{campaign_id}/images/{image_filename}"
            print(f"✅ Premium Asset saved: {local_file_path}")
            return (url_path, local_file_path)
        else:
            return ("No image data returned", None)
    except Exception as e:
        return (f"Premium failure: {str(e)}", None)

# =============================================================================
# ORCHESTRATOR (Premium)
# =============================================================================

def generate_all_ad_images_premium(image_prompt_list: ImagePromptListOutput, gemini_client: genai.Client, campaign_id: str) -> List[Dict[str, Any]]:
    """Premium orchestrator using campaign-specific isolation."""
    generated_assets = []
    for prompt_data in image_prompt_list.prompts:
        url_path, local_path = generate_single_image_premium(
            image_prompt=prompt_data.image_prompt,
            campaign_id=campaign_id,
            gemini_client=gemini_client,
            filename_prefix=f"premium_asset_{prompt_data.prompt_id}"
        )
        generated_assets.append({
            "prompt_id": prompt_data.prompt_id,
            "image_url": url_path,
            "local_path": local_path,
            "model_used": "Imagen 3"
        })
    return generated_assets