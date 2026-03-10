#!/usr/bin/env python3
"""
CrimeSafe UK - Static Site Generator
"""

import json
import os
import re
from datetime import datetime

DATA_DIR = "data"
OUTPUT_DIR = "."

# Crime category display names and weights for safety score
CRIME_WEIGHTS = {
    "violent-crime": {"name": "Violent Crime", "weight": 1.0, "icon": "⚠️"},
    "robbery": {"name": "Robbery", "weight": 0.9, "icon": "💰"},
    "burglary": {"name": "Burglary", "weight": 0.7, "icon": "🏠"},
    "vehicle-crime": {"name": "Vehicle Crime", "weight": 0.5, "icon": "🚗"},
    "theft-from-the-person": {"name": "Theft from Person", "weight": 0.6, "icon": "👛"},
    "other-theft": {"name": "Other Theft", "weight": 0.4, "icon": "🛍️"},
    "criminal-damage-arson": {"name": "Criminal Damage", "weight": 0.5, "icon": "🔥"},
    "drugs": {"name": "Drugs", "weight": 0.3, "icon": "💊"},
    "possession-of-weapons": {"name": "Weapons", "weight": 0.8, "icon": "🔪"},
    "public-order": {"name": "Public Order", "weight": 0.3, "icon": "📢"},
    "shoplifting": {"name": "Shoplifting", "weight": 0.2, "icon": "🛒"},
    "anti-social-behaviour": {"name": "Anti-Social Behaviour", "weight": 0.2, "icon": "😤"},
    "bicycle-theft": {"name": "Bicycle Theft", "weight": 0.2, "icon": "🚲"},
    "other-crime": {"name": "Other Crime", "weight": 0.3, "icon": "📋"},
}

# Logo SVG
LOGO_SVG = '''<svg width="28" height="28" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="currentColor" opacity="0.1"/>
  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="none" stroke="currentColor" stroke-width="20" stroke-linejoin="round"/>
  <text x="256" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="160" fill="currentColor">UK</text>
</svg>'''

def slugify(text):
    """Convert text to URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def get_header(title="CrimeSafe UK", description="UK crime statistics and safety scores"):
    """Return HTML header"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="S7uUZGMb9yLeKT16YkQGWumhCd0n70jt19wxR1qrYEc">
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-CK531DR9X9');</script>
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link rel="preconnect" href="https://api.fontshare.com" crossorigin>
    <link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
    <meta name="theme-color" content="#01696F">
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="/" class="nav-logo">
                {LOGO_SVG}
                <span>CrimeSafe UK</span>
            </a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/forces/">Forces</a>
                <a href="/districts/">Districts</a>
                <a href="/safest/">Rankings</a>
                <a href="/about/">About</a>
                <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
            </div>
        </div>
    </nav>
'''

def get_footer():
    """Return HTML footer"""
    return '''
    <footer class="footer">
        <div class="container">
            <p>CrimeSafe UK — Crime statistics from <a href="https://data.police.uk" target="_blank" rel="noopener">data.police.uk</a></p>
            <p style="margin-top: var(--space-2);">Data updated quarterly. Last update: Q1 2026</p>
        </div>
    </footer>
    <script src="/forces_search.js"></script>
    <script src="/neighbourhoods_search.js"></script>
    <script src="/script.js"></script>
