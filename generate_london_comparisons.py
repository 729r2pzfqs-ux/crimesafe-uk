#!/usr/bin/env python3
"""
Generate ALL London (Met Police) comparison pages
~211K pages
"""

import json
import os
import re
import html as html_lib
from itertools import combinations

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

def get_header(title, description):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="S7uUZGMb9yLeKT16YkQGWumhCd0n70jt19wxR1qrYEc">
    <link rel="preconnect" href="https://api.fontshare.com" crossorigin>
    <link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
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
                <a href="/districts/">Districts</a>
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
        </div>
    </footer>
    <script src="/script.js"></script>
</body>
</html>
'''

def grade_class(grade):
    return f"grade-{grade.lower()}"

def generate_comparison_page(nb1, nb2):
    """Generate a minimal comparison page"""
    name1 = html_lib.escape(nb1['name'])
    name2 = html_lib.escape(nb2['name'])
    
    title = f"{name1} vs {name2} Crime Comparison — London — CrimeSafe UK"
    desc = f"Compare crime rates: {name1} ({nb1['score']}/100) vs {name2} ({nb2['score']}/100). Which London neighbourhood is safer?"
    
    if nb1['score'] > nb2['score']:
        winner, winner_score = name1, nb1['score']
    elif nb2['score'] > nb1['score']:
        winner, winner_score = name2, nb2['score']
    else:
        winner, winner_score = "Tie", nb1['score']
    
    score_diff = abs(nb1['score'] - nb2['score'])
    
    html = get_header(title, desc)
    html += f'''
    <main>
        <div class="container" style="padding: var(--space-4) 0;">
            <a href="/">Home</a> › <a href="/compare/">Compare</a> › {name1} vs {name2}
        </div>
        
        <section style="padding: var(--space-6) 0;">
            <div class="container">
                <h1 style="font-size: var(--text-2xl);">{name1} vs {name2}</h1>
                <p style="color: var(--muted);">London crime comparison • January 2026</p>
                
                <div style="background: linear-gradient(135deg, var(--color-primary), #0f766e); color: white; text-align: center; padding: var(--space-4); border-radius: var(--radius-md); margin: var(--space-4) 0;">
                    <div style="font-size: var(--text-sm);">{"🏆 Safer" if winner != "Tie" else "⚖️ Equal"}</div>
                    <div style="font-size: var(--text-xl); font-weight: 700;">{winner}</div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                    <div class="kpi-card" style="text-align: center; padding: var(--space-4);">
                        <h2 style="font-size: var(--text-lg); margin-bottom: var(--space-2);">{name1}</h2>
                        <div style="font-size: 2rem; font-weight: 700; color: {"#16a34a" if nb1['score'] >= 60 else "#ca8a04" if nb1['score'] >= 40 else "#dc2626"};">{nb1['score']}</div>
                        <div style="font-size: var(--text-sm); color: var(--muted);">Safety Score</div>
                        <a href="/neighbourhood/{nb1['force_slug']}/{nb1['nb_slug']}/" style="display: inline-block; margin-top: var(--space-3); color: var(--color-primary);">View →</a>
                    </div>
                    <div class="kpi-card" style="text-align: center; padding: var(--space-4);">
                        <h2 style="font-size: var(--text-lg); margin-bottom: var(--space-2);">{name2}</h2>
                        <div style="font-size: 2rem; font-weight: 700; color: {"#16a34a" if nb2['score'] >= 60 else "#ca8a04" if nb2['score'] >= 40 else "#dc2626"};">{nb2['score']}</div>
                        <div style="font-size: var(--text-sm); color: var(--muted);">Safety Score</div>
                        <a href="/neighbourhood/{nb2['force_slug']}/{nb2['nb_slug']}/" style="display: inline-block; margin-top: var(--space-3); color: var(--color-primary);">View →</a>
                    </div>
                </div>
                
                <p style="margin-top: var(--space-4); color: var(--muted);">
                    {f"{winner} is safer with {score_diff} points higher rating." if winner != "Tie" else "Both areas have equal safety ratings."}
                    Scores based on official Metropolitan Police crime data.
                </p>
            </div>
        </section>
    </main>
'''
    html += get_footer()
    return html

def main():
    print("Loading rankings...")
    with open('data/rankings.json') as f:
        rankings = json.load(f)
    
    # Filter to Met Police only
    met_nbs = [r for r in rankings if r['force'] == 'Metropolitan Police Service']
    print(f"London neighbourhoods: {len(met_nbs)}")
    
    total_pairs = len(met_nbs) * (len(met_nbs) - 1) // 2
    print(f"Total comparison pages: {total_pairs:,}")
    
    # Generate all pairs
    generated = 0
    for nb1, nb2 in combinations(met_nbs, 2):
        # Alphabetical order
        if nb1['nb_slug'] > nb2['nb_slug']:
            nb1, nb2 = nb2, nb1
        
        slug = f"{nb1['nb_slug']}-vs-{nb2['nb_slug']}"
        out_dir = f"compare/{slug}"
        
        # Skip if exists
        if os.path.exists(f"{out_dir}/index.html"):
            generated += 1
            continue
        
        os.makedirs(out_dir, exist_ok=True)
        
        with open(f"{out_dir}/index.html", 'w') as f:
            f.write(generate_comparison_page(nb1, nb2))
        
        generated += 1
        if generated % 10000 == 0:
            print(f"  Generated {generated:,}/{total_pairs:,}...")
    
    print(f"\n{'='*50}")
    print(f"Generated {generated:,} London comparison pages")

if __name__ == "__main__":
    main()
