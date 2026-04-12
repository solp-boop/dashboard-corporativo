import pandas as pd
url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=0"
df = pd.read_csv(url, nrows=2)
print("Columns list:")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

col_ay = df.columns[50] if len(df.columns) > 50 else "NOT FOUND"
print(f"\nColumn index 50 (AY): {col_ay}")
