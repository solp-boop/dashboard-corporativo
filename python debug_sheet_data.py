import pandas as pd
import requests
from io import StringIO

# URL de tu archivo (Formato CSV para lectura directa)
base_url = "https://docs.google.com/spreadsheets/d/1dCWU6gY3zMVL2eMhXAUJLsoGdWYUMPVjrZbMutU5lIc"
url_export = f"{base_url}/export?format=csv&gid=0"

def diagnostico():
    print("--- INICIANDO DIAGNÓSTICO DE DATOS ---")
    try:
        response = requests.get(url_export)
        df = pd.read_csv(StringIO(response.text))
        
        print(f"Total filas detectadas: {len(df)}")
        
        # Columnas solicitadas
        cols_interes = {
            "SO": 0,
            "Fecha Instruccion": 20, # U
            "N Invoice": 29,         # AD
            "Modalidad": 68,         # BQ
            "M3 Total": 50,          # AY
            "Fecha Prioritaria": 99  # CV
        }
        
        for name, idx in cols_interes.items():
            col_name = df.columns[idx]
            val_ejemplo = df.iloc[5, idx]
            print(f"Columna {idx} ({name}): Se llama '{col_name}' | Ejemplo fila 5: '{val_ejemplo}'")

        # Verificar cuántos cumplen "Sin Instruccion"
        instr_col = df.columns[20]
        sin_instr = df[df[instr_col].isna() | (df[instr_col].astype(str).str.upper().str.contains("SIN INSTRUCCION"))]
        print(f"\nSOs Sin Instrucción encontrados: {len(sin_instr)}")
        
        if len(sin_instr) > 0:
            mod_col = df.columns[68]
            con_barco = sin_instr[sin_instr[mod_col].astype(str).str.upper().str.contains("BARCO")]
            print(f"SOs Marítimos (BARCO) sin instrucción: {len(con_barco)}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    diagnostico()
