#!/usr/bin/env python3
"""
Generate neighbourhood pages with HoodSafe styling
"""

import json
import os
import re
from generate_site import get_header, get_footer, slugify, CRIME_WEIGHTS

DATA_DIR = "data"
OUTPUT_DIR = "."

def generate_neighbourhood_page(force, neighbourhood, crime_data=None):
    """Generate a neighbourhood detail page"""
    force_slug = slugify(force['name'])
    nb_slug = slugify(neighbourhood['name'])
    
    desc = f"Crime statistics and safety score for {neighbourhood['name']} in {force['name']}"
    html = get_header(f"{neighbourhood['name']} — {force['name']} — CrimeSafe UK", desc)
    
    # Crime stats section
    if crime_data and crime_data.get('total_crimes', 0) > 0:
        total = crime_data['total_crimes']
        categories = crime_data.get('categories', {})
        
        # Calculate safety score (100 = safest, 0 = most dangerous)
        weighted_score = 0
        for cat, count in categories.items():
            if cat in CRIME_WEIGHTS:
                weighted_score += count * CRIME_WEIGHTS[cat]['weight']
        
        # Normalize: lower crime = higher score
        raw_score = max(0, 100 - (weighted_score / 5))
        safety_score = round(min(100, max(0, raw_score)))
        
        if safety_score >= 70:
            score_class = "score-safe"
            score_label = "Safe"
        elif safety_score >= 40:
            score_class = "score-moderate"
            score_label = "Moderate"
        else:
            score_class = "score-unsafe"
            score_label = "Needs Attention"
        
        crime_html = f'''
                <div class="kpi-grid" style="grid-template-columns: repeat(2, 1fr); max-width: 500px; margin: 0 auto var(--space-8);">
                    <div class="kpi-card" style="text-align: center;">
                        <div class="kpi-label">Safety Score</div>
                        <div class="kpi-value">{safety_score}</div>
                        <span class="score-badge {score_class}">{score_label}</span>
                    </div>
                    <div class="kpi-card" style="text-align: center;">
                        <div class="kpi-label">Total Crimes</div>
                        <div class="kpi-value">{total:,}</div>
                        <div class="kpi-detail">January 2026</div>
                    </div>
                </div>
                
                <div class="section-header">
                    <h2 class="section-title">Crime Breakdown</h2>
                </div>
                <div class="crime-grid">
'''
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:8]:
            info = CRIME_WEIGHTS.get(cat, {"name": cat.replace("-", " ").title(), "icon": "📋"})
            crime_html += f'''
                    <div class="crime-item">
                        <div class="icon">{info['icon']}</div>
                        <div class="count">{count}</div>
                        <div class="type">{info['name']}</div>
                    </div>
'''
        crime_html += '</div>'
    else:
        crime_html = '''
                <div class="kpi-card" style="text-align: center; max-width: 500px; margin: 0 auto;">
                    <div class="kpi-label">Status</div>
                    <div class="kpi-value" style="font-size: var(--text-lg);">Data Loading</div>
                    <div class="kpi-detail">Crime statistics are being collected for this neighbourhood</div>
                </div>
'''
    
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/forces/">Forces</a> › <a href="/force/{force_slug}/">{force['name']}</a> › {neighbourhood['name']}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{neighbourhood['name']}</h1>
                <p class="hero-sub">{force['name']}</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container">
                {crime_html}
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
    
    # Load any existing crime data
    crime_data = {}
    crimes_dir = f"{DATA_DIR}/neighbourhood_crimes"
    if os.path.exists(crimes_dir):
        for fname in os.listdir(crimes_dir):
            if fname.endswith('.json'):
                with open(f"{crimes_dir}/{fname}") as f:
                    data = json.load(f)
                    key = fname.replace('.json', '')
                    crime_data[key] = data
    
    # Also check old crimes dir
    old_crimes_dir = f"{DATA_DIR}/crimes"
    if os.path.exists(old_crimes_dir):
        for fname in os.listdir(old_crimes_dir):
            if fname.endswith('.json'):
                with open(f"{old_crimes_dir}/{fname}") as f:
                    data = json.load(f)
                    key = fname.replace('.json', '')
                    if key not in crime_data:
                        crime_data[key] = data
    
    print(f"Loaded crime data for {len(crime_data)} neighbourhoods")
    
    # Generate neighbourhood pages
    total = sum(len(f['neighbourhoods']) for f in forces_data['forces'])
    generated = 0
    
    for force in forces_data['forces']:
        force_id = force['id']
        force_slug = slugify(force['name'])
        
        for nb in force['neighbourhoods']:
            nb_slug = slugify(nb['name'])
            
            # Get crime data if available
            key = f"{force_id}_{nb['id']}"
            nb_crime = crime_data.get(key)
            
            # Generate page
            os.makedirs(f"{OUTPUT_DIR}/neighbourhood/{force_slug}/{nb_slug}", exist_ok=True)
            with open(f"{OUTPUT_DIR}/neighbourhood/{force_slug}/{nb_slug}/index.html", 'w') as f:
                f.write(generate_neighbourhood_page(force, nb, nb_crime))
            
            generated += 1
            if generated % 500 == 0:
                print(f"  Generated {generated}/{total} neighbourhood pages...")
    
    print(f"\n{'='*50}")
    print(f"Generated {generated} neighbourhood pages")

if __name__ == "__main__":
    main()
