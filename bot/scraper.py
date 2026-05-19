import requests
from bs4 import BeautifulSoup
import cloudscraper
import re
import json
import time
from urllib.parse import urlparse, quote_plus

class MangaScraper:
    def __init__(self):
        # Using a more specific and modern fingerprint for cloudscraper
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True,
                'mobile': False
            }
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

    # ── MangaDex API Constants ─────────────────────────
    MANGADEX_API = "https://api.mangadex.org"
    MANGADEX_UPLOADS = "https://uploads.mangadex.org"

    def get_manga_details(self, url):
        """Discovers chapters and metadata from any supported manga source."""
        # Detect MangaDex URLs and extract UUID correctly
        if 'mangadex.org/title/' in url:
            parts = url.rstrip('/').split('/')
            # MangaDex URLs are typically https://mangadex.org/title/{uuid}/{slug}
            # The UUID is usually the 5th element in a full URL (index 4)
            manga_id = ""
            for p in parts:
                if len(p) == 36 and '-' in p: # Basic UUID check
                    manga_id = p
                    break
            if not manga_id: # fallback
                manga_id = parts[4] if len(parts) > 4 else parts[-1]
                
            return self._get_mangadex_details(manga_id)
            
        if 'mangadex.org' in url:
            return self._scrape_mangadex_url(url)
        elif 'mangatek.com' in url:
            return self._scrape_mangatek(url)
        elif 'olympustaff.com' in url or 'olympus-v2.com' in url:
            return self._scrape_olympus(url)
        elif 'meshmanga.com' in url or 'lek-manga.net' in url or 'lekmanga' in url.lower():
            return self._scrape_madara(url)
        else:
            # Try Madara as a generic fallback since it's very common
            try:
                return self._scrape_madara(url)
            except:
                raise ValueError(f"Unsupported source: {url}")

    def _scrape_mangatek(self, url):
        """Scrape Mangatek (Custom Theme) with full history support."""
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=20)
            if "Attention Required! | Cloudflare" in response.text or "cf-challenge" in response.text:
                print(f"[Scraper] ERROR: Mangatek is blocking us with Cloudflare. URL: {url}")
                # We'll try one last time with a slightly different header
                time.sleep(2)
                response = self.scraper.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
            
            response.encoding = 'utf-8'
            res_text = response.text
            soup = BeautifulSoup(res_text, 'lxml')
            
            title_el = soup.find('h1', class_='text-3xl') or soup.find('h1')
            title_text = title_el.get_text(strip=True) if title_el else "Unknown Title"
            
            if title_text == "Attention Required!" or "blocked" in title_text.lower():
                # Try to get title from URL slug as ultimate fallback
                title_text = url.rstrip('/').split('/')[-1].replace('-', ' ').title()
                print(f"[Scraper] Title blocked by CF, using slug: {title_text}")

            cover_el = soup.select_one('img.rounded-lg') or soup.select_one('img[src*="/manga/"]') or soup.select_one('.manga-thumbnail img')
            cover_url = cover_el['src'] if cover_el and 'src' in cover_el.attrs else ""
            if not cover_url and cover_el:
                cover_url = cover_el.get('data-src') or cover_el.get('data-lazy-src') or ""

            
            desc_el = soup.find('p', class_='text-gray-400') or soup.find('div', class_='story-info-right-extent') or soup.select_one('.summary')
            desc_text = desc_el.get_text(strip=True) if desc_el else "قصة مشوقة ومثيرة! استكشف الأحداث الآن."
            
            rating = "9.5"
            rating_match = re.search(r'(\d\.\d+|\d{1,2})\s*/\s*10', res_text) or re.search(r'rating[^\d]*(\d\.\d+)', res_text.lower()) or re.search(r'class="score"[^>]*>(\d\.\d+)', res_text)
            if rating_match:
                try:
                    r = float(rating_match.group(1))
                    if 1.0 <= r <= 10.0: rating = str(r)
                except: pass
            
            # Genres
            genres = []
            genre_tags = soup.select('a[href*="/genre/"]') or soup.select('.genre-link')
            for g in genre_tags:
                genres.append(g.text.strip())

            # Chapters Discovery (Multi-Strategy)
            chapters = []
            slug = url.rstrip('/').split('/')[-1]

            # Strategy 1: ID-Based Direct Chapters API
            try:
                manga_id = None
                m_res = self.scraper.get(f"https://mangatek.com/api/manga/{slug}", headers=self.headers, timeout=10)
                if m_res.status_code == 200:
                    m_data = m_res.json()
                    manga_id = m_data.get('id')
                
                if manga_id:
                    api_url = f"https://mangatek.com/api/chapters?filters[manga][id][$eq]={manga_id}&pagination[limit]=500&sort[0]=number:desc"
                    api_res = self.scraper.get(api_url, headers=self.headers, timeout=15)
                    if api_res.status_code == 200:
                        data = api_res.json()
                        batch = data if isinstance(data, list) else data.get('data', [])
                        if batch:
                            for item in batch:
                                ch = item.get('attributes', item)
                                chapters.append({
                                    'number': str(ch.get('number', '0')),
                                    'url': f"https://mangatek.com/reader/{item.get('id', ch.get('id'))}",
                                    'title': ch.get('title', f"الفصل {ch.get('number')}")
                                })
            except: pass

            # Strategy 2: Deep Script Scan
            if len(chapters) < 5:
                try:
                    for script in soup.find_all('script'):
                        if script.string and ('chapters' in script.string or '"id":' in script.string):
                            matches = re.findall(r'\[\s*\{\s*"id":.*?"number":.*?\s*\}\s*\]', script.string)
                            for m in matches:
                                try:
                                    data = json.loads(m)
                                    if len(data) > len(chapters):
                                        chapters = []
                                        for ch in data:
                                            chapters.append({
                                                'number': str(ch.get('number', '0')),
                                                'url': f"https://mangatek.com/reader/{ch.get('id')}",
                                                'title': ch.get('title', '')
                                            })
                                except: pass
                except: pass

            # Strategy 3: Ultra-Raw HTML Regex Scanner
            if len(chapters) < 5:
                try:
                    all_raw_links = re.findall(r'/reader/([a-zA-Z0-9\-\.\/]+)', res_text)
                    for link in set(all_raw_links):
                        if link.strip('/') == slug: continue
                        if not (link.startswith(slug + '/') or link.strip('/').isdigit()):
                            continue
                        
                        full_url = f"https://mangatek.com/reader/{link.lstrip('/')}"
                        last_part = link.rstrip('/').split('/')[-1]
                        num = last_part if last_part.replace('.', '', 1).isdigit() else "0"
                        chapters.append({
                            'number': str(num),
                            'url': full_url,
                            'title': f"الفصل {num}" if num != "0" else "رابط قراءة"
                        })
                except: pass

            # Strategy 4: Reader Context Discovery
            if len(chapters) < 5:
                try:
                    guess_url = f"https://mangatek.com/reader/{slug}/1"
                    print(f"[Discovery] No chapters found. Trying Reader Context: {guess_url}")
                    extra_chapters = self._scrape_reader_context(guess_url)
                    if len(extra_chapters) > len(chapters):
                        chapters = extra_chapters
                except: pass

            # Final Deduplication & Numeric Sorting
            seen_nums = {}
            temp_data = []
            for ch in chapters:
                try:
                    n = float(ch['number'])
                    if n not in seen_nums:
                        seen_nums[n] = ch
                except: continue
            
            for n, ch in seen_nums.items():
                temp_data.append((n, ch))
            temp_data.sort(key=lambda x: x[0])
            final_list = [x[1] for x in temp_data]

            category = 'manga'
            manhwa_hints = ['مانهوا', 'Manhwa', 'كورية', 'Korean', 'ويب تون', 'Webtoon']
            if any(hint.lower() in [g.lower() for g in genres] for hint in manhwa_hints):
                category = 'manhwa'
                
            return {
                'title': title_text,
                'cover': cover_url,
                'description': desc_text,
                'rating': rating,
                'genres': genres,
                'category': category,
                'chapters': final_list
            }
        except Exception as e:
            print(f"[Scraper] Fatal error in Mangatek: {e}")
            return {'title': url.split('/')[-1], 'chapters': [], 'description': str(e)}

    def _scrape_reader_context(self, reader_url):
        """Helper to extract chapters from a reader page."""
        try:
            res = self.scraper.get(reader_url, headers=self.headers, timeout=15)
            if "Attention Required" in res.text:
                print(f"[Scraper] Reader page blocked by Cloudflare: {reader_url}")
            
            chapters = []
            soup = BeautifulSoup(res.text, 'lxml')
            links = soup.find_all('a', href=re.compile(r'/reader/'))
            
            for link in links:
                href = link['href']
                text = link.get_text(strip=True)
                if not href.startswith('http'):
                    from urllib.parse import urlparse
                    p = urlparse(reader_url)
                    href = f"{p.scheme}://{p.netloc}{href}"
                
                num_match = re.search(r'(\d+(\.\d+)?)', text)
                if num_match:
                    num = num_match.group(1)
                else:
                    parts = href.rstrip('/').split('/')
                    if parts[-1].replace('.', '', 1).isdigit():
                        num = parts[-1]
                    else: continue
                
                chapters.append({'number': num, 'url': href, 'title': text if 'الفصل' in text else f"الفصل {num}"})
            
            # Pattern 2: Scripts
            json_blobs = re.findall(r'(\{"id":\d+,"number":".*?","title":".*?"\})', res.text)
            for blob in json_blobs:
                try:
                    ch = json.loads(blob)
                    chapters.append({
                        'number': str(ch.get('number', '0')),
                        'url': f"https://mangatek.com/reader/{ch.get('id')}",
                        'title': ch.get('title', '')
                    })
                except: pass
            return chapters
        except: return []

    def _scrape_madara(self, url):
        """Scrape Madara Theme with robust AJAX and Cloudflare support."""
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=20)
            res_text = response.text
            
            if "Just a moment..." in res_text or "cf-challenge" in res_text:
                print(f"[Scraper] Cloudflare detected for {url}. Waiting...")
                time.sleep(4)
                response = self.scraper.get(url, headers=self.headers)
                res_text = response.text

            soup = BeautifulSoup(res_text, 'lxml')
            title_el = soup.select_one('.post-title h1') or soup.find('h1') or soup.select_one('.entry-title')
            title = title_el.text.strip() if title_el else url.rstrip('/').split('/')[-1].replace('-', ' ').title()
            
            cover_el = soup.select_one('.summary_image img') or soup.select_one('.post-thumbnail img')
            cover = ""
            if cover_el:
                cover = cover_el.get('data-src') or cover_el.get('data-lazy-src') or cover_el.get('src') or ""
                
            desc_el = soup.select_one('.description-summary') or soup.select_one('.manga-excerpt') or soup.select_one('.summary__content')
            description = desc_el.text.strip() if desc_el else "قصة مشوقة ومثيرة! استكشف الأحداث الآن."
            
            rating = "9.5"
            score_el = soup.select_one('#item-rating') or soup.select_one('.score')
            if score_el:
                r_str = re.search(r'(\d\.\d+)', score_el.text)
                if r_str: rating = r_str.group(1)
            
            genres = [g.text.strip() for g in soup.select('.genres-content a')]
            chapters = self._parse_madara_chapters(soup)
            
            manga_id = None
            for pattern in [r'manga-style-id-(\d+)', r'data-id="(\d+)"', r'post-(\d+)']:
                match = re.search(pattern, res_text)
                if match:
                    manga_id = match.group(1)
                    break
                
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # AJAX Call
            if not chapters:
                try:
                    ajax_url = url.rstrip('/') + '/ajax/chapters/'
                    ajax_res = self.scraper.post(ajax_url, headers=self.headers, timeout=15)
                    if ajax_res.status_code == 200:
                        chapters.extend(self._parse_madara_chapters(BeautifulSoup(ajax_res.text, 'lxml')))
                except: pass

            if not chapters and manga_id:
                try:
                    ajax_res = self.scraper.post(f"{base_url}/wp-admin/admin-ajax.php", data={
                        'action': 'manga_get_chapters',
                        'manga': manga_id
                    }, headers=self.headers, timeout=15)
                    if ajax_res.status_code == 200:
                        chapters.extend(self._parse_madara_chapters(BeautifulSoup(ajax_res.text, 'lxml')))
                except: pass

            seen_urls = set()
            temp_data = []
            for ch in chapters:
                if ch['url'] not in seen_urls:
                    try:
                        n_match = re.search(r'(\d+(\.\d+)?)', ch['number'])
                        n = float(n_match.group(1)) if n_match else 0
                    except: n = 0
                    temp_data.append((n, ch))
                    seen_urls.add(ch['url'])
            
            temp_data.sort(key=lambda x: x[0])
            final_list = [x[1] for x in temp_data]
            
            category = 'manhwa'
            if any(h in [g.lower() for g in genres] for h in ['مانجا', 'manga']): category = 'manga'
            
            return {'title': title, 'cover': cover, 'description': description, 'rating': rating, 'genres': genres, 'category': category, 'chapters': final_list}
        except Exception as e:
            print(f"[Scraper] Madara Error: {e}")
            return {'title': url.split('/')[-1], 'chapters': []}

    def _parse_madara_chapters(self, soup):
        chapters = []
        items = soup.select('.wp-manga-chapter a') or soup.select('.list-chap a')
        for item in items:
            href = item['href']
            text = item.text.strip()
            num_match = re.search(r'(\d+(\.\d+)?)', text) or re.search(r'chapter-(\d+(\.\d+)?)', href)
            chapters.append({'number': num_match.group(1) if num_match else "0", 'url': href, 'title': text})
        return chapters

    def _scrape_olympus(self, url):
        """Scrape Olympus Staff with robust support."""
        try:
            response = self.scraper.get(url, headers=self.headers, timeout=20)
            soup = BeautifulSoup(response.text, 'lxml')
            
            title_el = soup.find('h1', class_='text-white') or soup.find('h1') or soup.select_one('.text-2xl.font-bold')
            title = title_el.text.strip() if title_el else url.rstrip('/').split('/')[-1].replace('-', ' ').title()
            
            cover_el = soup.find('img', class_='mx-auto') or soup.find('img', class_='rounded-lg') or soup.select_one('img[alt="Poster"]')
            cover_url = cover_el['src'] if cover_el and 'src' in cover_el.attrs else ""
            
            desc_el = soup.select_one('.summary') or soup.select_one('.comic-description') or soup.select_one('article')
            description = desc_el.text.strip() if desc_el else "قصة مشوقة ومثيرة!"
            
            rating = "9.5"
            r_match = re.search(r'([0-9](\.[0-9]+)?)\s*(/|من)\s*10', response.text)
            if r_match: rating = str(float(r_match.group(1)))
            
            genres = [g.text.strip() for g in soup.select('a[href*="/type/"], a[href*="/genre/"]')]
            chapters = []
            for link in soup.find_all('a', href=re.compile(r'/chapter/|/series/')):
                href = link['href']
                txt = link.get_text(strip=True)
                if any(char.isdigit() for char in txt) or "فصل" in txt:
                    num_match = re.search(r'(\d+(\.\d+)?)', txt)
                    chapters.append({
                        'number': num_match.group(1) if num_match else "0",
                        'url': href if href.startswith('http') else f"https://olympustaff.com{href}",
                        'title': txt
                    })
                
            seen_urls = set()
            temp_data = []
            for ch in chapters:
                if ch['url'] not in seen_urls:
                    try: n = float(ch['number'])
                    except: n = 0
                    temp_data.append((n, ch))
                    seen_urls.add(ch['url'])
            
            temp_data.sort(key=lambda x: x[0])
            return {'title': title, 'cover': cover_url, 'description': description, 'rating': rating, 'genres': genres, 'category': 'manhwa', 'chapters': [x[1] for x in temp_data]}
        except: return {'title': url.split('/')[-1], 'chapters': []}

    def get_chapter_images(self, url):
        """Scrape all manga pages from a chapter URL with enhanced selectors."""
        # Handle MangaDex chapter URLs
        if 'mangadex.org' in url or 'api.mangadex.org' in url:
            return self._get_mangadex_chapter_images_from_url(url)

        try:
            response = self.scraper.get(url, headers=self.headers, timeout=25)
            res_text = response.text
            
            if "Just a moment..." in res_text:
                 time.sleep(3) 

            soup = BeautifulSoup(res_text, 'lxml')
            
            selectors = [
                '.reading-content img', '.wp-manga-chapter-img', '.chapter-content img', 
                '.reader-area img', '#chapter-video-frame img', '.page-break img', 
                '.vung-doc img', '.container-reading img', '.entry-content img'
            ]
            
            image_tags = []
            for selector in selectors:
                found = soup.select(selector)
                if found and len(found) > 2:
                    image_tags = found
                    break
            
            if not image_tags:
                image_tags = [img for img in soup.find_all('img') if not any(x in (img.get('src') or "").lower() for x in ['logo', 'banner', 'avatar', 'ads'])]

            images = []
            for img in image_tags:
                src = (
                    img.get('data-src') or 
                    img.get('data-lazy-src') or 
                    img.get('data-original') or 
                    img.get('data-src-img') or
                    img.get('data-echo') or
                    img.get('src')
                )
                
                if src:
                    src = src.strip()
                    if src.startswith('data:image') or 'pixel.gif' in src or not src: continue
                    if src.startswith('//'): src = 'https:' + src
                    elif src.startswith('/'):
                        p = urlparse(url)
                        src = f"{p.scheme}://{p.netloc}{src}"
                    images.append(src)
            
            seen = set()
            return [x for x in images if not (x in seen or seen.add(x))]
        except Exception as e:
            print(f"[Scraper] Error fetching images: {e}")
            return []

    def search_manga(self, query, include_english=True):
        """Searches for a manga across multiple sources and returns a list of candidates."""
        query_safe = query.replace(' ', '+')
        sources = [
            {"name": "Olympus Staff", "url": f"https://olympustaff.com/series?search={query_safe}", "lang": "ar"},
            {"name": "Mangatek", "url": f"https://mangatek.com/?s={query_safe}", "lang": "ar"},
            {"name": "Lek Manga", "url": f"https://lek-manga.net/?s={query_safe}&post_type=wp-manga", "lang": "ar"}
        ]
        
        results = []

        # ── MangaDex Search (English - API) ────────────
        if include_english:
            try:
                print(f"[Search] Searching '{query}' on MangaDex (EN)...")
                mdx_results = self._search_mangadex(query)
                results.extend(mdx_results)
            except Exception as e:
                print(f"[Search] Error on MangaDex: {e}")

        # ── Arabic Sources ─────────────────────────────
        for source in sources:
            try:
                print(f"[Search] Searching '{query}' on {source['name']}...")
                res = self.scraper.get(source['url'], headers=self.headers, timeout=15)
                if res.status_code != 200: continue
                
                soup = BeautifulSoup(res.text, 'lxml')
                q_words = set(re.sub(r'[^a-z0-9 ]', '', query.lower()).split())
                
                def is_good_match(found_title):
                    f_words = set(re.sub(r'[^a-z0-9 ]', '', found_title.lower()).split())
                    if not q_words or not f_words: return False
                    intersection = q_words.intersection(f_words)
                    return len(intersection) / len(q_words) >= 0.7 or query.lower() in found_title.lower()

                if source['name'] == "Olympus Staff":
                    for a in soup.find_all('a', href=re.compile(r'/series/')):
                        title_el = a.find('h3') or a.find('h4') or a.find('p') or a.find('span', class_='font-bold')
                        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
                        if is_good_match(title):
                            href = a['href']
                            full_url = href if href.startswith('http') else f"https://olympustaff.com{href}"
                            if full_url not in [r['url'] for r in results]:
                                results.append({"title": title, "url": full_url, "source": source['name'], "lang": "ar"})
                
                else:
                    items = soup.select('.c-tabs-item__content') or soup.select('.manga-title h3 a') or soup.select('.post-title a') or soup.select('a[href*="/manga/"]')
                    for item in items:
                        a = item if item.name == 'a' else item.find('a')
                        if a and a.get('href') and ('/manga/' in a['href'] or '/series/' in a['href']):
                            title = a.get_text(strip=True)
                            if not title:
                                title = a.get('title') or ""
                            
                            if is_good_match(title):
                                url_val = a['href']
                                if url_val.startswith('/'):
                                    p = urlparse(source['url'])
                                    url_val = f"{p.scheme}://{p.netloc}{url_val}"
                                    
                                if url_val not in [r['url'] for r in results]:
                                    results.append({"title": title, "url": url_val, "source": source['name'], "lang": "ar"})
                
                if len(results) >= 20: break
            except Exception as e:
                print(f"[Search] Error on {source['name']}: {e}")
                
        return results

    def _scrape_olympus(self, url):
        """Scrape Olympus V3 (Team-X) with support for new path-based chapters."""
        try:
            res = self.scraper.get(url, headers=self.headers, timeout=20)
            soup = BeautifulSoup(res.text, 'lxml')
            
            title = soup.find('h1') or soup.find('h6') or soup.select_one('.text-white.font-bold')
            title_text = title.get_text(strip=True) if title else "Solo Leveling"
            
            cover_el = soup.select_one('img[src*="/storage/"]') or soup.select_one('img.rounded-lg')
            cover_url = ""
            if cover_el:
                cover_url = cover_el['src']
                if cover_url.startswith('/'):
                    from urllib.parse import urlparse
                    p = urlparse(url)
                    cover_url = f"{p.scheme}://{p.netloc}{cover_url}"
            
            desc_el = soup.select_one('p.text-sm') or soup.select_one('.summary')
            desc_text = desc_el.get_text(strip=True) if desc_el else ""

            # Discover Chapters from HTML
            chapters = []
            links = soup.select('a[href*="/series/"]')
            seen_nums = set()
            
            for a in links:
                href = a['href']
                # Match structures like /series/SL/1 or /series/NAME/10
                match = re.search(r'/series/[^/]+/(\d+\.?\d*)$', href)
                if match:
                    num = match.group(1)
                    if num not in seen_nums:
                        chapters.append({
                            'number': num,
                            'url': href if href.startswith('http') else f"https://olympustaff.com{href}",
                            'title': f"الفصل {num}"
                        })
                        seen_nums.add(num)
            
            # Sort chapters numerically
            chapters.sort(key=lambda x: float(x['number']))
            
            return {
                'title': title_text,
                'cover': cover_url,
                'desc': desc_text,
                'chapters': chapters,
                'genres': [g.text.strip() for g in soup.select('a[href*="genre="]')]
            }
        except Exception as e:
            print(f"[Olympus] Error: {e}")
            # Fallback to Madara if V3 fails
            return self._scrape_madara(url)

    # ══════════════════════════════════════════════════════
    #  MangaDex API Integration (English Source)
    # ══════════════════════════════════════════════════════

    def _search_mangadex(self, query, limit=10):
        """Search MangaDex API for manga/manhwa titles."""
        results = []
        try:
            params = {
                'title': query,
                'limit': limit,
                'includes[]': ['cover_art'],
                'order[relevance]': 'desc',
                'contentRating[]': ['safe', 'suggestive'],
            }
            resp = requests.get(
                f"{self.MANGADEX_API}/manga",
                params=params,
                headers={'User-Agent': self.headers['User-Agent']},
                timeout=15
            )
            if resp.status_code != 200:
                print(f"[MangaDex] API returned {resp.status_code}")
                return results

            data = resp.json().get('data', [])
            for manga in data:
                manga_id = manga['id']
                attrs = manga.get('attributes', {})

                # Get title (prefer English, fallback to any)
                titles = attrs.get('title', {})
                title = titles.get('en') or titles.get('ja-ro') or titles.get('ja') or next(iter(titles.values()), 'Unknown')

                # Get cover from relationships
                cover_filename = ''
                for rel in manga.get('relationships', []):
                    if rel['type'] == 'cover_art':
                        cover_filename = rel.get('attributes', {}).get('fileName', '')
                        break

                cover_url = ''
                if cover_filename:
                    cover_url = f"{self.MANGADEX_UPLOADS}/covers/{manga_id}/{cover_filename}"

                results.append({
                    'title': title,
                    'url': f"https://mangadex.org/title/{manga_id}",
                    'source': 'MangaDex (EN)',
                    'lang': 'en',
                    'cover': cover_url,
                    'mangadex_id': manga_id
                })

            print(f"[MangaDex] Found {len(results)} results for '{query}'")
        except Exception as e:
            print(f"[MangaDex] Search error: {e}")

        return results

    def _scrape_mangadex_url(self, url):
        """Extract manga details from a MangaDex URL using the API."""
        # Extract manga ID from URL
        match = re.search(r'mangadex\.org/title/([a-f0-9-]+)', url)
        if not match:
            raise ValueError(f"Invalid MangaDex URL: {url}")

        manga_id = match.group(1)
        return self._get_mangadex_details(manga_id)

    def _get_mangadex_details(self, manga_id):
        """Get full manga details from MangaDex API by manga ID."""
        try:
            # 1. Manga metadata
            resp = requests.get(
                f"{self.MANGADEX_API}/manga/{manga_id}",
                params={'includes[]': ['cover_art', 'author', 'artist']},
                headers={'User-Agent': self.headers['User-Agent']},
                timeout=15
            )
            if resp.status_code != 200:
                return {'title': manga_id, 'chapters': [], 'description': f'API Error: {resp.status_code}'}

            manga = resp.json().get('data', {})
            attrs = manga.get('attributes', {})

            # Title Selection (Prefer Arabic if available in altTitles)
            titles = attrs.get('title', {})
            main_title = titles.get('en') or titles.get('ja-ro') or next(iter(titles.values()), 'Unknown')
            
            # Look for Arabic title in altTitles
            alt_titles = attrs.get('altTitles', [])
            arabic_title = ""
            for alt in alt_titles:
                if 'ar' in alt:
                    arabic_title = alt['ar']
                    break
            
            title = arabic_title if arabic_title else main_title

            # Description Translation
            descriptions = attrs.get('description', {})
            description = descriptions.get('ar') or descriptions.get('en') or next(iter(descriptions.values()), '')
            
            if description and not descriptions.get('ar'):
                try:
                    from deep_translator import GoogleTranslator
                    print(f"[MangaDex] Translating description for '{title}'...")
                    description = GoogleTranslator(source='auto', target='ar').translate(description)
                except Exception as e:
                    print(f"[MangaDex] Metadata translation error: {e}")
            
            if not description:
                description = "قصة مشوقة ومثيرة! استكشف الأحداث الآن."

            # Cover (original quality)
            cover_url = ''
            for rel in manga.get('relationships', []):
                if rel['type'] == 'cover_art':
                    fn = rel.get('attributes', {}).get('fileName', '')
                    if fn:
                        cover_url = f"{self.MANGADEX_UPLOADS}/covers/{manga_id}/{fn}"
                    break

            # Genres / Tags
            genres = []
            category = 'manhwa'
            for tag in attrs.get('tags', []):
                tag_name = tag.get('attributes', {}).get('name', {}).get('en', '')
                if tag_name:
                    genres.append(tag_name)

            # Detect type
            original_lang = attrs.get('originalLanguage', '')
            if original_lang == 'ko':
                category = 'manhwa'
            elif original_lang == 'ja':
                category = 'manga'
            elif original_lang == 'zh':
                category = 'manhua'

            # Status
            status_map = {'ongoing': 'مستمر', 'completed': 'مكتمل', 'hiatus': 'متوقف', 'cancelled': 'ملغي'}
            status = status_map.get(attrs.get('status', ''), 'مستمر')

            # Rating
            rating = '9.0'

            # 2. Chapters (English)
            chapters = self._get_mangadex_chapters(manga_id)

            return {
                'title': title,
                'cover': cover_url,
                'description': description,
                'rating': rating,
                'genres': genres,
                'category': category,
                'status': status,
                'chapters': chapters,
                'lang': 'en',
                'mangadex_id': manga_id
            }

        except Exception as e:
            print(f"[MangaDex] Details error: {e}")
            return {'title': manga_id, 'chapters': [], 'description': str(e)}

    def _get_mangadex_chapters(self, manga_id, lang='en'):
        """Get all chapters for a manga from MangaDex API with robust handling."""
        chapters = []
        try:
            # We fetch more chapters in one go and handle the feed correctly
            url = f"{self.MANGADEX_API}/manga/{manga_id}/feed"
            # Correct way to pass list parameters in requests for MangaDex
            params = [
                ('translatedLanguage[]', lang),
                ('order[chapter]', 'asc'),
                ('limit', 500),
                ('contentRating[]', 'safe'),
                ('contentRating[]', 'suggestive'),
                ('contentRating[]', 'erotica')
            ]
            resp = requests.get(url, params=params, headers={'User-Agent': self.headers['User-Agent']}, timeout=15)
            
            if resp.status_code != 200:
                print(f"[MangaDex] Feed API returned {resp.status_code}")
                return []

            data = resp.json().get('data', [])
            for ch in data:
                ch_id = ch['id']
                attr = ch.get('attributes', {})
                ch_num = attr.get('chapter') or "0"
                ch_title = attr.get('title') or f"Chapter {ch_num}"
                
                chapters.append({
                    'number': ch_num,
                    'title': ch_title,
                    'url': f"{self.MANGADEX_API}/at-home/server/{ch_id}", # We use ID for the reader
                    'id': ch_id
                })
            
            print(f"[MangaDex] Found {len(chapters)} {lang} chapters.")
            return chapters
        except Exception as e:
            print(f"[MangaDex] Feed error: {e}")
            return []

    def _get_mangadex_chapter_images_from_url(self, url):
        """Get chapter images from MangaDex URL or internal ID/URI."""
        chapter_id = url
        if 'mangadex.org/chapter/' in url:
            chapter_id = url.split('/')[-1].split('?')[0]
        elif 'api.mangadex.org/at-home/server/' in url:
            chapter_id = url.split('/')[-1]
        elif url.startswith('mangadex://chapter/'):
            chapter_id = url.replace('mangadex://chapter/', '')
            if match:
                chapter_id = match.group(1)
            else:
                print(f"[MangaDex] Cannot extract chapter ID from: {url}")
                return []

        return self._get_mangadex_chapter_images(chapter_id)

    def _get_mangadex_chapter_images(self, chapter_id):
        """Get page image URLs for a specific MangaDex chapter using At-Home API."""
        try:
            url = f"{self.MANGADEX_API}/at-home/server/{chapter_id}"
            resp = requests.get(url, headers={'User-Agent': self.headers['User-Agent']}, timeout=15)

            if resp.status_code != 200:
                print(f"[MangaDex] At-Home API error: {resp.status_code} for {chapter_id}")
                return []

            data = resp.json()
            base_url = data.get('baseUrl')
            chapter = data.get('chapter')
            
            if not base_url or not chapter:
                print(f"[MangaDex] Missing critical data (baseUrl/chapter) in API response for {chapter_id}")
                return []
                
            ch_hash = chapter.get('hash')
            pages = chapter.get('data') # Regular quality
            
            if not ch_hash or not pages:
                print(f"[MangaDex] Missing hash or pages list for chapter {chapter_id}")
                return []

            image_urls = [f"{base_url}/data/{ch_hash}/{p}" for p in pages]
            print(f"[MangaDex] Found {len(image_urls)} images for chapter {chapter_id}")
            return image_urls
        except Exception as e:
            print(f"[MangaDex] Chapter images exception: {e}")
            return []

        except Exception as e:
            print(f"[MangaDex] Chapter images error: {e}")
            return []

    def get_mangadex_cover(self, manga_id):
        """Get the highest quality cover image URL from MangaDex."""
        try:
            resp = requests.get(
                f"{self.MANGADEX_API}/cover",
                params={
                    'manga[]': [manga_id],
                    'limit': 1,
                    'order[volume]': 'asc'
                },
                headers={'User-Agent': self.headers['User-Agent']},
                timeout=10
            )

            if resp.status_code == 200:
                covers = resp.json().get('data', [])
                if covers:
                    fn = covers[0].get('attributes', {}).get('fileName', '')
                    if fn:
                        # Return original (full quality) cover URL
                        return f"{self.MANGADEX_UPLOADS}/covers/{manga_id}/{fn}"
        except Exception as e:
            print(f"[MangaDex] Cover fetch error: {e}")

        return ''

    def detect_source_language(self, url):
        """Detect if a source is English or Arabic based on the URL."""
        english_domains = ['mangadex.org', 'asurascans', 'reaperscans', 'flamescans', 'mangakakalot', 'manganato']
        arabic_domains = ['olympustaff.com', 'olympus-v2.com', 'mangatek.com', 'lek-manga.net', 'meshmanga.com', 'lekmanga']

        url_lower = url.lower()
        for domain in english_domains:
            if domain in url_lower:
                return 'en'
        for domain in arabic_domains:
            if domain in url_lower:
                return 'ar'

        return 'ar'  # Default to Arabic for existing behavior

    def get_popular_from_all_sources(self, count_per_site=5):
        """Discover popular works from multiple sources (Arabic focus)."""
        from urllib.parse import urlparse
        sources = [
            {"url": "https://olympustaff.com", "selectors": ["a[href*='/series/']"], "name": "Olympus Staff"},
            {"url": "https://mangatek.com", "selectors": ["a[href*='/manga/']"], "name": "Mangatek"},
            {"url": "https://lek-manga.net", "selectors": [".page-item-detail.manga a", ".manga-title h3 a"], "name": "Lek Manga"},
            {"url": "https://meshmanga.com", "selectors": [".page-item-detail.manga a", ".manga-title h3 a"], "name": "Mesh Manga"}
        ]
        
        all_results = []
        seen_urls = set()
        
        for src in sources:
            try:
                print(f"[Discovery] Searching popular on {src['name']}...")
                res = self.scraper.get(src['url'], headers=self.headers, timeout=15)
                soup = BeautifulSoup(res.text, 'lxml')
                found_on_this_site = 0
                
                for selector in src['selectors']:
                    for a in soup.select(selector):
                        href = a.get('href')
                        title = a.get_text(strip=True)
                        if not title:
                            title = a.get('title') or ""
                        
                        if href and ('/series/' in href or '/manga/' in href):
                            if not href.startswith('http'):
                                p = urlparse(src['url'])
                                href = f"{p.scheme}://{p.netloc}{href}"
                            
                            href_lower = href.lower()
                            # Filter out non-series links
                            if any(x in href_lower for x in ['/genre/', '/type/', '/year/', '/status/', '?search=', '/reader/']): continue
                            
                            if href not in seen_urls:
                                seen_urls.add(href)
                                all_results.append({"title": title or href.split('/')[-1], "url": href})
                                found_on_this_site += 1
                                if found_on_this_site >= count_per_site: break
                    if found_on_this_site >= count_per_site: break
                
                print(f"[Discovery] Found {found_on_this_site} titles on {src['name']}")
                
            except Exception as e:
                print(f"[Discovery] Error on {src['name']}: {e}")
                
        return all_results

    def get_mangakatana_cover(self, title):
        """Search MangaKatana for a high-quality cover and return absolute URL."""
        try:
            query = quote_plus(title)
            url = f"https://mangakatana.com/?search={query}"
            resp = self.scraper.get(url, headers=self.headers, timeout=15)
            if resp.status_code != 200: return ""

            soup = BeautifulSoup(resp.text, 'lxml')
            items = soup.select('#manga_list .item')
            if not items: return ""

            # Normalize query words for matching
            q_words = set(re.sub(r'[^a-z0-9 ]', '', title.lower()).split())

            for item in items:
                title_a = item.select_one('.title a')
                if not title_a: continue
                
                found_title = title_a.get_text(strip=True)
                f_words = set(re.sub(r'[^a-z0-9 ]', '', found_title.lower()).split())
                
                # Check if it's a good match
                if q_words.intersection(f_words) or title.lower() in found_title.lower():
                    img = item.select_one('.image img')
                    if img:
                        src = img.get('src') or img.get('data-src')
                        if src and src.startswith('//'): src = 'https:' + src
                        return src
            return ""
        except Exception as e:
            print(f"[MangaKatana] Cover error: {e}")
            return ""

    def get_best_cover(self, title):
        """Try multiple sources with aggressive title variations to get a cover."""
        print(f"[Covers] Aggressive search for: {title}")
        
        # Clean title variations
        variations = [
            title,
            re.sub(r'[:\-!?,]', '', title), # Remove punctuation
            ' '.join(title.split()[:4]), # First 4 words
            ' '.join(title.split()[:3])  # First 3 words (even broader)
        ]
        # Deduplicate variations
        variations = list(dict.fromkeys(v for v in variations if len(v) > 3))

        for v in variations:
            print(f"  🔍 Trying variation: '{v}'")
            # 1. Try MangaDex
            try:
                mdx = self._search_mangadex(v, limit=2)
                for res in mdx:
                    if res.get('cover'):
                        print(f"  ✨ Found on MangaDex via '{v}'")
                        return res['cover']
            except: pass

            # 2. Try MangaKatana
            try:
                mk = self.get_mangakatana_cover(v)
                if mk:
                    print(f"  ✨ Found on MangaKatana via '{v}'")
                    return mk
            except: pass

        return ""

    def get_best_source_chapters(self, title, primary_url):
        """
        Searches all sources for the manga title, fetches chapter list for matching sources,
        and returns a merged list of chapters along with details.
        """
        print(f"[Multi-Source] Searching for best/complete chapters for '{title}'...")
        
        # 1. Search all sources
        candidates = self.search_manga(title, include_english=True)
        if not candidates:
            candidates = []
        
        # Normalize search words for matching
        q_words = set(re.sub(r'[^a-z0-9 ]', '', title.lower()).split())
        
        # Add primary URL as candidate
        candidates.insert(0, {
            "title": title,
            "url": primary_url,
            "source": "Primary",
            "lang": self.detect_source_language(primary_url)
        })
        
        # Remove duplicate candidate URLs to avoid repeating scraping
        seen_candidate_urls = set()
        unique_candidates = []
        for c in candidates:
            if c['url'] not in seen_candidate_urls:
                seen_candidate_urls.add(c['url'])
                unique_candidates.append(c)
                
        # 2. Iterate and get details
        merged_chapters = {} # normalized_ch_number -> ch_dict
        all_found_sources = []
        
        for cand in unique_candidates:
            # Check title similarity
            cand_title = cand.get('title', '')
            c_words = set(re.sub(r'[^a-z0-9 ]', '', cand_title.lower()).split())
            
            # Simple word intersection matching
            intersection = q_words.intersection(c_words)
            if cand['source'] != "Primary" and len(intersection) / max(1, len(q_words)) < 0.6 and title.lower() not in cand_title.lower() and cand_title.lower() not in title.lower():
                print(f"[Multi-Source] Skipping candidate '{cand_title}' on {cand['source']} - Title similarity too low.")
                continue
                
            print(f"[Multi-Source] Fetching chapters from {cand['source']}: {cand['url']}")
            try:
                details = self.get_manga_details(cand['url'])
                ch_list = details.get('chapters', [])
                if ch_list:
                    all_found_sources.append((cand['source'], len(ch_list), cand['url'], cand.get('lang', 'ar')))
                    
                    # Merge chapters: if chapter is already in merged_chapters, we prefer:
                    # - Arabic source over English (lang == 'ar' vs 'en') because it doesn't need download/translation
                    # - If same lang, keep the one we already have.
                    for ch in ch_list:
                        num_str = str(ch.get('number', ch.get('n', '0')))
                        # Parse float number for indexing
                        try:
                            num_match = re.search(r'(\d+\.?\d*)', num_str)
                            num_float = float(num_match.group(1)) if num_match else 0.0
                        except:
                            num_float = 0.0
                            
                        existing_ch = merged_chapters.get(num_float)
                        if not existing_ch:
                            ch['n'] = num_str # ensure 'n' is populated
                            ch['source'] = cand['source']
                            ch['lang'] = cand.get('lang', 'ar')
                            merged_chapters[num_float] = ch
                        elif existing_ch.get('lang') == 'en' and cand.get('lang') == 'ar':
                            ch['n'] = num_str
                            ch['source'] = cand['source']
                            ch['lang'] = cand.get('lang', 'ar')
                            merged_chapters[num_float] = ch
            except Exception as e:
                print(f"[Multi-Source] Error fetching from candidate {cand['source']}: {e}")
                
        # 3. Sort chapters numerically (descending, as needed by DB)
        sorted_nums = sorted(merged_chapters.keys(), reverse=True)
        final_chapters = [merged_chapters[n] for n in sorted_nums]
        
        # 4. Fill Gap Warning/Fixing: log if we still have huge gaps
        if len(sorted_nums) > 1:
            min_ch = sorted_nums[-1]
            max_ch = sorted_nums[0]
            expected_count = int(max_ch - min_ch + 1)
            actual_count = len(sorted_nums)
            if expected_count > actual_count * 2 and expected_count < 1000:
                print(f"[Multi-Source] WARNING: Gaps detected! Expected ~{expected_count} chapters, but found only {actual_count}.")
                
        print(f"[Multi-Source] Completed. Found {len(final_chapters)} total merged chapters across sources: {all_found_sources}")
        return final_chapters

