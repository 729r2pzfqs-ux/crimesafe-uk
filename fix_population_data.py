#!/usr/bin/env python3
"""
Fix population data for all CrimeSafe UK neighbourhoods.

Uses Census 2021 LSOA population data and police neighbourhood boundaries
to calculate accurate population estimates. Then recalculates per-capita
crime rates and regional scores.

Steps:
1. Download Census 2021 LSOA populations from Nomis API
2. Download LSOA population-weighted centroids from ONS
3. Fetch neighbourhood boundary polygons from Police UK API
4. Point-in-polygon: assign LSOAs to neighbourhoods
5. Update crime data JSONs with population and crime rate
6. Recalculate regional scores

Usage:
    python3 fix_population_data.py [--skip-download] [--force FORCE_ID]

Options:
    --skip-download   Skip downloading LSOA data if already cached
    --force FORCE_ID  Only process a specific force (e.g. avon-and-somerset)
"""

import json
import os
import sys
import time
import math
import csv
import urllib.request
from collections import defaultdict
from io import StringIO

try:
    from shapely.geometry import Point, Polygon
    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False
    print("WARNING: shapely not installed. Install with: pip install shapely")
    print("Falling back to simple point-in-polygon algorithm (slower but works)")

DATA_DIR = "data"
CACHE_DIR = "data/population_cache"

# ─── Simple point-in-polygon (fallback if shapely not available) ───

