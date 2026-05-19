/* =========================================================
   Profile Page Logic - Nexus (Vortex Scans Style)
   ========================================================= */

// Safe LocalStorage Interceptor to prevent SecurityError on file:/// protocol
(function() {
    try {
        const x = '__storage_test__';
        window.localStorage.setItem(x, x);
        window.localStorage.removeItem(x);
    } catch (e) {
        console.warn('[SafeStorage] localStorage is blocked. Using memory fallback.');
        const mockStore = {};
        const mockStorage = {
            getItem: function(key) { return key in mockStore ? mockStore[key] : null; },
            setItem: function(key, val) { mockStore[key] = String(val); },
            removeItem: function(key) { delete mockStore[key]; },
            clear: function() { for (let key in mockStore) delete mockStore[key]; },
            key: function(i) { return Object.keys(mockStore)[i] || null; },
            get length() { return Object.keys(mockStore).length; }
        };
        Object.defineProperty(window, 'localStorage', { value: mockStorage, writable: true });
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    initProfileData();
    initTabs();
    renderProfileHistory();
    renderProfileBookmarks();
    renderOwnedDecorations();
    initSettingsActions();
    
    // Quest initialization
    initQuests();
});

/* ---- Profile Data ---- */
function initProfileData() {
    const user = JSON.parse(localStorage.getItem('nile_user'));
    if (!user) return;

    const nameEl = document.getElementById('profileName');
    const handleEl = document.getElementById('profileHandle');
    const avatarEl = document.getElementById('profileAvatar');

    if (nameEl) {
        nameEl.textContent = user.name;
        // Click to edit username
        nameEl.style.cursor = 'pointer';
        nameEl.title = 'اضغط لتعديل الاسم';
        nameEl.addEventListener('click', () => {
            const newName = prompt('أدخل اسمك الجديد:', user.name);
            if (newName && newName.trim()) {
                user.name = newName.trim();
                localStorage.setItem('nile_user', JSON.stringify(user));
                nameEl.textContent = user.name;
                if (handleEl) handleEl.textContent = `@${user.name.toLowerCase().replace(/\s/g, '_')}_nexus`;
            }
        });
    }
    if (handleEl) handleEl.textContent = `@${user.name.toLowerCase().replace(/\s/g, '_')}_nexus`;
    if (avatarEl && user.avatar) avatarEl.src = user.avatar;

    // Calculate total chapters read
    const history = JSON.parse(localStorage.getItem('nile_history')) || [];
    let totalChaptersRead = 0;
    history.forEach(item => {
        totalChaptersRead += Math.max(1, parseInt(item.chapter) || 1);
    });
    const chaptersEl = document.getElementById('countChaptersRead');
    if (chaptersEl) chaptersEl.textContent = totalChaptersRead;
}

/* ---- Tabs ---- */
function initTabs() {
    const tabs = document.querySelectorAll('.vx-tab');
    const panes = document.querySelectorAll('.vx-pane');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const id = tab.getAttribute('data-tab');
            tabs.forEach(t => t.classList.remove('active'));
            panes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(`tab-${id}`);
            if (target) target.classList.add('active');
        });
    });

    // URL param support (e.g. ?tab=bookmarks)
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = urlParams.get('tab');
    if (initialTab) {
        const targetBtn = document.querySelector(`.vx-tab[data-tab="${initialTab}"]`);
        if (targetBtn) targetBtn.click();
    }
}

