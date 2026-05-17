"""
sync_covers.py - Syncs covers.json into data.js
- Updates cover URLs for existing manhwas
- Adds missing manhwas from covers.json as new entries
"""
import json
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COVERS_PATH = os.path.join(SCRIPT_DIR, 'covers.json')
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')

# Manual title mappings: covers.json title -> canonical title to use in data.js
# Some covers.json entries are duplicates or shorthand aliases
DUPLICATE_ALIASES = {
    "Omniscient Reader": "Omniscient Reader's Viewpoint",
    "A Wimp": "A Wimp's Strategy Guide to Conquer the Tower",
    "The Regressed Mercenary": "The Regressed Mercenary's Machinations",
    "Mount Hua Sect": "Return of the Mount Hua Sect",
    "Reverend Insanity Remake": "Reverend Insanity",
    "Reverend Insanity (Master of Gu)": "Reverend Insanity",
    "Pick Me Up _ Infinite Gacha": "Pick Me Up Infinite Gacha",
    "The Back-Alley Mage": "The Back-Alley Mage's Return",
    "The Extra": "The Extra's Academy Survival Guide",
    "A Regressor": "A Regressor's Tale of Cultivation",
}


def slugify(text):
    """Generate a URL-friendly slug from a title."""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug


def load_covers():
    """Load the covers.json mapping."""
    with open(COVERS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_data_js():
    """Parse the data.js file and return the raw content and parsed DB array."""
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the JSON array from "var DB = [...];"
    match = re.search(r'var\s+DB\s*=\s*(\[.*\])\s*;', content, re.DOTALL)
    if not match:
        print("[ERROR] Could not parse data.js - 'var DB = [...]' not found!")
        return content, None

    json_str = match.group(1)

    # Fix potential issues: trailing commas before ] or }
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

    try:
        db = json.loads(json_str)
        return content, db
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error in data.js: {e}")
        return content, None


def save_data_js(db):
    """Write the updated DB array back to data.js."""
    # Serialize with nice formatting
    json_str = json.dumps(db, ensure_ascii=False, indent=2)
    content = f"var DB = {json_str};"

    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)


def sync():
    """Main sync logic."""
    covers = load_covers()
    _, db = load_data_js()

    if db is None:
        print("[FATAL] Cannot proceed without a valid data.js")
        return

    # Build a lookup of existing titles (case-insensitive)
    existing_titles = {}
    for i, entry in enumerate(db):
        title = entry.get('title', '').strip()
        existing_titles[title.lower()] = i

    # Deduplicate covers.json: resolve aliases to canonical names
    # and pick the best (non-placeholder) cover URL
    canonical_covers = {}
    for raw_title, cover_url in covers.items():
        canonical = DUPLICATE_ALIASES.get(raw_title, raw_title)

        # Skip if we already have a better (anilist) cover for this canonical name
        if canonical in canonical_covers:
            existing_url = canonical_covers[canonical]
            # Keep whichever is from anilist; skip dupes with worse quality
            if 'anilist' in existing_url and 'large' in existing_url:
                continue  # Already have a high-quality cover
            if 'imgur.com' in cover_url and 'anilist' in existing_url:
                continue  # Keep the anilist one
        canonical_covers[canonical] = cover_url

    updated_count = 0
    added_count = 0

    for title, cover_url in canonical_covers.items():
        title_lower = title.lower()

        if title_lower in existing_titles:
            # Update existing entry's cover
            idx = existing_titles[title_lower]
            old_cover = db[idx].get('cover', '')
            if old_cover != cover_url:
                db[idx]['cover'] = cover_url
                updated_count += 1
                print(f"[UPDATE] {title} -> cover updated")
            else:
                print(f"[SKIP]   {title} -> cover already set")
        else:
            # Add new entry
            slug = slugify(title)
            new_entry = {
                "id": f"nm_{slug}",
                "title": title,
                "cover": cover_url,
                "desc": "قصة مشوقة ومثيرة! استكشف الأحداث الآن.",
                "status": "Ongoing",
                "author": "Nile Bot",
                "genres": [],
                "chapters": []
            }
            db.append(new_entry)
            existing_titles[title_lower] = len(db) - 1
            added_count += 1
            print(f"[ADD]    {title} -> added with cover")

    # Save back
    save_data_js(db)

    print(f"\n{'='*50}")
    print(f"  DONE!")
    print(f"  Updated covers: {updated_count}")
    print(f"  New manhwas added: {added_count}")
    print(f"  Total entries in data.js: {len(db)}")
    print(f"{'='*50}")


if __name__ == '__main__':
    sync()
