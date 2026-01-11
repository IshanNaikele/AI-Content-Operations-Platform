"""
Main FastAPI Application Entry Point
Refactored for better modularity and maintainability
"""
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# 1. Absolute Imports from root
from config import initialize_clients, MEDIA_ROOT, DATA_ROOT
from middleware import setup_middleware, setup_static_files
 
# 2. Corrected Route Imports based on your 'routes/' folder
from routes import wordpress, content, static, youtube, X

# 3. Corrected Scheduler Import based on your 'Campaign/' folder
from Campaign.scheduler_service import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background clock
    print("\n⏰ Starting Scheduler...")
    start_scheduler()
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(DATA_ROOT, exist_ok=True)
    print(f"📁 Storage Directories Verified: {MEDIA_ROOT}")
    yield
    # Shutdown: Clean up
    print("\n🛑 Stopping Scheduler...")
    stop_scheduler()
    
# =============================================================================
# APPLICATION INITIALIZATION
# =============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Content Generation API",
    description="Multi-Intent Parallel Content Pipeline (AWS Production Ready)",
    version="2.0.0",
    lifespan=lifespan
)

# Initialize all clients (Groq, Gemini, Tavily)
print("\n🚀 Initializing API clients...")
initialize_clients()
 
# Mount dynamic static files (/media/campaign/...)
print("\n📂 Mounting dynamic static files...")
setup_static_files(app)

# Setup middleware (Session, Force Localhost)
print("\n⚙️ Configuring middleware...")
setup_middleware(app)

 

# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

# Register all routers
print("\n🛣️ Registering routes...")
app.include_router(static.router, tags=["Static"])
app.include_router(wordpress.router, tags=["WordPress OAuth"])
app.include_router(content.router, tags=["Content Generation"])
app.include_router(youtube.router, tags=["YouTube Publishing"])
app.include_router(X.router, tags=["X Publishing"])
print("\n✅ Application startup complete!\n")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0") 
    port = int(os.getenv("APP_PORT", 8000))
    
    print(f"📡 Serving on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)