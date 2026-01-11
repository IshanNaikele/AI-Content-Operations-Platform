import requests
import os
import time
import random
import json
from datetime import datetime
from pathlib import Path

# Freesound API credentials
API_KEY = os.getenv("FREESOUND_API_KEY")
BASE_URL = "https://freesound.org/apiv2"

if not API_KEY:
    raise ValueError("FREESOUND_API_KEY not found in environment variables")

# Folder structure
MUSIC_FOLDER = "downloaded_music"
HISTORY_FILE = os.path.join(MUSIC_FOLDER, "music_history.json")

class MusicDownloader:
    def __init__(self):
        # Create music folder if it doesn't exist
        os.makedirs(MUSIC_FOLDER, exist_ok=True)
        self.history = self.load_history()
    
    def load_history(self):
        """Load previously downloaded track IDs"""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_history(self):
        """Save download history to JSON file in music folder"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def is_downloaded(self, search_query, sound_id):
        """Check if we've already downloaded this track for this search query"""
        if search_query not in self.history:
            return False
        # FIX: Check if sound_id exists in any dictionary's 'sound_id' field
        downloaded_ids = [track['sound_id'] for track in self.history[search_query]]
        return sound_id in downloaded_ids
    
    def mark_downloaded(self, search_query, sound_id, sound_name):
        """Mark a track as downloaded"""
        if search_query not in self.history:
            self.history[search_query] = []
        
        self.history[search_query].append({
            'sound_id': sound_id,
            'name': sound_name,
            'downloaded_at': datetime.now().isoformat()
        })
        self.save_history()
    
    def get_downloaded_count(self, search_query):
        """Get count of downloaded tracks for a search query"""
        return len(self.history.get(search_query, []))
    
    def download_music_from_llm_query(self, music_search_query: str, 
                                      output_filename: str = None) -> dict:
        """
        Download music based on LLM-generated search query.
        This is the main function to use with your LLM intent classifier.
        
        Args:
            music_search_query: Search query from LLM (e.g., "uplifting acoustic corporate")
            output_filename: Optional custom filename (auto-generated if None)
        
        Returns:
            dict with download info or None if failed
        """
        # Generate filename if not provided
        if output_filename is None:
            # Sanitize query for filename
            safe_query = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' 
                               for c in music_search_query)
            safe_query = safe_query.replace(' ', '_').lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"music_{safe_query}_{timestamp}.mp3"
        
        # Ensure file goes into music folder
        output_path = os.path.join(MUSIC_FOLDER, output_filename)
        
        print(f"\n{'='*70}")
        print(f"🎵 DOWNLOADING MUSIC FROM LLM QUERY")
        print(f"{'='*70}")
        print(f"Query: '{music_search_query}'")
        print(f"Output: {output_path}")
        
        result = self.search_and_download_music(
            search_query=music_search_query,
            output_path=output_path,
            max_attempts=10
        )
        
        if result:
            print(f"\n✅ SUCCESS! Music downloaded to: {output_path}")
            print(f"   Track: {result['name']}")
            print(f"   Duration: {result['duration']:.1f}s")
            print(f"{'='*70}\n")
        else:
            print(f"\n❌ FAILED to download music for query: '{music_search_query}'")
            print(f"{'='*70}\n")
        
        return result
    
    def search_and_download_music(self, search_query: str, output_path: str, 
                                  max_attempts: int = 10) -> dict:
        """
        Search for music and download, avoiding previously downloaded tracks.
        Now accepts ANY search query, not just predefined moods.
        
        Args:
            search_query: Any search query string (from LLM or manual)
            output_path: Full path where to save the file
            max_attempts: How many different tracks to try before giving up
        """
        max_duration = 90  # 1.5 minutes
        
        print(f"\n🔍 Searching for: '{search_query}'")
        print(f"   Duration limit: Up to {max_duration}s (1.5 minutes)")
        print(f"   Previously downloaded for this query: {self.get_downloaded_count(search_query)}")
        
        # Random sort for variety
        sort_options = ["rating_desc", "downloads_desc", "duration_desc", "created_desc"]
        random_sort = random.choice(sort_options)
        
        search_url = f"{BASE_URL}/search/text/"
        
        # Try multiple pages until we find results
        for page_attempt in range(1, 4):
            params = {
                "query": search_query,
                "filter": f"duration:[0 TO {max_duration}]",
                "token": API_KEY,
                "fields": "id,name,tags,duration,previews,username,num_downloads,avg_rating",
                "sort": random_sort,
                "page": page_attempt,
                "page_size": 30
            }
            
            try:
                response = requests.get(search_url, params=params, timeout=10)
                
                if response.status_code == 404:
                    print(f"   ⏭️  Page {page_attempt} not found, trying next...")
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                total_available = data['count']
                results = data['results']
                
                print(f"   📊 Total: {total_available} | Page: {page_attempt} | Results: {len(results)}")
                
                if not results:
                    continue
                
                random.shuffle(results)
                
                # Try to find a NEW track
                selected_track = None
                attempts = 0
                
                for track in results:
                    attempts += 1
                    if attempts > max_attempts:
                        break
                    
                    sound_id = track['id']
                    
                    if not self.is_downloaded(search_query, sound_id):
                        selected_track = track
                        print(f"   ✅ Found NEW track (attempt {attempts})")
                        break
                    else:
                        print(f"   ⏭️  Skipping: {track['name'][:40]}... (already downloaded)")
                
                # If all were downloaded, pick random
                if not selected_track and results:
                    print(f"   ⚠️  All checked tracks were downloaded, picking random one")
                    selected_track = random.choice(results)
                
                if selected_track:
                    sound_id = selected_track['id']
                    sound_name = selected_track['name']
                    duration = selected_track['duration']
                    username = selected_track['username']
                    downloads = selected_track.get('num_downloads', 'N/A')
                    rating = selected_track.get('avg_rating', 'N/A')
                    tags = ', '.join(selected_track.get('tags', [])[:5])
                    
                    print(f"   🎵 Selected: '{sound_name}' by {username}")
                    print(f"      Duration: {duration:.1f}s | Downloads: {downloads} | Rating: {rating}")
                    print(f"      Tags: {tags}")
                    
                    preview_url = selected_track['previews']['preview-hq-mp3']
                    print(f"   ⬇️  Downloading...")
                    
                    download_response = requests.get(preview_url, stream=True, timeout=30)
                    download_response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"   ✅ Downloaded: {output_path} ({file_size:.2f} MB)")
                    
                    self.mark_downloaded(search_query, sound_id, sound_name)
                    
                    return {
                        'path': output_path,
                        'name': sound_name,
                        'duration': duration,
                        'username': username,
                        'sound_id': sound_id,
                        'total_available': total_available,
                        'tags': tags
                    }
                
            except requests.exceptions.RequestException as e:
                if "404" not in str(e):
                    print(f"   ❌ Error on page {page_attempt}: {e}")
                continue
        
        print(f"   ❌ No suitable results found")
        return None


