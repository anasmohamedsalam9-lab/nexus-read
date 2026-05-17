import cloudscraper
import json

scraper = cloudscraper.create_scraper()
headers = {'User-Agent': 'Mozilla/5.0'}

def check_api(slug):
    for p in range(1, 4):
        url = f"https://mangatek.com/api/manga/{slug}?page={p}&limit=50"
        print(f"Testing Page {p}: {url}")
        res = scraper.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            chapters = data.get('chapters', [])
            print(f"  Found {len(chapters)} chapters.")
            if chapters:
                print(f"  First Ch: {chapters[0]['number']}, Last Ch: {chapters[-1]['number']}")
        else:
            print(f"  Error {res.status_code}")

check_api('white-dragon-duke-pendragon')
