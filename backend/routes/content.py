import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Form, HTTPException, Request
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
    get_groq_client, 
    get_gemini_client, 
    get_tavily_client,
    get_elevenlabs_client, 
    get_fireworks_api_key,
    get_gemini_client_research,
    get_gemini_client_image_prompt,
    get_gemini_client_blog_prompt,
    get_gemini_client_video_1,
    get_gemini_client_video_2,
    get_fireworks_api_key_1,
    get_fireworks_api_key_2,
    get_fireworks_api_key_3,
    get_fireworks_api_key_4,
    X_SESSION_KEY,
    MEDIA_ROOT,
    IMAGE_FOLDER,             
    BASE_VIDEO_ASSETS_DIR       
)
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


@router.post("/analyze_topic")
async def analyze_topic(
    request: Request, 
    topic: str = Form(...), 
    plan: str = Form(...), 
    video_duration: Optional[str] = Form("60s"),
    publish_time: Optional[str] = Form(None)
): 
    """
    STEP 1: Main endpoint with PARALLEL execution of Blog, Image & Video pipelines.
    """
    print("\n" + "="*80)
    print("📥 STEP 1: RECEIVED FORM DATA & START GENERATION")
    print("="*80)
    print(f"Topic: {topic}")
    print(f"Plan: {plan}")
    print(f"Video Duration: {video_duration}")
    print("="*80 + "\n")
    campaign_id = str(uuid.uuid4())
    paths = CampaignPathManager.get_campaign_paths(campaign_id)
    print(f"🚀 Launching Campaign ID: {campaign_id}")
    try:
        # Initialize all clients upfront
        gemini_client = get_gemini_client()
        groq_client = get_groq_client()
        tavily_client = get_tavily_client()
        elevenlabs_client = get_elevenlabs_client() 
        fireworks_api_key = get_fireworks_api_key()
        client_research = get_gemini_client_research()
        client_image_prompt = get_gemini_client_image_prompt()
        client_blog_prompt = get_gemini_client_blog_prompt()
        client_video_1 = get_gemini_client_video_1()
        client_video_2 = get_gemini_client_video_2()
        fireworks_api_key_1 = get_fireworks_api_key_1()
        fireworks_api_key_2 = get_fireworks_api_key_2()
        fireworks_api_key_3 = get_fireworks_api_key_3()
        fireworks_api_key_4 = get_fireworks_api_key_4()

        if not all([fireworks_api_key_1, fireworks_api_key_2, fireworks_api_key_3, fireworks_api_key_4]):
            raise HTTPException(status_code=500, detail="Missing one or more Fireworks API keys")

        print(f"✅ All 4 Fireworks API keys loaded")
        
        if not client_research:
            raise HTTPException(status_code=500, detail="Gemini client (Research key) failed to initialize.")
        
        # 1. Intent Classification (SERIAL)
        strategy_model = classify_and_strategize(topic, client_research)
        
        final_response: Dict[str, Any] = {
            "strategy": strategy_model.model_dump(),
            "plan_used": plan,
            "research_results": "N/A",
            "strategic_brief": "N/A",
            "blog_generation_data": "N/A",
            "final_blog_content": "N/A",
            "blog_hero_image_url": "N/A", 
            "wordpress_status": "N/A", 
            "wordpress_message": "N/A",
            "wordpress_post_id": "N/A",
            "image_prompts": "N/A",
            "generated_image_urls": [],
            "videos": []
        }

        # 2. Handle Image Intent (Simple path)
        if strategy_model.intent == "image":
             
            if not client_image_prompt:
                raise HTTPException(status_code=500, detail="Gemini client (Image Prompt key) failed to initialize.")
            
            # Use a specialized sub-folder for personal assets to keep the root media clean
            personal_assets_path = Path("media/personal") / campaign_id
            personal_assets_path.mkdir(parents=True, exist_ok=True)

            refined_output_model = await asyncio.to_thread(
                generate_image_prompt, topic, client_image_prompt
            )
            final_response["image_prompts"] = [p.model_dump() for p in refined_output_model.prompts]
            
            generated_urls = []
            sanitized_topic = sanitize_topic_for_filename(topic)
            
            for i, refined_prompt_detail in enumerate(refined_output_model.prompts):
                refined_prompt = refined_prompt_detail.prompt
                ratio_str = refined_prompt_detail.aspect_ratio 
                dimensions = map_ratio_to_dimensions(ratio_str)
                width = dimensions['width']
                height = dimensions['height']
                image_filename = f"{sanitized_topic}{uuid.uuid4().hex[:4]}{i+1}.jpeg" 
                
                # --- PREMIUM VS FREE SWITCH ---
                if plan == "premium":
                    # Call Nano Banana Pro for Premium Users
                    image_url_path = generate_image_nano_banana(
                        refined_prompt, 
                        image_filename, 
                        str(personal_assets_path),
                        width=width, 
                        height=height,
                        gemini_client=client_image_prompt
                    )
                else:
                    # Call Fireworks FLUX for Free Users
                    image_url_path = generate_image(
                        refined_prompt, 
                        image_filename, 
                        str(personal_assets_path),
                        width=width, 
                        height=height
                    )
                generated_urls.append(image_url_path)
            
            final_response["generated_image_urls"] = generated_urls
            final_response["message"] = f"Image prompts refined and {len(generated_urls)} images generated."
        
        # 3. Handle Campaign Intent (PARALLEL EXECUTION)
        elif strategy_model.intent == "campaign":
            if plan == "free":
                if strategy_model.requires_research and strategy_model.research_queries:
                    if not client_research:
                        raise HTTPException(status_code=500, detail="Gemini client (Research key) failed to initialize.")
                    
                    # SERIAL: Research Analysis (Foundation for all pipelines)
                    tavily_results = perform_tavily_search(strategy_model.research_queries, tavily_client)
                    final_response["research_results"] = tavily_results
                    strategic_brief_model = perform_research_analysis(topic, tavily_results, client_research)
                    final_response["strategic_brief"] = strategic_brief_model.model_dump()
                    
                    if not client_blog_prompt:
                        raise HTTPException(status_code=500, detail="Gemini client (Blog Prompt key) failed to initialize.")
                    blog_prompt_model = generate_blog_prompt(
                        analysis_brief=strategic_brief_model, 
                        initial_strategy=strategy_model, 
                        gemini_client=client_blog_prompt,
                        original_topic=topic 
                    )
                    final_response["blog_generation_data"] = blog_prompt_model.model_dump()
                    
                    # ═══════════════════════════════════════════════════════════
                    # 🔥 PARALLEL EXECUTION: Blog, Ad Images, Video
                    # ═══════════════════════════════════════════════════════════
                    
                    async def blog_pipeline():
                        """Blog content + hero image generation"""
                        blog_image_local_path = None
                        try:
                            print(f"\n🖼 [BLOG] Starting hero image generation...")
                            blog_image_url, blog_image_local_path = await asyncio.to_thread(
                                generate_blog_image,
                                image_prompt=blog_prompt_model.visual_image_prompt,
                                campaign_id=campaign_id 
                            )
                            print(f"✅ [BLOG] Hero image generated!")
                        except Exception as e:
                            print(f"❌ [BLOG] Hero image failed: {str(e)}")
                            blog_image_url = f"Image generation failed: {str(e)}"
                        
                        final_blog_text = await asyncio.to_thread(
                            generate_final_blog_content,
                            blog_prompt_data=blog_prompt_model,
                            groq_client=groq_client
                        )
                        print("✅ [BLOG] Content generation complete!")
                        return {
                            "blog_content": final_blog_text,
                            "blog_image_url": blog_image_url,
                            "blog_image_path": blog_image_local_path
                        }

                    async def ad_image_pipeline():
                        """Advertisement image generation"""
                        print("\n🖼 [AD IMAGES] Starting generation...")
                        required_image_count = strategy_model.image_count
                        if not client_image_prompt:
                            raise HTTPException(status_code=500, detail="Gemini client (Image Prompt key) failed.")
                        
                        image_prompt_list_model = await asyncio.to_thread(
                            generate_image_prompts,
                            analysis_brief=strategic_brief_model,
                            gemini_client=client_image_prompt,
                            required_image_count=required_image_count
                        )
                        
                        generated_ad_assets = await asyncio.to_thread(
                            generate_all_ad_images,
                            image_prompt_list=image_prompt_list_model,
                           campaign_id=campaign_id 
                        )
                        print(f"✅ [AD IMAGES] {len(generated_ad_assets)} assets generated!")
                        return {
                            "image_prompts": [p.model_dump() for p in image_prompt_list_model.prompts],
                            "generated_urls": [
                                asset.get('image_url') for asset in generated_ad_assets 
                                if asset.get('image_url') and 'error' not in asset
                            ],
                            "ad_assets_details": generated_ad_assets
                        }
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
                    async def video_pipeline(duration_s: int, label: str, fireworks_api_key: str, api_key_num: int, request: Request, paths: Dict, bg_music_path: Path = None):
                        """
                        🔥 FIXED: Video generation WITHOUT immediate YouTube upload
                        Now stores metadata for later publishing via /schedule_post endpoint
                        """
                        if not elevenlabs_client or not fireworks_api_key:
                            print(f"❌ [VIDEO - {label}] Skipping: Missing API config")
                            return {"status": "Skipped", "label": label, "error": "Missing API Config"}
                        
                        # 1. Path Isolation: Create unique workspace
                        # Map label to correct campaign path
                        path_mapping = {
                            "LONG_FORM": paths["long_form"],
                            "SHORT_1": paths["short_1"],
                            "SHORT_2": paths["short_2"],
                            "SHORT_3": paths["short_3"]
                        }
                        variant_dir = path_mapping[label]
                        # Directories already created by CampaignPathManager, but ensure images subfolder exists
                        (variant_dir / "images").mkdir(parents=True, exist_ok=True)
                        
                        audio_path = variant_dir / f"{label}_audio.mp3"
                        srt_path = variant_dir / f"{label}_captions.srt"
                        final_video_path = variant_dir / f"{label}_final.mp4"

                        try:
                            print(f"\n🎥 [VIDEO - {label}] Starting {duration_s}s pipeline with API Key #{api_key_num}...")
                            
                            # Step A: Bible & Script
                            video_bible_model = await asyncio.to_thread(
                                generate_video_bible, strategic_brief_model, strategy_model.keywords, client_video_1
                            )
                            
                            script_model = await asyncio.to_thread(
                                generate_video_script, video_bible_model, strategic_brief_model, duration_s, client_video_2, topic
                            )

                            # Step B: Audio
                            audio_sync_output = await asyncio.to_thread(
                                generate_audio_and_timestamps,
                                full_narration_text=script_model.full_narration,
                                google_client=get_tts_client(),
                                output_audio_path=audio_path
                            )
                            
                            # Step C: Storyboard & Prompts
                            await asyncio.to_thread(generate_srt, audio_sync_output.timestamps, srt_path)
                            ffmpeg_srt_path = get_ffmpeg_compatible_path(str(srt_path))

                            storyboard_model = await asyncio.to_thread(
                                generate_storyboard, script_model.full_narration, audio_sync_output, video_bible_model, strategic_brief_model, client_video_1
                            )
                            
                            optimized_prompts = await asyncio.to_thread(
                                optimize_video_prompts_batch, storyboard_model.scenes, video_bible_model.video_bible, client_video_2
                            )

                            # Step D: Images (Using rate-limited Fireworks call)
                            await rate_limited_fireworks_call(
                                generate_campaign_images,
                                api_key_num,
                                optimized_prompts,
                                fireworks_api_key,
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
                            
                            # ═══════════════════════════════════════════════════════════
                            # ✅ FIXED: STORE METADATA WITHOUT UPLOADING
                            # ═══════════════════════════════════════════════════════════
                            
                            # Check YouTube connection status (but don't upload yet)
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
                    # 🚀 PARALLEL VIDEO GENERATION WITH 4 API KEYS
                    # ═══════════════════════════════════════════════════════════
                    print("\n🎥 Starting 4 videos in parallel with separate API keys...")

                    video_tasks = [
                        video_pipeline(45, "LONG_FORM", fireworks_api_key_1, api_key_num=1, request=request, paths=paths, bg_music_path=bg_music_path),
                        video_pipeline(10, "SHORT_3", fireworks_api_key_2, api_key_num=2, request=request, paths=paths, bg_music_path=bg_music_path),
                        video_pipeline(15, "SHORT_2", fireworks_api_key_3, api_key_num=3, request=request, paths=paths, bg_music_path=bg_music_path),
                        video_pipeline(10, "SHORT_1", fireworks_api_key_4, api_key_num=4, request=request, paths=paths, bg_music_path=bg_music_path)
                    ]
                                        
                    results = await asyncio.gather(
                        blog_pipeline(),
                        ad_image_pipeline(),
                        *video_tasks,
                        return_exceptions=True
                    )

                    blog_result = results[0]
                    ad_image_result = results[1]
                    video_results = results[2:]  # All 4 video results

                    # ═══════════════════════════════════════════════════════════
                    # 📊 PROCESS ALL RESULTS
                    # ═══════════════════════════════════════════════════════════
                    
                    # Process Blog Results
                    if isinstance(blog_result, Exception):
                        print(f"❌ Blog pipeline failed: {blog_result}")
                        final_response["blog_status"] = "Failed"
                        final_response["blog_error"] = str(blog_result)
                        blog_image_local_path = None
                    else:
                        final_response["final_blog_content"] = blog_result["blog_content"]
                        final_response["blog_hero_image_url"] = blog_result["blog_image_url"]
                        blog_image_local_path = blog_result["blog_image_path"]
                    
                    # Process Ad Image Results
                    if isinstance(ad_image_result, Exception):
                        print(f"❌ Ad image pipeline failed: {ad_image_result}")
                        final_response["image_status"] = "Failed"
                    else:
                        final_response["image_prompts"] = ad_image_result["image_prompts"]
                        final_response["generated_image_urls"] = ad_image_result["generated_urls"]
                        final_response["generated_ad_assets_details"] = ad_image_result["ad_assets_details"]
                    
                    # Process Video Results (ALL 4 VIDEOS) - NO UPLOAD STATUS
                    final_response["videos"] = []
                    for i, video_result in enumerate(video_results):
                        if isinstance(video_result, Exception):
                            print(f"❌ Video {i+1} failed: {video_result}")
                            final_response["videos"].append({
                                "status": "Failed",
                                "error": str(video_result)
                            })
                        elif video_result.get("status") == "Generated":
                            video_data = {
                                "label": video_result.get("label"),
                                "duration": video_result.get("duration"),
                                "title": video_result.get("title"),
                                "video_url": video_result.get("video_url"),
                                "video_path": video_result.get("video_path"),
                                "description": video_result.get("description"),
                                "status": "Generated",
                                "youtube_upload_data": video_result.get("youtube_upload_data", {})
                            }
                            final_response["videos"].append(video_data)
                        else:
                            final_response["videos"].append(video_result)
                    
                    # Summary counts
                    successful_videos = sum(1 for v in final_response["videos"] if v.get("status") == "Generated")
                    
                    final_response["video_summary"] = {
                        "total": 4,
                        "generated": successful_videos,
                        "ready_to_publish": successful_videos
                    }
                    
                    print(f"\n✅ Video Generation: {successful_videos}/4 successful - Ready for publishing")
                    
                    # WordPress Draft Creation (only if blog succeeded)
                    if not isinstance(blog_result, Exception) and blog_image_local_path:
                        try:
                            print("\n📝 Creating WordPress draft...")
                            draft_data = create_draft_post_to_wordpress(
                                request=request,
                                title=blog_prompt_model.title,
                                content=blog_result["blog_content"],
                                featured_image_path=blog_image_local_path
                            )
                            final_response["wordpress_status"] = "Draft Created"
                            final_response["wordpress_message"] = "Content saved as DRAFT."
                            final_response["wordpress_post_id"] = draft_data['post_id']
                            final_response["wordpress_url"] = draft_data['post_url']
                            print(f"✅ Draft created: Post ID {draft_data['post_id']}")
                        except Exception as e:
                            print(f"❌ Draft creation failed: {str(e)}")
                            final_response["wordpress_status"] = "Failed"
                            final_response["wordpress_message"] = f"Draft failed: {str(e)}"
                    
                    # X Draft Preparation
                    x_session_id = request.session.get(X_SESSION_KEY)
                    final_response["x_draft"] = {
                        "text": f"🚀 {blog_prompt_model.title}\n\nCheck out our latest insights!",
                        "media_path": str(blog_image_local_path) if blog_image_local_path else None
                    }
                    final_response["x_status"] = "Draft Ready" if x_session_id else "X Not Connected"
                    final_response["message"] = f"Campaign complete: {successful_videos}/4 videos generated and ready to publish."
            
            # ═══════════════════════════════════════════════════════════
            # 🌟 PREMIUM PLAN: HIGH-FIDELITY CAMPAIGN PIPELINE
            # ═══════════════════════════════════════════════════════════
            elif plan == "premium":
                print("\n" + "⭐"*40)
                print("🚀 STARTING PREMIUM CAMPAIGN PIPELINE (NANO BANANA)")
                print("⭐"*40)

                # 1. Mandatory Research & Analysis
                if not client_research:
                    raise HTTPException(status_code=500, detail="Gemini client (Research) failed.")
                
                tavily_results = perform_tavily_search(strategy_model.research_queries, tavily_client)
                final_response["research_results"] = tavily_results
                
                strategic_brief_model = perform_research_analysis(topic, tavily_results, client_research)
                final_response["strategic_brief"] = strategic_brief_model.model_dump()
                
                # 2. Generate Premium Blog & Image Prompts
                if not client_blog_prompt:
                    raise HTTPException(status_code=500, detail="Gemini client (Blog Prompt) failed.")
                
                blog_prompt_model = generate_blog_prompt(
                    analysis_brief=strategic_brief_model, 
                    initial_strategy=strategy_model, 
                    gemini_client=client_blog_prompt,
                    original_topic=topic 
                )
                final_response["blog_generation_data"] = blog_prompt_model.model_dump()

                # ═══════════════════════════════════════════════════════════
                # 🔥 PREMIUM PARALLEL PIPELINES (Blog & Ad Images)
                # ═══════════════════════════════════════════════════════════

                async def premium_blog_pipeline():
                    """Premium: Blog text + Nano Banana Hero Image"""
                    blog_image_local_path = None
                    try:
                        print(f"🖼 [PREMIUM BLOG] Generating Nano Banana Hero Image...")
                        # Call your premium blog image function
                        blog_image_url, blog_image_local_path = await asyncio.to_thread(
                            generate_blog_image_premium, 
                            image_prompt=blog_prompt_model.visual_image_prompt,
                            campaign_id=campaign_id,
                            gemini_client=client_image_prompt
                        )
                    except Exception as e:
                        print(f"❌ [PREMIUM BLOG IMAGE] Failed: {e}")
                        blog_image_url = "N/A"

                    # Generate High-Tier Blog Content
                    final_blog_text = await asyncio.to_thread(
                        generate_final_blog_content,
                        blog_prompt_data=blog_prompt_model,
                        groq_client=groq_client
                    )
                    return {
                        "blog_content": final_blog_text,
                        "blog_image_url": blog_image_url,
                        "blog_image_path": blog_image_local_path
                    }

                async def premium_ad_image_pipeline():
                    """Premium: Ad Assets using Nano Banana"""
                    print("🖼 [PREMIUM AD IMAGES] Starting Nano Banana Generation...")
                    required_image_count = strategy_model.image_count
                    
                    image_prompt_list_model = await asyncio.to_thread(
                        generate_image_prompts,
                        analysis_brief=strategic_brief_model,
                        gemini_client=client_image_prompt,
                        required_image_count=required_image_count
                    )
                    
                    # Call your premium ad asset orchestrator
                    generated_ad_assets = await asyncio.to_thread(
                        generate_all_ad_images_premium,
                        image_prompt_list=image_prompt_list_model,
                        gemini_client=client_image_prompt,
                        campaign_id=campaign_id 
                    )
                    
                    return {
                        "image_prompts": [p.model_dump() for p in image_prompt_list_model.prompts],
                        "generated_urls": [asset.get('image_url') for asset in generated_ad_assets if 'error' not in asset],
                        "ad_assets_details": generated_ad_assets
                    }

                # 3. Parallel Execution
                # (Video tasks skipped for now per your request)
                results = await asyncio.gather(
                    premium_blog_pipeline(),
                    premium_ad_image_pipeline(),
                    return_exceptions=True
                )

                # 4. Process Results
                blog_res = results[0]
                ad_res = results[1]

                # Process Blog
                if not isinstance(blog_res, Exception):
                    final_response["final_blog_content"] = blog_res["blog_content"]
                    final_response["blog_hero_image_url"] = blog_res["blog_image_url"]
                    blog_image_local_path = blog_res["blog_image_path"]
                
                # Process Ad Images
                if not isinstance(ad_res, Exception):
                    final_response["image_prompts"] = ad_res["image_prompts"]
                    final_response["generated_image_urls"] = ad_res["generated_urls"]
                    final_response["generated_ad_assets_details"] = ad_res["ad_assets_details"]

                # 5. WordPress & X Draft Preparation (Shared Logic)
                if not isinstance(blog_res, Exception) and blog_image_local_path:
                    try:
                        draft_data = create_draft_post_to_wordpress(
                            request=request,
                            title=blog_prompt_model.title,
                            content=blog_res["blog_content"],
                            featured_image_path=blog_image_local_path
                        )
                        final_response["wordpress_status"] = "Draft Created"
                        final_response["wordpress_post_id"] = draft_data['post_id']
                        final_response["wordpress_url"] = draft_data['post_url']
                    except Exception as e:
                        final_response["wordpress_status"] = f"Failed: {e}"

                # X/Twitter Draft
                x_session_id = request.session.get(X_SESSION_KEY)
                final_response["x_draft"] = {
                    "text": f"🚀 {blog_prompt_model.title}\n\nGenerated with Premium AI.",
                    "media_path": str(blog_image_local_path) if blog_image_local_path else None
                }
                final_response["x_status"] = "Draft Ready" if x_session_id else "X Not Connected"
                final_response["message"] = "Premium Campaign Assets Generated Successfully via Nano Banana."
        
        return JSONResponse(content=final_response)

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
                    # Fix: upload_and_post_auto expects 'session_input' not 'session_id'
                    x_result_url = await upload_and_post_auto(
                        session_input=x_session_id,  # ✅ Correct parameter name
                        text=tweet_text,
                        image_path=image_path
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
                    # Load user session tokens
                    from Campaign.X_publish import load_sessions
                    sessions = load_sessions()
                    user_tokens_dict = sessions.get(x_session_id)
                    
                    if not user_tokens_dict:
                        return JSONResponse({
                            "status": "Error",
                            "platform": "x",
                            "error": "Session not found",
                            "message": "X credentials not found. Please reconnect."
                        }, status_code=401)
                    
                    # Schedule the post using your existing scheduler
                    from Campaign.scheduler_service import schedule_x_post
                    result = await schedule_x_post(
                        session_dict=user_tokens_dict,
                        text=tweet_text,
                        media_path=image_path,
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
                