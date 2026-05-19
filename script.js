/* =========================================================
   Nexus - Homepage Logic (2026)
   Uses data.js for shared SITE_DATA
   ========================================================= */

// Safe LocalStorage Interceptor to prevent SecurityError on file:/// protocol
(function() {
    try {
        const x = '__storage_test__';
        window.localStorage.setItem(x, x);
        window.localStorage.removeItem(x);
    } catch (e) {
        console.warn('[SafeStorage] localStorage is blocked or insecure in this environment. Using memory fallback.');
        const mockStore = {};
        const mockStorage = {
            getItem: function(key) {
                return key in mockStore ? mockStore[key] : null;
            },
            setItem: function(key, val) {
                mockStore[key] = String(val);
            },
            removeItem: function(key) {
                delete mockStore[key];
            },
            clear: function() {
                for (let key in mockStore) delete mockStore[key];
            },
            key: function(i) {
                const keys = Object.keys(mockStore);
                return keys[i] || null;
            },
            get length() {
                return Object.keys(mockStore).length;
            }
        };
        Object.defineProperty(window, 'localStorage', {
            value: mockStorage,
            writable: true
        });
    }
})();

let currentCategory = 'manhwa';

// API Configuration
const API_BASE_URL = 'http://localhost:3000/api';

// =========================================================
// DB → SITE_DATA Bridge
// Auto-generates SITE_DATA from the scraped DB array
// =========================================================
function titleToSlug(title) {
    return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function findSeriesBySlug(slug) {
    if (!slug) return null;
    // Search in DB first (scraped data - primary source)
    if (typeof DB !== 'undefined') {
        const found = DB.find(s => titleToSlug(s.title) === slug);
        if (found) return { item: found, category: 'manhwa' };
    }
    // Then search in SITE_DATA
    if (typeof SITE_DATA !== 'undefined') {
        for (let cat in SITE_DATA) {
            const list = SITE_DATA[cat].latest || [];
            const found = list.find(s => titleToSlug(s.title) === slug);
            if (found) return { item: found, category: cat };
        }
    }
    return null;
}

// NSFW tag filter - blocks adult content
const NSFW_TAGS = ['adult','mature','smut','ecchi','hentai','pornographic','+18','18+','nsfw','إباحي','بالغين'];
function isNSFW(entry) {
    if (!entry || !entry.genres) return false;
    const genres = Array.isArray(entry.genres) ? entry.genres : (typeof entry.genres === 'string' ? entry.genres.split(',') : []);
    return genres.some(g => NSFW_TAGS.includes(g.trim().toLowerCase()));
}

function generateSiteDataFromDB(db) {
    if (!db || db.length === 0) return null;

    // Filter out NSFW content globally
    db = db.filter(entry => !isNSFW(entry));

    function getEntriesByType(type) {
        return db.filter(entry => {
            const entryType = entry.type || 'manhwa';
            if (type === 'manhwa') {
                return entryType === 'manhwa';
            } else if (type === 'manga') {
                return entryType === 'manga';
            } else if (type === 'romance') {
                const genres = Array.isArray(entry.genres) ? entry.genres : (typeof entry.genres === 'string' ? entry.genres.split(',') : []);
                return genres.some(g => g.trim().toLowerCase().includes('romance') || g.trim().includes('رومانسي'));
            }
            return false;
        });
    }

    function toDisplayItem(entry, rank) {
        if (!entry) return null;
        const sortedChs = Array.isArray(entry.chapters) && entry.chapters.length > 0
            ? [...entry.chapters].sort((a, b) => parseFloat(b.n) - parseFloat(a.n))
            : [];
        const latestCh = sortedChs[0];

        return {
            title: entry.title || 'بدون عنوان',
            img: (typeof entry.cover === 'string' && entry.cover.trim() !== "") ? entry.cover.trim() : 'https://via.placeholder.com/300x450/111111/00FF9F?text=No+Cover',
            desc: entry.desc || 'الوصف غير متاح.',
            rating: entry.rating || (8.0 + Math.random() * 1.9).toFixed(1),
            genres: Array.isArray(entry.genres) ? entry.genres.join(', ') : (typeof entry.genres === 'string' ? entry.genres : 'Action, Fantasy'),
            rank: rank || 1,
            ch: latestCh ? `فصل ${latestCh.n}` : 'قريباً',
            chapters: sortedChs.map(c => ({
                n: c.n,
                d: c.d || 'اليوم',
                pages: Array.isArray(c.pages) ? c.pages : []
            }))
        };
    }

    const categoriesData = {};
    const categories = ['manhwa', 'manga', 'romance'];

    categories.forEach(cat => {
        const catEntries = getEntriesByType(cat);
        const withChapters = catEntries.filter(s => s.chapters && s.chapters.length > 0);
        
        // Sort by chapter count (most chapters first = more content)
        const sortedWithChapters = [...withChapters].sort((a, b) => (b.chapters?.length || 0) - (a.chapters?.length || 0));

        const trending = sortedWithChapters.slice(0, 10).map((e, i) => toDisplayItem(e, i + 1));
        const topSlider = sortedWithChapters.slice(0, 8).map((e, i) => toDisplayItem(e, i + 1));
        const latest = sortedWithChapters.map((e, i) => toDisplayItem(e, i + 1));
        const popular = catEntries.slice(0, 20).map((e, i) => toDisplayItem(e, i + 1));
        
        // Pick random suggestions
        const shuffled = [...catEntries].sort(() => 0.5 - Math.random());
        const randomHero = shuffled.length > 0 ? [toDisplayItem(shuffled[0], 1)] : [];
        const randomRecs = shuffled.slice(1, 11).map((e, i) => toDisplayItem(e, i + 1));

        categoriesData[cat] = { trending, topSlider, latest, popular, randomHero, randomRecs };
    });

    return categoriesData;
}

// Generate SITE_DATA from DB if not already defined
if (typeof SITE_DATA === 'undefined' || !SITE_DATA) {
    if (typeof DB !== 'undefined' && DB.length > 0) {
        var SITE_DATA = generateSiteDataFromDB(DB);
        console.log('[Bridge] SITE_DATA generated from DB with', DB.length, 'series');
    } else {
        var SITE_DATA = { manhwa: { trending: [], topSlider: [], latest: [], popular: [] }, manga: { trending: [], topSlider: [], latest: [], popular: [] }, comics: { trending: [], topSlider: [], latest: [], popular: [] }, novels: { trending: [], topSlider: [], latest: [], popular: [] } };
        console.warn('[Bridge] No DB data found, using empty SITE_DATA');
    }
}

// Initialize immediately
document.addEventListener('DOMContentLoaded', () => {
    initCategoryTabs();
    renderHomeContent(currentCategory);
    initReaderEngine();
    initPremiumCarouselAutoplay();
    initMobileMenu();
    initSearchOverlay();

    // Auto-hide header on scroll down
    let lastScroll = 0;

    const header = document.getElementById('stickyHeader');
    if (header) {
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            if (currentScroll <= 0) {
                header.classList.remove('hidden');
                return;
            }
            if (currentScroll > lastScroll && currentScroll > 150) {
                header.classList.add('hidden');
            } else if (currentScroll < lastScroll) {
                header.classList.remove('hidden');
            }
            lastScroll = currentScroll;
        }, { passive: true });
    }

    // URL Params Reader Trigger
    const params = new URLSearchParams(window.location.search);
    if (params.get('reader') === 'true') {
        const titleSlug = params.get('title');
        const chNum = params.get('ch');
        if (titleSlug) {
            const series = findSeriesBySlug(titleSlug);
            if (series) {
                window.openReader(series.item.title, chNum || (series.item.chapters && series.item.chapters[0] ? series.item.chapters[0].n : '1'));
            }
        }
    }

    // Initialize Scroll To Top Button
    const scrollTopBtn = document.createElement('button');
    scrollTopBtn.id = 'scrollTopBtn';
    scrollTopBtn.className = 'scroll-top-btn';
    scrollTopBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    document.body.appendChild(scrollTopBtn);

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });

    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Initialize Load More Updates Button
    const loadMoreBtn = document.getElementById('loadMoreUpdatesBtn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            currentLatestCount += 4;
            renderLatestUpdates(cachedLatestData);
            
            // Hide button if all items are shown
            if (currentLatestCount >= cachedLatestData.length) {
                loadMoreBtn.style.display = 'none';
            }
        });
    }

    // Start Auto-Animations for Homepage
    initHeroAutoRotation();
    initPopularSliderAutoMotion();
});

// --- Dynamic Animations ---

function initHeroAutoRotation() {
    let heroTimer = setInterval(() => {
        if (typeof SITE_DATA !== 'undefined' && SITE_DATA[currentCategory]) {
            const data = SITE_DATA[currentCategory];
            const pool = [...(data.trending || []), ...(data.randomHero || [])];
            if (pool.length > 0) {
                const randomItem = [pool[Math.floor(Math.random() * pool.length)]];
                renderRandomHero(randomItem);
            }
        }
    }, 10000); // 10 Seconds
}

function initPopularSliderAutoMotion() {
    const track = document.getElementById('premiumCarouselTrack');
    if (!track) return;
    
    let scrollSpeed = 1; // pixels per step
    let direction = -1; // -1 for moving right in RTL/Some contexts, 1 for left
    
    // We'll use a smooth interval
    let motionInterval = setInterval(() => {
        if (track) {
            track.scrollLeft += direction; // Moving towards the right
            
            // Loop logic
            if (Math.abs(track.scrollLeft) >= (track.scrollWidth - track.clientWidth)) {
                track.scrollLeft = 0;
            }
        }
    }, 50);

    // Pause on hover
    track.addEventListener('mouseenter', () => clearInterval(motionInterval));
    track.addEventListener('mouseleave', () => {
        motionInterval = setInterval(() => { track.scrollLeft += direction; if (Math.abs(track.scrollLeft) >= (track.scrollWidth - track.clientWidth)) track.scrollLeft = 0; }, 50);
    });
};

// Navigation & Modal Logic
window.goToSeries = function(title, category) {
    const slug = titleToSlug(title);
    if (slug) {
        window.location.href = 'series.html?title=' + encodeURIComponent(slug);
    } else {
        console.error('Series not found:', title);
    }
};

