#!/usr/bin/env python3
"""
Generate neighbourhood pages with full content (HoodSafe style)
Uses percentile-based scoring for even distribution
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

def calculate_weighted_crime(categories):
    """Calculate weighted crime score"""
    weighted = 0
    for cat, count in categories.items():
        if cat in CRIME_WEIGHTS:
            weighted += count * CRIME_WEIGHTS[cat]['weight']
        else:
            weighted += count * 1.0
    return weighted

def calculate_percentile_scores(all_crime_data):
    """
    Calculate percentile-based safety scores using per-capita crime rates.
    Lower crime rate per 1000 = higher percentile = higher safety score.
    """
    # Use per-capita crime rate for fairer comparison
    crime_rates = []
    for key, data in all_crime_data.items():
        # Use crime_rate_per_1000 if available, otherwise fall back to weighted calculation
        rate = data.get('crime_rate_per_1000')
        if rate is None:
            # Fallback: calculate from total_crimes and estimated population
            pop = data.get('population', 12098)  # National average
            total = data.get('total_crimes', 0)
            rate = (total / pop) * 1000 if pop > 0 else 0
        crime_rates.append((key, rate))
    
    # Sort by crime rate (ascending - lowest rate first = safest)
    crime_rates.sort(key=lambda x: x[1])
    
    # Assign percentile scores
    total = len(crime_rates)
    scores = {}
    for i, (key, rate) in enumerate(crime_rates):
        # Percentile: what % of neighbourhoods have MORE crime than this one
        percentile = (i / max(1, total - 1)) * 100
        # Safest (lowest crime rate) get highest scores
        safety_score = round(100 - percentile)
        scores[key] = safety_score
    
    return scores

def generate_neighbourhood_page(force_name, force_slug, nb_name, nb_slug, crime_data=None, safety_score=None):
    """Generate a neighbourhood detail page with full content"""
    
    # Calculate stats - show data even for 0 crimes (safest areas!)
    if crime_data is not None:
        total = crime_data['total_crimes']
        categories = crime_data.get('categories', {})
        
        if safety_score is None:
            safety_score = 50  # Default if not provided
        
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
    
    if safety_score:
        title = f"{nb_name} Crime Rate 2026 — Safety Score {safety_score}/100 | CrimeSafe UK"
        desc = f"Is {nb_name} safe? Safety Score: {safety_score}/100. View {total:,} crimes reported in January 2026, compare with nearby areas, and see crime breakdown."
    else:
        title = f"{nb_name} Crime Statistics 2026 | CrimeSafe UK"
        desc = f"Crime statistics for {nb_name} in {force_name}. View latest crime data and safety information."
    html = get_header(title, desc)
    
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
                        {nb_name} has a safety score of <strong>{safety_score}/100</strong>, placing it in the <strong>{"top " + str(100-safety_score) + "%" if safety_score >= 50 else "bottom " + str(safety_score) + "%"}</strong> of UK neighbourhoods.
                        In January 2026, police recorded {total} crimes in this area, including {violent} violent offences.
                    </p>
                    <p style="color: var(--color-text-muted);">
                        {"This area has lower crime rates than most UK neighbourhoods, making it a relatively safe place to live or visit." if safety_score >= 60 else "This area has average crime levels compared to other UK neighbourhoods. As with any area, stay aware of your surroundings." if safety_score >= 40 else "This area has higher crime rates than most UK neighbourhoods. Take extra precautions with personal belongings and avoid walking alone at night."}
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
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">Is {nb_name} safe to live in?</div>
                        <div style="color: var(--color-text-muted);">{nb_name} has a Safety Score of {safety_score}/100, rated "{grade_text}". This score is based on {total:,} crimes reported in January 2026.</div>
                    </div>
                    
                    <div style="border-bottom: 1px solid var(--color-divider); padding: var(--space-4) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">What is {nb_name}'s crime rate?</div>
                        <div style="color: var(--color-text-muted);">{nb_name} recorded {total:,} crimes in January 2026, including {violent} violent crimes and {property_crime} property crimes.</div>
                    </div>
                    
                    <div style="padding: var(--space-4) 0;">
                        <div style="font-weight: 600; margin-bottom: var(--space-2);">Which police force covers {nb_name}?</div>
                        <div style="color: var(--color-text-muted);">{nb_name} is policed by <a href="/force/{force_slug}/">{force_name}</a>.</div>
                    </div>
                </div>
                
                <!-- FAQ Schema -->
                <script type="application/ld+json">
                {{
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": [
                        {{
                            "@type": "Question",
                            "name": "Is {nb_name} safe to live in?",
                            "acceptedAnswer": {{
                                "@type": "Answer",
                                "text": "{nb_name} has a Safety Score of {safety_score}/100, rated {grade_text}. This score is based on {total:,} crimes reported in January 2026."
                            }}
                        }},
                        {{
                            "@type": "Question",
                            "name": "What is {nb_name}'s crime rate?",
                            "acceptedAnswer": {{
                                "@type": "Answer",
                                "text": "{nb_name} recorded {total:,} crimes in January 2026, including {violent} violent crimes and {property_crime} property crimes."
                            }}
                        }},
                        {{
                            "@type": "Question",
                            "name": "Which police force covers {nb_name}?",
                            "acceptedAnswer": {{
                                "@type": "Answer",
                                "text": "{nb_name} is policed by {force_name}."
                            }}
                        }}
                    ]
                }}
                </script>
                
                <!-- CTA -->
                <div style="background: linear-gradient(135deg, var(--color-primary), #0f766e); color: white; text-align: center; padding: var(--space-8); border-radius: var(--radius-lg); margin-top: var(--space-6);">
                    <h3 style="margin-bottom: var(--space-2);">Compare {nb_name}</h3>
                    <p style="opacity: 0.9;">See how this neighbourhood compares to others</p>
                    <a href="/safest/" style="display: inline-block; background: white; color: var(--color-primary); padding: var(--space-3) var(--space-6); border-radius: var(--radius-md); text-decoration: none; font-weight: 600; margin-top: var(--space-4);">View UK Rankings →</a>
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
                    <div class="kpi-detail">Crime statistics coming soon</div>
                </div>
            </div>
        </section>
    </main>
'''
    
    html += get_footer()
    return html


def main():
    print("Loading data...")
    
    # Load forces
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    forces = {f['id']: f for f in forces_data['forces']}
    
    # Load all crime data from neighbourhood_crimes
    all_crime_data = {}
    crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
    
    # Build lookup by force_id + nb_name_slug
    slug_to_key = {}
    
    if os.path.exists(crime_dir):
        for fname in os.listdir(crime_dir):
            if fname.endswith('.json'):
                key = fname.replace('.json', '')
                with open(f"{crime_dir}/{fname}") as f:
                    data = json.load(f)
                    all_crime_data[key] = data
                    
                    # Create slug-based lookup
                    force_id = data.get('force_id', key.split('_')[0])
                    nb_name = data.get('neighbourhood_name', '')
                    if nb_name:
                        nb_slug = slugify(nb_name)
                        force = forces.get(force_id, {'name': force_id})
                        force_slug = slugify(force['name'])
                        lookup_key = f"{force_slug}/{nb_slug}"
                        slug_to_key[lookup_key] = key
    
    print(f"Loaded crime data for {len(all_crime_data)} neighbourhoods")
    
    # Calculate percentile-based scores
    percentile_scores = calculate_percentile_scores(all_crime_data)
    
    # Show score distribution
    scores = list(percentile_scores.values())
    if scores:
        print(f"Score distribution:")
        print(f"  0-20: {len([s for s in scores if s < 20])}")
        print(f"  20-40: {len([s for s in scores if 20 <= s < 40])}")
        print(f"  40-60: {len([s for s in scores if 40 <= s < 60])}")
        print(f"  60-80: {len([s for s in scores if 60 <= s < 80])}")
        print(f"  80-100: {len([s for s in scores if s >= 80])}")
    
    # Generate pages directly from crime data
    generated = 0
    for key, crime_data in all_crime_data.items():
        force_id = crime_data.get('force_id', key.split('_')[0])
        nb_name = crime_data.get('neighbourhood_name', key.split('_')[1] if '_' in key else key)
        
        force = forces.get(force_id, {'id': force_id, 'name': force_id.replace('-', ' ').title()})
        force_slug = slugify(force['name'])
        nb_slug = slugify(nb_name)
        
        # Get percentile score
        safety_score = percentile_scores.get(key, 50)
        
        # Generate page
        out_dir = f"{OUTPUT_DIR}/neighbourhood/{force_slug}/{nb_slug}"
        os.makedirs(out_dir, exist_ok=True)
        
        html = generate_neighbourhood_page(force['name'], force_slug, nb_name, nb_slug, crime_data, safety_score)
        with open(f"{out_dir}/index.html", 'w') as f:
            f.write(html)
        
        generated += 1
        if generated % 500 == 0:
            print(f"  Generated {generated}/{len(all_crime_data)}...")
    
    print(f"\n{'='*50}")
    print(f"Generated {generated} neighbourhood pages")


if __name__ == "__main__":
    main()
