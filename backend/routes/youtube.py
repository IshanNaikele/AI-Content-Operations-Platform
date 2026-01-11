from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional

from Campaign.youtube_publish import (
    get_youtube_authorization_url,
    handle_youtube_oauth_callback,
    is_youtube_connected,
    disconnect_youtube,
    verify_youtube_channel,
    publish_video_to_youtube,
)

router = APIRouter()

# --- AUTHENTICATION ENDPOINTS ---

@router.get("/youtube/login")
async def youtube_login(request: Request):
    """Initiate YouTube OAuth 2.0 login."""
    try:
        auth_url = get_youtube_authorization_url(request)
        return RedirectResponse(url=auth_url, status_code=307)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth URL generation failed: {str(e)}")


@router.get("/youtube/callback")
async def youtube_callback(
    request: Request, 
    state: Optional[str] = None, 
    code: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle OAuth callback and store credentials."""
    try:
        handle_youtube_oauth_callback(request, state, code, error)
        return RedirectResponse(url="/?youtube_status=connected", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/?youtube_error={e.detail}", status_code=303)


@router.post("/youtube/disconnect")
async def youtube_disconnect(request: Request):
    """Disconnect YouTube account."""
    result = disconnect_youtube(request)
    return JSONResponse(result)


@router.get("/youtube/status")
async def youtube_status(request: Request):
    """Check YouTube connection and channel status."""
    is_connected = is_youtube_connected(request)
    
    response_data = {
        "is_connected": is_connected,
        "channel_info": None
    }
    
    if is_connected:
        # CRITICAL FIX: Don't disconnect on verification failure
        channel_data = verify_youtube_channel(request)
        response_data["channel_info"] = channel_data
        
        # Update connection status based on verification
        # If channel verification explicitly shows the token is bad, mark as disconnected
        if not channel_data.get("success") and channel_data.get("error_code") == 401:
            response_data["is_connected"] = False
            response_data["needs_reconnect"] = True
    
    return JSONResponse(response_data)


# --- UPLOAD & SCHEDULING ENDPOINT ---

@router.post("/youtube/upload_and_schedule")
async def upload_and_schedule_video(
    request: Request,
    video_file_url: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(""),
    privacy: Optional[str] = Form("unlisted"),
    publish_time: Optional[str] = Form(None)
):
    """Upload video to YouTube with optional scheduling."""
    try:
        # Convert URL path to local file path
        local_video_path = video_file_url.lstrip('/')
        
        upload_result = publish_video_to_youtube(
            request=request,
            video_file_path=local_video_path,
            title=title,
            description=description,
            privacy=privacy,
            publish_at=publish_time
        )
        
        return JSONResponse(upload_result)
    
    except HTTPException as e:
        return JSONResponse({"error": e.detail}, status_code=e.status_code)
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return JSONResponse(
            {"error": "Upload failed", "details": str(e)}, 
            status_code=500
        )