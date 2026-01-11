import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
 
# Absolute import from config.py to ensure path consistency
from config import SECRET_KEY, MEDIA_ROOT, DATA_ROOT
 

class ProductionRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect 127.0.0.1 to localhost"""
    async def dispatch(self, request: Request, call_next):
        if os.getenv("ENV") == "development" and request.url.hostname == "127.0.0.1":
            new_url = str(request.url).replace("127.0.0.1", "localhost")
            return RedirectResponse(url=new_url, status_code=307)
        
        response = await call_next(request)
        return response

def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI app"""
    # Force localhost middleware
    app.add_middleware(ProductionRedirectMiddleware)
    
    # Session middleware for OAuth
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        session_cookie="session",
        max_age=7200,
        same_site="lax",
        https_only=False,
        path="/"
    )
    print("✓ Middleware configured for Production/Dev")

def setup_static_files(app: FastAPI):
    """Mount static file directories"""
    # 1. Mount personal images (existing)
    if os.path.exists(MEDIA_ROOT):
        app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")
        print(f"✓ Dynamic media directory mounted at /media")
    else:
        print(f"WARNING: Media directory {MEDIA_ROOT} not found. Creating it now...")
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")

    print("✓ Static file system initialized")
     