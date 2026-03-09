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

def slugify(text):
    """Convert text to URL-safe slug"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def get_css():
    """Return the site CSS"""
    return '''
:root {
    --bg: #ffffff;
    --bg-card: #f8f9fa;
    --text: #1a1a2e;
    --text-muted: #6c757d;
    --border: #dee2e6;
    --primary: #0d6efd;
    --success: #198754;
    --warning: #ffc107;
    --danger: #dc3545;
    --safe: #198754;
    --moderate: #ffc107;
    --unsafe: #dc3545;
}

[data-theme="dark"] {
    --bg: #1a1a2e;
    --bg-card: #16213e;
    --text: #eaeaea;
    --text-muted: #adb5bd;
    --border: #2d3748;
    --primary: #4dabf7;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

.container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }

header {
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.header-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
    text-decoration: none;
}

.logo span { color: var(--text); }

nav a {
    color: var(--text-muted);
    text-decoration: none;
    margin-left: 1.5rem;
    font-size: 0.95rem;
}

nav a:hover { color: var(--primary); }

.theme-toggle {
    background: none;
    border: 1px solid var(--border);
    border-radius: 50%;
    width: 36px;
    height: 36px;
    cursor: pointer;
    font-size: 1.1rem;
    margin-left: 1rem;
}

.hero {
    text-align: center;
    padding: 3rem 1rem;
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg) 100%);
}

.hero h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
.hero p { color: var(--text-muted); font-size: 1.1rem; }

.search-box {
    max-width: 500px;
    margin: 2rem auto 0;
    position: relative;
}

.search-box input {
    width: 100%;
    padding: 1rem 1.5rem;
    font-size: 1rem;
    border: 2px solid var(--border);
    border-radius: 50px;
    background: var(--bg);
    color: var(--text);
}

.search-box input:focus {
    outline: none;
    border-color: var(--primary);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    padding: 2rem 0;
}

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
}

.stat-card .number {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary);
}

.stat-card .label {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.force-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
    padding: 2rem 0;
}

.force-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    text-decoration: none;
    color: var(--text);
    transition: transform 0.2s, box-shadow 0.2s;
}

.force-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.force-card h3 {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}

.force-card .meta {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.score-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}

.score-safe { background: var(--safe); color: white; }
.score-moderate { background: var(--warning); color: #333; }
.score-unsafe { background: var(--danger); color: white; }

section { padding: 2rem 0; }
section h2 { margin-bottom: 1.5rem; font-size: 1.75rem; }

.breadcrumb {
    padding: 1rem 0;
    color: var(--text-muted);
    font-size: 0.9rem;
}

.breadcrumb a { color: var(--primary); text-decoration: none; }

footer {
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    padding: 2rem 0;
    margin-top: 3rem;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.9rem;
}

footer a { color: var(--primary); text-decoration: none; }

@media (max-width: 768px) {
    .hero h1 { font-size: 1.75rem; }
    .header-inner { flex-wrap: wrap; }
    nav { margin-top: 0.5rem; width: 100%; }
    nav a { margin: 0 1rem 0 0; }
}
'''

def get_js():
    """Return the site JavaScript"""
    return '''
// Theme toggle
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
'''

def get_header(title="CrimeSafe UK"):
    """Return HTML header"""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
    <meta name="theme-color" content="#01696F">
</head>
<body>
    <header>
        <div class="container header-inner">
            <a href="/" class="logo">🛡️ Crime<span>Safe</span> UK</a>
            <nav>
                <a href="/">Home</a>
                <a href="/forces/">Forces</a>
                <a href="/about/">About</a>
            </nav>
            <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
        </div>
    </header>
'''

def get_footer():
    """Return HTML footer"""
    return f'''
    <footer>
        <div class="container">
            <p>CrimeSafe UK — Crime statistics from <a href="https://data.police.uk" target="_blank">data.police.uk</a></p>
            <p style="margin-top: 0.5rem;">Data updated monthly. Last update: January 2026</p>
        </div>
    </footer>
    <script src="/script.js"></script>
</body>
</html>
'''

def generate_homepage(forces_data):
    """Generate the homepage"""
    total_neighbourhoods = sum(len(f['neighbourhoods']) for f in forces_data['forces'])
    
    # Sort forces by neighbourhood count
    forces_sorted = sorted(forces_data['forces'], key=lambda f: len(f['neighbourhoods']), reverse=True)
    
    html = get_header("CrimeSafe UK — UK Crime Statistics & Safety Scores")
    html += '''
    <main>
        <section class="hero">
            <div class="container">
                <h1>🛡️ UK Crime Statistics</h1>
                <p>Explore crime data and safety scores for neighbourhoods across the UK</p>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search neighbourhoods, forces..." autocomplete="off">
                </div>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="number">44</div>
                        <div class="label">Police Forces</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">''' + f'{total_neighbourhoods:,}' + '''</div>
                        <div class="label">Neighbourhoods</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">Monthly</div>
                        <div class="label">Data Updates</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">14</div>
                        <div class="label">Crime Categories</div>
                    </div>
                </div>
            </div>
        </section>
        
        <section id="forces-section">
            <div class="container">
                <h2>Police Forces</h2>
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

def generate_force_page(force, all_forces):
    """Generate a force detail page"""
    slug = slugify(force['name'])
    nb_count = len(force['neighbourhoods'])
    
    html = get_header(f"{force['name']} — CrimeSafe UK")
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/forces/">Forces</a> › {force['name']}
            </div>
        </div>
        
        <section class="hero" style="padding: 2rem 1rem;">
            <div class="container">
                <h1>{force['name']}</h1>
                <p>{nb_count:,} neighbourhoods covered</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <h2>Neighbourhoods</h2>
                <div class="force-grid">
'''
    
    for nb in sorted(force['neighbourhoods'], key=lambda n: n['name']):
        nb_slug = slugify(nb['name'])
        html += f'''
                    <a href="/neighbourhood/{slug}/{nb_slug}/" class="force-card">
                        <h3>{nb['name']}</h3>
                        <div class="meta">{force['name']}</div>
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
    
    html = get_header("All Police Forces — CrimeSafe UK")
    html += '''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Forces
            </div>
        </div>
        
        <section class="hero" style="padding: 2rem 1rem;">
            <div class="container">
                <h1>UK Police Forces</h1>
                <p>44 forces covering England, Wales, and Northern Ireland</p>
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
    
    # Generate CSS and JS
    print("Generating CSS and JS...")
    with open(f"{OUTPUT_DIR}/style.css", 'w') as f:
        f.write(get_css())
    with open(f"{OUTPUT_DIR}/script.js", 'w') as f:
        f.write(get_js())
    
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
            f.write(generate_force_page(force, forces_data))
    
    # Summary
    total_pages = 1 + 1 + len(forces_data['forces'])  # home + forces index + force pages
    print(f"\n{'='*50}")
    print(f"Generated {total_pages} pages")
    print(f"  - Homepage: /index.html")
    print(f"  - Forces index: /forces/index.html")
    print(f"  - Force pages: {len(forces_data['forces'])}")

if __name__ == "__main__":
    main()
