import pandas as pd
urls = {
    "Planif Cargas": "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=0",
    "Reservas": "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=276804813",
    "Items": "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=1109673977" 
}
for name, url in urls.items():
    try:
        df = pd.read_csv(url, nrows=2)
        print(f"\nHeaders for {name}:")
        print(df.columns.tolist())
    except Exception as e:
        print(f"Error loading {name}: {e}")
