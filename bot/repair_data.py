import os
import re
import json

data_path = r'f:\anas\موقع\nile-manhwa\data.js'

def repair_data_js():
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Detect the corruption in LATEST_MANGA_START
    # Current: /* LATEST_MANGA_START */\n    "title": "ordeal"
    # Needs: /* LATEST_MANGA_START */\n    { "title": "ordeal"
    
    # Let's try a regex to find blocks that look like objects but miss the start brace
    # and are between LATEST_..._START and LATEST_..._END
    
    markers = [
        ('/* LATEST_MANGA_START */', '/* LATEST_MANGA_END */'),
        ('/* LATEST_MANHWA_START */', '/* LATEST_MANHWA_END */')
    ]
    
    new_content = content
    for start, end in markers:
        if start in new_content and end in new_content:
            parts = new_content.split(start)
            head = parts[0]
            rest = parts[1].split(end)
            mid = rest[0]
            tail = rest[1]
            
            # If mid contains "title" but not '{' at the start of the first entry
            mid_stripped = mid.strip()
            if mid_stripped and not mid_stripped.startswith('{'):
                print(f"Repairing missing braces in {start} section...")
                # Try to wrap each "title" block in braces if missing
                # A simple way: find indices of "title": and wrap until the next "title": or end
                items = []
                # Split by "title": but keep the delimiter's effect
                raw_items = re.split(r'(?=\{\s*"title"|(?<!\{)\s*"title")', mid)
                for raw in raw_items:
                    raw = raw.strip().rstrip(',')
                    if not raw: continue
                    if not raw.startswith('{'):
                        raw = '{' + raw + '}'
                    items.append(raw)
                
                new_mid = ",\n".join(items)
                new_content = f"{head}{start}\n{new_mid}\n{end}{tail}"

    # Final sanity check: try to find any "title": that isn't preceded by { or , 
    # but let's just write and see.
    
    with open(data_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Repaired data.js syntax errors.")

if __name__ == "__main__":
    repair_data_js()
