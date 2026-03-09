#!/usr/bin/env python3
"""
UK Crime Data Fetcher
Fetches data from data.police.uk API
"""

import json
import os
import time
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE = "https://data.police.uk/api"
DATA_DIR = "data"

def fetch_json(url, retries=3):
    """Fetch JSON from URL with retries"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
            else:
                print(f"  ✗ Failed: {url} - {e}")
                return None
    return None

def fetch_forces():
    """Fetch all police forces"""
    print("Fetching forces...")
    forces = fetch_json(f"{API_BASE}/forces")
    if forces:
        print(f"  ✓ Found {len(forces)} forces")
    return forces or []

def fetch_neighbourhoods(force_id):
    """Fetch neighbourhoods for a force"""
    neighbourhoods = fetch_json(f"{API_BASE}/{force_id}/neighbourhoods")
    return neighbourhoods or []

def fetch_neighbourhood_details(force_id, neighbourhood_id):
    """Fetch detailed info for a neighbourhood"""
    return fetch_json(f"{API_BASE}/{force_id}/{neighbourhood_id}")

def fetch_crimes(force_id, neighbourhood_id, date=None):
    """Fetch crimes for a neighbourhood boundary"""
    # First get the boundary
    boundary = fetch_json(f"{API_BASE}/{force_id}/{neighbourhood_id}/boundary")
    if not boundary or len(boundary) < 3:
        return None
    
    # Build poly parameter
    poly = ":".join([f"{p['latitude']},{p['longitude']}" for p in boundary])
    
    url = f"{API_BASE}/crimes-street/all-crime?poly={poly}"
    if date:
        url += f"&date={date}"
    
    return fetch_json(url)

def fetch_force_details(force_id):
    """Fetch detailed info for a force"""
    return fetch_json(f"{API_BASE}/forces/{force_id}")

def get_latest_date():
    """Get the latest available crime data date"""
    dates = fetch_json(f"{API_BASE}/crimes-street-dates")
    if dates:
        return dates[0]  # Most recent
    return None

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Get latest data date
    latest_date = get_latest_date()
    print(f"Latest crime data: {latest_date}")
    
    # Fetch all forces
    forces = fetch_forces()
    
    # Fetch force details and neighbourhoods
    all_data = {
        "fetched_at": datetime.now().isoformat(),
        "latest_crime_date": latest_date,
        "forces": []
    }
    
    for i, force in enumerate(forces):
        force_id = force['id']
        force_name = force['name']
        print(f"[{i+1}/{len(forces)}] {force_name}...")
        
        # Get force details
        details = fetch_force_details(force_id)
        
        # Get neighbourhoods
        neighbourhoods = fetch_neighbourhoods(force_id)
        print(f"  ✓ {len(neighbourhoods)} neighbourhoods")
        
        force_data = {
            "id": force_id,
            "name": force_name,
            "details": details,
            "neighbourhoods": neighbourhoods
        }
        
        all_data["forces"].append(force_data)
        time.sleep(0.1)  # Be nice to the API
    
    # Save forces data
    with open(f"{DATA_DIR}/forces.json", 'w') as f:
        json.dump(all_data, f, indent=2)
    
    # Summary
    total_neighbourhoods = sum(len(f['neighbourhoods']) for f in all_data['forces'])
    print(f"\n{'='*50}")
    print(f"Total forces: {len(all_data['forces'])}")
    print(f"Total neighbourhoods: {total_neighbourhoods}")
    print(f"Data saved to {DATA_DIR}/forces.json")

if __name__ == "__main__":
    main()
