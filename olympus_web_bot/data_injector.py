import os
import re
import json

DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.js')

def load_data():
    if not os.path.exists(DATA_FILE_PATH):
        return ""
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def save_data(content):
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def add_or_update_manga_in_datajs(manga_obj):
    """
    manga_obj: dict containing title, img, rating, genres, description, chapters
    """
    content = load_data()
    if not content:
        print("data.js not found at", DATA_FILE_PATH)
        return False
        
    title = manga_obj['title']
    
    # We serialize the object with indent
    # JavaScript requires standard JSON so json.dumps works perfectly
    manga_json = json.dumps(manga_obj, ensure_ascii=False, indent=4)
    # Adjust formatting slightly so it aligns with standard structure
    manga_json = '\n'.join('    ' + line for line in manga_json.split('\n'))
    
    escaped_title = re.escape(title)
    
    # Check if manga exists in the file
    # We look for a pattern that matches the whole object for this title
    # Since our JSON always ends with `]    }` (chapters array end and object end), we can use a non-greedy patch.
    # Note: JSON dumps output:
    # {
    #     "title": "Manga",
    #     ...
    #     "chapters": [
    #         ...
    #         ]
    #     }
    # }
    
    # Simpler approach: find `{"title": "Title"` or `{ "title": "Title"`
    pattern_exists = r'\{\s*["\']title["\']:\s*["\']' + escaped_title + r'["\']'
    if re.search(pattern_exists, content, re.IGNORECASE):
        # Difficult to safely replace just this object via Regex without failing on nested braces.
        # But wait! We can match from `{"title": "EscapedTitle"` up to the NEXT `{"title":` OR the end of the `latest` array `]\n}`.
        # Actually, let's use a simple trick: Split the `latest` array into individual manga elements.
        
        # We will simply append it if we can't safely replace, but avoiding duplicates is crucial.
        # How about extracting all text before the match, then counting brackets to find the end of the object?
        
        match = re.search(pattern_exists, content, re.IGNORECASE)
        start_idx = match.start()
        
        # We need to backtrack to the opening brace `{`
        while start_idx > 0 and content[start_idx] != '{':
            start_idx -= 1
            
        brace_count = 0
        end_idx = start_idx
        in_string = False
        escape_char = False
        
        for i in range(start_idx, len(content)):
            char = content[i]
            if escape_char:
                escape_char = False
                continue
            if char == '\\':
                escape_char = True
                continue
            if char == '"' or char == "'":
                in_string = not in_string
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
                        
        if brace_count == 0:
            # We found the perfect start and end inside the JS file!
            new_content = content[:start_idx] + manga_json.strip() + content[end_idx:]
            save_data(new_content)
            return True
        else:
            print("Could not balance brackets for existing manga.")
            return False

    else:
        # Manga doesn't exist, we must add it.
        # Find `latest: [`
        insert_marker = r'latest:\s*\['
        match = re.search(insert_marker, content)
        if match:
            pos = match.end()
            # We insert it right after `latest: [`
            
            # check if there's an existing object right after it, if so we need a comma
            rest = content[pos:].lstrip()
            
            comma = ",\n" if rest.startswith("{") else "\n"
            
            insertion = "\n" + manga_json.strip() + comma
            new_content = content[:pos] + insertion + content[pos:]
            save_data(new_content)
            return True
        else:
            print("Could not find 'latest: [' array in data.js")
            return False
