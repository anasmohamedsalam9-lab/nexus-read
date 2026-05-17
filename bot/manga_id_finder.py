import cloudscraper
import requests
import json

scraper = cloudscraper.create_scraper()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://mangatek.com/'
}

def test_reader_endpoints(slug):
    print(f"Testing Reader-related endpoints for: {slug}...")
    
    # Try fetching the first known chapter id or the manga id
    try:
        # Strategy A: Main API but looking for the FULL list if it exists
        manga_url = f"https://mangatek.com/api/manga/{slug}"
        res = scraper.get(manga_url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            chapters = data.get('chapters', [])
            print(f"[Main API] Found {len(chapters)} chapters in the main object.")
            if chapters:
                # Test if we can get MORE via a chapter-details call
                first_ch_id = chapters[0].get('id')
                ch_url = f"https://mangatek.com/api/chapter/{first_ch_id}"
                print(f"Testing Chapter Details API: {ch_url}")
                r = scraper.get(ch_url, headers=headers)
                if r.status_code == 200:
                    ch_data = r.json()
                    # Look for 'manga' -> 'chapters' or similar navigation props
                    all_ch = ch_data.get('manga', {}).get('chapters', [])
                    print(f"  --> FOUND {len(all_ch)} chapters in the Reader context!")
                    if len(all_ch) > len(chapters):
                        print(f"  [!!!] SUCCESS: Reader context provides full history.")
                        return
        else:
            print(f"[Error] 404 for {manga_url}")
    except Exception as e:
        print(f"[Error] Request failed: {e}")

test_reader_endpoints('white-dragon-duke-pendragon')
