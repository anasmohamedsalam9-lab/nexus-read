"""
auto_updater.py - Nexus Background Auto-Updater
=====================================================
يعمل في الخلفية ويقوم بـ:
  1. فحص المانهوات المتابعة كل 30 دقيقة وسحب الفصول الجديدة
  2. استكشاف أعمال شائعة جديدة كل 6 ساعات
"""
import asyncio
import time

bot_dir = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
if bot_dir not in __import__('sys').path:
    __import__('sys').path.append(bot_dir)

from tracker import MangaTracker
import main as bot_main


class AutoUpdater:
    def __init__(self, check_interval_minutes=30, popular_interval_hours=6):
        self.check_interval = check_interval_minutes * 60
        self.popular_interval = popular_interval_hours * 3600
        self.tracker = MangaTracker()
        self.is_running = False

    async def _update_tracked(self):
        """فحص المانهوات المتابعة وسحب الجديد فقط."""
        while self.is_running:
            bot_main.add_log("🔄 دورة تحديث المتابعات...", "info")

            tracked = self.tracker.get_all_tracked()
            if not tracked:
                bot_main.add_log("📝 لا توجد مانهوات متتبعة", "warning")
            else:
                for key, data in tracked.items():
                    if not self.is_running:
                        break
                    url = data.get('url')
                    title = data.get('title', key)
                    if url:
                        bot_main.add_log(f"🔎 فحص {title}...", "info")
                        try:
                            await bot_main.scrape_manga(url, start_ch='auto')
                        except Exception as e:
                            bot_main.add_log(f"⚠️ خطأ في {title}: {e}", "error")
                        await asyncio.sleep(3)

            bot_main.add_log(f"💤 الدورة القادمة بعد {self.check_interval // 60} دقيقة", "success")

            # Sleep in small increments to allow stopping
            for _ in range(self.check_interval // 5):
                if not self.is_running:
                    break
                await asyncio.sleep(5)

    async def _discover_popular(self):
        """استكشاف أعمال جديدة شائعة من كل المصادر."""
        while self.is_running:
            bot_main.add_log("🌍 دورة استكشاف الأعمال الشائعة...", "info")
            try:
                await bot_main.scrape_popular(5)
            except Exception as e:
                bot_main.add_log(f"⚠️ خطأ في الاستكشاف: {e}", "error")

            bot_main.add_log(f"💤 الاستكشاف القادم بعد {self.popular_interval // 3600} ساعات", "success")

            for _ in range(self.popular_interval // 5):
                if not self.is_running:
                    break
                await asyncio.sleep(5)

    async def start(self):
        """تشغيل الحلقتين بشكل متزامن."""
        bot_main.add_log("🚀 بدأ نظام التحديث التلقائي!", "success")
        self.is_running = True

        task1 = asyncio.create_task(self._update_tracked())
        task2 = asyncio.create_task(self._discover_popular())
        await asyncio.gather(task1, task2)

    def stop(self):
        bot_main.add_log("🛑 جاري إيقاف التحديث التلقائي...", "warning")
        self.is_running = False


if __name__ == '__main__':
    updater = AutoUpdater(check_interval_minutes=1, popular_interval_hours=1)
    asyncio.run(updater.start())



