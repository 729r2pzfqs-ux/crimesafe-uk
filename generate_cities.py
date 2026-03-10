#!/usr/bin/env python3
"""Generate city/town landing pages for CrimeSafe UK."""

import json
import os
import re
from pathlib import Path

# Top UK cities and towns by population/search volume
CITIES = {
    "london": {"name": "London", "force": "metropolitan", "force_name": "Metropolitan Police Service", "show_all": True},
    "birmingham": {"name": "Birmingham", "force": "west-midlands", "force_name": "West Midlands Police"},
    "manchester": {"name": "Manchester", "force": "greater-manchester", "force_name": "Greater Manchester Police"},
    "leeds": {"name": "Leeds", "force": "west-yorkshire", "force_name": "West Yorkshire Police"},
    "liverpool": {"name": "Liverpool", "force": "merseyside", "force_name": "Merseyside Police"},
    "bristol": {"name": "Bristol", "force": "avon-and-somerset", "force_name": "Avon and Somerset Constabulary"},
    "sheffield": {"name": "Sheffield", "force": "south-yorkshire", "force_name": "South Yorkshire Police"},
    "newcastle": {"name": "Newcastle", "force": "northumbria", "force_name": "Northumbria Police"},
    "nottingham": {"name": "Nottingham", "force": "nottinghamshire", "force_name": "Nottinghamshire Police"},
    "cardiff": {"name": "Cardiff", "force": "south-wales", "force_name": "South Wales Police"},
    # Note: Edinburgh/Glasgow removed - Police Scotland doesn't use data.police.uk
    "leicester": {"name": "Leicester", "force": "leicestershire", "force_name": "Leicestershire Police"},
    "coventry": {"name": "Coventry", "force": "west-midlands", "force_name": "West Midlands Police"},
    "bradford": {"name": "Bradford", "force": "west-yorkshire", "force_name": "West Yorkshire Police"},
    # Note: Belfast removed - PSNI uses district names (Strandtown, etc.) not "Belfast"
    "brighton": {"name": "Brighton", "force": "sussex", "force_name": "Sussex Police"},
    "hull": {"name": "Hull", "force": "humberside", "force_name": "Humberside Police"},
    "plymouth": {"name": "Plymouth", "force": "devon-and-cornwall", "force_name": "Devon & Cornwall Police"},
    "stoke-on-trent": {"name": "Stoke-on-Trent", "force": "staffordshire", "force_name": "Staffordshire Police"},
    "wolverhampton": {"name": "Wolverhampton", "force": "west-midlands", "force_name": "West Midlands Police"},
    "derby": {"name": "Derby", "force": "derbyshire", "force_name": "Derbyshire Constabulary"},
    "southampton": {"name": "Southampton", "force": "hampshire", "force_name": "Hampshire Constabulary"},
    "portsmouth": {"name": "Portsmouth", "force": "hampshire", "force_name": "Hampshire Constabulary"},
    "oxford": {"name": "Oxford", "force": "thames-valley", "force_name": "Thames Valley Police"},
    "cambridge": {"name": "Cambridge", "force": "cambridgeshire", "force_name": "Cambridgeshire Constabulary"},
    "york": {"name": "York", "force": "north-yorkshire", "force_name": "North Yorkshire Police"},
    "reading": {"name": "Reading", "force": "thames-valley", "force_name": "Thames Valley Police"},
    "norwich": {"name": "Norwich", "force": "norfolk", "force_name": "Norfolk Constabulary"},
    "swansea": {"name": "Swansea", "force": "south-wales", "force_name": "South Wales Police"},
    "luton": {"name": "Luton", "force": "bedfordshire", "force_name": "Bedfordshire Police"},
    "milton-keynes": {"name": "Milton Keynes", "force": "thames-valley", "force_name": "Thames Valley Police"},
    "warrington": {"name": "Warrington", "force": "cheshire", "force_name": "Cheshire Constabulary"},
    "swindon": {"name": "Swindon", "force": "wiltshire", "force_name": "Wiltshire Police"},
    "peterborough": {"name": "Peterborough", "force": "cambridgeshire", "force_name": "Cambridgeshire Constabulary"},
    "exeter": {"name": "Exeter", "force": "devon-and-cornwall", "force_name": "Devon & Cornwall Police"},
    "bath": {"name": "Bath", "force": "avon-and-somerset", "force_name": "Avon and Somerset Constabulary"},
    "cheltenham": {"name": "Cheltenham", "force": "gloucestershire", "force_name": "Gloucestershire Constabulary"},
    "gloucester": {"name": "Gloucester", "force": "gloucestershire", "force_name": "Gloucestershire Constabulary"},
    "lincoln": {"name": "Lincoln", "force": "lincolnshire", "force_name": "Lincolnshire Police"},
}

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

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
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="website">
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="/" class="nav-logo">
                <svg width="28" height="28" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="currentColor" opacity="0.1"/>
  <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="none" stroke="currentColor" stroke-width="20" stroke-linejoin="round"/>
  <text x="256" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="160" fill="currentColor">UK</text>