# ============================================================================
# INTEGRATION FUNCTION FOR YOUR LLM PIPELINE
# ============================================================================

def download_music_for_campaign(content_strategy_dict: dict, output_path: str) -> dict:
    """
    Main integration function for your content generation pipeline.
    Call this after getting ContentStrategy from llm_intent_classifier.
    
    Args:
        content_strategy_dict: Dictionary from ContentStrategy.model_dump()
                              Must contain 'music_search_query' key
    
    Returns:
        dict with music file info or None if failed
    
    Example:
        from llm_intent_classifier import classify_and_strategize
        
        strategy = classify_and_strategize(user_topic, gemini_client)
        music_info = download_music_for_campaign(strategy.model_dump())
        
        if music_info:
            print(f"Use this music file: {music_info['path']}")
    """
    downloader = MusicDownloader()
    
    music_query = content_strategy_dict.get('music_search_query')
    
    if not music_query:
        print("❌ No 'music_search_query' found in content_strategy_dict")
        return None
    
    return downloader.download_music_from_llm_query(
        music_search_query=music_query,
        output_filename=output_path
    )


# ============================================================================
# TEST CASES
# ============================================================================

def test_with_llm_style_queries():
    """Test with realistic LLM-generated music search queries"""
    downloader = MusicDownloader()
    
    print("\n" + "="*70)
    print("🧪 TESTING WITH LLM-STYLE MUSIC QUERIES")
    print("="*70)
    
    # Simulate queries that your LLM would generate
    test_queries = [
        "uplifting acoustic corporate",
        "cinematic ambient",
        "upbeat electronic",
        "lofi hip hop",
        "emotional piano"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Testing query: '{query}'")
        print("-" * 70)
        
        result = downloader.download_music_from_llm_query(query)
        
        if result:
            results.append(result)
        
        time.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"✅ Downloaded: {len(results)}/{len(test_queries)} tracks")
    
    if results:
        print(f"\n📁 All files in folder: {MUSIC_FOLDER}/")
        print(f"📄 History JSON: {HISTORY_FILE}")
        print(f"\nDownloaded files:")
        for r in results:
            print(f"   • {os.path.basename(r['path'])}")
            print(f"     {r['name']} - {r['duration']:.1f}s")
    
    print("\n" + "="*70 + "\n")


