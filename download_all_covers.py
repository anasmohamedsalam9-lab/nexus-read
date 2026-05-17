import json
import requests
import os
import re

def title_to_slug(title):
    # Same as in data.js to maintain consistency
    return title.lower().replace(" (master of gu)", "").replace("_", "").replace(" ", "-").replace("'", "").replace("&", "and").strip("-")

def download_all():
    with open('covers.json', 'r', encoding='utf-8') as f:
        covers = json.load(f)
    
    os.makedirs('assets/covers', exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for title, url in covers.items():
        slug = title_to_slug(title)
        # Handle different potential extensions from the URL
        ext = '.jpg'
        if '.png' in url.lower():
            ext = '.png'
        elif '.webp' in url.lower():
            ext = '.webp'
            
        filepath = os.path.join('assets', 'covers', f'{slug}{ext}')
        
        print(f"Downloading {title} -> {filepath}...")
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(r.content)
                print(f"  SUCCESS (size: {len(r.content)} bytes)")
            else:
                print(f"  FAILED (status: {r.status_code})")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    download_all()
