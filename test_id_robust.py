import cloudscraper
import re

scraper = cloudscraper.create_scraper()
url = "https://lek-manga.net/manga/white-dragon-duke-pendragon/"
response = scraper.get(url)

with open("lek_manga_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

# Search for common Madara ID markers
patterns = [
    r'id="manga-style-id-(\d+)"',
    r'data-id="(\d+)"',
    r'post-(\d+)',
    r'var manga_id = "(\d+)";',
    r'manga-(\d+)'
]

for pattern in patterns:
    matches = re.findall(pattern, response.text)
    if matches:
        print(f"Pattern {pattern} matched: {matches}")

# Also try looking for AJAX endpoints
if "wp-admin/admin-ajax.php" in response.text:
    print("Found admin-ajax.php")
if "ajax/chapters" in response.text:
    print("Found ajax/chapters")