def point_in_polygon_simple(x, y, polygon_coords):
    """Ray casting algorithm for point-in-polygon test."""
    n = len(polygon_coords)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon_coords[i]
        xj, yj = polygon_coords[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

# ─── API helpers ───

def fetch_json(url, retries=3, delay=1):
    """Fetch JSON with retries and rate limiting."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                return None
    return None

def fetch_csv(url):
    """Fetch CSV data from URL."""
    req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode('utf-8')

# ─── Step 1 & 2: Download LSOA data ───

def download_lsoa_data():
    """Download Census 2021 LSOA populations and centroids."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    pop_file = f"{CACHE_DIR}/lsoa_populations.csv"
    centroid_file = f"{CACHE_DIR}/lsoa_centroids.json"
    
    # Download LSOA populations from Nomis (Census 2021 TS001)
    if not os.path.exists(pop_file):
        print("Downloading Census 2021 LSOA populations from Nomis...")
        all_rows = []
        for offset in [0, 25000]:
            url = (f"https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1.data.csv"
                   f"?geography=TYPE298&date=latest&gender=0&c_age=0&measures=20100"
                   f"&select=geography_code,geography_name,obs_value"
                   f"&recordlimit=25000&recordoffset={offset}")
            data = fetch_csv(url)
            lines = data.strip().split('\n')
            if offset == 0:
                all_rows.append(lines[0])  # Header
            all_rows.extend(lines[1:])
            print(f"  Fetched {len(lines)-1} records (offset {offset})")
        
        with open(pop_file, 'w') as f:
            f.write('\n'.join(all_rows) + '\n')
        print(f"  Saved {len(all_rows)-1} LSOA populations")
    else:
        print(f"Using cached LSOA populations: {pop_file}")
    
    # Download LSOA centroids from ONS ArcGIS
    if not os.path.exists(centroid_file):
        print("Downloading LSOA population-weighted centroids from ONS...")
        base_url = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services"
                    "/LSOA_PopCentroids_EW_2021_V4/FeatureServer/0/query")
        all_centroids = []
        offset = 0
        batch_size = 2000
        while True:
            url = (f"{base_url}?where=1%3D1&outFields=LSOA21CD"
                   f"&returnGeometry=true&f=json"
                   f"&resultRecordCount={batch_size}&resultOffset={offset}&outSR=4326")
            req = urllib.request.Request(url, headers={'User-Agent': 'CrimeSafe-UK/1.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            features = data.get('features', [])
            if not features:
                break
            for f in features:
                code = f['attributes']['LSOA21CD']
                x = f['geometry']['x']
                y = f['geometry']['y']
                all_centroids.append([code, y, x])
            offset += len(features)
            print(f"  Fetched {offset} centroids...")
            if not data.get('exceededTransferLimit', False):
                break
        
        with open(centroid_file, 'w') as f:
            json.dump(all_centroids, f)
        print(f"  Saved {len(all_centroids)} LSOA centroids")
    else:
        print(f"Using cached LSOA centroids: {centroid_file}")
    
    return pop_file, centroid_file

# ─── Step 3: Load and match data ───

def load_lsoa_data(pop_file, centroid_file):
    """Load and merge LSOA populations with centroids."""
    # Load populations
    lsoa_pop = {}
    with open(pop_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['GEOGRAPHY_CODE'].strip('"')
            try:
                pop = int(row['OBS_VALUE'].strip('"'))
            except:
                continue
            lsoa_pop[code] = pop
    
    # Load centroids
    with open(centroid_file, 'r') as f:
        centroids = json.load(f)
    
    # Merge - only keep LSOAs with both population and coordinates
    lsoa_data = []
    for code, lat, lng in centroids:
        if code in lsoa_pop:
            lsoa_data.append((code, lat, lng, lsoa_pop[code]))
    
    print(f"Loaded {len(lsoa_data)} LSOAs with population and coordinates")
    print(f"Total population: {sum(d[3] for d in lsoa_data):,}")
    return lsoa_data

# ─── Step 4: Fetch boundaries and assign populations ───

def fetch_and_assign_populations(lsoa_data, force_filter=None):
    """Fetch neighbourhood boundaries and assign LSOA populations."""
    
    # Load forces data
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    # Load existing crime data for neighbourhood list
    crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
    nb_list = []
    for fname in sorted(os.listdir(crime_dir)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(crime_dir, fname)) as f:
            crime = json.load(f)
        force_id = crime.get('force_id', '')
        nb_id = crime.get('neighbourhood_id', '')
        if force_filter and force_id != force_filter:
            continue
        nb_list.append((force_id, nb_id, crime.get('neighbourhood_name', '?'), fname))
    
    print(f"\nProcessing {len(nb_list)} neighbourhoods...")
    
    # Build spatial index for LSOA centroids
    lsoa_points = [(lng, lat, pop, code) for code, lat, lng, pop in lsoa_data]
    
    # Cache for boundaries
    boundary_cache_file = f"{CACHE_DIR}/boundaries.json"
    if os.path.exists(boundary_cache_file):
        with open(boundary_cache_file) as f:
            boundary_cache = json.load(f)
        print(f"Loaded {len(boundary_cache)} cached boundaries")
    else:
        boundary_cache = {}
    
    populations = {}
    processed = 0
    api_calls = 0
    errors = 0
    
    for force_id, nb_id, name, fname in nb_list:
        key = f"{force_id}_{nb_id}"
        processed += 1
        
        # Get boundary (from cache or API)
        if key not in boundary_cache:
            url = f"https://data.police.uk/api/{force_id}/{nb_id}/boundary"
            boundary = fetch_json(url)
            api_calls += 1
            
            if boundary:
                boundary_cache[key] = boundary
            else:
                errors += 1
                if processed % 100 == 0:
                    print(f"  [{processed}/{len(nb_list)}] Failed to get boundary for {name}")
                continue
            
            # Rate limiting - be polite to the API
            if api_calls % 50 == 0:
                time.sleep(1)
            
            # Save cache periodically
            if api_calls % 200 == 0:
                with open(boundary_cache_file, 'w') as f:
                    json.dump(boundary_cache, f)
                print(f"  [{processed}/{len(nb_list)}] Saved boundary cache ({api_calls} API calls, {errors} errors)")
        
        boundary = boundary_cache[key]
        
        # Build polygon
        try:
            coords = [(float(p['longitude']), float(p['latitude'])) for p in boundary]
            if len(coords) < 3:
                continue
            
            if HAS_SHAPELY:
                poly = Polygon(coords)
                if not poly.is_valid:
                    poly = poly.buffer(0)  # Fix invalid geometries
                
                # Find LSOAs inside this polygon
                pop = 0
                lsoa_count = 0
                min_lng = min(c[0] for c in coords) - 0.01
                max_lng = max(c[0] for c in coords) + 0.01
                min_lat = min(c[1] for c in coords) - 0.01
                max_lat = max(c[1] for c in coords) + 0.01
                
                for lng, lat, lpop, code in lsoa_points:
                    if lng < min_lng or lng > max_lng or lat < min_lat or lat > max_lat:
                        continue
                    if poly.contains(Point(lng, lat)):
                        pop += lpop
                        lsoa_count += 1
            else:
                # Fallback to simple algorithm
                pop = 0
                lsoa_count = 0
                min_lng = min(c[0] for c in coords) - 0.01
                max_lng = max(c[0] for c in coords) + 0.01
                min_lat = min(c[1] for c in coords) - 0.01
                max_lat = max(c[1] for c in coords) + 0.01
                
                for lng, lat, lpop, code in lsoa_points:
                    if lng < min_lng or lng > max_lng or lat < min_lat or lat > max_lat:
                        continue
                    if point_in_polygon_simple(lng, lat, coords):
                        pop += lpop
                        lsoa_count += 1
            
            populations[key] = {'population': pop, 'lsoa_count': lsoa_count}
            
        except Exception as e:
            errors += 1
            continue
        
        if processed % 200 == 0:
            print(f"  [{processed}/{len(nb_list)}] Processing... ({api_calls} API calls)")
    
    # Final cache save
    with open(boundary_cache_file, 'w') as f:
        json.dump(boundary_cache, f)
    
    print(f"\nDone! Processed {processed} neighbourhoods")
    print(f"  API calls: {api_calls}")
    print(f"  Errors: {errors}")
    print(f"  With population data: {len(populations)}")
    
    # Stats
    pops = [v['population'] for v in populations.values() if v['population'] > 0]
    if pops:
        pops.sort()
        print(f"\nPopulation distribution:")
        print(f"  Min: {pops[0]:,}")
        print(f"  Median: {pops[len(pops)//2]:,}")
        print(f"  Mean: {sum(pops)//len(pops):,}")
        print(f"  Max: {pops[-1]:,}")
        print(f"  Zero population: {sum(1 for v in populations.values() if v['population'] == 0)}")
    
    return populations

# ─── Step 5: Update crime data files ───

def update_crime_data(populations):
    """Update neighbourhood crime JSON files with population and crime rate."""
    crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
    updated = 0
    
    for fname in sorted(os.listdir(crime_dir)):
        if not fname.endswith('.json'):
            continue
        
        filepath = os.path.join(crime_dir, fname)
        with open(filepath) as f:
            crime = json.load(f)
        
        key = f"{crime['force_id']}_{crime['neighbourhood_id']}"
        pop_data = populations.get(key)
        
        if pop_data and pop_data['population'] > 0:
            pop = pop_data['population']
            total_crimes = int(crime.get('total_crimes', 0) or 0)
            crime_rate = round((total_crimes / pop) * 1000, 1) if pop > 0 else 0
            
            crime['population'] = pop
            crime['crime_rate_per_1000'] = crime_rate
            crime['population_source'] = 'census_2021_lsoa'
            crime['lsoa_count'] = pop_data['lsoa_count']
            
            with open(filepath, 'w') as f:
                json.dump(crime, f, indent=2)
            updated += 1
    
    print(f"Updated {updated} crime data files with population data")
    return updated

# ─── Step 6: Recalculate regional scores ───

def recalculate_regional_scores():
    """Recalculate regional (per-force) percentile scores using per-capita crime rates."""
    crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
    
    # Group by force
    force_data = defaultdict(list)
    for fname in sorted(os.listdir(crime_dir)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(crime_dir, fname)) as f:
            crime = json.load(f)
        
        force_id = crime['force_id']
        nb_id = crime['neighbourhood_id']
        key = f"{force_id}_{nb_id}"
        
        pop = int(crime.get('population', 0) or 0)
        total = int(crime.get('total_crimes', 0) or 0)
        
        # Use per-capita rate if population available, else use total crimes
        if pop > 0:
            rate = (total / pop) * 1000
        else:
            rate = total  # Fallback: use raw count
        
        force_data[force_id].append((key, rate))
    
    # Calculate percentile scores per force
    regional_scores = {}
    for force_id, entries in force_data.items():
        entries.sort(key=lambda x: x[1])  # Sort ascending (lowest rate = safest)
        total = len(entries)
        for i, (key, rate) in enumerate(entries):
            percentile = (i / max(1, total - 1)) * 100
            score = round(100 - percentile)
            regional_scores[key] = score
    
    # Save
    output_path = f"{DATA_DIR}/regional_scores.json"
    with open(output_path, 'w') as f:
        json.dump(regional_scores, f, indent=2)
    
    print(f"Recalculated {len(regional_scores)} regional scores across {len(force_data)} forces")
    
    # Show sample for Avon and Somerset
    avon_entries = [(k, v) for k, v in regional_scores.items() if 'avon' in k]
    avon_entries.sort(key=lambda x: x[1])
    print(f"\nAvon & Somerset scores ({len(avon_entries)} neighbourhoods):")
    for key in ['avon-and-somerset_BN152', 'avon-and-somerset_BN120']:
        print(f"  {key}: {regional_scores.get(key, '?')}")
    
    return regional_scores

# ─── Main ───

def main():
    skip_download = '--skip-download' in sys.argv
    force_filter = None
    if '--force' in sys.argv:
        idx = sys.argv.index('--force')
        if idx + 1 < len(sys.argv):
            force_filter = sys.argv[idx + 1]
            print(f"Filtering to force: {force_filter}")
    
    print("=" * 60)
    print("CrimeSafe UK - Population Data Fix")
    print("=" * 60)
    
    # Step 1 & 2: Download LSOA data
    if not skip_download:
        pop_file, centroid_file = download_lsoa_data()
    else:
        pop_file = f"{CACHE_DIR}/lsoa_populations.csv"
        centroid_file = f"{CACHE_DIR}/lsoa_centroids.json"
    
    # Step 3: Load and merge
    lsoa_data = load_lsoa_data(pop_file, centroid_file)
    
    # Step 4: Fetch boundaries and assign populations
    populations = fetch_and_assign_populations(lsoa_data, force_filter)
    
    # Save population lookup
    pop_lookup_file = f"{DATA_DIR}/population_lookup.json"
    with open(pop_lookup_file, 'w') as f:
        json.dump(populations, f, indent=2)
    print(f"\nSaved population lookup to {pop_lookup_file}")
    
    # Step 5: Update crime data files
    update_crime_data(populations)
    
    # Step 6: Recalculate regional scores
    recalculate_regional_scores()
    
    print("\n" + "=" * 60)
    print("Done! Next steps:")
    print("1. Run: python3 generate_neighbourhoods.py  (regenerate HTML pages)")
    print("2. Run: python3 generate_search.py  (update search data)")
    print("3. Commit and push changes")
    print("=" * 60)

if __name__ == '__main__':
    main()
