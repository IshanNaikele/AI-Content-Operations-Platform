import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Form, HTTPException, Request,BackgroundTasks 
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import asyncio
from Campaign.video.subtitle_service import generate_srt, get_ffmpeg_compatible_path
import os
import traceback
from Campaign.X_publish import upload_and_post_auto
from Campaign.youtube_publish import publish_video_to_youtube
from config import (
    CampaignPathManager, 
    get_tavily_client,
    X_SESSION_KEY,
    MEDIA_ROOT,
    IMAGE_FOLDER,             
    BASE_VIDEO_ASSETS_DIR       
)
import json
import shutil
from llm_intent_classifier import classify_and_strategize
from  personal.personal_image_generator import (
    generate_image_prompt, 
    generate_image, 
    sanitize_topic_for_filename, 
    map_ratio_to_dimensions,
    generate_image_nano_banana
)
from Campaign.campaign_tavily_search import perform_tavily_search
from Campaign.research_analysis import perform_research_analysis
from Campaign.blog.blog_prompt_generator import generate_blog_prompt
from Campaign.image.image_prompt_generator import generate_image_prompts
from Campaign.image.image_generation import generate_all_ad_images, generate_all_ad_images_premium
from Campaign.blog.blog_generation import generate_final_blog_content, generate_blog_image,generate_blog_image_premium
from Campaign.wordpress_publish import (
    create_draft_post_to_wordpress,
    update_and_schedule_post
)
 
# Pipeline Modules
from Campaign.video.video_bible_generator import generate_video_bible, VideoBibleOutput
from Campaign.video.video_script_generator import generate_video_script, ScriptOutput
from Campaign.video.audio_generator_elevenlabs import generate_audio_and_timestamps, AudioTimestampOutput, get_tts_client
from Campaign.video.storyboard_generator import generate_storyboard, StoryboardOutput
from Campaign.video.final_prompt_optimizer import optimize_video_prompts_batch, FinalVideoPromptOutput
from Campaign.video.campaign_free_video_image_generation import generate_campaign_images
from Campaign.video.image_to_video_creation import stitch_slideshow_video_ffmpeg 
from Campaign.video.background_music_downloader import download_music_for_campaign 

router = APIRouter()

# Add rate limiter class
class RateLimiters:
    """Global rate limiters for all API calls"""
    gemini_semaphore = asyncio.Semaphore(2)
    fireworks_semaphore_1 = asyncio.Semaphore(1)
    fireworks_semaphore_2 = asyncio.Semaphore(1)
    fireworks_semaphore_3 = asyncio.Semaphore(1)
    fireworks_semaphore_4 = asyncio.Semaphore(1)
    elevenlabs_semaphore = asyncio.Semaphore(2)

async def rate_limited_fireworks_call(func, api_key_num, *args, **kwargs):
    """Rate limited Fireworks call using specified API key"""
    semaphores = {
        1: RateLimiters.fireworks_semaphore_1,
        2: RateLimiters.fireworks_semaphore_2,
        3: RateLimiters.fireworks_semaphore_3,
        4: RateLimiters.fireworks_semaphore_4
    }
    semaphore = semaphores.get(api_key_num, RateLimiters.fireworks_semaphore_1)
    async with semaphore:
        result = await asyncio.to_thread(func, *args, **kwargs)
        return result

# ═══════════════════════════════════════════════════════════
# 🔍 POLLING ENDPOINT - Check Campaign Status
# ═══════════════════════════════════════════════════════════

