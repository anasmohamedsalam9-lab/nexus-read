"""
Find a manhwa on supported Arabic sites (lek-manga, meshmanga, olympustaff)
"""
import sys, os
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import MangaScraper

scraper = MangaScraper()

# Try to discover popular manhwa from each source
sources = [
    {"name": "Lek-Manga", "url": "https://lek-manga.net/", "manga_base": "https://lek-manga.net/manga/"},
    {"name": "MeshManga", "url": "https://meshmanga.com/", "manga_base": "https://meshmanga.com/manga/"},
    {"name": "Olympus", "url": "https://olympustaff.com/", "manga_base": "https://olympustaff.com/series/"},
]

# Try specific popular manhwa URLs on each site
test_urls = [
    # Lek-Manga
    ("Lek-Manga", "https://lek-manga.net/manga/the-beginning-after-the-end/"),
    ("Lek-Manga", "https://lek-manga.net/manga/tower-of-god/"),
    ("Lek-Manga", "https://lek-manga.net/manga/omniscient-readers-viewpoint/"),
    ("Lek-Manga", "https://lek-manga.net/manga/nano-machine/"),
    ("Lek-Manga", "https://lek-manga.net/manga/the-greatest-estate-designer/"),
    # MeshManga  
    ("MeshManga", "https://meshmanga.com/manga/nano-machine/"),
    ("MeshManga", "https://meshmanga.com/manga/the-beginning-after-the-end/"),
    ("MeshManga", "https://meshmanga.com/manga/tower-of-god/"),
    ("MeshManga", "https://meshmanga.com/manga/return-of-the-blossoming-blade/"),
    # Olympus
    ("Olympus", "https://olympustaff.com/series/nano-machine"),
    ("Olympus", "https://olympustaff.com/series/the-beginning-after-the-end"),
]

print("=" * 60)
print("🔍 Searching for manhwa on supported Arabic sources...")
print("=" * 60)

for source_name, url in test_urls:
    print(f"\n[{source_name}] Trying: {url}")
    try:
        data = scraper.get_manga_details(url)
        title = data.get('title', 'Unknown')
        ch_count = len(data.get('chapters', []))
        if ch_count > 0:
            print(f"  ✅ FOUND: {title} — {ch_count} chapters")
            print(f"     Cover: {data.get('cover', 'N/A')[:60]}")
            print(f"     Genres: {data.get('genres', [])}")
            print(f"     Category: {data.get('category')}")
            # Print first chapter URL
            if data['chapters']:
                print(f"     First Ch: {data['chapters'][0]['url']}")
            print(f"\n🎯 USE THIS URL: {url}")
            break
        else:
            print(f"  ⚠️ No chapters: {title}")
    except Exception as e:
        err = str(e)[:80]
        print(f"  ❌ Error: {err}")
else:
    print("\n❌ None found. Trying discovery...")
    # Try the scraper's built-in discovery
    try:
        links = scraper.get_popular_from_all_sources(5)
        for l in links:
            # Skip mangatek
            if 'mangatek' in l['url']:
                continue
            print(f"  Discovered: {l['title']} -> {l['url']}")
    except Exception as e:
        print(f"  Discovery error: {e}")
