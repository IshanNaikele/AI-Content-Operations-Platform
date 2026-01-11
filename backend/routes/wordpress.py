import secrets
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from config import OAUTH_STATE_KEY
from  Campaign.wordpress_publish import (
    get_authorization_url,
    handle_oauth_callback_exchange,
    is_wordpress_connected,
    disconnect_wordpress,
    save_persistent_credentials
)

router = APIRouter()
@router.get("/status")
async def get_wordpress_status(request: Request):
    """Check if the user is currently connected (checks file + session)."""
    return {"connected": is_wordpress_connected(request)}

@router.get("/connect_wordpress")
async def connect_wordpress(request: Request):
    """Initiate WordPress OAuth flow"""
    try:
        state = secrets.token_urlsafe(32)
        request.session[OAUTH_STATE_KEY] = state
        
        print(f"DEBUG: Setting state in session: {state}")
        print(f"DEBUG: Session after set: {dict(request.session)}")
        
        auth_url = get_authorization_url(state)
        
        return RedirectResponse(url=auth_url, status_code=307)
        
    except HTTPException as e:
        return JSONResponse({"error": "Configuration Error", "details": e.detail}, status_code=500)
    
@router.post("/disconnect")
async def handle_disconnect(request: Request):
    """Trigger the full disconnect logic."""
    return disconnect_wordpress(request)

@router.get("/callback")
async def wordpress_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle WordPress OAuth callback"""
    session_state = request.session.get(OAUTH_STATE_KEY)
    
    print(f"DEBUG: Received state: {state}")
    print(f"DEBUG: Session state: {session_state}")
    
    if error:
        return RedirectResponse(url=f"/?wp_error=Authorization%20denied", status_code=303)
        
    if not state or state != session_state:
        return RedirectResponse(url=f"/?wp_error=Invalid%20state", status_code=303)

    if not code:
        return RedirectResponse(url=f"/?wp_error=No%20code", status_code=303)
        
    try:
        auth_data = handle_oauth_callback_exchange(
            code=code,
            state=state,
            expected_state=session_state
        )
         
        save_persistent_credentials(
            access_token=request.session.get('wp_access_token'),
            blog_id=request.session.get('wp_blog_id'),
            user_sites=request.session.get('wp_user_sites')
        )
        request.session['wp_access_token'] = auth_data['access_token']
        request.session['wp_blog_id'] = auth_data['blog_id']
        
        return RedirectResponse(url=f"/?wp_status=connected", status_code=303)
        
    except HTTPException as e:
        return RedirectResponse(url=f"/?wp_error={e.detail}", status_code=303)