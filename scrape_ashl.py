import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime, timezone

API = "https://canlan2-api.sportninja.net/v1"
SEED = os.environ["ASHL_SEED_TOKEN"]

# ---- CONFIG: ASHL teams ----
# (team_id, label)
TEAMS = [
    ("vn1dxgLkcLT896eN", "VS - D"),
    ("1S9vxCG4ogfXwn8U", "VS - C"),
]

# ---- 1. Bootstrap auth: seed token -> fresh 7-day token ----
r = requests.post(f"{API}/auth/refresh",
                  headers={"Authorization": f"Bearer {SEED}"},
                  timeout=30)
r.raise_for_status()
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}
print("Auth OK")

player_rows, goalie_rows = [], []

for team_id, label in TEAMS:
    # ---- 2. Discover all seasons (schedules) for this team ----
    r = requests.get(f"{API}/teams/{team_id}/schedules", headers=H, timeout=30)
    r.raise_for_status()
    sched_json = r.json()
    schedules = sched_json["data"] if isinstance(sched_json, dict) else sched_json

    for sched in schedules:
        sched_id = sched.get("id")
        sched_name = sched.get("name") or sched.get("name_full") or "unknown"
        if not sched_id:
            continue

        # ---- 3. Pull skater (goalie=0) and goalie (goalie=1) stats, paginated ----
        for goalie_flag, bucket in ((0, player_rows), (1, goalie_rows)):
            page = 1
            while True:
                url = (f"{API}/schedules/{sched_id}/stats/team/{team_id}"
                       f"?page={page}&sortBy=4&sort=desc&goalie={goalie_flag}")
                r = requests.get(url, headers=H, timeout=30)
                if r.status_code != 200:
                    print(f"SKIP: {label} / {sched_name} g={goalie_flag} -> HTTP {r.status_code}")
                    break
                body = r.json()
                for entry in body.get("data", []):
                    p = entry.get("player", {})
                    row = {
                        "player_id": p.get("id"),
                        "jersey": p.get("player_number"),
                        "first_name": p.get("name_first"),
                        "last_name": p.get("name_last"),
                        "division": entry.get("schedule", {}).get("name"),
                        "season_id": sched_id,
                        "season_name": sched_name,
                        "team_id": team_id,
                        "label": label,
                        "source": "ASHL",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                    for s in entry.get("stats", []):
                        row[s["abbr"]] = s["value"]
                    bucket.append(row)

                pages = body.get("meta", {}).get("pagination", {}).get("total_pages", 0)
                if page >= pages:
                    break
                page += 1
                time.sleep(1)

        print(f"OK: {label} / {sched_name}")
        time.sleep(2)

if not player_rows and not goalie_rows:
    sys.exit("No data scraped - check token/endpoints")

pd.DataFrame(player_rows).fillna(0).to_csv("ashl_player_stats.csv", index=False)
pd.DataFrame(goalie_rows).fillna(0).to_csv("ashl_goalie_stats.csv", index=False)
print(f"Done. {len(player_rows)} skater rows, {len(goalie_rows)} goalie rows.")
