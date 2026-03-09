#!/usr/bin/env python3
"""
Generate neighbourhood pages
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
    
    html = get_header(f"{neighbourhood['name']} — {force['name']} — CrimeSafe UK")
    
    # Crime stats section
    if crime_data and crime_data.get('total_crimes', 0) > 0:
        total = crime_data['total_crimes']
        categories = crime_data.get('categories', {})
        
        # Calculate safety score (100 = safest, 0 = most dangerous)
        weighted_score = 0
        max_weight = sum(c['weight'] for c in CRIME_WEIGHTS.values())
        for cat, count in categories.items():
            if cat in CRIME_WEIGHTS:
                weighted_score += count * CRIME_WEIGHTS[cat]['weight']
        
        # Normalize: lower crime = higher score
        # Rough estimate: <50 crimes/month = safe, >500 = dangerous
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
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="number">{safety_score}</div>
                    <div class="label">Safety Score</div>
                    <span class="score-badge {score_class}">{score_label}</span>
                </div>
                <div class="stat-card">
                    <div class="number">{total:,}</div>
                    <div class="label">Crimes (Jan 2026)</div>
                </div>
            </div>
            
            <h3 style="margin-top: 2rem;">Crime Breakdown</h3>
            <div class="force-grid" style="margin-top: 1rem;">
'''
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:8]:
            info = CRIME_WEIGHTS.get(cat, {"name": cat.replace("-", " ").title(), "icon": "📋"})
            crime_html += f'''
                <div class="stat-card" style="text-align: left;">
                    <div style="font-size: 1.5rem;">{info['icon']} {count}</div>
                    <div class="label">{info['name']}</div>
                </div>
'''
        crime_html += '</div>'
    else:
        crime_html = '''
            <div class="stat-card" style="text-align: center; padding: 2rem;">
                <p>Crime statistics coming soon</p>
                <p class="label">Data is being collected for this neighbourhood</p>
            </div>
'''
    
    html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/forces/">Forces</a> › <a href="/force/{force_slug}/">{force['name']}</a> › {neighbourhood['name']}
            </div>
        </div>
        
        <section class="hero" style="padding: 2rem 1rem;">
            <div class="container">
                <h1>{neighbourhood['name']}</h1>
                <p>{force['name']}</p>
            </div>
        </section>
        
        <section>
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
