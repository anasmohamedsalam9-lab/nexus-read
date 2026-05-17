"""
data_manager.py - Handles reading/writing the data.js file (var DB = [...])
No local file storage. All image URLs are external references.
"""
import json
import re
import os

DATA_JS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data.js')


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def load_db():
    """Parse data.js and return the DB array."""
    if not os.path.exists(DATA_JS_PATH):
        return []

    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'var\s+DB\s*=\s*(\[.*\])\s*;', content, re.DOTALL)
    if not match:
        print("[DataManager] ERROR: Could not parse data.js")
        return []

    json_str = match.group(1)
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[DataManager] JSON parse error: {e}")
        return []


def save_db(db):
    """Write the DB array back to data.js."""
    json_str = json.dumps(db, ensure_ascii=False, indent=2)
    content = f"var DB = {json_str};"
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[DataManager] Saved {len(db)} entries to data.js")


def find_entry(db, title):
    """Find an entry by title (case-insensitive). Returns (index, entry) or (-1, None)."""
    for i, entry in enumerate(db):
        if entry.get('title', '').strip().lower() == title.strip().lower():
            return i, entry
    return -1, None


def get_max_chapter(entry):
    """Get the highest chapter number from an entry."""
    max_ch = 0
    for ch in entry.get('chapters', []):
        try:
            n = float(ch.get('n', '0'))
            if n > max_ch:
                max_ch = n
        except (ValueError, TypeError):
            pass
    return max_ch


def upsert_manga(title, cover='', desc='', genres=None, status='Ongoing', chapters=None):
    """
    Add or update a manga entry in data.js.
    - If exists: merges new chapters into existing ones.
    - If new: creates a fresh entry.
    Returns True on success.
    """
    db = load_db()
    idx, existing = find_entry(db, title)

    if chapters is None:
        chapters = []
    if genres is None:
        genres = []

    if existing:
        # Merge chapters: keep existing + add new (by chapter number)
        existing_ch_nums = {str(ch.get('n', '')): ch for ch in existing.get('chapters', [])}
        new_count = 0
        for ch in chapters:
            ch_num = str(ch.get('n', ''))
            if ch_num not in existing_ch_nums:
                existing_ch_nums[ch_num] = ch
                new_count += 1

        # Sort chapters descending
        merged = list(existing_ch_nums.values())
        merged.sort(key=lambda c: float(c.get('n', 0)), reverse=True)
        existing['chapters'] = merged

        # Update cover if better one provided
        if cover and not existing.get('cover'):
            existing['cover'] = cover
        # Update description if was placeholder
        if desc and existing.get('desc', '').startswith('قصة مشوقة'):
            existing['desc'] = desc
        if genres and not existing.get('genres'):
            existing['genres'] = genres

        db[idx] = existing
        print(f"[DataManager] Updated '{title}': +{new_count} new chapters (total: {len(merged)})")
    else:
        # Create new entry
        slug = slugify(title)
        new_entry = {
            "id": f"nm_{slug}",
            "title": title,
            "cover": cover,
            "desc": desc or "قصة مشوقة ومثيرة! استكشف الأحداث الآن.",
            "status": status,
            "author": "Nile Bot",
            "genres": genres,
            "chapters": sorted(chapters, key=lambda c: float(c.get('n', 0)), reverse=True)
        }
        db.insert(0, new_entry)  # Add to top
        print(f"[DataManager] Added new manga '{title}' with {len(chapters)} chapters")

    save_db(db)
    return True
