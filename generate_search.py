#!/usr/bin/env python3
"""
Generate search data for CrimeSafe UK
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
            
            # Get crime score if available
            key = f"{force['id']}_{nb['id']}"
            nb_crime = crime_data.get(key)
            
            if nb_crime and nb_crime.get('total_crimes', 0) > 0:
                # Calculate simple score
                total = nb_crime['total_crimes']
                score = max(0, min(100, round(100 - total / 5)))
            else:
                score = None
            
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
