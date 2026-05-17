"""
server.py - Nexus Bot Server
===================================
Flask server + Admin Dashboard API.
Auto-starts the background updater on launch.

المصادر: عربية + أجنبية (MangaDex EN) مع ترجمة تلقائية

Usage: python bot/server.py
Then open: http://localhost:5000
"""
import threading
import asyncio
import os
import sys

bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import main as bot_main
from auto_updater import AutoUpdater

PROJECT_ROOT = os.path.dirname(bot_dir)

app = Flask(__name__, static_folder=PROJECT_ROOT, static_url_path='')
CORS(app)

# ── Task Status ──────────────────────────────────
task_status = {"running": False, "done": False}

# ── Auto Updater ─────────────────────────────────
global_updater = AutoUpdater(check_interval_minutes=30, popular_interval_hours=6)
updater_thread = None


def run_updater_bg():
    asyncio.run(global_updater.start())


def auto_start_updater():
    """تشغيل التحديث التلقائي عند بدء السيرفر."""
    global updater_thread
    if not global_updater.is_running:
        updater_thread = threading.Thread(target=run_updater_bg, daemon=True)
        updater_thread.start()
        bot_main.add_log("🤖 تم تشغيل التحديث التلقائي عند بدء السيرفر", "success")


# ── API Routes ───────────────────────────────────

@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    data = request.json
    url = data.get('url')
    start_ch = data.get('start', 1)
    end_ch = data.get('end') or None

    if not url:
        return jsonify({"error": "لم يتم تقديم رابط"}), 400
    if task_status["running"]:
        return jsonify({"error": "مهمة أخرى قيد التشغيل"}), 409

    def run():
        bot_main.cancel_flag = False
        try:
            task_status["running"] = True
            task_status["done"] = False
            bot_main.add_log(f"--- بدء مهمة: {url} ---", 'info')
            asyncio.run(bot_main.scrape_manga(url, start_ch, end_ch))
            bot_main.add_log("✅ اكتملت المهمة!", 'success')
        except Exception as e:
            bot_main.add_log(f"❌ خطأ: {e}", 'error')
        finally:
            task_status["running"] = False
            task_status["done"] = True

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "Started", "msg": "تم بدء السحب ✅"})


@app.route('/api/scrape-popular', methods=['POST'])
def start_scrape_popular():
    data = request.json or {}
    count = data.get('count', 5)

    if task_status["running"]:
        return jsonify({"error": "مهمة أخرى قيد التشغيل"}), 409

    def run():
        bot_main.cancel_flag = False
        try:
            task_status["running"] = True
            task_status["done"] = False
            bot_main.add_log(f"--- سحب جماعي: أشهر {count} من كل موقع ---", 'info')
            asyncio.run(bot_main.scrape_popular(count))
        except Exception as e:
            bot_main.add_log(f"❌ خطأ: {e}", 'error')
        finally:
            task_status["running"] = False
            task_status["done"] = True

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "Started", "msg": "تم بدء السحب الجماعي ✅"})


@app.route('/api/scrape-en', methods=['POST'])
def start_scrape_en():
    """Scrape from English source (MangaDex etc.) with optional translation."""
    data = request.json
    url = data.get('url')
    start_ch = data.get('start', 1)
    end_ch = data.get('end') or None
    translate = data.get('translate', True)  # Default: translate enabled

    if not url:
        return jsonify({"error": "لم يتم تقديم رابط"}), 400
    if task_status["running"]:
        return jsonify({"error": "مهمة أخرى قيد التشغيل"}), 409

    def run():
        bot_main.cancel_flag = False
        try:
            task_status["running"] = True
            task_status["done"] = False
            bot_main.add_log(f"--- بدء مهمة أجنبية: {url} (ترجمة: {'نعم' if translate else 'لا'}) ---", 'info')
            asyncio.run(bot_main.scrape_manga(url, start_ch, end_ch, translate=translate))
            bot_main.add_log("✅ اكتملت المهمة!", 'success')
        except Exception as e:
            bot_main.add_log(f"❌ خطأ: {e}", 'error')
        finally:
            task_status["running"] = False
            task_status["done"] = True

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"status": "Started", "msg": f"تم بدء السحب {'+ الترجمة' if translate else ''} ✅"})


@app.route('/api/search', methods=['POST'])
def search_manga():
    """Search for manga across all sources (Arabic + English)."""
    data = request.json or {}
    query = data.get('query', '')
    include_english = data.get('include_english', True)

    if not query:
        return jsonify({"error": "أدخل اسم المانهوا"}), 400

    from scraper import MangaScraper
    scraper = MangaScraper()
    results = scraper.search_manga(query, include_english=include_english)
    return jsonify({"results": results, "count": len(results)})


@app.route('/api/translator-status', methods=['GET'])
def translator_status():
    """Check if translator is available."""
    return jsonify({
        "available": bot_main.TRANSLATOR_AVAILABLE,
        "engine": "Google Translate (Free)" if bot_main.TRANSLATOR_AVAILABLE else "Not installed"
    })


@app.route('/api/stop-task', methods=['POST'])
def stop_task():
    if not task_status["running"]:
        return jsonify({"msg": "لا توجد مهمة قيد التشغيل"}), 400
    bot_main.cancel_flag = True
    bot_main.add_log("⛔ تم إرسال أمر الإيقاف", "warning")
    return jsonify({"status": "Stopping", "msg": "جاري الإيقاف..."})


@app.route('/api/toggle-updater', methods=['POST'])
def toggle_updater():
    global updater_thread
    if global_updater.is_running:
        global_updater.stop()
        return jsonify({"status": "Stopped", "msg": "تم إيقاف التحديث التلقائي"})
    else:
        updater_thread = threading.Thread(target=run_updater_bg, daemon=True)
        updater_thread.start()
        return jsonify({"status": "Started", "msg": "تم تشغيل التحديث التلقائي"})


@app.route('/api/updater-status', methods=['GET'])
def get_updater_status():
    return jsonify({"running": global_updater.is_running})


@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(bot_main.get_logs())


@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(task_status)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """إحصائيات سريعة من data.js."""
    from data_manager import load_db
    db = load_db()
    total_manga = len(db)
    total_chapters = sum(len(e.get('chapters', [])) for e in db)
    with_covers = sum(1 for e in db if e.get('cover'))
    return jsonify({
        "total_manga": total_manga,
        "total_chapters": total_chapters,
        "with_covers": with_covers
    })


# ── Static Files ─────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(PROJECT_ROOT, 'admin.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(PROJECT_ROOT, path)


# ── Main ─────────────────────────────────────────

if __name__ == '__main__':
    bot_main.add_log("=" * 50, "info")
    bot_main.add_log("🚀 Nexus Bot Server (Cloud-Only)", "success")
    bot_main.add_log(f"📂 المجلد: {PROJECT_ROOT}", "info")
    bot_main.add_log("🌐 لوحة التحكم: http://localhost:5000", "info")
    bot_main.add_log("=" * 50, "info")

    # Auto-start background updater
    auto_start_updater()

    app.run(port=5000, debug=False)



