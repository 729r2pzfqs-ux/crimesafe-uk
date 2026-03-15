#!/usr/bin/env python3
"""
Generate neighbourhood pages with full content (HoodSafe style)
Uses percentile-based scoring for even distribution
"""

import json
import os
import re
import math
from generate_site import get_header, get_footer, slugify, CRIME_WEIGHTS

DATA_DIR = "data"
OUTPUT_DIR = "."

# Global forces lookup for internal links
forces = {}

# District mapping
DISTRICT_LOOKUP = {}

# City mapping for neighbourhoods (based on police force areas)
CITY_MAPPING = {
    'metropolitan': 'london',
    'west-midlands': 'birmingham',
    'greater-manchester': 'manchester',
    'west-yorkshire': 'leeds',
    'merseyside': 'liverpool',
    'south-yorkshire': 'sheffield',
    'avon-and-somerset': 'bristol',
    'west-mercia': 'coventry',
    'northumbria': 'newcastle',
    'hampshire': 'southampton',
    'thames-valley': 'oxford',
    'nottinghamshire': 'nottingham',
    'leicestershire': 'leicester',
    'south-wales': 'cardiff',
    'sussex': 'brighton',
    'humberside': 'hull',
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def find_nearby_neighbourhoods(target_key, all_crime_data, max_distance=10, limit=6):
    """Find nearby neighbourhoods within max_distance km"""
    target = all_crime_data.get(target_key)
    if not target or 'lat' not in target or 'lng' not in target:
        return []
    
    target_lat = float(target['lat'])
    target_lng = float(target['lng'])
    
    nearby = []
    for key, data in all_crime_data.items():
        if key == target_key:
            continue
        if 'lat' not in data or 'lng' not in data:
            continue
        try:
            dist = haversine_distance(target_lat, target_lng, float(data['lat']), float(data['lng']))
            if dist <= max_distance:
                nearby.append((key, data, dist))
        except:
            continue
    
    nearby.sort(key=lambda x: x[2])
    return nearby[:limit]

def load_district_mapping():
    """Load district to neighbourhood mapping"""
    global DISTRICT_LOOKUP
    try:
        with open('data/districts.json', 'r') as f:
            districts = json.load(f)
        for d in districts:
            force_id = d['force_id']
            district_slug = d['district'].lower().replace(' ', '-')
            for nb in d.get('neighbourhoods', []):
                nb_id = nb['id']
                key = f"{force_id}_{nb_id}"
                DISTRICT_LOOKUP[key] = {
                    'district_name': d['district'].title(),
                    'district_slug': district_slug
                }
    except:
        pass

def build_internal_links_html(nb_name, nearby, district_info, city_slug):
    """Build the internal links HTML section"""
    parts = []
    
    # Nearby neighbourhoods
    if nearby and len(nearby) > 0:
        links = []
        for key, data, dist in nearby[:6]:
            nb_n = data.get('neighbourhood_name', key.split('_')[1] if '_' in key else key)
            f_id = data.get('force_id', key.split('_')[0])
            force_info = forces.get(f_id, {})
            force_name_lookup = force_info.get('name', f_id) if force_info else f_id
            f_slug = slugify(force_name_lookup)
            nb_s = slugify(nb_n)
            links.append('<a href="/neighbourhood/' + f_slug + '/' + nb_s + '/" style="color: var(--color-primary);">' + nb_n + '</a>')
        nearby_html = '<div style="margin-bottom: var(--space-3);"><span style="font-size: var(--text-sm); color: var(--color-text-muted);">Nearby: </span>' + ' · '.join(links) + '</div>'
        parts.append(nearby_html)
    
    # District link
    if district_info:
        d_slug = district_info['district_slug']
        d_name = district_info['district_name']
        parts.append('<div style="margin-bottom: var(--space-3);"><span style="font-size: var(--text-sm); color: var(--color-text-muted);">District: </span><a href="/district/' + d_slug + '/" style="color: var(--color-primary);">' + d_name + '</a></div>')
    
    # City link
    if city_slug:
        city_name = city_slug.replace('-', ' ').title()
        parts.append('<div style="margin-bottom: var(--space-3);"><span style="font-size: var(--text-sm); color: var(--color-text-muted);">City: </span><a href="/city/' + city_slug + '/" style="color: var(--color-primary);">' + city_name + '</a></div>')
    
    # Compare links
    if nearby and len(nearby) >= 2:
        compare_links = []
        for key, data, dist in nearby[:3]:
            nb_n = data.get('neighbourhood_name', key.split('_')[1] if '_' in key else key)
            nb_s = slugify(nb_n)
            slug1 = slugify(nb_name)
            if slug1 < nb_s:
                compare_url = '/compare/' + slug1 + '-vs-' + nb_s + '/'
            else:
                compare_url = '/compare/' + nb_s + '-vs-' + slug1 + '/'
            compare_links.append('<a href="' + compare_url + '" style="color: var(--color-primary);">vs ' + nb_n + '</a>')
        parts.append('<div><span style="font-size: var(--text-sm); color: var(--color-text-muted);">Compare: </span>' + ' · '.join(compare_links) + '</div>')
    else:
        parts.append('<div><span style="font-size: var(--text-sm); color: var(--color-text-muted);">Compare: </span><a href="/compare/" style="color: var(--color-primary);">Find similar areas</a></div>')
    
    if not parts:
        return ''
    
    return '''
                <div class="kpi-card" style="margin-top: var(--space-6); text-align: left; padding: var(--space-5);">
                    <h3 style="color: var(--color-primary); margin-bottom: var(--space-4); font-size: var(--text-base);">Explore More</h3>
                    ''' + '\n                    '.join(parts) + '''
                </div>
'''

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

def generate_neighbourhood_page(force_name, force_slug, nb_name, nb_slug, crime_data=None, safety_score=None, regional_score=None, internal_links_html=''):
    """Generate a neighbourhood detail page with full content"""
    
    # Calculate stats - show data even for 0 crimes (safest areas!)
    if crime_data is not None:
        total = crime_data['total_crimes']
        categories = crime_data.get('categories', {})
        population = crime_data.get('population', 0)
        crime_rate = crime_data.get('crime_rate_per_1000', 0)
        
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
        population = 0
        crime_rate = 0
    
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
                    <div style="text-align: center;">
                        <div style="width: 120px; height: 120px; border-radius: 50%; background: {score_color}; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; margin: 0 auto;">
                            <span style="font-size: var(--text-2xl); font-weight: 700; line-height: 1;">{safety_score}</span>
                        </div>
                        <div style="margin-top: var(--space-2); font-size: var(--text-sm); color: var(--color-text-muted);">UK Score</div>
                    </div>
                    {f'''<div style="text-align: center;">
                        <div style="width: 120px; height: 120px; border-radius: 50%; background: {"#22c55e" if regional_score >= 60 else "#eab308" if regional_score >= 40 else "#f97316" if regional_score >= 20 else "#ef4444"}; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; margin: 0 auto;">
                            <span style="font-size: var(--text-2xl); font-weight: 700; line-height: 1;">{regional_score}</span>
                        </div>
                        <div style="margin-top: var(--space-2); font-size: var(--text-sm); color: var(--color-text-muted);">{force_name.split()[0]} Score</div>
                    </div>''' if regional_score is not None else ''}
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
                    <div class="kpi-card">
                        <div class="kpi-label">Population</div>
                        <div class="kpi-value">{population:,}</div>
                        <div class="kpi-detail">Census 2021</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Crime Rate</div>
                        <div class="kpi-value">{crime_rate:.1f}</div>
                        <div class="kpi-detail">per 1,000 people</div>
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
                
                {internal_links_html}
                
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
    global forces
    print("Loading data...")
    
    # Load forces
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    forces = {f['id']: f for f in forces_data['forces']}
    
    # Load district mapping for internal links
    load_district_mapping()
    print(f"Loaded {len(DISTRICT_LOOKUP)} district mappings")
    
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
    
    # Load regional scores
    regional_scores = {}
    regional_path = f"{DATA_DIR}/regional_scores.json"
    if os.path.exists(regional_path):
        with open(regional_path) as f:
            regional_scores = json.load(f)
        print(f"Loaded {len(regional_scores)} regional scores")
    
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
        
        # Get regional score
        regional_key = f"{force_id}_{crime_data.get('neighbourhood_id', '')}"
        regional_score = regional_scores.get(regional_key)
        
        # Build internal links
        nearby = find_nearby_neighbourhoods(key, all_crime_data, max_distance=10, limit=6)
        district_info = DISTRICT_LOOKUP.get(key)
        city_slug = CITY_MAPPING.get(force_id)
        internal_links_html = build_internal_links_html(nb_name, nearby, district_info, city_slug)
        
        # Generate page
        out_dir = f"{OUTPUT_DIR}/neighbourhood/{force_slug}/{nb_slug}"
        os.makedirs(out_dir, exist_ok=True)
        
        html = generate_neighbourhood_page(force['name'], force_slug, nb_name, nb_slug, crime_data, safety_score, regional_score, internal_links_html)
        with open(f"{out_dir}/index.html", 'w') as f:
            f.write(html)
        
        generated += 1
        if generated % 500 == 0:
            print(f"  Generated {generated}/{len(all_crime_data)}...")
    
    print(f"\n{'='*50}")
    print(f"Generated {generated} neighbourhood pages")


if __name__ == "__main__":
    main()
