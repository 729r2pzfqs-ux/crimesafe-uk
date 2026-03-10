#!/usr/bin/env python3
"""
Generate safest/most dangerous neighbourhoods ranking pages
"""

import json
import os
import html

def get_header(title, description):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="S7uUZGMb9yLeKT16YkQGWumhCd0n70jt19wxR1qrYEc">
    <link rel="preconnect" href="https://api.fontshare.com" crossorigin>
    <link rel="preconnect" href="https://cdn.fontshare.com" crossorigin>
    <!-- Google Analytics -->
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

def grade_class(grade):
    return {
        'A': 'grade-a',
        'B': 'grade-b',
        'C': 'grade-c',
        'D': 'grade-d',
        'F': 'grade-f'
    }.get(grade, 'grade-c')

def generate_safest_page(rankings, top_n=100):
    """Generate safest neighbourhoods page"""
    title = "Safest Places to Live in the UK 2026 — CrimeSafe UK"
    desc = f"Top {top_n} safest neighbourhoods in the UK ranked by crime rate. Find the lowest crime areas to live in England, Wales, and Northern Ireland."
    
    html_content = get_header(title, desc)
    html_content += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Safest Neighbourhoods
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>Safest Places to Live in the UK</h1>
                <p class="hero-sub">Top {top_n} neighbourhoods with lowest crime rates • Q1 2026 data</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container">
                <div style="display: flex; gap: var(--space-4); margin-bottom: var(--space-6); flex-wrap: wrap;">
                    <a href="/safest/" class="btn btn-primary">Safest Areas</a>
                    <a href="/dangerous/" class="btn btn-outline">Highest Crime Areas</a>
                </div>
                
                <div class="ranking-table">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 2px solid var(--border); text-align: left;">
                                <th style="padding: var(--space-3);">#</th>
                                <th style="padding: var(--space-3);">Neighbourhood</th>
                                <th style="padding: var(--space-3);">Police Force</th>
                                <th style="padding: var(--space-3); text-align: center;">Score</th>
                                <th style="padding: var(--space-3); text-align: center;">Grade</th>
                            </tr>
                        </thead>
                        <tbody>
'''
    
    for i, r in enumerate(rankings[:top_n], 1):
        name = html.escape(r['name'])
        force = html.escape(r['force'])
        link = f"/neighbourhood/{r['force_slug']}/{r['nb_slug']}/"
        
        html_content += f'''
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: var(--space-3); font-weight: 600; color: var(--muted);">{i}</td>
                                <td style="padding: var(--space-3);"><a href="{link}" style="color: var(--primary); text-decoration: none;">{name}</a></td>
                                <td style="padding: var(--space-3); color: var(--muted);">{force}</td>
                                <td style="padding: var(--space-3); text-align: center; font-weight: 600;">{r['score']}</td>
                                <td style="padding: var(--space-3); text-align: center;"><span class="grade {grade_class(r['grade'])}">{r['grade']}</span></td>
                            </tr>
'''
    
    html_content += '''
                        </tbody>
                    </table>
                </div>
                
                <div class="card" style="margin-top: var(--space-8); padding: var(--space-6);">
                    <h2 style="margin-bottom: var(--space-4);">About This Ranking</h2>
                    <p>This ranking shows neighbourhoods with the lowest recorded crime rates based on official police data from data.police.uk. The safety score (0-100) is calculated from total reported crimes in the latest month.</p>
                    <p style="margin-top: var(--space-3);">Higher scores indicate safer areas. Grade A (80-100) represents the safest neighbourhoods, while Grade F (0-19) indicates areas with higher crime rates.</p>
                </div>
            </div>
        </section>
    </main>
'''
    html_content += get_footer()
    return html_content

def generate_dangerous_page(rankings, bottom_n=100):
    """Generate highest crime neighbourhoods page"""
    title = "Highest Crime Areas in the UK 2026 — CrimeSafe UK"
    desc = f"Top {bottom_n} neighbourhoods with highest crime rates in the UK. Crime statistics for England, Wales, and Northern Ireland."
    
    # Reverse rankings for most dangerous
    reversed_rankings = list(reversed(rankings))
    
    html_content = get_header(title, desc)
    html_content += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › Highest Crime Areas
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>Highest Crime Areas in the UK</h1>
                <p class="hero-sub">Top {bottom_n} neighbourhoods with highest crime rates • Q1 2026 data</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container">
                <div style="display: flex; gap: var(--space-4); margin-bottom: var(--space-6); flex-wrap: wrap;">
                    <a href="/safest/" class="btn btn-outline">Safest Areas</a>
                    <a href="/dangerous/" class="btn btn-primary">Highest Crime Areas</a>
                </div>
                
                <div class="ranking-table">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 2px solid var(--border); text-align: left;">
                                <th style="padding: var(--space-3);">#</th>
                                <th style="padding: var(--space-3);">Neighbourhood</th>
                                <th style="padding: var(--space-3);">Police Force</th>
                                <th style="padding: var(--space-3); text-align: center;">Score</th>
                                <th style="padding: var(--space-3); text-align: center;">Grade</th>
                            </tr>
                        </thead>
                        <tbody>
'''
    
    for i, r in enumerate(reversed_rankings[:bottom_n], 1):
        name = html.escape(r['name'])
        force = html.escape(r['force'])
        link = f"/neighbourhood/{r['force_slug']}/{r['nb_slug']}/"
        
        html_content += f'''
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: var(--space-3); font-weight: 600; color: var(--muted);">{i}</td>
                                <td style="padding: var(--space-3);"><a href="{link}" style="color: var(--primary); text-decoration: none;">{name}</a></td>
                                <td style="padding: var(--space-3); color: var(--muted);">{force}</td>
                                <td style="padding: var(--space-3); text-align: center; font-weight: 600;">{r['score']}</td>
                                <td style="padding: var(--space-3); text-align: center;"><span class="grade {grade_class(r['grade'])}">{r['grade']}</span></td>
                            </tr>
'''
    
    html_content += '''
                        </tbody>
                    </table>
                </div>
                
                <div class="card" style="margin-top: var(--space-8); padding: var(--space-6);">
                    <h2 style="margin-bottom: var(--space-4);">About This Ranking</h2>
                    <p>This ranking shows neighbourhoods with the highest recorded crime rates based on official police data from data.police.uk.</p>
                    <p style="margin-top: var(--space-3);"><strong>Note:</strong> High crime rates don't necessarily mean an area is "dangerous". Commercial areas, city centres, and transport hubs often have higher reported crime due to more people passing through, not because residents are at greater risk.</p>
                </div>
            </div>
        </section>
    </main>
'''
    html_content += get_footer()
    return html_content

def main():
    print("Loading rankings...")
    with open('data/rankings.json') as f:
        rankings = json.load(f)
    
    print(f"Loaded {len(rankings)} rankings")
    
    # Generate safest page
    print("Generating safest neighbourhoods page...")
    os.makedirs('safest', exist_ok=True)
    with open('safest/index.html', 'w') as f:
        f.write(generate_safest_page(rankings, 100))
    
    # Generate dangerous page
    print("Generating highest crime areas page...")
    os.makedirs('dangerous', exist_ok=True)
    with open('dangerous/index.html', 'w') as f:
        f.write(generate_dangerous_page(rankings, 100))
    
    print("\n" + "="*50)
    print("Generated ranking pages:")
    print("  - /safest/ - Top 100 safest neighbourhoods")
    print("  - /dangerous/ - Top 100 highest crime areas")

if __name__ == "__main__":
    main()