</svg>
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
    return '''
    <footer class="footer">
        <div class="container">
            <p>&copy; 2026 CrimeSafe UK. Data from <a href="https://data.police.uk">data.police.uk</a> (Open Government Licence)</p>
            <p style="margin-top: var(--space-2);">
                <a href="/about/">About</a> · 
                <a href="/privacy/">Privacy</a>
            </p>
        </div>
    </footer>
    <script>
        const toggle = document.getElementById('themeToggle');
        const html = document.documentElement;
        const stored = localStorage.getItem('theme');
        if (stored) html.setAttribute('data-theme', stored);
        else if (window.matchMedia('(prefers-color-scheme: dark)').matches) html.setAttribute('data-theme', 'dark');
        toggle.textContent = html.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            toggle.textContent = next === 'dark' ? '☀️' : '🌙';
        });
    </script>
</body>
</html>'''

def find_neighbourhoods_for_city(city_slug, city_name, force_id, forces_data, crime_data):
    """Find neighbourhoods that match the city name."""
    matching = []
    
    for force in forces_data['forces']:
        if force['id'] == force_id:
            for nb in force.get('neighbourhoods', []):
                nb_name = nb.get('name', '').lower()
                nb_id = nb.get('id', '')
                
                # Match if city name is in neighbourhood name
                if city_name.lower() in nb_name or city_slug in slugify(nb_name):
                    # Get crime data
                    key = f"{force_id}_{nb_id}"
                    crime = crime_data.get(key, {})
                    matching.append({
                        'name': nb['name'],
                        'slug': slugify(nb['name']),
                        'force_slug': slugify(force['name']),
                        'score': crime.get('score', 0),
                        'total_crimes': crime.get('total_crimes', 0)
                    })
    
    # Sort by score descending (safest first)
    matching.sort(key=lambda x: x['score'], reverse=True)
    return matching

def generate_city_page(city_slug, city_info, neighbourhoods, crime_stats):
    """Generate a city landing page."""
    city_name = city_info['name']
    force_name = city_info['force_name']
    force_slug = slugify(force_name)
    
    title = f"Crime in {city_name} — Safety Statistics | CrimeSafe UK"
    desc = f"Is {city_name} safe? View crime statistics, safety scores, and neighbourhood data for {city_name}. Compare areas and find the safest places to live."
    
    html = get_header(title, desc)
    
    # Calculate city-wide stats
    total_crimes = sum(n.get('total_crimes', 0) for n in neighbourhoods)
    avg_score = round(sum(n.get('score', 0) for n in neighbourhoods) / max(1, len(neighbourhoods)))
    
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/cities/">Cities</a> › {city_name}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>Crime in {city_name}</h1>
                <p class="hero-sub">Explore crime statistics and safety scores for {city_name} neighbourhoods</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{len(neighbourhoods)}</div>
                        <div class="stat-label">Neighbourhoods</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_crimes:,}</div>
                        <div class="stat-label">Total Crimes (Monthly)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{avg_score}</div>
                        <div class="stat-label">Average Safety Score</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label" style="margin-bottom: var(--space-2);">Police Force</div>
                        <a href="/force/{force_slug}/" style="color: var(--color-primary); font-weight: 600;">{force_name}</a>
                    </div>
                </div>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="stat-card" style="margin-bottom: var(--space-6);">
                    <h2 style="margin: 0; color: var(--color-primary);">Neighbourhoods in {city_name}</h2>
                    <p style="margin-top: var(--space-2); color: var(--color-text-muted);">Sorted by safety score (safest first)</p>
                </div>
                <div class="force-grid">'''
    
    for nb in neighbourhoods:
        score = nb.get('score', 0)
        if score >= 60:
            color = "#16a34a"
        elif score >= 40:
            color = "#ca8a04"
        else:
            color = "#dc2626"
        
        html += f'''
                    <a href="/neighbourhood/{nb['force_slug']}/{nb['slug']}/" class="force-card" style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0;">{nb['name']}</h3>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: var(--text-sm);"><span style="font-weight: 600; color: {color};">{score}</span>/100</div>
                        </div>
                    </a>'''
    
    html += '''
                </div>
            </div>
        </section>
        
        <section style="padding: var(--space-8) 0;">
            <div class="container">
                <div class="stat-card">
                    <h2>Is ''' + city_name + ''' Safe?</h2>
                    <p style="margin-top: var(--space-4);">''' + city_name + f''' has an average safety score of <strong>{avg_score}/100</strong> across its {len(neighbourhoods)} neighbourhoods. '''
    
    if avg_score >= 60:
        html += f'''This indicates that {city_name} is generally a <strong>safe city</strong> to live in or visit.'''
    elif avg_score >= 40:
        html += f'''This indicates <strong>moderate safety levels</strong>. Some areas are safer than others - check individual neighbourhood scores.'''
    else:
        html += f'''This indicates <strong>higher than average crime rates</strong>. Some areas have lower crime - check individual neighbourhood scores for safer options.'''
    
    html += '''</p>
                    <p style="margin-top: var(--space-3);">Data is sourced from the official <a href="https://data.police.uk">data.police.uk</a> API and updated monthly.</p>
                </div>
            </div>
        </section>
    </main>
