#!/usr/bin/env python3
"""
Generate neighbourhood pages with full content (HoodSafe style)
"""

import json
import os
import re
from generate_site import get_header, get_footer, slugify, CRIME_WEIGHTS

DATA_DIR = "data"
OUTPUT_DIR = "."

def get_grade(score):
    if score >= 80: return "A", "Very Safe"
    if score >= 60: return "B", "Safe"
    if score >= 40: return "C", "Moderate"
    if score >= 20: return "D", "Below Average"
    return "F", "High Risk"

def generate_neighbourhood_page(force, neighbourhood, crime_data=None):
    """Generate a neighbourhood detail page with full content"""
    force_slug = slugify(force['name'])
    nb_slug = slugify(neighbourhood['name'])
    nb_name = neighbourhood['name']
    force_name = force['name']
    
    # Calculate stats
    if crime_data and crime_data.get('total_crimes', 0) > 0:
        total = crime_data['total_crimes']
        categories = crime_data.get('categories', {})
        
        weighted_score = 0
        for cat, count in categories.items():
            if cat in CRIME_WEIGHTS:
                weighted_score += count * CRIME_WEIGHTS[cat]['weight']
        
        raw_score = max(0, 100 - (weighted_score / 5))
        safety_score = round(min(100, max(0, raw_score)))
        grade, grade_text = get_grade(safety_score)
        
        violent = categories.get('violent-crime', 0)
        property_crime = categories.get('burglary', 0) + categories.get('other-theft', 0) + categories.get('vehicle-crime', 0)
        asb = categories.get('anti-social-behaviour', 0)
        
        if safety_score >= 60:
            score_color = "#16a34a"
        elif safety_score >= 40:
            score_color = "#ca8a04"
        else:
            score_color = "#dc2626"
    else:
        safety_score = None
        total = 0
        categories = {}
        grade, grade_text = "?", "Data Pending"
        violent = 0
        property_crime = 0
        asb = 0
        score_color = "var(--color-text-muted)"
    
    desc = f"Crime statistics and safety score for {nb_name} in {force_name}. Safety Score: {safety_score}/100" if safety_score else f"Crime statistics for {nb_name}"
    html = get_header(f"{nb_name} Crime Rate & Safety — CrimeSafe UK", desc)
    
    if safety_score is not None:
        # Full page with crime data
        html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/forces/">Forces</a> › <a href="/force/{force_slug}/">{force_name}</a> › {nb_name}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{nb_name} Crime Rate</h1>
                <p class="hero-sub">{force_name} • January 2026 Data</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-8);">
            <div class="container" style="max-width: 900px;">
                <!-- Score Card -->
                <div class="kpi-card" style="display: flex; align-items: center; gap: var(--space-8); padding: var(--space-8); flex-wrap: wrap; justify-content: center;">
                    <div style="width: 140px; height: 140px; border-radius: 50%; background: {score_color}; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white;">
                        <span style="font-size: var(--text-2xl); font-weight: 700; line-height: 1;">{safety_score}</span>
                        <span style="font-size: var(--text-xs); opacity: 0.9;">Safety Score</span>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 4rem; font-weight: 700; color: {score_color}; line-height: 1;">{grade}</div>
                        <div style="color: var(--color-text-muted);">{grade_text}</div>
                    </div>
                </div>
                
                <!-- Stats Grid -->
                <div class="kpi-grid" style="margin-top: var(--space-6);">
                    <div class="kpi-card">
                        <div class="kpi-label">Total Crimes</div>
                        <div class="kpi-value">{total}</div>
                        <div class="kpi-detail">January 2026</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Violent Crime</div>
                        <div class="kpi-value" style="color: #dc2626;">{violent}</div>
                        <div class="kpi-detail">Assaults, robbery</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Property Crime</div>
                        <div class="kpi-value" style="color: #ca8a04;">{property_crime}</div>
                        <div class="kpi-detail">Burglary, theft</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Anti-Social</div>
                        <div class="kpi-value">{asb}</div>
                        <div class="kpi-detail">Nuisance, disorder</div>
                    </div>
                </div>
                
                <!-- Is it Safe? Section -->
                <div class="kpi-card" style="margin-top: var(--space-6); text-align: left; padding: var(--space-6);">
                    <h2 style="color: var(--color-primary); margin-bottom: var(--space-4);">Is {nb_name} Safe?</h2>
                    <p style="color: var(--color-text-muted); margin-bottom: var(--space-4);">
                        {nb_name} has a safety score of <strong>{safety_score}/100</strong>, which is rated as <strong>{grade_text}</strong>.
                        In January 2026, police recorded {total} crimes in this neighbourhood, including {violent} violent offences.
                    </p>
                    <p style="color: var(--color-text-muted);">
                        {"This area has lower crime rates compared to many urban neighbourhoods, making it a relatively safe place to live or visit." if safety_score >= 60 else "This area has moderate crime levels. As with any neighbourhood, we recommend staying aware of your surroundings, especially at night." if safety_score >= 40 else "This area has above-average crime rates. Take extra precautions with personal belongings and avoid walking alone at night."}
                    </p>
                </div>
                
                <!-- Crime Breakdown -->
                <div class="kpi-card" style="margin-top: var(--space-6); text-align: left; padding: var(--space-6);">
                    <h2 style="color: var(--color-primary); margin-bottom: var(--space-4);">Crime Breakdown</h2>
                    <div class="kpi-grid" style="grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));">
