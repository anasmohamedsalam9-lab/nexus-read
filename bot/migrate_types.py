import os
import sys

# Add bot directory to path
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from data_manager import load_db, save_db

def migrate():
    db = load_db()
    if not db:
        print("[Migration] No DB loaded.")
        return

    manga_count = 0
    comics_count = 0
    manhwa_count = 0
    novels_count = 0

    manga_titles = [
        "one piece", "one piece (official colored)", "ichigo mashimaro", 
        "yuukoku no moriarty", "time of the blind beast", "one piece (translated demo)"
    ]
    comics_titles = [
        "martial peak", "apotheosis", "magic emperor", "demonic emperor", 
        "apocalypse sword god", "my simulated path to immortality", 
        "global horror: start with trillions of coins", "logging 10.000 years into the future",
        "catastrophic necromancer"
    ]

    for entry in db:
        title = entry.get('title', '').strip().lower()
        genres = [g.lower() for g in entry.get('genres', [])]

        # 1. Novels
        if 'novel' in title or 'رواية' in title or 'novel' in genres or 'رواية' in genres:
            entry['type'] = 'novels'
            novels_count += 1
        # 2. Manga
        elif any(mt in title for mt in manga_titles) or any(g in genres for g in ['manga', 'japanese', 'مانجا', 'يابانية']):
            entry['type'] = 'manga'
            manga_count += 1
        # 3. Comics / Manhua
        elif any(ct in title for ct in comics_titles) or any(g in genres for g in ['manhua', 'chinese', 'مانها', 'صينية', 'comics', 'كوميكس']):
            entry['type'] = 'comics'
            comics_count += 1
        # 4. Manhwa (Default)
        else:
            entry['type'] = 'manhwa'
            manhwa_count += 1

    save_db(db)
    print(f"\n[Migration] Completed successfully!")
    print(f"  - Manhwa (Korean): {manhwa_count}")
    print(f"  - Manga (Japanese): {manga_count}")
    print(f"  - Comics/Manhua (Chinese): {comics_count}")
    print(f"  - Novels (Translated): {novels_count}")

if __name__ == "__main__":
    migrate()
