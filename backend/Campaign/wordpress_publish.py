import os
import requests
import secrets
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode
from fastapi import HTTPException, Request
from datetime import datetime
import json # Import json for response debugging
from pathlib import Path
# 1. Absolute Imports from root config
from  config import DATA_ROOT, MEDIA_ROOT
from config import get_wordpress_credentials

CLIENT_ID, CLIENT_SECRET = get_wordpress_credentials()
# Configure logging for better debugging
logger = logging.getLogger(__name__)
REDIRECT_URI = "http://localhost:8000/callback"
# Add validation:
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("WordPress credentials not configured in environment")

# WordPress API Endpoints
AUTHORIZATION_URL = "https://public-api.wordpress.com/oauth2/authorize"
TOKEN_URL = "https://public-api.wordpress.com/oauth2/token"
MEDIA_API_TEMPLATE = "https://public-api.wordpress.com/rest/v1.1/sites/{blog_id}/media/new"
# Base template for posts (new or specific ID)
POST_API_BASE_TEMPLATE = "https://public-api.wordpress.com/rest/v1.1/sites/{blog_id}/posts/{post_id}"
WP_CREDENTIALS_PATH = DATA_ROOT / "wp_token_store.json"

# --- HELPER FUNCTIONS (RETAINED) ---
def save_persistent_credentials(access_token: str, blog_id: str, user_sites: list = None):
    """Saves credentials to a local file so they stay 'connected' forever."""
    data = {
        "access_token": access_token,
        "blog_id": blog_id,
        "user_sites": user_sites or []
    }
    with open(WP_CREDENTIALS_PATH, "w") as f:
        json.dump(data, f)

def get_session_data(request: Request) -> Dict[str, Any]:
    """Safely extract WordPress data, falling back to persistent storage."""
    # 1. Try to get from session first
    data = {
        'access_token': request.session.get('wp_access_token'),
        'blog_id': request.session.get('wp_blog_id'),
        'user_sites': request.session.get('wp_user_sites', [])
    }
    
    # 2. If session is empty, check the persistent file
    if not data['access_token'] and os.path.exists(WP_CREDENTIALS_PATH):
        try:
            with open(WP_CREDENTIALS_PATH, "r") as f:
                stored = json.load(f)
                # Restore into session for the current request
                request.session['wp_access_token'] = stored.get('access_token')
                request.session['wp_blog_id'] = stored.get('blog_id')
                request.session['wp_user_sites'] = stored.get('user_sites', [])
                return stored
        except Exception as e:
            logger.error(f"Failed to read persistent WP credentials: {e}")
            
    return data

def is_wordpress_connected(request: Request) -> bool:
    """Check if access token and blog ID are present in the session."""
    session_data = get_session_data(request)
    return bool(session_data['access_token'] and session_data['blog_id'])

def disconnect_wordpress(request: Request) -> Dict[str, str]:
    """Clear WordPress session data and the persistent file."""
    request.session.pop('wp_access_token', None)
    request.session.pop('wp_blog_id', None)
    request.session.pop('wp_user_sites', None)
    
    if os.path.exists(WP_CREDENTIALS_PATH):
        os.remove(WP_CREDENTIALS_PATH)
        
    logger.info("WordPress disconnected and persistent storage cleared")
    return {"status": "success", "message": "WordPress disconnected"}


# --- OAUTH FLOW FUNCTIONS (RETAINED) ---
# ... (get_authorization_url and handle_oauth_callback_exchange functions remain unchanged) ...
# --- OAUTH FLOW FUNCTIONS ---



def get_authorization_url(state: str) -> str:
 
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="WordPress Client ID/Secret not configured.")
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "posts media",
        "state": state
    }
    auth_url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
    return auth_url