def test_content_strategy_integration():
    """Test with a mock ContentStrategy object (simulating your LLM output)"""
    print("\n" + "="*70)
    print("🧪 TESTING CONTENT STRATEGY INTEGRATION")
    print("="*70)
    
    # Simulate what your LLM returns
    mock_content_strategy = {
        "intent": "campaign",
        "keywords": ["eco-friendly", "sustainable"],
        "content_summary": "Eco-friendly water bottle campaign",
        "requires_research": True,
        "image_count": 3,
        "duration_seconds": 30,
        "music_search_query": "uplifting acoustic corporate"
    }
    
    print("\n📋 Mock ContentStrategy:")
    print(json.dumps(mock_content_strategy, indent=2))
    
    # Download music based on the strategy
    music_info = download_music_for_campaign(mock_content_strategy)
    
    if music_info:
        print(f"\n✅ Music ready for campaign!")
        print(f"   File: {music_info['path']}")
        print(f"   Duration: {music_info['duration']:.1f}s")
    else:
        print(f"\n❌ Failed to download music")
    
    print("\n" + "="*70 + "\n")


def test_anti_repetition():
    """Test that downloading the same query multiple times gives different tracks"""
    downloader = MusicDownloader()
    
    print("\n" + "="*70)
    print("🧪 TESTING ANTI-REPETITION")
    print("   Downloading same query 3 times - should get different tracks")
    print("="*70)
    
    query = "ambient peaceful"
    downloads = []
    
    for i in range(3):
        print(f"\n[Download {i+1}/3]")
        result = downloader.download_music_from_llm_query(
            query, 
            output_filename=f"test_repetition_{i+1}.mp3"
        )
        if result:
            downloads.append(result)
        time.sleep(1)
    
    # Check uniqueness
    unique_ids = set(d['sound_id'] for d in downloads)
    
    print("\n" + "="*70)
    print("📊 ANTI-REPETITION SUMMARY")
    print("="*70)
    print(f"Downloaded: {len(downloads)} tracks")
    print(f"Unique: {len(unique_ids)} tracks")
    
    for i, d in enumerate(downloads, 1):
        print(f"{i}. {d['name']} (ID: {d['sound_id']})")
    
    if len(unique_ids) == len(downloads):
        print("\n🎉 SUCCESS! All tracks are different!")
    else:
        print(f"\n⚠️  Some repetition (pool might be small)")
    
    print("="*70 + "\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n🎵 MUSIC DOWNLOADER - LLM INTEGRATION VERSION\n")
    
    print("Choose test mode:")
    print("1. Test with LLM-style queries (5 different music types)")
    print("2. Test ContentStrategy integration (simulates your pipeline)")
    print("3. Test anti-repetition (same query 3 times)")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        test_with_llm_style_queries()
    elif choice == "2":
        test_content_strategy_integration()
    elif choice == "3":
        test_anti_repetition()
    else:
        print("Invalid choice. Exiting.")