#!/usr/bin/env python3
"""
Generate rankings.json from crime data with percentile scoring.
"""

import json
import os
import re

DATA_DIR = "data"
CRIME_DIR = f"{DATA_DIR}/neighbourhood_crimes"

CRIME_WEIGHTS = {
    'violent-crime': 2.0,
    'robbery': 1.8,
    'burglary': 1.5,
    'vehicle-crime': 1.3,
    'criminal-damage-arson': 1.2,
    'drugs': 1.1,
    'public-order': 1.0,
    'shoplifting': 0.8,
    'other-theft': 0.9,
    'theft-from-the-person': 1.0,
    'bicycle-theft': 0.7,
    'anti-social-behaviour': 0.5,
    'possession-of-weapons': 1.5,
    'other-crime': 1.0
}

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

def get_grade(score):
    if score >= 80: return 'A'
    elif score >= 60: return 'B'
    elif score >= 40: return 'C'
    elif score >= 20: return 'D'
    return 'F'

def main():
    # Load forces for name lookup
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    force_names = {f['id']: f['name'] for f in forces_data['forces']}
    
    # Load all crime data
    print("Loading crime data...")
    all_data = []
    
    for fname in os.listdir(CRIME_DIR):
        if not fname.endswith('.json'):
            continue
        
        with open(f"{CRIME_DIR}/{fname}") as f:
            data = json.load(f)
        
        force_id = data.get('force_id', '')
        nb_id = data.get('neighbourhood_id', '')
        nb_name = data.get('neighbourhood_name', '')
        categories = data.get('categories', {})
        total_crimes = data.get('total_crimes', 0)
        
        # Calculate weighted crime score
        weighted = sum(count * CRIME_WEIGHTS.get(cat, 1.0) for cat, count in categories.items())
        
        force_name = force_names.get(force_id, force_id.replace('-', ' ').title())
        force_slug = slugify(force_name)
        nb_slug = slugify(nb_name)
        
        all_data.append({
            'name': nb_name,
            'force': force_name,
            'force_id': force_id,
            'force_slug': force_slug,
            'nb_id': nb_id,
            'nb_slug': nb_slug,
            'total_crimes': total_crimes,
            'weighted': weighted
        })
    
    print(f"Loaded {len(all_data)} neighbourhoods")
    
    # Sort by weighted crime (ascending - lowest crime first = safest)
    all_data.sort(key=lambda x: x['weighted'])
    
    # Assign percentile scores
    total = len(all_data)
    rankings = []
    
    for i, data in enumerate(all_data):
        percentile = (i / max(1, total - 1)) * 100
        score = round(100 - percentile)  # Flip so lower crime = higher score
        grade = get_grade(score)
        
        rankings.append({
            'name': data['name'],
            'force': data['force'],
            'force_slug': data['force_slug'],
            'nb_slug': data['nb_slug'],
            'score': score,
            'grade': grade,
            'total_crimes': data['total_crimes']
        })
    
    # Save rankings (already sorted by safety score descending)
    with open(f"{DATA_DIR}/rankings.json", 'w') as f:
        json.dump(rankings, f, indent=2)
    
    print(f"\n✅ Generated rankings.json with {len(rankings)} neighbourhoods")
    
    # Show some stats
    print("\n📊 Score distribution:")
    for threshold in [0, 1, 10, 20, 40, 60, 80, 100]:
        count = len([r for r in rankings if r['score'] <= threshold])
        print(f"  Score ≤ {threshold}: {count} neighbourhoods")
    
    print("\n🔴 Top 10 highest crime (score 0-1):")
    for r in reversed(rankings[-10:]):
        print(f"  {r['name']} ({r['force']}): score={r['score']}, crimes={r['total_crimes']}")
    
    print("\n🟢 Top 10 safest (score 80+):")
    for r in rankings[:10]:
        print(f"  {r['name']} ({r['force']}): score={r['score']}, crimes={r['total_crimes']}")

if __name__ == '__main__':
    main()
