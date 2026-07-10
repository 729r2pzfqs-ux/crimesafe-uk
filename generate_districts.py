#!/usr/bin/env python3
"""
Generate district pages for CrimeSafe UK
"""

import json
import os
import re

DATA_DIR = "data"
OUTPUT_DIR = "."

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    # Don't collapse multiple dashes - they come from " - " in names
    return text.strip('-')

def social_meta(title, description, canonical):
    if not canonical:
        return ""
    return f'''    <link rel="canonical" href="{canonical}">
    <link rel="alternate" hreflang="en" href="{canonical}">
    <link rel="alternate" hreflang="x-default" href="{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:site_name" content="CrimeSafe UK">
    <meta property="og:image" content="https://crimesafe.uk/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="https://crimesafe.uk/og-image.png">
'''

def get_header(title, description, canonical=None, extra_head=""):
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
{social_meta(title, description, canonical)}{extra_head}    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet" media="print" onload="this.media='all'"><noscript><link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet"></noscript>
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <meta name="theme-color" content="#01696F">
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>
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
                <a href="/districts/">Districts</a>
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
            <p>CrimeSafe UK — Crime statistics from <a href="https://data.police.uk" target="_blank" rel="noopener">data.police.uk</a></p>
            <p style="margin-top: var(--space-2);">Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/" target="_blank" rel="license noopener">Open Government Licence v3.0</a>.</p>
            <p style="margin-top: var(--space-2);">Data updated monthly. Last update: April 2026</p>
        </div>
    </footer>
    <script src="/forces_search.js"></script>
    <script src="/neighbourhoods_search.js"></script>
    <script src="/script.js"></script>
</body>
</html>
'''

def get_score_class(score):
    if score is None: return 'score-na'
    if score >= 60: return 'score-green'
    if score >= 40: return 'score-amber'
    return 'score-red'

def generate_district_page(district, rankings_lookup):
    """Generate a district detail page"""
    district_name = district['district'].title()
    force_name = district['force']
    force_slug = slugify(force_name)
    district_slug = slugify(district['district'])
    nb_count = district['neighbourhood_count']
    neighbourhoods = district['neighbourhoods']
    nb_word = "neighbourhood" if nb_count == 1 else "neighbourhoods"

    desc = f"{district_name} crime statistics: safety scores for {nb_count} police {nb_word} in {force_name}. See the safest areas and monthly crime trends from police.uk."
    _title = f"{district_name} Crime Statistics — CrimeSafe UK"
    _url = f"https://crimesafe.uk/district/{district_slug}/"
    _ld = '    <script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "WebPage", "name": _title,
         "description": desc, "url": _url,
         "isPartOf": {"@type": "WebSite", "name": "CrimeSafe UK", "url": "https://crimesafe.uk/"}},
        ensure_ascii=False, separators=(',', ':')) + '</script>\n'
    _ld += '<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://crimesafe.uk/"},
            {"@type": "ListItem", "position": 2, "name": "Districts", "item": "https://crimesafe.uk/districts/"},
            {"@type": "ListItem", "position": 3, "name": district_name}]},
        ensure_ascii=False) + '</script>\n'
    html = get_header(_title, desc, canonical=_url, extra_head=_ld)
    
    html += f'''
    <main id="main-content">
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/districts/">Districts</a> › {district_name}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{district_name}</h1>
                <p class="hero-sub">{force_name} • {nb_count} {nb_word}</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container">
                <div class="section-header">
                    <h2 class="section-title">Neighbourhoods in {district_name}</h2>
                </div>
                <div class="force-grid">
'''
    
    for nb in sorted(neighbourhoods, key=lambda n: n['name']):
        nb_slug = slugify(nb['name'])
        # Look up score
        key = f"{force_slug}_{nb_slug}"
        ranking = rankings_lookup.get(key, {})
        score = ranking.get('score')
        score_class = get_score_class(score)
        score_display = score if score is not None else '—'
        
        html += f'''
                    <a href="/neighbourhood/{force_slug}/{nb_slug}/" class="force-card">
                        <div class="card-header">
                            <h3>{nb['name']}</h3>
                            <span class="score-badge {score_class}">{score_display}</span>
                        </div>
                        <div class="meta">{district_name}</div>
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

def generate_districts_index(districts):
    """Generate the districts index page"""
    districts_sorted = sorted(districts, key=lambda d: d['district'])
    
    _crumbs = '<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://crimesafe.uk/"},
            {"@type": "ListItem", "position": 2, "name": "Districts"}]},
        ensure_ascii=False) + '</script>\n'
    html = get_header("UK Districts — CrimeSafe UK", "Browse crime statistics by district across the UK",
                      canonical="https://crimesafe.uk/districts/", extra_head=_crumbs)
    html += f'''
    <main id="main-content">
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Districts
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>UK Districts</h1>
                <p class="hero-sub">{len(districts)} districts across England and Wales</p>
            </div>
        </section>
        
        <section>
            <div class="container">
                <div class="force-grid">
'''
    
    for d in districts_sorted:
        district_slug = slugify(d['district'])
        html += f'''
                    <a href="/district/{district_slug}/" class="force-card">
                        <h3>{d['district'].title()}</h3>
                        <div class="meta">{d['force']} • {d['neighbourhood_count']} neighbourhood{'' if d['neighbourhood_count'] == 1 else 's'}</div>
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
    print("Loading districts data...")
    with open(f"{DATA_DIR}/districts.json") as f:
        districts = json.load(f)
    
    print(f"Loaded {len(districts)} districts")
    
    # Load rankings for scores
    print("Loading rankings...")
    with open(f"{DATA_DIR}/rankings.json") as f:
        rankings = json.load(f)
    
    # Build lookup by force_slug + nb_slug
    rankings_lookup = {}
    for r in rankings:
        key = f"{r.get('force_slug', '')}_{r.get('nb_slug', '')}"
        rankings_lookup[key] = r
    print(f"Loaded {len(rankings_lookup)} neighbourhood scores")
    
    # Generate districts index
    print("Generating districts index...")
    os.makedirs(f"{OUTPUT_DIR}/districts", exist_ok=True)
    with open(f"{OUTPUT_DIR}/districts/index.html", 'w') as f:
        f.write(generate_districts_index(districts))
    
    # Generate district pages
    print("Generating district pages...")
    for d in districts:
        district_slug = slugify(d['district'])
        os.makedirs(f"{OUTPUT_DIR}/district/{district_slug}", exist_ok=True)
        with open(f"{OUTPUT_DIR}/district/{district_slug}/index.html", 'w') as f:
            f.write(generate_district_page(d, rankings_lookup))
    
    print(f"\n{'='*50}")
    print(f"Generated {len(districts) + 1} pages")
    print(f"  - Districts index: /districts/index.html")
    print(f"  - District pages: {len(districts)}")

if __name__ == "__main__":
    main()
