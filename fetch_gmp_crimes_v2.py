#!/usr/bin/env python3
"""Fetch GMP crime data using neighbourhood centroids"""

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
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
    return None

def get_centroid(boundary):
    """Calculate centroid of polygon"""
    lats = [float(p['latitude']) for p in boundary]
    lngs = [float(p['longitude']) for p in boundary]
    return sum(lats)/len(lats), sum(lngs)/len(lngs)

def fetch_neighbourhood_crimes(force_id, nb_id, date="2026-01"):
    """Fetch crimes using neighbourhood centroid"""
    # Get boundary
    boundary = fetch_json(f"{API_BASE}/{force_id}/{nb_id}/boundary")
    if not boundary or len(boundary) < 3:
        return None
    
    # Get centroid
    lat, lng = get_centroid(boundary)
    
    # Fetch crimes at point
    url = f"{API_BASE}/crimes-street/all-crime?lat={lat}&lng={lng}&date={date}"
    crimes = fetch_json(url)
    
    if not crimes:
        return {'total': 0, 'categories': {}, 'date': date}
    
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
    
    gmp = next(f for f in data['forces'] if f['id'] == FORCE_ID)
    neighbourhoods = gmp['neighbourhoods']
    
    os.makedirs(f"{DATA_DIR}/crimes", exist_ok=True)
    
    print(f"Fetching crimes for {len(neighbourhoods)} GMP neighbourhoods...")
    total_crimes = 0
    
    for i, nb in enumerate(neighbourhoods):
        nb_id = nb['id']
        nb_name = nb['name']
        cache_file = f"{DATA_DIR}/crimes/{FORCE_ID}_{nb_id}.json"
        
        crimes = fetch_neighbourhood_crimes(FORCE_ID, nb_id)
        
        if crimes:
            with open(cache_file, 'w') as f:
                json.dump(crimes, f)
            total_crimes += crimes['total']
            print(f"  [{i+1}/{len(neighbourhoods)}] {nb_name}: {crimes['total']} crimes")
        else:
            print(f"  [{i+1}/{len(neighbourhoods)}] {nb_name}: error")
        
        time.sleep(0.12)
    
    print(f"\n✅ GMP: {total_crimes} total crimes across {len(neighbourhoods)} neighbourhoods")

if __name__ == "__main__":
    main()
