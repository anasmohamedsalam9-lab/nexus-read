import json
import re
import os

data_path = r"A:\nexus\data.js"
print(f"Reading {data_path}...")

with open(data_path, "r", encoding="utf-8") as f:
    text = f.read()

match = re.search(r'var\s+DB\s*=\s*(\[.*\])\s*;', text, re.DOTALL)
if match:
    json_str = match.group(1)
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    try:
        db = json.loads(json_str)
        initial_len = len(db)
        
        # 1. Remove the duplicate 'ون پیس' (with trailing spaces just in case)
        db = [entry for entry in db if entry.get('title', '').strip() != 'ون پیس']
        print(f"Removed duplicate entries. Size went from {initial_len} to {len(db)}")
        
        # 2. Update the demo_one-piece-translated entry
        for entry in db:
            if entry.get('id') == 'demo_one-piece-translated':
                for ch in entry.get('chapters', []):
                    if str(ch.get('n')) == '2':
                        print("Updating Chapter 2 pages to 25 pages...")
                        ch['pages'] = [f"assets/chapters/one-piece-official-colored/ch-2/{i}.webp" for i in range(1, 26)]
                        break
                break
                
        # 3. Save back
        new_json = json.dumps(db, ensure_ascii=False, indent=2)
        with open(data_path, "w", encoding="utf-8") as f:
            f.write(f"var DB = {new_json};")
        print("Healed data.js successfully!")
    except Exception as e:
        print("Error processing JSON:", e)
else:
    print("Could not find var DB = [...] in data.js")
