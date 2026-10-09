#!/bin/bash
cd "$(dirname "$0")"
rm -f .git/index.lock
git config user.name "729r2pzfqs-ux"
git config user.email "729r2pzfqs-ux@users.noreply.github.com"
git add force_map.js index.html generate_site.py generate_cities.py generate_districts.py generate_rankings.py generate_comparisons.py generate_postcodes.py generate_london_comparisons.py maps/ forces/index.html city/ districts/ safest/ dangerous/
git commit -m "Fix map tiles (CARTO->OSM) and add Maps to nav"
git push
rm -f commit_fix.sh