@router.get("/campaign_status/{campaign_id}")
async def get_campaign_status(campaign_id: str):
    """
    Frontend polls this endpoint every 15 seconds to check if videos are ready.
    Returns video URLs when they exist.
    """
    try:
        paths = CampaignPathManager.get_campaign_paths(campaign_id)
        
        # Check if campaign folder exists
        if not paths["base"].exists():
            return JSONResponse({
                "status": "not_found",
                "message": "Campaign not found"
            }, status_code=404)
        
        # Define expected video files
        video_mapping = {
            "SHORT_1": paths["short_1"] / "SHORT_1_final.mp4"
        }
        
        # Check which videos are complete
        completed_videos = []
        for label, video_path in video_mapping.items():
            if video_path.exists():
                metadata_path = video_path.parent / f"{label}_metadata.json"
                title = f"{label} Video"
                description = "Generated video"
                
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            title = metadata.get('title', title)
                            description = metadata.get('description', description)
                    except:
                        pass
                
                completed_videos.append({
                    "label": label,
                    "video_path": str(video_path),
                    "video_url": f"/media/campaign/{campaign_id}/{label}/{video_path.name}",
                    "title": title,
                    "description": description,
                    "duration": 30 if label == "LONG_FORM" else 10,
                    "status": "ready"
                })

        blog_data = None
        blog_content_path = paths["base"] / "blog_content.txt"
        blog_image_path = paths["base"] / "blog_hero_image.jpeg"
        
        if blog_content_path.exists():
            try:
                with open(blog_content_path, 'r', encoding='utf-8') as f:
                    blog_content = f.read()
                
                blog_image_url = None
                if blog_image_path.exists():
                    blog_image_url = f"/media/campaign/{campaign_id}/blog_hero_image.jpeg"
                
                blog_data = {
                    "content": blog_content,
                    "image_url": blog_image_url,
                    "status": "ready"
                }
            except Exception as e:
                print(f"Error reading blog: {e}")

        ad_images = []
        ad_images_dir = paths["base"] / "ad_images"
        
        if ad_images_dir.exists():
            for img_file in sorted(ad_images_dir.glob("*.jpeg")):
                ad_images.append({
                    "filename": img_file.name,
                    "url": f"/media/campaign/{campaign_id}/ad_images/{img_file.name}",
                    "status": "ready"
                })
        
        # Determine overall status
        total_videos = len(video_mapping)
        completed_count = len(completed_videos)
        
        if completed_count == 0:
            status = "processing"
            message = "Reel is being generated..."
        elif completed_count < total_videos:
            status = "processing"
            message = f"Videos in progress... ({completed_count}/{total_videos} complete)"
        else:
            status = "complete"
            message = "Reel ready!"
        
        # ✅ NEW: Check for WordPress post ID
        wordpress_post_id = None
        wp_id_path = paths["base"] / "wordpress_post_id.txt"
        if wp_id_path.exists():
            try:
                with open(wp_id_path, 'r') as f:
                    wordpress_post_id = f.read().strip()
            except Exception as e:
                print(f"⚠️ Failed to read WordPress post ID: {e}")

        return JSONResponse({
            "status": status,
            "campaign_id": campaign_id,
            "message": message,
            "progress": {
                "completed": completed_count,
                "total": total_videos,
                "percentage": int((completed_count / total_videos) * 100)
            },
            "videos": completed_videos,
            "blog": blog_data,
            "ad_images": ad_images,
            "wordpress_post_id": wordpress_post_id  
        })
        
    except Exception as e:
        print(f"❌ Error checking campaign status: {str(e)}")
        traceback.print_exc()
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)
    
# ═══════════════════════════════════════════════════════════
# 🔧 NEW WORKER FUNCTION (Heavy Operations Run Here)
# ═══════════════════════════════════════════════════════════

