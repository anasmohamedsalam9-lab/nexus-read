import os
import re

def title_to_slug(title):
    s = title.lower()
    s = s.replace(" (master of gu)", "").replace("(master of gu)", "").replace("remake", "").strip()
    s = s.replace("'", "")
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s

def final_fix():
    # Map files
    files = os.listdir('assets/covers')
    file_map = {}
    for f in files:
        if os.path.getsize(os.path.join('assets/covers', f)) < 2000:
            continue
        slug = title_to_slug(os.path.splitext(f)[0])
        file_map[slug] = f

    with open('data.js', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    updated = 0
    
    for line in lines:
        if 'title:' in line and 'img:' in line:
            # Try to extract title
            t_match = re.search(r'title:\s*["\'](.+?)["\']', line)
            if t_match:
                title = t_match.group(1)
                slug = title_to_slug(title)
                
                # Special cases
                if 'omniscient-reader' in slug: slug = 'omniscient-readers-viewpoint'
                if 'reverend-insanity' in slug: slug = 'reverend-insanity'
                
                if slug in file_map:
                    local_path = f"assets/covers/{file_map[slug]}"
                    # Replace whatever is in img: "..."
                    new_line = re.sub(r'(img:\s*["\'])(.+?)(["\'])', r'\g<1>' + local_path + r'\g<3>', line)
                    if new_line != line:
                        updated += 1
                        line = new_line
        new_lines.append(line)

    with open('data.js', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Final Fix: Updated {updated} lines.")

if __name__ == "__main__":
    final_fix()
