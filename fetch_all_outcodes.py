#!/usr/bin/env python3
"""Fetch ALL UK outcodes from postcodes.io"""

import json
import time
import urllib.request
import urllib.error

OUTPUT_FILE = "data/all_outcodes.json"

# UK postcode areas
AREAS = [
    "AB", "AL", "B", "BA", "BB", "BD", "BH", "BL", "BN", "BR", "BS", "BT",
    "CA", "CB", "CF", "CH", "CM", "CO", "CR", "CT", "CV", "CW",
    "DA", "DD", "DE", "DG", "DH", "DL", "DN", "DT", "DY",
    "E", "EC", "EH", "EN", "EX",
    "FK", "FY",
    "G", "GL", "GU",
    "HA", "HD", "HG", "HP", "HR", "HS", "HU", "HX",
    "IG", "IP", "IV",
    "KA", "KT", "KW", "KY",
    "L", "LA", "LD", "LE", "LL", "LN", "LS", "LU",
    "M", "ME", "MK", "ML",
    "N", "NE", "NG", "NN", "NP", "NR", "NW",
    "OL", "OX",
    "PA", "PE", "PH", "PL", "PO", "PR",
    "RG", "RH", "RM",
    "S", "SA", "SE", "SG", "SK", "SL", "SM", "SN", "SO", "SP", "SR", "SS", "ST", "SW", "SY",
    "TA", "TD", "TF", "TN", "TQ", "TR", "TS", "TW",
    "UB",
    "W", "WA", "WC", "WD", "WF", "WN", "WR", "WS", "WV",
    "YO",
    "ZE"
]

def check_outcode(outcode):
    """Check if outcode exists and get its data."""
    url = f"https://api.postcodes.io/outcodes/{outcode}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 200 and data.get('result'):
                r = data['result']
                return {
                    'outcode': r['outcode'],
                    'lat': r['latitude'],
                    'lng': r['longitude'],
                    'admin_district': r.get('admin_district', []),
                    'country': r.get('country', [])
                }
    except urllib.error.HTTPError:
        pass
    except Exception as e:
        print(f"  Error checking {outcode}: {e}")
    return None

def main():
    all_outcodes = {}
    
    for area in AREAS:
        print(f"Checking {area}...")
        found = 0
        
        # Try numbers 1-99
        for num in range(1, 100):
            outcode = f"{area}{num}"
            result = check_outcode(outcode)
            if result:
                all_outcodes[outcode.upper()] = result
                found += 1
            time.sleep(0.05)  # Rate limit
        
        # Also try some letter suffixes (like EC1A, EC1M, etc.)
        if area in ['EC', 'WC', 'W', 'E', 'N', 'NW', 'SE', 'SW']:
            for num in range(1, 20):
                for suffix in ['A', 'B', 'C', 'D', 'E', 'H', 'K', 'M', 'N', 'P', 'R', 'V', 'W', 'Y']:
                    outcode = f"{area}{num}{suffix}"
                    result = check_outcode(outcode)
                    if result:
                        all_outcodes[outcode.upper()] = result
                        found += 1
                    time.sleep(0.05)
        
        print(f"  Found {found} outcodes")
    
    print(f"\n✅ Total: {len(all_outcodes)} outcodes")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_outcodes, f, indent=2)
    
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
