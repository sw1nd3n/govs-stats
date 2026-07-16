import requests
import pandas as pd
import cloudscraper
import time
from datetime import datetime, timezone
from io import StringIO

NCHL = "https://cstats.nchl.com/team/{team}/stats/?season={season}"
WRAHL = "https://wrahl.com/team/{team}/stats/?season={season}"
ASUMMERHL = "https://albertasummerhockey.com/team/{team}/stats/?season={season}"
LEAGUE_NAMES = {NCHL: "NCHL", WRAHL: "WRAHL", ASUMMERHL: "ASUMMERHL"}

# ---- CONFIG: add your teams here ----
# (team_id, season_id, label)
TARGETS = [
    # ---- NCHL Teams Here ----
    (25649, 163, "VS - E", NCHL),
    (25649, 164, "VS - E", NCHL),
    (25649, 165, "VS - E", NCHL),
    (25649, 166, "VS - E", NCHL),
    (25655, 163, "VS - F", NCHL),
    (25655, 164, "VS - F", NCHL),
    (25655, 165, "VS - F", NCHL),
    (25655, 166, "VS - F", NCHL),
    (28185, 163, "VS - G", NCHL),
    (28185, 164, "VS - G", NCHL),
    (28185, 165, "VS - G", NCHL),
    (28185, 166, "VS - G", NCHL),
    (30960, 163, "VS - H", NCHL),
    (30960, 164, "VS - H", NCHL),
    (30960, 165, "VS - H", NCHL),
    (30960, 166, "VS - H", NCHL),
    # ---- WRAHL Teams Here ----
    (10828, 113, "VS - B", WRAHL),
    (10828, 114, "VS - B", WRAHL),
    (10828, 117, "VS - B", WRAHL),
    (10828, 118, "VS - B", WRAHL),
    (10828, 119, "VS - B", WRAHL),
    (11835, 113, "VS - A", WRAHL),
    (11835, 114, "VS - A", WRAHL),
    (11835, 117, "VS - A", WRAHL),
    # ---- Adult Summer Hockey Teams Here ----
    (3020, 64, "VS - A", ASUMMERHL),
    
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://cstats.nchl.com/",
}

player_frames, goalie_frames = [], []

scraper = cloudscraper.create_scraper()

for team_id, season_id, label, base in TARGETS:
    url = base.format(team=team_id, season=season_id)
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
        df["source"] = LEAGUE_NAMES[base]

    player_frames.append(players)
    goalie_frames.append(goalies)
    print(f"OK: {label} — {len(players)} skaters, {len(goalies)} goalies")
    time.sleep(3)

pd.concat(player_frames).to_csv("player_stats.csv", index=False)
pd.concat(goalie_frames).to_csv("goalie_stats.csv", index=False)
print("Done.")
