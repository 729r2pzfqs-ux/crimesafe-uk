#!/usr/bin/env python3
"""Fetch crime data for Greater Manchester Police neighbourhoods"""

import json
import os
import time
import urllib.request

API_BASE = "https://data.police.uk/api"
DATA_DIR = "data"
FORCE_ID = "greater-manchester"

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"    Retry {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
    return None

def fetch_neighbourhood_crimes(force_id, nb_id, date="2026-01"):
    """Fetch crimes using neighbourhood boundary"""
    # Get boundary
    boundary = fetch_json(f"{API_BASE}/{force_id}/{nb_id}/boundary")
    if not boundary or len(boundary) < 3:
        return None
    
    # Sample boundary points (API has URL length limits)
    points = boundary[::max(1, len(boundary)//15)]
    poly = ":".join([f"{p['latitude']},{p['longitude']}" for p in points])
    
    # Fetch crimes in polygon
    url = f"{API_BASE}/crimes-street/all-crime?poly={poly}&date={date}"
    crimes = fetch_json(url)
    
    if not crimes:
        return None
    
    # Aggregate by category
    categories = {}
    for crime in crimes:
        cat = crime.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        'total': len(crimes),
        'categories': categories,
        'date': date
    }

def main():
    with open(f"{DATA_DIR}/forces.json") as f:
        data = json.load(f)
    
    # Find GMP
    gmp = next(f for f in data['forces'] if f['id'] == FORCE_ID)
    neighbourhoods = gmp['neighbourhoods']
    
    os.makedirs(f"{DATA_DIR}/crimes", exist_ok=True)
    
    print(f"Fetching crimes for {len(neighbourhoods)} GMP neighbourhoods...")
    
    for i, nb in enumerate(neighbourhoods):
        nb_id = nb['id']
        nb_name = nb['name']
        cache_file = f"{DATA_DIR}/crimes/{FORCE_ID}_{nb_id}.json"
        
        # Skip if recent cache exists
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cached = json.load(f)
            if cached.get('total', 0) > 0:
                print(f"  [{i+1}/{len(neighbourhoods)}] {nb_name}: {cached['total']} (cached)")
                continue
        
        crimes = fetch_neighbourhood_crimes(FORCE_ID, nb_id)
        
        if crimes:
            with open(cache_file, 'w') as f:
                json.dump(crimes, f)
            print(f"  [{i+1}/{len(neighbourhoods)}] {nb_name}: {crimes['total']} crimes")
        else:
            # Save empty to avoid retry
            with open(cache_file, 'w') as f:
                json.dump({'total': 0, 'categories': {}, 'date': '2026-01'}, f)
            print(f"  [{i+1}/{len(neighbourhoods)}] {nb_name}: no data")
        
        time.sleep(0.15)  # Rate limit
    
    print("\n✅ GMP crime fetch complete")

if __name__ == "__main__":
    main()