async def run_campaign_generation_worker(
    campaign_id: str,
    topic: str,
    plan: str,
    request: Request,
    paths: Dict,
    strategy_model,
    strategic_brief_model,
    blog_prompt_model 
):
    """
    Background worker that generates all campaign assets.
    Runs independently after the main endpoint returns.
    """
    try:
        print(f"\n🚀 [WORKER] Starting background generation for campaign {campaign_id}")
        
        # Download music ONCE for all videos
        print("\n🎵 Downloading background music (shared across all videos)...")
        music_output_path = paths["base"] / "background_music.mp3"

        try:
            music_info = await asyncio.to_thread(
                download_music_for_campaign,
                strategy_model.model_dump(),
                str(music_output_path)
            )
            bg_music_path = Path(music_info['path']) if music_info else None
            print(f"✅ Music downloaded: {bg_music_path}")
        except Exception as e:
            print(f"⚠️ Music download failed: {e}")
            bg_music_path = None

        # ═══════════════════════════════════════════════════════════
        # 📋 DEFINE ALL PIPELINES (Same as before)
        # ═══════════════════════════════════════════════════════════
        
        async def blog_pipeline():
            """Blog content + hero image generation"""
            blog_image_local_path = None
            try:
                print(f"\n🖼 [BLOG] Starting hero image generation...")
                
                if plan == "premium":
                    blog_image_url, blog_image_local_path = await asyncio.to_thread(
                        generate_blog_image_premium, 
                        image_prompt=blog_prompt_model.visual_image_prompt,
                        campaign_id=campaign_id 
                    )
                else:
                    blog_image_url, blog_image_local_path = await asyncio.to_thread(
                        generate_blog_image,
                        image_prompt=blog_prompt_model.visual_image_prompt,
                        campaign_id=campaign_id 
                    )
                print(f"✅ [BLOG] Hero image generated!")
                
                # ✅ COPY IMAGE IMMEDIATELY
                if blog_image_local_path and Path(blog_image_local_path).exists():
                    dest_path = paths["base"] / "blog_hero_image.jpeg"
                    await asyncio.to_thread(shutil.copy2, blog_image_local_path, dest_path)
                    print(f"✅ Blog image copied immediately to {dest_path}")
                
            except Exception as e:
                print(f"❌ [BLOG] Hero image failed: {str(e)}")
                blog_image_url = f"Image generation failed: {str(e)}"
            
            final_blog_text = await asyncio.to_thread(
                generate_final_blog_content,
                blog_prompt_data=blog_prompt_model 
            )
            print("✅ [BLOG] Content generation complete!")
            
            # ✅ SAVE BLOG CONTENT IMMEDIATELY
            try:
                blog_content_path = paths["base"] / "blog_content.txt"
                await asyncio.to_thread(
                    lambda: open(blog_content_path, 'w', encoding='utf-8').write(final_blog_text)
                )
                print(f"✅ Blog content saved immediately to {blog_content_path}")
            except Exception as e:
                print(f"⚠️ Blog content save failed: {e}")
            
            # ✅ NEW: Create WordPress draft post
            wordpress_post_id = None
            try:
                wordpress_result = await asyncio.to_thread(
                    create_draft_post_to_wordpress,
                    request=request,
                    title=blog_prompt_model.title,
                    content=final_blog_text,
                    featured_image_path=blog_image_local_path
                )
                wordpress_post_id = wordpress_result.get('post_id')
                
                # ✅ Save post_id to disk for polling endpoint
                if wordpress_post_id:
                    wp_id_path = paths["base"] / "wordpress_post_id.txt"
                    await asyncio.to_thread(
                        lambda: open(wp_id_path, 'w').write(str(wordpress_post_id))
                    )
                    print(f"✅ WordPress draft created: Post ID {wordpress_post_id}")
            except Exception as e:
                print(f"⚠️ WordPress draft creation failed: {e}")
            return {
                "blog_content": final_blog_text,
                "blog_image_url": blog_image_url,
                "blog_image_path": blog_image_local_path,
                "wordpress_post_id": wordpress_post_id 
            }

        async def ad_image_pipeline():
            """Advertisement image generation"""
            print("\n🖼 [AD IMAGES] Starting generation...")
            required_image_count = strategy_model.image_count
            
            image_prompt_list_model = await asyncio.to_thread(
                generate_image_prompts,
                analysis_brief=strategic_brief_model, 
                required_image_count=required_image_count
            )
            
            if plan == "premium":
                generated_ad_assets = await asyncio.to_thread(
                    generate_all_ad_images_premium,
                    image_prompt_list=image_prompt_list_model, 
                    campaign_id=campaign_id 
                )
            else:
                generated_ad_assets = await asyncio.to_thread(
                    generate_all_ad_images,
                    image_prompt_list=image_prompt_list_model,
                    campaign_id=campaign_id 
                )
            
            print(f"✅ [AD IMAGES] {len(generated_ad_assets)} assets generated!")
            
            # ✅ COPY AD IMAGES IMMEDIATELY
            try:
                ad_dir = paths["base"] / "ad_images"
                await asyncio.to_thread(ad_dir.mkdir, parents=True, exist_ok=True)
                
                for idx, asset in enumerate(generated_ad_assets):
                    local_path = asset.get('local_path')
                    if local_path and Path(local_path).exists():
                        dest = ad_dir / f"ad_asset_{idx+1}.jpeg"
                        await asyncio.to_thread(shutil.copy2, local_path, dest)
                        print(f"✅ Ad asset {idx+1} copied immediately to {dest}")
            except Exception as e:
                print(f"⚠️ Ad images immediate copy failed: {e}")
            
            return {
                "image_prompts": [p.model_dump() for p in image_prompt_list_model.prompts],
                "generated_urls": [
                    asset.get('image_url') for asset in generated_ad_assets 
                    if asset.get('image_url') and 'error' not in asset
                ],
                "ad_assets_details": generated_ad_assets
            }

        async def video_pipeline(duration_s: int, label: str, request: Request, paths: Dict, bg_music_path: Path = None):
            """Video generation WITHOUT immediate YouTube upload"""
            
            path_mapping = {
                "LONG_FORM": paths["long_form"],
                "SHORT_1": paths["short_1"],
                "SHORT_2": paths["short_2"],
                "SHORT_3": paths["short_3"]
            }
            variant_dir = path_mapping[label]
            (variant_dir / "images").mkdir(parents=True, exist_ok=True)
            
            audio_path = variant_dir / f"{label}_audio.mp3"
            srt_path = variant_dir / f"{label}_captions.srt"
            final_video_path = variant_dir / f"{label}_final.mp4"

            try:
                 
                video_bible_model = await asyncio.to_thread(
                    generate_video_bible, strategic_brief_model, strategy_model.keywords 
                )
                
                script_model = await asyncio.to_thread(
                    generate_video_script, video_bible_model, strategic_brief_model, duration_s , topic
                )

                audio_sync_output = await asyncio.to_thread(
                    generate_audio_and_timestamps,
                    full_narration_text=script_model.full_narration,
                    google_client=get_tts_client(),
                    output_audio_path=audio_path
                )
                
                await asyncio.to_thread(generate_srt, audio_sync_output.timestamps, srt_path)
                ffmpeg_srt_path = get_ffmpeg_compatible_path(str(srt_path))

                storyboard_model = await asyncio.to_thread(
                    generate_storyboard, script_model.full_narration, audio_sync_output, video_bible_model, strategic_brief_model 
                )
                
                optimized_prompts = await asyncio.to_thread(
                    optimize_video_prompts_batch, storyboard_model.scenes, video_bible_model.video_bible 
                )

                await asyncio.to_thread(
                    generate_campaign_images,
                    optimized_prompts,
                    variant_dir
                )

                await asyncio.to_thread(
                    stitch_slideshow_video_ffmpeg,
                    metadata_file_path=variant_dir / "master_scene_metadata.json",
                    output_video_path=final_video_path,
                    audio_file_path=audio_path,
                    srt_path=ffmpeg_srt_path,
                    bg_music_path=bg_music_path,
                    delete_music_after=False
                )
                
                print(f"✅ [VIDEO - {label}] Generation complete!")
                
                youtube_connected = bool(request.session.get('youtube_token'))
                
                return {
                    "label": label,
                    "status": "Generated",
                    "video_path": str(final_video_path),
                    "video_url": f"/media/campaign/{paths['id']}/{label}/{final_video_path.name}",
                    "title": script_model.video_title,
                    "description": script_model.full_narration[:500],
                    "duration": duration_s,
                    "youtube_upload_data": {
                        "file_path": str(final_video_path),
                        "title": script_model.video_title,
                        "description": script_model.full_narration[:500],
                        "public_url": f"/media/campaign/{paths['id']}/{label}/{final_video_path.name}", 
                        "connected": youtube_connected,
                        "status": "Ready to Publish"
                    }
                }
                
            except Exception as e:
                print(f"❌ [VIDEO - {label}] Pipeline failed: {str(e)}")
                traceback.print_exc()
                return {"status": "Failed", "label": label, "error": str(e)}

        # ═══════════════════════════════════════════════════════════
        # 🚀 RUN ALL PIPELINES IN PARALLEL
        # ═══════════════════════════════════════════════════════════
        
        print("\n🎥 Starting all pipelines in parallel...")
        
        video_tasks = [
    video_pipeline(10, "SHORT_1",  request=request, paths=paths, bg_music_path=bg_music_path)
]

        
        results = await asyncio.gather(
            blog_pipeline(),
            ad_image_pipeline(),
            *video_tasks,
            return_exceptions=True
        )

        blog_result = results[0]
        ad_image_result = results[1]
        video_results = results[2:]

        # ═══════════════════════════════════════════════════════════
        # 📝 WORDPRESS DRAFT CREATION
        # ═══════════════════════════════════════════════════════════
        
        print("\n💾 Saving assets to disk...")
        
         
        
        # 3. Save Video Metadata (titles, descriptions)
        path_mapping = {
            "LONG_FORM": paths["long_form"],
            "SHORT_1": paths["short_1"],
            "SHORT_2": paths["short_2"],
            "SHORT_3": paths["short_3"]
        }
        
        for video_result in video_results:
            if isinstance(video_result, Exception):
                continue
                
            if video_result.get("status") == "Generated":
                try:
                    label = video_result.get("label")
                    variant_dir = path_mapping.get(label)
                    
                    if variant_dir:
                        metadata_path = variant_dir / f"{label}_metadata.json"
                        with open(metadata_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                "title": video_result.get("title", ""),
                                "description": video_result.get("description", ""),
                                "video_path": str(video_result.get("video_path", "")),
                                "video_url": video_result.get("video_url", "")
                            }, f, indent=2)
                        print(f"✅ Metadata saved for {label}")
                except Exception as e:
                    print(f"⚠️ Metadata save failed for {label}: {e}")

        
    except Exception as e:
        print(f"❌ [WORKER] Fatal error: {str(e)}")
        traceback.print_exc()


