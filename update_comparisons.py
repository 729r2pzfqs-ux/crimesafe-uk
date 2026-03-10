#!/usr/bin/env python3
"""Update comparison pages with more content, FAQ, and links"""

import json
import os
import re
from pathlib import Path

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')

# Load rankings
with open('data/rankings.json') as f:
    rankings = json.load(f)
rankings_lookup = {r['nb_slug']: r for r in rankings}

def get_extra_content(nb1_name, nb2_name, score1, score2, force_name, force_slug, slug1, slug2):
    safer = nb1_name if score1 > score2 else nb2_name
    other = nb2_name if score1 > score2 else nb1_name
    diff = abs(score1 - score2)
    
    return f'''
<div style="max-width: 700px; margin: var(--space-6) auto 0;">
    <h2 style="margin-bottom: var(--space-4);">About This Comparison</h2>
    <p style="color: var(--color-text-muted); margin-bottom: var(--space-4);">
        Based on official police crime data, <strong>{safer}</strong> currently has a 
        {"higher" if diff > 5 else "slightly higher"} safety score than {other}. 
        Both areas are policed by {force_name}. Safety scores are calculated using 
        a percentile ranking of all UK neighbourhoods, where higher scores indicate lower crime rates.
    </p>
    
    <h3 style="margin: var(--space-6) 0 var(--space-3);">Explore These Areas</h3>
    <div style="display: flex; gap: var(--space-3); flex-wrap: wrap;">
        <a href="/neighbourhood/{force_slug}/{slug1}/" class="btn" style="border: 1px solid var(--color-border); padding: var(--space-2) var(--space-4); border-radius: var(--radius); text-decoration: none;">View {nb1_name} Details →</a>
        <a href="/neighbourhood/{force_slug}/{slug2}/" class="btn" style="border: 1px solid var(--color-border); padding: var(--space-2) var(--space-4); border-radius: var(--radius); text-decoration: none;">View {nb2_name} Details →</a>
    </div>
    
    <h3 style="margin: var(--space-6) 0 var(--space-3);">Frequently Asked Questions</h3>
    <details style="border: 1px solid var(--color-border); border-radius: var(--radius); margin-bottom: var(--space-3); padding: var(--space-4);">
        <summary style="font-weight: 600; cursor: pointer;">Is {nb1_name} safer than {nb2_name}?</summary>
        <p style="margin-top: var(--space-3); color: var(--color-text-muted);">{safer} currently has a {"higher" if diff > 5 else "slightly higher"} safety score ({max(score1, score2)}/100 vs {min(score1, score2)}/100), indicating {"lower" if diff > 10 else "somewhat lower"} crime rates based on recent police data.</p>
    </details>
    <details style="border: 1px solid var(--color-border); border-radius: var(--radius); margin-bottom: var(--space-3); padding: var(--space-4);">
        <summary style="font-weight: 600; cursor: pointer;">How are safety scores calculated?</summary>
        <p style="margin-top: var(--space-3); color: var(--color-text-muted);">Safety scores are based on official crime statistics from UK police forces. We rank all neighbourhoods by their crime rates and assign percentile scores, where 100 means safer than all other areas and 0 means higher crime than all others.</p>
    </details>
    <details style="border: 1px solid var(--color-border); border-radius: var(--radius); margin-bottom: var(--space-3); padding: var(--space-4);">
        <summary style="font-weight: 600; cursor: pointer;">How often is the data updated?</summary>
        <p style="margin-top: var(--space-3); color: var(--color-text-muted);">Crime data is updated monthly from data.police.uk. There is typically a 2-month lag between crimes occurring and data being published.</p>
    </details>
</div>
'''

# Process Manchester and Birmingham comparisons
forces_to_update = ['greater-manchester-police', 'west-midlands-police']
updated = 0

for force_slug in forces_to_update:
    compare_dir = Path(f'compare/{force_slug}')
    if not compare_dir.exists():
        continue
    
    force_name = "Greater Manchester Police" if "manchester" in force_slug else "West Midlands Police"
    
    for comp_dir in compare_dir.iterdir():
        if not comp_dir.is_dir():
            continue
        
        html_file = comp_dir / 'index.html'
        if not html_file.exists():
            continue
        
        # Parse the comparison slug
        parts = comp_dir.name.split('-vs-')
        if len(parts) != 2:
            continue
        
        slug1, slug2 = parts
        
        # Get names and scores from rankings
        r1 = rankings_lookup.get(slug1, {})
        r2 = rankings_lookup.get(slug2, {})
        
        nb1_name = r1.get('name', slug1.replace('-', ' ').title())
        nb2_name = r2.get('name', slug2.replace('-', ' ').title())
        score1 = r1.get('score', 50) or 50
        score2 = r2.get('score', 50) or 50
        
        # Read current HTML
        with open(html_file) as f:
            html = f.read()
        
        # Check if already updated
        if 'Frequently Asked Questions' in html:
            continue
        
        # Add content before footer
        extra = get_extra_content(nb1_name, nb2_name, score1, score2, force_name, force_slug, slug1, slug2)
        html = html.replace('</div></section></main>', f'</div>{extra}</div></section></main>')
        
        with open(html_file, 'w') as f:
            f.write(html)
        
        updated += 1
        if updated % 1000 == 0:
            print(f"Updated {updated} pages...")

print(f"✅ Updated {updated} comparison pages")
