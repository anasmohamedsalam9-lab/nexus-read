import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def check_site(name, url, chapter_pattern):
    print(f"\n--- Checking {name} ({url}) ---")
    try:
        res = requests.get(url, headers=headers, timeout=15)
        # Fix encoding for Arabic
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'lxml')
        
        # 1. Check title and description
        print(f"Title: {soup.title.text.strip()}")
        desc = soup.select_one('.description-summary, .manga-excerpt, .summary__content, .text-gray-400')
        if desc:
            print(f"Description sample: {desc.text.strip()[:100]}...")
            
        # 2. Check chapter count in initial HTML
        chapters = soup.find_all('a', href=re.compile(chapter_pattern))
        print(f"Chapters in initial HTML: {len(chapters)}")
        
        # 3. Check for 'manga_id' or similar for AJAX (Madara)
        manga_id = re.search(r'id="manga-style-id-(\d+)"', res.text) or \
                   re.search(r'data-id="(\d+)"', res.text) or \
                   re.search(r'manga-(\d+)', res.text)
        if manga_id:
            print(f"Detected Manga ID: {manga_id.group(1)}")
            
        # 4. Check for 'button' or 'load more'
        buttons = [b.text.strip() for b in soup.find_all(['button', 'a']) if 'load' in b.text.lower() or 'عرض المزيد' in b.text]
        if buttons:
            print(f"Load more buttons found: {buttons}")

    except Exception as e:
        print(f"Error: {e}")

# Test URLs
check_site("Mangatek (One Piece)", "https://mangatek.com/manga/one-piece", r'/reader/')
check_site("LekManga (TBATE)", "https://lek-manga.net/manga/the-beginning-after-the-end/", r'/manga/')
