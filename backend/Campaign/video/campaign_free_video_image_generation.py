import os
import json
import time
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

from Campaign.video.final_prompt_optimizer import FinalVideoPromptOutput
from utils.ai_helpers import generate_cloudflare_image

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


def generate_single_image_with_retry(
    scene_data: FinalVideoPromptOutput,
    headers: dict,
    payload: dict,
    image_path: Path,
    max_retries: int = 3
) -> bool:
    """
    Attempts to generate a single image with retry logic.
    Returns True if successful, False if all retries failed.
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   Attempt {attempt}/{max_retries}...")
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=payload, 
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            # Save image
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Validate image file
            if image_path.exists() and image_path.stat().st_size > 10000:  # At least 10KB
                print(f"   ✅ Success on attempt {attempt}")
                return True
            else:
                print(f"   ⚠️ Image too small or invalid on attempt {attempt}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # 2s, 4s, 8s
                    
        except Exception as e:
            print(f"   ❌ Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = 2 ** attempt
                print(f"   ⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
    
    return False


# --- 4. Main Generation Function ---

def generate_campaign_images(
    prompts_data: List[FinalVideoPromptOutput],
    output_base_dir: Path,
    image_guidance_scale: float = 7.0,
) -> List[ImageMetadata]:
    """
    Iterates through the list of final prompts, calls Cloudflare Flux-1-schnell
    alternating between account #3 and #4 to avoid rate limits.
    Saves the generated image and returns scene metadata.
    """

    if not prompts_data:
        print("Error: No prompts provided for image generation.")
        return []

    # 1. Isolation Setup
    images_sub_dir = output_base_dir / "images"
    images_sub_dir.mkdir(parents=True, exist_ok=True)

    # Calculate total duration to decide the format
    total_duration = sum(p.duration for p in prompts_data)

    if total_duration <= 20:
        aspect_ratio = "9:16"
        width, height = 1080, 1920
        format_tag = "vertical 9:16 portrait orientation, tall framing, vertical composition"
        format_name = "VERTICAL (Reels/Shorts)"
    else:
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

    metadata_list: List[ImageMetadata] = []

    for idx, scene_data in enumerate(prompts_data, 1):
        # Alternate between Cloudflare account #3 and #4
        key_num = 3 if idx % 2 == 1 else 4

        enhanced_prompt = f"{scene_data.video_prompt}, {format_tag}"

        image_filename = f"scene_{scene_data.scene_id:03d}.jpeg"
        image_path = images_sub_dir / image_filename

        print(f"🎨 Generating Scene {idx}/{len(prompts_data)} (ID: {scene_data.scene_id})")
        print(f"   Format: {aspect_ratio} ({width}x{height})")
        print(f"   Duration: {scene_data.duration}s")
        print(f"   Using Cloudflare Account #{key_num}")
        print(f"   Prompt: {enhanced_prompt[:100]}...")

        try:
            generate_cloudflare_image(
                prompt=enhanced_prompt,
                output_path=str(image_path),
                width=width,
                height=height,
                key_num=key_num,
            )

            # Validate image file
            if image_path.exists() and image_path.stat().st_size > 10000:
                print(f"   ✅ Saved: {image_filename}")

                # Save Metadata per scene
                metadata = ImageMetadata(
                    scene_id=scene_data.scene_id,
                    duration=scene_data.duration,
                    image_filename=image_filename,
                )

                metadata_path = output_base_dir / f"scene_{scene_data.scene_id}_meta.json"
                with open(metadata_path, "w") as f:
                    f.write(metadata.model_dump_json(indent=2))

                metadata_list.append(metadata)
            else:
                print(f"   ❌ Image too small or invalid: {image_filename}")

        except Exception as e:
            print(f"   ❌ FAILED Scene {scene_data.scene_id}: {e}")

        # Small delay between calls to be polite to the API
        if idx < len(prompts_data):
            time.sleep(1.0)

    # Master metadata for stitching step
    if metadata_list:
        master_metadata_path = output_base_dir / "master_scene_metadata.json"
        json_output = [m.model_dump() for m in metadata_list]
        with open(master_metadata_path, "w") as f:
            json.dump(json_output, f, indent=2)
        print(f"✅ Master metadata saved: {master_metadata_path}")

    return metadata_list

 