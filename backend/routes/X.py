import secrets
import os
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from urllib.parse import urlparse
from typing import Optional

# Import keys and constants from config
from config import X_API_KEY, X_API_KEY_SECRET, X_SESSION_KEY, APP_URL
from Campaign.scheduler_service import schedule_x_post, scheduler
# Import the logic from X_publish
from Campaign.X_publish import (
    load_sessions, save_session, 
    delete_session, upload_and_post, tweepy
)

router = APIRouter(prefix="/x", tags=["X Publishing"])

# Temporary store for OAuth tokens (Shared with routes/static.py)
pending_auth = {}

@router.get("/login")
async def x_login(request: Request):
    """Step 1: Initiate OAuth 1.0a Flow matching your Portal settings"""
    # CRITICAL: We hardcode the callback to http://localhost:8000/ to match your screenshot
    callback_url = "http://localhost:8000/"
    
    auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_KEY_SECRET, callback=callback_url)
    try:
        url = auth.get_authorization_url(signin_with_twitter=True)
        # Store the secret temporarily
        pending_auth[auth.request_token['oauth_token']] = auth.request_token['oauth_token_secret']
        return RedirectResponse(url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"X Login Error: {str(e)}")

@router.post("/x_action")
async def x_action(
    request: Request,
    action: str = Form(...),
    tweet_text: str = Form(...),
    media_path: str = Form(...),
    publish_time: Optional[str] = Form(None),
    job_id: Optional[str] = Form(None)  # Added to track scheduled jobs for discarding
):
    # 1. Session Verification
    session_id = request.session.get(X_SESSION_KEY)
    if not session_id:
        raise HTTPException(status_code=401, detail="X not connected. Please login first.")

    # 2. Path Sanitization: Extract local path if a full URL is provided
    # If media_path is "http://localhost:8000/personal_image/pic.jpg", 
    # parsed.path becomes "/personal_image/pic.jpg"
    parsed = urlparse(media_path)
    clean_path = parsed.path.lstrip('/')
    local_media_path = os.path.join(os.getcwd(), clean_path)

    if action == 'publish':
        print(f"🚀 [X] Immediate Publish Triggered")
        result = await upload_and_post(session_id, tweet_text, local_media_path)
        return JSONResponse(result)

    elif action == 'schedule' and publish_time:
        print(f"⏰ [X] Scheduling Triggered for {publish_time}")
        
        sessions = load_sessions()
        user_tokens_dict = sessions.get(session_id)
        
        if not user_tokens_dict:
            raise HTTPException(status_code=401, detail="X credentials not found.")

        # Schedule the post and get the job ID
        result = await schedule_x_post(
            session_dict=user_tokens_dict, 
            text=tweet_text, 
            media_path=local_media_path, 
            publish_time=publish_time
        )
        return JSONResponse(result)

    elif action == 'discard':
        print(f"🗑️ [X] Discard Action Triggered")
        
        # If a job_id was passed, remove it from the scheduler
        if job_id:
            try:
                scheduler.remove_job(job_id)
                print(f"✅ Job {job_id} cancelled.")
            except:
                print(f"⚠️ Job {job_id} not found or already executed.")

        # Cleanup: Only delete if it's a specific temporary file
        if "temp_" in local_media_path and os.path.exists(local_media_path):
            os.remove(local_media_path)
            
        return {"status": "discarded", "message": "Post cleared and resources cleaned."}

@router.get("/status")
async def x_status(request: Request):
    session_id = request.session.get(X_SESSION_KEY)
    if not session_id: return {"connected": False}
    
    sessions = load_sessions()
    if session_id in sessions:
        user_data = sessions[session_id]
        return {
            "connected": True, 
            "username": user_data['screen_name'],
            "profile_image": user_data['profile_image']
        }
    return {"connected": False}

@router.post("/disconnect")
async def x_disconnect(request: Request):
    session_id = request.session.get(X_SESSION_KEY)
    if session_id:
        delete_session(session_id)
        request.session.pop(X_SESSION_KEY, None)
    return {"message": "Disconnected"}