/* ---- Helper: titleToSlug ---- */
function _titleToSlug(title) {
    return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

/* ---- Helper: Find series in DB ---- */
function _findSeries(title) {
    if (typeof DB === 'undefined') return null;
    return DB.find(s => s.title === title) || DB.find(s => _titleToSlug(s.title) === _titleToSlug(title));
}

/* ---- Helper: Time ago ---- */
function _timeAgo(timestamp) {
    if (!timestamp) return 'غير معروف';
    const diff = Date.now() - timestamp;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'الآن';
    if (mins < 60) return `منذ ${mins} دقيقة`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `منذ ${hours} ساعة`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `منذ ${days} يوم`;
    return `منذ ${Math.floor(days/30)} شهر`;
}

/* ---- Reading History ---- */
function renderProfileHistory() {
    const history = JSON.parse(localStorage.getItem('nile_history')) || [];
    const container = document.getElementById('historyGrid');
    const countEl = document.getElementById('countReading');

    if (!container) return;
    if (countEl) countEl.textContent = history.length;

    if (history.length === 0) {
        container.innerHTML = `
            <div class="vx-empty">
                <i class="fas fa-book-open"></i>
                <p>لم تبدأ قراءة أي عمل بعد!</p>
                <a href="browse.html">تصفح الأعمال</a>
            </div>
        `;
        return;
    }

    container.innerHTML = history.map(item => {
        // Try to get cover from DB if item.img is broken
        let cover = '';
        if (item.img && item.img !== 'undefined' && item.img !== 'null' && !item.img.includes('placeholder')) {
            cover = item.img;
        }
        
        const series = _findSeries(item.title);
        if (series) {
            cover = series.cover || series.img || cover;
        }
        
        if (!cover || cover === 'images/default-cover.jpg') {
            cover = 'images/default-cover.jpg';
        }
        
        const totalCh = series && series.chapters ? series.chapters.length : '?';
        const timeAgo = _timeAgo(item.timestamp);

        return `
            <div class="vx-h-card" onclick="window.openReader && window.openReader('${item.title.replace(/'/g, "\\'")}', '${item.chapter}')">
                <div class="vx-h-thumb">
                    <img src="${cover}" alt="${item.title}" onerror="this.src='images/default-cover.jpg';">
                    <span class="vx-h-badge">قيد القراءة</span>
                    <span class="vx-h-chapter-tag">فصل ${item.chapter}</span>
                </div>
                <div class="vx-h-body">
                    <div class="vx-h-title">${item.title}</div>
                    <div class="vx-h-meta">
                        <i class="fas fa-clock"></i> ${timeAgo}
                        <span style="opacity:0.3">|</span>
                        <i class="fas fa-layer-group"></i> ${totalCh} فصل
                    </div>
                    <div class="vx-h-progress">
                        <div class="vx-h-progress-fill" style="width: 100%;"></div>
                    </div>
                    <button class="vx-h-action" onclick="event.stopPropagation(); window.openReader && window.openReader('${item.title.replace(/'/g, "\\'")}', '${item.chapter}')">
                        <i class="fas fa-play"></i> متابعة القراءة
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/* ---- Bookmarks ---- */
function renderProfileBookmarks() {
    const bookmarks = JSON.parse(localStorage.getItem('nile_bookmarks')) || [];
    const container = document.getElementById('bookmarksGrid');
    const countEl = document.getElementById('countBookmarks');

    if (!container) return;
    if (countEl) countEl.textContent = bookmarks.length;

    if (bookmarks.length === 0) {
        container.innerHTML = `
            <div class="vx-empty">
                <i class="fas fa-heart-broken"></i>
                <p>لا توجد أعمال في قائمة المفضلة!</p>
                <a href="browse.html">أضف أعمالاً الآن</a>
            </div>
        `;
        return;
    }

    container.innerHTML = bookmarks.map(title => {
        const series = _findSeries(title);
        const cover = series ? (series.cover || series.img || 'images/default-cover.jpg') : 'images/default-cover.jpg';
        const status = series ? (series.status || 'Ongoing') : 'Ongoing';
        const statusClass = status.toLowerCase() === 'completed' ? 'completed' : 'ongoing';
        const statusText = status.toLowerCase() === 'completed' ? 'مكتمل' : 'مستمر';
        const latestCh = series && series.chapters && series.chapters.length > 0
            ? [...series.chapters].sort((a,b) => parseFloat(b.n) - parseFloat(a.n))[0].n
            : '?';
        const slug = _titleToSlug(title);

        return `
            <div class="vx-bm-card" onclick="window.location.href='series.html?title=${slug}'">
                <div class="vx-bm-cover">
                    <img src="${cover}" alt="${title}" onerror="this.src='images/default-cover.jpg';">
                    <span class="vx-bm-status ${statusClass}">${statusText}</span>
                    <button class="vx-bm-heart" onclick="event.stopPropagation(); removeBookmark('${title.replace(/'/g, "\\'")}')">
                        <i class="fas fa-heart"></i>
                    </button>
                </div>
                <div class="vx-bm-info">
                    <div class="vx-bm-title">${title}</div>
                    <div class="vx-bm-chapter">آخر فصل: ${latestCh}</div>
                </div>
            </div>
        `;
    }).join('');
}

/* ---- Remove Bookmark ---- */
window.removeBookmark = function(title) {
    let bookmarks = JSON.parse(localStorage.getItem('nile_bookmarks')) || [];
    bookmarks = bookmarks.filter(b => b !== title);
    localStorage.setItem('nile_bookmarks', JSON.stringify(bookmarks));
    renderProfileBookmarks();
};

/* ---- Settings Actions ---- */
function initSettingsActions() {
    // Clear History
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', () => {
            if (confirm('هل أنت متأكد من مسح سجل القراءة بالكامل؟')) {
                localStorage.removeItem('nile_history');
                renderProfileHistory();
            }
        });
    }

    // Clear All Data
    const clearAllBtn = document.getElementById('clearAllDataBtn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', () => {
            if (confirm('⚠️ سيتم حذف جميع بياناتك (السجل، المفضلة، الإعدادات). هل أنت متأكد؟')) {
                localStorage.removeItem('nile_history');
                localStorage.removeItem('nile_bookmarks');
                localStorage.removeItem('nile_decorations');
                localStorage.removeItem('nile_active_decoration');
                alert('تم حذف جميع البيانات.');
                location.reload();
            }
        });
    }

    // Avatar Upload
    const avatarUpload = document.getElementById('avatarUpload');
    if (avatarUpload) {
        avatarUpload.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => {
                const avatarEl = document.getElementById('profileAvatar');
                if (avatarEl) avatarEl.src = ev.target.result;
                // Save to user data
                let user = JSON.parse(localStorage.getItem('nile_user')) || {};
                user.avatar = ev.target.result;
                localStorage.setItem('nile_user', JSON.stringify(user));
            };
            reader.readAsDataURL(file);
        });
    }
}

/* ---- Avatar Decorator Logic ---- */
const DECORATION_MAP = {
    'deco-phoenix-aura': { name: 'هالة طائر العنقاء (Phoenix)', img: 'Phoenix' },
    'deco-dragon-spirit': { name: 'روح التنين الذهبي (Dragon)', img: 'Dragon' },
    'deco-galaxy-orbit': { name: 'مدار المجرة الكونية (Galaxy)', img: 'Galaxy' },
    'deco-cyber-neon': { name: 'السيبراني المشع (Cyber)', img: 'Cyber' },
    'deco-blossom-drift': { name: 'بتلات الكرز (Blossom)', img: 'Blossom' },
    'deco-abyss-gaze': { name: 'بوابة الهاوية (Abyss)', img: 'Abyss' },
    'deco-lightning-storm': { name: 'عاصفة البرق (Lightning)', img: 'Thunder' },
    'deco-prism-shimmer': { name: 'انعكاس قوس قزح (Prism)', img: 'Rainbow' }
};

function renderOwnedDecorations() {
    const grid = document.getElementById('ownedDecosGrid');
    if (!grid) return;

    let ownedIds = JSON.parse(localStorage.getItem('nile_decorations')) || [];
    let activeId = localStorage.getItem('nile_active_decoration') || '';

    if (ownedIds.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <i class="fas fa-box-open"></i>
                <p>لم تقم بشراء أي زينة حتى الآن. قم بزيارة <a href="shop.html" class="text-accent">المتجر</a> لاقتناء أروع التصاميم!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = ownedIds.map(id => {
        const deco = DECORATION_MAP[id] || { name: id, img: 'Mystery' };
        const isActive = id === activeId;
        return `
            <div class="owned-deco-card ${isActive ? 'active' : ''}" onclick="equipDecoration('${id}')">
                <div class="owned-preview-box deco-parent">
                    <div class="deco-overlay ${id}"></div>
                    <img src="https://api.dicebear.com/7.x/bottts/svg?seed=${deco.img}" alt="Preview">
                </div>
                <div class="owned-deco-title">${deco.name}</div>
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.35); margin-top:5px;">
                    ${isActive ? '✅ مستخدم حالياً' : 'انقر للتفعيل'}
                </div>
            </div>
        `;
    }).join('');
}

window.equipDecoration = function(id) {
    let activeId = localStorage.getItem('nile_active_decoration') || '';
    if (activeId === id) {
        localStorage.removeItem('nile_active_decoration');
    } else {
        localStorage.setItem('nile_active_decoration', id);
    }
    renderOwnedDecorations();
    applyStylesToProfileAvatar();
};

function applyStylesToProfileAvatar() {
    const activeDeco = localStorage.getItem('nile_active_decoration');
    const avatarWrapper = document.querySelector('.vx-avatar-ring');
    if (!avatarWrapper) return;

    const oldOverlay = avatarWrapper.querySelector('.deco-overlay');
    if (oldOverlay) oldOverlay.remove();

    if (activeDeco) {
        avatarWrapper.classList.add('deco-parent');
        const overlay = document.createElement('div');
        overlay.className = `deco-overlay ${activeDeco}`;
        avatarWrapper.appendChild(overlay);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(applyStylesToProfileAvatar, 300);
});

/* =========================================================
   QUEST / MISSION SYSTEM LOGIC
   ========================================================= */

const QUEST_STATE_KEY = 'nexus_quests_state_v1';

// Default Daily & Weekly quests templates
const DAILY_QUEST_TEMPLATE = {
    id: "daily_read_5",
    title: "اقرأ 5 فصول اليوم (اربح 30 كـونز)",
    progress: 0,
    target: 5,
    reward: 30,
    claimed: false,
    icon: "fa-book-open"
};

const WEEKLY_QUESTS_TEMPLATES = [
    { id: "wk_login_3", title: "سجل الدخول لـ 3 أيام متتالية", progress: 1, target: 3, reward: 100, claimed: false, icon: "fa-calendar-check" },
    { id: "wk_read_20", title: "اقرأ 20 فصلاً هذا الأسبوع", progress: 0, target: 20, reward: 150, claimed: false, icon: "fa-book-reader" },
    { id: "wk_read_50", title: "اقرأ 50 فصلاً هذا الأسبوع", progress: 0, target: 50, reward: 350, claimed: false, icon: "fa-fire" },
    { id: "wk_fav_5", title: "أضف 5 أعمال للمفضلة", progress: 0, target: 5, reward: 80, claimed: false, icon: "fa-bookmark" },
    { id: "wk_read_action", title: "اقرأ فصلاً من تصنيف الأكشن (Action)", progress: 0, target: 1, reward: 50, claimed: false, icon: "fa-swords" },
    { id: "wk_read_romance", title: "اقرأ فصلاً من تصنيف الرومانسية (Romance)", progress: 0, target: 1, reward: 50, claimed: false, icon: "fa-heart" },
    { id: "wk_view_10", title: "تصفح 10 أعمال مختلفة في المنصة", progress: 0, target: 10, reward: 120, claimed: false, icon: "fa-search" },
    { id: "wk_finish_1", title: "أكمل قراءة عمل مكتمل بالكامل", progress: 0, target: 1, reward: 200, claimed: false, icon: "fa-check-double" },
    { id: "wk_comment_1", title: "ترك تعليقاً على أي فصل منهوا", progress: 0, target: 1, reward: 60, claimed: false, icon: "fa-comment-alt" },
    { id: "wk_like_5", title: "تفاعل بـ 5 إعجابات على الفصول", progress: 0, target: 5, reward: 80, claimed: false, icon: "fa-thumbs-up" }
];

function initQuests() {
    let questState = JSON.parse(localStorage.getItem(QUEST_STATE_KEY));
    const now = Date.now();
    const oneDayMs = 24 * 60 * 60 * 1000;
    const oneWeekMs = 7 * 24 * 60 * 60 * 1000;

    if (!questState) {
        // Initialize fresh state
        questState = {
            lastDailyReset: now,
            lastWeeklyReset: now,
            daily: { ...DAILY_QUEST_TEMPLATE },
            weekly: WEEKLY_QUESTS_TEMPLATES.map(q => ({ ...q }))
        };
    } else {
        // Safe check and reset if daily reset time passed
        if (now - questState.lastDailyReset > oneDayMs) {
            questState.daily = { ...DAILY_QUEST_TEMPLATE };
            questState.lastDailyReset = now;
        }
        // Safe check and reset if weekly reset time passed
        if (now - questState.lastWeeklyReset > oneWeekMs) {
            questState.weekly = WEEKLY_QUESTS_TEMPLATES.map(q => ({ ...q }));
            questState.lastWeeklyReset = now;
        }
    }

    localStorage.setItem(QUEST_STATE_KEY, JSON.stringify(questState));
    updateQuestProgress();
}

function updateQuestProgress() {
    const questState = JSON.parse(localStorage.getItem(QUEST_STATE_KEY));
    if (!questState) return;

    const history = JSON.parse(localStorage.getItem('nile_history')) || [];
    const bookmarks = JSON.parse(localStorage.getItem('nile_bookmarks')) || [];
    const comments = JSON.parse(localStorage.getItem('nile_comments')) || [];
    const likes = parseInt(localStorage.getItem('nile_likes_count')) || 0;

    // 1. Daily read quest progress (chapters read today)
    const startOfDay = new Date().setHours(0, 0, 0, 0);
    // count unique chapter items read today
    const readToday = history.filter(item => item.timestamp && item.timestamp >= startOfDay).length;
    if (!questState.daily.claimed) {
        questState.daily.progress = Math.min(questState.daily.target, readToday);
    }

    // 2. Weekly quests progress
    questState.weekly.forEach(quest => {
        if (quest.claimed) return; // Don't overwrite claimed quest progress

        switch (quest.id) {
            case "wk_login_3":
                // Just a mock visit counter for simplicity, initialized at 1, goes up with visits
                let visitDays = JSON.parse(localStorage.getItem('nexus_visit_days')) || [];
                const todayStr = new Date().toDateString();
                if (!visitDays.includes(todayStr)) {
                    visitDays.push(todayStr);
                    localStorage.setItem('nexus_visit_days', JSON.stringify(visitDays));
                }
                quest.progress = Math.min(quest.target, visitDays.length);
                break;

            case "wk_read_20":
                quest.progress = Math.min(quest.target, history.length);
                break;

            case "wk_read_50":
                quest.progress = Math.min(quest.target, history.length);
                break;

            case "wk_fav_5":
                quest.progress = Math.min(quest.target, bookmarks.length);
                break;

            case "wk_read_action":
                const hasAction = history.some(item => {
                    const series = _findSeries(item.title);
                    return series && (series.genres.includes('أكشن') || series.genres.toLowerCase().includes('action'));
                });
                quest.progress = hasAction ? 1 : 0;
                break;

            case "wk_read_romance":
                const hasRomance = history.some(item => {
                    const series = _findSeries(item.title);
                    return series && (series.genres.includes('رومانسية') || series.genres.toLowerCase().includes('romance') || series.genres.includes('دراما'));
                });
                quest.progress = hasRomance ? 1 : 0;
                break;

            case "wk_view_10":
                const distinctTitles = new Set(history.map(item => item.title)).size;
                quest.progress = Math.min(quest.target, distinctTitles);
                break;

            case "wk_finish_1":
                const hasCompletedRead = history.some(item => {
                    const series = _findSeries(item.title);
                    return series && (series.status && (series.status.toLowerCase() === 'completed' || series.status === 'مكتمل'));
                });
                quest.progress = hasCompletedRead ? 1 : 0;
                break;

            case "wk_comment_1":
                quest.progress = comments.length > 0 ? 1 : 0;
                break;

            case "wk_like_5":
                quest.progress = Math.min(quest.target, likes);
                break;
        }
    });

    localStorage.setItem(QUEST_STATE_KEY, JSON.stringify(questState));
    renderQuests();
}

function renderQuests() {
    const questState = JSON.parse(localStorage.getItem(QUEST_STATE_KEY));
    if (!questState) return;

    const dailyList = document.getElementById('dailyQuestsList');
    const weeklyList = document.getElementById('weeklyQuestsList');

    if (dailyList) {
        const q = questState.daily;
        const isFinished = q.progress >= q.target;
        dailyList.innerHTML = renderQuestCardHTML(q, isFinished, 'daily');
    }

    if (weeklyList) {
        weeklyList.innerHTML = questState.weekly.map(q => {
            const isFinished = q.progress >= q.target;
            return renderQuestCardHTML(q, isFinished, 'weekly');
        }).join('');
    }
}

function renderQuestCardHTML(q, isFinished, type) {
    const percentage = Math.round((q.progress / q.target) * 100);
    
    let btnClass = 'incomplete';
    let btnText = 'غير مكتمل';
    
    if (q.claimed) {
        btnClass = 'claimed';
        btnText = 'تم استلام الجائزة';
    } else if (isFinished) {
        btnClass = 'claimable';
        btnText = 'استلام الجائزة';
    }

    let cardClass = '';
    if (q.claimed) cardClass = 'claimed';
    else if (isFinished) cardClass = 'completed';
    else cardClass = 'active-quest';

    return `
        <div class="quest-card ${cardClass}" id="quest-card-${q.id}">
            <div class="quest-icon-side">
                <i class="fas ${q.icon || 'fa-tasks'}"></i>
            </div>
            <div class="quest-details-side">
                <div class="quest-title">${q.title}</div>
                <div class="quest-progress-wrapper">
                    <div class="quest-progress-bar">
                        <div class="quest-progress-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="quest-progress-text">${q.progress}/${q.target}</div>
                </div>
            </div>
            <div class="quest-reward-side">
                <div class="quest-reward-badge">
                    <i class="fas fa-coins"></i> +${q.reward}
                </div>
                <button class="quest-btn ${btnClass}" onclick="claimQuestReward('${q.id}', '${type}')" ${q.claimed || !isFinished ? 'disabled' : ''}>
                    ${btnText}
                </button>
            </div>
        </div>
    `;
}

window.claimQuestReward = function(questId, type) {
    const questState = JSON.parse(localStorage.getItem(QUEST_STATE_KEY));
    if (!questState) return;

    let targetQuest = null;
    if (type === 'daily' && questState.daily.id === questId) {
        targetQuest = questState.daily;
    } else if (type === 'weekly') {
        targetQuest = questState.weekly.find(q => q.id === questId);
    }

    if (targetQuest && targetQuest.progress >= targetQuest.target && !targetQuest.claimed) {
        targetQuest.claimed = true;
        
        // Add coins!
        const rewardAmount = targetQuest.reward;
        const currentCoins = parseInt(localStorage.getItem('nile_coins')) || 0;
        const newCoins = currentCoins + rewardAmount;
        localStorage.setItem('nile_coins', newCoins);

        // Update quest state in storage
        localStorage.setItem(QUEST_STATE_KEY, JSON.stringify(questState));
        
        // Refresh UI
        updateQuestProgress();
        if (window.refreshNavBalance) window.refreshNavBalance();

        // Premium alert
        alert(`🎉 مبروك! لقد حصلت على +${rewardAmount} عملة من عملات نيكسس لإتمامك المهمة: "${targetQuest.title}"`);
    }
};
