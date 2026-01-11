from fastapi import Request, HTTPException
from starlette.responses import RedirectResponse
import os
from typing import Optional, Dict, Any
from  config import (
    get_youtube_client_id, 
    get_youtube_client_secret, 
    get_youtube_redirect_uri
)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request as GoogleRequest

# Configuration
G_CLIENT_ID = get_youtube_client_id()
G_CLIENT_SECRET = get_youtube_client_secret()
G_REDIRECT_URI = get_youtube_redirect_uri()
YOUTUBE_SCOPE = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

CLIENT_CONFIG = {
    "web": {
        "client_id": G_CLIENT_ID,
        "client_secret": G_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [G_REDIRECT_URI],
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }
}


def get_youtube_service(request: Request) -> Optional[Any]:
    """Rebuild YouTube service from session credentials."""
    token_data = request.session.get('youtube_token')
    if not token_data:
        return None
    
    try:
        creds = Credentials(
            token=token_data['token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            print("⏳ Refreshing YouTube token...")
            creds.refresh(GoogleRequest())
            # CRITICAL FIX: Save refreshed token back to session
            request.session['youtube_token'] = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': list(creds.scopes)
            }
            print("✅ Token refreshed and saved.")
        
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Service build failed: {e}")
        return None


def get_youtube_authorization_url(request: Request) -> str:
    """Generate YouTube OAuth URL."""
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=YOUTUBE_SCOPE)
    flow.redirect_uri = G_REDIRECT_URI
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    request.session['google_oauth_state'] = state
    print("🔗 Redirecting to Google OAuth...")
    return authorization_url


def handle_youtube_oauth_callback(
    request: Request,
    state: Optional[str] = None,
    code: Optional[str] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Handle OAuth callback and store credentials."""
    if error:
        raise HTTPException(status_code=403, detail=f"Authorization failed: {error}")
    
    stored_state = request.session.get('google_oauth_state')
    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="State mismatch - CSRF protection")
    
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=YOUTUBE_SCOPE, state=state)
    flow.redirect_uri = G_REDIRECT_URI
    
    try:
        flow.fetch_token(authorization_response=str(request.url))
        creds = flow.credentials
        
        # Store in session
        request.session['youtube_token'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes)
        }
        request.session.pop('google_oauth_state', None)
        print("✅ YouTube connected successfully!")
        
        return {"success": True, "message": "Connected to YouTube"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


def disconnect_youtube(request: Request) -> Dict[str, Any]:
    """Disconnect YouTube account."""
    request.session.pop('youtube_token', None)
    print("🔌 YouTube disconnected")
    return {"success": True, "message": "Disconnected from YouTube"}


def is_youtube_connected(request: Request) -> bool:
    """Check if YouTube is connected."""
    return 'youtube_token' in request.session


def verify_youtube_channel(request: Request) -> Dict[str, Any]:
    """Verify YouTube channel exists - DON'T delete token on failure."""
    youtube = get_youtube_service(request)
    if not youtube:
        # Return failure status but DON'T clear token
        return {
            "success": False,
            "has_channel": False,
            "message": "Could not build YouTube service. Token may need refresh."
        }
    
    try:
        response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
        
        if response.get('items'):
            channel = response['items'][0]
            return {
                "success": True,
                "has_channel": True,
                "channel_name": channel['snippet']['title'],
                "channel_id": channel['id'],
                "subscriber_count": channel['statistics'].get('subscriberCount', '0')
            }
        else:
            # No channel found - token is valid but no channel exists
            return {
                "success": False,
                "has_channel": False,
                "message": "No YouTube channel found. Please create one at youtube.com"
            }
    except HttpError as e:
        error_msg = e.content.decode() if e.content else "Unknown error"
        print(f"⚠️ Channel verification failed: {error_msg}")
        # CRITICAL FIX: Don't clear token, just return error info
        return {
            "success": False,
            "has_channel": False,
            "message": f"API Error: {error_msg}",
            "error_code": e.resp.status
        }


def sanitize_youtube_title(title: str, max_length: int = 100) -> str:
    """Sanitize title for YouTube."""
    clean_title = ' '.join(title.split())
    if len(clean_title) > max_length:
        clean_title = clean_title[:max_length].rsplit(' ', 1)[0]
    return clean_title.strip() or "Generated Video"


def publish_video_to_youtube(
    request: Request,
    video_file_path: str,
    title: str,
    description: str = "",
    privacy: str = "unlisted",
    publish_at: Optional[str] = None
) -> Dict[str, Any]:
    """Upload video to YouTube with optional scheduling."""
    youtube = get_youtube_service(request)
    if not youtube:
        raise HTTPException(status_code=401, detail="Not authenticated. Please reconnect.")
    
    if not os.path.exists(video_file_path):
        raise HTTPException(status_code=404, detail=f"Video file not found: {video_file_path}")
    
    # Determine status
    status_payload = {}
    if publish_at:
        status_payload['privacyStatus'] = 'private'
        status_payload['publishAt'] = publish_at
        print(f"🗓 Scheduling for: {publish_at}")
    else:
        status_payload['privacyStatus'] = privacy if privacy in ['public', 'unlisted', 'private'] else 'unlisted'
        print(f"🔥 Publishing immediately (Privacy: {status_payload['privacyStatus']})")
    
    video_metadata = {
        'snippet': {
            'title': sanitize_youtube_title(title),
            'description': description,
            'categoryId': '22'
        },
        'status': status_payload
    }
    
    try:
        print("📤 Starting upload...")
        media = MediaFileUpload(video_file_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
        upload_request = youtube.videos().insert(part="snippet,status", body=video_metadata, media_body=media)
        
        response = None
        while response is None:
            status, response = upload_request.next_chunk()
            if status:
                print(f"   Progress: {int(status.progress() * 100)}%")
        
        video_id = response.get('id')
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"✅ Upload complete: {video_url}")
        
        return {
            "success": True,
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "video_url": video_url,
            "title": video_metadata['snippet']['title'],
            "privacy": status_payload.get('privacyStatus'),
            "scheduled_at": status_payload.get('publishAt', 'N/A')
        }
    except HttpError as e:
        error_content = e.content.decode() if e.content else "Unknown error"
        print(f"❌ YouTube API Error: {error_content}")
        
        if "youtubeSignupRequired" in error_content:
            raise HTTPException(status_code=403, detail="No YouTube channel. Create one first.")
        elif "quotaExceeded" in error_content:
            raise HTTPException(status_code=403, detail="API quota exceeded. Try tomorrow.")
        
        raise HTTPException(status_code=e.resp.status, detail=f"Upload failed: {error_content}")
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")