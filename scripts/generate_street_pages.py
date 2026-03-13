#!/usr/bin/env python3
"""
Generate street pages using cached crime data and site template.
"""
import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / 'data'
STREETS_DIR = Path(__file__).parent.parent / 'streets'

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-CK531DR9X9');</script>
    <title>{street_name} Crime Statistics | Is {street_name} Safe? | CrimeSafe UK</title>
    <meta name="description" content="Is {street_name} safe? View real-time crime statistics, safety score of {score}/100, and recent incidents for {street_name}, {city}. Updated with official UK police data.">
    <link rel="canonical" href="https://crimesafe.uk/streets/{slug}/">
    
    <meta property="og:title" content="{street_name} Crime Statistics | CrimeSafe UK">
    <meta property="og:description" content="Safety score: {score}/100. {total_crimes} crimes recorded. View detailed crime breakdown for {street_name}.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://crimesafe.uk/streets/{slug}/">
    
    <link rel="preconnect" href="https://api.fontshare.com" crossorigin>
    <link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <meta name="theme-color" content="#01696F">
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "{street_name} Crime Statistics",
        "description": "Crime statistics and safety information for {street_name}, {city}",
        "url": "https://crimesafe.uk/streets/{slug}/",
        "isPartOf": {{
            "@type": "WebSite",
            "name": "CrimeSafe UK",
            "url": "https://crimesafe.uk"
        }},
        "mainEntity": {{
            "@type": "Place",
            "name": "{street_name}",
            "address": {{
                "@type": "PostalAddress",
                "streetAddress": "{street_name}",
                "addressLocality": "{city}",
                "addressCountry": "GB"
            }}
        }}
    }}
    </script>
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {{
                "@type": "Question",
                "name": "Is {street_name} safe?",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "{street_name} has a safety score of {score}/100 based on recent crime data. There were {total_crimes} crimes recorded in the area last month."
                }}
            }},
            {{
                "@type": "Question",
                "name": "What is the crime rate on {street_name}?",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "{total_crimes} crimes were reported near {street_name} in the most recent month. The most common crime type is {top_crime_formatted}."
                }}
            }},
            {{
                "@type": "Question",
                "name": "Is {street_name} safe at night?",
                "acceptedAnswer": {{
                    "@type": "Answer",
                    "text": "Like many urban areas, safety on {street_name} varies by time of day. We recommend staying in well-lit areas and being aware of your surroundings, especially after dark."
                }}
            }}
        ]
    }}
    </script>
