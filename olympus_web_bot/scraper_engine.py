import os
import re
import time
import requests
import cloudscraper
import threading
import queue
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

from data_injector import add_or_update_manga_in_datajs

BASE_URL = "https://olympustaff.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Referer": BASE_URL
}

# Where the manhwa assets should go in the user site
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
COVERS_DIR = os.path.join(ASSETS_DIR, 'covers')
CHAPTERS_DIR = os.path.join(ASSETS_DIR, 'chapters')

os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(CHAPTERS_DIR, exist_ok=True)

class ScraperStatus:
    def __init__(self):
        self.is_running = False
        self.logs_queue = queue.Queue()
        self.progress_queue = queue.Queue()

status = ScraperStatus()

def log(msg, level='info'):
    status.logs_queue.put({"type": "log", "msg": msg, "level": level})
    try:
        print(f"[{level}] {msg}")
    except UnicodeEncodeError:
        print(f"[{level}] " + msg.encode('ascii', 'replace').decode('ascii'))

def update_progress(manga_title=None, chapter=None, manga_current=None, manga_total=None):
    status.progress_queue.put({
        "type": "progress",
        "manga_title": manga_title,
        "chapter": chapter,
        "manga_current": manga_current,
        "manga_total": manga_total
    })

def get_soup(scraper, url, retries=3):
    for attempt in range(retries):
        if not status.is_running:
            return None
        try:
            resp = scraper.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                resp.encoding = 'utf-8'
                return BeautifulSoup(resp.text, 'lxml')
            elif resp.status_code in (403, 503):
                log(f"حماية (403/503) في {url} - محاولة {attempt+1}", "warning")
                time.sleep(5)
        except Exception as e:
            log(f"خطأ في الاتصال {url}: {e}", "error")
        time.sleep(3)
    return None

def clean_slug(href):
    # Handle both relative and absolute URLs
    parts = href.rstrip('/').split('/')
    if 'series' in parts:
        idx = parts.index('series')
        if idx + 1 < len(parts):
            slug = parts[idx+1]
            if slug and slug != 'series':
                return slug
    return None

def fetch_all_manga_links(scraper):
    log("جاري جلب جميع مسارات المانهوا من صفحة series...")
    all_manhwa = {}
    page = 1
    
    while status.is_running:
        url = f"{BASE_URL}/series?page={page}"
        log(f"جاري فحص الصفحة: {page}...")
        soup = get_soup(scraper, url)
        if not soup:
            break
            
        # Find all series links - looking for the specific cards
        found_new_on_page = False
        
        # In this theme, series are usually in anchor tags with a specific slug pattern
        for a in soup.find_all('a', href=True):
            href = a['href']
            slug = clean_slug(href)
            if slug and slug not in all_manhwa:
                # Get data from the card/container
                # Try to find a title in child elements or text
                title_elem = a.find('h3') or a.find('h4') or a.find('span', class_='font-bold')
                title = title_elem.get_text(strip=True) if title_elem else a.get_text(strip=True)
                
                # Filter out navigation links or search buttons that might match slug
                if not title or title.endswith("...") or len(title) < 2:
                    continue
                
                img_elem = a.find('img')
                cover_url = ""
                if img_elem:
                    cover_url = img_elem.get('data-src') or img_elem.get('data-lazy') or img_elem.get('src') or ""
                
                if not cover_url: continue # Likely not a series card
                
                full_url = urljoin(BASE_URL, href)
                all_manhwa[slug] = {
                    "title": title,
                    "slug": slug,
                    "url": full_url,
                    "cover": cover_url
                }
                found_new_on_page = True
                
        if not found_new_on_page:
            # Check if we have pagination links to double check
            has_next = soup.find('a', href=re.compile(r'page=' + str(page + 1)))
            if not has_next:
                log("انتهت الصفحات، لم يتم العثور على مانهوا جديدة.", "info")
                break
            
        page += 1
        time.sleep(2)
        
    return list(all_manhwa.values())

def fetch_manga_details_and_chapters(scraper, manhwa):
    soup = get_soup(scraper, manhwa['url'])
    if not soup:
        return None
        
    chapters = []
    
    # Try to grab better title or ratings from details page if needed
    
    # Grab chapters
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(r'/series/[^/]+/(\d+(?:\.\d+)?)', href)
        if match:
            chapter_num_str = match.group(1)
            # Some titles might have text
            full_url = urljoin(BASE_URL, href)
            # avoid duplicates
            if not any(c['n'] == chapter_num_str for c in chapters):
                chapters.append({
                    "n": chapter_num_str,
                    "url": full_url
                })
                
    # Sort chapters descending
    try:
        chapters = sorted(chapters, key=lambda x: float(x['n']), reverse=True)
    except:
        pass
        
    manhwa['chapter_links'] = chapters
    return manhwa

