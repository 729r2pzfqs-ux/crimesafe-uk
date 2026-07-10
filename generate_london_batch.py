#!/usr/bin/env python3
"""
Generate London comparison pages in batches to work within inode limits.
Usage: python3 generate_london_batch.py <batch_num> <batch_size>
  batch_num: 0-indexed batch number
  batch_size: number of pages per batch
"""

import json
import os
import sys
import re
import html as html_lib
from itertools import combinations, islice

# Import the page generator from the main script
exec(open('generate_london_comparisons.py').read().replace("if __name__", "if False"))

# Re-import needed functions since exec scope is messy
def slugify(text):
    text = text.lower()
    text = re.sub(r'&(?:amp;)+', ' and ', text)
    text = re.sub(r'&(?![a-z]+;)', ' and ', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    slug = text.strip('-')
    if slug == 'devon-and-cornwall-police':
        slug = 'devon-cornwall-police'  # force slug predates '&' -> 'and'
    return slug

def main():
    batch_num = int(sys.argv[1])
    batch_size = int(sys.argv[2])

    print(f"Loading rankings...")
    with open('data/rankings.json') as f:
        rankings = json.load(f)

    met_nbs = [r for r in rankings if r['force'] == 'Metropolitan Police Service']
    total_pairs = len(met_nbs) * (len(met_nbs) - 1) // 2

    start = batch_num * batch_size
    end = min(start + batch_size, total_pairs)

    print(f"Batch {batch_num}: generating pages {start:,} to {end:,} of {total_pairs:,}")

    if start >= total_pairs:
        print("Nothing to generate - batch exceeds total pairs")
        return

    # Generate the specific batch
    generated = 0
    skipped = 0
    for i, (nb1, nb2) in enumerate(combinations(met_nbs, 2)):
        if i < start:
            continue
        if i >= end:
            break

        if nb1['nb_slug'] > nb2['nb_slug']:
            nb1, nb2 = nb2, nb1

        slug = f"{nb1['nb_slug']}-vs-{nb2['nb_slug']}"
        out_dir = f"compare/{slug}"

        os.makedirs(out_dir, exist_ok=True)

        with open(f"{out_dir}/index.html", 'w') as f:
            f.write(generate_comparison_page(nb1, nb2))

        generated += 1
        if generated % 10000 == 0:
            print(f"  Generated {generated:,}...")

    print(f"Generated {generated:,} pages in this batch")

if __name__ == "__main__":
    main()