function populateSeriesModal(seriesData) {
    const modal = document.getElementById('seriesModal');
    const titleEl = document.getElementById('smTitle');
    const coverEl = document.getElementById('smCover');
    const ratingEl = document.getElementById('smRating');
    const statusEl = document.getElementById('smStatus');
    const synopsisEl = document.getElementById('smSynopsis');
    const genresEl = document.getElementById('smGenres');
    const chaptersList = document.getElementById('smChaptersList');
    const startReadingBtn = document.getElementById('smStartReadingBtn');
    
    if (!modal || !titleEl) return;
    
    titleEl.textContent = seriesData.title || seriesData.n;
    
    // Support both API format 'cover' and DB format 'img'
    const coverUrl = seriesData.cover || seriesData.img || 'images/default-cover.jpg';
    if (coverEl) coverEl.src = coverUrl;
    
    const backdrop = document.getElementById('seriesModalBackdrop');
    if (backdrop) {
        backdrop.style.backgroundImage = `url('${coverUrl}')`;
    }
    
    if (ratingEl) ratingEl.textContent = seriesData.rating || '9.5';
    if (statusEl) statusEl.textContent = seriesData.status || 'Ongoing';
    if (synopsisEl) synopsisEl.textContent = seriesData.desc || 'لا يوجد وصف متاح حالياً.';
    
    if (genresEl) {
        const genres = Array.isArray(seriesData.genres) ? seriesData.genres : (seriesData.genres || '').split(',');
        genresEl.innerHTML = genres.map(g => `<span class="genre-tag">${g.trim()}</span>`).join('');
    }
    
    // Populate chapters
    if (chaptersList && seriesData.chapters) {
        const sortedChs = [...seriesData.chapters].sort((a,b) => parseFloat(b.n) - parseFloat(a.n));
        chaptersList.innerHTML = sortedChs.map(ch => `
            <div class="chapter-row" onclick="window.openReader('${seriesData.title.replace(/'/g, "\\'")}', '${ch.n}')">
                <span class="ch-number">فصل ${ch.n}</span>
                <span class="ch-date">${ch.d || 'اليوم'}</span>
            </div>
        `).join('');
        
        if (startReadingBtn) {
            const firstCh = sortedChs[sortedChs.length - 1]; // First indexed chapter
            startReadingBtn.onclick = () => window.openReader(seriesData.title, firstCh ? firstCh.n : '1');
        }
    }
    
    modal.classList.add('active');

    // History Tracking and Bookmark logic setup
    const bookmarkBtn = document.getElementById('smBookmarkBtn');
    if (bookmarkBtn) {
        let bookmarks = JSON.parse(localStorage.getItem('nile_bookmarks')) || [];
        const isBookmarked = bookmarks.includes(seriesData.title);
        bookmarkBtn.innerHTML = isBookmarked ? '<i class="fas fa-bookmark"></i> في قائمتي' : '<i class="far fa-bookmark"></i> أضف لقائمتي';
        bookmarkBtn.onclick = () => {
            const nowBookmarked = toggleBookmark(seriesData.title);
            bookmarkBtn.innerHTML = nowBookmarked ? '<i class="fas fa-bookmark"></i> في قائمتي' : '<i class="far fa-bookmark"></i> أضف لقائمتي';
        };
    }
}

function toggleBookmark(title) {
    let bookmarks = JSON.parse(localStorage.getItem('nile_bookmarks')) || [];
    const index = bookmarks.indexOf(title);
    if (index > -1) {
        bookmarks.splice(index, 1);
    } else {
        bookmarks.push(title);
    }
    localStorage.setItem('nile_bookmarks', JSON.stringify(bookmarks));
    return bookmarks.includes(title);
}

function saveToHistory(title, chapter) {
    let history = JSON.parse(localStorage.getItem('nile_history')) || [];
    history = history.filter(item => item.title !== title);
    const seriesData = findSeriesBySlug(titleToSlug(title));
    history.unshift({
        title: title,
        chapter: chapter,
        img: seriesData ? (seriesData.item.img || seriesData.item.cover || 'images/default-cover.jpg') : 'images/default-cover.jpg',
        timestamp: Date.now()
    });
    if (history.length > 50) history.pop();
    localStorage.setItem('nile_history', JSON.stringify(history));
    if (typeof renderContinueReading === 'function') renderContinueReading();
}

// Close Modal logic
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('seriesModal');
    const closeBtn = document.getElementById('closeSeriesModal');
    const backdrop = document.getElementById('seriesModalBackdrop');
    
    if (closeBtn) closeBtn.onclick = () => modal.classList.remove('active');
    if (backdrop) backdrop.onclick = () => modal.classList.remove('active');
});

// Category Switching
function initCategoryTabs() {
    const tabs = document.querySelectorAll('.cat-nav-btn');
    if(tabs.length === 0) return;

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const btn = e.target.closest('.cat-nav-btn');
            tabs.forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            
            const category = btn.getAttribute('data-category');
            currentCategory = category;
            
            if(category === 'novels') {
                document.body.classList.add('novel-mode');
            } else {
                document.body.classList.remove('novel-mode');
            }
            
            renderHomeContent(category);
            
            const mainContentEl = document.querySelector('.asura-home');
            const topBarEl = document.querySelector('.top-horizontal-bar');
            if(mainContentEl) {
                mainContentEl.style.opacity = '0';
                if(topBarEl) topBarEl.style.opacity = '0';
                setTimeout(() => {
                    mainContentEl.style.opacity = '1';
                    if(topBarEl) topBarEl.style.opacity = '1';
                }, 100);
            }
        });
    });
}

// Global state for Latest Updates
let currentLatestCount = 4;
let cachedLatestData = [];

// Master Render
function renderHomeContent(category) {
    const data = SITE_DATA[category];
    if(!data) return;

    renderRandomHero(data.randomHero);
    renderPremiumCarousel(data.trending);
    renderTopSlider(data.topSlider);
    renderTrendingSlider(data.trending);
    
    currentLatestCount = 4;
    cachedLatestData = data.latest || [];
    renderLatestUpdates(cachedLatestData);
    
    // Logic for Other Works (Trending section replacement)
    renderOtherWorks(category);
    
    renderPopularSidebar(data.popular, data.randomRecs);
    renderContinueReading();
    renderCollections();
}

function renderOtherWorks(currentCat) {
    const categories = ['manhwa', 'manga', 'romance'];
    const otherCats = categories.filter(c => c !== currentCat);
    const randomCat = otherCats[Math.floor(Math.random() * otherCats.length)];
    const catNames = {manhwa: 'المنهوا', manga: 'المانجا', romance: 'الرومانسي'};
    
    const data = SITE_DATA[randomCat];
    if (data && data.trending) {
        renderTrendingSlider(data.trending);
        const header = document.querySelector('#trending .section-header h2');
        if (header) {
            header.innerHTML = `<i class="fas fa-random text-accent"></i> أعمال أخرى - ${catNames[randomCat] || randomCat}`;
        }
    }
}

