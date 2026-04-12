import pandas as pd
url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=276804813"
df = pd.read_csv(url, nrows=2)
print("Columns for Reservas Tab (gid=276804813):")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")
