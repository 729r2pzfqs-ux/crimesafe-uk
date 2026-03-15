#!/usr/bin/env python3
"""
Patch generate_neighbourhoods.py to add internal linking sections
"""

# Read the original file
with open('generate_neighbourhoods.py', 'r') as f:
    content = f.read()

# 1. Add imports for math at the top
if 'import math' not in content:
    content = content.replace(
        'import json',
        'import json\nimport math'
    )

# 2. Add helper functions after the imports
helper_functions = '''
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def find_nearby_neighbourhoods(target_key, all_crime_data, max_distance=15, limit=6):
    """Find nearby neighbourhoods within max_distance km"""
    target = all_crime_data.get(target_key)
    if not target or 'lat' not in target or 'lng' not in target:
        return []
    
    target_lat = float(target['lat'])
    target_lng = float(target['lng'])
    
    nearby = []
    for key, data in all_crime_data.items():
        if key == target_key:
            continue
        if 'lat' not in data or 'lng' not in data:
            continue
        try:
            dist = haversine_distance(target_lat, target_lng, float(data['lat']), float(data['lng']))
            if dist <= max_distance:
                nearby.append((key, data, dist))
        except:
            continue
    
    # Sort by distance
    nearby.sort(key=lambda x: x[2])
    return nearby[:limit]

# City mapping for neighbourhoods (based on police force areas)
CITY_MAPPING = {
    'metropolitan': 'london',
    'west-midlands': 'birmingham',
    'greater-manchester': 'manchester',
    'west-yorkshire': 'leeds',
    'merseyside': 'liverpool',
    'south-yorkshire': 'sheffield',
    'avon-and-somerset': 'bristol',
    'west-mercia': 'coventry',
    'northumbria': 'newcastle',
    'hampshire': 'southampton',
    'thames-valley': 'oxford',
    'nottinghamshire': 'nottingham',
    'leicestershire': 'leicester',
    'south-wales': 'cardiff',
    'sussex': 'brighton',
    'humberside': 'hull',
}

# District mapping (force_id -> district slugs -> neighbourhood ids)
DISTRICT_LOOKUP = {}

def load_district_mapping():
    """Load district to neighbourhood mapping"""
    global DISTRICT_LOOKUP
    try:
        with open('data/districts.json', 'r') as f:
            districts = json.load(f)
        for d in districts:
            force_id = d['force_id']
            district_slug = d['district'].lower().replace(' ', '-')
            for nb in d.get('neighbourhoods', []):
                nb_id = nb['id']
                key = f"{force_id}_{nb_id}"
                DISTRICT_LOOKUP[key] = {
                    'district_name': d['district'].title(),
                    'district_slug': district_slug,
                    'force_id': force_id
                }
    except:
        pass

'''

# Insert helper functions after the DATA_DIR line
content = content.replace(
    'OUTPUT_DIR = "."',
    'OUTPUT_DIR = "."\n' + helper_functions
)

# 3. Modify the generate_neighbourhood_page function to accept new params
# Find the function signature and add nearby_neighbourhoods parameter
content = content.replace(
    'def generate_neighbourhood_page(force_name, force_slug, nb_name, nb_slug, crime_data=None, safety_score=None, regional_score=None):',
    'def generate_neighbourhood_page(force_name, force_slug, nb_name, nb_slug, crime_data=None, safety_score=None, regional_score=None, nearby=None, district_info=None, city_slug=None, force_id=None):'
)

# 4. Add the internal links section before the CTA
internal_links_section = '''
                <!-- Internal Links Section -->
                <div class="kpi-card" style="margin-top: var(--space-6); text-align: left; padding: var(--space-6);">
                    <h3 style="color: var(--color-primary); margin-bottom: var(--space-4); font-size: var(--text-lg);">Explore More</h3>
                    
                    {nearby_html}
                    
                    {district_html}
                    
                    {city_html}
                    
                    <div style="margin-top: var(--space-4);">
                        <span style="color: var(--color-text-muted); font-size: var(--text-sm);">Compare: </span>
                        {compare_links}
                    </div>
                </div>
                
'''

# We need to build the nearby_html, district_html, city_html, and compare_links dynamically
# This requires modifying the function body to use the new parameters
# Let's add a section that builds these before the CTA

