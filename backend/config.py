import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from google import genai
from tavily import TavilyClient
from elevenlabs import client as elevenlabs_client_lib
from openai import OpenAI

load_dotenv()
# --- Configuration Constants ---
APP_URL = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")
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
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key-only")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# 🌟 NEW: YouTube API Configuration
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID") 
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
# This must match the redirect URI configured in your Google Cloud Console
YOUTUBE_REDIRECT_URI = "http://localhost:8000/youtube/callback"

# 🌟 X (Twitter) API Configuration
X_API_KEY = os.getenv("X_API_KEY")
X_API_KEY_SECRET = os.getenv("X_API_KEY_SECRET") # Matches your .env variable name
X_REDIRECT_URI = "http://localhost:8000/"
X_SESSION_KEY = "x_session_id" # Key used in request.session
 
FIREWORKS_API_KEY_1 = os.getenv("FIREWORKS_API_KEY_1")
FIREWORKS_API_KEY_2 = os.getenv("FIREWORKS_API_KEY_2")
FIREWORKS_API_KEY_3 = os.getenv("FIREWORKS_API_KEY_3")
FIREWORKS_API_KEY_4 = os.getenv("FIREWORKS_API_KEY_4")

WORDPRESS_CLIENT_ID = os.getenv("WORDPRESS_CLIENT_ID")
WORDPRESS_CLIENT_SECRET = os.getenv("WORDPRESS_CLIENT_SECRET")

if not WORDPRESS_CLIENT_ID or not WORDPRESS_CLIENT_SECRET:
    print("WARNING: WordPress credentials not configured")

# Add a print statement here to debug (remove this after it works)
print(f"DEBUG: X_API_KEY is {'Set' if X_API_KEY else 'None'}")
print(f"DEBUG: X_API_KEY_SECRET is {'Set' if X_API_KEY_SECRET else 'None'}")
# --- Client Initialization ---
groq_client = None
gemini_client = None
openrouter_client = None
tavily_client = None
elevenlabs_client = None
fireworks_api_key = None


# Changing API Key 
gemini_client_research = None
gemini_client_image_prompt = None
gemini_client_blog_prompt = None
gemini_client_video_1 = None
gemini_client_video_2 = None


