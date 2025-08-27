import os
import requests
import json
import csv
from datetime import datetime, timedelta, timezone

# Files
USER_FILE = "twitter_usernames.txt"
HISTORY_FILE = "data/twitter_history.csv"
STATE_FILE = "state/twitter_last_seen.json"

# Load bearer token from GitHub secret
BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

# Ensure folders exist
os.makedirs("data", exist_ok=True)
os.makedirs("state", exist_ok=True)

# Define IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

def get_user_data(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics,name,username"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching {username}: {response.text}")
        return None
    return response.json().get("data")

def save_last_seen(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log_history(entry):
    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp (IST)", "username", "name",
                "followers", "following", "tweets", "likes"
            ])
        writer.writerow(entry)

def main():
    if not os.path.exists(USER_FILE):
        print(f"{USER_FILE} not found!")
        return

    with open(USER_FILE, "r") as f:
        usernames = [line.strip() for line in f if line.strip()]

    if not usernames:
        print("No usernames to track.")
        return

    new_state = {}

    for username in usernames:
        data = get_user_data(username)
        if not data:
            continue

        metrics = data.get("public_metrics", {})
        entry = [
            datetime.now(IST).isoformat(),  # <-- log IST time
            data.get("username", ""),
            data.get("name", ""),
            metrics.get("followers_count", 0),
            metrics.get("following_count", 0),
            metrics.get("tweet_count", 0),
            metrics.get("like_count", 0)
        ]

        # Always log every run
        log_history(entry)
        print(f"Logged {username}: {entry}")  # debug print

        # Update last seen
        new_state[username] = entry

    save_last_seen(new_state)

if __name__ == "__main__":
    main()
