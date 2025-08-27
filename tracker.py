import os
import requests
import json
import csv
from datetime import datetime

USER_FILE = "twitter_usernames.txt"
HISTORY_FILE = "data/twitter_history.csv"
STATE_FILE = "state/twitter_last_seen.json"

# Load bearer token from GitHub secret
BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

def get_user_data(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics,name,username"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching {username}: {response.text}")
        return None
    return response.json()["data"]

def save_last_seen(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log_history(entry):
    file_exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "username", "name", "followers", "following", "tweets"])
        writer.writerow(entry)

def main():
    with open(USER_FILE, "r") as f:
        usernames = [line.strip() for line in f if line.strip()]

    new_state = {}

    for username in usernames:
        data = get_user_data(username)
        if not data:
            continue

        metrics = data["public_metrics"]
        entry = [
            datetime.utcnow().isoformat(),
            data["username"],
            data["name"],
            metrics["followers_count"],
            metrics["following_count"],
            metrics["tweet_count"]
        ]

        # Always log the data
        log_history(entry)

        # Save the latest snapshot for reference
        new_state[username] = entry

    save_last_seen(new_state)

if __name__ == "__main__":
    main()
