import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()
headers = {'User-Agent': 'Mozilla/5.0'}

def test_lek():
    url = "https://lek-manga.net/manga/the-return-of-the-unrivaled-genius-ranker/"
    print(f"Testing {url}")
    res = scraper.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'lxml')
    print(f"Title in h1: {soup.find('h1').text if soup.find('h1') else 'N/A'}")
    chapters = soup.select('.wp-manga-chapter a')
    print(f"Chapter links in HTML: {len(chapters)}")
    
    # Check for Load More
    load_more = soup.select_one('#load_more_chapters')
    print(f"Load more present: {load_more is not None}")

test_lek()
