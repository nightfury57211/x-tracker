# X/Twitter Profile Tracker (Free, Scheduled via GitHub Actions)

Tracks **followers**, **following**, and **posts** for any *public* X/Twitter usernames you list,  
and records changes with timestamps. Runs **every hour** for free using GitHub Actions and pushes updates (CSV + state) back to your repo.

> ⚠️ Use responsibly. Scraping may violate X/Twitter’s Terms of Use. Track only public profiles and avoid excessive frequency.

---

## What you get
- `data/twitter_history.csv` — appended only when a change is detected (UTC timestamps).  
- `state/twitter_last_seen.json` — the most recent snapshot to compare against.  
- `twitter_usernames.txt` — list of X/Twitter usernames to track (one per line).  
- Runs on a **free schedule** using GitHub Actions: `0 * * * *` (every **hour**, UTC).  

---

## Quick Start (best method — GitHub Actions)
1. **Create a new GitHub repository** (public or private).  
2. **Upload these files** to the repo (keep the folder structure). Easiest way: upload the ZIP and extract via GitHub web, or push via Git.  
3. Edit `twitter_usernames.txt` with the handles you want to track (one per line, without the `@`).  
4. Commit & push. Go to **Actions** tab → enable workflows if prompted.  
5. Wait for the schedule to kick in (cron uses **UTC**). You can also run it immediately via **Run workflow**.

---

### Change the frequency
Open `.github/workflows/track.yml` and edit the cron line:

```yaml
- cron: '0 * * * *'   # every hour (UTC)
GitHub schedules are best-effort and may run a bit later than the exact hour.

Where do the logs go?
All changes get appended to data/twitter_history.csv with UTC timestamps.

If nothing changed since last run, the CSV is untouched.