# ═══════════════════════════════════════════════════════════
# 🎯 UPDATED MAIN ENDPOINT (Returns Immediately)
# ═══════════════════════════════════════════════════════════

@router.post("/analyze_topic")
async def analyze_topic(
    request: Request,
    background_tasks: BackgroundTasks,  # ← ADDED
    topic: str = Form(...), 
    plan: str = Form(...), 
    video_duration: Optional[str] = Form("60s"),
    publish_time: Optional[str] = Form(None)
): 
    """
    STEP 1: Fast classification & research, then hand off to background worker.
    Returns immediately to avoid Cloudflare timeout.
    """
    print("\n" + "="*80)
    print("📥 STEP 1: RECEIVED FORM DATA & START GENERATION")
    print("="*80)
    print(f"Topic: {topic}")
    print(f"Plan: {plan}")
    print("="*80 + "\n")
    
    campaign_id = str(uuid.uuid4())
    paths = CampaignPathManager.get_campaign_paths(campaign_id)
    print(f"🚀 Launching Campaign ID: {campaign_id}")
    
    try:
        # ═══════════════════════════════════════════════════════════
        # ⚡ FAST OPERATIONS (Complete in <30 seconds)
        # ═══════════════════════════════════════════════════════════
         
        tavily_client = get_tavily_client()

        # 1. Intent Classification
        strategy_model = classify_and_strategize(topic )
        
        # ═══════════════════════════════════════════════════════════
        # 🖼️ HANDLE IMAGE INTENT (Keep synchronous - it's fast)
        # ═══════════════════════════════════════════════════════════
        
        if strategy_model.intent == "image":
             
            personal_assets_path = Path("media/personal") / campaign_id
            personal_assets_path.mkdir(parents=True, exist_ok=True)

            refined_output_model = await asyncio.to_thread(
                generate_image_prompt, topic 
            )
            
            generated_urls = []
            sanitized_topic = sanitize_topic_for_filename(topic)
            
            for i, refined_prompt_detail in enumerate(refined_output_model.prompts):
                refined_prompt = refined_prompt_detail.prompt
                ratio_str = refined_prompt_detail.aspect_ratio 
                dimensions = map_ratio_to_dimensions(ratio_str)
                width = dimensions['width']
                height = dimensions['height']
                image_filename = f"{sanitized_topic}{uuid.uuid4().hex[:4]}{i+1}.jpeg" 
                
                if plan == "premium":
                    image_url_path = generate_image_nano_banana(
                        refined_prompt, 
                        image_filename, 
                        str(personal_assets_path),
                        width=width, 
                        height=height 
                    )
                else:
                    image_url_path = generate_image(
                        refined_prompt, 
                        image_filename, 
                        str(personal_assets_path),
                        width=width, 
                        height=height
                    )
                generated_urls.append(image_url_path)
            
            return JSONResponse(content={
                "status": "complete",
                "strategy": strategy_model.model_dump(),
                "image_prompts": [p.model_dump() for p in refined_output_model.prompts],
                "generated_image_urls": generated_urls,
                "message": f"Image prompts refined and {len(generated_urls)} images generated."
            })
        
        # ═══════════════════════════════════════════════════════════
        # 📰 HANDLE CAMPAIGN INTENT (Background processing)
        # ═══════════════════════════════════════════════════════════
        
        elif strategy_model.intent == "campaign":
            # 2. Research (Fast - happens synchronously)
            if strategy_model.requires_research and strategy_model.research_queries:
                tavily_results = perform_tavily_search(strategy_model.research_queries, tavily_client)
                strategic_brief_model = perform_research_analysis(topic, tavily_results)
                
                blog_prompt_model = generate_blog_prompt(
                    analysis_brief=strategic_brief_model, 
                    initial_strategy=strategy_model,  
                    original_topic=topic 
                )
                
                # ═══════════════════════════════════════════════════════════
                # 🚀 HAND OFF TO BACKGROUND WORKER
                # ═══════════════════════════════════════════════════════════
                
                background_tasks.add_task(
                    run_campaign_generation_worker,
                    campaign_id=campaign_id,
                    topic=topic,
                    plan=plan,
                    request=request,
                    paths=paths,
                    strategy_model=strategy_model,
                    strategic_brief_model=strategic_brief_model,
                    blog_prompt_model=blog_prompt_model 
                )
                
                # ═══════════════════════════════════════════════════════════
                # ✅ RETURN IMMEDIATELY (No timeout!)
                # ═══════════════════════════════════════════════════════════
                
                return JSONResponse(content={
                    "status": "processing",
                    "campaign_id": campaign_id,
                    "message": "Campaign generation started! Assets will be ready in 5-7 minutes. Check your WordPress drafts.",
                    "strategy": strategy_model.model_dump(),
                    "strategic_brief": strategic_brief_model.model_dump(),
                    "blog_title": blog_prompt_model.title,
                    "expected_assets": {
                        "blog": "1 post",
                        "images": f"{strategy_model.image_count} ad assets",
                        "videos": "1 short reel (10s)"
                    },
                    "wordpress_status": "Will auto-draft when complete",
                    "estimated_completion": "5-7 minutes"
                })
            
            else:
                # No research needed - still fast
                return JSONResponse(content={
                    "status": "complete",
                    "message": "Campaign strategy created (no research needed)",
                    "strategy": strategy_model.model_dump()
                })
        
    except ValidationError as e:
        print(f"Validation Error: {e}")
        return JSONResponse(
            content={"error": "LLM output validation failed", "details": str(e)}, 
            status_code=500
        )
    except HTTPException as e:
        print(f"HTTP Exception: {e.detail}")
        return JSONResponse(
            content={"error": e.detail}, 
            status_code=e.status_code
        )
    except ValueError as e: 
        print(f"Value Error: {e}")
        return JSONResponse(
            content={"error": "LLM parsing error", "details": str(e)}, 
            status_code=500
        )
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return JSONResponse(
            content={"error": "Internal server error", "details": str(e)}, 
            status_code=500
        )


