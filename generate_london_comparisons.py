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
    """Generate a comparison page with FAQ and descriptive text"""
    name1 = html_lib.escape(nb1['name'])
    name2 = html_lib.escape(nb2['name'])
    
    title = f"{name1} vs {name2} Crime Comparison — London — CrimeSafe UK"
    desc = f"Compare crime rates: {name1} ({nb1['score']}/100) vs {name2} ({nb2['score']}/100). Which London neighbourhood is safer?"
    
    if nb1['score'] > nb2['score']:
        winner, winner_score = name1, nb1['score']
        loser, loser_score = name2, nb2['score']
        safer_text = f"{name1} is safer than {name2}"
    elif nb2['score'] > nb1['score']:
        winner, winner_score = name2, nb2['score']
        loser, loser_score = name1, nb1['score']
        safer_text = f"{name2} is safer than {name1}"
    else:
        winner, winner_score = "Tie", nb1['score']
        loser, loser_score = "", nb1['score']
        safer_text = f"{name1} and {name2} have equal safety ratings"
    
    score_diff = abs(nb1['score'] - nb2['score'])
    
    # Grade descriptions
    def grade_desc(score):
        if score >= 80: return "very safe"
        if score >= 60: return "safe"
        if score >= 40: return "average"
        if score >= 20: return "below average"
        return "high risk"
    
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
                    <div style="font-size: var(--text-sm);">{"🏆 Safer Neighbourhood" if winner != "Tie" else "⚖️ Equal Safety"}</div>
                    <div style="font-size: var(--text-xl); font-weight: 700;">{winner}</div>
                    <div style="font-size: var(--text-sm); opacity: 0.9;">{f"Score {winner_score}/100" if winner != "Tie" else f"Both score {winner_score}/100"}</div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4);">
                    <div class="kpi-card" style="text-align: center; padding: var(--space-4);">
                        <h2 style="font-size: var(--text-lg); margin-bottom: var(--space-2);">{name1}</h2>
                        <div style="font-size: 2rem; font-weight: 700; color: {"#16a34a" if nb1['score'] >= 60 else "#ca8a04" if nb1['score'] >= 40 else "#dc2626"};">{nb1['score']}</div>
                        <div style="font-size: var(--text-sm); color: var(--muted);">Safety Score</div>
                        <a href="/neighbourhood/{nb1['force_slug']}/{nb1['nb_slug']}/" style="display: inline-block; margin-top: var(--space-3); color: var(--color-primary);">View Details →</a>
                    </div>
                    <div class="kpi-card" style="text-align: center; padding: var(--space-4);">
                        <h2 style="font-size: var(--text-lg); margin-bottom: var(--space-2);">{name2}</h2>
                        <div style="font-size: 2rem; font-weight: 700; color: {"#16a34a" if nb2['score'] >= 60 else "#ca8a04" if nb2['score'] >= 40 else "#dc2626"};">{nb2['score']}</div>
                        <div style="font-size: var(--text-sm); color: var(--muted);">Safety Score</div>
                        <a href="/neighbourhood/{nb2['force_slug']}/{nb2['nb_slug']}/" style="display: inline-block; margin-top: var(--space-3); color: var(--color-primary);">View Details →</a>
                    </div>
                </div>
                
                <!-- Summary Section -->
                <div class="kpi-card" style="margin-top: var(--space-4); padding: var(--space-4);">
                    <h2 style="font-size: var(--text-lg); color: var(--color-primary); margin-bottom: var(--space-3);">Comparison Summary</h2>
                    <p style="color: var(--muted); margin-bottom: var(--space-3);">
                        When comparing {name1} and {name2}, {safer_text}. 
                        {name1} has a safety score of {nb1['score']}/100, which is considered {grade_desc(nb1['score'])} for London. 
                        {name2} scores {nb2['score']}/100, rated as {grade_desc(nb2['score'])}.
                    </p>
                    <p style="color: var(--muted);">
                        {f"The {score_diff}-point difference indicates {winner} has noticeably lower crime rates." if score_diff >= 10 else f"The {score_diff}-point difference suggests similar crime levels in both areas." if score_diff > 0 else "Both neighbourhoods have identical crime profiles."}
                        These scores are based on official Metropolitan Police crime data from January 2026.
                    </p>
                </div>
                
                <!-- FAQ Section -->
                <div class="kpi-card" style="margin-top: var(--space-4); padding: var(--space-4);">
                    <h2 style="font-size: var(--text-lg); color: var(--color-primary); margin-bottom: var(--space-3);">Frequently Asked Questions</h2>
                    
                    <div style="border-bottom: 1px solid var(--border); padding: var(--space-3) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">Which is safer, {name1} or {name2}?</div>
                        <div style="color: var(--muted);">
                            {f"{winner} is safer with a score of {winner_score}/100 compared to {loser}'s {loser_score}/100." if winner != "Tie" else f"Both neighbourhoods are equally safe with scores of {winner_score}/100."}
                        </div>
                    </div>
                    
                    <div style="border-bottom: 1px solid var(--border); padding: var(--space-3) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">Is {name1} a safe place to live?</div>
                        <div style="color: var(--muted);">
                            {name1} has a safety score of {nb1['score']}/100, which is {grade_desc(nb1['score'])} compared to other London neighbourhoods.
                            {"It ranks in the top 40% for safety." if nb1['score'] >= 60 else "It has average crime levels for the area." if nb1['score'] >= 40 else "Extra caution is advised in this area."}
                        </div>
                    </div>
                    
                    <div style="padding: var(--space-3) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">How are these safety scores calculated?</div>
                        <div style="color: var(--muted);">
                            Safety scores are based on official crime data from the Metropolitan Police. 
                            Each neighbourhood is ranked against all other UK neighbourhoods, with 100 being the safest and 0 the least safe.
                            Scores account for violent crime, property crime, and anti-social behaviour.
                        </div>
                    </div>
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
        
        # Always regenerate (template updated)
        # if os.path.exists(f"{out_dir}/index.html"):
        #     generated += 1
        #     continue
        
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
