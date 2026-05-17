"""
fix_covers.py - Enhanced bulk update to repair all missing/broken covers using multiple sources.
"""
import asyncio
import os
import sys

# Add current dir to sys.path
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import MangaScraper
from data_manager import load_db, save_db, slugify

# Project root
PROJECT_ROOT = os.path.dirname(bot_dir)

async def download_cover(scraper, title):
    try:
        slug = slugify(title)
        cover_dir = os.path.join(PROJECT_ROOT, 'assets', 'covers')
        os.makedirs(cover_dir, exist_ok=True)
        cover_path = os.path.join(cover_dir, f"{slug}.webp")

        best_url = scraper.get_best_cover(title)
        if not best_url:
            return ""

        print(f"  📥 Downloading from: {best_url}")
        # Try cloudscraper first, fallback to simple requests
        try:
            resp = scraper.scraper.get(best_url, timeout=15, headers={'User-Agent': scraper.headers['User-Agent']})
        except:
            import requests
            resp = requests.get(best_url, timeout=15, headers={'User-Agent': scraper.headers['User-Agent']})

        if resp.status_code == 200:
            from PIL import Image as PILImage
            from io import BytesIO as BIO
            img = PILImage.open(BIO(resp.content)).convert('RGB')
            img.save(cover_path, 'WEBP', quality=85)
            return f"assets/covers/{slug}.webp"
        
        return ""
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return ""

async def main():
    db = load_db()
    scraper = MangaScraper()
    print(f"Starting Emergency Cover Repair for {len(db)} entries...")

    for i, entry in enumerate(db):
        title = entry.get('title', '')
        print(f"[{i+1}/{len(db)}] {title}")
        
        new_path = await download_cover(scraper, title)
        if new_path:
            entry['cover'] = new_path
            print(f"  ✅ Fixed!")
        else:
            print(f"  ⚠️ Still missing")
            
        if (i+1) % 4 == 0:
            save_db(db)

    save_db(db)
    print("\n--- Repair Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
