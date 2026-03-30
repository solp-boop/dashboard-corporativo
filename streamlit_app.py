import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Logístico", layout="wide")
st.title("📊 Panel de Control Directo (Planif Cargas)")

try:
    # 1. Configuración del Link y la Hoja
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    
    # IMPORTANTE: Reemplaza el 0 por el número GID que copiaste de tu pestaña "Planif cargas"
    # Si "Planif cargas" es la primera hoja, déjalo en 0.
    GID_HOJA = "0" 
    
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    
    # Leemos los datos (Añadimos decimal=',' por si usas comas en Excel)
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip() # Limpiamos espacios en los nombres

    st.success(f"✅ Conexión con 'Planif cargas' exitosa")

    # --- PROCESAMIENTO DE M3 (COLUMNA AY) ---
    if 'M3 Total' in df.columns:
        # Convertimos a string, quitamos puntos de miles si existen, cambiamos coma por punto y a número
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # --- MÉTRICAS ---
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    
    c1, c2 = st.columns(2)
    c1.metric("📦 Cantidad de SO (Registros)", f"{cant_so}")
    c2.metric("📐 Volumen Total (M3)", f"{m3_totales:,.2f} m³")

    st.markdown("---")

    # --- RESUMEN POR PAÍS ---
    if 'Pais Destino' in df.columns:
        st.subheader("Análisis por País")
        resumen = df.groupby('Pais Destino').agg({
            'SO': 'count',
            'M3 Total': 'sum'
        }).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3 en Origen'})
        
        # Ordenamos para ver dónde hay más volumen
        resumen = resumen.sort_values(by='M3 en Origen', ascending=False)
        
        # Mostramos la tabla con formato
        st.dataframe(resumen.style.format({'M3 en Origen': '{:,.2f}'}), use_container_width=True)
    else:
        st.warning("⚠️ No encontré la columna 'Pais Destino'. Revisa que se llame exactamente así.")

except Exception as e:
    st.error(f"Error: {e}")
