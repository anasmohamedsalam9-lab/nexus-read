import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}

def test_discovery(url, selectors):
    print(f"\n--- Testing Discovery for {url} ---")
    try:
        res = scraper.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'lxml')
        links = []
        seen = set()
        
        for selector in selectors:
            found = soup.select(selector)
            for el in found:
                href = el.get('href')
                if href and '/manga/' in href or '/series/' in href:
                    if not href.startswith('http'):
                        from urllib.parse import urlparse
                        p = urlparse(url)
                        href = f"{p.scheme}://{p.netloc}{href}"
                    if href not in seen:
                        seen.add(href)
                        links.append(href)
                        if len(links) >= 10: break
            if len(links) >= 10: break
            
        print(f"Found {len(links)} links:")
        for l in links: print(f"  - {l}")
    except Exception as e:
        print(f"Error: {e}")

# Sources and their likely selectors
sources = [
    ("https://mangatek.com", ["a[href*='/manga/']"]),
    ("https://lek-manga.net", [".page-item-detail.manga a", ".manga-title h3 a", "a[href*='/manga/']"]),
    ("https://meshmanga.com", [".page-item-detail.manga a", ".manga-title h3 a", "a[href*='/manga/']"]),
    ("https://olympustaff.com", ["a[href*='/series/']"])
]

for url, selectors in sources:
    test_discovery(url, selectors)
