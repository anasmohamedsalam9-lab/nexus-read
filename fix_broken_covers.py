import requests
import os

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

corrections = [
    {
        "title": "A Regressor's Tale of Cultivation",
        "url": "https://s4.anilist.co/file/anilistcdn/media/manga/cover/large/bx178656-LqR9vLzWkP6m.jpg",
        "slug": "a-regressors-tale-of-cultivation"
    },
    {
        "title": "The Beginning After The End",
        "url": "https://s4.anilist.co/file/anilistcdn/media/manga/cover/large/bx108685-6pY6Y6pY6Y6p.jpg", # Alternative
        "slug": "the-beginning-after-the-end"
    },
    {
        "title": "Superman",
        "url": "https://m.media-amazon.com/images/I/91vYQFTF-bL._AC_UF1000,1000_QL80_.jpg",
        "slug": "superman"
    }
]

def fix_broken():
    for item in corrections:
        path = f"assets/covers/{item['slug']}.jpg"
        print(f"Fixing {item['title']}...")
        try:
            r = requests.get(item['url'], headers=headers, timeout=15)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(r.content)
                print(f"  SUCCESS: {len(r.content)} bytes")
            else:
                print(f"  FAILED: Status {r.status_code}")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    fix_broken()
