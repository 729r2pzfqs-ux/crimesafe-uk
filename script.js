// ===== THEME TOGGLE =====
const toggle = document.getElementById('themeToggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const saved = localStorage.getItem('theme');
const theme = saved || (prefersDark ? 'dark' : 'light');

document.documentElement.setAttribute('data-theme', theme);
if (toggle) {
    toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        toggle.textContent = next === 'dark' ? '☀️' : '🌙';
    });
}

// ===== HELPER =====
function getScoreColor(score) {
    if (score === null || score === undefined) return 'var(--color-text-muted)';
    if (score >= 70) return '#16a34a';
    if (score >= 40) return '#ca8a04';
    return '#dc2626';
}

// ===== SEARCH =====
const searchInput = document.getElementById('searchInput');
const searchDropdown = document.getElementById('searchDropdown');

if (searchInput && searchDropdown) {
    searchInput.addEventListener('input', function() {
        const q = this.value.toLowerCase().trim();
        if (!q || q.length < 2) {
            searchDropdown.classList.remove('active');
            return;
        }
        
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
    
    searchInput.addEventListener('blur', () => setTimeout(() => searchDropdown.classList.remove('active'), 200));
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim().length >= 2) searchInput.dispatchEvent(new Event('input'));
    });
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const firstLink = searchDropdown.querySelector('a.search-item');
            if (firstLink) window.location.href = firstLink.href;
        }
    });
}

// ===== COMPARE TOOL =====
const compareCity1 = document.getElementById('compareCity1');
const compareCity2 = document.getElementById('compareCity2');
const compareDropdown1 = document.getElementById('compareDropdown1');
const compareDropdown2 = document.getElementById('compareDropdown2');
const compareBtn = document.getElementById('compareBtn');

let compareData1 = null;
let compareData2 = null;

function setupCompareInput(input, dropdown, setData) {
    if (!input || !dropdown) return;
    
    input.addEventListener('input', function() {
        const q = this.value.toLowerCase().trim();
        setData(null);
        updateCompareBtn();
        
        if (!q || q.length < 2) {
            dropdown.classList.remove('active');
            return;
        }
        
        const results = (typeof NEIGHBOURHOODS_SEARCH !== 'undefined' ? NEIGHBOURHOODS_SEARCH : [])
            .filter(n => n[2] !== null && (n[0].toLowerCase().includes(q) || n[1].toLowerCase().includes(q)))
            .slice(0, 8);
        
        if (!results.length) {
            dropdown.classList.remove('active');
            return;
        }
        
        dropdown.innerHTML = results.map(n => `
            <div class="search-item" data-force="${n[3]}" data-nb="${n[4]}" data-name="${n[0]}, ${n[1]}" data-score="${n[2]}">
                <div>
                    <span class="search-item-name">${n[0]}</span>
                    <span class="search-item-meta">${n[1]}</span>
                </div>
                <span class="search-item-score" style="background:${getScoreColor(n[2])}">${n[2]}</span>
            </div>
        `).join('');
        
        dropdown.querySelectorAll('.search-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.name;
                setData({
                    force: item.dataset.force,
                    nb: item.dataset.nb,
                    name: item.dataset.name,
                    score: item.dataset.score
                });
                dropdown.classList.remove('active');
                updateCompareBtn();
            });
        });
        
        dropdown.classList.add('active');
    });
    
    input.addEventListener('blur', () => setTimeout(() => dropdown.classList.remove('active'), 200));
}

function updateCompareBtn() {
    if (compareBtn) {
        compareBtn.disabled = !compareData1 || !compareData2;
    }
}

if (compareCity1 && compareCity2) {
    setupCompareInput(compareCity1, compareDropdown1, d => compareData1 = d);
    setupCompareInput(compareCity2, compareDropdown2, d => compareData2 = d);
    
    if (compareBtn) {
        compareBtn.addEventListener('click', () => {
            if (!compareData1 || !compareData2) return;
            const slugs = [
                `${compareData1.force}_${compareData1.nb}`,
                `${compareData2.force}_${compareData2.nb}`
            ].sort();
            window.location.href = `/compare/${slugs[0]}-vs-${slugs[1]}/`;
        });
    }
}

// ===== SEARCH/COMPARE TABS =====
document.querySelectorAll('.search-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.search-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.panel).classList.add('active');
    });
});
