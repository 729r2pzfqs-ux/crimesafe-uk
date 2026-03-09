#!/usr/bin/env python3
"""
Fetch bulk crime data from data.police.uk
Uses force-level crime counts which is MUCH faster than neighbourhood boundaries
"""

import json
import os
import time
import urllib.request
from collections import defaultdict
from datetime import datetime

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
                print(f"  ✗ Failed: {url[:80]}... - {e}")
                return None
    return None

def fetch_force_crimes(force_id, date="2026-01"):
    """Fetch all crimes for a force (no location data)"""
    # crimes-no-location gives force-level totals
    url = f"{API_BASE}/crimes-no-location?category=all-crime&force={force_id}&date={date}"
    return fetch_json(url)

def fetch_neighbourhood_with_centroid(force_id, neighbourhood_id):
    """Fetch neighbourhood details including location"""
    details = fetch_json(f"{API_BASE}/{force_id}/{neighbourhood_id}")
    if details and details.get('centre'):
        return {
            'lat': details['centre'].get('latitude'),
            'lng': details['centre'].get('longitude'),
            'population': details.get('population'),
            'description': details.get('description', '')
        }
    return None

def fetch_crimes_at_point(lat, lng, date="2026-01"):
    """Fetch crimes near a point (1 mile radius) - fast!"""
    url = f"{API_BASE}/crimes-street/all-crime?lat={lat}&lng={lng}&date={date}"
    return fetch_json(url)

def main():
    print("Loading forces data...")
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    os.makedirs(f"{DATA_DIR}/neighbourhood_crimes", exist_ok=True)
    
    total = sum(len(f['neighbourhoods']) for f in forces_data['forces'])
    processed = 0
    success = 0
    
    for force in forces_data['forces']:
        force_id = force['id']
        force_name = force['name']
        
        print(f"\n{force_name} ({len(force['neighbourhoods'])} neighbourhoods)...")
        
        for nb in force['neighbourhoods']:
            nb_id = nb['id']
            nb_name = nb['name']
            processed += 1
            
            # Cache file
            cache_file = f"{DATA_DIR}/neighbourhood_crimes/{force_id}_{nb_id}.json"
            if os.path.exists(cache_file):
                success += 1
                continue
            
            # Get neighbourhood centroid
            details = fetch_neighbourhood_with_centroid(force_id, nb_id)
            if not details or not details.get('lat'):
                print(f"  [{processed}/{total}] {nb_name}: no centroid")
                continue
            
            # Fetch crimes at centroid (1 mile radius)
            crimes = fetch_crimes_at_point(details['lat'], details['lng'])
            
            if crimes is not None:
                # Aggregate by category
                counts = defaultdict(int)
                for crime in crimes:
                    counts[crime.get('category', 'other')] += 1
                
                result = {
                    "neighbourhood_id": nb_id,
                    "neighbourhood_name": nb_name,
                    "force_id": force_id,
                    "lat": details['lat'],
                    "lng": details['lng'],
                    "population": details.get('population'),
                    "total_crimes": len(crimes),
                    "categories": dict(counts),
                    "date": "2026-01"
                }
                
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                
                success += 1
                print(f"  [{processed}/{total}] {nb_name}: {len(crimes)} crimes")
            else:
                print(f"  [{processed}/{total}] {nb_name}: fetch failed")
            
            time.sleep(0.15)  # Rate limit
    
    print(f"\n{'='*50}")
    print(f"Processed: {processed}/{total}")
    print(f"Success: {success}")

if __name__ == "__main__":
    main()