# ═══════════════════════════════════════════════════════════════════════════
# ✅ FIXED: UNIFIED PUBLISHING ENDPOINT FOR ALL PLATFORMS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/schedule_post")
async def schedule_post_action(
    request: Request,
    platform: str = Form(...),  # 'wordpress', 'youtube', or 'x'
    action: str = Form(...),     # 'publish', 'schedule', 'discard'
    
    # WordPress-specific fields
    post_id: Optional[str] = Form(None),
    
    # YouTube-specific fields
    video_path: Optional[str] = Form(None),
    video_title: Optional[str] = Form(None),
    video_description: Optional[str] = Form(None),
    video_label: Optional[str] = Form(None),
    
    # X/Twitter-specific fields
    tweet_text: Optional[str] = Form(None),
    image_path: Optional[str] = Form(None),
    
    # Common fields
    publish_time: Optional[str] = Form(None)
):
    """
    ✅ UNIFIED ENDPOINT: Handles publishing for WordPress, YouTube, and X/Twitter
    
    Platform-specific requirements:
    - WordPress: Requires post_id
    - YouTube: Requires video_path, video_title, video_description
    - X/Twitter: Requires tweet_text, optional image_path
    """
    print("\n" + "#"*80)
    print(f"🗓 STEP 2: {platform.upper()} {action.upper()} REQUEST")
    print("#"*80)
    
    try:
        platform = platform.lower()
        action = action.lower()
        
         
        
        # ═══════════════════════════════════════════════════════════
        # 📝 WORDPRESS PUBLISHING
        # ═══════════════════════════════════════════════════════════
        if platform == 'wordpress':
            if not post_id:
                raise HTTPException(status_code=400, detail="post_id is required for WordPress")
            
            if action == 'discard' or action == 'trash':
                print(f"🗑 WordPress: Discarding post {post_id}")
                wp_result = update_and_schedule_post(request, post_id, 'trash')
                return JSONResponse({
                    "status": "Success",
                    "platform": "wordpress",
                    "action": "discarded",
                    "wordpress": wp_result
                })
            
            elif action == 'publish':
                print(f"🔥 WordPress: Publishing post {post_id} immediately")
                wp_result = update_and_schedule_post(request, post_id, 'publish')
                return JSONResponse({
                    "status": "Success",
                    "platform": "wordpress",
                    "action": "published",
                    "wordpress": wp_result
                })
            
            elif action == 'schedule':
                if not publish_time:
                    raise HTTPException(status_code=400, detail="publish_time is required for scheduling")
                
                print(f"🕰 WordPress: Scheduling post {post_id} for {publish_time}")
                wp_result = update_and_schedule_post(request, post_id, 'schedule', publish_time)
                return JSONResponse({
                    "status": "Success",
                    "platform": "wordpress",
                    "action": "scheduled",
                    "scheduled_time": publish_time,
                    "wordpress": wp_result
                })
        
        # ═══════════════════════════════════════════════════════════
        # 📺 YOUTUBE PUBLISHING
        # ═══════════════════════════════════════════════════════════
        elif platform == 'youtube':
            if not all([video_path, video_title, video_description]):
                raise HTTPException(
                    status_code=400, 
                    detail="video_path, video_title, and video_description are required for YouTube"
                )
            
            # Check YouTube authentication
            if not request.session.get('youtube_token'):
                return JSONResponse({
                    "status": "Error",
                    "platform": "youtube",
                    "error": "Not authenticated with YouTube",
                    "message": "Please connect your YouTube account first"
                }, status_code=401)
            
            if action == 'discard':
                print(f"🗑 YouTube: User chose to discard video {video_label or video_path}")
                # Optionally delete the local video file here
                return JSONResponse({
                    "status": "Success",
                    "platform": "youtube",
                    "action": "discarded",
                    "message": "Video discarded (not uploaded)"
                })
            
            elif action == 'publish':
                print(f"📺 YouTube: Publishing video immediately - {video_title}")
                try:
                    youtube_result = await asyncio.to_thread(
                        publish_video_to_youtube,
                        request=request,
                        video_file_path=video_path,
                        title=video_title,
                        description=video_description,
                        privacy="unlisted",  # Options: "public", "unlisted", "private"
                        publish_at=None
                    )
                    
                    return JSONResponse({
                        "status": "Success",
                        "platform": "youtube",
                        "action": "published",
                        "video_url": youtube_result.get("video_url", "N/A"),
                        "video_id": youtube_result.get("video_id", "N/A"),
                        "privacy": youtube_result.get("privacy", "unlisted"),
                        "message": "Video published successfully to YouTube!"
                        })
                
                except HTTPException as http_err:
                            error_msg = http_err.detail
                            print(f"⚠️ YouTube upload failed: {error_msg}")
                            
                            # Handle specific error cases
                            if "Not authenticated" in error_msg or http_err.status_code == 401:
                                message = "YouTube session expired. Please reconnect your account."
                            elif "No YouTube channel" in error_msg:
                                message = "No YouTube channel found. Please create one at youtube.com"
                            elif "quota exceeded" in error_msg.lower():
                                message = "YouTube API quota exceeded. Try again tomorrow."
                            else:
                                message = error_msg
                            
                            return JSONResponse({
                                "status": "Error",
                                "platform": "youtube",
                                "error": error_msg,
                                "message": message
                            }, status_code=http_err.status_code)
                        
                except Exception as e:
                    print(f"❌ YouTube upload error: {str(e)}")
                    return JSONResponse({
                        "status": "Error",
                        "platform": "youtube",
                        "error": str(e),
                        "message": "Failed to upload video to YouTube"
                    }, status_code=500)
                    
            elif action == 'schedule':
                if not publish_time:
                    raise HTTPException(status_code=400, detail="publish_time is required for scheduling")
                
                print(f"🕰 YouTube: Scheduling video for {publish_time} - {video_title}")
                try:
                    youtube_result = await asyncio.to_thread(
                        publish_video_to_youtube,
                        request=request,
                        video_file_path=video_path,
                        title=video_title,
                        description=video_description,
                        privacy="private",  # Scheduled videos are initially private
                        publish_at=publish_time  # ISO 8601 format: "2024-12-25T10:00:00Z"
                    )
                    
                    return JSONResponse({
                        "status": "Success",
                        "platform": "youtube",
                        "action": "scheduled",
                        "scheduled_time": publish_time,
                        "video_url": youtube_result.get("video_url", "N/A"),
                        "video_id": youtube_result.get("video_id", "N/A"),
                        "message": f"Video scheduled for {publish_time}"
                    })
                    
                except Exception as e:
                    print(f"❌ YouTube scheduling error: {str(e)}")
                    return JSONResponse({
                        "status": "Error",
                        "platform": "youtube",
                        "error": str(e),
                        "message": "Failed to schedule video on YouTube"
                    }, status_code=500)
                
        # ═══════════════════════════════════════════════════════════
        # 🐦 X/TWITTER PUBLISHING
        # ═══════════════════════════════════════════════════════════
        elif platform == 'x' or platform == 'twitter':
            if not tweet_text:
                raise HTTPException(status_code=400, detail="tweet_text is required for X/Twitter")
            
            # Check X authentication
            x_session_id = request.session.get(X_SESSION_KEY)
            if not x_session_id:
                return JSONResponse({
                    "status": "Error",
                    "platform": "x",
                    "error": "Not authenticated with X",
                    "message": "Please connect your X/Twitter account first"
                }, status_code=401)
            
            if action == 'discard':
                print(f"🗑 X: User chose to discard post")
                return JSONResponse({
                    "status": "Success",
                    "platform": "x",
                    "action": "discarded",
                    "message": "Post discarded (not published)"
                })
            
            elif action == 'publish':
                print(f"🐦 X: Publishing tweet immediately")
                try:
                    # ✅ NEW: Sanitize image path
                    local_image_path = None
                    if image_path:
                        from urllib.parse import urlparse
                        parsed = urlparse(image_path)
                        clean_path = parsed.path.lstrip('/')  # Remove leading "/"
                        local_image_path = os.path.join(os.getcwd(), clean_path)
                        
                        # Verify file exists
                        if not os.path.exists(local_image_path):
                            print(f"⚠️ Image not found: {local_image_path}")
                            local_image_path = None
                    
                    x_result_url = await upload_and_post_auto(
                        session_input=x_session_id,
                        text=tweet_text,
                        image_path=local_image_path  # ✅ FIXED PATH
                    )
                    
                    # upload_and_post_auto returns a URL string on success, None on failure
                    if x_result_url:
                        return JSONResponse({
                            "status": "Success",
                            "platform": "x",
                            "action": "published",
                            "tweet_url": x_result_url,
                            "message": "Posted successfully to X!"
                        })
                    else:
                        return JSONResponse({
                            "status": "Error",
                            "platform": "x",
                            "error": "Posting failed",
                            "message": "Failed to post to X/Twitter"
                        }, status_code=500)
                    
                except Exception as e:
                    print(f"❌ X posting error: {str(e)}")
                    return JSONResponse({
                        "status": "Error",
                        "platform": "x",
                        "error": str(e),
                        "message": "Failed to post to X/Twitter"
                    }, status_code=500)
            
            elif action == 'schedule':
                if not publish_time:
                    raise HTTPException(status_code=400, detail="publish_time is required for scheduling")
                
                print(f"🕰 X: Scheduling tweet for {publish_time}")
                try:
                    # ✅ NEW: Sanitize image path (same as above)
                    local_image_path = None
                    if image_path:
                        from urllib.parse import urlparse
                        parsed = urlparse(image_path)
                        clean_path = parsed.path.lstrip('/')
                        local_image_path = os.path.join(os.getcwd(), clean_path)
                        
                        if not os.path.exists(local_image_path):
                            print(f"⚠️ Image not found: {local_image_path}")
                            local_image_path = None
                    
                    # Load user session tokens
                    from Campaign.X_publish import load_sessions
                    sessions = load_sessions()
                    user_tokens_dict = sessions.get(x_session_id)
                    
                    if not user_tokens_dict:
                        return JSONResponse({...}, status_code=401)
                    
                    # Schedule the post
                    from Campaign.scheduler_service import schedule_x_post
                    result = await schedule_x_post(
                        session_dict=user_tokens_dict,
                        text=tweet_text,
                        media_path=local_image_path,  # ✅ FIXED PATH
                        publish_time=publish_time
                    )
                    
                    return JSONResponse({
                        "status": "Success",
                        "platform": "x",
                        "action": "scheduled",
                        "scheduled_time": publish_time,
                        "job_id": result.get("job_id", "N/A"),
                        "message": f"Tweet scheduled for {publish_time}"
                    })
                    
                except Exception as e:
                    print(f"❌ X scheduling error: {str(e)}")
                    return JSONResponse({
                        "status": "Error",
                        "platform": "x",
                        "error": str(e),
                        "message": "Failed to schedule tweet"
                    }, status_code=500)
        
            else:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"❌ Error in schedule_post_action: {e}")
        traceback.print_exc()
        return JSONResponse({
            "status": "Error",
            "error": str(e),
            "message": "An unexpected error occurred"
        }, status_code=500)
                