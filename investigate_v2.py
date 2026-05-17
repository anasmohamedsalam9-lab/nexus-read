import cloudscraper
from bs4 import BeautifulSoup
import re
import json

scraper = cloudscraper.create_scraper()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def check_site(name, url):
    print(f"\n--- Checking {name} ({url}) ---")
    try:
        res = scraper.get(url, headers=headers, timeout=15)
        # Fix encoding for Arabic
        res_text = res.content.decode('utf-8', errors='ignore')
        soup = BeautifulSoup(res_text, 'lxml')
        
        # 1. Check title
        print(f"Title: {soup.title.text.strip()}")
        
        # 2. Check chapter count in initial HTML
        chapters = soup.find_all('a', href=re.compile(r'/reader/|/chapter/|/manga/'))
        # Specific filter for Mangatek reader links
        reader_links = [a for a in chapters if '/reader/' in a['href']]
        print(f"Reader links (Mangatek): {len(reader_links)}")
        
        # 3. Check for 'manga_id' or 'post_id'
        manga_id = re.search(r'id="manga-style-id-(\d+)"|data-id="(\d+)"|manga-(\d+)', res_text)
        if manga_id:
            found_id = manga_id.group(1) or manga_id.group(2) or manga_id.group(3)
            print(f"Detected ID: {found_id}")
            
        # 4. Check for 'Load More' or 'Next Page'
        load_more = soup.find(id='load_more_chapters') or soup.select_one('.btn-load-more')
        if load_more:
            print(f"Load more button detected: {load_more.get('id') or load_more.get('class')}")

        # 5. Check for JSON in script tags (for SPAs)
        scripts = soup.find_all('script')
        for s in scripts:
            if s.string and 'chapters' in s.string.lower() and len(s.string) > 1000:
                print("Potential big JSON in script tag detected.")

    except Exception as e:
        print(f"Error: {e}")

# Test URLs
check_site("Mangatek (One Piece)", "https://mangatek.com/manga/one-piece")
check_site("LekManga (TBATE)", "https://lek-manga.net/manga/the-beginning-after-the-end/")
