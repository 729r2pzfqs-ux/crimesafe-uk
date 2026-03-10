#!/usr/bin/env python3
"""
Generate postcode district pages for CrimeSafe UK
Maps UK postcode districts to neighbourhoods
"""

import json
import os
import re
import requests
import time
from math import radians, cos, sin, sqrt, atan2

DATA_DIR = "data"
OUTPUT_DIR = "."

# UK postcode areas
POSTCODE_AREAS = [
    "AB", "AL", "B", "BA", "BB", "BD", "BH", "BL", "BN", "BR", "BS", "BT",
    "CA", "CB", "CF", "CH", "CM", "CO", "CR", "CT", "CV", "CW",
    "DA", "DD", "DE", "DG", "DH", "DL", "DN", "DT", "DY",
    "E", "EC", "EH", "EN", "EX",
    "FK", "FY",
    "G", "GL", "GU",
    "HA", "HD", "HG", "HP", "HR", "HS", "HU", "HX",
    "IG", "IP", "IV",
    "KA", "KT", "KW", "KY",
    "L", "LA", "LD", "LE", "LL", "LN", "LS", "LU",
    "M", "ME", "MK", "ML",
    "N", "NE", "NG", "NN", "NP", "NR", "NW",
    "OL", "OX",
    "PA", "PE", "PH", "PL", "PO", "PR",
    "RG", "RH", "RM",
    "S", "SA", "SE", "SG", "SK", "SL", "SM", "SN", "SO", "SP", "SR", "SS", "ST", "SW", "SY",
    "TA", "TD", "TF", "TN", "TQ", "TR", "TS", "TW",
    "UB",
    "W", "WA", "WC", "WD", "WF", "WN", "WR", "WS", "WV",
    "YO",
    "ZE"
]

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def get_header(title, description):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="S7uUZGMb9yLeKT16YkQGWumhCd0n70jt19wxR1qrYEc">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-CK531DR9X9');</script>
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <meta name="theme-color" content="#01696F">
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="/" class="nav-logo">
                <svg width="28" height="28" viewBox="0 0 512 512" fill="none">
                  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="currentColor" opacity="0.1"/>
                  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="none" stroke="currentColor" stroke-width="20" stroke-linejoin="round"/>
                  <text x="256" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="160" fill="currentColor">UK</text>
                </svg>
                <span>CrimeSafe UK</span>
            </a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/forces/">Forces</a>
                <a href="/postcode/">Postcodes</a>
                <a href="/safest/">Rankings</a>
                <a href="/about/">About</a>
            </div>
        </div>
    </nav>
'''

def get_footer():
    return '''
    <footer class="footer">
        <div class="container">
            <p>CrimeSafe UK — Data from <a href="https://data.police.uk">data.police.uk</a></p>
            <p style="margin-top: var(--space-2);">Data updated monthly. Last update: January 2026</p>
        </div>
    </footer>
    <script src="/script.js"></script>