// Render Random Hero
function renderRandomHero(heroData) {
    const container = document.getElementById('dynamicHeroContainer');
    if (!container || !heroData || heroData.length === 0) return;
    const item = heroData[0];
    
    // Clean up or omit the description if it is the generic placeholder or empty
    const isPlaceholder = !item.desc || item.desc.includes("اكتشف العناصر الحصرية والجديدة") || item.desc.trim() === "";
    const descriptionHTML = isPlaceholder ? "" : `<p class="hero-subtitle" style="font-size:1.05rem; color:#bbb; line-height:1.7; margin-bottom:2rem; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;">${item.desc}</p>`;

    container.innerHTML = `
        <div class="hero-blur-bg" style="position: absolute; inset: 0; z-index: 0; opacity: 1;">
            <img src="${item.img}" alt="Background" style="width: 100%; height: 100%; object-fit: cover; object-position: center 20%; filter: blur(30px) brightness(0.35) saturate(1.5) !important; transform: scale(1.1) !important;">
            <div style="position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.7) 40%, #0a0a0f 80%);"></div>
            <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 120px; background: linear-gradient(0deg, var(--bg-main) 0%, transparent 100%);"></div>
        </div>
        <div class="hero-content" style="position: relative; z-index: 2; width: 100%; padding: 0 5%; display: flex; align-items: center; justify-content: space-between; min-height: 420px; gap: 3rem;">
            <div class="hero-poster-side" style="flex: 0 0 240px; text-align: left; position: relative;">
                <img src="${item.img}" style="width:100%; height: 350px; object-fit: cover; border-radius:12px; box-shadow: 0 20px 50px rgba(0,0,0,0.9); border: 2px solid rgba(255,255,255,0.05); transform: perspective(800px) rotateY(-5deg); transition: transform 0.3s;" onmouseover="this.style.transform='perspective(800px) rotateY(0deg) scale(1.05)'" onmouseout="this.style.transform='perspective(800px) rotateY(-5deg)'">
            </div>
            <div class="hero-text-side" style="flex: 1; max-width: 650px; text-align: right;">
                <div style="display:inline-block; background:transparent; color: var(--accent-nile); font-weight:800; font-family:var(--font-ar); font-size:1rem; margin-bottom:0.8rem; letter-spacing: 1px;">أقوى الترشيحات <i class="fas fa-fire"></i></div>
                <h1 class="hero-title" style="font-size:3rem; font-weight: 900; line-height:1.2; margin-bottom:1rem; font-family: var(--font-en); color: #fff; text-shadow: 0 5px 20px rgba(0,0,0,0.8);">${item.title}</h1>
                <div style="margin-bottom: 1.2rem; color: #ccc; font-weight: 700; font-size: 0.95rem; display: flex; justify-content: flex-end; align-items: center; gap: 0.8rem;">
                    2026 <span style="color:#666;">|</span> ${item.genres.split(',').join(' <span style="color:#666;">·</span> ')}
                </div>
                ${descriptionHTML}
                <div class="hero-actions" style="display:flex; gap:1.5rem; justify-content: flex-end;">
                    <button onclick="goToSeries('${item.title.replace(/'/g, "\\'")}', '${currentCategory}')" style="background: rgba(255,255,255,0.15); color: #fff; padding: 0.7rem 1.8rem; border-radius: 4px; font-weight: 700; font-size: 1rem; border: none; cursor: pointer; display: flex; align-items: center; gap: 0.8rem; transition: background 0.2s; font-family: var(--font-ar);">
                        المزيد <i class="fas fa-info-circle"></i>
                    </button>
                    <button onclick="window.openReader('${item.title.replace(/'/g, "\\'")}', '${item.chapters && item.chapters[0] ? item.chapters[item.chapters.length-1].n : '1'}')" style="background: #ffffff; color: #000; padding: 0.7rem 2.5rem; border-radius: 4px; font-weight: 800; font-size: 1.1rem; border: none; cursor: pointer; display: flex; align-items: center; gap: 0.8rem; transition: transform 0.2s; font-family: var(--font-ar);">
                        قراءة <i class="fas fa-play" style="font-size: 0.8em;"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Render Top Bar
function renderTopSlider(data) {
    const container = document.getElementById('topSlider');
    if(!container) return;
    container.innerHTML = data.map(item => `
        <div class="mini-card ${currentCategory === 'novels' || document.body.classList.contains('novel-mode') ? 'novel-card' : ''}" onclick="goToSeries('${item.title.replace(/'/g, "\\'")}', '${currentCategory}')">
            <div class="mini-thumb"><img src="${item.img}" alt="cover" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.add('broken-img');"></div>
            <div class="mini-info">
                <div class="mini-title">${item.title}</div>
                <div class="mini-badge">${item.ch}</div>
            </div>
        </div>
    `).join('');
}

// Render Trending
function renderTrendingSlider(data) {
    const grid = document.getElementById('trendingGrid');
    if(!grid) return;
    grid.innerHTML = data.map(item => `
        <div class="trend-card ${document.body.classList.contains('novel-mode') ? 'novel-card' : ''}" onclick="goToSeries('${item.title.replace(/'/g, "\\'")}', '${currentCategory}')">
            <div class="trend-poster">
                <img src="${item.img}" alt="" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.add('broken-img'); this.parentElement.setAttribute('data-title', '${item.title}');">
                <div class="trend-overlay"></div>
                <div class="trend-rank">${item.rank}</div>
            </div>
            <div class="trend-info">
                <div class="trend-title">${item.title}</div>
                <div class="trend-meta">
                    <span class="stars"><i class="fas fa-star"></i> ${item.rating}</span>
                </div>
                <div class="trend-genres">${item.genres}</div>
            </div>
        </div>
    `).join('');

    // Rebind Scroll Buttons
    const prevBtn = document.getElementById('trendPrev');
    const nextBtn = document.getElementById('trendNext');
    if (prevBtn && nextBtn) {
        const newPrev = prevBtn.cloneNode(true);
        const newNext = nextBtn.cloneNode(true);
        prevBtn.parentNode.replaceChild(newPrev, prevBtn);
        nextBtn.parentNode.replaceChild(newNext, nextBtn);
        
        newPrev.addEventListener('click', () => { grid.scrollBy({ left: 300, behavior: 'smooth' }); });
        newNext.addEventListener('click', () => { grid.scrollBy({ left: -300, behavior: 'smooth' }); });
    }
}

// Time Ago Helper
function timeAgo(dateStr) {
    if (!dateStr || dateStr === 'اليوم') return 'اليوم';
    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        const diffWeeks = Math.floor(diffDays / 7);
        const diffMonths = Math.floor(diffDays / 30);
        if (diffMins < 1) return 'الآن';
        if (diffMins < 60) return `منذ ${diffMins} دقيقة`;
        if (diffHours < 24) return `منذ ${diffHours} ساعة`;
        if (diffDays === 1) return 'أمس';
        if (diffDays < 7) return `منذ ${diffDays} أيام`;
        if (diffWeeks < 5) return `منذ ${diffWeeks} أسبوع`;
        if (diffMonths < 12) return `منذ ${diffMonths} شهر`;
        return dateStr;
    } catch(e) { return dateStr; }
}

// Render Latest Updates (آخر الفصول - Vortex Scans Style)
function renderLatestUpdates(data) {
    const list = document.getElementById('latestUpdatesList');
    if(!list) return;
    
    const displayData = data.slice(0, currentLatestCount);
    
    list.innerHTML = displayData.map(item => {
        const ch = (item.chapters || []).slice(0, 3); 
        const chHTML = ch.map((c, i) => {
            const isNew = i === 0;
            const dateLabel = timeAgo(c.d);
            return `
                <div class="lc-ch-row" onclick="event.stopPropagation(); window.openReader('${item.title.replace(/'/g, "\\'")}', '${c.n}')">
                    ${isNew ? '<i class="fas fa-lock-open lc-ch-icon lc-new"></i>' : '<i class="fas fa-eye lc-ch-icon"></i>'}
                    <span class="lc-ch-name">Chapter ${c.n}</span>
                    <span class="lc-ch-date">${isNew ? '<span class="lc-new-badge">New</span>' : dateLabel}</span>
                </div>
            `;
        }).join('');

        // Determine type badge from DB
        let typeBadge = 'Manhwa';
        if (typeof DB !== 'undefined') {
            const dbEntry = DB.find(s => s.title === item.title);
            if (dbEntry) typeBadge = (dbEntry.type === 'manga') ? 'Manga' : 'Manhwa';
        }

        return `
            <div class="latest-card-v2" onclick="goToSeries('${item.title.replace(/'/g, "\\'")}', '${currentCategory}')">
                <div class="lc-cover">
                    <img src="${item.img || 'images/default-cover.jpg'}" alt="${item.title}" loading="lazy">
                    <span class="lc-type-badge">${typeBadge}</span>
                    <div class="lc-pinned"><i class="fas fa-fire"></i> Pinned</div>
                </div>
                <div class="lc-info">
                    <h3 class="lc-title">${item.title}</h3>
                    <div class="lc-meta">
                        <span class="lc-rating">${item.rating || '9.5'} <i class="fas fa-star"></i></span>
                        <span class="lc-status"><i class="fas fa-circle"></i> Ongoing</span>
                    </div>
                    <div class="lc-chapters">
                        ${chHTML}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    console.log('[Render] Latest updates rendered with', displayData.length, 'items');
}

// Render Popular Tabs
function renderPopularSidebar(dataBase, randomRecs) {
    const list = document.getElementById('popularList');
    const tabs = document.querySelectorAll('.pop-tab');
    if(!list || tabs.length === 0) return;

    function generateListHTML(data) {
        return data.map((item, idx) => `
            <div class="pop-item ${document.body.classList.contains('novel-mode') ? 'novel-card' : ''}" onclick="goToSeries('${item.title.replace(/'/g, "\\'")}', '${currentCategory}')">
                <div class="pop-rank">${idx + 1}</div>
                <div class="pop-thumb"><img src="${item.img}" alt="cover" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.add('broken-img');"></div>
                <div class="pop-info">
                    <div class="pop-title">${item.title}</div>
                    <div class="pop-genres">${item.genres}</div>
                    <div class="pop-rating"><i class="fas fa-star"></i> ${item.rating}</div>
                </div>
            </div>
        `).join('');
    }

    function renderPopularList(data) {
        // Only shuffle slightly to make tabs look a bit different
        const sortedData = [...data].sort((a,b) => Math.random() - 0.5);
        list.innerHTML = generateListHTML(sortedData);
    }

    renderPopularList(dataBase);

    // Render Random Recommendations List
    const randomRecsList = document.getElementById('randomRecsList');
    if (randomRecsList && randomRecs) {
        randomRecsList.innerHTML = generateListHTML(randomRecs);
    }

    const newTabs = [];
    tabs.forEach(tab => {
        const newTab = tab.cloneNode(true);
        tab.parentNode.replaceChild(newTab, tab);
        newTabs.push(newTab);
    });

    newTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            newTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderPopularList(dataBase);
        });
    });
}

