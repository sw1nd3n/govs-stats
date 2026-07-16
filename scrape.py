import requests
import pandas as pd
import cloudscraper
import time
from datetime import datetime, timezone
from io import StringIO

# ---- CONFIG: add your teams here ----
# (team_id, season_id, label)
TARGETS = [
    (25649, 163, "VS - E"),
    (25649, 164, "VS - E"),
    (25649, 165, "VS - E"),
    (25649, 166, "VS - E"),
    (25655, 163, "VS - F"),
    (25655, 164, "VS - F"),
    (25655, 165, "VS - F"),
    (25655, 166, "VS - F"),
    (28185, 163, "VS - G"),
    (28185, 164, "VS - G"),
    (28185, 165, "VS - G"),
    (28185, 166, "VS - G"),
    (30960, 163, "VS - H"),
    (30960, 164, "VS - H"),
    (30960, 165, "VS - H"),
    (30960, 166, "VS - H")
    
]

BASE = "https://cstats.nchl.com/team/{team}/stats/?season={season}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://cstats.nchl.com/",
}

player_frames, goalie_frames = [], []

scraper = cloudscraper.create_scraper()

for team_id, season_id, label in TARGETS:
    url = BASE.format(team=team_id, season=season_id)
    try:
        for attempt in range(4):
            resp = scraper.get(url, timeout=30)
            if resp.status_code == 200:
                break
            print(f"WARN: {resp.status_code} on {url}, retry {attempt + 1}")
            time.sleep(15)
        resp.raise_for_status()

        players = pd.read_html(StringIO(resp.text), match="PPGA")[0]
        goalies = pd.read_html(StringIO(resp.text), match="GAA")[0]
    except Exception as e:
        print(f"SKIP: {label} ({url}) — {type(e).__name__}: {e}")
        time.sleep(3)
        continue

    for df in (players, goalies):
        df["team_id"] = team_id
        df["season_id"] = season_id
        df["label"] = label
        df["scraped_at"] = datetime.now(timezone.utc).isoformat()

    player_frames.append(players)
    goalie_frames.append(goalies)
    print(f"OK: {label} — {len(players)} skaters, {len(goalies)} goalies")
    time.sleep(3)

pd.concat(player_frames).to_csv("player_stats.csv", index=False)
pd.concat(goalie_frames).to_csv("goalie_stats.csv", index=False)
print("Done.")
