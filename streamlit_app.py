import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Logístico", layout="wide")

# --- ESTILO PARA MÉTRICAS ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 35px; color: #1E88E5; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Control de Cargas Corporativo")

try:
    # 1. Obtención de datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" # Asegúrate que sea el GID de 'Planif cargas'
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # --- LIMPIEZA DE M3 ---
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)

    # --- CREACIÓN DE SOLAPAS (TABS) ---
    tab1, tab2, tab3 = st.tabs(["🏗️ Status Origen", "🚢 En Tránsito", "🏁 Destino Final"])

    with tab1:
        st.subheader("Análisis de Carga en Origen")
        
        # Métricas principales
        m3_totales = df['M3 Total'].sum()
        cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Cantidad de SO", f"{cant_so}")
        c2.metric("📐 Volumen Total", f"{m3_totales:,.2f} m³")
        c3.metric("🎯 Eficiencia", "100%") # Ejemplo de métrica extra

        st.markdown("---")

        # --- TABLA CON PORCENTAJES ---
        if 'Pais Destino' in df.columns:
            st.write("### Participación por Destino")
            
            # Agrupamos
            resumen = df.groupby('Pais Destino').agg({
                'SO': 'count',
                'M3 Total': 'sum'
            }).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3 en Origen'})
            
            # Calculamos el % de representación
            resumen['% del Total'] = (resumen['M3 en Origen'] / m3_totales) * 100
            
            # Ordenamos
            resumen = resumen.sort_values(by='M3 en Origen', ascending=False)
            
            # Formateamos para mostrar en pantalla
            st.dataframe(
                resumen.style.format({
                    'M3 en Origen': '{:,.2f}',
                    '% del Total': '{:.1f}%'
                }), 
                use_container_width=True
            )
        else:
            st.warning("No se encontró la columna 'Pais Destino'.")

    with tab2:
        st.info("🚧 Sección en desarrollo: Aquí irán las cargas con Status 'Embarcado' o 'En Tránsito'.")

    with tab3:
        st.info("🚧 Sección en desarrollo: Seguimiento de arribos y entregas finales.")

except Exception as e:
    st.error(f"Ocurrió un error: {e}")
