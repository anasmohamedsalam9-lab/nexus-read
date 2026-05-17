import cloudscraper
import re
import json

scraper = cloudscraper.create_scraper()
headers = {'User-Agent': 'Mozilla/5.0'}

def find_hidden_chapters(slug):
    url = f"https://mangatek.com/manga/{slug}"
    print(f"Investigating: {url}")
    res = scraper.get(url, headers=headers)
    
    # 1. Search for JSON in scripts
    scripts = re.findall(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
    if scripts:
        print("Found __NEXT_DATA__!")
        data = json.loads(scripts[0])
        # Drill down into props...
        # Common structure: props -> pageProps -> manga -> chapters
        # Or similar. I'll just print keys to find it.
        def find_key(obj, target):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == target: return v
                    res = find_key(v, target)
                    if res: return res
            elif isinstance(obj, list):
                for i in obj:
                    res = find_key(i, target)
                    if res: return res
            return None
        
        manga = find_key(data, 'manga')
        if manga and 'chapters' in manga:
            print(f"Total Chapters in __NEXT_DATA__: {len(manga['chapters'])}")
            return
            
    # 2. Search for any large array in text
    arrays = re.findall(r'\[\{"id":.*?"number":.*?\}\]', res.text)
    if arrays:
        for arr in arrays:
            try:
                data = json.loads(arr)
                if len(data) > 10:
                    print(f"Found array with {len(data)} chapters in script body!")
                    return
            except: pass

find_hidden_chapters('white-dragon-duke-pendragon')
