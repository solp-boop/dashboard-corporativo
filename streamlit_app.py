import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Corporativo", layout="wide")
st.title("📊 Panel de Control Directo")

try:
    # 1. Obtención de datos
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    # Forzamos la descarga de la hoja específica "Planif cargas" mediante su GID
    # Nota: El GID 0 suele ser la primera hoja. 
    csv_url = url.replace("/edit?gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    
    st.success("✅ Datos sincronizados")

    # --- PROCESAMIENTO DE INFORMACIÓN ---
    
    # 2. Selección de columnas necesarias (Usamos los nombres exactos que tiene tu Excel)
    # Columna A: 'SO' (o el nombre que tenga la primera columna)
    # Columna S: 'Pais Destino'
    # Columna AY: 'M3 Total' 
    
    # Limpiamos los nombres de las columnas por si tienen espacios locos
    df.columns = df.columns.str.strip()

    # Convertimos M3 a número por si viene como texto, ignorando errores
    if 'M3 Total' in df.columns:
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)

    # 3. CREACIÓN DE MÉTRICAS GLOBALES
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
        st.metric("📦 Cantidad de SO", f"{total_so}")

    with col2:
        total_m3 = df['M3 Total'].sum() if 'M3 Total' in df.columns else 0
        st.metric("📐 M3 Totales", f"{total_m3:,.2f} m³")

    with col3:
        paises_count = df['Pais Destino'].nunique() if 'Pais Destino' in df.columns else 0
        st.metric("🌎 Países Destino", paises_count)

    st.markdown("---")

    # 4. TABLA DE RESUMEN POR PAÍS
    st.subheader("Resumen Logístico por País")
    
    if 'Pais Destino' in df.columns and 'M3 Total' in df.columns:
        # Agrupamos los datos
        resumen = df.groupby('Pais Destino').agg({
            'SO': 'count',
            'M3 Total': 'sum'
        }).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'Volumen (m3)'})
        
        # Ordenamos de mayor a menor volumen
        resumen = resumen.sort_values(by='Volumen (m3)', ascending=False)
        
        st.table(resumen) # Usamos table para que sea más formal o dataframe para interactiva
    else:
        st.warning("No se encontraron las columnas 'Pais Destino' o 'M3 Total'. Revisa los nombres en el Excel.")

    # 5. VISTA DETALLADA
    with st.expander("Ver base de datos completa"):
        st.dataframe(df)

except Exception as e:
    st.error(f"Error procesando el dashboard: {e}")
    st.info("Asegúrate de que los nombres de las columnas en el Excel coincidan exactamente con el código.")
