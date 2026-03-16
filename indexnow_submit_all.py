#!/usr/bin/env python3
"""Submit all URLs to IndexNow in batches"""

import requests
import xml.etree.ElementTree as ET
import time
import sys

HOST = "crimesafe.uk"
KEY = "6156c16295faf5b142ce44824c9d217d"
BATCH_SIZE = 10000
DELAY_BETWEEN_BATCHES = 2  # seconds

def urls_from_sitemap(path):
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in root.findall(".//sm:loc", ns)]

def submit_batch(urls):
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls
    }
    try:
        resp = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        return resp.status_code
    except Exception as e:
        return f"Error: {e}"

# Priority order - important pages first
sitemaps = [
    "sitemap-main.xml",           # 178 - core pages
    "sitemap-neighbourhoods.xml", # 4,929 - key content
    "sitemap-streets.xml",        # 490
    "sitemap-postcodes.xml",      # 2,475
    "sitemap-embeds.xml",         # 4,748
    # Compare pages last (252,087 URLs)
    "sitemap-compare-1.xml",
    "sitemap-compare-2.xml", 
    "sitemap-compare-3.xml",
    "sitemap-compare-4.xml",
    "sitemap-compare-5.xml",
    "sitemap-compare-6.xml",
]

total_submitted = 0
for sitemap in sitemaps:
    print(f"\n📄 Processing {sitemap}...")
    try:
        urls = urls_from_sitemap(sitemap)
    except:
        print(f"  ⚠️ Could not read {sitemap}")
        continue
    
    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i+BATCH_SIZE]
        status = submit_batch(batch)
        total_submitted += len(batch)
        print(f"  Batch {i//BATCH_SIZE + 1}: {len(batch)} URLs → {status}")
        
        if i + BATCH_SIZE < len(urls):
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    # Longer delay between sitemaps
    time.sleep(3)

print(f"\n✅ Total submitted: {total_submitted:,} URLs")
