"""
Test script to find Solo Leveling on Arabic manga sources and scrape it.
"""
import sys
import os

# Ensure 'bot' directory is in the path
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

# Windows CMD Unicode Fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from scraper import MangaScraper

def find_solo_leveling():
    scraper = MangaScraper()
    
    # Try known URLs for Solo Leveling on Arabic sites
    possible_urls = [
        "https://lek-manga.net/manga/solo-leveling/",
        "https://lek-manga.net/manga/solo-leveling-manga/",
        "https://mangatek.com/manga/solo-leveling",
        "https://mangatek.com/manga/solo-leveling-manhwa",
        "https://meshmanga.com/manga/solo-leveling/",
    ]
    
    for url in possible_urls:
        print(f"\n{'='*60}")
        print(f"Trying: {url}")
        print(f"{'='*60}")
        try:
            data = scraper.get_manga_details(url)
            if data and data.get('chapters'):
                print(f"\n✅ FOUND: {data['title']}")
                print(f"   Cover: {data.get('cover', 'N/A')[:80]}...")
                print(f"   Genres: {data.get('genres', [])}")
                print(f"   Rating: {data.get('rating')}")
                print(f"   Chapters: {len(data['chapters'])}")
                print(f"   Category: {data.get('category')}")
                print(f"   Description: {data.get('description', '')[:100]}...")
                # Print first 3 chapter URLs for verification
                for ch in data['chapters'][:3]:
                    print(f"   Ch {ch['number']}: {ch['url']}")
                return url, data
            else:
                print(f"   ⚠️ Got data but no chapters: {data.get('title', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # If none found, try search approach
    print("\n\n🔍 Trying search approach...")
    try:
        search_urls = [
            "https://lek-manga.net/?s=solo+leveling",
            "https://mangatek.com/api/search?q=solo-leveling",
        ]
        for search_url in search_urls:
            print(f"\nSearching: {search_url}")
            try:
                resp = scraper.scraper.get(search_url, headers=scraper.headers, timeout=15)
                print(f"   Status: {resp.status_code}")
                if resp.status_code == 200 and len(resp.text) > 100:
                    # Check for manga links
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'lxml')
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        text = link.get_text(strip=True)
                        if 'solo' in href.lower() or 'solo' in text.lower():
                            print(f"   Found link: {text} -> {href}")
            except Exception as e:
                print(f"   Error: {e}")
    except Exception as e:
        print(f"Search failed: {e}")
    
    return None, None

if __name__ == "__main__":
    url, data = find_solo_leveling()
    if url:
        print(f"\n\n🎉 Solo Leveling found at: {url}")
        print(f"Total chapters: {len(data['chapters'])}")
    else:
        print("\n\n❌ Solo Leveling not found on any supported source.")
