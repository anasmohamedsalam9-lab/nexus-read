/* =========================================================
   Nexus - Dynamic Browse Engine (2026)
   ========================================================= */

// Sync with shared SITE_DATA from data.js
function getBrowseData() {
    let allMedia = [];
    
    Object.keys(SITE_DATA).forEach(catKey => {
        const catData = SITE_DATA[catKey];
        // Merge trending, latest, popular into one list for browsing
        ['trending', 'latest', 'popular', 'topSlider'].forEach(section => {
            if (catData[section]) {
                catData[section].forEach(item => {
                    // Prevent duplicates based on title
                    if (!allMedia.find(m => m.title === item.title)) {
                        allMedia.push({ ...item, category: catKey });
                    }
                });
            }
        });
    });
    
    return allMedia;
}

document.addEventListener('DOMContentLoaded', () => {
    // Wait slightly if SITE_DATA is still being filled by enrichment
    if (typeof SITE_DATA !== 'undefined') {
        initBrowseGrid();
        initFilterLogic();
    }
});

// Render the grid elements based on Data
function renderBrowseGrid(data) {
    const grid = document.getElementById('browseGrid');
    const count = document.getElementById('resultCount');
    
    if (!grid || !count) return;
    
    count.textContent = data.length;
    
    if(data.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-secondary);">لا توجد نتائج تطابق فلاتر البحث.</div>`;
        return;
    }

    grid.innerHTML = data.map(item => {
        const typeLabel = item.category === 'manhwa' ? 'مانها' : 
                         item.category === 'manga' ? 'مانجا' :
                         item.category === 'novels' ? 'رواية' : 'كوميكس';
                         
        const latestCh = item.chapters && item.chapters.length > 0 ? item.chapters[0].n : (item.ch || '0');
        
        return `
        <article class="media-card" onclick="goToSeries('${item.title}', '${item.category}')">
            <div class="media-poster-wrap">
                <div class="media-badges">
                    <span class="rating-badge"><i class="fas fa-star"></i> ${item.rating || '9.5'}</span>
                    <span class="type-badge ${item.category}">${typeLabel}</span>
                </div>
                <img src="${item.img || ''}" alt="${item.title}" class="media-poster-img" loading="lazy" onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='; this.classList.add('broken-img');">
                <div class="media-overlay-gradient"></div>
                <div class="media-chapter-tag">الفصل ${latestCh}</div>
                
                <div class="media-action-overlay">
                    <button class="btn btn-primary btn-glow btn-sm">
                        <i class="fas fa-book-open"></i> اقرأ الآن
                    </button>
                </div>
            </div>
            <div class="media-info">
                <h3 class="media-title">${item.title}</h3>
                <div class="media-meta">
                    <span><i class="fas fa-clock text-accent"></i> ${item.status || 'مستمر'}</span>
                </div>
            </div>
        </article>
        `;
    }).join('');
}

function initBrowseGrid() {
    renderBrowseGrid(getBrowseData());
}

// Logic for handling filters
function initFilterLogic() {
    let browseData = getBrowseData();
    let currentFilters = {
        type: 'all',
        genre: 'all',
        status: 'all',
        sort: 'latest'
    };

    const typeTabs = document.querySelectorAll('.type-tab');
    const genreFilter = document.getElementById('genreFilter');
    const statusFilter = document.getElementById('statusFilter');
    const sortFilter = document.getElementById('sortFilter');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');

    function applyFilters() {
        let filtered = browseData.filter(item => {
            let passType = currentFilters.type === 'all' || item.category === currentFilters.type;
            let passGenre = currentFilters.genre === 'all' || (item.genres && item.genres.map(g => g.toLowerCase()).includes(currentFilters.genre.toLowerCase()));
            let passStatus = currentFilters.status === 'all' || item.status === currentFilters.status;
            return passType && passGenre && passStatus;
        });

        // Sorting Logic
        if (currentFilters.sort === 'popular') {
             // Use rating or total chapters if views not available
            filtered.sort((a, b) => parseFloat(b.rating || 0) - parseFloat(a.rating || 0));
        } else if (currentFilters.sort === 'rating') {
            filtered.sort((a, b) => parseFloat(b.rating || 0) - parseFloat(a.rating || 0));
        } else if (currentFilters.sort === 'az') {
            filtered.sort((a, b) => a.title.localeCompare(b.title));
        }

        renderBrowseGrid(filtered);
    }

    // Event Listeners
    typeTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            typeTabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentFilters.type = e.target.dataset.type;
            applyFilters();
        });
    });

    if(genreFilter) {
        genreFilter.addEventListener('change', (e) => {
            currentFilters.genre = e.target.value;
            applyFilters();
        });
    }

    if(statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            currentFilters.status = e.target.value;
            applyFilters();
        });
    }

    if(sortFilter) {
        sortFilter.addEventListener('change', (e) => {
            currentFilters.sort = e.target.value;
            applyFilters();
        });
    }
    
    if(resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', () => {
            currentFilters = { type: 'all', genre: 'all', status: 'all', sort: 'latest' };
            typeTabs.forEach(t => t.classList.remove('active'));
            document.querySelector('.type-tab[data-type="all"]').classList.add('active');
            
            if(genreFilter) genreFilter.value = 'all';
            if(statusFilter) statusFilter.value = 'all';
            if(sortFilter) sortFilter.value = 'latest';
            
            applyFilters();
        });
    }
    
    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const urlGenre = urlParams.get('genre');
    if (urlGenre && genreFilter) {
        genreFilter.value = urlGenre;
        currentFilters.genre = urlGenre;
        applyFilters();
    }
}



