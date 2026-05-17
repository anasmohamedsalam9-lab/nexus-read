import os
import sys
import time
import json
import re

# Add bot directory to path
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from scraper import MangaScraper
from data_manager import load_db, find_entry, upsert_manga

def load_tracker():
    tracker_path = os.path.join(bot_dir, 'tracked_mangas.json')
    if os.path.exists(tracker_path):
        with open(tracker_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def update_metadata(batch_size=10):
    scraper = MangaScraper()
    db = load_db()
    tracker = load_tracker()
    
    # Identify items needing updates
    # 1. Missing cover
    # 2. Placeholder description
    # 3. Missing genres
    to_update = []
    for item in db:
        title = item.get('title', '')
        cover = item.get('cover', '')
        desc = item.get('desc', '') or ''
        
        needs_cover = not cover or 'default-cover' in cover
        needs_desc = not desc or 'قصة مشوقة' in desc or len(desc) < 20
        
        if needs_cover or needs_desc:
            to_update.append(item)
            
    print(f"[Updater] Found {len(to_update)} items needing metadata updates.")
    
    processed = 0
    for item in to_update:
        if processed >= batch_size:
            print(f"[Updater] Reached batch size limit ({batch_size}). Stopping for now.")
            break
            
        title = item.get('title', '')
        print(f"[Updater] Processing: '{title}'...")
        
        # Determine source URL
        url = None
        # Step 1: Check tracker
        key = title.lower()
        if key in tracker:
            url = tracker[key].get('url')
        
        # Step 2: Try to search if no URL (optional/limited to avoid bot detection)
        if not url:
            print(f"[Updater] No URL in tracker for '{title}'. Searching...")
            search_results = scraper.search_manga(title)
            if search_results:
                # Pick the best match (first one)
                url = search_results[0].get('url')
                print(f"[Updater] Found URL via search: {url}")
        
        if url:
            try:
                print(f"[Updater] Fetching details from {url}...")
                details = scraper.get_manga_details(url)
                
                # Update DB
                # Note: upsert_manga already handles merging
                upsert_manga(
                    title=title,
                    cover=details.get('cover', ''),
                    desc=details.get('description', ''),
                    genres=details.get('genres', []),
                    status=details.get('status', 'Ongoing')
                )
                print(f"[Updater] SUCCESS: Updated '{title}'")
                processed += 1
            except Exception as e:
                print(f"[Updater] ERROR fetching '{title}': {e}")
        else:
            print(f"[Updater] SKIP: Could not find URL for '{title}'")
            
        # Delay to avoid IP ban
        time.sleep(3)

if __name__ == "__main__":
    # If arguments are passed, use them as title to update specific ones
    if len(sys.argv) > 1:
        # Simple manual mode (not implemented here but could be)
        pass
    else:
        update_metadata(batch_size=20) # Process 20 items per run
