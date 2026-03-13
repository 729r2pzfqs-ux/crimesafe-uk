import json
import requests
from collections import Counter
import time

# Major UK city centers with coordinates
CITIES = {
    'london-central': (51.5074, -0.1278),
    'london-oxford-st': (51.5154, -0.1410),
    'london-camden': (51.5391, -0.1426),
    'london-shoreditch': (51.5256, -0.0780),
    'london-brixton': (51.4613, -0.1156),
    'london-stratford': (51.5430, -0.0004),
    'london-croydon': (51.3762, -0.0982),
    'manchester': (53.4808, -2.2426),
    'manchester-central': (53.4830, -2.2441),
    'birmingham': (52.4862, -1.8904),
    'birmingham-central': (52.4796, -1.9026),
    'leeds': (53.7997, -1.5492),
    'liverpool': (53.4084, -2.9916),
    'newcastle': (54.9783, -1.6178),
    'sheffield': (53.3811, -1.4701),
    'bristol': (51.4545, -2.5879),
    'nottingham': (52.9548, -1.1581),
    'glasgow': (55.8642, -4.2518),  # Scotland - different API?
    'edinburgh': (55.9533, -3.1883),
    'cardiff': (51.4816, -3.1791),
    'brighton': (50.8225, -0.1372),
    'leicester': (52.6369, -1.1398),
    'coventry': (52.4068, -1.5197),
    'reading': (51.4543, -0.9781),
    'southampton': (50.9097, -1.4044),
    'portsmouth': (50.8198, -1.0880),
    'oxford': (51.7520, -1.2577),
    'cambridge': (52.2053, 0.1218),
    'york': (53.9591, -1.0815),
    'bath': (51.3811, -2.3590),
}

all_streets = Counter()
street_locations = {}

print("Fetching crime data from UK cities...")

for city, (lat, lng) in CITIES.items():
    try:
        url = f"https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date=2024-01"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for crime in data:
                loc = crime.get('location', {})
                street_info = loc.get('street', {})
                street_name = street_info.get('name', '')
                
                # Skip generic locations
                if not street_name or street_name.startswith('On or near ') == False:
                    continue
                    
                # Clean the street name
                clean_name = street_name.replace('On or near ', '')
                
                # Skip generic types
                skip_words = ['Nightclub', 'Theatre', 'Educational', 'Parking', 
                              'Shopping Area', 'Conference', 'Supermarket', 
                              'Petrol Station', 'Sports', 'Hospital', 'Prison']
                if any(w in clean_name for w in skip_words):
                    continue
                
                all_streets[clean_name] += 1
                if clean_name not in street_locations:
                    street_locations[clean_name] = {
                        'lat': loc.get('latitude'),
                        'lng': loc.get('longitude'),
                        'city': city.split('-')[0].title()
                    }
            
            print(f"  ✓ {city}: {len(data)} crimes")
        else:
            print(f"  ✗ {city}: HTTP {resp.status_code}")
        
        time.sleep(0.2)  # Rate limit
        
    except Exception as e:
        print(f"  ✗ {city}: {e}")

# Get top 500 streets
top_streets = all_streets.most_common(500)

print(f"\n=== Top 30 streets by crime count ===")
for i, (street, count) in enumerate(top_streets[:30], 1):
    loc = street_locations.get(street, {})
    print(f"{i:3d}. {street} ({count} crimes) - {loc.get('city', '?')}")

# Save to JSON
output = []
for street, count in top_streets:
    loc = street_locations.get(street, {})
    output.append({
        'name': street,
        'slug': street.lower().replace(' ', '-').replace("'", '').replace('.', ''),
        'crimes': count,
        'lat': loc.get('lat'),
        'lng': loc.get('lng'),
        'city': loc.get('city')
    })

with open('data/top_streets.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Saved {len(output)} streets to data/top_streets.json")
