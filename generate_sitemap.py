#!/usr/bin/env python3
"""
Generate sitemap.xml
"""

import json
import os
import re
from datetime import datetime

DATA_DIR = "data"
OUTPUT_DIR = "."
BASE_URL = "https://729r2pzfqs-ux.github.io/crimesafe-uk"

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def main():
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    urls = []
    
    # Homepage
    urls.append(("", "1.0", "daily"))
    
    # Forces index
    urls.append(("/forces/", "0.9", "weekly"))
    
    # Force pages
    for force in forces_data['forces']:
        force_slug = slugify(force['name'])
        urls.append((f"/force/{force_slug}/", "0.8", "weekly"))
        
        # Neighbourhood pages
        for nb in force['neighbourhoods']:
            nb_slug = slugify(nb['name'])
            urls.append((f"/neighbourhood/{force_slug}/{nb_slug}/", "0.7", "monthly"))
    
    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for path, priority, changefreq in urls:
        xml += f'  <url>\n'
        xml += f'    <loc>{BASE_URL}{path}</loc>\n'
        xml += f'    <lastmod>{today}</lastmod>\n'
        xml += f'    <changefreq>{changefreq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += f'  </url>\n'
    
    xml += '</urlset>\n'
    
    with open(f"{OUTPUT_DIR}/sitemap.xml", 'w') as f:
        f.write(xml)
    
    # Robots.txt
    robots = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    with open(f"{OUTPUT_DIR}/robots.txt", 'w') as f:
        f.write(robots)
    
    print(f"Generated sitemap.xml with {len(urls)} URLs")
    print(f"Generated robots.txt")

if __name__ == "__main__":
    main()
