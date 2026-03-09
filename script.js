// ===== THEME TOGGLE =====
const toggle = document.getElementById('themeToggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const saved = localStorage.getItem('theme');
const theme = saved || (prefersDark ? 'dark' : 'light');

document.documentElement.setAttribute('data-theme', theme);
toggle.textContent = theme === 'dark' ? '☀️' : '🌙';

toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    toggle.textContent = next === 'dark' ? '☀️' : '🌙';
});

// ===== SEARCH =====
const searchInput = document.getElementById('searchInput');
const searchDropdown = document.getElementById('searchDropdown');

function getScoreColor(score) {
    if (score === null || score === undefined) return 'var(--color-text-muted)';
    if (score >= 70) return '#16a34a';
    if (score >= 40) return '#ca8a04';
    return '#dc2626';
}

if (searchInput && searchDropdown) {
    searchInput.addEventListener('input', function() {
        const q = this.value.toLowerCase().trim();
        if (!q || q.length < 2) {
            searchDropdown.classList.remove('active');
            return;
        }
        
        // Search forces: [name, count, slug]
        const forceResults = (typeof FORCES_SEARCH !== 'undefined' ? FORCES_SEARCH : [])
            .filter(f => f[0].toLowerCase().includes(q))
            .slice(0, 3)
            .map(f => ({
                name: f[0],
                meta: f[1] + ' neighbourhoods',
                score: null,
                url: '/force/' + f[2] + '/',
                type: 'force'
            }));
        
        // Search neighbourhoods: [name, force, score, force_slug, nb_slug]
        const nbResults = (typeof NEIGHBOURHOODS_SEARCH !== 'undefined' ? NEIGHBOURHOODS_SEARCH : [])
            .filter(n => n[0].toLowerCase().includes(q) || n[1].toLowerCase().includes(q))
            .slice(0, 8)
            .map(n => ({
                name: n[0],
                meta: n[1],
                score: n[2],
                url: '/neighbourhood/' + n[3] + '/' + n[4] + '/',
                type: 'neighbourhood'
            }));
        
        const results = [...forceResults, ...nbResults];
        
        if (!results.length) {
            searchDropdown.innerHTML = '<div class="search-item" style="justify-content:center;color:var(--color-text-muted);">No results found</div>';
            searchDropdown.classList.add('active');
            return;
        }
        
        searchDropdown.innerHTML = results.map(r => `
            <a class="search-item" href="${r.url}">
                <div>
                    <span class="search-item-name">${r.name}</span>
                    <span class="search-item-meta">${r.meta}</span>
                    <span class="search-item-type">${r.type}</span>
                </div>
                ${r.score !== null ? `<span class="search-item-score" style="background:${getScoreColor(r.score)}">${r.score}</span>` : ''}
            </a>
        `).join('');
        searchDropdown.classList.add('active');
    });
    
    searchInput.addEventListener('blur', () => {
        setTimeout(() => searchDropdown.classList.remove('active'), 200);
    });
    
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim().length >= 2) {
            searchInput.dispatchEvent(new Event('input'));
        }
    });
    
    // Enter key navigates to first result
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const firstLink = searchDropdown.querySelector('a.search-item');
            if (firstLink) {
                window.location.href = firstLink.href;
            }
        }
    });
}
