/* =========================================================
   Profile Page Logic (Nexus)
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

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Page Data
    initProfileData();
    
    // 2. Initialize Tabs Switching
    initTabs();
    
    // 3. Render Reading History
    renderProfileHistory();
    
    // 4. Render Owned Decorations in Settings
    renderOwnedDecorations();
});

function initProfileData() {
    const user = JSON.parse(localStorage.getItem('nile_user'));
    
    if (!user) {
        // If no user, redirect to login for demo purposes
        // window.location.href = 'login.html';
        return;
    }
    
    // Update UI elements
    const nameEl = document.getElementById('profileName');
    const handleEl = document.getElementById('profileHandle');
    const avatarEl = document.getElementById('profileAvatar');
    
    if (nameEl) nameEl.textContent = user.name;
    if (handleEl) handleEl.textContent = `@${user.name.toLowerCase().replace(/\s/g, '_')}_nile`;
    if (avatarEl && user.avatar) avatarEl.src = user.avatar;
}

function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // Remove active class from all
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            // Add active to current
            btn.classList.add('active');
            const targetPane = document.getElementById(`tab-${tabId}`);
            if (targetPane) targetPane.classList.add('active');
        });
    });
    
    // Check URL for specific tab (e.g. ?tab=bookmarks)
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = urlParams.get('tab');
    if (initialTab) {
        const targetBtn = document.querySelector(`.tab-btn[data-tab="${initialTab}"]`);
        if (targetBtn) targetBtn.click();
    }
}

function renderProfileHistory() {
    const history = JSON.parse(localStorage.getItem('nile_history')) || [];
    const container = document.getElementById('historyGrid');
    const countEl = document.getElementById('countReading');
    
    if (!container) return;
    
    // Update Currently Reading Stats
    if (countEl) countEl.textContent = history.length;
    
    if (history.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-ghost"></i>
                <p>لم تبدأ قراءة أي منهوا بعد! استكشف الموقع وابشر بالخير.</p>
                <a href="browse.html" class="btn btn-login" style="margin-top:20px; display:inline-block;">تصفح المنهوا</a>
            </div>
        `;
        return;
    }
    
    // Render History Grid (Vortex Style)
    // We try to cross-reference with DB for more info if available
    container.innerHTML = history.map(item => {
        // Mock progress % and additional info
        const progress = Math.floor(Math.random() * 40) + 60; // 60-100%
        const totalChapters = 50; // Mock total
        
        return `
            <div class="history-card">
                <div class="hc-thumb">
                    <img src="${item.img}" alt="${item.title}">
                    <div class="hc-progress-overlay">${progress}%</div>
                </div>
                <div class="hc-content">
                    <div class="hc-title">${item.title}</div>
                    <div class="hc-meta">
                        <span>Chapter ${item.chapter}</span>
                        <span style="margin: 0 8px; opacity: 0.3;">|</span>
                        <span>آخر قراءة: منذ ساعة</span>
                    </div>
                    
                    <div class="hc-actions">
                        <button class="btn-continue" onclick="window.openReader('${item.title.replace(/'/g, "\\'")}', '${item.chapter}')">
                            <i class="fas fa-play"></i> متابعة القراءة
                        </button>
                    </div>

                    <div class="hc-footer-meta">
                        <span>Chapters (${totalChapters})</span>
                        <i class="fas fa-chevron-down"></i>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/* =========================================================
   Avatar Decorator Logic
   ========================================================= */
const DECORATION_MAP = {
    'deco-nile-aura': { name: 'هالة النيل (Nile Aura)', img: 'Aura' },
    'deco-cyber-glitch': { name: 'اضطراب سيبراني (Cyber)', img: 'Glitch' },
    'deco-solar-flare': { name: 'توهج شمسي (Solar Flare)', img: 'Sun' },
    'deco-void-rift': { name: 'صدع الفراغ (Void Rift)', img: 'Void' },
    'deco-pharaoh': { name: 'تاج الفرعون (Pharaoh)', img: 'Gold' },
    'deco-crescent': { name: 'شفرة الهلال (Crescent)', img: 'Moon' },
    'deco-ethereal': { name: 'ضباب أثيري (Ethereal)', img: 'Mist' },
    'deco-circuit': { name: 'لوحة دوائر (Circuit)', img: 'Tech' },
    'deco-hex': { name: 'درع سداسي (Golden Hex)', img: 'Hex' },
    'deco-egg': { name: 'بيضة التنين (Dragon Egg)', img: 'Egg' },
    'deco-headphones': { name: 'سماعات نيون (Neon Headphones)', img: 'Beats' },
    'deco-pumpkin': { name: 'إطار هالوين (Halloween Ring)', img: 'Spooky' },
    'deco-wings': { name: 'أجنحة شيطانية (Demon Wings)', img: 'Wings' }
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
                    <img src="https://api.dicebear.com/7.x/bottts/svg?seed=${deco.img}" alt="Avatar Preview">
                </div>
                <div class="owned-deco-title">${deco.name}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:5px;">
                    ${isActive ? 'مستخدم حالياً' : 'انقر للتفعيل'}
                </div>
            </div>
        `;
    }).join('');
}

window.equipDecoration = function(id) {
    let activeId = localStorage.getItem('nile_active_decoration') || '';
    
    // Toggle logic: if clicking already active one, unequip it.
    if (activeId === id) {
        localStorage.removeItem('nile_active_decoration');
        alert('تم إزالة الزينة.');
    } else {
        localStorage.setItem('nile_active_decoration', id);
        alert('تم تفعيل الزينة بنجاح! ستظهر عبر الموقع بأكمله.');
    }
    
    // Re-render the grid
    renderOwnedDecorations();
    
    // Immediately apply to profile avatar
    applyStylesToProfileAvatar();
};

function applyStylesToProfileAvatar() {
    const activeDeco = localStorage.getItem('nile_active_decoration');
    const profileAvatar = document.querySelector('.profile-avatar-wrapper');
    
    if(!profileAvatar) return;
    
    // Remove old overlay
    const oldOverlay = profileAvatar.querySelector('.deco-overlay');
    if(oldOverlay) oldOverlay.remove();
    
    if(activeDeco) {
        profileAvatar.classList.add('deco-parent');
        const overlay = document.createElement('div');
        overlay.className = `deco-overlay ${activeDeco}`;
        // Adjust inset because profile avatar has a thick border
        overlay.style.inset = '-15px'; 
        profileAvatar.appendChild(overlay);
    }
}

// Ensure the profile avatar gets the effect on load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(applyStylesToProfileAvatar, 500);
});



