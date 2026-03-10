/**
 * Interactive Police Force Map for CrimeSafe UK
 * Uses Leaflet.js with force boundaries from ONS
 */

// Force name mapping (ONS names to our slugs)
const forceNameMap = {
    'Metropolitan Police': 'metropolitan-police-service',
    'City of London': 'city-of-london-police',
    'Greater Manchester': 'greater-manchester-police',
    'West Midlands': 'west-midlands-police',
    'West Yorkshire': 'west-yorkshire-police',
    'Merseyside': 'merseyside-police',
    'South Yorkshire': 'south-yorkshire-police',
    'Northumbria': 'northumbria-police',
    'Essex': 'essex-police',
    'Hampshire': 'hampshire-constabulary',
    'Thames Valley': 'thames-valley-police',
    'Kent': 'kent-police',
    'Avon and Somerset': 'avon-and-somerset-constabulary',
    'Devon and Cornwall': 'devon-and-cornwall-police',
    'Lancashire': 'lancashire-constabulary',
    'Surrey': 'surrey-police',
    'Hertfordshire': 'hertfordshire-constabulary',
    'Sussex': 'sussex-police',
    'South Wales': 'south-wales-police',
    'Nottinghamshire': 'nottinghamshire-police',
    'West Mercia': 'west-mercia-police',
    'Staffordshire': 'staffordshire-police',
    'Leicestershire': 'leicestershire-police',
    'Derbyshire': 'derbyshire-constabulary',
    'Cheshire': 'cheshire-constabulary',
    'Humberside': 'humberside-police',
    'Cleveland': 'cleveland-police',
    'Dorset': 'dorset-police',
    'Cambridgeshire': 'cambridgeshire-constabulary',
    'Norfolk': 'norfolk-constabulary',
    'Suffolk': 'suffolk-constabulary',
    'Bedfordshire': 'bedfordshire-police',
    'Northamptonshire': 'northamptonshire-police',
    'Warwickshire': 'warwickshire-police',
    'Gloucestershire': 'gloucestershire-constabulary',
    'Wiltshire': 'wiltshire-police',
    'Lincolnshire': 'lincolnshire-police',
    'North Yorkshire': 'north-yorkshire-police',
    'North Wales': 'north-wales-police',
    'Dyfed-Powys': 'dyfed-powys-police',
    'Gwent': 'gwent-police',
    'Cumbria': 'cumbria-constabulary',
    'Durham': 'durham-constabulary'
};

// Safety scores by force (will be populated from data)
let forceScores = {};

// Initialize map
function initForceMap() {
    const mapContainer = document.getElementById('forceMap');
    if (!mapContainer) return;
    
    // Create map centered on UK
    const map = L.map('forceMap', {
        center: [54.5, -2],
        zoom: 6,
        scrollWheelZoom: false,
        zoomControl: true
    });
    
    // Add tile layer (light theme)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 10
    }).addTo(map);
    
    // Load force boundaries
    fetch('/data/police_force_boundaries.geojson')
        .then(r => r.json())
        .then(data => {
            addForceLayers(map, data);
        })
        .catch(err => console.error('Error loading boundaries:', err));
}

function getScoreColor(score) {
    if (!score && score !== 0) return '#6b7280'; // gray for no data
    if (score >= 60) return '#16a34a'; // green
    if (score >= 40) return '#ca8a04'; // yellow
    return '#dc2626'; // red
}

function addForceLayers(map, geojson) {
    const forceLayer = L.geoJSON(geojson, {
        style: feature => {
            const name = feature.properties.PFA23NM;
            const slug = forceNameMap[name];
            const score = forceScores[slug];
            
            return {
                fillColor: getScoreColor(score),
                weight: 1,
                opacity: 1,
                color: '#ffffff',
                fillOpacity: 0.6
            };
        },
        onEachFeature: (feature, layer) => {
            const name = feature.properties.PFA23NM;
            const slug = forceNameMap[name] || name.toLowerCase().replace(/\s+/g, '-');
            const score = forceScores[slug];
            
            // Popup content
            const popupContent = `
                <div style="text-align: center; min-width: 150px;">
                    <strong style="font-size: 14px;">${name}</strong><br>
                    ${score ? `<span style="font-size: 18px; font-weight: bold; color: ${getScoreColor(score)};">${score}/100</span><br>` : ''}
                    <a href="/force/${slug}/" style="color: #0f766e;">View Details →</a>
                </div>
            `;
            
            layer.bindPopup(popupContent);
            
            // Hover effect
            layer.on('mouseover', function() {
                this.setStyle({
                    fillOpacity: 0.8,
                    weight: 2
                });
            });
            
            layer.on('mouseout', function() {
                this.setStyle({
                    fillOpacity: 0.6,
                    weight: 1
                });
            });
            
            // Click to navigate
            layer.on('click', function() {
                // Popup will show, then user can click link
            });
        }
    }).addTo(map);
    
    // Fit bounds to UK
    map.fitBounds(forceLayer.getBounds(), { padding: [20, 20] });
}

// Load force scores from our data
function loadForceScores() {
    // This would ideally come from a JSON endpoint
    // For now, calculate from neighbourhoods if available
    if (window.neighbourhoodsData) {
        const scoresByForce = {};
        const countByForce = {};
        
        for (const nb of window.neighbourhoodsData) {
            const force = nb.force || '';
            if (nb.score) {
                if (!scoresByForce[force]) {
                    scoresByForce[force] = 0;
                    countByForce[force] = 0;
                }
                scoresByForce[force] += nb.score;
                countByForce[force]++;
            }
        }
        
        for (const force in scoresByForce) {
            const slug = force.toLowerCase().replace(/\s+/g, '-');
            forceScores[slug] = Math.round(scoresByForce[force] / countByForce[force]);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadForceScores();
    initForceMap();
});