</body>
</html>
'''

def fetch_outcode_info(outcode):
    """Fetch postcode district info from postcodes.io"""
    try:
        resp = requests.get(f"https://api.postcodes.io/outcodes/{outcode}", timeout=10)
        if resp.status_code == 200:
            return resp.json().get('result')
    except:
        pass
    return None

def generate_postcode_page(outcode, outcode_info, nearby_neighbourhoods):
    """Generate a postcode district page"""
    districts = outcode_info.get('admin_district', [])
    lat = outcode_info.get('latitude', 0)
    lng = outcode_info.get('longitude', 0)
    
    title = f"{outcode} Postcode Crime Statistics — CrimeSafe UK"
    desc = f"Crime rates and safety scores for {outcode} postcode area. Covers {', '.join(districts[:3])}."
    
    # Calculate average score
    scores = [n['score'] for n in nearby_neighbourhoods if n.get('score')]
    avg_score = round(sum(scores) / len(scores)) if scores else None
    
    if avg_score:
        if avg_score >= 60:
            grade = "Safe"
            color = "#16a34a"
        elif avg_score >= 40:
            grade = "Average"
            color = "#ca8a04"
        else:
            grade = "Below Average"
            color = "#dc2626"
    else:
        grade = "Unknown"
        color = "var(--muted)"
    
    html = get_header(title, desc)
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/postcode/">Postcodes</a> › {outcode}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{outcode} Postcode Area</h1>
                <p class="hero-sub">{', '.join(districts[:3])}</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-8);">
            <div class="container">
'''
    
    if avg_score:
        html += f'''
                <div class="kpi-card" style="text-align: center; padding: var(--space-6); margin-bottom: var(--space-6);">
                    <div style="font-size: 3rem; font-weight: 700; color: {color};">{avg_score}</div>
                    <div style="color: var(--muted);">Average Safety Score</div>
                    <div style="font-weight: 600; color: {color}; margin-top: var(--space-2);">{grade}</div>
                </div>
'''
    
    html += f'''
                <h2 style="margin-bottom: var(--space-4);">Neighbourhoods in {outcode}</h2>
                <div class="force-grid">
'''
    
    for nb in sorted(nearby_neighbourhoods, key=lambda n: -(n.get('score') or 0))[:20]:
        score = nb.get('score', '—')
        score_color = "#16a34a" if score and score >= 60 else "#ca8a04" if score and score >= 40 else "#dc2626" if score else "var(--muted)"
        
        html += f'''
                    <a href="{nb['url']}" class="force-card" style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0;">{nb['name']}</h3>
                            <div style="font-size: var(--text-sm); color: var(--muted);">{nb.get('force', '')}</div>
                        </div>
                        <div style="font-weight: 600; color: {score_color};">{score if score else '—'}/100</div>
                    </a>
'''
    
    html += f'''
                </div>
                
                <div class="kpi-card" style="margin-top: var(--space-6); padding: var(--space-6);">
                    <h2 style="margin-bottom: var(--space-4);">About {outcode} Area</h2>
                    <p style="color: var(--muted);">
                        The {outcode} postcode district covers parts of {', '.join(districts)}. 
                        {"This area has an average safety score of " + str(avg_score) + "/100, which is considered " + grade.lower() + " for the UK." if avg_score else "Safety scores are based on official police crime data."}
                    </p>
                    <p style="color: var(--muted); margin-top: var(--space-3);">
                        The neighbourhoods shown above are the closest to the {outcode} postcode area. Click on any neighbourhood for detailed crime statistics.
                    </p>
                </div>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    return html

def generate_postcodes_index(valid_outcodes):
    """Generate the postcodes index page"""
    html = get_header("UK Postcode Crime Statistics — CrimeSafe UK", "Find crime rates by UK postcode. Enter your postcode to see local safety scores.")
    html += '''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Postcodes
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>Postcode Crime Lookup</h1>
                <p class="hero-sub">Find crime statistics for any UK postcode</p>
                
                <div style="max-width: 400px; margin: var(--space-6) auto 0;">
                    <div style="display: flex; gap: var(--space-2);">
                        <input type="text" id="postcodeInput" class="search-input" placeholder="Enter postcode (e.g., SW1A 1AA)" style="flex: 1;">
                        <button id="postcodeBtn" class="btn btn-primary">Search</button>
                    </div>
                    <div id="postcodeResult"></div>
                </div>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container">
                <h2 style="margin-bottom: var(--space-4);">Browse by Postcode District</h2>
                <div class="force-grid">
'''
    
    # Group by area
    by_area = {}
    for outcode in sorted(valid_outcodes):
        area = ''.join(c for c in outcode if c.isalpha())
        if area not in by_area:
            by_area[area] = []
        by_area[area].append(outcode)
    
    for area in sorted(by_area.keys()):
        codes = by_area[area]
        html += f'''
                    <div class="force-card">
                        <h3>{area} Area</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-2);">
