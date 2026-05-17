"""
Test scraping Martial Peak from Olympus Staff then verify on reading site
"""
import sys, os
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import MangaScraper

scraper = MangaScraper()

# Try Olympus Staff URLs
urls = [
    "https://olympustaff.com/series/martial-peak",
    "https://olympustaff.com/series/demonic-emperor",
    "https://olympustaff.com/series/eleceed",
    "https://olympustaff.com/series/ECD",
]

for url in urls:
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print(f"{'='*60}")
    try:
        data = scraper.get_manga_details(url)
        title = data.get('title', 'Unknown')
        ch_count = len(data.get('chapters', []))
        cover = data.get('cover', '')
        genres = data.get('genres', [])
        desc = data.get('description', '')[:80]
        cat = data.get('category', 'unknown')
        
        print(f"  Title: {title}")
        print(f"  Chapters: {ch_count}")
        print(f"  Cover: {cover[:60]}...")
        print(f"  Genres: {genres}")
        print(f"  Category: {cat}")
        print(f"  Description: {desc}...")
        
        if ch_count > 0:
            print(f"\n  First 3 chapters:")
            for ch in data['chapters'][:3]:
                print(f"    Ch {ch['number']}: {ch['url']}")
            
            # Test getting images from first chapter
            print(f"\n  📸 Testing chapter image extraction from Ch {data['chapters'][0]['number']}...")
            images = scraper.get_chapter_images(data['chapters'][0]['url'])
            print(f"     Found {len(images)} images!")
            if images:
                for i, img in enumerate(images[:3]):
                    print(f"     Page {i+1}: {img[:70]}...")
            
            print(f"\n  ✅ This source WORKS! Use URL: {url}")
            break
        else:
            print(f"  ⚠️ No chapters found")
    except Exception as e:
        print(f"  ❌ Error: {e}")
