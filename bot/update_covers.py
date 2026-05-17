"""
update_covers.py - Bulk update covers for existing manga in data.js using MangaKatana.
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
    """Reuse logic for downloading cover."""
    try:
        slug = slugify(title)
        cover_dir = os.path.join(PROJECT_ROOT, 'assets', 'covers')
        os.makedirs(cover_dir, exist_ok=True)
        cover_path = os.path.join(cover_dir, f"{slug}.webp")

        # Force redownload if file is tiny/broken
        # if os.path.exists(cover_path) and os.path.getsize(cover_path) > 1000:
        #    return f"assets/covers/{slug}.webp"

        print(f"  🔍 Searching MangaKatana for '{title}'...")
        mk_cover = scraper.get_mangakatana_cover(title)
        
        if not mk_cover:
            print(f"  ⚠️ No cover found on MangaKatana for '{title}'")
            return ""

        print(f"  📥 Downloading cover from: {mk_cover}")
        resp = scraper.scraper.get(mk_cover, timeout=20, headers={
            'User-Agent': scraper.headers['User-Agent']
        })
        
        if resp.status_code == 200:
            try:
                from PIL import Image as PILImage
                from io import BytesIO as BIO
                img = PILImage.open(BIO(resp.content)).convert('RGB')
                img.save(cover_path, 'WEBP', quality=90)
            except Exception as e:
                with open(cover_path, 'wb') as f:
                    f.write(resp.content)

            return f"assets/covers/{slug}.webp"
        else:
            print(f"  ❌ Failed to download: {resp.status_code}")
            return ""
    except Exception as e:
        print(f"  ❌ Error processing cover for '{title}': {e}")
        return ""

async def main():
    db = load_db()
    if not db:
        print("Empty database. Nothing to update.")
        return

    scraper = MangaScraper()
    print(f"Starting bulk cover update for {len(db)} entries...")

    updated_count = 0
    for i, entry in enumerate(db):
        title = entry.get('title', 'Unknown')
        print(f"[{i+1}/{len(db)}] Processing: {title}")
        
        new_cover = await download_cover(scraper, title)
        if new_cover:
            entry['cover'] = new_cover
            updated_count += 1
            print(f"  ✅ Updated cover: {new_cover}")
        
        # Save periodically
        if (i+1) % 5 == 0:
            save_db(db)
            print("--- Intermediate save completed ---")

    save_db(db)
    print(f"\nCompleted! Updated {updated_count} covers.")

if __name__ == "__main__":
    asyncio.run(main())
