import os
import json
import csv
import requests
from datetime import datetime

USER_FILE = "twitter_usernames.txt"
DATA_FOLDER = "data"
STATE_FOLDER = "state"
HISTORY_FILE = os.path.join(DATA_FOLDER, "twitter_history.csv")
STATE_FILE = os.path.join(STATE_FOLDER, "twitter_last_seen.json")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(STATE_FOLDER, exist_ok=True)

with open(USER_FILE, "r") as f:
    usernames = [line.strip() for line in f if line.strip()]

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        last_seen = json.load(f)
else:
    last_seen = {}

BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

def fetch_user_info(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()
    metrics = data.get("data", {}).get("public_metrics", {})
    return {
        "username": username,
        "followers": metrics.get("followers_count"),
        "following": metrics.get("following_count"),
        "posts": metrics.get("tweet_count")
    }

csv_headers = ["timestamp", "username", "followers", "following", "posts"]
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()

updates = []
for username in usernames:
    info = fetch_user_info(username)
    previous = last_seen.get(username)
    if previous != info:
        updates.append(info)
        last_seen[username] = info

if updates:
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        timestamp = datetime.utcnow().isoformat()
        for item in updates:
            row = {"timestamp": timestamp}
            row.update(item)
            writer.writerow(row)

with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(last_seen, f, indent=2, ensure_ascii=False)