build_links_code = '''
    # Build internal links HTML
    nearby_html = ""
    if nearby and len(nearby) > 0:
        nearby_html = '<div style="margin-bottom: var(--space-4);"><span style="color: var(--color-text-muted); font-size: var(--text-sm);">Nearby: </span>'
        links = []
        for key, data, dist in nearby[:6]:
            nb_n = data.get('neighbourhood_name', key.split('_')[1] if '_' in key else key)
            f_id = data.get('force_id', key.split('_')[0])
            f_slug = slugify(forces.get(f_id, {}).get('name', f_id))
            nb_s = slugify(nb_n)
            links.append(f'<a href="/neighbourhood/{f_slug}/{nb_s}/" style="color: var(--color-primary);">{nb_n}</a>')
        nearby_html += ' • '.join(links) + '</div>'
    
    district_html = ""
    if district_info:
        district_html = f'<div style="margin-bottom: var(--space-4);"><span style="color: var(--color-text-muted); font-size: var(--text-sm);">District: </span><a href="/district/{district_info["district_slug"]}/" style="color: var(--color-primary);">{district_info["district_name"]}</a></div>'
    
    city_html = ""
    if city_slug:
        city_name = city_slug.replace('-', ' ').title()
        city_html = f'<div style="margin-bottom: var(--space-4);"><span style="color: var(--color-text-muted); font-size: var(--text-sm);">City: </span><a href="/city/{city_slug}/" style="color: var(--color-primary);">{city_name}</a></div>'
    
    # Build compare links - use nearby if available, otherwise generic
    compare_links = ""
    if nearby and len(nearby) >= 2:
        compare_pairs = []
        for key, data, dist in nearby[:3]:
            nb_n = data.get('neighbourhood_name', key.split('_')[1] if '_' in key else key)
            nb_s = slugify(nb_n)
            slug1 = slugify(nb_name)
            # Alphabetical order for compare URL
            if slug1 < nb_s:
                compare_url = f"/compare/{slug1}-vs-{nb_s}/"
            else:
                compare_url = f"/compare/{nb_s}-vs-{slug1}/"
            compare_pairs.append(f'<a href="{compare_url}" style="color: var(--color-primary);">vs {nb_n}</a>')
        compare_links = ' • '.join(compare_pairs)
    else:
        compare_links = f'<a href="/compare/" style="color: var(--color-primary);">Compare with other areas</a>'
    
    internal_links_html = f"""
                <!-- Internal Links Section -->
                <div class="kpi-card" style="margin-top: var(--space-6); text-align: left; padding: var(--space-6);">
                    <h3 style="color: var(--color-primary); margin-bottom: var(--space-4); font-size: var(--text-lg);">Explore More</h3>
                    
                    {nearby_html}
                    
                    {district_html}
                    
                    {city_html}
                    
                    <div style="margin-top: var(--space-4);">
                        <span style="color: var(--color-text-muted); font-size: var(--text-sm);">Compare: </span>
                        {compare_links}
                    </div>
                </div>
"""
'''

# Find the CTA section and insert internal links before it
cta_marker = '<!-- CTA -->'
content = content.replace(
    cta_marker,
    '{internal_links_html}\n                \n                ' + cta_marker
)

# Now we need to add the build_links_code before the CTA marker
# Find a good insertion point - after the FAQ schema script
faq_schema_end = '</script>'
# Find the last occurrence before CTA
faq_end_pos = content.rfind(faq_schema_end, 0, content.find(cta_marker))
if faq_end_pos > 0:
    insert_pos = faq_end_pos + len(faq_schema_end)
    content = content[:insert_pos] + '\n' + build_links_code + '\n' + content[insert_pos:]

# 5. Modify main() to pass the new parameters
# Find the generate_neighbourhood_page call in main() and update it
old_call = 'html = generate_neighbourhood_page(force[\'name\'], force_slug, nb_name, nb_slug, crime_data, safety_score, regional_score)'
new_call = '''# Find nearby neighbourhoods
        nearby = find_nearby_neighbourhoods(key, all_crime_data, max_distance=10, limit=6)
        
        # Get district info
        district_info = DISTRICT_LOOKUP.get(key)
        
        # Get city slug
        city_slug = CITY_MAPPING.get(force_id)
        
        html = generate_neighbourhood_page(force['name'], force_slug, nb_name, nb_slug, crime_data, safety_score, regional_score, nearby, district_info, city_slug, force_id)'''

content = content.replace(old_call, new_call)

# 6. Add load_district_mapping() call in main() after loading forces
old_load = 'forces = {f[\'id\']: f for f in forces_data[\'forces\']}'
new_load = '''forces = {f['id']: f for f in forces_data['forces']}
    
    # Load district mapping for internal links
    load_district_mapping()'''

content = content.replace(old_load, new_load)

# 7. Make forces available in generate_neighbourhood_page
# Add forces as a global or pass it
# Actually, the nearby loop needs forces - we need to make it global
content = content.replace(
    'def main():',
    '''# Global forces lookup for internal links
forces = {}

def main():'''
)

content = content.replace(
    "forces = {f['id']: f for f in forces_data['forces']}",
    '''global forces
    forces = {f['id']: f for f in forces_data['forces']}'''
)

# Write the modified file
with open('generate_neighbourhoods.py', 'w') as f:
    f.write(content)

print("✅ Modified generate_neighbourhoods.py with internal linking")
