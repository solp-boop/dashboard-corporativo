import pandas as pd

base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
url = f"{base_url}/export?format=csv&gid=0"

df = pd.read_csv(url)
df.columns = df.columns.str.strip()

# Columna 23 (X) - ETD
col_23 = df.columns[23]
print(f"Columna 23 (X): '{col_23}'")

# Buscar columna Modalidad de Costeo
col_mod_list = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
print(f"\nColumnas Modalidad de Costeo encontradas: {col_mod_list}")
col_mod = col_mod_list[0] if col_mod_list else None

if col_mod:
    mask_barco = df[col_mod].astype(str).str.upper().str.startswith("BARCO")
    df_barco = df[mask_barco].copy()
    print(f"\nTotal filas 'BARCO': {len(df_barco)}")
    
    # Parsear ETD
    df_barco['ETD_DT'] = pd.to_datetime(df_barco.iloc[:, 23], errors='coerce')
    df_barco['Mes'] = df_barco['ETD_DT'].dt.strftime('%m/%Y')
    
    # Ver cuántos por mes
    print("\nConteo por mes (Columna X):")
    print(df_barco.groupby('Mes', dropna=False).size().reset_index(name='Total'))
    
    # Ver las de junio
    df_jun = df_barco[df_barco['Mes'] == '06/2026']
    print(f"\nFilas Junio 2026: {len(df_jun)}")
    
    if not df_jun.empty:
        print("\nFechas ETD únicas en Junio:")
        print(df_jun['ETD_DT'].dt.strftime('%d/%m/%Y').value_counts().reset_index())
        print("\nSemanas del mes (día):")
        print(df_jun['ETD_DT'].dt.day.value_counts().sort_index().reset_index())
    
    # Mostrar también el nombre exacto de la columna X en la hoja original
    print(f"\nPrimeras 5 filas de columna '{col_23}':")
    print(df_barco.iloc[:5, 23])
else:
    print("No se encontró columna de Modalidad de Costeo")
    print("Columnas disponibles:", list(df.columns[:30]))
