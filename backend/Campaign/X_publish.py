import os
import json
import tweepy
import asyncio
from pathlib import Path
from typing import Optional, Dict, Union

# Import the keys from your config file
from  config import X_API_KEY, X_API_KEY_SECRET, DATA_ROOT

# Persistent storage for sessions
SESSION_FILE = DATA_ROOT / "user_x_sessions.json"

def load_sessions() -> Dict:
    """Load all authorized users from the JSON file."""
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading X sessions: {e}")
            return {}
    return {}

def save_session(session_id: str, data: dict):
    """Save a new user's tokens to the JSON file."""
    sessions = load_sessions()
    sessions[session_id] = data
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=4)

def delete_session(session_id: str):
    """Remove a user's tokens."""
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        with open(SESSION_FILE, "w") as f:
            json.dump(sessions, f, indent=4)

def get_x_client_from_dict(user_data: dict):
    """Initializes Tweepy clients directly from a dictionary of tokens."""
    auth = tweepy.OAuth1UserHandler(
        X_API_KEY, X_API_KEY_SECRET, 
        user_data['access_token'], user_data['access_token_secret']
    )
    api_v1 = tweepy.API(auth)
    client_v2 = tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_KEY_SECRET,
        access_token=user_data['access_token'],
        access_token_secret=user_data['access_token_secret']
    )
    return api_v1, client_v2

async def upload_and_post_auto(session_input: Union[str, dict], text: str, image_path: Optional[str] = None):
    """
    Automated function used by both Live Publish and Scheduler.
    """
    # 1. Resolve Credentials
    if isinstance(session_input, str):
        sessions = load_sessions()
        if session_input not in sessions:
            return None
        user_data = sessions[session_input]
    else:
        user_data = session_input 

    api_v1, client_v2 = get_x_client_from_dict(user_data)

    try:
        media_ids = []
        if image_path and os.path.exists(image_path):
            # FIX: Use to_thread to prevent blocking the FastAPI event loop during upload
            media = await asyncio.to_thread(api_v1.media_upload, filename=str(image_path))
            media_ids.append(media.media_id)

        # 2. Create the Tweet via v2 API
        response = client_v2.create_tweet(
            text=text, 
            media_ids=media_ids if media_ids else None
        )
        
        # 3. Get accurate screen name for the URL
        # Re-verify or use stored name to build the link
        screen_name = user_data.get('screen_name', 'i') 
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/{screen_name}/status/{tweet_id}"
        
        print(f"✅ X Post Success: {tweet_url}")
        return tweet_url

    except Exception as e:
        print(f"❌ X Post Error: {str(e)}")
        return None

async def upload_and_post(session_id: str, text: str, image_path: Optional[str] = None):
    """Manual UI helper."""
    result_url = await upload_and_post_auto(session_id, text, image_path)
    if result_url:
        return {"success": True, "url": result_url}
    return {"success": False, "error": "Posting failed"}