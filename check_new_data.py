#!/usr/bin/env python3
"""
CrimeSafe UK - Check for new crime data (notify only, no download)
Run via cron: 0 9 * * 1 (every Monday at 9am)
"""

import json
import os
import subprocess
import requests

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = f"{REPO_DIR}/data"
TELEGRAM_CHAT_ID = "491341613"
TRACKING_FILE = f"{DATA_DIR}/last_known_date.txt"

def send_telegram(message):
    """Send notification via Telegram"""
    try:
        subprocess.run([
            "openclaw", "message", "send",
            "--target", TELEGRAM_CHAT_ID,
            "--message", message
        ], capture_output=True, timeout=30)
    except Exception as e:
        print(f"Telegram failed: {e}")

def get_api_latest_date():
    """Check data.police.uk for latest available date"""
    try:
        resp = requests.get("https://data.police.uk/api/crime-last-updated", timeout=30)
        if resp.status_code == 200:
            return resp.json().get("date", "")[:7]  # "2026-01-01" -> "2026-01"
    except Exception as e:
        print(f"API error: {e}")
    return None

def get_our_current_date():
    """Get date from our neighbourhood_crimes files"""
    try:
        crime_dir = f"{DATA_DIR}/neighbourhood_crimes"
        for fname in os.listdir(crime_dir)[:10]:
            if fname.endswith('.json'):
                with open(f"{crime_dir}/{fname}") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "date" in data:
                        return data["date"]  # "2026-01"
    except Exception as e:
        print(f"Error reading local data: {e}")
    return None

def get_last_notified_date():
    """Get the date we last notified about (to avoid spam)"""
    try:
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE) as f:
                return f.read().strip()
    except:
        pass
    return None

def save_notified_date(date):
    """Save the date we just notified about"""
    try:
        with open(TRACKING_FILE, 'w') as f:
            f.write(date)
    except:
        pass

if __name__ == "__main__":
    api_date = get_api_latest_date()
    our_date = get_our_current_date()
    last_notified = get_last_notified_date()
    
    print(f"API latest: {api_date}")
    print(f"Our data: {our_date}")
    print(f"Last notified: {last_notified}")
    
    if not api_date:
        print("Could not check API")
    elif api_date == our_date:
        print("No new data available")
    elif api_date == last_notified:
        print("Already notified about this date")
    else:
        # New data available!
        msg = f"🚨 CrimeSafe UK: New crime data available!\n\n"
        msg += f"📅 New: {api_date}\n"
        msg += f"📦 Current: {our_date}\n\n"
        msg += f"Reply 'update crimesafe' to download and apply."
        
        send_telegram(msg)
        save_notified_date(api_date)
        print(f"Notified about new data: {api_date}")