def download_images(scraper, url, chapter_dir, slug, chapter_str):
    soup = get_soup(scraper, url)
    if not soup:
        return []

    images = []
    selectors = [
        '.reading-content img', '.chapter-content img', '#readerarea img',
        'div.read-content img', 'img[src*="wp-content/uploads"]', 'img[data-src]'
    ]

    for sel in selectors:
        for img in soup.select(sel):
            src = (img.get('data-src') or img.get('data-lazy') or img.get('src') or img.get('srcset'))
            if src:
                if ',' in str(src):
                    src = src.split(',')[0].strip().split()[0]
                if not src.startswith('http'):
                    src = urljoin(BASE_URL, src)
                if src not in images and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    images.append(src)

    images = list(dict.fromkeys(images))
    
    saved_paths = []
    if not images:
        log(f"⚠️  لم يتم العثور على صور في الفصل {chapter_str}", "warning")
        return []
        
    log(f"جاري تحميل {len(images)} صورة للفصل {chapter_str}...")
    os.makedirs(chapter_dir, exist_ok=True)
    
    for idx, img_url in enumerate(images):
        if not status.is_running:
            break
        try:
            resp = scraper.get(img_url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                ext = '.webp'
                filename = f"{idx+1}{ext}"
                filepath = os.path.join(chapter_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                    
                # Relative path for data.js
                rel_path = f"assets/chapters/{slug}/ch-{chapter_str}/{filename}"
                saved_paths.append(rel_path)
            time.sleep(0.3)
        except Exception as e:
            log(f"خطأ في تحميل صورة {idx+1}: {e}", "error")
            
    return saved_paths

def download_cover(scraper, cover_url, slug):
    if not cover_url: return ""
    try:
        resp = scraper.get(cover_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            ext = '.webp' # forcing webp for consistency or keep original
            filepath = os.path.join(COVERS_DIR, f"{slug}{ext}")
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            return f"assets/covers/{slug}{ext}"
    except:
        pass
    return ""

def scraper_worker():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    log("🚀 جاري الاتصال وعمل حصر بجميع المانهوا من الموقع...", "info")
    manga_list = fetch_all_manga_links(scraper)
    
    if not manga_list:
        log("❌ لم يتم العثور على مانهوا! قد يكون الموقع مغلق أو هناك حظر.", "error")
        status.is_running = False
        return
        
    total_manga = len(manga_list)
    log(f"✅ تم العثور على {total_manga} مانهوا. جاري المعالجة والتحميل...", "success")
    
    for idx, manga in enumerate(manga_list):
        if not status.is_running:
            break
            
        update_progress(manga_title=manga['title'], manga_current=idx+1, manga_total=total_manga)
        log(f"📚 {manga['title']} (Slug: {manga['slug']})...")
        
        # 1. Download Cover
        cover_path = download_cover(scraper, manga['cover'], manga['slug'])
        
        # 2. Fetch Chapters List
        detailed_manga = fetch_manga_details_and_chapters(scraper, manga)
        if not detailed_manga or not detailed_manga.get('chapter_links'):
            log(f"⚠️  لا توجد فصول لـ {manga['title']}", "warning")
            continue
            
        # Determine chapters to download (assuming we want all, but for safety in test let's download all)
        # Actually, if we just run this blindly it could take weeks for whole site.
        # But this is what the user requested.
        # We will loop over ALL chapters.
        
        saved_chapters_data = [] # For data.js
        
        for ch in detailed_manga['chapter_links']:
            if not status.is_running:
                break
                
            update_progress(chapter=ch['n'])
            ch_dir = os.path.join(CHAPTERS_DIR, manga['slug'], f"ch-{ch['n']}")
            
            # Check if chapter is already downloaded fully
            if os.path.exists(ch_dir) and len(os.listdir(ch_dir)) > 3:
                # Assuming if dir exists with images it's downloaded
                # We just gather relative paths
                images = sorted(os.listdir(ch_dir), key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else x)
                rel_paths = [f"assets/chapters/{manga['slug']}/ch-{ch['n']}/{img}" for img in images]
            else:
                rel_paths = download_images(scraper, ch['url'], ch_dir, manga['slug'], ch['n'])
                
            if rel_paths:
                saved_chapters_data.append({
                    "n": str(ch['n']),
                    "d": datetime.now().strftime("%Y-%m-%d"),
                    "pages": rel_paths
                })
                
        # 3. Update data.js natively!
        if saved_chapters_data:
            manga_obj = {
                "title": manga['title'],
                "img": cover_path,
                "rating": "9.0", # default
                "genres": ["Action", "Fantasy"], # default or scrape
                "status": "مستمر",
                "description": "تم السحب آلياً من Olympus.",
                "chapters": saved_chapters_data
            }
            res = add_or_update_manga_in_datajs(manga_obj)
            if res:
                log(f"✅ تم دمج المانهوا وتحديث الفصول بنجاح: {manga['title']}", "success")
            else:
                log(f"⚠️ فشل حقن المانهوا في data.js: {manga['title']}", "error")
                
        time.sleep(3) # Wait before next manga
        
    status.is_running = False
    status.progress_queue.put({"type": "done"})
    log("🏁 انتهت جميع مهام السحب بنجاح!", "success")

def start_scraper():
    if status.is_running:
        return False, "السحب يعمل حالياً!"
    
    status.is_running = True
    threading.Thread(target=scraper_worker, daemon=True).start()
    return True, "تم بدء السحب."

def stop_scraper():
    status.is_running = False
    return True, "تم إيقاف السحب. يرجى الانتظار لحين توقف المهام الحالية..."