// --- Pro Reader Engine ---
window.openReader = function(title = "العنوان", chapterStr = "الفصل") {
    // AUTH WALL: Check if user is logged in
    const user = JSON.parse(localStorage.getItem('nile_user'));
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    // Save to history
    saveToHistory(title, chapterStr);
    
    // URL State Persistence
    const slug = titleToSlug(title);
    const newUrl = `${window.location.pathname}?reader=true&title=${encodeURIComponent(slug)}&ch=${encodeURIComponent(chapterStr)}`;
    window.history.replaceState({reader: true, title: slug, ch: chapterStr}, '', newUrl);
    
    // Dynamic Page Title
    document.title = `Nexus | ${title} - الفصل ${chapterStr}`;
    
    let engine = document.getElementById('readerEngine');
    if(!engine) {
        initReaderEngine();
        engine = document.getElementById('readerEngine');
    }
    const titleEl = document.getElementById('readerMangaTitle');
    const chEl = document.getElementById('readerChapterNumber');
    const viewport = document.getElementById('readerViewport');
    
    if(!engine || !titleEl || !viewport) return;
    
    titleEl.textContent = title;
    if(chEl) chEl.textContent = `الفصل ${chapterStr}`;
    
    // Return-to-Series button
    const returnBtn = document.getElementById('returnToSeriesBtn');
    if (returnBtn) {
        returnBtn.onclick = () => {
            engine.classList.remove('active');
            document.body.style.overflow = 'auto';
            window.history.replaceState({}, '', window.location.pathname);
            document.title = 'Nexus | اقرأ أقوى المانها والمانجا';
            window.location.href = `series.html?title=${encodeURIComponent(slug)}`;
        };
    }
    
    // Find the real data
    const series = findSeriesBySlug(titleToSlug(title));
    let pagesHTML = '';
    
    if (series && series.item && series.item.chapters) {
        const chapter = series.item.chapters.find(c => c.n === chapterStr || c.n == chapterStr);
        if (chapter && chapter.pages && chapter.pages.length > 0) {
            pagesHTML = chapter.pages.map(p => `
                <img src="${p}" class="reader-image-page skeleton-img" loading="lazy" onload="this.classList.remove('skeleton-img');" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.remove('skeleton-img'); this.classList.add('broken-img');">
            `).join('');
        }
    }

    // Fallback if no pages found
    if (!pagesHTML) {
        pagesHTML = `
            <div style="padding: 100px 20px; text-align: center; color: #888;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem; color: var(--accent-nile);"></i>
                <p>محتوى هذا الفصل غير متوفر حالياً أو لم يتم سحبه بعد.</p>
            </div>
        `;
    }

    // Append Comments Section to Reader
    const readerIdentifier = `reader_${titleToSlug(title)}_${chapterStr}`;
    pagesHTML += `
        <div style="max-width: 800px; margin: 40px auto; padding: 20px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md);">
            <div id="readerCommentsContainer"></div>
        </div>
    `;

    viewport.innerHTML = pagesHTML;

    // Initialize comments after HTML is set
    setTimeout(() => initComments(readerIdentifier, 'readerCommentsContainer'), 100);
    
    // --- Navigation Logic ---
    const selector = document.getElementById('chapterSelector');
    const prevBtn = document.querySelector('.prev-chapter-btn');
    const nextBtn = document.querySelector('.next-chapter-btn');
    
    if (series && series.item && series.item.chapters && selector) {
        const chapters = [...series.item.chapters].sort((a,b) => parseFloat(b.n) - parseFloat(a.n));
        const currentIndex = chapters.findIndex(c => String(c.n) === String(chapterStr));
        
        selector.innerHTML = chapters.map(c => `
            <option value="${c.n}" ${String(c.n) === String(chapterStr) ? 'selected' : ''}>الفصل ${c.n}</option>
        `).join('');
        selector.disabled = false;
        selector.parentElement.style.opacity = '1';
        
        // Unbind and Rebind
        selector.onchange = (e) => window.openReader(title, e.target.value);
        
        const hasNewer = currentIndex > 0;
        const hasOlder = currentIndex < chapters.length - 1;
        
        if (prevBtn) {
            prevBtn.disabled = !hasOlder;
            prevBtn.onclick = () => { if(hasOlder) window.openReader(title, chapters[currentIndex + 1].n); };
        }
        if (nextBtn) {
            nextBtn.disabled = !hasNewer;
            nextBtn.onclick = () => { if(hasNewer) window.openReader(title, chapters[currentIndex - 1].n); };
        }
    }
    
    // Reset Progress
    const fill = document.getElementById('readerProgressFill');
    if(fill) fill.style.width = '0%';
    viewport.scrollTop = 0;
    viewport.scrollLeft = 0;
    
    engine.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // CRITICAL: Hide global scroll-to-top button while reader is active
    const topBtn = document.getElementById('scrollToTopBtn');
    if(topBtn) topBtn.style.display = 'none';

    // Load Persistent Settings
    applyReaderSettings();
};

function applyReaderSettings() {
    const viewport = document.getElementById('readerViewport');
    if(!viewport) return;

    const settings = {
        brightness: localStorage.getItem('nile_bri') || '100',
        contWidth: localStorage.getItem('nile_contw') || '800',
        imgWidth: localStorage.getItem('nile_imgw') || '100',
        gap: localStorage.getItem('nile_gap') || '0',
        mode: localStorage.getItem('nile_mode') || 'rm-longstrip'
    };

    // Apply to UI
    viewport.style.filter = `brightness(${settings.brightness}%)`;
    const wrapper = viewport.firstElementChild;
    if(wrapper) wrapper.style.maxWidth = settings.contWidth + 'px';
    
    const images = viewport.querySelectorAll('.reader-image-page');
    images.forEach(img => {
        img.style.width = settings.imgWidth + '%';
        img.style.marginBottom = settings.gap + 'px';
    });

    viewport.classList.remove('rm-longstrip', 'rm-single', 'rm-double');
    viewport.classList.add(settings.mode);

    // Update Sliders if active
    const slips = {
        bri: document.getElementById('slipBri'),
        contw: document.getElementById('slipContW'),
        imgw: document.getElementById('slipImgW'),
        gap: document.getElementById('slipGap')
    };
    if(slips.bri) slips.bri.value = settings.brightness;
    if(slips.contw) slips.contw.value = settings.contWidth;
    if(slips.imgw) slips.imgw.value = settings.imgWidth;
    if(slips.gap) slips.gap.value = settings.gap;

    const vals = {
        bri: document.getElementById('valBri'),
        contw: document.getElementById('valContW'),
        imgw: document.getElementById('valImgW'),
        gap: document.getElementById('valGap')
    };
    if(vals.bri) vals.bri.textContent = settings.brightness + '%';
    if(vals.contw) vals.contw.textContent = settings.contWidth + 'px';
    if(vals.imgw) vals.imgw.textContent = settings.imgWidth + '%';
    if(vals.gap) vals.gap.textContent = settings.gap + 'px';

    // Update Mode Buttons
    const modeBtns = {
        'rm-longstrip': document.getElementById('modeLongStrip'),
        'rm-single': document.getElementById('modeSingle'),
        'rm-double': document.getElementById('modeDouble')
    };
    Object.keys(modeBtns).forEach(k => {
        if(modeBtns[k]) modeBtns[k].classList.toggle('active', k === settings.mode);
    });
}

