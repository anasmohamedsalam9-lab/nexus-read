"""
main.py - Nexus Scraper Bot (Cloud-Only Mode + Translation)
====================================================
يقوم بسحب فصول المانهوا من مواقع عربية وأجنبية.
إذا كان المصدر إنجليزياً، يقوم بترجمة الصور إلى العربية تلقائياً.

المصادر المدعومة:
  - عربية: Mangatek, Olympus Staff, Lek Manga, Mesh Manga (Madara)
  - أجنبية: MangaDex (EN) + أي موقع Madara إنجليزي

الاستخدام:
  python main.py <URL>                    # سحب مانهوا (كشف اللغة تلقائي)
  python main.py <URL> --translate        # سحب + ترجمة تلقائية للعربية
  python main.py <URL> --no-translate     # سحب بدون ترجمة (إنجليزي كما هو)
  python main.py <URL> 10                 # من فصل 10 فصاعداً
  python main.py <URL> 10 20             # من فصل 10 إلى 20
  python main.py <URL> auto              # سحب الفصول الجديدة فقط
  python main.py --popular 5             # سحب أشهر 5 من كل موقع
  python main.py --search "Solo Leveling" # بحث في جميع المصادر
"""
import asyncio
import os
import sys
import re
import time
import requests
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

bot_dir = os.path.dirname(os.path.abspath(__file__))
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from scraper import MangaScraper
from data_manager import load_db, find_entry, get_max_chapter, upsert_manga, slugify
from tracker import MangaTracker

# Try to import translator (optional — only needed for EN sources)
try:
    from translator import MangaTranslator
    _translator = MangaTranslator()
    TRANSLATOR_AVAILABLE = _translator.is_available()
except ImportError:
    _translator = None
    TRANSLATOR_AVAILABLE = False

load_dotenv()

# Project root for local storage
PROJECT_ROOT = os.path.dirname(bot_dir)

# ── Blacklist ──────────────────────────────────────────────
GENRE_BLACKLIST = [
    "Romance", "رومنسية", "Ecchi", "إيتشي", "Harem", "حريم",
    "Smut", "Adult", "Mature", "18+", "Yaoi", "Yuri", "Hentai",
    "NSFW", "Explicit", "BDSM", "Doujinshi"
]

# ── Global State ──────────────────────────────────────────
cancel_flag = False
logs_queue = []


def add_log(msg, type='info'):
    try:
        print(f"[{type}] {msg}")
    except UnicodeEncodeError:
        print(f"[{type}] " + msg.encode('ascii', 'replace').decode('ascii'))
    logs_queue.append({
        "time": time.strftime("%H:%M:%S"),
        "msg": msg,
        "type": type
    })


def get_logs():
    res = list(logs_queue)
    logs_queue.clear()
    return res


def is_nsfw(genres):
    """Check if a series has blacklisted genres."""
    genre_lower = [g.lower() for g in genres]
    return any(bl.lower() in genre_lower for bl in GENRE_BLACKLIST)


# ── Core Scraping Logic ───────────────────────────────────

