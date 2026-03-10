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

// Cities for comparison
const COMPARE_CITIES = [
    ["London", "City", 52, "city", "london"],
    ["Birmingham", "City", 44, "city", "birmingham"],
    ["Manchester", "City", 39, "city", "manchester"],
    ["Leeds", "City", 49, "city", "leeds"],
    ["Liverpool", "City", 42, "city", "liverpool"],
    ["Sheffield", "City", 47, "city", "sheffield"],
    ["Bristol", "City", 52, "city", "bristol"],
    ["Newcastle", "City", 45, "city", "newcastle"],
    ["Nottingham", "City", 43, "city", "nottingham"],
    ["Cardiff", "City", 41, "city", "cardiff"],
    ["Leicester", "City", 46, "city", "leicester"],
    ["Coventry", "City", 44, "city", "coventry"],
];

// Forces with comparison pages
const COMPARE_FORCES = ['metropolitan-police-service', 'greater-manchester-police', 'west-midlands-police'];

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
        
        // Filter to only forces with comparison pages + add cities
        const neighbourhoods = (typeof NEIGHBOURHOODS_SEARCH !== 'undefined' ? NEIGHBOURHOODS_SEARCH : [])
            .filter(n => n[2] !== null && COMPARE_FORCES.includes(n[3]) && (n[0].toLowerCase().includes(q) || n[1].toLowerCase().includes(q)))
            .slice(0, 6);
        
        const cities = COMPARE_CITIES
            .filter(c => c[0].toLowerCase().includes(q))
            .slice(0, 4);
        
        const results = [...cities, ...neighbourhoods].slice(0, 8);
        
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
            
            // City vs City - use original order from COMPARE_CITIES
            if (compareData1.force === 'city' && compareData2.force === 'city') {
                const cityOrder = COMPARE_CITIES.map(c => c[4]);
                const idx1 = cityOrder.indexOf(compareData1.nb);
                const idx2 = cityOrder.indexOf(compareData2.nb);
                const first = idx1 < idx2 ? compareData1.nb : compareData2.nb;
                const second = idx1 < idx2 ? compareData2.nb : compareData1.nb;
                window.location.href = `/compare/city/${first}-vs-${second}/`;
                return;
            }
            
            // Same force - neighbourhood comparison (alphabetical sort)
            if (compareData1.force === compareData2.force && compareData1.force !== 'city') {
                const slugs = [compareData1.nb, compareData2.nb].sort();
                // London (Met Police) comparisons are at /compare/{slug}-vs-{slug}/ (no force prefix)
                if (compareData1.force === 'metropolitan-police-service') {
                    window.location.href = `/compare/${slugs[0]}-vs-${slugs[1]}/`;
                } else {
                    window.location.href = `/compare/${compareData1.force}/${slugs[0]}-vs-${slugs[1]}/`;
                }
                return;
            }
            
            // Different forces - redirect to city comparison if available
            alert('Please compare neighbourhoods from the same city, or compare cities directly.');
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
