import os
import json
import requests
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
import time
# --- 1. Pydantic Models for Input (Output of Step 5) ---
# 1. Corrected Absolute Import
from Campaign.video.final_prompt_optimizer import FinalVideoPromptOutput

class FinalVideoPromptOutput(BaseModel):
    """
    Input model for a single scene, carrying the final prompt and timing data.
    This is the output structure from the previous LLM step (Step 5).
    """
    scene_id: int
    duration: float
    video_prompt: str

# --- 2. Pydantic Model for Metadata Output (Used in Stitching Step) ---

class ImageMetadata(BaseModel):
    """
    Metadata saved alongside the image for the final video stitching process.
    """
    scene_id: int
    duration: float
    image_filename: str

# --- 3. Configuration ---

API_URL = "https://api.fireworks.ai/inference/v1/workflows/accounts/fireworks/models/flux-1-schnell-fp8/text_to_image"
OUTPUT_DIR = Path("free_video_generator/images")


# --- 4. Main Generation Function ---

def generate_campaign_images(
    prompts_data: List[FinalVideoPromptOutput],
    fireworks_api_key: str,
    output_base_dir: Path ,
    image_guidance_scale: float = 7.0,
) -> List[ImageMetadata]:
    """
    Iterates through the list of final prompts, calls the Fireworks AI API, 
    saves the generated image, and returns the scene metadata.
    """
    
    if not prompts_data:
        print("Error: No prompts provided for image generation.")
        return []
    
    # 1. Isolation Setup: Ensure the specific variant folders exist
    images_sub_dir = output_base_dir / "images"
    images_sub_dir.mkdir(parents=True, exist_ok=True)

    # Calculate total duration to decide the format
    total_duration = sum(p.duration for p in prompts_data)
    
    if total_duration <= 40:
        # Portrait (Insta Reels / YT Shorts)
        aspect_ratio = "9:16"
        width, height = 1080, 1920
        format_tag = "vertical 9:16 portrait orientation, tall framing, vertical composition"
        format_name = "VERTICAL (Reels/Shorts)"
    else:
        # Landscape (Standard Video)
        aspect_ratio = "16:9"
        width, height = 1920, 1080
        format_tag = "landscape 16:9 cinematic widescreen, horizontal composition"
        format_name = "LANDSCAPE (YouTube)"
    
    print(f"\n{'='*70}")
    print(f"🎬 VIDEO FORMAT DETECTION")
    print(f"{'='*70}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print(f"Selected Format: {format_name}")
    print(f"Aspect Ratio: {aspect_ratio}")
    print(f"Dimensions: {width}x{height}")
    print(f"{'='*70}\n")

 
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "image/jpeg",
        "Authorization": f"Bearer {fireworks_api_key}",
    }
    
    metadata_list: List[ImageMetadata] = []
    
    for idx, scene_data in enumerate(prompts_data, 1):
        enhanced_prompt = f"{scene_data.video_prompt}, {format_tag}"
        
        # CRITICAL FIX: Include aspect_ratio parameter
        # Try multiple parameter combinations for maximum compatibility
        payload = {
            "prompt": enhanced_prompt,
            "aspect_ratio": aspect_ratio,  # ✅ PRIMARY: Aspect ratio string
            "width": width,                 # ✅ BACKUP: Explicit dimensions
            "height": height,               # ✅ BACKUP: Explicit dimensions
            "guidance_scale": image_guidance_scale,
            "num_inference_steps": 28,
        }
        
        print(f"🎨 Generating Scene {idx}/{len(prompts_data)} (ID: {scene_data.scene_id})")
        print(f"   Format: {aspect_ratio} ({width}x{height})")
        print(f"   Duration: {scene_data.duration}s")
        print(f"   Prompt: {enhanced_prompt[:100]}...")
        
        try:
            # Call Fireworks AI API
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=payload, 
                stream=True,
                timeout=120  # Add timeout for long-running requests
            )
            response.raise_for_status()
            
            image_filename = f"scene_{scene_data.scene_id:03d}.jpeg"
            image_path = images_sub_dir / image_filename
            
            # Save image
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify image was created and has content
            if image_path.exists() and image_path.stat().st_size > 0:
                # Save Metadata per scene for granular recovery
                metadata = ImageMetadata(
                    scene_id=scene_data.scene_id,
                    duration=scene_data.duration,
                    image_filename=image_filename
                )
                
                metadata_path = output_base_dir / f"scene_{scene_data.scene_id}_meta.json"
                with open(metadata_path, 'w') as f:
                    f.write(metadata.model_dump_json(indent=2))
                     
                metadata_list.append(metadata)
                print(f"   ✅ Saved: {image_filename}")
            
        except Exception as e:
            print(f"   ❌ Error generating scene {scene_data.scene_id}: {e}")
        
        # Prevent API rate limiting
        if idx < len(prompts_data):
            time.sleep(1.0)

    # 4. Master Metadata: Essential for the stitching step
    if metadata_list:
        master_metadata_path = output_base_dir / "master_scene_metadata.json"
        json_output = [m.model_dump() for m in metadata_list] 
        with open(master_metadata_path, 'w') as f:
            json.dump(json_output, f, indent=2)
        print(f"✅ Master metadata saved: {master_metadata_path}")
            
    return metadata_list

# --- 5. Debug Function to Test API Parameters ---

def test_api_parameters(fireworks_api_key: str):
    """
    Test function to verify which parameters the Fireworks API accepts.
    Run this first to diagnose the issue!
    """
    print("\n🔍 TESTING API PARAMETER ACCEPTANCE\n")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "image/jpeg",
        "Authorization": f"Bearer {fireworks_api_key}",
    }
    
    test_prompt = "a simple red circle on white background"
    
    test_cases = [
        {
            "name": "Test 1: Aspect Ratio Only (9:16)",
            "payload": {
                "prompt": test_prompt,
                "aspect_ratio": "9:16",
                "guidance_scale": 7.0,
                "num_inference_steps": 28,
            }
        },
        {
            "name": "Test 2: Width/Height Only (1080x1920)",
            "payload": {
                "prompt": test_prompt,
                "width": 1080,
                "height": 1920,
                "guidance_scale": 7.0,
                "num_inference_steps": 28,
            }
        },
        {
            "name": "Test 3: Both Aspect Ratio AND Width/Height",
            "payload": {
                "prompt": test_prompt,
                "aspect_ratio": "9:16",
                "width": 1080,
                "height": 1920,
                "guidance_scale": 7.0,
                "num_inference_steps": 28,
            }
        },
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}")
        print(f"Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=test['payload'],
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Status: {response.status_code}")
                
                # Save test image to check dimensions
                test_path = Path(f"test_{test['name'].replace(' ', '_').replace(':', '')}.jpeg")
                with open(test_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"   Saved to: {test_path}")
                print(f"   Check this image to verify it's actually vertical!")
            else:
                print(f"❌ FAILED! Status: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
    
    print("\n" + "="*70)
    print("Testing complete! Check the generated test images to see which worked.")
    print("="*70 + "\n")