async def scrape_manga(url, start_ch=1, end_ch=None, translate=None):
    """
    Main scraping function. Scrapes a manhwa from URL:
    1. Gets manga details (title, cover, genres, chapters list)
    2. For each chapter, extracts image URLs from the reader page
    3. If English source + translate=True: downloads images, translates, saves locally
    4. If Arabic source: stores external URLs directly in data.js

    Args:
        url: Manga page URL
        start_ch: Starting chapter number or 'auto'
        end_ch: Ending chapter number (optional)
        translate: True=force translate, False=force no translate, None=auto detect
    """
    global cancel_flag
    cancel_flag = False

    scraper = MangaScraper()
    tracker = MangaTracker()

    add_log(f"🔗 جاري جلب بيانات المانهوا من: {url}", 'info')

    try:
        manga_data = scraper.get_manga_details(url)
    except Exception as e:
        add_log(f"❌ فشل جلب البيانات: {e}", 'error')
        return

    title = manga_data.get('title', 'Unknown')
    all_chapters = manga_data.get('chapters', [])
    cover = manga_data.get('cover', '')
    desc = manga_data.get('description', '')
    genres = manga_data.get('genres', [])
    source_lang = manga_data.get('lang', scraper.detect_source_language(url))

    if not all_chapters:
        add_log(f"⚠️ لم يتم العثور على فصول لـ '{title}'", 'warning')
        # Still save the manga entry with cover
        if cover:
            cover = await _download_cover(scraper, title, cover)
            upsert_manga(title, cover=cover, desc=desc, genres=genres)
        return

    # NSFW Filter
    if is_nsfw(genres):
        add_log(f"🚫 تم تخطي '{title}' - محتوى محظور", 'warning')
        return

    # Determine if we should translate
    should_translate = translate
    if should_translate is None:
        # Auto detect: translate if source is English
        should_translate = (source_lang == 'en')

    lang_label = "🇬🇧 EN" if source_lang == 'en' else "🇸🇦 AR"
    add_log(f"✅ {title} [{lang_label}] — {len(all_chapters)} فصل | غلاف: {'✓' if cover else '✗'}", 'success')

    if should_translate and not TRANSLATOR_AVAILABLE:
        add_log(f"⚠️ المترجم غير متاح. سيتم حفظ الصور بدون ترجمة. ثبّت: pip install easyocr deep-translator", 'warning')
        should_translate = False

    if should_translate:
        add_log(f"🌐 وضع الترجمة مفعّل: EN → AR (Google Translate)", 'info')

    # Track this manga for auto-updates
    tracker.add_tracking(title, url)

    # ── Download original cover ─────────────
    local_cover = cover
    if cover:
        local_cover = await _download_cover(scraper, title, cover)

    # ── Determine chapter range ─────────────
    actual_start = start_ch
    if str(start_ch).lower() == 'auto':
        db = load_db()
        idx, existing = find_entry(db, title)
        if existing:
            max_ch = get_max_chapter(existing)
            actual_start = max_ch + 1
            add_log(f"📌 وضع التحديث: البدء من الفصل {actual_start}", 'info')
        else:
            actual_start = 1
            add_log(f"🆕 مانهوا جديدة — سيتم سحب كل الفصول", 'info')

    # Filter chapters by range
    chapters_to_scrape = []
    for ch in all_chapters:
        try:
            n_match = re.search(r'(\d+\.?\d*)', str(ch.get('number', '0')))
            n = float(n_match.group(1)) if n_match else 0
            if n >= float(actual_start):
                if end_ch and n > float(end_ch):
                    continue
                chapters_to_scrape.append(ch)
        except (ValueError, AttributeError):
            chapters_to_scrape.append(ch)

    if not chapters_to_scrape:
        add_log(f"✅ لا توجد فصول جديدة لسحبها", 'success')
        upsert_manga(title, cover=local_cover, desc=desc, genres=genres)
        return

    add_log(f"📥 سيتم سحب {len(chapters_to_scrape)} فصل...", 'info')

    # ── Scrape each chapter's images ────────
    scraped_chapters = []
    slug = slugify(title)

    for i, ch in enumerate(chapters_to_scrape):
        if cancel_flag:
            add_log("⛔ تم إيقاف السحب بأمر المستخدم", 'warning')
            break

        ch_num = ch.get('number', '0')
        ch_url = ch.get('url', '')

        add_log(f"  📄 الفصل {ch_num} ({i+1}/{len(chapters_to_scrape)})...", 'info')

        try:
            image_urls = scraper.get_chapter_images(ch_url)
        except Exception as e:
            add_log(f"  ❌ فشل سحب صور الفصل {ch_num}: {e}", 'error')
            continue

        if not image_urls:
            add_log(f"  ⚠️ لم يتم العثور على صور بالفصل {ch_num}", 'warning')
            continue

        # Decide: translate + save locally OR store external URLs
        if source_lang == 'en':
            # English source → download locally (with or without translation)
            chapter_dir = os.path.join(PROJECT_ROOT, 'assets', 'chapters', slug, f'ch-{ch_num}')

            if should_translate:
                add_log(f"  🔄 جاري ترجمة {len(image_urls)} صفحة...", 'info')
                saved_paths = _translator.translate_chapter(
                    image_urls, chapter_dir, chapter_num=ch_num,
                    log_func=lambda msg: add_log(msg, 'info')
                )
            else:
                add_log(f"  💾 جاري تحميل {len(image_urls)} صفحة...", 'info')
                saved_paths = _translator.download_and_save_original(
                    image_urls, chapter_dir,
                    log_func=lambda msg: add_log(msg, 'info')
                ) if _translator else []

                # Fallback download without translator module
                if not saved_paths and not _translator:
                    import requests as req_lib
                    from PIL import Image as PILImage
                    from io import BytesIO as BIO
                    os.makedirs(chapter_dir, exist_ok=True)
                    for idx, img_url in enumerate(image_urls):
                        try:
                            r = req_lib.get(img_url, timeout=20,
                                           headers={'User-Agent': 'Mozilla/5.0'})
                            if r.status_code == 200:
                                out_path = os.path.join(chapter_dir, f"{idx+1}.webp")
                                try:
                                    im = PILImage.open(BIO(r.content)).convert('RGB')
                                    im.save(out_path, 'WEBP', quality=85)
                                except:
                                    with open(out_path, 'wb') as f:
                                        f.write(r.content)
                                saved_paths.append(out_path)
                        except:
                            pass
                        await asyncio.sleep(0.3)

            # Convert to relative paths for data.js
            page_urls = []
            for p in saved_paths:
                rel = os.path.relpath(p, PROJECT_ROOT).replace('\\', '/')
                page_urls.append(rel)

            if page_urls:
                scraped_chapters.append({
                    "n": str(ch_num),
                    "d": datetime.now().strftime("%Y-%m-%d"),
                    "pages": page_urls
                })
                add_log(f"  ✅ الفصل {ch_num}: {len(page_urls)} صفحة {'(مترجم)' if should_translate else '(إنجليزي)'}", 'success')

        else:
            # Arabic source → store external URLs directly (no download)
            scraped_chapters.append({
                "n": str(ch_num),
                "d": datetime.now().strftime("%Y-%m-%d"),
                "pages": image_urls
            })
            add_log(f"  ✅ الفصل {ch_num}: {len(image_urls)} صفحة", 'success')

        # Small delay to avoid hammering the source
        await asyncio.sleep(1.5)

    # ── Save to data.js ─────────────────────
    if scraped_chapters or local_cover:
        upsert_manga(
            title=title,
            cover=local_cover,
            desc=desc,
            genres=genres,
            chapters=scraped_chapters
        )
        add_log(f"🎉 اكتمل سحب '{title}': {len(scraped_chapters)} فصل جديد", 'success')
    else:
        add_log(f"⚠️ لم يتم سحب أي فصل من '{title}'", 'warning')


