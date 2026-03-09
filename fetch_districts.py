#!/usr/bin/env python3
"""
Extract and fetch district data from neighbourhood details
"""

import json
import os
import re
import time
import urllib.request
from collections import defaultdict

API_BASE = "https://data.police.uk/api"
DATA_DIR = "data"

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return None
    return None

def extract_district_from_url(url_force):
    """Extract district name from URL like /met/Tower-Hamlets/..."""
    if not url_force:
        return None
    # Pattern: /area/your-area/FORCE/DISTRICT/NEIGHBOURHOOD
    match = re.search(r'/area/your-area/[^/]+/([^/]+)/', url_force)
    if match:
        return match.group(1).replace('-', ' ')
    return None

def main():
    # Load forces data
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    os.makedirs(f"{DATA_DIR}/districts", exist_ok=True)
    
    # Build district mapping
    districts = defaultdict(lambda: {"neighbourhoods": [], "force": None})
    
    total = sum(len(f['neighbourhoods']) for f in forces_data['forces'])
    processed = 0
    
    for force in forces_data['forces']:
        force_id = force['id']
        force_name = force['name']
        
        print(f"{force_name}...")
        
        for nb in force['neighbourhoods']:
            nb_id = nb['id']
            processed += 1
            
            # Check cache
            cache_file = f"{DATA_DIR}/districts/{force_id}_{nb_id}.json"
            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    details = json.load(f)
            else:
                # Fetch details
                details = fetch_json(f"{API_BASE}/{force_id}/{nb_id}")
                if details:
                    with open(cache_file, 'w') as f:
                        json.dump(details, f)
                    time.sleep(0.1)
            
            if details:
                district = extract_district_from_url(details.get('url_force', ''))
                if district:
                    key = f"{force_id}|{district}"
                    districts[key]["neighbourhoods"].append({
                        "id": nb_id,
                        "name": nb['name']
                    })
                    districts[key]["force"] = force_name
                    districts[key]["force_id"] = force_id
                    districts[key]["district"] = district
            
            if processed % 200 == 0:
                print(f"  [{processed}/{total}] {len(districts)} districts found")
    
    # Save districts
    districts_list = []
    for key, data in districts.items():
        districts_list.append({
            "force_id": data["force_id"],
            "force": data["force"],
            "district": data["district"],
            "neighbourhood_count": len(data["neighbourhoods"]),
            "neighbourhoods": data["neighbourhoods"]
        })
    
    with open(f"{DATA_DIR}/districts.json", 'w') as f:
        json.dump(districts_list, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Found {len(districts_list)} districts")
    print(f"Saved to {DATA_DIR}/districts.json")

if __name__ == "__main__":
    main()
