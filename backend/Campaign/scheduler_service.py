import os
import json
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pathlib import Path

# 1. Absolute Imports from config
from config import DATA_ROOT

# --- 1. Setup Logging & JobStore ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SchedulerService")

os.makedirs(DATA_ROOT, exist_ok=True)
JOBS_DB_PATH = DATA_ROOT / "jobs.sqlite"

# SQLite ensures jobs survive a server restart or crash
jobstores = {
    'default': SQLAlchemyJobStore(url=f'sqlite:///{JOBS_DB_PATH}')
}

scheduler = AsyncIOScheduler(jobstores=jobstores)

# --- 2. The Task Execution Logic ---

async def execute_scheduled_x_post(session_json: str, tweet_text: str, media_path: str):
    """
    Background worker that triggers the actual X API call.
    """
    # FIX 1: Import inside the function to prevent Circular Dependency
    from Campaign.X_publish import upload_and_post_auto
    
    try:
        logger.info(f"🚀 [SCHEDULER] Starting execution for scheduled post.")
        
        # 1. Validate Media Exists
        if media_path and not os.path.exists(media_path):
            logger.error(f"❌ [SCHEDULER] Aborting: Media file missing at {media_path}")
            media_path = None
            return

        # Parse session
        session_dict = json.loads(session_json)
        
        # Execute Post
        link = await upload_and_post_auto(
            session_input=session_dict, 
            text=tweet_text, 
            image_path=media_path
        )
        
        if link:
            logger.info(f"✅ [SCHEDULER] Success! Post live: {link}")
        else:
            logger.error(f"❌ [SCHEDULER] X API rejected the post.")
            
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Execution Error: {e}")

# --- 3. The Interface: Adding & Removing Jobs ---

async def schedule_x_post(session_dict: dict, text: str, media_path: str, publish_time: str):
    """
    Adds a post to the SQLite queue.
    """
    try:
        # Normalize the date format
        run_date = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
        
        absolute_media_path = str(Path(media_path).resolve()) if media_path else None
        session_json = json.dumps(session_dict)
        
        # Unique ID for tracking
        job_id = f"x_post_{int(datetime.now().timestamp())}"

        scheduler.add_job(
            execute_scheduled_x_post,
            trigger='date',
            run_date=run_date,
            args=[session_json, text, absolute_media_path],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=3600 # FIX 2: Allows posting even if server was briefly down
        )
        
        logger.info(f"⏰ [SCHEDULER] Job {job_id} queued for {publish_time}")
        return {"status": "scheduled", "job_id": job_id, "run_date": publish_time}
        
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Scheduling Failed: {e}")
        return {"status": "error", "message": str(e)}

# FIX 3: New function to support the "Discard" action
def cancel_scheduled_post(job_id: str):
    """
    Removes a job from the scheduler (used for Discard feature).
    """
    try:
        scheduler.remove_job(job_id)
        logger.info(f"🗑️ [SCHEDULER] Job {job_id} has been cancelled/discarded.")
        return True
    except Exception as e:
        logger.warning(f"⚠️ [SCHEDULER] Could not cancel job {job_id}: {e}")
        return False

# --- 4. Lifecycle Management ---
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("📅 [SCHEDULER] Background monitor is ONLINE.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 [SCHEDULER] Background monitor is OFFLINE.")