import pandas as pd
base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
url_hi = f"{base_url}/export?format=csv&gid=32771816"
df_hi = pd.read_csv(url_hi, nrows=1)
print("Columns of df_hi:")
for i, col in enumerate(df_hi.columns):
    print(f"{i}: {col}")
