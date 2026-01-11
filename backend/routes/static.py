from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import tweepy
from config import X_API_KEY, X_API_KEY_SECRET, X_SESSION_KEY, BASE_DIR
from routes.X import pending_auth, save_session, X_SESSION_KEY
import secrets
from pathlib import Path
import os

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def get_form(request: Request, oauth_token: str = None, oauth_verifier: str = None):
    """
    Serves the main UI and handles the X (Twitter) OAuth 1.0a callback 
    directly on the root URL to match the Developer Portal settings.
    """
    
    # 1. Check if this is a callback from X
    if oauth_token and oauth_verifier:
        try:
            # Retrieve the secret we stored during the /x/login step
            token_secret = pending_auth.get(oauth_token)
            if not token_secret:
                return RedirectResponse(url="/?x_error=session_expired")

            # Initialize the handler to exchange the verifier for an Access Token
            auth = tweepy.OAuth1UserHandler(X_API_KEY, X_API_KEY_SECRET)
            auth.request_token = {
                'oauth_token': oauth_token, 
                'oauth_token_secret': token_secret
            }

            access_token, access_token_secret = auth.get_access_token(oauth_verifier)
            
            # Verify credentials to get user details for the UI
            api = tweepy.API(auth)
            user = api.verify_credentials()

            # Generate a unique session ID for your JSON storage
            session_id = secrets.token_urlsafe(16)
            save_session(session_id, {
                "access_token": access_token,
                "access_token_secret": access_token_secret,
                "screen_name": user.screen_name,
                "profile_image": user.profile_image_url_https
            })

            # Store the session ID in the browser cookie
            request.session[X_SESSION_KEY] = session_id
            
            # Clean up the temporary pending storage
            if oauth_token in pending_auth:
                del pending_auth[oauth_token]

            # Redirect to the root WITHOUT the query parameters for a clean URL
            return RedirectResponse(url="/?x_status=connected")

        except Exception as e:
            print(f"Callback Error: {e}")
            return RedirectResponse(url=f"/?x_error=auth_failed")
    index_path = BASE_DIR / "index.html"
    # 2. Standard flow: Serve the index.html
    try:
        with open(index_path, "r", encoding='utf-8') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        print(f"CRITICAL: index.html not found at {index_path}")
        return HTMLResponse(content="<h1>index.html not found! Check server logs.</h1>", status_code=500)