'''
        for code in codes[:10]:
            html += f'<a href="/postcode/{code.lower()}/" style="color: var(--color-primary);">{code}</a> '
        if len(codes) > 10:
            html += f'<span style="color: var(--muted);">+{len(codes)-10} more</span>'
        html += '''
                        </div>
                    </div>
'''
    
    html += '''
                </div>
            </div>
        </section>
    </main>
    <script src="/postcode_lookup.js"></script>
'''
    html += get_footer()
    return html

def main():
    print("Loading neighbourhood data...")
    
    # Load rankings for neighbourhood scores
    with open(f"{DATA_DIR}/rankings.json") as f:
        rankings = json.load(f)
    
    # Load crime data for lat/lng
    crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
    nb_locations = {}
    
    for fname in os.listdir(crime_dir):
        if not fname.endswith('.json'):
            continue
        with open(f"{crime_dir}/{fname}") as f:
            data = json.load(f)
        
        lat = data.get('lat')
        lng = data.get('lng')
        if lat and lng:
            try:
                nb_locations[fname.replace('.json', '')] = {
                    'lat': float(lat),
                    'lng': float(lng),
                    'name': data.get('neighbourhood_name', ''),
                    'force': data.get('force_id', '')
                }
            except:
                pass
    
    print(f"Loaded {len(nb_locations)} neighbourhood locations")
    
    # Build rankings lookup
    rankings_lookup = {}
    for r in rankings:
        key = f"{slugify(r['force'])}_{r['nb_slug']}"
        rankings_lookup[r['nb_slug']] = r
    
    # Generate postcode districts
    valid_outcodes = []
    generated = 0
    
    for area in POSTCODE_AREAS:
        for num in range(1, 25):
            outcode = f"{area}{num}"
            
            # Check if valid
            info = fetch_outcode_info(outcode)
            if not info:
                continue
            
            valid_outcodes.append(outcode)
            lat = info.get('latitude')
            lng = info.get('longitude')
            
            if not lat or not lng:
                continue
            
            # Find nearby neighbourhoods (within 5km)
            nearby = []
            for key, loc in nb_locations.items():
                dist = haversine_distance(lat, lng, loc['lat'], loc['lng'])
                if dist <= 5:
                    nb_slug = slugify(loc['name'])
                    r = rankings_lookup.get(nb_slug, {})
                    
                    # Build URL
                    force_slug = slugify(loc['force'].replace('-', ' '))
                    url = f"/neighbourhood/{force_slug}/{nb_slug}/"
                    
                    nearby.append({
                        'name': loc['name'],
                        'force': loc['force'].replace('-', ' ').title(),
                        'score': r.get('score'),
                        'url': url,
                        'distance': dist
                    })
            
            nearby.sort(key=lambda n: n['distance'])
            
            # Generate page
            out_dir = f"{OUTPUT_DIR}/postcode/{outcode.lower()}"
            os.makedirs(out_dir, exist_ok=True)
            
            with open(f"{out_dir}/index.html", 'w') as f:
                f.write(generate_postcode_page(outcode, info, nearby[:15]))
            
            generated += 1
            if generated % 50 == 0:
                print(f"  Generated {generated} postcode pages...")
            
            time.sleep(0.1)  # Rate limit
    
    # Generate index
    print("Generating postcodes index...")
    os.makedirs(f"{OUTPUT_DIR}/postcode", exist_ok=True)
    with open(f"{OUTPUT_DIR}/postcode/index.html", 'w') as f:
        f.write(generate_postcodes_index(valid_outcodes))
    
    print(f"\n{'='*50}")
    print(f"Generated {generated + 1} postcode pages")
    print(f"  - Index: /postcode/")
    print(f"  - District pages: {generated}")

if __name__ == "__main__":
    main()
