import os
import requests
import json
import csv
from datetime import datetime

# Load bearer token from environment (GitHub secret)
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

USER_FILE = "twitter_usernames.txt"
HISTORY_FILE = "data/twitter_history.csv"
STATE_FILE = "state/twitter_last_seen.json"

def fetch_profile(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics,name,username"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()

    if "data" not in data:
        print(f"Error fetching {username}: {data}")
        return None

    user = data["data"]
    metrics = user["public_metrics"]

    return {
        "username": user["username"],
        "name": user["name"],
        "followers": metrics.get("followers_count", 0),
        "following": metrics.get("following_count", 0),
        "tweets": metrics.get("tweet_count", 0),
        "likes": metrics.get("like_count", 0)   # 🔥 New field
    }

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def append_history(row):
    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["time", "username", "name", "followers", "following", "tweets", "likes"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def main():
    state = load_state()
    with open(USER_FILE, "r") as f:
        usernames = [line.strip() for line in f if line.strip()]

    for username in usernames:
        profile = fetch_profile(username)
        if not profile:
            continue

        last = state.get(username)
        if last != profile:  # Only log if changed
            row = {"time": datetime.utcnow().isoformat(), **profile}
            append_history(row)
            state[username] = profile

    save_state(state)

if __name__ == "__main__":
    main()
