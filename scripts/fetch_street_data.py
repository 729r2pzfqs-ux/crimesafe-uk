#!/usr/bin/env python3
"""
Fetch crime data for all streets and cache locally.
Run monthly via cron: 0 3 1 * * cd ~/clawd/crimesafe-uk && python3 scripts/fetch_street_data.py
"""
import json
import requests
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
STREETS_FILE = DATA_DIR / 'top_streets.json'
OUTPUT_FILE = DATA_DIR / 'street_crime_data.json'

def get_latest_month():
    """Get the most recent available month (usually 2-3 months ago)"""
    now = datetime.now()
    year = now.year
    month = now.month - 2
    if month < 1:
        month += 12
        year -= 1
    return f"{year}-{month:02d}"

def fetch_crimes(lat, lng, date):
    """Fetch crimes near a location"""
    try:
        url = f"https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={date}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 503:
            time.sleep(2)
            resp = requests.get(url, timeout=15)
            return resp.json() if resp.status_code == 200 else []
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

def process_crimes(crimes):
    """Process raw crime data into summary stats"""
    if not crimes:
        return {"total": 0, "types": {}, "score": 50}
    
    types = {}
    for c in crimes:
        cat = c.get('category', 'other-crime')
        types[cat] = types.get(cat, 0) + 1
    
    total = len(crimes)
    score = max(0, min(100, int(100 - (total / 10))))
    
    return {
        "total": total,
        "types": dict(sorted(types.items(), key=lambda x: -x[1])[:10]),
        "score": score,
        "top_crime": max(types.items(), key=lambda x: x[1])[0] if types else None
    }

def main():
    print(f"=== Street Crime Data Fetcher ===")
    print(f"Started: {datetime.now()}")
    
    with open(STREETS_FILE) as f:
        streets = json.load(f)
    
    print(f"Processing {len(streets)} streets...")
    
    date = get_latest_month()
    print(f"Fetching data for: {date}")
    
    results = {}
    
    for i, street in enumerate(streets):
        slug = street['slug']
        lat = street.get('lat', '51.5074')
        lng = street.get('lng', '-0.1278')
        
        crimes = fetch_crimes(lat, lng, date)
        stats = process_crimes(crimes)
        
        results[slug] = {
            "name": street['name'],
            "city": street.get('city', 'UK'),
            "lat": lat,
            "lng": lng,
            "month": date,
            "stats": stats
        }
        
        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(streets)} streets...")
            time.sleep(0.3)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({
            "updated": datetime.now().isoformat(),
            "month": date,
            "streets": results
        }, f, indent=2)
    
    print(f"\n✅ Saved data for {len(results)} streets to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
