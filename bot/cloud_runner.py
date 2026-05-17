"""
cloud_runner.py - GitHub Actions Daily/Hourly Scraper
===================================================
Runs a single pass to check for updates and discover new popular manhwa.
Designed to run on GitHub Actions cleanly and efficiently.
"""
import asyncio
import os
import sys

bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure environment uses utf-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

from tracker import MangaTracker
import main as bot_main
from data_manager import load_db, save_db
from scraper import MangaScraper

async def heal_database():
    """يفحص قاعدة البيانات أولاً: يصحح الأغلفة المفقودة ويحذف الفصول الفارغة ليتم سحبها مجدداً."""
    bot_main.add_log("🛠️ [Healer] Starting Data Integrity Check...", "info")
    db_changed = False
    db = load_db()
    scraper = MangaScraper()

    for entry in db:
        title = entry.get('title', 'Unknown')
        
        # 1. Check Covers
        cover = entry.get('cover', '')
        if not cover or cover == 'images/logo.png' or cover.startswith('http'):
            bot_main.add_log(f"  🔍 Healing cover for '{title}'...", "warning")
            new_cover_url = scraper.get_best_cover(title)
            if new_cover_url:
                local_path = await bot_main._download_cover(scraper, title, new_cover_url)
                if local_path:
                    entry['cover'] = local_path
                    db_changed = True
                    bot_main.add_log(f"    ✨ Cover fixed and downloaded!", "success")

        # 2. Check Broken Chapters (empty pages)
        chapters = entry.get('chapters', [])
        valid_chapters = []
        for ch in chapters:
            pages = ch.get('pages', [])
            if not pages or len(pages) == 0:
                bot_main.add_log(f"  🗑️ Removing broken chapter {ch.get('n')} from '{title}' for re-scraping...", "warning")
                db_changed = True
                # Don't add to valid_chapters, so it gets removed and then scraped again
            else:
                valid_chapters.append(ch)
        
        if len(valid_chapters) != len(chapters):
            entry['chapters'] = valid_chapters

    if db_changed:
        save_db(db)
        bot_main.add_log("🛠️ [Healer] Database cleaned and saved.", "success")
    else:
        bot_main.add_log("🛠️ [Healer] Database is healthy. No issues found.", "success")

async def run_cloud_updates():
    bot_main.add_log("☁️ [Cloud Runner] Starting background update...", "info")
    
    # 0. Heal Database
    await heal_database()

    # 1. Update Existing Tracker
    tracker = MangaTracker()
    tracked = tracker.get_all_tracked()
    
    if tracked:
        bot_main.add_log(f"🔄 Updating {len(tracked)} tracked manhwas...", "info")
        for key, data in tracked.items():
            url = data.get('url')
            title = data.get('title', key)
            if url:
                try:
                    bot_main.add_log(f"🔎 Checking: {title}...", "info")
                    await bot_main.scrape_manga(url, start_ch='auto')
                except Exception as e:
                    bot_main.add_log(f"⚠️ Error on {title}: {e}", "error")
    else:
        bot_main.add_log("📝 No mangas tracked yet.", "warning")

    # 2. Discover Popular Titles
    bot_main.add_log("🌍 Discovering Top 3 popular manhwa from sources...", "info")
    try:
        await bot_main.scrape_popular(3)
    except Exception as e:
        bot_main.add_log(f"⚠️ Error in popular discovery: {e}", "error")

    bot_main.add_log("✅ [Cloud Runner] Update cycle complete! Files are ready to be pushed to GitHub.", "success")

if __name__ == '__main__':
    try:
        asyncio.run(run_cloud_updates())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)




