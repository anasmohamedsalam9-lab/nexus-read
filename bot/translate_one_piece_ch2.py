import asyncio
import sys
import os

# Set PYTHONPATH
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from main import scrape_manga

async def run():
    url = "https://mangadex.org/title/a1c7c817-e785-4efb-9958-aab6123a5b4f"
    print("==================================================")
    print("   Nexus - Translate One Piece Chapter 2          ")
    print("==================================================")
    print("🚀 Connecting to MangaDex...")
    
    # Scrape chapter 2 specifically! (start_ch=2, end_ch=2, translate=True)
    try:
        await scrape_manga(url, start_ch=2, end_ch=2, translate=True)
        print("\n🎉 Success! Chapter 2 of One Piece has been successfully translated and added to data.js!")
    except Exception as e:
        print(f"\n❌ Error during translation: {e}")

if __name__ == '__main__':
    asyncio.run(run())