</body>
</html>
'''

def generate_homepage(forces_data):
    """Generate the homepage"""
    total_neighbourhoods = sum(len(f['neighbourhoods']) for f in forces_data['forces'])
    
    # Sort forces by neighbourhood count
    forces_sorted = sorted(forces_data['forces'], key=lambda f: len(f['neighbourhoods']), reverse=True)
    
    html = get_header("CrimeSafe UK — UK Crime Statistics & Safety Scores", "Explore crime data and safety scores for neighbourhoods across the UK")
    html += '''
    <main>
        <section class="hero">
            <div class="container">
                <h1>UK Crime Statistics</h1>
                <p class="hero-sub">Explore crime data and safety scores for neighbourhoods across England, Wales, and Northern Ireland</p>
                <div class="search-tabs">
                    <button class="search-tab active" data-panel="searchPanel">Search</button>
                    <button class="search-tab" data-panel="comparePanel">Compare</button>
                </div>
                
                <div class="search-panel active" id="searchPanel">
                    <div class="search-wrap">
                        <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                        <input type="text" class="search-input" id="searchInput" placeholder="Search neighbourhoods, forces..." autocomplete="off">
                        <div class="search-dropdown" id="searchDropdown"></div>
                    </div>
                </div>
                
                <div class="search-panel" id="comparePanel">
                    <div class="compare-wrap">
                        <div class="compare-input-wrap">
                            <input type="text" class="search-input" id="compareCity1" placeholder="First neighbourhood..." autocomplete="off">
                            <div class="search-dropdown" id="compareDropdown1"></div>
                        </div>
                        <span class="compare-vs">vs</span>
                        <div class="compare-input-wrap">
                            <input type="text" class="search-input" id="compareCity2" placeholder="Second neighbourhood..." autocomplete="off">
                            <div class="search-dropdown" id="compareDropdown2"></div>
                        </div>
                        <button class="compare-btn" id="compareBtn" disabled>Compare</button>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="kpi-section">
            <div class="container">
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Police Forces</div>
                        <div class="kpi-value">44</div>
                        <div class="kpi-detail">Across UK</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Neighbourhoods</div>
                        <div class="kpi-value">''' + f'{total_neighbourhoods:,}' + '''</div>
                        <div class="kpi-detail">Coverage areas</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Data Updates</div>
                        <div class="kpi-value">Monthly</div>
                        <div class="kpi-detail">Official police data</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Crime Types</div>
                        <div class="kpi-value">14</div>
                        <div class="kpi-detail">Categories tracked</div>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Rankings Section -->
        <section style="padding: var(--space-8) 0;">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title">UK Crime Rankings</h2>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-6);">
                    <a href="/safest/" class="kpi-card" style="text-decoration: none; text-align: center; padding: var(--space-6);">
                        <div style="font-size: 3rem; margin-bottom: var(--space-2);">🏆</div>
                        <div style="font-size: var(--text-xl); font-weight: 700; color: var(--color-primary);">Safest Places</div>
                        <div style="color: var(--color-text-muted); margin-top: var(--space-2);">Top 100 lowest crime neighbourhoods in the UK</div>
                    </a>
                    <a href="/dangerous/" class="kpi-card" style="text-decoration: none; text-align: center; padding: var(--space-6);">
                        <div style="font-size: 3rem; margin-bottom: var(--space-2);">⚠️</div>
                        <div style="font-size: var(--text-xl); font-weight: 700; color: var(--color-primary);">Highest Crime Areas</div>
                        <div style="color: var(--color-text-muted); margin-top: var(--space-2);">Top 100 highest crime neighbourhoods</div>
                    </a>
                </div>
            </div>
        </section>
        
        <section id="forces-section">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title">Police Forces</h2>
                </div>
                <div class="force-grid">
'''
    
    for force in forces_sorted:
        slug = slugify(force['name'])
        nb_count = len(force['neighbourhoods'])
        html += f'''
                    <a href="/force/{slug}/" class="force-card">
                        <h3>{force['name']}</h3>
                        <div class="meta">{nb_count:,} neighbourhoods</div>
                    </a>
'''
    
    html += '''
                </div>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    return html

def generate_force_page(force, all_forces, rankings_lookup=None):
    """Generate a force detail page"""
    slug = slugify(force['name'])
    if rankings_lookup is None:
        rankings_lookup = {}
    nb_count = len(force['neighbourhoods'])
    
    html = get_header(f"{force['name']} — CrimeSafe UK", f"Crime statistics for {nb_count} neighbourhoods in {force['name']}")
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/forces/">Forces</a> › {force['name']}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{force['name']}</h1>
                <p class="hero-sub">{nb_count:,} neighbourhoods covered</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title">Neighbourhoods</h2>
                </div>
                <div class="force-grid">
'''
    
    for nb in sorted(force['neighbourhoods'], key=lambda n: n['name']):
        nb_slug = slugify(nb['name'])
        nb_id = nb.get('id', nb_slug)
        
        # Try ID-based lookup first, then slug-based
        id_key = f"{force['id']}_{nb_id}"
        slug_key = f"{slug}/{nb_slug}"
        score_data = rankings_lookup.get(id_key) or rankings_lookup.get(slug_key, {})
        score = score_data.get('score')
        grade = score_data.get('grade', '?')
        
        if score is not None:
            score_html = f'<span style="font-weight: 600; color: {"#16a34a" if score >= 60 else "#ca8a04" if score >= 40 else "#dc2626"};">{score}</span>/100'
        else:
            score_html = '<span style="color: var(--color-text-muted);">—</span>'
        
        html += f'''
                    <a href="/neighbourhood/{slug}/{nb_slug}/" class="force-card" style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0;">{nb['name']}</h3>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: var(--text-sm);">{score_html}</div>
                        </div>
                    </a>
