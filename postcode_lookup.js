/**
 * Postcode Lookup for CrimeSafe UK
 * Uses postcodes.io API (free, no key needed)
 */

// Initialize postcode lookup
function initPostcodeLookup() {
    const input = document.getElementById('postcodeInput');
    const btn = document.getElementById('postcodeBtn');
    const result = document.getElementById('postcodeResult');
    
    if (!input || !btn) return;
    
    btn.addEventListener('click', () => lookupPostcode(input.value));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') lookupPostcode(input.value);
    });
}

async function lookupPostcode(postcode) {
    const result = document.getElementById('postcodeResult');
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
    
    // Find matching neighbourhood from our search data
    let matchedNb = null;
    let matchedScore = null;
    
    if (window.neighbourhoodsData) {
        // Try to find by ward name or district
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
    
    if (matchedNb) {
        const score = matchedNb.score || '—';
        const color = score >= 60 ? '#16a34a' : score >= 40 ? '#ca8a04' : '#dc2626';
        html += `
            <div style="margin-top: var(--space-3); padding: var(--space-3); background: var(--color-surface-offset); border-radius: var(--radius-sm);">
                <div style="font-size: var(--text-sm); color: var(--muted);">Nearest Area</div>
                <div style="font-weight: 600;">${matchedNb.name}</div>
                <div style="margin-top: var(--space-2);">
                    Safety Score: <span style="font-weight: 700; color: ${color};">${score}/100</span>
                </div>
                <a href="${matchedNb.url}" style="display: inline-block; margin-top: var(--space-2); color: var(--color-primary);">View Details →</a>
            </div>
        `;
    } else {
        html += `
            <p style="margin-top: var(--space-3); color: var(--muted);">
                Search for "${ward}" or "${district}" above to find crime statistics.
            </p>
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
            <p style="color: var(--muted);">Covers: ${districts.join(', ')}</p>
            <p style="margin-top: var(--space-3);">
                <a href="/postcode/${outcode.toLowerCase()}/" style="color: var(--color-primary);">View ${outcode} crime statistics →</a>
            </p>
        </div>
    `;
    
    result.innerHTML = html;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initPostcodeLookup);
