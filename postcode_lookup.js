/**
 * Postcode Lookup with Autocomplete for CrimeSafe UK
 * Uses postcodes.io API (free, no key needed)
 */

// Initialize postcode lookup
function initPostcodeLookup() {
    const input = document.getElementById('postcodeInput');
    const btn = document.getElementById('postcodeBtn');
    const result = document.getElementById('postcodeResult');
    
    if (!input || !btn) return;
    
    // Create autocomplete dropdown
    const wrapper = input.parentElement;
    wrapper.style.position = 'relative';
    
    const dropdown = document.createElement('div');
    dropdown.id = 'postcodeAutocomplete';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--color-surface, #fff);
        border: 1px solid var(--border, #e5e5e5);
        border-radius: 0 0 8px 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        max-height: 250px;
        overflow-y: auto;
        display: none;
        z-index: 1000;
    `;
    wrapper.appendChild(dropdown);
    
    // Debounce function
    let debounceTimer;
    const debounce = (fn, delay) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fn, delay);
    };
    
    // Autocomplete on input
    input.addEventListener('input', () => {
        const query = input.value.trim();
        if (query.length < 2) {
            dropdown.style.display = 'none';
            return;
        }
        debounce(() => fetchAutocomplete(query, dropdown, input), 200);
    });
    
    // Hide dropdown on blur (with delay for click)
    input.addEventListener('blur', () => {
        setTimeout(() => dropdown.style.display = 'none', 200);
    });
    
    // Show dropdown on focus if has value
    input.addEventListener('focus', () => {
        if (input.value.trim().length >= 2 && dropdown.children.length > 0) {
            dropdown.style.display = 'block';
        }
    });
    
    btn.addEventListener('click', () => lookupPostcode(input.value));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            dropdown.style.display = 'none';
            lookupPostcode(input.value);
        }
    });
    
    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.autocomplete-item');
        const active = dropdown.querySelector('.autocomplete-item.active');
        let idx = Array.from(items).indexOf(active);
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (idx < items.length - 1) idx++;
            else idx = 0;
            items.forEach(i => i.classList.remove('active'));
            items[idx]?.classList.add('active');
            items[idx]?.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (idx > 0) idx--;
            else idx = items.length - 1;
            items.forEach(i => i.classList.remove('active'));
            items[idx]?.classList.add('active');
            items[idx]?.scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter' && active) {
            e.preventDefault();
            active.click();
        }
    });
}

async function fetchAutocomplete(query, dropdown, input) {
    try {
        const resp = await fetch(`https://api.postcodes.io/postcodes/${encodeURIComponent(query)}/autocomplete`);
        if (!resp.ok) {
            dropdown.style.display = 'none';
            return;
        }
        
        const data = await resp.json();
        const suggestions = data.result || [];
        
        if (suggestions.length === 0) {
            dropdown.style.display = 'none';
            return;
        }
        
        dropdown.innerHTML = suggestions.map((postcode, idx) => `
            <div class="autocomplete-item${idx === 0 ? ' active' : ''}" 
                 style="padding: 10px 14px; cursor: pointer; border-bottom: 1px solid var(--border, #eee); transition: background 0.15s;"
                 onmouseover="this.style.background='var(--color-surface-offset, #f5f5f5)'"
                 onmouseout="this.style.background='transparent'"
                 data-postcode="${postcode}">
                <span style="font-weight: 500;">${postcode}</span>
            </div>
        `).join('');
        
        // Add click handlers
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.postcode;
                dropdown.style.display = 'none';
                lookupPostcode(item.dataset.postcode);
            });
        });
        
        dropdown.style.display = 'block';
        
    } catch (err) {
        console.error('Autocomplete error:', err);
        dropdown.style.display = 'none';
    }
}

