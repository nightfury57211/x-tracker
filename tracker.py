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

    # Extract counts from HTML
    followers = following = posts = None

    try:
        # crude extraction example; you may need to adjust
        followers = int(html.split('"followers_count":')[1].split(",")[0])
        following = int(html.split('"friends_count":')[1].split(",")[0])
        posts =