'''
    
    html += get_footer()
    return html

def load_crime_scores():
    """Load crime data and calculate scores."""
    crime_dir = 'data/neighbourhood_crimes'
    
    CRIME_WEIGHTS = {
        'violent-crime': 2.0, 'robbery': 1.8, 'burglary': 1.5,
        'vehicle-crime': 1.3, 'criminal-damage-arson': 1.2,
        'drugs': 1.1, 'public-order': 1.0, 'shoplifting': 0.8,
        'other-theft': 0.9, 'theft-from-the-person': 1.0,
        'bicycle-theft': 0.7, 'anti-social-behaviour': 0.5,
        'possession-of-weapons': 1.5, 'other-crime': 1.0
    }
    
    all_weighted = []
    crime_data = {}
    
    for fname in os.listdir(crime_dir):
        if not fname.endswith('.json'):
            continue
        with open(f'{crime_dir}/{fname}') as f:
            data = json.load(f)
        
        force_id = data.get('force_id', '')
        nb_id = data.get('neighbourhood_id', '')
        categories = data.get('categories', {})
        total_crimes = data.get('total_crimes', 0)
        
        weighted = sum(count * CRIME_WEIGHTS.get(cat, 1.0) for cat, count in categories.items())
        key = f'{force_id}_{nb_id}'
        crime_data[key] = {'weighted': weighted, 'total_crimes': total_crimes}
        all_weighted.append((key, weighted))
    
    # Assign percentile scores
    all_weighted.sort(key=lambda x: x[1])
    total = len(all_weighted)
    for i, (key, _) in enumerate(all_weighted):
        percentile = (i / max(1, total - 1)) * 100
        score = round(100 - percentile)
        crime_data[key]['score'] = score
    
    return crime_data

def main():
    """Generate all city pages."""
    
    # Load data
    with open('data/forces.json') as f:
        forces_data = json.load(f)
    
    crime_data = load_crime_scores()
    
    # Create output directory
    Path('city').mkdir(exist_ok=True)
    
    generated = 0
    
    for city_slug, city_info in CITIES.items():
        neighbourhoods = []
        
        # For cities with show_all flag, get all force neighbourhoods
        if city_info.get('show_all'):
            for force in forces_data['forces']:
                if force['id'] == city_info['force']:
                    for nb in force.get('neighbourhoods', []):
                        nb_id = nb.get('id', '')
                        key = f"{city_info['force']}_{nb_id}"
                        crime = crime_data.get(key, {})
                        neighbourhoods.append({
                            'name': nb['name'],
                            'slug': slugify(nb['name']),
                            'force_slug': slugify(force['name']),
                            'score': crime.get('score', 0),
                            'total_crimes': crime.get('total_crimes', 0)
                        })
                    neighbourhoods.sort(key=lambda x: x['score'], reverse=True)
                    break
        else:
            # Find matching neighbourhoods by name
            neighbourhoods = find_neighbourhoods_for_city(
                city_slug, city_info['name'], city_info['force'], forces_data, crime_data
            )
        
        if not neighbourhoods:
            # Fallback: get all neighbourhoods for the force
            for force in forces_data['forces']:
                if force['id'] == city_info['force']:
                    for nb in force.get('neighbourhoods', []):
                        nb_id = nb.get('id', '')
                        key = f"{city_info['force']}_{nb_id}"
                        crime = crime_data.get(key, {})
                        neighbourhoods.append({
                            'name': nb['name'],
                            'slug': slugify(nb['name']),
                            'force_slug': slugify(force['name']),
                            'score': crime.get('score', 0),
                            'total_crimes': crime.get('total_crimes', 0)
                        })
                    neighbourhoods.sort(key=lambda x: x['score'], reverse=True)
                    break
        
        if neighbourhoods:
            html = generate_city_page(city_slug, city_info, neighbourhoods, crime_data)
            
            page_dir = Path(f'city/{city_slug}')
            page_dir.mkdir(exist_ok=True)
            
            with open(page_dir / 'index.html', 'w') as f:
                f.write(html)
            
            generated += 1
            print(f"  {city_info['name']}: {len(neighbourhoods)} neighbourhoods")
    
    # Generate cities index page
    generate_cities_index()
    
    print(f"\n✅ Generated {generated} city pages")

def generate_cities_index():
    """Generate the cities index page."""
    html = get_header("UK Cities Crime Statistics | CrimeSafe UK", 
                      "Browse crime statistics for major UK cities and towns. Compare safety scores and find the safest areas.")
    
    html += '''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Cities
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>UK Cities</h1>
                <p class="hero-sub">Crime statistics for major UK cities and towns</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="force-grid">'''
    
    for city_slug, city_info in sorted(CITIES.items(), key=lambda x: x[1]['name']):
        html += f'''
                    <a href="/city/{city_slug}/" class="force-card">
                        <h3>{city_info['name']}</h3>
                        <p style="color: var(--color-text-muted); font-size: var(--text-sm);">{city_info['force_name']}</p>
                    </a>'''
    
    html += '''
                </div>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    
    Path('city').mkdir(exist_ok=True)
    with open('city/index.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()