function initReaderEngine() {
    if(!document.getElementById('readerEngine')) {
        const readerHtml = `
        <div class="reader-engine" id="readerEngine">
            <style>
                .reader-hud { transition: transform 0.3s ease, opacity 0.3s ease; }
                .reader-hud-top.hidden { transform: translateY(-100%); opacity: 0; pointer-events: none; }
                .reader-hud-bottom.hidden { transform: translateY(100%); opacity: 0; pointer-events: none; }
                .reader-settings-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(5px); z-index: 10001; display: none; align-items: center; justify-content: center; opacity: 0; transition: 0.2s; }
                .reader-settings-overlay.active { display: flex; opacity: 1; }
                .pro-settings-panel { background: #111112; border: 1px solid #2a2a2a; border-radius: 12px; padding: 25px; color: #ccc; font-family: inherit; width: 750px; max-width: 95vw; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
                
                /* Reading Mode Styles */
                .reader-viewport { display: flex; align-items: center; overflow-y: auto; overflow-x: hidden; scroll-behavior: smooth; }
                .reader-viewport.rm-longstrip { flex-direction: column; }
                .reader-viewport.rm-single { flex-direction: column; scroll-snap-type: y mandatory; }
                .reader-viewport.rm-single .reader-image-page { height: 100vh !important; width: 100% !important; object-fit: contain; scroll-snap-align: start; margin-bottom: 0 !important; }
                .reader-viewport.rm-double { flex-direction: row; flex-wrap: wrap; justify-content: center; direction: rtl; align-items: flex-start; }
                .reader-viewport.rm-double .reader-image-page { width: 50% !important; height: 100vh !important; object-fit: contain; margin-bottom: 0 !important; border: 1px solid #000; box-sizing: border-box; }
                @media (max-width: 768px) { .reader-viewport.rm-double .reader-image-page { width: 100% !important; } }

                .pro-settings-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #222; padding-bottom: 15px; margin-bottom: 25px; }
                .pro-settings-header h3 { font-size: 1.1rem; color: #fff; margin:0; font-weight: 600; display: flex; align-items: center; gap: 10px; }
                .pro-settings-header .close-pro { background: transparent; color: #888; border: none; font-size: 1.2rem; cursor: pointer; transition: 0.3s; }
                .pro-settings-header .close-pro:hover { color: #fff; }
                .pro-settings-body { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
                @media (max-width: 700px) { .pro-settings-body { grid-template-columns: 1fr; gap: 20px; } }
                .pro-slider-group { margin-bottom: 25px; }
                .pro-slider-label { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; margin-bottom: 12px; color: #bbb; }
                .pro-slider-label span:first-child i { margin-left: 8px; font-size: 1rem; color: #666; }
                .pro-slider-val { background: #1e1e1e; padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 0.8rem; font-weight: 600; min-width: 50px; text-align: center; }
                .pro-range { width: 100%; appearance: none; height: 4px; border-radius: 2px; background: #333; outline: none; margin:0; }
                .pro-range::-webkit-slider-thumb { appearance: none; width: 18px; height: 18px; border-radius: 50%; background: #fff; cursor: pointer; box-shadow: 0 0 5px rgba(0,0,0,0.5); transition: 0.2s; }
                .pro-range::-webkit-slider-thumb:hover { transform: scale(1.2); }
                .pro-mode-group h5 { color: #aaa; font-size: 0.9rem; margin: 0 0 15px 0; font-weight: normal; }
                .pro-modes { display: flex; gap: 10px; }
                .pro-mode-btn { flex: 1; background: #18181A; display:flex; flex-direction: column; align-items:center; justify-content:center; padding: 15px 5px; border: 1px solid #2a2a2a; border-radius: 8px; cursor: pointer; color: #888; transition: 0.2s; font-size: 0.85rem; font-family: inherit; font-weight: 600; }
                .pro-mode-btn i { font-size: 1.5rem; margin-bottom: 8px; font-weight: 300; }
                .pro-mode-btn:hover { background: #222; color: #ddd; }
                .pro-mode-btn.active { background: rgba(59, 130, 246, 0.1); border-color: #3b82f6; color: #3b82f6; }
            </style>
            <div class="reader-hud reader-hud-top" id="readerHudTop">
                <button class="hud-btn" id="settingsBtn" title="الإعدادات"><i class="fas fa-cog"></i></button>
                <div class="reader-title-info" style="text-align: center;">
                    <h3 id="readerMangaTitle">العنوان</h3>
                    <p id="readerChapterNumber" class="text-accent">الفصل</p>
                </div>
                <button class="hud-btn" id="closeReader" title="العودة"><i class="fas fa-times"></i></button>
            </div>

            <div class="reader-settings-overlay" id="readerSettingsPanel">
                <div class="pro-settings-panel">
                    <div class="pro-settings-header">
                        <h3><i class="fas fa-sliders-h"></i> إعدادات القراءة</h3>
                        <button class="close-pro" id="closeSettingsBtn"><i class="fas fa-times"></i></button>
                    </div>
                    <div class="pro-settings-body">
                        <!-- Right column (in RTL): Sliders -->
                        <div class="pro-sliders">
                            <div class="pro-slider-group">
                                <div class="pro-slider-label"><span><i class="fas fa-desktop"></i> عرض حاوية القراءة</span><span class="pro-slider-val" id="valContW">800px</span></div>
                                <input type="range" class="pro-range" id="slipContW" min="500" max="1200" value="800" step="50">
                            </div>
                            <div class="pro-slider-group">
                                <div class="pro-slider-label"><span><i class="fas fa-expand-arrows-alt"></i> عرض الصورة</span><span class="pro-slider-val" id="valImgW">100%</span></div>
                                <input type="range" class="pro-range" id="slipImgW" min="40" max="100" value="100" step="1">
                            </div>
                            <div class="pro-slider-group">
                                <div class="pro-slider-label"><span><i class="far fa-sun"></i> السطوع</span><span class="pro-slider-val" id="valBri">100%</span></div>
                                <input type="range" class="pro-range" id="slipBri" min="30" max="100" value="100" step="1">
                            </div>
                            <div class="pro-slider-group">
                                <div class="pro-slider-label"><span><i class="fas fa-grip-lines"></i> الفراغ بين الصور</span><span class="pro-slider-val" id="valGap">0px</span></div>
                                <input type="range" class="pro-range" id="slipGap" min="0" max="50" value="0" step="5">
                            </div>
                        </div>
                        <!-- Left column (in RTL): Modes -->
                        <div class="pro-modes-container">
                            <div class="pro-mode-group">
                                <h5>وضع القراءة (Reading Mode)</h5>
                                <div class="pro-modes">
                                    <button class="pro-mode-btn active" id="modeLongStrip"><i class="fas fa-list"></i> شريط طولي</button>
                                    <button class="pro-mode-btn" id="modeSingle"><i class="far fa-square"></i> مفردة</button>
                                    <button class="pro-mode-btn" id="modeDouble"><i class="fas fa-book-open"></i> مزدوجة</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="reader-progress-wrapper" id="readerProgressWrapper">
                <div class="reader-progress-fill" id="readerProgressFill"></div>
            </div>
            <div class="reader-viewport rm-longstrip" id="readerViewport"></div>
            
            <div class="reader-hud reader-hud-bottom" id="readerHudBottom">
                <button class="hud-btn next-chapter-btn"><i class="fas fa-step-forward"></i> التالي</button>
                <div class="chapter-selector-wrapper">
                    <select class="chapter-selector" id="chapterSelector" disabled><option>الفصل الحالي</option></select>
                    <i class="fas fa-chevron-up select-icon"></i>
                </div>
                <button class="hud-btn prev-chapter-btn">السابق <i class="fas fa-step-backward"></i></button>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', readerHtml);
    }

    const engine = document.getElementById('readerEngine');
    if(!engine) return;

    const closeBtn = document.getElementById('closeReader');
    if(closeBtn) {
        closeBtn.replaceWith(closeBtn.cloneNode(true));
        document.getElementById('closeReader').addEventListener('click', () => {
            engine.classList.remove('active');
            document.body.style.overflow = 'auto'; 
            
            // Clear URL state
            window.history.replaceState({}, '', window.location.pathname);
            document.title = 'Nexus | اقرأ أقوى المانها والمانجا';
            
            // Restore scroll button when reader closes
            const topBtn = document.getElementById('scrollToTopBtn');
            if(topBtn) topBtn.style.display = 'flex';
        });
    }

    const viewport = document.getElementById('readerViewport');
    if(viewport) {
        if (!viewport.dataset.clickBound) {
            viewport.dataset.clickBound = 'true';
            viewport.addEventListener('click', (e) => {
                if (e.target.closest('.hud-btn, .reader-settings-panel, .chapter-selector-wrapper')) return;
                
                const head = document.getElementById('readerHudTop');
                const foot = document.getElementById('readerHudBottom');
                const settingsPanel = document.getElementById('readerSettingsPanel');
                const progressBar = document.getElementById('readerProgressWrapper');
                
                if(head) head.classList.toggle('hidden');
                if(foot) foot.classList.toggle('hidden');
                if(progressBar) progressBar.classList.toggle('hidden');
                
                if (settingsPanel && head && head.classList.contains('hidden')) {
                    settingsPanel.classList.remove('active');
                }
            });
        }
    }

    if(viewport) {
        const fill = document.getElementById('readerProgressFill');
        viewport.addEventListener('scroll', () => {
            const maxScroll = viewport.scrollHeight - viewport.clientHeight;
            const perc = maxScroll > 0 ? (viewport.scrollTop / maxScroll) * 100 : 0;
            fill.style.width = perc + '%';
        });
    }

    const settingsBtn = document.getElementById('settingsBtn');
    const settingsPanel = document.getElementById('readerSettingsPanel');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    if(settingsBtn && settingsPanel) {
        settingsBtn.replaceWith(settingsBtn.cloneNode(true));
        document.getElementById('settingsBtn').addEventListener('click', () => {
            settingsPanel.classList.toggle('active');
        });
        if(closeSettingsBtn) {
            closeSettingsBtn.addEventListener('click', () => {
                settingsPanel.classList.remove('active');
            });
        }
        // Click outside to close
        settingsPanel.addEventListener('click', (e) => {
            if(e.target === settingsPanel) {
                settingsPanel.classList.remove('active');
            }
        });
    }

    // Logic for Pro Sliders
    const slipContW = document.getElementById('slipContW');
    if(slipContW) {
        slipContW.addEventListener('input', (e) => {
            const val = e.target.value;
            localStorage.setItem('nile_contw', val);
            applyReaderSettings();
        });
    }

    const slipImgW = document.getElementById('slipImgW');
    if(slipImgW) {
        slipImgW.addEventListener('input', (e) => {
            const val = e.target.value;
            localStorage.setItem('nile_imgw', val);
            applyReaderSettings();
        });
    }

    const slipBri = document.getElementById('slipBri');
    if(slipBri) {
        slipBri.addEventListener('input', (e) => {
            const val = e.target.value;
            localStorage.setItem('nile_bri', val);
            applyReaderSettings();
        });
    }

    const slipGap = document.getElementById('slipGap');
    if(slipGap) {
        slipGap.addEventListener('input', (e) => {
            const val = e.target.value;
            localStorage.setItem('nile_gap', val);
            applyReaderSettings();
        });
        
        // Ensure gap is applied to dynamic pages
        const observer = new MutationObserver(() => {
            applyReaderSettings();
        });
        observer.observe(viewport, {childList: true, subtree: true});
    }

    // Logic for Reading Modes
    const modeLongStrip = document.getElementById('modeLongStrip');
    const modeSingle = document.getElementById('modeSingle');
    const modeDouble = document.getElementById('modeDouble');
    
    if(modeLongStrip) modeLongStrip.addEventListener('click', () => {
        localStorage.setItem('nile_mode', 'rm-longstrip');
        applyReaderSettings();
    });
    if(modeSingle) modeSingle.addEventListener('click', () => {
        localStorage.setItem('nile_mode', 'rm-single');
        applyReaderSettings();
    });
    if(modeDouble) modeDouble.addEventListener('click', () => {
        localStorage.setItem('nile_mode', 'rm-double');
        applyReaderSettings();
    });
}

// --- Premium Coverflow Carousel Logic (Infinite Loop) ---
function renderPremiumCarousel(data) {
    const track = document.getElementById('premiumCarouselTrack');
    if(!track) return;
    
    // Triple the data for seamless infinite scrolling
    const richData = [...data, ...data, ...data, ...data, ...data];
    
    track.innerHTML = richData.map(item => `
        <div class="premium-card ${document.body.classList.contains('novel-mode') ? 'novel-card' : ''}" onclick="goToSeries('${item.title.replace(/'/g, "\\'")}', '${currentCategory}')">
                <img src="${item.img}" alt="" class="media-poster-img" loading="lazy" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.add('broken-img'); this.parentElement.setAttribute('data-title', '${item.title}');">
            <div class="premium-rating"><i class="fas fa-star"></i> ${item.rating}</div>
            <div class="premium-title">${item.title}</div>
        </div>
    `).join('');
    
    // Start at the middle set so we can scroll in both directions
    requestAnimationFrame(() => {
        const oneSetWidth = track.scrollWidth / 5;
        track.scrollLeft = oneSetWidth * 2;
    });
}

let premiumAutoplayInterval;
let isAutoplayPaused = false;

function initPremiumCarouselAutoplay() {
    const track = document.getElementById('premiumCarouselTrack');
    const toggleBtn = document.getElementById('toggleAutoplayBtn');
    if(!track || !toggleBtn) return;
    
    const oneSetWidth = track.scrollWidth / 5;
    
    // Seamless infinite loop: when scroll reaches edges, jump to middle silently
    track.addEventListener('scroll', () => {
        if (track.scrollLeft <= 10) {
            track.scrollLeft += oneSetWidth * 2;
        } else if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 10) {
            track.scrollLeft -= oneSetWidth * 2;
        }
    });
    
    function startAutoplay() {
        if (premiumAutoplayInterval) clearInterval(premiumAutoplayInterval);
        premiumAutoplayInterval = setInterval(() => {
            if (!isAutoplayPaused && track) {
                track.scrollBy({ left: 162, behavior: 'smooth' });
            }
        }, 3000);
    }
    
    startAutoplay();
    
    track.addEventListener('mouseenter', () => isAutoplayPaused = true);
    track.addEventListener('mouseleave', () => {
        if (!toggleBtn.classList.contains('stopped')) isAutoplayPaused = false;
    });
    
    const newBtn = toggleBtn.cloneNode(true);
    toggleBtn.parentNode.replaceChild(newBtn, toggleBtn);
    
    newBtn.addEventListener('click', () => {
        newBtn.classList.toggle('stopped');
        if (newBtn.classList.contains('stopped')) {
            isAutoplayPaused = true;
            clearInterval(premiumAutoplayInterval);
            newBtn.innerHTML = '<i class="fas fa-play"></i> استئناف التمرير';
            newBtn.classList.replace('btn-secondary', 'btn-primary');
        } else {
            isAutoplayPaused = false;
            startAutoplay();
            newBtn.innerHTML = '<i class="fas fa-pause"></i> إيقاف التمرير الآلي';
            newBtn.classList.replace('btn-primary', 'btn-secondary');
        }
    });
}

/* =========================================================
   Local Comments System (Dynamic & Reusable)
   ========================================================= */
function initComments(identifier, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div style="text-align: center; margin-bottom: 1rem;">
            <i class="fas fa-comments text-accent" style="font-size: 2rem;"></i>
            <h3 style="color: #fff; margin-top: 10px;">شارك برأيك في هذا الفصل</h3>
        </div>
        <div id="disqus_thread"></div>
    `;
    
    // Shortname user can configure later. Defaulting to a placeholder.
    const disqus_shortname = 'nexus-scans-demo'; 
    const pageUrl = window.location.origin + window.location.pathname + '#' + identifier;

    if (window.DISQUS) {
        window.DISQUS.reset({
            reload: true,
            config: function () {
                this.page.identifier = identifier;
                this.page.url = pageUrl;
            }
        });
    } else {
        window.disqus_config = function () {
            this.page.identifier = identifier;
            this.page.url = pageUrl;
        };
        const d = document, s = d.createElement('script');
        s.src = 'https://' + disqus_shortname + '.disqus.com/embed.js';
        s.setAttribute('data-timestamp', +new Date());
        (d.head || d.body).appendChild(s);
    }
}