'''
    
    html += '''
                </div>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    return html

def generate_forces_index(forces_data):
    """Generate the forces index page"""
    forces_sorted = sorted(forces_data['forces'], key=lambda f: f['name'])
    
    html = get_header("All Police Forces — CrimeSafe UK", "Browse all 44 UK police forces")
    html += '''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Forces
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>UK Police Forces</h1>
                <p class="hero-sub">44 forces covering England, Wales, and Northern Ireland</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="force-grid">
'''
    
    for force in forces_sorted:
        slug = slugify(force['name'])
        nb_count = len(force['neighbourhoods'])
        html += f'''
                    <a href="/force/{slug}/" class="force-card">
                        <h3>{force['name']}</h3>
                        <div class="meta">{nb_count:,} neighbourhoods</div>
                    </a>
'''
    
    html += '''
                </div>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    return html

def main():
    print("Loading data...")
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    print(f"Loaded {len(forces_data['forces'])} forces")
    
    # Load rankings for score lookup (by both ID and slug)
    rankings_lookup = {}
    
    # Load crime data to build ID-based lookup
    crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
    if os.path.exists(crime_dir):
        # First, calculate all weighted crimes for percentile scoring
        all_weighted = []
        crime_data_map = {}
        
        for fname in os.listdir(crime_dir):
            if not fname.endswith('.json'):
                continue
            with open(f'{crime_dir}/{fname}') as f:
                data = json.load(f)
            
            force_id = data.get('force_id', '')
            nb_id = data.get('neighbourhood_id', '')
            nb_name = data.get('neighbourhood_name', '')
            categories = data.get('categories', {})
            
            # Calculate weighted crime
            weighted = 0
            for cat, count in categories.items():
                weight = CRIME_WEIGHTS.get(cat, {}).get('weight', 1.0)
                weighted += count * weight
            
            key = f"{force_id}_{nb_id}"
            crime_data_map[key] = {
                'weighted': weighted,
                'force_id': force_id,
                'nb_id': nb_id,
                'nb_name': nb_name
            }
            all_weighted.append((key, weighted))
        
        # Sort by weighted crime (ascending = lowest crime first)
        all_weighted.sort(key=lambda x: x[1])
        
        # Assign percentile scores
        total = len(all_weighted)
        for i, (key, _) in enumerate(all_weighted):
            percentile = (i / max(1, total - 1)) * 100
            score = round(100 - percentile)
            if score >= 80: grade = 'A'
            elif score >= 60: grade = 'B'
            elif score >= 40: grade = 'C'
            elif score >= 20: grade = 'D'
            else: grade = 'F'
            
            data = crime_data_map[key]
            # Store by force_id + nb_id
            rankings_lookup[key] = {'score': score, 'grade': grade}
            # Also store by slugified names for fallback
            force_slug = slugify(data['force_id'].replace('-', ' '))
            nb_slug = slugify(data['nb_name'])
            rankings_lookup[f"{force_slug}/{nb_slug}"] = {'score': score, 'grade': grade}
        
        print(f"Loaded {len(crime_data_map)} neighbourhood scores")
    
    # Generate JS
    
    # Generate homepage
    print("Generating homepage...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(f"{OUTPUT_DIR}/index.html", 'w') as f:
        f.write(generate_homepage(forces_data))
    
    # Generate forces index
    print("Generating forces index...")
    os.makedirs(f"{OUTPUT_DIR}/forces", exist_ok=True)
    with open(f"{OUTPUT_DIR}/forces/index.html", 'w') as f:
        f.write(generate_forces_index(forces_data))
    
    # Generate force pages
    print("Generating force pages...")
    for force in forces_data['forces']:
        slug = slugify(force['name'])
        os.makedirs(f"{OUTPUT_DIR}/force/{slug}", exist_ok=True)
        with open(f"{OUTPUT_DIR}/force/{slug}/index.html", 'w') as f:
            f.write(generate_force_page(force, forces_data, rankings_lookup))
    
    # Summary
    total_pages = 1 + 1 + len(forces_data['forces'])
    print(f"\n{'='*50}")
    print(f"Generated {total_pages} pages")
    print(f"  - Homepage: /index.html")
    print(f"  - Forces index: /forces/index.html")
    print(f"  - Force pages: {len(forces_data['forces'])}")

if __name__ == "__main__":
    main()
