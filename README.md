# AI Content Operations Platform

A full-stack, AI-powered content generation and publishing platform built with FastAPI. Given a single topic or product idea, it autonomously generates an entire marketing campaign including blog posts, advertisement images, and multiple video formats then publishes or schedules them directly to WordPress, YouTube, and X (Twitter).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [API Endpoints](#api-endpoints)
- [Campaign Pipeline (Deep Dive)](#campaign-pipeline-deep-dive)
- [Video Generation Pipeline](#video-generation-pipeline)
- [Publishing Integrations](#publishing-integrations)
- [Plans: Standard vs Premium](#plans-standard-vs-premium)
- [Media Storage](#media-storage)

---

## Overview

The platform accepts a topic (e.g., *"Launch an eco-friendly water bottle brand"*) and automatically:

1. **Classifies intent** determines if the request is a full marketing campaign or a personal image generation request.
2. **Researches the topic** performs live web research via the Tavily API across 5 targeted queries if intent is Campaign(product, audience, colors, competitors, strategy).
3. **Synthesizes a strategic brief** an LLM condenses the research into a structured brand strategy, content guidelines, and visual brief.
4. **Generates all assets in parallel:**
   - A long-form SEO blog post with a hero image
   - 3–5 marketing/ad images
   - 4 videos (1 long-form ~30s, 3 short-form ~10s) with voiceover, subtitles, and background music
5. **Publishes or schedules** to WordPress, YouTube, and X/Twitter.

All heavy operations run as background tasks, and the frontend polls a status endpoint for updates. This design avoids proxy/gateway timeouts on long-running jobs.

---

## Architecture

```
User Request (topic + plan)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  POST /analyze_topic                                │
│  ① LLM Intent Classification (campaign vs image)   │
│  ② Tavily Research (5 parallel web searches)       │
│  ③ LLM Research Synthesis → Strategic Brief        │
│  ④ Blog Prompt Generation                          │
│  ⑤ Return campaign_id IMMEDIATELY (< 30s)          │
└──────────────────┬──────────────────────────────────┘
                   │ BackgroundTask handed off
                   ▼
┌─────────────────────────────────────────────────────┐
│  Background Worker (asyncio.gather)                 │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ Blog        │ │ Ad Images    │ │ 4x Video     │ │
│  │ Pipeline    │ │ Pipeline     │ │ Pipelines    │ │
│  │ • Content   │ │ • Prompts    │ │ (parallel)   │ │
│  │ • Hero img  │ │ • Generation │ │              │ │
│  │ • WP Draft  │ │              │ │              │ │
│  └─────────────┘ └──────────────┘ └──────────────┘ │
└──────────────────────────────────────────────────────┘
                   │ Assets saved to disk
                   ▼
        GET /campaign_status/{id}  ← Frontend polls
```

---

## Project Structure

```
backend/
├── app.py                          # FastAPI entry point, router registration, lifespan
├── config.py                       # All API clients, env vars, CampaignPathManager
├── middleware.py                   # Session middleware, static file mounts
├── llm_intent_classifier.py        # Step 1: Classifies intent, generates ContentStrategy
├── index.html                      # Frontend SPA
├── requirements.txt
│
├── routes/
│   ├── static.py                   # Serves index.html; handles X OAuth callback on "/"
│   ├── content.py                  # /analyze_topic, /campaign_status, /schedule_post
│   ├── wordpress.py                # WordPress OAuth connect/callback/disconnect
│   ├── youtube.py                  # YouTube OAuth connect/callback/upload
│   └── X.py                        # X (Twitter) OAuth login/action/status
│
├── Campaign/
│   ├── campaign_tavily_search.py   # Step 2: Performs 5 Tavily web searches
│   ├── research_analysis.py        # Step 3: Synthesizes research → ResearchAnalysis model
│   ├── scheduler_service.py        # APScheduler for post scheduling
│   ├── wordpress_publish.py        # WordPress REST API integration
│   ├── youtube_publish.py          # YouTube Data API v3 integration
│   ├── X_publish.py                # X (Twitter) API v2 integration
│   │
│   ├── blog/
│   │   ├── blog_prompt_generator.py  # Step 4: Generates BlogPromptOutput from brief
│   │   └── blog_generation.py        # Generates blog text (Groq) + hero image
│   │
│   ├── image/
│   │   ├── image_prompt_generator.py # Generates N image prompts from brief
│   │   └── image_generation.py       # Calls Fireworks AI / Imagen 3 for ad images
│   │
│   └── video/
│       ├── video_bible_generator.py        # Defines global video aesthetics
│       ├── video_script_generator.py       # Generates narration script (word-count controlled)
│       ├── audio_generator_elevenlabs.py   # Google Cloud TTS with word-level timestamps
│       ├── storyboard_generator.py         # Divides script into timed scenes
│       ├── final_prompt_optimizer.py       # Batch-optimizes all scene image prompts
│       ├── campaign_free_video_image_generation.py  # Generates scene images via Fireworks AI
│       ├── image_to_video_creation.py      # FFmpeg: stitches images + audio + subtitles
│       ├── subtitle_service.py             # Converts timestamps → SRT file
│       └── background_music_downloader.py  # Downloads royalty-free music from Freesound
│
└── personal/
    └── personal_image_generator.py  # Personal image generation (non-campaign)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| LLM (Research & Orchestration) | OpenRouter API → Google Gemini 2.0 Flash |
| LLM (Blog Content) | Groq → LLaMA 3.1 8B Instant |
| Image Generation (Standard) | Fireworks AI — FLUX.1-schnell-fp8 |
| Image Generation (Premium) | Google Gemini / Imagen 3 |
| Text-to-Speech | Google Cloud TTS v1beta1 (word-level timestamps) |
| Video Assembly | FFmpeg (slideshow + audio + SRT subtitles) |
| Web Research | Tavily API (advanced search) |
| Background Music | Freesound API |
| Task Scheduling | APScheduler |
| Publishing | WordPress REST API, YouTube Data API v3, X (Twitter) API v2 via Tweepy |
| Session Management | Starlette session middleware |
| Data Validation | Pydantic v2 |

---

## Prerequisites

- Python 3.10+
- `ffmpeg` installed and available on system PATH
- Node.js (optional, for frontend tooling)
- A Google Cloud project with the Text-to-Speech API enabled and a service account JSON key
- API accounts for: OpenRouter, Groq, Fireworks AI (4 separate keys recommended), Tavily, Freesound, ElevenLabs (optional)
- OAuth apps configured for: WordPress.com, YouTube (Google Cloud Console), X Developer Portal

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd backend

# Create and activate a virtual environment
python -m venv my_env
source my_env/bin/activate  # Windows: my_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the `backend/` root with the following variables:

```env
# ── Application ──────────────────────────────────────────────
APP_URL=http://your-server-ip:3000
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=your-secret-key-for-sessions

# ── LLM: OpenRouter (5 dedicated clients for parallel pipelines) ──
OPENROUTER_API_KEY=your-general-key
OPENROUTER_API_KEY_STAGE_RESEARCH=key-for-research-stage
OPENROUTER_API_KEY_STAGE_IMAGE_PROMPT=key-for-image-prompts
OPENROUTER_API_KEY_STAGE_BLOG_PROMPT=key-for-blog-prompts
OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_1=key-for-video-pipeline-1
OPENROUTER_API_KEY_STAGE_VIDEO_PIPELINE_2=key-for-video-pipeline-2

# ── LLM: Groq (Blog Content Generation) ──────────────────────
GROQ_API_KEY=your-groq-key

# ── Image Generation: Fireworks AI (4 keys for parallel video pipelines) ──
FIREWORKS_API_KEY=your-default-key
FIREWORKS_API_KEY_1=key-for-long-form-video
FIREWORKS_API_KEY_2=key-for-short-3
FIREWORKS_API_KEY_3=key-for-short-2
FIREWORKS_API_KEY_4=key-for-short-1

# ── Google Cloud TTS ──────────────────────────────────────────
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}

# ── Research ──────────────────────────────────────────────────
TAVILY_API_KEY=your-tavily-key

# ── Background Music ─────────────────────────────────────────
FREESOUND_API_KEY=your-freesound-key

# ── Audio (Optional — TTS has been migrated to Google) ────────
ELEVENLABS_API_KEY=your-elevenlabs-key

# ── Publishing: WordPress ─────────────────────────────────────
WORDPRESS_CLIENT_ID=your-wp-client-id
WORDPRESS_CLIENT_SECRET=your-wp-client-secret

# ── Publishing: YouTube ──────────────────────────────────────
YOUTUBE_CLIENT_ID=your-yt-client-id
YOUTUBE_CLIENT_SECRET=your-yt-client-secret
YOUTUBE_REDIRECT_URI=http://your-server:3000/youtube/callback

# ── Publishing: X (Twitter) ──────────────────────────────────
X_API_KEY=your-x-api-key
X_API_KEY_SECRET=your-x-api-secret
X_REDIRECT_URI=http://your-server:3000/
```

> **Note on Fireworks keys:** Using 4 separate API keys (one per video pipeline) avoids rate limiting when all 4 videos are generated simultaneously. A single key can be used across all 4, but generation may be throttled.

> **Note on OpenRouter keys:** Similarly, using 5 dedicated keys (one per pipeline stage) prevents one slow stage from blocking others. A single key works but may hit rate limits on large campaigns.

---

## Running the App

```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The app will be available at `http://localhost:8000`. The frontend SPA is served at `/`.

---

## API Endpoints

### Content Generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/analyze_topic` | Main entry point. Accepts `topic`, `plan` (standard/premium), optional `video_duration`. Returns `campaign_id` immediately; generation runs in background. |
| `GET` | `/campaign_status/{campaign_id}` | Poll for campaign progress. Returns videos, blog, ad images, WordPress post ID as they become available. |
| `POST` | `/schedule_post` | Unified publishing endpoint for WordPress, YouTube, and X. |

**`/analyze_topic` form fields:**
- `topic` *(required)* — The product, idea, or campaign description.
- `plan` *(required)* — `standard` (Fireworks AI) or `premium` (Imagen 3).
- `video_duration` *(optional)* — e.g., `"60s"`, `"2min"`. Defaults to `60s` if not specified in topic.

**`/schedule_post` form fields:**
- `platform` *(required)* — `wordpress`, `youtube`, or `x`
- `action` *(required)* — `publish`, `schedule`, or `discard`
- `publish_time` *(required for schedule)* — ISO 8601 datetime string
- Platform-specific: `post_id` (WordPress), `video_path` + `video_title` + `video_description` (YouTube), `tweet_text` + `image_path` (X)

### WordPress OAuth

| Method | Path | Description |
|---|---|---|
| `GET` | `/status` | Check WordPress connection status |
| `GET` | `/connect_wordpress` | Initiate OAuth flow |
| `GET` | `/callback` | OAuth callback (exchanges code for token) |
| `POST` | `/disconnect` | Disconnect WordPress account |

### YouTube OAuth

| Method | Path | Description |
|---|---|---|
| `GET` | `/youtube/login` | Initiate YouTube OAuth 2.0 |
| `GET` | `/youtube/callback` | OAuth callback |
| `GET` | `/youtube/status` | Check connection + channel info |
| `POST` | `/youtube/disconnect` | Disconnect account |
| `POST` | `/youtube/upload_and_schedule` | Direct upload/schedule endpoint |

### X (Twitter) OAuth

| Method | Path | Description |
|---|---|---|
| `GET` | `/x/login` | Initiate OAuth 1.0a flow |
| `GET` | `/` | Root URL — handles X OAuth callback, then serves `index.html` |
| `POST` | `/x/x_action` | Post, schedule, or discard a tweet with media |
| `GET` | `/x/status` | Check X connection status |
| `POST` | `/x/disconnect` | Disconnect X account |

---

## Campaign Pipeline (Deep Dive)

When `intent = "campaign"`, the following stages execute sequentially in the foreground (fast, < 30s), then hand off to a background worker:

### Foreground (synchronous, returns to client)

**Stage 1 — Intent Classification** (`llm_intent_classifier.py`)
The topic is sent to Gemini 2.0 Flash via OpenRouter. The LLM returns a `ContentStrategy` object containing: intent, keywords, content_summary, requires_research, research_queries, image_count, duration_seconds, and music_search_query.

**Stage 2 — Web Research** (`campaign_tavily_search.py`)
Five targeted Tavily searches run for: product overview, target audience, color/design trends, competitor analysis, and marketing strategy. Each returns 2 advanced-depth results.

**Stage 3 — Research Synthesis** (`research_analysis.py`)
Raw Tavily snippets are passed to Gemini, which synthesizes them into a `ResearchAnalysis` object containing a `BrandStrategy`, `ContentGuidelines`, and `VisualBrief`.

**Stage 4 — Blog Prompt Generation** (`blog/blog_prompt_generator.py`)
The strategic brief is used to generate a `BlogPromptOutput` containing a finalized writing prompt, target word count, tone, primary keyword, and a visual image prompt for the hero image.

The API then returns immediately with a `campaign_id` and `"status": "processing"`.

### Background Worker (parallel, asyncio.gather)

All three pipelines below run concurrently:

**Blog Pipeline** → Generates hero image → Generates blog text via Groq LLaMA → Creates WordPress draft → Saves files to disk

**Ad Image Pipeline** → Generates N image prompts from brief → Generates all images via Fireworks AI or Imagen 3 → Copies to campaign folder

**Video Pipelines (×4 in parallel)** — see [Video Generation Pipeline](#video-generation-pipeline) below

---

## Video Generation Pipeline

Each of the 4 video variants (LONG_FORM, SHORT_1, SHORT_2, SHORT_3) runs through an identical 8-stage pipeline, each using a dedicated Fireworks API key to avoid rate limiting:

```
① Video Bible    →  Global aesthetics: color palette, mood, camera style, lighting
② Script         →  Full narration text, word-count controlled for exact duration
③ Google TTS     →  MP3 audio + word-level timestamps (SSML marks)
④ SRT Subtitles  →  Timestamp groups converted to .srt file
⑤ Storyboard     →  Narration divided into ~3.5s scenes with visual prompt drafts
⑥ Prompt Optimizer → All scene prompts refined in a single batch LLM call
⑦ Image Generation → One image per scene via Fireworks AI FLUX.1-schnell-fp8
⑧ FFmpeg Stitch  →  Images + audio + SRT subtitles + background music → final .mp4
```

**Format detection:** Videos with total duration ≤ 20s are rendered in portrait 9:16 (1080×1920) for Reels/Shorts. Longer videos use landscape 16:9 (1920×1080).

**Background music:** One track is downloaded via the Freesound API at the start of each campaign and shared across all 4 videos. The search query is intelligently generated by the intent classifier LLM to match the content mood.

**Subtitle rendering:** Subtitles are burned directly into the video by FFmpeg using the `subtitles` filter with a custom font style.

---

## Publishing Integrations

### WordPress
Uses OAuth 2.0 against the WordPress.com API. After authorization, an access token is stored in the user session and in a persistent credentials file. Blog posts are created as drafts automatically at the end of every campaign, then can be published, scheduled, or trashed via `/schedule_post`.

### YouTube
Uses OAuth 2.0 against the YouTube Data API v3. Videos can be uploaded as `public`, `unlisted`, or `private`. Scheduled uploads use YouTube's native `publishAt` field with the video set to `private` until the publish time.

### X (Twitter)
Uses OAuth 1.0a via Tweepy. The OAuth callback is handled on the root `/` URL to match typical developer portal configurations. Sessions are stored as JSON files on disk. Posts can be published immediately or scheduled via APScheduler. Images are uploaded as media attachments.

---

## Plans: Standard vs Premium

| Feature | Standard | Premium |
|---|---|---|
| Ad image generation | Fireworks AI FLUX.1-schnell-fp8 | Google Imagen 3 via Gemini |
| Blog hero image | Fireworks AI FLUX.1-schnell-fp8 | Google Imagen 3 via Gemini |
| Personal images | Fireworks AI FLUX.1-schnell-fp8 | Gemini `gemini-3-pro-image-preview` |
| Video scene images | Fireworks AI (both plans) | Fireworks AI (both plans) |

---

## Media Storage

All generated assets are stored under `backend/media/` with a per-campaign isolated directory structure:

```
media/
├── campaign/
│   └── {campaign_id}/
│       ├── blog/
│       │   └── assets/          # Blog hero image
│       ├── ad_images/           # Marketing images (copied here for polling)
│       ├── LONG_FORM/
│       │   ├── images/          # Scene images
│       │   ├── LONG_FORM_audio.mp3
│       │   ├── LONG_FORM_captions.srt
│       │   ├── LONG_FORM_final.mp4
│       │   └── LONG_FORM_metadata.json
│       ├── SHORT_1/             # Same structure as LONG_FORM
│       ├── SHORT_2/
│       ├── SHORT_3/
│       ├── background_music.mp3  # Shared across all 4 videos
│       ├── blog_content.txt
│       ├── blog_hero_image.jpeg
│       └── wordpress_post_id.txt
├── images/                      # Legacy/standalone images
├── personal/
│   └── {campaign_id}/           # Personal image generation output
└── videos/                      # Legacy/standalone videos
```

The `/media` directory is mounted as a static files route, making all assets directly accessible via URL. The polling endpoint (`/campaign_status/{id}`) reads this directory structure to report progress and return asset URLs as files appear.
