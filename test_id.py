import cloudscraper
import re

scraper = cloudscraper.create_scraper()
url = "https://lek-manga.net/manga/white-dragon-duke-pendragon/"
response = scraper.get(url)

with open("lek_manga_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

# Look for manga id
manga_id = re.search(r'data-id="(\d+)"', response.text)
if manga_id:
    print(f"Manga ID found: {manga_id.group(1)}")
else:
    # Try another selector
    manga_id = re.search(r'manga-(\d+)', response.text)
    if manga_id:
        print(f"Manga ID found (manga-): {manga_id.group(1)}")
    else:
        print("Manga ID not found")
