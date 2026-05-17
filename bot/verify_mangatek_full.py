import os
import sys

# Windows CMD Unicode Fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure the 'bot' directory is in the path
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from scraper import MangaScraper

def verify_mangatek():
    scraper = MangaScraper()
    url = "https://mangatek.com/manga/white-dragon-duke-pendragon"
    
    print(f"--- Testing Mangatek Fix ---")
    print(f"Scraping: {url}")
    
    result = scraper.get_manga_details(url)
    
    print(f"\nResults:")
    print(f"Title: {result['title']}")
    print(f"Chapters Found: {len(result['chapters'])}")
    
    if len(result['chapters']) > 0:
        print(f"First Chapter: {result['chapters'][0]['number']}")
        print(f"Last Chapter: {result['chapters'][-1]['number']}")
        
        # Check for gaps
        nums = [float(ch['number']) for ch in result['chapters']]
        if len(nums) > 1:
            missing = []
            for i in range(1, int(max(nums))):
                if float(i) not in nums:
                    missing.append(i)
            
            if not missing:
                print("✅ Success: No gaps found! All chapters recovered.")
            else:
                print(f"⚠️ Warning: Found gaps. Missing chapters: {missing[:10]}...")
    
    if len(result['chapters']) >= 131:
        print("\n🎉 Verification Passed: All 131 chapters captured!")
    else:
        print(f"\n❌ Verification Failed: Only {len(result['chapters'])} chapters found.")

if __name__ == "__main__":
    verify_mangatek()
