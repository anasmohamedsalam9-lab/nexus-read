import requests
import time
import json

titles = [
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
    "Pick Me Up Infinite Gacha", 
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

query = '''
query ($search: String) {
  Media (search: $search, type: MANGA) {
    coverImage {
      extraLarge
    }
  }
}
'''
results = {}

print("Fetching covers from Anilist...")
for title in titles:
    # Small cleanup for better search results
    search_term = title.replace(" (Master of Gu)", "").replace("_", "").strip()
    try:
        response = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'search': search_term}})
        data = response.json()
        if 'data' in data and data['data'] and data['data']['Media']:
            url = data['data']['Media']['coverImage']['extraLarge']
            results[title] = url
        else:
            results[title] = "https://i.imgur.com/rL71C5k.jpeg"
        time.sleep(0.7) # Respecting Anilist Rate Limits
    except Exception as e:
        results[title] = "https://i.imgur.com/rL71C5k.jpeg"

with open('covers.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("SUCCESS")
