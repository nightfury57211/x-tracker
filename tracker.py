\
import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import time
import random

import requests

HEADERS = {
    # Polite, realistic UA; do not pretend to be a specific app version.
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATE_DIR = BASE_DIR / "state"
USERNAMES_FILE = BASE_DIR / "usernames.txt"
HISTORY_CSV = DATA_DIR / "history.csv"
STATE_JSON = STATE_DIR / "last_seen.json"


def ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not USERNAMES_FILE.exists():
        USERNAMES_FILE.write_text("instagram\n", encoding="utf-8")
    if not STATE_JSON.exists():
        STATE_JSON.write_text("{}", encoding="utf-8")
    if not HISTORY_CSV.exists():
        with HISTORY_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_utc","username","followers","following","posts","bio","profile_pic_url"])


def parse_num(text: str) -> Optional[int]:
    """Parse numbers like '1,234', '1.2k', '3.4m' into ints."""
    text = text.strip().lower().replace(",", "")
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([km])?$", text)
    if not m:
        return None
    val = float(m.group(1))
    suf = m.group(2)
    if suf == "k":
        val *= 1_000
    elif suf == "m":
        val *= 1_000_000
    return int(round(val))


def decode_json_string(s: str) -> str:
    """Unescape JSON string content like \uXXXX and \" """
    try:
        return json.loads(f'"{s}"')
    except Exception:
        return s.replace('\\"','"').replace("\\n","\n")


def fetch_profile(username: str) -> Optional[Dict[str, Any]]:
    """Fetch and parse public profile page. Returns dict or None on error."""
    url = f"https://www.instagram.com/{username}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
    except Exception as e:
        print(f"[warn] request failed for {username}: {e}")
        return None

    if resp.status_code != 200:
        print(f"[warn] non-200 for {username}: {resp.status_code}")
        return None

    html = resp.text

    # Try to parse from JSON-like blobs embedded in HTML
    def rex(pat):
        return re.search(pat, html, flags=re.DOTALL)

    followers = None
    following = None
    posts = None
    bio = None
    pfp = None

    # Common JSON keys historically present in public profile payloads
    m = rex(r'"edge_followed_by"\s*:\s*{\s*"count"\s*:\s*(\d+)')
    if m:
        followers = int(m.group(1))

    m = rex(r'"edge_follow"\s*:\s*{\s*"count"\s*:\s*(\d+)')
    if m:
        following = int(m.group(1))

    m = rex(r'"edge_owner_to_timeline_media"\s*:\s*{\s*"count"\s*:\s*(\d+)')
    if m:
        posts = int(m.group(1))

    m = rex(r'"biography"\s*:\s*"(.+?)"')
    if m:
        bio = decode_json_string(m.group(1))

    # Profile pic URL (HD if possible)
    m = rex(r'"profile_pic_url_hd"\s*:\s*"(.+?)"')
    if not m:
        m = rex(r'"profile_pic_url"\s*:\s*"(.+?)"')
    if m:
        p = decode_json_string(m.group(1))
        # Unescape minimal \u0026 -> & etc.
        p = p.replace("\\u0026", "&")
        pfp = p

    # Fallback: parse counts from og:description if JSON keys missing
    if followers is None or following is None or posts is None:
        og = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if og:
            ogc = og.group(1)
            fm = re.search(r'([\d\.,]+)\s+Followers', ogc, flags=re.IGNORECASE)
            if fm:
                followers = followers or parse_num(fm.group(1))
            fm = re.search(r'([\d\.,]+)\s+Following', ogc, flags=re.IGNORECASE)
            if fm:
                following = following or parse_num(fm.group(1))
            fm = re.search(r'([\d\.,]+)\s+Posts', ogc, flags=re.IGNORECASE)
            if fm:
                posts = posts or parse_num(fm.group(1))

    if followers is None and following is None and posts is None and bio is None:
        print(f"[warn] could not parse anything for {username}")
        return None

    return {
        "username": username,
        "followers": followers,
        "following": following,
        "posts": posts,
        "bio": bio,
        "profile_pic_url": pfp,
    }


def load_state() -> Dict[str, Any]:
    try:
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: Dict[str, Any]) -> None:
    STATE_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_history(row: Dict[str, Any]) -> None:
    # Append a new row to history CSV
    with HISTORY_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            row.get("timestamp_utc",""),
            row.get("username",""),
            row.get("followers",""),
            row.get("following",""),
            row.get("posts",""),
            row.get("bio",""),
            row.get("profile_pic_url",""),
        ])


def changed(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    # Compare relevant fields
    keys = ["followers","following","posts","bio","profile_pic_url"]
    for k in keys:
        if a.get(k) != b.get(k):
            return True
    return False


def main():
    ensure_files()
    usernames = [u.strip().lstrip("@") for u in USERNAMES_FILE.read_text(encoding="utf-8").splitlines() if u.strip() and not u.strip().startswith("#")]
    state = load_state()

    any_change = False
    for u in usernames:
        # small jitter to be nice
        time.sleep(random.uniform(0.5, 1.5))
        info = fetch_profile(u)
        if not info:
            continue
        prev = state.get(u)
        if not prev or changed(prev, info):
            # record a change
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            row = {"timestamp_utc": ts, **info}
            append_history(row)
            any_change = True
            print(f"[info] change recorded for {u} at {ts}")
        else:
            print(f"[info] no change for {u}")
        # update state
        state[u] = info

    save_state(state)
    if not any_change:
        print("[info] no changes detected in this run.")


if __name__ == "__main__":
    main()
