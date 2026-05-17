import asyncio
import sys
import os

# التأكد من مسار البوت
bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

try:
    from tracker import MangaTracker
    import main as bot_main
except ImportError:
    print("MangaTracker or bot_main not found. Make sure bot files are available.")
    sys.exit(1)

async def run_once():
    print("🚀 بدء التحديث لمرة واحدة عبر GitHub Actions...")
    
    # 1. تحديث الأعمال المتابعة
    tracker = MangaTracker()
    tracked = tracker.get_all_tracked()
    
    if tracked:
        for key, data in tracked.items():
            url = data.get('url')
            if url:
                print(f"🔍 فحص {data.get('title', key)}...")
                try:
                    await bot_main.scrape_manga(url, start_ch='auto')
                except Exception as e:
                    print(f"خطأ في جلب {key}: {e}")
                await asyncio.sleep(2) # راحة لتجنب الحظر
    
    # 2. استكشاف أعمال جديدة شائعة (نكتفي بعملين فقط في كل دورة لتسريع الوقت)
    print("🌍 جلب أعمال شائعة جديدة...")
    try:
        await bot_main.scrape_popular(2)
    except Exception as e:
        print(f"خطأ في جلب الشائع: {e}")
        
    print("✅ اكتمل التحديث وتم تجهيز الفصول.")

if __name__ == '__main__':
    asyncio.run(run_once())
