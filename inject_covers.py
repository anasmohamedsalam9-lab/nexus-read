import json
import re
import os

# Manual mappings for titles that differ between data.js and covers.json
MANUAL_MAPPINGS = {
    "Reverend Insanity Remake": "Reverend Insanity",
    "Pick Me Up _ Infinite Gacha": "Pick Me Up Infinite Gacha",
    "Reverend Insanity (Master of Gu)": "Reverend Insanity"
}

def inject():
    with open('covers.json', 'r', encoding='utf-8') as f:
        covers = json.load(f)
        
    with open('data.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_count = 0
    
    # Titles in data.js to check
    all_titles_in_js = re.findall(r'title:\s*["\'](.+?)["\']', content)
    
    for js_title in set(all_titles_in_js):
        # Check manual mapping first
        search_title = MANUAL_MAPPINGS.get(js_title, js_title)
        
        if search_title in covers:
            new_img = covers[search_title]
            # Use escaped title for regex to avoid issues with special characters
            escaped_title = re.escape(js_title)
            # Pattern to find title and its subsequent img property
            pattern = r'(title:\s*["\']' + escaped_title + r'["\'][^}]*?img:\s*["\'])(.+?)(["\'])'
            
            def replace_func(match):
                nonlocal updated_count
                old_img = match.group(2)
                if old_img != new_img:
                    updated_count += 1
                    return match.group(1) + new_img + match.group(3)
                return match.group(0)
            
            content = re.sub(pattern, replace_func, content, flags=re.DOTALL)

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully updated image URLs for {updated_count} entries in data.js")

if __name__ == "__main__":
    inject()
