#!/usr/bin/env python3
"""Generate embeddable widgets for CrimeSafe UK"""

import json
import os
import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

# Load data
with open('data/rankings.json') as f:
    rankings = json.load(f)

with open('data/forces.json') as f:
    forces_data = json.load(f)

def get_score_color(score):
    if score >= 60: return '#16a34a'
    if score >= 40: return '#ca8a04'
    return '#dc2626'

def get_score_bg(score):
    if score >= 60: return '#dcfce7'
    if score >= 40: return '#fef9c3'
    return '#fee2e2'

def get_grade(score):
    if score >= 80: return 'A'
    if score >= 60: return 'B'
    if score >= 40: return 'C'
    if score >= 20: return 'D'
    return 'F'

# Generate embed pages for top neighbourhoods
count = 0
for r in rankings:  # All neighbourhoods
    slug = r['nb_slug']
    name = r.get('name', slug.replace('-', ' ').title())
    score = r.get('score', 50)
    force_slug = r.get('force_slug', 'unknown')
    
    color = get_score_color(score)
    bg = get_score_bg(score)
    grade = get_grade(score)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} Safety Score</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fff;
            padding: 16px;
        }}
        .widget {{
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            max-width: 320px;
        }}
        .header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .score-badge {{
            width: 56px;
            height: 56px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 700;
            background: {bg};
            color: {color};
        }}
        .info h2 {{
            font-size: 15px;
            font-weight: 600;
            color: #111;
            margin-bottom: 2px;
        }}
        .info p {{
            font-size: 12px;
            color: #6b7280;
        }}
        .bar-container {{
            background: #f3f4f6;
            border-radius: 6px;
            height: 8px;
            margin-bottom: 12px;
            overflow: hidden;
        }}
        .bar {{
            height: 100%;
            border-radius: 6px;
            background: {color};
            width: {score}%;
        }}
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .grade {{
            font-size: 12px;
            color: #6b7280;
        }}
        .grade strong {{
            color: {color};
        }}
        .powered {{
            font-size: 10px;
            color: #9ca3af;
            text-decoration: none;
        }}
        .powered:hover {{
            color: #01696F;
        }}
    </style>
</head>
<body>
    <div class="widget">
        <div class="header">
            <div class="score-badge">{score}</div>
            <div class="info">
                <h2>{name}</h2>
                <p>Safety Score</p>
            </div>
        </div>
        <div class="bar-container">
            <div class="bar"></div>
        </div>
        <div class="footer">
            <span class="grade">Grade: <strong>{grade}</strong> · Safer than {score}% of UK</span>
            <a href="https://crimesafe.uk/neighbourhood/{force_slug}/{slug}/" target="_blank" class="powered">CrimeSafe UK</a>
        </div>
    </div>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-CK531DR9X9');gtag('event','embed_view',{{'neighbourhood':'{slug}','referrer':document.referrer}});</script>
</body>
</html>'''
    
    os.makedirs(f'embed/{slug}', exist_ok=True)
    with open(f'embed/{slug}/index.html', 'w') as f:
        f.write(html)
    count += 1

print(f"✅ Generated {count} embed widgets")

# Create embed landing page
landing = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-CK531DR9X9"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-CK531DR9X9');</script>
    <title>Embed Safety Scores | CrimeSafe UK</title>
    <meta name="description" content="Embed crime safety scores on your website. Free widgets for estate agents, property sites, and local businesses.">
    <link href="https://api.fontshare.com/v2/css?f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
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
        </div>
    </nav>
    
    <main>
        <section class="hero">
            <div class="container">
                <h1>Embed Safety Scores</h1>
                <p class="hero-sub">Add crime safety widgets to your website — free for everyone</p>
            </div>
        </section>
        
        <section style="padding: var(--space-8) 0;">
            <div class="container" style="max-width: 800px;">
                <h2 style="margin-bottom: var(--space-4);">How to Use</h2>
                <p style="color: var(--color-text-muted); margin-bottom: var(--space-6);">
                    Copy the embed code below and paste it into your website. Replace <code>neighbourhood-slug</code> with the area you want to display.
                </p>
                
                <div style="background: var(--color-surface); border-radius: var(--radius); padding: var(--space-4); margin-bottom: var(--space-6);">
                    <code style="font-size: var(--text-sm); word-break: break-all;">
                        &lt;iframe src="https://crimesafe.uk/embed/brixton/" width="340" height="160" frameborder="0"&gt;&lt;/iframe&gt;
                    </code>
                </div>
                
                <h3 style="margin-bottom: var(--space-3);">Preview</h3>
                <iframe src="/embed/brixton/" width="340" height="160" frameborder="0" style="border-radius: var(--radius);"></iframe>
                
                <h3 style="margin: var(--space-6) 0 var(--space-3);">Find Your Neighbourhood</h3>
                <p style="color: var(--color-text-muted);">
                    Search for any neighbourhood on our <a href="/">homepage</a> and use its URL slug in the embed code.
                    <br><br>
                    Example: <code>crimesafe.uk/neighbourhood/metropolitan-police-service/<strong>brixton</strong>/</code> → use <code>brixton</code>
                </p>
                
                <h3 style="margin: var(--space-6) 0 var(--space-3);">Perfect For</h3>
                <ul style="color: var(--color-text-muted); padding-left: var(--space-4);">
                    <li>Estate agents & property listings</li>
                    <li>Relocation services</li>
                    <li>Local business directories</li>
                    <li>Community websites</li>
                    <li>Property comparison tools</li>
                </ul>
            </div>
        </section>
    </main>
    
    <footer class="footer">
        <div class="container">
            <p>&copy; 2026 CrimeSafe UK</p>
        </div>
    </footer>
</body>
</html>'''

with open('embed/index.html', 'w') as f:
    f.write(landing)

print("✅ Generated embed landing page")
