#!/bin/bash
# Monthly street data update for CrimeSafe
cd ~/clawd/crimesafe-uk
python3 scripts/fetch_street_data.py >> /tmp/crimesafe_update.log 2>&1
python3 scripts/generate_street_pages.py >> /tmp/crimesafe_update.log 2>&1
git add -A && git commit -m "Monthly street crime data update" && git push
