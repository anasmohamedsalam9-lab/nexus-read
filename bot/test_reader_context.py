import cloudscraper
import re
import json
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}

def test_reader_context(url):
    print(f"Testing Reader Context for: {url}")
    res = scraper.get(url, headers=headers)
    
    # Search for __NEXT_DATA__
    next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
    if next_data_match:
        print("Found __NEXT_DATA__!")
        data = json.loads(next_data_match.group(1))
        
        # Try to find 'chapters' array
        def find_chapters(obj):
            if isinstance(obj, dict):
                if 'chapters' in obj and isinstance(obj['chapters'], list):
                    return obj['chapters']
                for k, v in obj.items():
                    found = find_chapters(v)
                    if found: return found
            elif isinstance(obj, list):
                for item in obj:
                    found = find_chapters(item)
                    if found: return found
            return None

        chapters = find_chapters(data)
        if chapters:
            print(f"Total Chapters found in Reader Context: {len(chapters)}")
            if len(chapters) > 0:
                print(f"First chapter in list: {chapters[0].get('number') or chapters[0].get('id')}")
                print(f"Last chapter in list: {chapters[-1].get('number') or chapters[-1].get('id')}")
        else:
            print("No 'chapters' array found in __NEXT_DATA__")
    else:
        print("No __NEXT_DATA__ found")

# Test with a Pendragon reader URL (I saw it was ch 131)
test_reader_context("https://mangatek.com/reader/19325") # This is likely a reader URL for a chapter
