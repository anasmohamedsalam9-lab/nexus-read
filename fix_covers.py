import requests
import re
import time

mangas = [
    "A Regressor's Tale of Cultivation",
    "A Wimp's Strategy Guide to Conquer the Tower",
    "Absolute Regression",
    "Children Of The Rune",
    "Crimson Reset",
    "Kill The Hero",
    "L.A.G",
    "Legend of the Northern Blade",
    "Martial God Regressed to Level 2",
    "Mount Hua Sect's Genius Phantom Swordsman",
    "My Simulated Path To Immortality",
    "Omniscient Reader's Viewpoint",
    "Ovcharka",
    "Pick Me Up _ Infinite Gacha",
    "Reincarnation of the Fist King",
    "Reincarnation of the Suicidal Battle God",
    "Return of the Mount Hua Sect",
    "Revenge of the Iron-Blooded Sword Hound",
    "Reverend Insanity",
    "Star-Embracing Swordmaster",
    "Sword-Devouring Swordmaster",
    "The 100th Regression of the Max-Level Player",
    "The Back-Alley Mage's Return",
    "The Boxer",
    "The Demon King Overrun by Heroes",
    "The Extra's Academy Survival Guide",
    "The Greatest Estate Developer",
    "The Killer Lawyer",
    "The Regressed Mercenary's Machinations",
    "The Villain Wants to Live"
]

with open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()

print("Fetching genuine covers from MangaDex...")

for title in mangas:
    # Clean up title for search
    search_term = title.replace("_", "").replace("(Master of Gu)", "").strip()
    
    try:
        url = f"https://api.mangadex.org/manga?title={search_term}&includes[]=cover_art&order[relevance]=desc"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if data.get('data') and len(data['data']) > 0:
            manga = data['data'][0]
            manga_id = manga['id']
            cover_art = next((rel for rel in manga['relationships'] if rel['type'] == 'cover_art'), None)
            
            if cover_art and 'attributes' in cover_art and cover_art['attributes']:
                cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{filename}"
                
                # Replace in script.js
                escaped_title = re.escape(title)
                pattern = r'(title:\s*["\']' + escaped_title + r'["\'][^}]*?img:\s*["\'])(.+?)(["\'])'
                content = re.sub(pattern, r'\g<1>' + cover_url + r'\g<3>', content)
                print(f"Fixed: {title}")
            else:
                print(f"No cover art found for: {title}")
        else:
            print(f"Not found on MangaDex: {title}")
            
    except Exception as e:
        print(f"Error for {title}: {e}")
        
    time.sleep(0.3)

with open('script.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("INJECTION COMPLETE")