async def _download_cover(scraper, title, cover_url):
    """Download and save cover image locally, return relative path."""
    try:
        slug = slugify(title)
        cover_dir = os.path.join(PROJECT_ROOT, 'assets', 'covers')
        os.makedirs(cover_dir, exist_ok=True)
        cover_path = os.path.join(cover_dir, f"{slug}.webp")

        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 1000:
            return f"assets/covers/{slug}.webp"

        # Try MangaKatana first for premium covers
        mk_cover = scraper.get_mangakatana_cover(title)
        if mk_cover:
            add_log(f"  🔍 تم العثور على غلاف عالي الجودة في MangaKatana", 'info')
            cover_url = mk_cover

        if not cover_url: return ""

        # Use the scraper's session
        resp = scraper.scraper.get(cover_url, timeout=20, headers={
            'User-Agent': scraper.headers['User-Agent']
        })
        if resp.status_code == 200:
            try:
                from PIL import Image as PILImage
                from io import BytesIO as BIO
                img = PILImage.open(BIO(resp.content)).convert('RGB')
                img.save(cover_path, 'WEBP', quality=90)
            except Exception as e:
                with open(cover_path, 'wb') as f:
                    f.write(resp.content)

            relative = f"assets/covers/{slug}.webp"
            add_log(f"  🖼️ تم حفظ الغلاف: {relative}", 'success')
            return relative
        else:
            add_log(f"  ⚠️ فشل سحب الغلاف من {cover_url} (كود {resp.status_code})", 'warning')
            return ""
    except Exception as e:
        add_log(f"  ⚠️ خطأ في معالجة الغلاف لـ '{title}': {e}", 'warning')
        return ""

    return cover_url  # Return original URL as fallback