/* =========================================================
   Authentication System (Local Storage Simulation)
   ========================================================= */
document.addEventListener('DOMContentLoaded', () => {
    initAuthSystem();
});

function initAuthSystem() {
    // Redirection Logic replaces the modal injection
    const bindLoginButtons = () => {
        document.querySelectorAll('.btn-login').forEach(btn => {
            btn.removeEventListener('click', openModalHandler);
            btn.addEventListener('click', openModalHandler);
        });
    };
    
    const openModalHandler = (e) => {
        e.preventDefault();
        window.location.href = 'login.html';
    };

    // Clean up: Removed old modal event listeners

    // 3. Render Navbar state based on Auth
    const renderNavAuth = () => {
        const user = JSON.parse(localStorage.getItem('nile_user'));
        const navActionsList = document.querySelectorAll('.nav-actions');
        
        navActionsList.forEach(navActions => {
            const oldLogin = navActions.querySelector('.btn-login');
            const oldProfile = navActions.querySelector('.nav-user');
            if (oldLogin) oldLogin.remove();
            if (oldProfile) oldProfile.remove();
            if (user) {
                // User Logged In - Premium Vortex Style Dropdown
                const searchBar = navActions.querySelector('.nav-search-bar');
                const userHtml = `
                    <div class="nav-user">
                        <img src="${user.avatar}" class="nu-avatar" alt="Avatar">
                        <div class="nu-name">${user.name}</div>
                        <i class="fas fa-chevron-down nu-chevron"></i>
                        
                        <div class="nu-dropdown">
                            <!-- Dropdown Header -->
                            <div class="nud-header">
                                <div class="nud-user-info">
                                    <img src="${user.avatar}" alt="Avatar">
                                    <div class="nud-text">
                                        <div class="nud-name">${user.name} <span class="nud-badge">User</span></div>
                                        <div class="nud-handle">@${user.name.toLowerCase().replace(/\s/g, '_')}_nile</div>
                                        <div class="nud-email">${user.email}</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Coins Section -->
                            <div class="nud-coins">
                                <div class="nud-coin-text">
                                    <i class="fas fa-coins"></i>
                                    <span>Coins</span>
                                </div>
                                <div class="nud-coin-val">
                                    <img src="https://api.dicebear.com/7.x/icons/svg?seed=gold" alt="coin" style="width:14px; height:14px; margin-left:5px;">
                                    <span id="navCoinBalance">0</span>
                                </div>
                            </div>

                            <!-- Menu Items -->
                            <div class="nud-menu">
                                <a href="profile.html" class="nud-item">
                                    <i class="fas fa-user-alt"></i>
                                    <span>View Profile</span>
                                </a>
                                <a href="profile.html?tab=bookmarks" class="nud-item">
                                    <i class="fas fa-bookmark"></i>
                                    <span>My Bookmarks</span>
                                </a>
                                <a href="profile.html?tab=reports" class="nud-item">
                                    <i class="fas fa-flag"></i>
                                    <span>My Reports</span>
                                </a>
                                <div class="nud-divider"></div>
                                <a href="#" class="nud-item">
                                    <i class="fas fa-question-circle"></i>
                                    <span>Help & Support</span>
                                </a>
                                <button class="nud-item logout-btn logout">
                                    <i class="fas fa-sign-out-alt"></i>
                                    <span>Log Out</span>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                if(searchBar) {
                    searchBar.insertAdjacentHTML('afterend', userHtml);
                } else {
                    navActions.insertAdjacentHTML('afterbegin', userHtml);
                }
                
                // Bind Logout
                const logoutBtns = navActions.querySelectorAll('.logout');
                logoutBtns.forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        localStorage.removeItem('nile_user');
                        renderNavAuth();
                    });
                });
            } else {
                // User Logged Out - Show standard login button
                const searchBar = navActions.querySelector('.nav-search-bar');
                const btnHtml = `
                    <button class="btn btn-login btn-sm">
                        <i class="fas fa-sign-in-alt"></i> تسجيل الدخول
                    </button>
                `;
                if(searchBar) {
                    searchBar.insertAdjacentHTML('afterend', btnHtml);
                } else {
                    navActions.insertAdjacentHTML('afterbegin', btnHtml);
                }
                bindLoginButtons();
            }
        });
    };
    
    // Global Helper to refresh balance display
    window.refreshNavBalance = () => {
        const coins = localStorage.getItem('nile_coins') || '0';
        const el = document.getElementById('navCoinBalance');
        if(el) el.textContent = coins;
    };

    // Call render once at start
    renderNavAuth();
    window.refreshNavBalance();
}

/** 
 * SHOP LOGIC HELPERS 
 **/
function applyPurchasedDecorations() {
    const activeDeco = localStorage.getItem('nile_active_decoration');
    if(!activeDeco) return;
    
    // Apply to user avatar in nav if present
    const navAvatars = document.querySelectorAll('.nu-avatar, .nud-user-info img');
    navAvatars.forEach(av => {
        const parent = av.parentElement;
        if(!parent.classList.contains('deco-parent')) {
            parent.classList.add('deco-parent');
            const overlay = document.createElement('div');
            overlay.className = `deco-overlay ${activeDeco}`;
            parent.appendChild(overlay);
        }
    });

    // Apply to all manhwa covers globally
    const covers = document.querySelectorAll('.vortex-thumb, .trend-poster, .lu-cover, .hc-thumb');
    covers.forEach(cov => {
        if(!cov.querySelector('.deco-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = `deco-overlay ${activeDeco}`;
            cov.appendChild(overlay);
        }
    });
}
// Run application on load and interval
setInterval(applyPurchasedDecorations, 2000);

/* =========================================================
   Mobile Menu & Global Interactions
   ========================================================= */
function initMobileMenu() {
    const toggle = document.getElementById('menuToggle');
    const nav = document.getElementById('navLinks');
    if (!toggle || !nav) return;

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        nav.classList.toggle('active');
        toggle.querySelector('i').classList.toggle('fa-bars');
        toggle.querySelector('i').classList.toggle('fa-times');
    });

    document.addEventListener('click', (e) => {
        if (!nav.contains(e.target) && !toggle.contains(e.target)) {
            nav.classList.remove('active');
            toggle.querySelector('i').classList.add('fa-bars');
            toggle.querySelector('i').classList.remove('fa-times');
        }
    });
}

function initSearchOverlay() {
    const overlay = document.getElementById('searchOverlay');
    const openBtn = document.getElementById('mobileSearchBtn');
    const closeBtn = document.getElementById('closeSearch');
    const input = document.getElementById('searchInput');

    if (!overlay || !openBtn || !closeBtn) return;

    openBtn.addEventListener('click', () => {
        overlay.classList.add('active');
        setTimeout(() => input.focus(), 300);
    });

    closeBtn.addEventListener('click', () => {
        overlay.classList.remove('active');
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
    });

    // Handle ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            overlay.classList.remove('active');
            const nav = document.getElementById('navLinks');
            if(nav) nav.classList.remove('active');
        }
    });

    // Simple search redirect logic for demo
    if(input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                window.location.href = `browse.html?search=${encodeURIComponent(input.value.trim())}`;
            }
        });
    }
}

// REMOVED DUPLICATE OPENREADER

// =========================================================
// Nexus API INTEGRATION
// Connects to Python Backend (localhost:3000)
// =========================================================

// Fetch chapters from API
async function loadChaptersFromAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/chapters`);
        const data = await response.json();
        
        if (data.success && data.data.series) {
            displayAPIChapters(data.data.series);
            updateAPIStats(data.data);
        }
    } catch (error) {
        console.log('[API] Not connected or no chapters yet');
    }
}

// Display chapters in Latest Updates section
function displayAPIChapters(series) {
    const container = document.getElementById('latestUpdatesList');
    
    if (!container || !series || series.length === 0) {
        console.log('[API] No container or no series data');
        return;
    }
    
    console.log('[API] Displaying', series.length, 'series');
    
    // Convert API data to card HTML matching the website's style
    let html = '';
    series.forEach(s => {
        if (s.chapters && s.chapters.length > 0) {
            // Sort chapters by number descending
            const sortedChapters = s.chapters.sort((a, b) => b.number - a.number);
            const latestChapter = sortedChapters[0];
            
            html += `
                <div class="latest-row" onclick="openSeriesFromAPI('${s.id}', '${s.title.replace(/'/g, "\\'")}')">
                    <div class="latest-thumb">
                        <img src="${s.cover || 'images/default-cover.jpg'}" alt="${s.title}" loading="lazy">
                    </div>
                    <div class="latest-info">
                        <h4 class="latest-title">${s.title}</h4>
                        <div class="latest-chapter">فصل ${latestChapter.number}${latestChapter.status === 'new' ? ' <span class="new-badge">جديد</span>' : ''}</div>
                        <div class="latest-meta">
                            <span class="latest-time">${latestChapter.pages} صفحة</span>
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    if (html) {
        container.innerHTML = html;
        console.log('[API] Chapters displayed successfully');
    }
}

// Update statistics from API
function updateAPIStats(data) {
    // You can add stat elements to your HTML and update them here
    console.log('[API] Total chapters:', data.totalChapters);
    console.log('[API] New chapters:', data.newChapters);
}

// Open series from API data
function openSeriesFromAPI(seriesId, title) {
    // Find series data
    fetch(`${API_BASE_URL}/series/${seriesId}/chapters`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Populate modal with API data
                populateSeriesModal(data.data);
            }
        })
        .catch(err => console.error('[API] Error loading series:', err));
}

// Removed duplicate populateSeriesModal

// --- Continue Reading & Collections ---
function renderContinueReading() {
    const history = JSON.parse(localStorage.getItem('nile_history')) || [];
    const container = document.getElementById('continueReadingGrid');
    const section = document.getElementById('continueReadingSection');
    
    if (!container || !section) return;
    
    if (history.length === 0) {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    container.innerHTML = history.slice(0, 10).map(item => {
        let cover = '';
        if (item.img && item.img !== 'undefined' && item.img !== 'null' && !item.img.includes('placeholder')) {
            cover = item.img;
        }
        
        let totalCh = 0;
        if (typeof DB !== 'undefined') {
            const dbEntry = DB.find(s => s.title === item.title) || DB.find(s => titleToSlug(s.title) === titleToSlug(item.title));
            if (dbEntry && dbEntry.cover) {
                cover = dbEntry.cover;
            }
            if (dbEntry && dbEntry.chapters) {
                totalCh = dbEntry.chapters.length;
            }
        }
        
        if (!cover || cover === 'images/default-cover.jpg') {
            cover = 'images/default-cover.jpg';
        }
        
        // Calculate read percentage
        const currentCh = parseFloat(item.chapter) || 0;
        const readPercent = totalCh > 0 ? Math.min(Math.round((currentCh / totalCh) * 100), 100) : 0;
        const leftCh = totalCh > 0 ? Math.max(totalCh - currentCh, 0) : 0;
        const relTime = timeAgo(new Date(item.timestamp).toISOString().split('T')[0]);
        
        return `
        <div class="continue-card" onclick="window.openReader('${item.title.replace(/'/g, "\\'")}', '${item.chapter}')">
            <div class="continue-thumb">
                <img src="${cover}" alt="${item.title}" onerror="this.src='images/default-cover.jpg';">
                <div class="continue-play"><i class="fas fa-play"></i></div>
                <div class="cr-ch-overlay">
                    <span class="cr-ch-current">Chapter ${item.chapter}</span>
                    ${totalCh > 0 ? `<span class="cr-ch-total">/ ${totalCh}</span>` : ''}
                </div>
            </div>
            <div class="continue-info">
                <div class="continue-title">${item.title}</div>
                <div class="continue-ch"><i class="fas fa-clock"></i> Chapter ${item.chapter} · ${relTime}</div>
            </div>
            ${totalCh > 0 ? `
            <div class="cr-left-info">
                <span>${currentCh} / ${totalCh} (${leftCh} left)</span>
                <span class="cr-percent">${readPercent}%</span>
            </div>` : ''}
            <div class="continue-progress"><div class="progress-bar" style="width: ${readPercent || 5}%;"></div></div>
        </div>
    `}).join('');
}

function renderCollections() {
    const container = document.getElementById('collectionsGrid');
    if (!container) return;
    
    const collections = [
        { title: 'عالم السحر والتعاويذ', icon: 'fa-hat-wizard', color: '#9d50bb', genre: 'fantasy' },
        { title: 'عوالم البوابات والنظام', icon: 'fa-dungeon', color: '#00d4ff', genre: 'action' },
        { title: 'التناسخ والعودة بالزمن', icon: 'fa-history', color: '#f7971e', genre: 'isekai' },
        { title: 'قوة خارقة وفنون قتالية', icon: 'fa-fist-raised', color: '#ff4b2b', genre: 'martial-arts' },
        { title: 'قصص رومانسية', icon: 'fa-heart', color: '#ff69b4', genre: 'romance' }
    ];
    
    container.innerHTML = collections.map(col => `
        <a href="browse.html?genre=${col.genre}" class="collection-card" style="--col-color: ${col.color}">
            <div class="collection-icon"><i class="fas ${col.icon}"></i></div>
            <div class="collection-text">
                <span class="col-en">${col.title}</span>
            </div>
        </a>
    `).join('');
}

// Expose API functions globally
window.NileAPI = {
    loadChapters: loadChaptersFromAPI,
    openSeries: openSeriesFromAPI,
    baseURL: API_BASE_URL
};

/* =========================================================
   Premium Theme System - 10 Themes
   ========================================================= */
const NEXUS_THEMES = [
    { id: '', label: 'Nexus Default', labelAr: 'النيكسس الافتراضي', color: '#00FF9F' },
    { id: 'theme-midnight-blue', label: 'Midnight Blue', labelAr: 'أزرق منتصف الليل', color: '#3b82f6' },
    { id: 'theme-crimson-red', label: 'Crimson Red', labelAr: 'أحمر قرمزي', color: '#ef4444' },
    { id: 'theme-royal-purple', label: 'Royal Purple', labelAr: 'بنفسجي ملكي', color: '#a855f7' },
    { id: 'theme-ocean-teal', label: 'Ocean Teal', labelAr: 'أخضر محيطي', color: '#14b8a6' },
    { id: 'theme-sunset-orange', label: 'Sunset Orange', labelAr: 'برتقالي الغروب', color: '#f97316' },
    { id: 'theme-sakura-pink', label: 'Sakura Pink', labelAr: 'وردي ساكورا', color: '#ec4899' },
    { id: 'theme-emerald-forest', label: 'Emerald Forest', labelAr: 'زمردي الغابة', color: '#10b981' },
    { id: 'theme-golden-hour', label: 'Golden Hour', labelAr: 'الساعة الذهبية', color: '#eab308' },
    { id: 'theme-arctic-ice', label: 'Arctic Ice', labelAr: 'جليد القطب', color: '#06b6d4' }
];

function initThemeSystem() {
    // Load saved theme
    const savedTheme = localStorage.getItem('nexus_theme') || '';
    applyTheme(savedTheme);

    // Inject FAB Button
    const fab = document.createElement('button');
    fab.className = 'theme-fab';
    fab.id = 'themeFab';
    fab.innerHTML = '<i class="fas fa-palette"></i>';
    fab.title = 'تغيير الثيم';
    document.body.appendChild(fab);

    // Inject Panel Overlay
    const overlay = document.createElement('div');
    overlay.className = 'theme-panel-overlay';
    overlay.id = 'themePanelOverlay';
    overlay.innerHTML = `
        <div class="theme-panel">
            <div class="theme-panel-header">
                <h3><i class="fas fa-palette"></i> اختر الثيم</h3>
                <button class="theme-panel-close" id="themeCloseBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="theme-grid" id="themeGrid">
                ${NEXUS_THEMES.map(t => `
                    <div class="theme-option ${savedTheme === t.id ? 'active' : ''}" data-theme="${t.id}">
                        <div class="theme-preview" style="background: ${t.color};"></div>
                        <div>
                            <div class="theme-label">${t.label}</div>
                            <div class="theme-label-ar">${t.labelAr}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    // Events
    fab.addEventListener('click', () => {
        overlay.classList.add('active');
    });

    document.getElementById('themeCloseBtn').addEventListener('click', () => {
        overlay.classList.remove('active');
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
    });

    // Theme selection
    document.getElementById('themeGrid').addEventListener('click', (e) => {
        const option = e.target.closest('.theme-option');
        if (!option) return;
        const themeId = option.dataset.theme;
        
        // Update active state
        document.querySelectorAll('.theme-option').forEach(o => o.classList.remove('active'));
        option.classList.add('active');
        
        // Apply and save
        applyTheme(themeId);
        localStorage.setItem('nexus_theme', themeId);
    });
}

function applyTheme(themeId) {
    // Remove all theme classes
    NEXUS_THEMES.forEach(t => {
        if (t.id) document.body.classList.remove(t.id);
    });
    // Apply selected theme
    if (themeId) {
        document.body.classList.add(themeId);
    }
}

// Initialize theme system on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initThemeSystem();
});

/* =========================================================
   PWA & Preloader System
   ========================================================= */
window.addEventListener("load", () => {
    // Hide Preloader
    const preloader = document.getElementById("nexus-preloader");
    if (preloader) {
        setTimeout(() => {
            preloader.classList.add("hidden");
        }, 500); // 500ms delay to ensure smooth transition
    }

    // Register Service Worker for PWA
    if ("serviceWorker" in navigator) {
        navigator.serviceWorker.register("sw.js")
            .then(reg => console.log("[PWA] Service Worker ???? ?????", reg.scope))
            .catch(err => console.error("[PWA] ??? ????? Service Worker:", err));
    }
});


/* =========================================================
   Epic Features JS (Cursor & Scroll to Top)
   ========================================================= */
document.addEventListener("DOMContentLoaded", () => {
    // Custom Cursor Logic
    const cursor = document.getElementById("customCursor");
    if (cursor) {
        document.addEventListener("mousemove", (e) => {
            cursor.style.left = e.clientX + "px";
            cursor.style.top = e.clientY + "px";
            // Ensure cursor is visible when moving inside document
            if (cursor.style.display === "none") {
                cursor.style.display = "block";
            }
        });
        
        // Event delegation for all interactable elements (even dynamically added ones)
        document.addEventListener("mouseover", (e) => {
            const target = e.target;
            if (target && (
                target.closest("a, button, input, select, textarea, .logo, .latest-card-v2, .lc-ch-row, .chapter-row, .toolbar-btn, .scroll-top-btn, .pop-item, [role='button']")
            )) {
                cursor.classList.add("hovering");
            } else {
                cursor.classList.remove("hovering");
            }
        });

        // Hide when mouse leaves the browser window
        document.addEventListener("mouseleave", () => {
            cursor.style.display = "none";
        });
        document.addEventListener("mouseenter", () => {
            cursor.style.display = "block";
        });
    }


});


/* =========================================================
   Epic Features: Reader Toolbar (Cinema & Auto Scroll)
   ========================================================= */
document.addEventListener("DOMContentLoaded", () => {
    let scrollInterval = null;
    let autoScrollSpeed = 1;

    // We will wait for openReader to be called to attach the toolbar if not exists
    const originalOpenReader = window.openReader;
    window.openReader = function(...args) {
        originalOpenReader.apply(this, args);
        
        setTimeout(() => {
            let engine = document.getElementById("readerEngine");
            if (engine && !document.getElementById("epicReaderToolbar")) {
                const toolbarHTML = `
                    <div id="epicReaderToolbar" class="reader-toolbar">
                        <button class="toolbar-btn" id="btnCinemaMode" title="??? ???????"><i class="fas fa-film"></i></button>
                        <button class="toolbar-btn" id="btnAutoScroll" title="???? ??????"><i class="fas fa-angle-double-down"></i></button>
                        <button class="toolbar-btn" id="btnSpeedUp" title="????? ??????" style="display:none;"><i class="fas fa-plus"></i></button>
                        <button class="toolbar-btn" id="btnSpeedDown" title="????? ??????" style="display:none;"><i class="fas fa-minus"></i></button>
                    </div>
                `;
                engine.insertAdjacentHTML("beforeend", toolbarHTML);

                // Cinema Mode Logic
                const btnCinema = document.getElementById("btnCinemaMode");
                btnCinema.addEventListener("click", () => {
                    document.body.classList.toggle("cinema-mode");
                    btnCinema.classList.toggle("active");
                });

                // Auto Scroll Logic
                const btnAutoScroll = document.getElementById("btnAutoScroll");
                const btnSpeedUp = document.getElementById("btnSpeedUp");
                const btnSpeedDown = document.getElementById("btnSpeedDown");
                const viewport = document.getElementById("readerViewport");

                btnAutoScroll.addEventListener("click", () => {
                    if (scrollInterval) {
                        clearInterval(scrollInterval);
                        scrollInterval = null;
                        btnAutoScroll.classList.remove("active");
                        btnSpeedUp.style.display = "none";
                        btnSpeedDown.style.display = "none";
                    } else {
                        btnAutoScroll.classList.add("active");
                        btnSpeedUp.style.display = "block";
                        btnSpeedDown.style.display = "block";
                        
                        scrollInterval = setInterval(() => {
                            if (viewport) viewport.scrollBy(0, autoScrollSpeed);
                        }, 20);
                    }
                });

                btnSpeedUp.addEventListener("click", () => { autoScrollSpeed = Math.min(autoScrollSpeed + 0.5, 5); });
                btnSpeedDown.addEventListener("click", () => { autoScrollSpeed = Math.max(autoScrollSpeed - 0.5, 0.5); });
                
                // Clear on close
                document.getElementById("closeReader").addEventListener("click", () => {
                    if (scrollInterval) clearInterval(scrollInterval);
                    document.body.classList.remove("cinema-mode");
                });
            }
        }, 300);
    };
});


/* =========================================================
   Phase 2: Epic Features JS (Infinite Scroll, Manga Mode, Report, Custom Lists)
   ========================================================= */
document.addEventListener("DOMContentLoaded", () => {
    // 1. Report Button (AI Self-Healer integration)
    window.triggerAutoHealReport = function() {
        const title = window.currentReaderManga;
        const chapter = window.currentReaderChapter;
        
        if (!title || !chapter) {
            alert("⚠️ التبليغ عن الأعطال متاح فقط أثناء قراءة الفصول.");
            return;
        }
        
        const confirmReport = confirm(`🤖 [بوت نيكسس الذكي]\n\nهل تواجه مشكلة في صور هذا الفصل؟\nسيقوم البوت بإعادة سحب وإصلاح الفصل تلقائياً خلال دقيقة بمجرد إرسال البلاغ!\n\nهل تريد المتابعة لفتح تذكرة الإصلاح؟`);
        
        if (confirmReport) {
            const repoUrl = "https://github.com/anasmohamedsalam9-lab/nexus-read";
            const issueTitle = encodeURIComponent(`[BUG] Broken Chapter: ${title} - Chapter ${chapter}`);
            const issueBody = encodeURIComponent(`🤖 بلاغ تلقائي للإصلاح الذاتي:\n\nManga: ${title}\nChapter: ${chapter}\n\n(يرجى عدم تغيير عنوان البلاغ ليعمل البوت بشكل صحيح)`);
            const targetUrl = `${repoUrl}/issues/new?title=${issueTitle}&body=${issueBody}`;
            
            window.open(targetUrl, "_blank");
        }
    };

    const reportBtnHTML = `<button class="report-btn" onclick="window.triggerAutoHealReport()" title="تبليغ تلقائي عن مشكلة في الفصل"><i class="fas fa-flag"></i></button>`;
    document.body.insertAdjacentHTML("beforeend", reportBtnHTML);

    // 2. Manga Mode & Infinite Scroll Injection
    const origOpenReaderPhase2 = window.openReader;
    window.openReader = function(...args) {
        // Store current details for report button
        window.currentReaderManga = args[0];
        window.currentReaderChapter = args[1];
        
        origOpenReaderPhase2.apply(this, args);
        
        setTimeout(() => {
            let toolbar = document.getElementById("epicReaderToolbar");
            if (toolbar && !document.getElementById("btnMangaMode")) {
                toolbar.insertAdjacentHTML("afterbegin", `<button class="toolbar-btn" id="btnMangaMode" title="??? ??????? (????? ?????)"><i class="fas fa-book-open"></i></button>`);
                
                document.getElementById("btnMangaMode").addEventListener("click", function() {
                    document.body.classList.toggle("manga-mode");
                    this.classList.toggle("active");
                });
            }

            // Infinite Scroll Setup
            const viewport = document.getElementById("readerViewport");
            const seriesSlug = titleToSlug(args[0]);
            const series = findSeriesBySlug(seriesSlug);
            
            if (viewport && series && series.item && series.item.chapters) {
                // Remove old observer if exists
                if (window._currentObserver) {
                    window._currentObserver.disconnect();
                }

                const chapters = [...series.item.chapters].sort((a,b) => parseFloat(a.n) - parseFloat(b.n)); // Ascending
                let currentCh = args[1];

                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const currIdx = chapters.findIndex(c => String(c.n) === String(currentCh));
                            if (currIdx !== -1 && currIdx < chapters.length - 1) {
                                const nextCh = chapters[currIdx + 1];
                                loadNextChapterInline(series.item.title, nextCh, viewport);
                                currentCh = nextCh.n; 
                                observer.unobserve(entry.target); 
                            } else if (currIdx === chapters.length - 1) {
                                observer.unobserve(entry.target);
                                viewport.insertAdjacentHTML("beforeend", `<div class="next-chapter-loader" style="animation:none; color:#888;">??? ???? ??? ??? ???? ??????! ??</div>`);
                            }
                        }
                    });
                }, { root: viewport, rootMargin: "200px", threshold: 0 });
                window._currentObserver = observer;

                function attachObserver() {
                    let trigger = viewport.querySelector(".infinite-scroll-trigger");
                    if (!trigger) {
                        viewport.insertAdjacentHTML("beforeend", `<div class="infinite-scroll-trigger" style="height: 1px; width:100%;"></div>`);
                        trigger = viewport.querySelector(".infinite-scroll-trigger");
                    }
                    observer.observe(trigger);
                }

                function loadNextChapterInline(title, chapterObj, container) {
                    const pagesHTML = chapterObj.pages.map(p => `
                        <img src="${p}" class="reader-image-page skeleton-img" loading="lazy" onload="this.classList.remove('skeleton-img');" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.remove('skeleton-img'); this.classList.add('broken-img');">
                    `).join("");

                    const divider = `<div class="next-chapter-loader">--- ???? ????? ????? ${chapterObj.n} ---</div>`;
                    
                    const trig = container.querySelector(".infinite-scroll-trigger");
                    if (trig) trig.remove();

                    container.insertAdjacentHTML("beforeend", divider + pagesHTML);
                    
                    const slug = titleToSlug(title);
                    const newUrl = `${window.location.pathname}?reader=true&title=${encodeURIComponent(slug)}&ch=${encodeURIComponent(chapterObj.n)}`;
                    window.history.replaceState({reader: true, title: slug, ch: chapterObj.n}, "", newUrl);
                    document.title = `Nexus | ${title} - الفصل ${chapterObj.n}`;
                    document.getElementById("readerChapterNumber").textContent = `الفصل ${chapterObj.n}`;
                    
                    // Update global pointers for report button
                    window.currentReaderManga = title;
                    window.currentReaderChapter = chapterObj.n;
                    
                    saveToHistory(title, chapterObj.n);
                    
                    setTimeout(() => {
                        const loaders = container.querySelectorAll(".next-chapter-loader");
                        if(loaders.length > 0) loaders[loaders.length-1].innerHTML = `--- ????? ????? ${chapterObj.n} ---`;
                        attachObserver();
                    }, 500);
                }

                setTimeout(attachObserver, 1500);
            }
        }, 350);
    };

    // 3. Custom Lists Logic (Migration & Hook)
    // Migrate old flat bookmarks to "reading" list objects
    let bookmarks = JSON.parse(localStorage.getItem("nile_bookmarks")) || [];
    if (bookmarks.length > 0 && typeof bookmarks[0] === "string") {
        bookmarks = bookmarks.map(title => ({ title: title, list: "reading" }));
        localStorage.setItem("nile_bookmarks", JSON.stringify(bookmarks));
    }
});

// Override toggleBookmark to support lists
window.toggleBookmarkList = function(title, listType = "reading") {
    let bookmarks = JSON.parse(localStorage.getItem("nile_bookmarks")) || [];
    const index = bookmarks.findIndex(b => b.title === title);
    
    if (index > -1) {
        if (bookmarks[index].list === listType) {
            bookmarks.splice(index, 1); // remove if same list
            localStorage.setItem("nile_bookmarks", JSON.stringify(bookmarks));
            return false;
        } else {
            bookmarks[index].list = listType; // move to new list
            localStorage.setItem("nile_bookmarks", JSON.stringify(bookmarks));
            return true;
        }
    } else {
        bookmarks.push({ title: title, list: listType });
        localStorage.setItem("nile_bookmarks", JSON.stringify(bookmarks));
        return true;
    }
}