'''
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:8]:
            info = CRIME_WEIGHTS.get(cat, {"name": cat.replace("-", " ").title()})
            html += f'''
                        <div style="text-align: center; padding: var(--space-4); background: var(--color-surface-offset); border-radius: var(--radius-md);">
                            <div style="font-size: var(--text-xl); font-weight: 700; color: var(--color-primary);">{count}</div>
                            <div style="font-size: var(--text-xs); color: var(--color-text-muted);">{info['name']}</div>
                        </div>
'''
        html += f'''
                    </div>
                </div>
                
                <!-- FAQ Section -->
                <div class="kpi-card" style="margin-top: var(--space-6); text-align: left; padding: var(--space-6);">
                    <h2 style="color: var(--color-primary); margin-bottom: var(--space-4);">Frequently Asked Questions</h2>
                    
                    <div style="border-bottom: 1px solid var(--color-divider); padding: var(--space-4) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">What is {nb_name}'s crime rate?</div>
                        <div style="color: var(--color-text-muted);">{nb_name} recorded {total} crimes in January 2026, including {violent} violent crimes and {property_crime} property crimes.</div>
                    </div>
                    
                    <div style="border-bottom: 1px solid var(--color-divider); padding: var(--space-4) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">Is {nb_name} a safe neighbourhood?</div>
                        <div style="color: var(--color-text-muted);">With a safety score of {safety_score}/100 (Grade {grade}), {nb_name} is considered {grade_text.lower()}. {"It has below-average crime for the region." if safety_score >= 60 else "Crime levels are typical for the area." if safety_score >= 40 else "Extra caution is advised."}</div>
                    </div>
                    
                    <div style="padding: var(--space-4) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">Which police force covers {nb_name}?</div>
                        <div style="color: var(--color-text-muted);">{nb_name} is policed by <a href="/force/{force_slug}/">{force_name}</a>.</div>
                    </div>
                </div>
                
                <!-- CTA -->
                <div style="background: linear-gradient(135deg, var(--color-primary), #0f766e); color: white; text-align: center; padding: var(--space-8); border-radius: var(--radius-lg); margin-top: var(--space-6);">
                    <h3 style="margin-bottom: var(--space-2);">Compare {nb_name}</h3>
                    <p style="opacity: 0.9;">See how this neighbourhood compares to others</p>
                    <a href="/" style="display: inline-block; background: white; color: var(--color-primary); padding: var(--space-3) var(--space-6); border-radius: var(--radius-md); text-decoration: none; font-weight: 600; margin-top: var(--space-4);">Compare Neighbourhoods →</a>
                </div>
            </div>
        </section>
    </main>
'''
    else:
        # Minimal page without data
        html += f'''
    <main>
        <div class="container">
            <div class="breadcrumb">
                <a href="/">Home</a> › <a href="/forces/">Forces</a> › <a href="/force/{force_slug}/">{force_name}</a> › {nb_name}
            </div>
        </div>
        
        <section class="hero" style="padding: var(--space-8) 0;">
            <div class="container">
                <h1>{nb_name}</h1>
                <p class="hero-sub">{force_name}</p>
            </div>
        </section>
        
        <section style="padding-bottom: var(--space-12);">
            <div class="container" style="max-width: 800px;">
                <div class="kpi-card" style="text-align: center; padding: var(--space-8);">
                    <div class="kpi-label">Status</div>
                    <div class="kpi-value" style="font-size: var(--text-lg);">Data Loading</div>
                    <div class="kpi-detail">Crime statistics are being collected for this neighbourhood</div>
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
    
    # Load crime data
    crime_data = {}
    crimes_dir = f"{DATA_DIR}/neighbourhood_crimes"
    if os.path.exists(crimes_dir):
        for fname in os.listdir(crimes_dir):
            if fname.endswith('.json'):
                with open(f"{crimes_dir}/{fname}") as f:
                    data = json.load(f)
                    key = fname.replace('.json', '')
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
            key = f"{force_id}_{nb['id']}"
            nb_crime = crime_data.get(key)
            
            os.makedirs(f"{OUTPUT_DIR}/neighbourhood/{force_slug}/{nb_slug}", exist_ok=True)
            with open(f"{OUTPUT_DIR}/neighbourhood/{force_slug}/{nb_slug}/index.html", 'w') as f:
                f.write(generate_neighbourhood_page(force, nb, nb_crime))
            
            generated += 1
            if generated % 500 == 0:
                print(f"  Generated {generated}/{total}...")
    
    print(f"\n{'='*50}")
    print(f"Generated {generated} neighbourhood pages")


if __name__ == "__main__":
    main()
