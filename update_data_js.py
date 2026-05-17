import os
import re

def title_to_slug(title):
    # Normalized for mapping - remove punctuation instead of replacing with dash
    s = title.lower()
    s = s.replace(" (master of gu)", "").replace("(master of gu)", "").replace("remake", "").strip()
    # Remove apostrophes first
    s = s.replace("'", "")
    # Replace other non-alphanumeric with dash
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s

def update_data_js():
    # 1. Map available files by their normalized slug
    files = os.listdir('assets/covers')
    file_map = {}
    for f in files:
        name = os.path.splitext(f)[0]
        # Ignore broken placeholders
        if os.path.getsize(os.path.join('assets/covers', f)) < 2000:
            continue
        
        slug = title_to_slug(name)
        file_map[slug] = f
        
    # Manual Additions to map
    file_map['omniscient-reader'] = file_map.get('omniscient-readers-viewpoint', '')
    
    print(f"Mapped {len(file_map)} slugs to files.")

    # 2. Read data.js
    with open('data.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. Update paths
    all_titles = set(re.findall(r'title:\s*["\'](.+?)["\']', content))
    
    updated_count = 0
    for title in all_titles:
        slug = title_to_slug(title)
        
        # Try to find a file
        filename = file_map.get(slug)
        
        if filename:
            local_path = f"assets/covers/{filename}"
            # Escape title for regex
            escaped_title = re.escape(title)
            # Find title and then img in a single group
            # We use a non-greedy match that doesn't cross closing brackets or next titles
            pattern = r'(title:\s*["\']' + escaped_title + r'["\'][^}]*?img:\s*["\'])(.+?)(["\'])'
            
            def replace_func(match):
                nonlocal updated_count
                old_img = match.group(2)
                if old_img != local_path:
                    updated_count += 1
                    return match.group(1) + local_path + match.group(3)
                return match.group(0)
            
            content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
        else:
            print(f"No local file for: {title} (slug: {slug})")

    # 4. Write back
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully updated {updated_count} image paths in data.js")

if __name__ == "__main__":
    update_data_js()
