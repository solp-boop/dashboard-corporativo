import pandas as pd
import requests
from io import StringIO

# URL de tu archivo
base_url = "https://docs.google.com/spreadsheets/d/1dCWU6gY3zMVL2eMhXAUJLsoGdWYUMPVjrZbMutU5lIc"
url_export = f"{base_url}/export?format=csv&gid=0"

def diagnostico():
    print("--- INICIANDO DIAGNÓSTICO DE DATOS ---")
    try:
        response = requests.get(url_export)
        # Forzar lectura de strings para evitar que se pierdan ceros o se dañen fechas
        df = pd.read_csv(StringIO(response.text), dtype=str)
        
        print(f"Total filas detectadas: {len(df)}")
        
        # Columnas de interés según tus indicaciones
        indices = {
            "SO": 0,
            "Fecha Instruccion": 20, # Col U
            "N Invoice": 29,         # Col AD
            "Modalidad": 68,         # Col BQ
            "M3 Total": 50,          # Col AY
            "Fecha Prioritaria": 99  # Col CV
        }
        
        for name, idx in indices.items():
            if idx < len(df.columns):
                col_name = df.columns[idx]
                val_ejemplo = df.iloc[5, idx] if len(df) > 5 else "N/A"
                print(f"Index {idx} ({name}): Header='{col_name}' | Ejemplo='{val_ejemplo}'")
            else:
                print(f"ERROR: El índice {idx} ({name}) está fuera de rango. El CSV solo tiene {len(df.columns)} columnas.")

        # Verificar "Sin Instruccion"
        col_u_name = df.columns[20]
        mask_sin = (df[col_u_name].isna()) | (df[col_u_name].str.upper().str.contains("SIN INSTRUCCION", na=False))
        print(f"\nSOs Sin Instrucción (Col U): {mask_sin.sum()}")

    except Exception as e:
        print(f"ERROR DURANTE EL DIAGNÓSTICO: {e}")

if __name__ == "__main__":
    diagnostico()
