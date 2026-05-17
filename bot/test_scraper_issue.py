from scraper import MangaScraper
import json

scraper = MangaScraper()
url = "https://mangatek.com/manga/white-dragon-duke-pendragon"

print(f"Scraping: {url}")
result = scraper.get_manga_details(url)
print(f"Found {len(result['chapters'])} chapters.")

if result['chapters']:
    print(f"Latest Ch: {result['chapters'][-1]['number']} - {result['chapters'][-1]['url']}")
    print(f"Oldest Ch: {result['chapters'][0]['number']} - {result['chapters'][0]['url']}")

# Let's see if we can find MORE chapters from the reader page
if result['chapters']:
    reader_url = result['chapters'][-1]['url']
    print(f"\nChecking Reader Context at: {reader_url}")
    res = scraper.scraper.get(reader_url, headers=scraper.headers)
    print(f"Reader Page Status: {res.status_code}")
    # Search for any large JSON blob
    blobs = re.findall(r'(\{"id":\d+,"number":".*?","title":".*?"\})', res.text)
    print(f"Found {len(blobs)} chapter-like blobs in reader page HTML.")