</head>
<body>
    <nav class="nav">
        <div class="nav-inner">
            <a href="/" class="nav-logo">
                <svg width="28" height="28" viewBox="0 0 512 512" fill="none">
                    <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="currentColor" opacity="0.1"/>
                    <path d="M256 52L88 140v120c0 104 72 192 168 224 96-32 168-120 168-224V140L256 52z" fill="none" stroke="currentColor" stroke-width="20" stroke-linejoin="round"/>
                    <text x="256" y="320" text-anchor="middle" font-family="Arial" font-weight="bold" font-size="160" fill="currentColor">UK</text>
                </svg>
                <span>CrimeSafe UK</span>
            </a>
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/streets/">Streets</a>
                <a href="/forces/">Forces</a>
                <a href="/maps/">Maps</a>
                <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
            </div>
        </div>
    </nav>

    <main class="container" style="padding-top: var(--space-8); padding-bottom: var(--space-16);">
        <nav class="breadcrumb" style="margin-bottom: var(--space-6);">
            <a href="/">Home</a> › <a href="/streets/">Streets</a> › <span>{street_name}</span>
        </nav>

        <header style="margin-bottom: var(--space-8);">
            <h1 style="font-size: var(--text-2xl); margin-bottom: var(--space-2);">{street_name} Crime Statistics</h1>
            <p style="color: var(--color-text-muted); font-size: var(--text-lg);">{city}, United Kingdom</p>
        </header>

        <div class="kpi-grid" style="margin-bottom: var(--space-8);">
            <div class="kpi-card">
                <div class="kpi-label">Safety Score</div>
                <div class="kpi-value" style="color: {score_color};">{score}</div>
                <div class="kpi-detail">out of 100</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Crimes</div>
                <div class="kpi-value">{total_crimes}</div>
                <div class="kpi-detail">within 1 mile ({month})</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Most Common</div>
                <div class="kpi-value" style="font-size: var(--text-lg);">{top_crime_formatted}</div>
                <div class="kpi-detail">crime type</div>
            </div>
        </div>

        <section style="margin-bottom: var(--space-8);">
            <h2 style="font-size: var(--text-xl); margin-bottom: var(--space-4);">Crime Breakdown</h2>
            <div class="card" style="padding: var(--space-5);">
                {crime_breakdown_html}
            </div>
        </section>

        <section style="margin-bottom: var(--space-8);">
            <h2 style="font-size: var(--text-xl); margin-bottom: var(--space-4);">Is {street_name} Safe?</h2>
            <div class="card" style="padding: var(--space-5);">
                <p style="margin-bottom: var(--space-4);">
                    Based on the latest police data, <strong>{street_name}</strong> has a safety score of 
                    <strong style="color: {score_color};">{score}/100</strong>. 
                    {safety_text}
                </p>
                <p>
                    The most common crime type in this area is <strong>{top_crime_formatted}</strong>, 
                    accounting for a significant portion of recorded incidents.
                </p>
            </div>
        </section>

        <section style="margin-bottom: var(--space-8);">
            <a href="/maps/street-crime/?lat={lat}&lng={lng}" class="card" style="display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5); text-decoration: none; background: linear-gradient(135deg, var(--color-primary) 0%, #0891b2 100%); color: white; border-radius: var(--radius-lg);">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="10" r="3"/>
                    <path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/>
                </svg>
                <div>
                    <div style="font-weight: 600; font-size: var(--text-lg);">View on Interactive Map</div>
                    <div style="opacity: 0.9; font-size: var(--text-sm);">See exact crime locations around {street_name}</div>
                </div>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-left: auto;">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
            </a>
        </section>

        <section style="margin-bottom: var(--space-8);">
            <h2 style="font-size: var(--text-xl); margin-bottom: var(--space-4);">Safety Tips for {street_name}</h2>
            <div class="card" style="padding: var(--space-5);">
                <ul style="list-style: none; display: flex; flex-direction: column; gap: var(--space-3);">
                    <li style="display: flex; gap: var(--space-2); align-items: flex-start;">
                        <span style="color: var(--color-success);">✓</span>
                        <span>Stay aware of your surroundings, especially at night</span>
                    </li>
                    <li style="display: flex; gap: var(--space-2); align-items: flex-start;">
                        <span style="color: var(--color-success);">✓</span>
                        <span>Keep valuables secure and out of sight</span>
                    </li>
                    <li style="display: flex; gap: var(--space-2); align-items: flex-start;">
                        <span style="color: var(--color-success);">✓</span>
                        <span>Stick to well-lit areas when walking after dark</span>
                    </li>
                    <li style="display: flex; gap: var(--space-2); align-items: flex-start;">
                        <span style="color: var(--color-success);">✓</span>
                        <span>Report suspicious activity to local police (dial 101 for non-emergencies)</span>
                    </li>
                </ul>
            </div>
        </section>

        <section>
            <h2 style="font-size: var(--text-xl); margin-bottom: var(--space-4);">Frequently Asked Questions</h2>
            <div style="display: flex; flex-direction: column; gap: var(--space-4);">
                <div class="card" style="padding: var(--space-5);">
                    <h3 style="font-weight: 600; margin-bottom: var(--space-2);">Is {street_name} safe?</h3>
                    <p style="color: var(--color-text-muted);">
                        {street_name} has a safety score of {score}/100 based on recent crime data. 
                        There were {total_crimes} crimes recorded in the area last month.
                    </p>
                </div>
                <div class="card" style="padding: var(--space-5);">
                    <h3 style="font-weight: 600; margin-bottom: var(--space-2);">What crimes are most common on {street_name}?</h3>
                    <p style="color: var(--color-text-muted);">
                        The most frequently reported crime type is {top_crime_formatted}. 
                        See the crime breakdown above for full details.
                    </p>
                </div>
                <div class="card" style="padding: var(--space-5);">
                    <h3 style="font-weight: 600; margin-bottom: var(--space-2);">Is {street_name} safe at night?</h3>
                    <p style="color: var(--color-text-muted);">
                        Like many urban areas, safety on {street_name} may vary by time of day. 
                        We recommend staying in well-lit areas and being aware of your surroundings.
                    </p>
                </div>
            </div>
        </section>
    </main>

    <footer style="border-top: 1px solid var(--color-divider); padding: var(--space-8) 0; text-align: center;">
        <div class="container">
            <p style="color: var(--color-text-muted); font-size: var(--text-sm);">
                Data sourced from UK Police API. Last updated: {updated}.
            </p>
            <p style="color: var(--color-text-faint); font-size: var(--text-xs); margin-top: var(--space-2);">
                © 2026 CrimeSafe UK
            </p>
        </div>
    </footer>

    <script>
        // Theme toggle
        const toggle = document.getElementById('themeToggle');
        const html = document.documentElement;
        const saved = localStorage.getItem('theme');
        if (saved) html.setAttribute('data-theme', saved);
        toggle?.addEventListener('click', () => {{
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            toggle.textContent = next === 'dark' ? '☀️' : '🌙';
        }});
        if (html.getAttribute('data-theme') === 'dark') toggle.textContent = '☀️';
    </script>