async def scrape_popular(count_per_site=5):
    """Discover and scrape popular manhwas from all supported sources."""
    global cancel_flag
    cancel_flag = False

    scraper = MangaScraper()

    add_log(f"🌍 جاري استكشاف الأعمال الشائعة ({count_per_site} من كل موقع)...", 'info')

    all_series = scraper.get_popular_from_all_sources(count_per_site)
    add_log(f"✅ تم اكتشاف {len(all_series)} عمل", 'success')

    processed = set()

    for i, meta in enumerate(all_series):
        if cancel_flag:
            add_log("⛔ تم إيقاف السحب الجماعي", 'warning')
            break

        title = meta.get('title', '')
        url = meta.get('url', '')

        if title.lower() in processed:
            continue

        add_log(f"🔄 [{i+1}/{len(all_series)}] {title}...", 'info')

        try:
            await scrape_manga(url, start_ch='auto')
            processed.add(title.lower())
            await asyncio.sleep(3)
        except Exception as e:
            add_log(f"❌ فشل سحب {title}: {e}", 'error')

    add_log(f"🏁 انتهى السحب الجماعي — تمت معالجة {len(processed)} عمل", 'success')


# ── CLI Entry Point ────────────────────────────────────────
if __name__ == '__main__':
    import requests
    if len(sys.argv) > 1:
        if sys.argv[1] == '--popular':
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            asyncio.run(scrape_popular(count))
        elif sys.argv[1] == '--search':
            query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'Solo Leveling'
            scraper = MangaScraper()
            results = scraper.search_manga(query, include_english=True)
            print(f"\n{'='*60}")
            print(f"نتائج البحث عن: {query} ({len(results)} نتيجة)")
            print(f"{'='*60}")
            for i, r in enumerate(results):
                lang_icon = '🇬🇧' if r.get('lang') == 'en' else '🇸🇦'
                print(f"  {i+1}. {lang_icon} {r['title']} [{r['source']}]")
                print(f"     {r['url']}")
        else:
            url = sys.argv[1]
            # Parse flags
            translate = None
            start = 1
            end = None
            args = sys.argv[2:]

            for arg in args:
                if arg == '--translate':
                    translate = True
                elif arg == '--no-translate':
                    translate = False
                elif arg == 'auto':
                    start = 'auto'
                elif arg.replace('.', '').isdigit():
                    if start == 1:
                        start = arg
                    else:
                        end = arg

            asyncio.run(scrape_manga(url, start, end, translate=translate))
    else:
        print("Nexus Scraper Bot (Cloud + Translation)")
        print("=" * 50)
        print(f"المترجم: {'✅ متاح' if TRANSLATOR_AVAILABLE else '❌ غير متاح (pip install easyocr deep-translator)'}")
        print()
        print("Usage:")
        print("  python main.py <URL>                  # سحب (كشف اللغة تلقائي)")
        print("  python main.py <URL> --translate       # سحب + ترجمة EN→AR")
        print("  python main.py <URL> --no-translate    # سحب بدون ترجمة")
        print("  python main.py <URL> auto              # الفصول الجديدة فقط")
        print("  python main.py <URL> 10 20             # فصول 10-20")
        print("  python main.py --popular 5             # أشهر الأعمال")
        print("  python main.py --search 'Solo Leveling' # بحث في جميع المصادر")



