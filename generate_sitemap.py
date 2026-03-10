#!/usr/bin/env python3
"""
Generate sitemap.xml with sitemap index for large sites.
Splits into multiple sitemaps (max 50,000 URLs each).
"""

import json
import os
import re
from datetime import datetime
from math import ceil

DATA_DIR = "data"
OUTPUT_DIR = "."
BASE_URL = "https://crimesafe.uk"
MAX_URLS_PER_SITEMAP = 45000  # Leave some margin below 50K

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def write_sitemap(filename, urls, today):
    """Write a single sitemap file."""
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
    
    with open(f"{OUTPUT_DIR}/{filename}", 'w') as f:
        f.write(xml)
    
    return len(urls)

def write_sitemap_index(sitemap_files, today):
    """Write sitemap index file."""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for filename in sitemap_files:
        xml += f'  <sitemap>\n'
        xml += f'    <loc>{BASE_URL}/{filename}</loc>\n'
        xml += f'    <lastmod>{today}</lastmod>\n'
        xml += f'  </sitemap>\n'
    
    xml += '</sitemapindex>\n'
    
    with open(f"{OUTPUT_DIR}/sitemap.xml", 'w') as f:
        f.write(xml)

def main():
    with open(f"{DATA_DIR}/forces.json") as f:
        forces_data = json.load(f)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Collect all URLs by category
    main_urls = []
    neighbourhood_urls = []
    compare_urls = []
    postcode_urls = []
    lsoa_urls = []
    
    # Main pages
    main_urls.append(("", "1.0", "daily"))
    main_urls.append(("/forces/", "0.9", "weekly"))
    main_urls.append(("/districts/", "0.9", "weekly"))
    main_urls.append(("/safest/", "0.9", "weekly"))
    main_urls.append(("/dangerous/", "0.9", "weekly"))
    main_urls.append(("/compare/", "0.8", "weekly"))
    main_urls.append(("/about/", "0.7", "monthly"))
    
    # Districts
    districts_file = f"{DATA_DIR}/districts.json"
    if os.path.exists(districts_file):
        with open(districts_file) as f:
            districts = json.load(f)
        for d in districts:
            district_slug = slugify(d['district'])
            main_urls.append((f"/district/{district_slug}/", "0.8", "weekly"))
    
    # Force and neighbourhood pages
    for force in forces_data['forces']:
        force_slug = slugify(force['name'])
        main_urls.append((f"/force/{force_slug}/", "0.8", "weekly"))
        
        for nb in force['neighbourhoods']:
            nb_slug = slugify(nb['name'])
            neighbourhood_urls.append((f"/neighbourhood/{force_slug}/{nb_slug}/", "0.7", "monthly"))
    
    # Comparison pages
    compare_dir = f"{OUTPUT_DIR}/compare"
    if os.path.exists(compare_dir):
        for root, dirs, files in os.walk(compare_dir):
            for f in files:
                if f == "index.html":
                    rel_path = os.path.relpath(root, OUTPUT_DIR)
                    compare_urls.append((f"/{rel_path}/", "0.6", "monthly"))
    
    # Postcode pages
    postcode_dir = f"{OUTPUT_DIR}/postcode"
    if os.path.exists(postcode_dir):
        main_urls.append(("/postcode/", "0.8", "monthly"))
        for slug in os.listdir(postcode_dir):
            if os.path.isdir(f"{postcode_dir}/{slug}"):
                postcode_urls.append((f"/postcode/{slug}/", "0.5", "monthly"))
    
    # LSOA pages
    lsoa_dir = f"{OUTPUT_DIR}/lsoa"
    if os.path.exists(lsoa_dir):
        for slug in os.listdir(lsoa_dir):
            if os.path.isdir(f"{lsoa_dir}/{slug}"):
                lsoa_urls.append((f"/lsoa/{slug}/", "0.5", "monthly"))
    
    # City pages
    city_dir = f"{OUTPUT_DIR}/city"
    if os.path.exists(city_dir):
        main_urls.append(("/city/", "0.9", "weekly"))
        for slug in os.listdir(city_dir):
            if os.path.isdir(f"{city_dir}/{slug}"):
                main_urls.append((f"/city/{slug}/", "0.8", "weekly"))
    
    # Write sitemaps
    sitemap_files = []
    total_urls = 0
    
    # Main sitemap (forces, districts, etc.)
    if main_urls:
        count = write_sitemap("sitemap-main.xml", main_urls, today)
        sitemap_files.append("sitemap-main.xml")
        total_urls += count
        print(f"  sitemap-main.xml: {count} URLs")
    
    # Neighbourhoods sitemap
    if neighbourhood_urls:
        count = write_sitemap("sitemap-neighbourhoods.xml", neighbourhood_urls, today)
        sitemap_files.append("sitemap-neighbourhoods.xml")
        total_urls += count
        print(f"  sitemap-neighbourhoods.xml: {count} URLs")
    
    # Postcodes sitemap
    if postcode_urls:
        count = write_sitemap("sitemap-postcodes.xml", postcode_urls, today)
        sitemap_files.append("sitemap-postcodes.xml")
        total_urls += count
        print(f"  sitemap-postcodes.xml: {count} URLs")
    
    # LSOA sitemaps (may need multiple)
    if lsoa_urls:
        num_lsoa_sitemaps = ceil(len(lsoa_urls) / MAX_URLS_PER_SITEMAP)
        for i in range(num_lsoa_sitemaps):
            start = i * MAX_URLS_PER_SITEMAP
            end = min((i + 1) * MAX_URLS_PER_SITEMAP, len(lsoa_urls))
            chunk = lsoa_urls[start:end]
            filename = f"sitemap-lsoa-{i+1}.xml"
            count = write_sitemap(filename, chunk, today)
            sitemap_files.append(filename)
            total_urls += count
            print(f"  {filename}: {count} URLs")
    
    # Compare sitemaps (need multiple)
    if compare_urls:
        num_compare_sitemaps = ceil(len(compare_urls) / MAX_URLS_PER_SITEMAP)
        for i in range(num_compare_sitemaps):
            start = i * MAX_URLS_PER_SITEMAP
            end = min((i + 1) * MAX_URLS_PER_SITEMAP, len(compare_urls))
            chunk = compare_urls[start:end]
            filename = f"sitemap-compare-{i+1}.xml"
            count = write_sitemap(filename, chunk, today)
            sitemap_files.append(filename)
            total_urls += count
            print(f"  {filename}: {count} URLs")
    
    # Write sitemap index
    write_sitemap_index(sitemap_files, today)
    
    # Robots.txt
    robots = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    with open(f"{OUTPUT_DIR}/robots.txt", 'w') as f:
        f.write(robots)
    
    print(f"\n✅ Generated sitemap index with {len(sitemap_files)} sitemaps")
    print(f"📊 Total URLs: {total_urls}")
    print(f"📄 Generated robots.txt")

if __name__ == "__main__":
    main()
