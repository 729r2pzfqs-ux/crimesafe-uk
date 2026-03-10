#!/usr/bin/env python3
"""
Generate search data for CrimeSafe UK
Uses rankings.json for percentile-based scores
"""

import json
import os
import re

DATA_DIR = "data"
OUTPUT_DIR = "."

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def main():
    # Load forces data
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    # Load rankings for scores
    rankings_lookup = {}
    rankings_path = f"{DATA_DIR}/rankings.json"
    if os.path.exists(rankings_path):
        with open(rankings_path) as f:
            rankings = json.load(f)
        for r in rankings:
            key = f"{r['force_slug']}/{r['nb_slug']}"
            rankings_lookup[key] = r.get('score')
            # Also index by nb_slug alone as fallback
            rankings_lookup[r['nb_slug']] = r.get('score')
    
    # Build search arrays
    # Forces: [name, neighbourhood_count, slug]
    forces_search = []
    for force in forces_data['forces']:
        forces_search.append([
            force['name'],
            len(force['neighbourhoods']),
            slugify(force['name'])
        ])
    
    # Neighbourhoods: [name, force_name, score, force_slug, nb_slug]
    neighbourhoods_search = []
    for force in forces_data['forces']:
        force_slug = slugify(force['name'])
        for nb in force['neighbourhoods']:
            nb_slug = slugify(nb['name'])
            
            # Get score from rankings.json
            key = f"{force_slug}/{nb_slug}"
            score = rankings_lookup.get(key) or rankings_lookup.get(nb_slug)
            
            neighbourhoods_search.append([
                nb['name'],
                force['name'],
                score,
                force_slug,
                nb_slug
            ])
    
    # Write JS files
    with open(f"{OUTPUT_DIR}/forces_search.js", 'w') as f:
        f.write(f"const FORCES_SEARCH = {json.dumps(forces_search, ensure_ascii=False)};\n")
    
    with open(f"{OUTPUT_DIR}/neighbourhoods_search.js", 'w') as f:
        f.write(f"const NEIGHBOURHOODS_SEARCH = {json.dumps(neighbourhoods_search, ensure_ascii=False)};\n")
    
    print(f"Generated search data:")
    print(f"  - {len(forces_search)} forces")
    print(f"  - {len(neighbourhoods_search)} neighbourhoods")
    print(f"  - {sum(1 for n in neighbourhoods_search if n[2] is not None)} with scores")

if __name__ == "__main__":
    main()
