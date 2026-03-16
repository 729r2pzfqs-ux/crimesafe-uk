#!/usr/bin/env python3
"""
IndexNow - Instant indexing for Bing, Yandex, Seznam, Naver
Usage: python3 indexnow_ping.py [url1] [url2] ...
       python3 indexnow_ping.py --sitemap sitemap-main.xml
"""

import requests
import sys
import xml.etree.ElementTree as ET

HOST = "crimesafe.uk"
KEY = "6156c16295faf5b142ce44824c9d217d"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"

def ping_urls(urls):
    """Submit URLs to IndexNow"""
    if len(urls) == 1:
        # Single URL - use GET
        url = urls[0]
        endpoint = f"https://api.indexnow.org/indexnow?url={url}&key={KEY}"
        resp = requests.get(endpoint, timeout=30)
        print(f"Single URL: {resp.status_code} - {url}")
        return resp.status_code
    else:
        # Multiple URLs - use POST
        payload = {
            "host": HOST,
            "key": KEY,
            "keyLocation": KEY_LOCATION,
            "urlList": urls[:10000]  # Max 10k per request
        }
        resp = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        print(f"Batch ({len(urls)} URLs): {resp.status_code}")
        return resp.status_code

def urls_from_sitemap(sitemap_path):
    """Extract URLs from sitemap XML"""
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [loc.text for loc in root.findall(".//sm:loc", ns)]
    return urls

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 indexnow_ping.py [url1] [url2] ...")
        print("       python3 indexnow_ping.py --sitemap sitemap-main.xml")
        sys.exit(1)
    
    if sys.argv[1] == "--sitemap":
        urls = urls_from_sitemap(sys.argv[2])
        print(f"Found {len(urls)} URLs in sitemap")
    else:
        urls = sys.argv[1:]
    
    ping_urls(urls)
