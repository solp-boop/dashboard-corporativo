import pandas as pd
import time

base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
url = f"{base_url}/export?format=csv&gid=0&nocache={time.time()}"
df = pd.read_csv(url)
print(list(df.columns))
