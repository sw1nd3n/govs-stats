import requests
import pandas as pd
from datetime import datetime, timezone

# ---- CONFIG: add your teams here ----
# (team_id, season_id, label)
TARGETS = [
    (25649, 163, "VSIII - 25/26 Reg Season"),
    (25649, 164, "VSIII - 25/26 Playoffs"),
    (25649, 165, "VSII - 26 Summer Reg Season"),
    (25649, 166, "VSII - 26 Summer Playoffs"),
    # (25649, 165, "Victorious Secrets II - 2026 Summer"),
    # (25655, 165, "Victorious Secrets III - 2026 Summer"),
    # add the rest of your Sportzone teams here
]

BASE = "https://cstats.nchl.com/team/{team}/stats/?season={season}"
HEADERS = {"User-Agent": "Mozilla/5.0 (personal stats project)"}

player_frames, goalie_frames = [], []

for team_id, season_id, label in TARGETS:
    url = BASE.format(team=team_id, season=season_id)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Player table has a PPGA column; goalie table has GAA
    players = pd.read_html(resp.text, match="PPGA")[0]
    goalies = pd.read_html(resp.text, match="GAA")[0]

    for df in (players, goalies):
        df["team_id"] = team_id
        df["season_id"] = season_id
        df["label"] = label
        df["scraped_at"] = datetime.now(timezone.utc).isoformat()

    player_frames.append(players)
    goalie_frames.append(goalies)
    print(f"OK: {label} — {len(players)} skaters, {len(goalies)} goalies")

pd.concat(player_frames).to_csv("player_stats.csv", index=False)
pd.concat(goalie_frames).to_csv("goalie_stats.csv", index=False)
print("Done.")
