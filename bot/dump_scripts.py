import cloudscraper
from bs4 import BeautifulSoup
import re

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

def dump_scripts(url):
    print(f"Dumping scripts from: {url}")
    res = scraper.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    scripts = soup.find_all('script')
    for i, script in enumerate(scripts):
        if script.string:
            # Print first 100 chars and search for 'chapter'
            if 'chapter' in script.string.lower() or 'chapters' in script.string.lower():
                print(f"\n--- Script {i} (contains 'chapter') ---")
                print(script.string[:500])
                print(f"Length: {len(script.string)}")
        elif script.get('id'):
            print(f"\n--- Script {i} (ID: {script.get('id')}) ---")
            print(f"SRC: {script.get('src')}")

dump_scripts("https://mangatek.com/manga/white-dragon-duke-pendragon")