def initialize_clients():
    """Initialize all API clients"""
    global groq_client, gemini_client, tavily_client, elevenlabs_client, fireworks_api_key, openrouter_client
    global gemini_client_research, gemini_client_image_prompt, gemini_client_blog_prompt, gemini_client_video_1, gemini_client_video_2
    
    try:
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("✓ Groq client initialized")
    except Exception as e:
        print(f"Error initializing Groq Client: {e}")
        groq_client = None
    
    # 🌟 NEW: Initialize all 5 dedicated Gemini Clients
    GEMINI_KEYS = {
        "research": os.getenv("GEMINI_KEY_STAGE_RESEARCH"),
        "image_prompt": os.getenv("GEMINI_KEY_STAGE_IMAGE_PROMPT"),
        "blog_prompt": os.getenv("GEMINI_KEY_STAGE_BLOG_PROMPT"),
        "video_1": os.getenv("GEMINI_KEY_VIDEO_PIPELINE_1"),
        "video_2": os.getenv("GEMINI_KEY_VIDEO_PIPELINE_2"),
    }

    # Function to safely initialize a Gemini client
    def init_gemini_client(key_name, api_key_value):
        if not api_key_value:
            print(f"WARNING: API Key for {key_name.upper()} not found in environment.")
            return None
        try:
            # Explicitly pass the API key to ensure the correct key is used
            client = genai.Client(api_key=api_key_value)
            print(f"✓ Gemini client for {key_name.capitalize()} initialized.")
            return client
        except Exception as e:
            print(f"Error initializing Gemini Client for {key_name}: {e}")
            return None
        
    gemini_client_research = init_gemini_client("research", GEMINI_KEYS["research"])
    gemini_client_image_prompt = init_gemini_client("image_prompt", GEMINI_KEYS["image_prompt"])
    gemini_client_blog_prompt = init_gemini_client("blog_prompt", GEMINI_KEYS["blog_prompt"])
    gemini_client_video_1 = init_gemini_client("video_1", GEMINI_KEYS["video_1"])
    gemini_client_video_2 = init_gemini_client("video_2", GEMINI_KEYS["video_2"])
    try:
        gemini_client = genai.Client()
        print("✓ Gemini client initialized")
    except Exception as e:
        print(f"Error initializing Gemini Client: {e}")
        gemini_client = None

    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    if not TAVILY_API_KEY:
        print("WARNING: TAVILY_API_KEY environment variable not set. Research will be disabled.")
        tavily_client = None
    else:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        print("✓ Tavily client initialized")
    
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY environment variable not set. OpenRouter LLM will be disabled.")
        openrouter_client = None
    else:
        try:
            openrouter_client = OpenAI(
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
            )
            print("✓ OpenRouter client initialized")
        except Exception as e:
            print(f"Error initializing OpenRouter Client: {e}")
            openrouter_client = None


    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        print("WARNING: ELEVENLABS_API_KEY not set. Video audio generation will be disabled.")
    else:
        try:
            # NOTE: We use the mock client if you haven't installed the real one.
            # Replace the mock with the real client if possible in your environment:
            import elevenlabs.client
            elevenlabs_client = elevenlabs.client.ElevenLabs(api_key=ELEVENLABS_API_KEY)
            print("✓ ElevenLabs client initialized (using Mock or Real).")
        except Exception as e:
            print(f"Error initializing ElevenLabs Client: {e}")
            elevenlabs_client = None
            
    # 2. Fireworks AI Key (Image/Video Assets)
    fireworks_api_key = os.getenv("FIREWORKS_API_KEY") 
    if not fireworks_api_key:
        print("WARNING: FIREWORKS_API_KEY not set. Video image generation will be disabled.")

     

 

def get_groq_client():
    return groq_client

def get_gemini_client():
    return gemini_client

def get_tavily_client():
    return tavily_client

def get_elevenlabs_client():
    """Returns the initialized ElevenLabs client."""
    return elevenlabs_client

def get_fireworks_api_key():
    """Returns the Fireworks AI API key."""
    return fireworks_api_key

def get_base_video_assets_dir():
    """Returns the base path for all video assets (images, audio, final video)."""
    return BASE_VIDEO_ASSETS_DIR

def get_openrouter_client():
    return openrouter_client

# 🌟 NEW: Dedicated Getter functions for all Gemini clients
def get_gemini_client_research():
    return gemini_client_research

def get_gemini_client_image_prompt():
    return gemini_client_image_prompt

def get_gemini_client_blog_prompt():
    return gemini_client_blog_prompt

def get_gemini_client_video_1():
    return gemini_client_video_1

def get_gemini_client_video_2():
    return gemini_client_video_2

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

def get_fireworks_api_key_1():
    """Get Fireworks API Key 1"""
    if not FIREWORKS_API_KEY_1:
        raise ValueError("FIREWORKS_API_KEY_1 not found in environment variables")
    return FIREWORKS_API_KEY_1

def get_fireworks_api_key_2():
    """Get Fireworks API Key 2"""
    if not FIREWORKS_API_KEY_2:
        raise ValueError("FIREWORKS_API_KEY_2 not found in environment variables")
    return FIREWORKS_API_KEY_2

def get_fireworks_api_key_3():
    """Get Fireworks API Key 1"""
    if not FIREWORKS_API_KEY_3:
        raise ValueError("FIREWORKS_API_KEY_1 not found in environment variables")
    return FIREWORKS_API_KEY_3

def get_fireworks_api_key_4():
    """Get Fireworks API Key 2"""
    if not FIREWORKS_API_KEY_4:
        raise ValueError("FIREWORKS_API_KEY_2 not found in environment variables")
    return FIREWORKS_API_KEY_4

def get_wordpress_credentials():
    return WORDPRESS_CLIENT_ID, WORDPRESS_CLIENT_SECRET