import pandas as pd
import requests

base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"

# Try various known GIDs to find ETD sheet
candidate_gids = [0, 276804813, 32771816, 1234567890, 1, 2, 3, 
                  100, 200, 300, 400, 500, 1000, 2000, 5000]

for gid in candidate_gids:
    url = f"{base_url}/export?format=csv&gid={gid}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            lines = r.text.split('\n')
            header = lines[0][:200] if lines else ""
            print(f"GID {gid}: OK | Header start: {header[:120]}")
        else:
            print(f"GID {gid}: HTTP {r.status_code}")
    except Exception as e:
        print(f"GID {gid}: ERROR {e}")
