#!/usr/bin/env python3
"""
Fetch crime data for all neighbourhoods
"""

import json
import os
import time
import urllib.request
from datetime import datetime
from collections import defaultdict

API_BASE = "https://data.police.uk/api"
DATA_DIR = "data"

def fetch_json(url, retries=3):
    """Fetch JSON from URL with retries"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                return None
    return None

def fetch_crimes_for_force(force_id, date="2026-01"):
    """Fetch all crimes for a force in a given month"""
    url = f"{API_BASE}/crimes-no-location?category=all-crime&force={force_id}&date={date}"
    # Actually, let's use force-level summary which is faster
    
    # Better approach: fetch crimes by location for the whole force area
    # But that's complex. Let's use neighbourhood-level data
    return None

def fetch_neighbourhood_crime_summary(force_id, neighbourhood_id, months=12):
    """
    Fetch boundary and then crimes for a neighbourhood
    Returns aggregated crime counts
    """
    # Get boundary
    boundary = fetch_json(f"{API_BASE}/{force_id}/{neighbourhood_id}/boundary")
    if not boundary or len(boundary) < 3:
        return None
    
    # Build poly parameter (limit points to avoid URL too long)
    points = boundary[::max(1, len(boundary)//20)]  # Sample up to 20 points
    poly = ":".join([f"{p['latitude']},{p['longitude']}" for p in points])
    
    if len(poly) > 3500:  # URL limit safety
        points = boundary[::max(1, len(boundary)//10)]
        poly = ":".join([f"{p['latitude']},{p['longitude']}" for p in points])
    
    # Fetch latest month
    url = f"{API_BASE}/crimes-street/all-crime?poly={poly}&date=2026-01"
    crimes = fetch_json(url)
    
    if crimes is None:
        return None
    
    # Aggregate by category
    counts = defaultdict(int)
    for crime in crimes:
        counts[crime.get('category', 'other')] += 1
    
    return {
        "total": len(crimes),
        "categories": dict(counts),
        "date": "2026-01"
    }

def main():
    # Load forces data
    with open(f"{DATA_DIR}/forces.json") as f:
        data = json.load(f)
    
    os.makedirs(f"{DATA_DIR}/crimes", exist_ok=True)
    
    total_neighbourhoods = sum(len(f['neighbourhoods']) for f in data['forces'])
    processed = 0
    
    for force in data['forces']:
        force_id = force['id']
        force_name = force['name']
        force_crimes = {}
        
        print(f"\n{force_name} ({len(force['neighbourhoods'])} neighbourhoods)...")
        
        for nb in force['neighbourhoods']:
            nb_id = nb['id']
            nb_name = nb['name']
            
            processed += 1
            
            # Check if already fetched
            cache_file = f"{DATA_DIR}/crimes/{force_id}_{nb_id}.json"
            if os.path.exists(cache_file):
                print(f"  [{processed}/{total_neighbourhoods}] {nb_name} (cached)")
                continue
            
            crimes = fetch_neighbourhood_crime_summary(force_id, nb_id)
            
            if crimes:
                with open(cache_file, 'w') as f:
                    json.dump(crimes, f)
                print(f"  [{processed}/{total_neighbourhoods}] {nb_name}: {crimes['total']} crimes")
            else:
                print(f"  [{processed}/{total_neighbourhoods}] {nb_name}: no data")
            
            time.sleep(0.2)  # Rate limit
    
    print(f"\n{'='*50}")
    print(f"Crime data fetched for {processed} neighbourhoods")

if __name__ == "__main__":
    main()