</body>
</html>'''

def format_crime_type(category):
    return category.replace('-', ' ').title()

def get_crime_color(category):
    colors = {
        'violent-crime': '#dc2626',
        'robbery': '#dc2626',
        'burglary': '#ea580c',
        'vehicle-crime': '#ca8a04',
        'theft-from-the-person': '#ca8a04',
        'shoplifting': '#65a30d',
        'anti-social-behaviour': '#0891b2',
        'public-order': '#7c3aed',
        'drugs': '#be185d',
    }
    return colors.get(category, '#64748b')

def get_score_color(score):
    if score >= 60:
        return 'var(--color-success)'
    elif score >= 40:
        return 'var(--color-warning)'
    return 'var(--color-error)'

def get_safety_text(score):
    if score >= 70:
        return "This is a relatively safe area with below-average crime rates."
    elif score >= 50:
        return "This area has moderate crime levels typical of urban locations."
    elif score >= 30:
        return "This area has higher than average crime rates. Extra caution is advised."
    return "This area has significantly elevated crime rates. Please exercise caution."

def generate_crime_breakdown(types):
    if not types:
        return '<p style="color: var(--color-text-muted);">No crime data available for this period.</p>'
    
    html = '<div style="display: flex; flex-direction: column; gap: var(--space-3);">'
    for crime_type, count in types.items():
        color = get_crime_color(crime_type)
        formatted = format_crime_type(crime_type)
        html += f'''
        <div style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-2) 0; border-bottom: 1px solid var(--color-divider);">
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <span style="width: 12px; height: 12px; border-radius: 50%; background: {color};"></span>
                <span>{formatted}</span>
            </div>
            <strong>{count}</strong>
        </div>'''
    html += '</div>'
    return html

def main():
    # Check for cached data
    cache_file = DATA_DIR / 'street_crime_data.json'
    streets_file = DATA_DIR / 'top_streets.json'
    
    # Load streets
    with open(streets_file) as f:
        streets = json.load(f)
    
    # Try to load cached data
    cache = {}
    if cache_file.exists():
        with open(cache_file) as f:
            data = json.load(f)
            cache = data.get('streets', {})
            updated = data.get('updated', 'Unknown')
    else:
        updated = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Generating {len(streets)} street pages...")
    
    for i, street in enumerate(streets):
        slug = street['slug']
        name = street['name']
        city = street.get('city', 'UK')
        
        # Get cached stats or defaults
        if slug in cache:
            stats = cache[slug].get('stats', {})
            month = cache[slug].get('month', 'Recent')
        else:
            stats = {'total': 0, 'types': {}, 'score': 50, 'top_crime': None}
            month = 'Recent'
        
        total_crimes = stats.get('total', 0)
        score = stats.get('score', 50)
        types = stats.get('types', {})
        top_crime = stats.get('top_crime', 'anti-social-behaviour')
        
        # Generate HTML
        html = TEMPLATE.format(
            street_name=name,
            slug=slug,
            city=city,
            score=score,
            score_color=get_score_color(score),
            total_crimes=total_crimes,
            top_crime=top_crime or 'unknown',
            top_crime_formatted=format_crime_type(top_crime) if top_crime else 'Unknown',
            month=month,
            crime_breakdown_html=generate_crime_breakdown(types),
            safety_text=get_safety_text(score),
            updated=updated
        )
        
        # Write file
        # Skip if slug would create index
        if slug == "" or slug == "index":
            continue
        page_dir = STREETS_DIR / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / 'index.html').write_text(html)
        
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/{len(streets)}...")
    
    print(f"✅ Generated {len(streets)} street pages")

if __name__ == "__main__":
    main()
