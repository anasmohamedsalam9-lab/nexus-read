import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()
headers = {'User-Agent': 'Mozilla/5.0'}

def debug_response(url):
    print(f"\n--- Debugging URL: {url} ---")
    res = scraper.get(url, headers=headers)
    print(f"Status Code: {res.status_code}")
    print(f"Response Length: {len(res.text)}")
    print(f"Response HTML Head (Title): {BeautifulSoup(res.text, 'lxml').title}")
    
    soup = BeautifulSoup(res.text, 'lxml')
    # Find all h1, h2, h3
    hs = [h.text.strip() for h in soup.find_all(['h1', 'h2', 'h3'])]
    print(f"Headers found: {hs[:10]}")
    
    # Links
    links = [a['href'] for a in soup.find_all('a', href=True) if '/chapter/' in a['href'] or '/reader/' in a['href'] or '/manga/' in a['href']]
    print(f"Potential chapter links: {len(links)}")

debug_response("https://lek-manga.net/manga/the-beginning-after-the-end/")
debug_response("https://mangatek.com/manga/one-piece")
