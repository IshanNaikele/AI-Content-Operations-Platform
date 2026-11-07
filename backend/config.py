# Importing Libraries 

import os
import uuid
from pathlib import Path
from dotenv import load_dotenv 
from tavily import TavilyClient 

load_dotenv()
# --- Configuration Constants ---
APP_URL = os.getenv("APP_URL", "http://3.110.223.163:3000").rstrip("/")
# Base directories for the project
BASE_DIR = Path(__file__).resolve().parent
# Media root for all generated assets (Images, Videos, Blogs)
MEDIA_ROOT = BASE_DIR / "media"
# Data root for sensitive tokens and sessions
DATA_ROOT = BASE_DIR / "data"

os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(DATA_ROOT, exist_ok=True)
IMAGE_FOLDER = MEDIA_ROOT / "images"
BASE_VIDEO_ASSETS_DIR = MEDIA_ROOT / "videos"

# Create them immediately
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(BASE_VIDEO_ASSETS_DIR, exist_ok=True)
os.makedirs(BASE_VIDEO_ASSETS_DIR / "images", exist_ok=True)

# --- 📁 CAMPAIGN PATH MANAGER ---
class CampaignPathManager:
    """Manages unique directory creation for parallel campaign runs."""
    
    @staticmethod
    def get_campaign_paths(campaign_id: str = None):
        """
        Generates and creates isolated directories for a campaign run.
        Returns a dictionary of paths and the campaign ID.
        """
        c_id = campaign_id or str(uuid.uuid4())[:8]
        base_path = MEDIA_ROOT / "campaign" / c_id
        
        paths = {
            "base": base_path,
            "id": c_id,
            "blog": base_path / "blog",
            "blog_assets": base_path / "blog" / "assets",
            "ad_images": base_path / "ad_images",
            "long_form": base_path / "LONG_FORM",
            "long_form_images": base_path / "LONG_FORM" / "images",
            "short_1": base_path / "SHORT_1",
            "short_1_images": base_path / "SHORT_1" / "images",
            "short_2": base_path / "SHORT_2",
            "short_2_images": base_path / "SHORT_2" / "images",
            "short_3": base_path / "SHORT_3",
            "short_3_images": base_path / "SHORT_3" / "images",
            "personal": MEDIA_ROOT / "personal" / "images"
        }
        
        # Atomically create all required subdirectories
        for key, path in paths.items():
            if isinstance(path, Path):
                os.makedirs(path, exist_ok=True)
        
        return paths
    