def handle_oauth_callback_exchange(
    code: str,
    state: str,
    expected_state: str
) -> Dict[str, str]:
 
    # 1. Verify state
    if not state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")
    # 2. Exchange code for token

    token_payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code
    }

    try:
        response = requests.post(TOKEN_URL, data=token_payload, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        blog_id = token_data.get("blog_id")
        if not access_token or not blog_id:
            raise HTTPException(status_code=500, detail="Failed to retrieve access token or blog ID from WP.")
        return {
            "access_token": access_token,
            "blog_id": str(blog_id)
        }
    except requests.exceptions.RequestException as e:

        raise HTTPException(status_code=500, detail=f"Failed to exchange token with WordPress: {e}")

# --- CONTENT PUBLISHING FUNCTIONS ---

def upload_image_to_wordpress(
    access_token: str,
    blog_id: str,
    image_path: str
) -> Optional[Dict[str, Any]]:
    """Upload a single image to WordPress media library. Returns media ID and URL."""
    
    # 3. Use absolute path to ensure file is found in nested structure
    img_p = Path(image_path).absolute()
    
    if not img_p.exists():
        print(f"❌ ERROR: Media file not found: {img_p}")
        return None
    print("\n" + "="*50)
    print("🖼️ STARTING IMAGE UPLOAD")
    print("="*50)
    
    if not os.path.exists(image_path):
        print(f"❌ ERROR: Image file not found locally: {image_path}")
        return None
    
    media_endpoint = MEDIA_API_TEMPLATE.format(blog_id=blog_id)
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        with open(image_path, 'rb') as f:
            filename = os.path.basename(image_path)
            files = {
                'media[]': (filename, f, 'image/jpeg') 
            }
            
            print(f"⬆️ Uploading file: {filename} to {media_endpoint}")
            
            response = requests.post(media_endpoint, headers=headers, files=files, timeout=30)
            
            if response.status_code == 200:
                media_data = response.json()
                if 'media' in media_data and media_data['media']:
                    uploaded = media_data['media'][0]
                    print(f"✅ Image upload successful. ID: {uploaded.get('ID')}, URL: {uploaded.get('URL')}")
                    return {'ID': uploaded.get('ID'), 'URL': uploaded.get('URL')}
                else:
                    print(f"⚠️ WP Image upload succeeded but media array is empty.")
                    return None
            else:
                print(f"❌ WP Image upload failed: {response.status_code}")
                try:
                    print(f"   Error details: {json.loads(response.text)}")
                except json.JSONDecodeError:
                    print(f"   Raw error response: {response.text[:150]}...")
                return None
    except Exception as e:
        print(f"❌ ERROR: Exception during image upload: {e}")
        return None

# --- NEW FUNCTION: STEP 1 (CREATE DRAFT) ---

def create_draft_post_to_wordpress(
    request: Request,
    title: str,
    content: str,
    featured_image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates the generated blog post as a DRAFT in WordPress and returns its ID.
    This is the first step, separating content generation from user scheduling.
    """
    
    print("\n" + "="*80)
    print("🚀 STEP 1: CREATING DRAFT POST")
    print("="*80)
    
    session_data = get_session_data(request)
    access_token = session_data['access_token']
    blog_id = session_data['blog_id']
    
    if not access_token or not blog_id:
        raise HTTPException(
            status_code=401,
            detail="WordPress not connected. Please authorize your account first."
        )
    
    # 1. Upload featured image
    featured_image_id = None
    featured_image_url = None
    if featured_image_path:
        image_data = upload_image_to_wordpress(access_token, blog_id, featured_image_path)
        if image_data:
            featured_image_id = image_data['ID']
            featured_image_url = image_data['URL']

    # 2. Prepare payload for DRAFT creation
    post_endpoint = POST_API_BASE_TEMPLATE.format(blog_id=blog_id, post_id='new') # Use 'new' for creation
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": title,
        "content": content,
        "status": "draft", # <-- CRITICAL: Save as DRAFT
        "format": "standard"
    }
    
    if featured_image_id:
        payload["featured_image"] = str(featured_image_id)
        
    print(f"⬆️ Sending draft payload to {post_endpoint}")
    print(f"   Payload Status: {payload['status']}")
    print(f"   Title: {payload['title'][:50]}...")
    
    try:
        response = requests.post(post_endpoint, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            post_data = response.json()
            post_id = post_data.get('ID')
            post_url = post_data.get('URL')
            
            if not post_id:
                raise Exception("WordPress API created a post but did not return an ID.")
                
            print(f"✅ Draft created successfully!")
            print(f"   Post ID: {post_id}")
            print(f"   Post URL (Draft Preview): {post_url}")
            
            return {
                "success": True,
                "status": "draft",
                "post_id": post_id,
                "post_url": post_url,
                "featured_image_url": featured_image_url,
                "message": "Draft created successfully. Ready for scheduling/publishing."
            }
        else:
            error_data = response.json()
            print(f"❌ Draft creation failed: {response.status_code}")
            print(f"   Error: {error_data}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data.get('message', 'Failed to create blog draft')
            )
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during draft creation: {e}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")


# --- NEW FUNCTION: STEP 2 (UPDATE/SCHEDULE/TRASH) ---

def update_and_schedule_post(
    request: Request,
    post_id: str,
    action: str, # 'schedule', 'publish', or 'trash'
    publish_time: Optional[str] = None # Required if action is 'schedule'
) -> Dict[str, Any]:
    """
    Updates the status and schedule of an existing draft post based on user action.
    """
    print("\n" + "="*80)
    print(f"📅 STEP 2: HANDLING USER ACTION ({action.upper()}) for Post ID: {post_id}")
    print("="*80)

    session_data = get_session_data(request)
    access_token = session_data['access_token']
    blog_id = session_data['blog_id']
    
    if not access_token or not blog_id:
        raise HTTPException(
            status_code=401,
            detail="WordPress not connected. Please authorize your account first."
        )

    # 1. Determine the new status and payload
    payload = {}
    
    if action == 'trash':
        status = 'trash'
        payload = {"status": status}
        
    elif action == 'publish':
        status = 'publish'
        payload = {"status": status}
        
    elif action == 'schedule':
        if not publish_time:
            raise HTTPException(status_code=400, detail="Publish time is required for scheduling action.")
            
        status = 'future'
        
        # Validate/prepare the time for WP API
        try:
            scheduled_dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
            # The WP API requires ISO 8601 (which publish_time usually is), but often prefers the exact format
            wp_date_format = scheduled_dt.isoformat().replace('+00:00', '+00:00') 
            print(f"   Parsed Scheduled Time (UTC): {wp_date_format}")
            
            payload = {
                "status": status,
                "date": wp_date_format 
            }
        except ValueError as e:
            print(f"❌ ERROR: Failed to parse schedule time '{publish_time}': {e}")
            raise HTTPException(status_code=400, detail=f"Invalid date format for scheduling: {publish_time}")

    else:
        raise HTTPException(status_code=400, detail=f"Invalid action specified: {action}")
        
    # 2. Send update request
    post_endpoint = POST_API_BASE_TEMPLATE.format(blog_id=blog_id, post_id=post_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    print(f"⬆️ Sending update payload to {post_endpoint}")
    print(f"   Update Payload: {payload}")
    
    try:
        response = requests.post(post_endpoint, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            post_data = response.json()
            actual_status = post_data.get('status')
            
            print(f"✅ Update successful. New WP Status: {actual_status}")
            
            if actual_status == 'publish' and status == 'future':
                print("⚠️ WARNING: Post published immediately. Scheduled time was likely in the past.")

            return {
                "success": True,
                "action": action,
                "status": actual_status,
                "post_url": post_data.get('URL'),
                "message": f"Post successfully set to status: {actual_status}"
            }
        else:
            error_data = response.json()
            print(f"❌ Post update failed: {response.status_code}")
            print(f"   Error: {error_data}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data.get('message', f'Failed to update post status to {status}')
            )
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during post update: {e}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

# Remove the old, combined publish_blog_to_wordpress function
# It is now replaced by create_draft_post_to_wordpress and update_and_schedule_post.