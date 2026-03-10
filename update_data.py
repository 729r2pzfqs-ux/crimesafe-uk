#!/usr/bin/env python3
"""
CrimeSafe UK - Weekly Data Update Script
Checks for new crime data, regenerates site if new data available.
Run via cron: 0 6 * * 1 (every Monday at 6am)
"""

import json
import os
import subprocess
import sys
import requests
from datetime import datetime

# Config
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f"{REPO_DIR}/data"
TELEGRAM_CHAT_ID = "491341613"

def send_telegram(message):
    """Send notification via Telegram"""
    try:
        # Use openclaw message tool via CLI
        subprocess.run([
            "openclaw", "message", "send",
            "--target", TELEGRAM_CHAT_ID,
            "--message", message
        ], capture_output=True, timeout=30)
    except Exception as e:
        print(f"Telegram notification failed: {e}")

def get_latest_available_date():
    """Check data.police.uk for latest available crime data date"""
    try:
        resp = requests.get("https://data.police.uk/api/crime-last-updated", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("date")  # Format: "2026-01"
    except Exception as e:
        print(f"Error checking latest date: {e}")
    return None

def get_current_data_date():
    """Get date of currently stored crime data"""
    try:
        # Check a sample crime file
        crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
        for fname in os.listdir(crime_dir):
            if fname.endswith('.json'):
                with open(f"{crime_dir}/{fname}") as f:
                    data = json.load(f)
                    return data.get("date")
    except Exception as e:
        print(f"Error reading current data date: {e}")
    return None

def fetch_new_data():
    """Fetch new crime data from data.police.uk"""
    print("Fetching new crime data...")
    os.chdir(REPO_DIR)
    
    # Run the bulk fetch script
    result = subprocess.run(
        ["python3", "fetch_bulk.py"],
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour timeout
    )
    
    if result.returncode != 0:
        print(f"Fetch failed: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def regenerate_site():
    """Regenerate all site pages"""
    print("Regenerating site...")
    os.chdir(REPO_DIR)
    
    scripts = [
        "generate_site.py",
        "generate_neighbourhoods.py",
        "generate_districts.py",
        "generate_rankings.py",
        "generate_london_comparisons.py"
    ]
    
    for script in scripts:
        print(f"Running {script}...")
        result = subprocess.run(
            ["python3", script],
            capture_output=True,
            text=True,
            timeout=1800  # 30 min timeout per script
        )
        if result.returncode != 0:
            print(f"{script} failed: {result.stderr}")
            return False
    
    return True

def update_month_label(new_date):
    """Update the month label in generators based on new data date"""
    import re
    
    # Parse date (format: "2026-01")
    year, month = new_date.split("-")
    month = int(month)
    
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    month_label = f"{month_names[month-1]} {year}"
    
    print(f"Updating month label to: {month_label}")
    
    # Update generator files
    generators = [
        "generate_site.py",
        "generate_neighbourhoods.py",
        "generate_districts.py",
        "generate_rankings.py",
        "generate_comparisons.py",
        "generate_london_comparisons.py"
    ]
    
    # Pattern to match month names followed by year
    month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December) 20\d{2}'
    
    for gen in generators:
        filepath = f"{REPO_DIR}/{gen}"
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            content = re.sub(month_pattern, month_label, content)
            with open(filepath, 'w') as f:
                f.write(content)

def git_push(message):
    """Commit and push changes"""
    print("Pushing to GitHub...")
    os.chdir(REPO_DIR)
    
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True, timeout=3600)
    
    return True

def main():
    print(f"=== CrimeSafe UK Data Update - {datetime.now().isoformat()} ===\n")
    
    # Check latest available date
    latest_available = get_latest_available_date()
    current_date = get_current_data_date()
    
    print(f"Current data: {current_date}")
    print(f"Latest available: {latest_available}")
    
    if not latest_available:
        print("Could not check latest available date. Exiting.")
        return
    
    if latest_available == current_date:
        print("Data is already up to date. No update needed.")
        return
    
    print(f"\nNew data available! {current_date} → {latest_available}")
    send_telegram(f"🇬🇧 CrimeSafe UK: New crime data available ({latest_available}). Starting update...")
    
    try:
        # Fetch new data
        if not fetch_new_data():
            send_telegram("❌ CrimeSafe UK: Data fetch failed!")
            return
        
        # Update month label
        update_month_label(latest_available)
        
        # Regenerate site
        if not regenerate_site():
            send_telegram("❌ CrimeSafe UK: Site regeneration failed!")
            return
        
        # Push to GitHub
        git_push(f"Update crime data to {latest_available}")
        
        send_telegram(f"✅ CrimeSafe UK: Updated to {latest_available}! 216K+ pages regenerated.")
        print("\n=== Update complete! ===")
        
    except Exception as e:
        error_msg = f"❌ CrimeSafe UK update failed: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

if __name__ == "__main__":
    main()