OAUTH_STATE_KEY = "wordpress_oauth_state"
SECRET_KEY = os.getenv("SECRET_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# YouTube API Configuration ( Related to Video Uploading )
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID") 
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://3.110.223.163:3000/youtube/callback")

# X (Twitter) API Configuration ( Related to Tweet Publishing )
X_API_KEY = os.getenv("X_API_KEY")
X_API_KEY_SECRET = os.getenv("X_API_KEY_SECRET") # Matches your .env variable name
X_REDIRECT_URI = os.getenv("X_REDIRECT_URI", "http://3.110.223.163:3000/")
X_SESSION_KEY = "x_session_id" # Key used in request.session

# WordPress API Configuration ( Related to blog Publishing )
WORDPRESS_CLIENT_ID = os.getenv("WORDPRESS_CLIENT_ID")
WORDPRESS_CLIENT_SECRET = os.getenv("WORDPRESS_CLIENT_SECRET")

# --- Client Initialization --- 
tavily_client = None 

def initialize_clients():
    """Initialize all API clients"""
    global  tavily_client 

    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    if not TAVILY_API_KEY:
        print("WARNING: TAVILY_API_KEY environment variable not set. Research will be disabled.")
        tavily_client = None
    else:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        print("✓ Tavily client initialized")
     
def setup_folders():
    """Create necessary folders"""
    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    print(f"✓ Image folder '{IMAGE_FOLDER}' ready")

    os.makedirs(BASE_VIDEO_ASSETS_DIR, exist_ok=True)
    os.makedirs(BASE_VIDEO_ASSETS_DIR / "images", exist_ok=True)
    print(f"✓ Video assets base folder '{BASE_VIDEO_ASSETS_DIR}' ready")

 
# Text to Image Generation through CloudFlare Platform (Model :Flux )
CLOUDFLARE_ACCOUNT_ID_1 = os.getenv("CLOUDFLARE_ACCOUNT_ID_1")
CLOUDFLARE_API_TOKEN_1 = os.getenv("CLOUDFLARE_API_TOKEN_1")
CLOUDFLARE_ACCOUNT_ID_2 = os.getenv("CLOUDFLARE_ACCOUNT_ID_2")
CLOUDFLARE_API_TOKEN_2 = os.getenv("CLOUDFLARE_API_TOKEN_2")
CLOUDFLARE_ACCOUNT_ID_3 = os.getenv("CLOUDFLARE_ACCOUNT_ID_3")
CLOUDFLARE_API_TOKEN_3 = os.getenv("CLOUDFLARE_API_TOKEN_3")
CLOUDFLARE_ACCOUNT_ID_4 = os.getenv("CLOUDFLARE_ACCOUNT_ID_4")
CLOUDFLARE_API_TOKEN_4 = os.getenv("CLOUDFLARE_API_TOKEN_4")

# Model Used for Image Generation 
CLOUDFLARE_MODEL = "@cf/black-forest-labs/flux-1-schnell"

def get_cloudflare_credentials(key_num: int):
    """Returns (account_id, api_token) for Cloudflare key number 1-4."""
    account_id = os.getenv(f"CLOUDFLARE_ACCOUNT_ID_{key_num}")
    api_token = os.getenv(f"CLOUDFLARE_API_TOKEN_{key_num}")
    return account_id, api_token

OPENROUTER_FALLBACK_MODELS = [
    "google/gemini-2.5-flash",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "google/gemma-4-26b-a4b-it:free",
]

OPENROUTER_API_KEY_STAGE_RESEARCH = os.getenv("OPENROUTER_API_KEY_STAGE_RESEARCH")
OPENROUTER_API_KEY_STAGE_IMAGE_PROMPT = os.getenv("OPENROUTER_API_KEY_STAGE_IMAGE_PROMPT")
OPENROUTER_API_KEY_STAGE_BLOG_PROMPT = os.getenv("OPENROUTER_API_KEY_STAGE_BLOG_PROMPT")
OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_1 = os.getenv("OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_1")
OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_2 = os.getenv("OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_2")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY_STAGE_RESEARCH")
LLM_MAX_TOKENS = 32768

def get_openrouter_key(stage: str):
    """Returns the OpenRouter API key for a specific pipeline stage."""
    keys = {
        "research": OPENROUTER_API_KEY_STAGE_RESEARCH,
        "image_prompt": OPENROUTER_API_KEY_STAGE_IMAGE_PROMPT,
        "blog_prompt": OPENROUTER_API_KEY_STAGE_BLOG_PROMPT,
        "video_1": OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_1,
        "video_2": OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_2,
    }
    return keys.get(stage)


# Text to Speech (Google )
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

def get_google_tts_credentials():
    """Returns parsed Google service account credentials for TTS."""
    import json
    from google.oauth2 import service_account
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        return None
    try:
        service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        return service_account.Credentials.from_service_account_info(service_account_info)
    except Exception as e:
        print(f"❌ Google TTS Credentials Error: {e}")
        return None

def get_tavily_client():
    return tavily_client

def get_base_video_assets_dir():
    """Returns the base path for all video assets (images, audio, final video)."""
    return BASE_VIDEO_ASSETS_DIR

def get_youtube_client_id():
    """Returns the configured YouTube Client ID."""
    return YOUTUBE_CLIENT_ID

def get_youtube_client_secret():
    """Returns the configured YouTube Client Secret."""
    return YOUTUBE_CLIENT_SECRET

def get_youtube_redirect_uri():
    """Returns the configured YouTube Redirect URI."""
    return YOUTUBE_REDIRECT_URI

def get_x_keys(): 
    return X_API_KEY, X_API_KEY_SECRET

def get_wordpress_credentials():
    return WORDPRESS_CLIENT_ID, WORDPRESS_CLIENT_SECRET