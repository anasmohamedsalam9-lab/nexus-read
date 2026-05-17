import requests
import json
import re
import os
import time

def fetch_all_covers():
    # 1. Extract titles from data.js
    with open('data.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    titles = set(re.findall(r'title:\s*["\'](.+?)["\']', content))
    print(f"Found {len(titles)} unique titles in data.js")
    
    # Existing covers.json
    results = {}
    if os.path.exists('covers.json'):
        with open('covers.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
            
    query = '''
    query ($search: String) {
      Media (search: $search, type: MANGA) {
        coverImage {
          extraLarge
        }
      }
    }
    '''
    
    newly_fetched = 0
    for title in titles:
        if title in results and not results[title].startswith('https://i.imgur.com'):
            continue
            
        print(f"Fetching cover for: {title}")
        search_term = title.replace("(Master of Gu)", "").replace("Remake", "").strip()
        try:
            # Try manga first
            r = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'search': search_term}})
            data = r.json()
            if data.get('data') and data['data']['Media']:
                url = data['data']['Media']['coverImage']['extraLarge']
                results[title] = url
                newly_fetched += 1
            else:
                # Try search on another service or placeholder
                results[title] = "https://i.imgur.com/rL71C5k.jpeg"
            time.sleep(0.7)
        except Exception as e:
            print(f"  Error: {e}")
            
    # Save back to covers.json
    with open('covers.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print(f"Finished. Newly fetched: {newly_fetched}")

if __name__ == "__main__":
    fetch_all_covers()
