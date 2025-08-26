import requests
import json
import csv
import os
from datetime import datetime

# Files and folders
USER_FILE = "twitter_usernames.txt"
DATA_FOLDER = "data"
STATE_FOLDER = "state"
HISTORY_FILE = os.path.join(DATA_FOLDER, "twitter_history.csv")
STATE_FILE = os.path.join(STATE_FOLDER, "twitter_last_seen.json")

# Ensure folders exist
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(STATE_FOLDER, exist_ok=True)

# Read usernames
with open(USER_FILE, "r") as f:
    usernames = [line.strip() for line in f if line.strip()]

# Load previous state
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        last_seen = json.load(f)
else:
    last_seen = {}

# Function to fetch user info
def fetch_user_info(username):
    url = f"https://x.com/{username}"
    r = requests.get(url)
    html = r.text

    followers = following = posts = None

    try:
        # crude extraction example; adjust if HTML changes
        followers = int(html.split('"followers_count":')[1].split(",")[0])
        following = int(html.split('"friends_count":')[1].split(",")[0])
        posts = int(html.split('"statuses_count":')[1].split(",")[0])
    except Exception:
        followers = following = posts = None

    return {
        "username": username,
        "followers": followers,
        "following": following,
        "posts": posts
    }

# Prepare CSV headers
csv_headers = ["timestamp", "username", "followers", "following", "posts"]
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()

# Track updates
updates = []
for username in usernames:
    info = fetch_user_info(username)
    previous = last_seen.get(username)
    if previous != info:
        updates.append(info)
        last_seen[username] = info

# Append to CSV if there are updates
if updates:
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        timestamp = datetime.utcnow().isoformat()
        for item in updates:
            row = {"timestamp": timestamp}
            row.update(item)
            writer.writerow(row)

# Save last seen state
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(last_seen, f, indent=2, ensure_ascii=False)
