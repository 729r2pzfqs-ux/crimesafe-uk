#!/usr/bin/env python3
"""
Generate comparison pages for popular neighbourhood pairs
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
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
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
            <p style="margin-top: var(--space-2);">Data updated quarterly. Last update: Q1 2026</p>
        </div>
    </footer>
    <script src="/script.js"></script>
</body>
</html>
'''

def get_grade(score):
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "F"

def grade_class(grade):
    return f"grade-{grade.lower()}"

def generate_comparison_page(nb1, nb2):
    """Generate a comparison page between two neighbourhoods"""
    name1 = html_lib.escape(nb1['name'])
    name2 = html_lib.escape(nb2['name'])
    force1 = html_lib.escape(nb1['force'])
    force2 = html_lib.escape(nb2['force'])
    
    title = f"{name1} vs {name2} — Crime Comparison — CrimeSafe UK"
    desc = f"Compare crime rates between {name1} and {name2}. Safety scores, crime breakdown, and which neighbourhood is safer."
    
    # Determine winner
    if nb1['score'] > nb2['score']:
        winner = name1
        winner_score = nb1['score']
    elif nb2['score'] > nb1['score']:
        winner = name2
        winner_score = nb2['score']
    else:
        winner = "Tie"
        winner_score = nb1['score']
    
    score_diff = abs(nb1['score'] - nb2['score'])
    
    html = get_header(title, desc)
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/compare/">Compare</a> › {name1} vs {name2}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{name1} vs {name2}</h1>
                <p class="hero-sub">Crime rate comparison • Q1 2026 data</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container" style="max-width: 1000px;">
                
                <!-- Winner Banner -->
                <div class="kpi-card" style="text-align: center; padding: var(--space-6); margin-bottom: var(--space-6); background: linear-gradient(135deg, var(--color-primary), #0f766e); color: white;">
                    <div style="font-size: var(--text-sm); opacity: 0.9; margin-bottom: var(--space-2);">{"🏆 Safer Neighbourhood" if winner != "Tie" else "⚖️ Equal Safety"}</div>
                    <div style="font-size: var(--text-2xl); font-weight: 700;">{winner}</div>
                    <div style="opacity: 0.9; margin-top: var(--space-2);">{"Score " + str(winner_score) + "/100" if winner != "Tie" else "Both score " + str(winner_score) + "/100"}</div>
                </div>
                
                <!-- Side by Side Comparison -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-6);">
                    <!-- Neighbourhood 1 -->
                    <div class="kpi-card" style="text-align: center; padding: var(--space-6);">
                        <h2 style="color: var(--color-primary); margin-bottom: var(--space-4);">{name1}</h2>
                        <div style="font-size: var(--text-sm); color: var(--color-text-muted); margin-bottom: var(--space-4);">{force1}</div>
                        
                        <div style="display: flex; justify-content: center; gap: var(--space-4); margin-bottom: var(--space-4);">
                            <div>
                                <div style="font-size: 3rem; font-weight: 700; color: {"#16a34a" if nb1['score'] >= 60 else "#ca8a04" if nb1['score'] >= 40 else "#dc2626"};">{nb1['score']}</div>
                                <div style="font-size: var(--text-xs); color: var(--color-text-muted);">Safety Score</div>
                            </div>
                            <div>
                                <div style="font-size: 3rem; font-weight: 700;"><span class="grade {grade_class(nb1['grade'])}">{nb1['grade']}</span></div>
                                <div style="font-size: var(--text-xs); color: var(--color-text-muted);">Grade</div>
                            </div>
                        </div>
                        
                        <a href="/neighbourhood/{nb1['force_slug']}/{nb1['nb_slug']}/" class="btn btn-outline" style="margin-top: var(--space-4);">View Details →</a>
                    </div>
                    
                    <!-- Neighbourhood 2 -->
                    <div class="kpi-card" style="text-align: center; padding: var(--space-6);">
                        <h2 style="color: var(--color-primary); margin-bottom: var(--space-4);">{name2}</h2>
                        <div style="font-size: var(--text-sm); color: var(--color-text-muted); margin-bottom: var(--space-4);">{force2}</div>
                        
                        <div style="display: flex; justify-content: center; gap: var(--space-4); margin-bottom: var(--space-4);">
                            <div>
                                <div style="font-size: 3rem; font-weight: 700; color: {"#16a34a" if nb2['score'] >= 60 else "#ca8a04" if nb2['score'] >= 40 else "#dc2626"};">{nb2['score']}</div>
                                <div style="font-size: var(--text-xs); color: var(--color-text-muted);">Safety Score</div>
                            </div>
                            <div>
                                <div style="font-size: 3rem; font-weight: 700;"><span class="grade {grade_class(nb2['grade'])}">{nb2['grade']}</span></div>
                                <div style="font-size: var(--text-xs); color: var(--color-text-muted);">Grade</div>
                            </div>
                        </div>
                        
                        <a href="/neighbourhood/{nb2['force_slug']}/{nb2['nb_slug']}/" class="btn btn-outline" style="margin-top: var(--space-4);">View Details →</a>
                    </div>
                </div>
                
                <!-- Summary -->
                <div class="kpi-card" style="margin-top: var(--space-6); padding: var(--space-6);">
                    <h3 style="color: var(--color-primary); margin-bottom: var(--space-4);">Summary</h3>
                    <p style="color: var(--color-text-muted);">
                        {f"{name1} has a safety score of {nb1['score']}/100, while {name2} scores {nb2['score']}/100." }
                        {f" {winner} is the safer choice with {score_diff} points higher safety rating." if winner != "Tie" else " Both neighbourhoods have identical safety ratings."}
                    </p>
                    <p style="color: var(--color-text-muted); margin-top: var(--space-3);">
                        Safety scores are based on official police crime data and represent the neighbourhood's percentile ranking compared to all UK neighbourhoods.
                    </p>
                </div>
                
            </div>
        </section>
    </main>
'''
    html += get_footer()
    return html

def generate_compare_index(popular_comparisons):
    """Generate the compare index page"""
    html = get_header("Compare Neighbourhoods — CrimeSafe UK", "Compare crime rates between UK neighbourhoods. Side-by-side safety score comparisons.")
    html += '''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Compare
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>Compare Neighbourhoods</h1>
                <p class="hero-sub">Side-by-side crime rate comparisons</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container">
                <h2 style="margin-bottom: var(--space-6);">Popular Comparisons</h2>
                <div class="force-grid">
'''
    
    for comp in popular_comparisons[:50]:
        nb1, nb2 = comp
        slug = f"{nb1['nb_slug']}-vs-{nb2['nb_slug']}"
        html += f'''
                    <a href="/compare/{slug}/" class="force-card">
                        <h3>{nb1['name']} vs {nb2['name']}</h3>
                        <div class="meta">Score {nb1['score']} vs {nb2['score']}</div>
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
    print("Loading rankings...")
    with open('data/rankings.json') as f:
        rankings = json.load(f)
    
    print(f"Loaded {len(rankings)} neighbourhoods")
    
    # Group by force for intra-force comparisons
    by_force = {}
    for r in rankings:
        force = r['force']
        if force not in by_force:
            by_force[force] = []
        by_force[force].append(r)
    
    # Generate popular comparisons:
    # 1. London neighbourhoods (Met Police)
    # 2. Top vs Bottom within same force
    # 3. Adjacent rankings (safest vs safest)
    
    comparisons = []
    
    # London comparisons (Met Police has most interest)
    met_nbs = by_force.get('Metropolitan Police Service', [])[:20]
    for nb1, nb2 in combinations(met_nbs[:10], 2):
        comparisons.append((nb1, nb2))
    
    # Manchester comparisons
    gmp_nbs = by_force.get('Greater Manchester Police', [])[:10]
    for nb1, nb2 in combinations(gmp_nbs[:6], 2):
        comparisons.append((nb1, nb2))
    
    # West Midlands comparisons
    wmp_nbs = by_force.get('West Midlands Police', [])[:10]
    for nb1, nb2 in combinations(wmp_nbs[:6], 2):
        comparisons.append((nb1, nb2))
    
    # Top safest comparisons
    for nb1, nb2 in combinations(rankings[:15], 2):
        if (nb1, nb2) not in comparisons:
            comparisons.append((nb1, nb2))
    
    # Cross-force: safest vs most dangerous
    safest = rankings[:10]
    dangerous = rankings[-10:]
    for nb1 in safest[:5]:
        for nb2 in dangerous[:5]:
            comparisons.append((nb1, nb2))
    
    print(f"Generating {len(comparisons)} comparison pages...")
    
    # Generate comparison index
    os.makedirs('compare', exist_ok=True)
    with open('compare/index.html', 'w') as f:
        f.write(generate_compare_index(comparisons))
    
    # Generate individual comparison pages
    generated = 0
    for nb1, nb2 in comparisons:
        # Alphabetical order for consistent URLs
        if nb1['nb_slug'] > nb2['nb_slug']:
            nb1, nb2 = nb2, nb1
        
        slug = f"{nb1['nb_slug']}-vs-{nb2['nb_slug']}"
        out_dir = f"compare/{slug}"
        os.makedirs(out_dir, exist_ok=True)
        
        with open(f"{out_dir}/index.html", 'w') as f:
            f.write(generate_comparison_page(nb1, nb2))
        
        generated += 1
    
    print(f"\n{'='*50}")
    print(f"Generated {generated + 1} pages:")
    print(f"  - Compare index: /compare/")
    print(f"  - Comparison pages: {generated}")

if __name__ == "__main__":
    main()
