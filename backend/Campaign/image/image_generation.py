import os
import requests
import uuid
from typing import Tuple, Optional, List, Dict, Any
from fastapi import HTTPException   
from config import CampaignPathManager
from Campaign.image.image_prompt_generator import ImagePromptListOutput, GeneratedImagePrompt
from utils.ai_helpers import generate_cloudflare_image
# =============================================================================
# CORE IMAGE GENERATION (Standard - Fireworks AI)
# =============================================================================

def generate_single_image(image_prompt: str, campaign_id: str, filename_prefix: str = "ad_asset") -> Tuple[str, Optional[str]]:
    """
    Generates a single image using Fireworks AI and saves it to a unique campaign folder.
    """
    paths = CampaignPathManager.get_campaign_paths(campaign_id)
    image_folder = paths["base"] / "images"
    os.makedirs(image_folder, exist_ok=True)

    image_filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.jpeg"
    local_file_path = str(image_folder / image_filename)
    
    try:
        saved_path = generate_cloudflare_image(
            prompt=image_prompt,
            output_path=local_file_path,
            width=1024,
            height=1024,
            key_num=2
        )
        
        url_path = f"/media/campaign/{campaign_id}/images/{image_filename}"
        print(f"✅ Ad Asset saved: {local_file_path}")
        return (url_path, local_file_path)
        
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
    filename_prefix: str = "premium_ad_asset"
) -> Tuple[str, Optional[str]]:
    """Generates high-fidelity image using Imagen 3 via Gemini."""
    try:
        paths = CampaignPathManager.get_campaign_paths(campaign_id)
        image_folder = paths["base"] / "images"
        os.makedirs(image_folder, exist_ok=True)

        image_filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
        local_file_path = str(image_folder / image_filename)

        saved_path = generate_cloudflare_image(
            prompt=image_prompt,
            output_path=local_file_path,
            width=1024,
            height=1024,
            key_num=2
        )
        
        url_path = f"/media/campaign/{campaign_id}/images/{image_filename}"
        print(f"✅ Premium Asset saved: {local_file_path}")
        return (url_path, local_file_path)
        
    except Exception as e:
        return (f"Premium failure: {str(e)}", None)

# =============================================================================
# ORCHESTRATOR (Premium)
# =============================================================================

def generate_all_ad_images_premium(image_prompt_list: ImagePromptListOutput, campaign_id: str) -> List[Dict[str, Any]]:
    """Premium orchestrator using campaign-specific isolation."""
    generated_assets = []
    for prompt_data in image_prompt_list.prompts:
        url_path, local_path = generate_single_image_premium(
            image_prompt=prompt_data.image_prompt,
            campaign_id=campaign_id,
            filename_prefix=f"premium_asset_{prompt_data.prompt_id}"
        )
        generated_assets.append({
            "prompt_id": prompt_data.prompt_id,
            "image_url": url_path,
            "local_path": local_path,
            "model_used": "Imagen 3"
        })
    return generated_assets