async function lookupPostcode(postcode) {
    const result = document.getElementById('postcodeResult');
    const dropdown = document.getElementById('postcodeAutocomplete');
    if (dropdown) dropdown.style.display = 'none';
    
    const cleanPostcode = postcode.trim().toUpperCase().replace(/\s+/g, '');
    
    if (!cleanPostcode || cleanPostcode.length < 2) {
        result.innerHTML = '<p style="color: #dc2626;">Please enter a valid UK postcode</p>';
        return;
    }
    
    result.innerHTML = '<p>Looking up...</p>';
    
    try {
        // Get postcode details
        const resp = await fetch(`https://api.postcodes.io/postcodes/${cleanPostcode}`);
        
        if (!resp.ok) {
            // Try outcode (district) lookup
            const outcode = cleanPostcode.replace(/[0-9][A-Z]{2}$/, '');
            const outcodeResp = await fetch(`https://api.postcodes.io/outcodes/${outcode}`);
            
            if (!outcodeResp.ok) {
                result.innerHTML = '<p style="color: #dc2626;">Postcode not found. Try a different postcode.</p>';
                return;
            }
            
            const outcodeData = await outcodeResp.json();
            showOutcodeResult(outcodeData.result, outcode);
            return;
        }
        
        const data = await resp.json();
        showPostcodeResult(data.result);
        
    } catch (err) {
        result.innerHTML = '<p style="color: #dc2626;">Error looking up postcode. Please try again.</p>';
        console.error(err);
    }
}

function showPostcodeResult(data) {
    const result = document.getElementById('postcodeResult');
    const district = data.admin_district || 'Unknown';
    const ward = data.admin_ward || '';
    const outcode = data.outcode || data.postcode.split(' ')[0];
    
    // Find matching neighbourhood from our search data
    let matchedNb = null;
    
    if (window.neighbourhoodsData) {
        const searchTerms = [ward.toLowerCase(), district.toLowerCase()];
        
        for (const nb of window.neighbourhoodsData) {
            const nbName = nb.name.toLowerCase();
            for (const term of searchTerms) {
                if (term && (nbName.includes(term) || term.includes(nbName))) {
                    matchedNb = nb;
                    break;
                }
            }
            if (matchedNb) break;
        }
    }
    
    let html = `
        <div style="background: var(--color-surface); border-radius: var(--radius-md); padding: var(--space-4); margin-top: var(--space-4);">
            <h3 style="margin-bottom: var(--space-2);">${data.postcode}</h3>
            <p style="color: var(--muted);">${ward}, ${district}</p>
    `;
    
    // Always show outcode link
    html += `
        <p style="margin-top: var(--space-3);">
            <a href="/postcode/${outcode.toLowerCase()}/" style="color: var(--color-primary); font-weight: 500;">View ${outcode} area statistics →</a>
        </p>
    `;
    
    if (matchedNb) {
        const score = matchedNb.score || '—';
        const color = score >= 60 ? '#16a34a' : score >= 40 ? '#ca8a04' : '#dc2626';
        html += `
            <div style="margin-top: var(--space-3); padding: var(--space-3); background: var(--color-surface-offset); border-radius: var(--radius-sm);">
                <div style="font-size: var(--text-sm); color: var(--muted);">Nearest Neighbourhood</div>
                <div style="font-weight: 600;">${matchedNb.name}</div>
                <div style="margin-top: var(--space-2);">
                    Safety Score: <span style="font-weight: 700; color: ${color};">${score}/100</span>
                </div>
                <a href="${matchedNb.url}" style="display: inline-block; margin-top: var(--space-2); color: var(--color-primary);">View Details →</a>
            </div>
        `;
    }
    
    html += '</div>';
    result.innerHTML = html;
}

function showOutcodeResult(data, outcode) {
    const result = document.getElementById('postcodeResult');
    const districts = data.admin_district || [];
    
    let html = `
        <div style="background: var(--color-surface); border-radius: var(--radius-md); padding: var(--space-4); margin-top: var(--space-4);">
            <h3 style="margin-bottom: var(--space-2);">${outcode} Area</h3>
            <p style="color: var(--muted);">Covers: ${districts.slice(0, 3).join(', ')}${districts.length > 3 ? '...' : ''}</p>
            <p style="margin-top: var(--space-3);">
                <a href="/postcode/${outcode.toLowerCase()}/" style="color: var(--color-primary); font-weight: 500;">View ${outcode} crime statistics →</a>
            </p>
        </div>
    `;
    
    result.innerHTML = html;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initPostcodeLookup);
