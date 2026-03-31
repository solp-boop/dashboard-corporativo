import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA INDEPENDIENTE ---
st.set_page_config(page_title="BIDCOM | Status Cargas", layout="wide")

# --- ESTILOS BIDCOM (Copiamos el CSS para mantener la estética) ---
st.markdown("""
    <style>
    .main { background-color: #040911; color: #ffffff; }
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
    }
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; }
    .value-massive { font-size: 100px; font-weight: 900; color: #00a8ff; text-shadow: 0 0 30px rgba(0,168,255,0.5); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600) # Esto hace que la carga sea súper rápida tras la primera vez
def cargar_datos_status():
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    
    # Solo cargamos lo necesario para esta página
    df_inst = pd.read_csv(f"{base_url}/export?format=csv&gid=0") 
    df_reserva = pd.read_csv(f"{base_url}/export?format=csv&gid=276804813")
    
    return df_inst, df_reserva

try:
    df_inst, df_reserva = cargar_datos_status()
    
    # --- LOGICA DE PROCESAMIENTO ---
    # Limpiar M3 de la Hoja 0
    df_inst.columns = df_inst.columns.str.strip()
    if 'M3 Total' in df_inst.columns:
        df_inst['M3 Total'] = pd.to_numeric(df_inst['M3 Total'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    # Filtrar solo Instruidos
    df_inst['Fecha_Inst_DT'] = pd.to_datetime(df_inst['Fecha de Instruccion'], errors='coerce')
    df_valido = df_inst[df_inst['Fecha_Inst_DT'].notna()].copy()

    # --- VISUALIZACIÓN ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div style='color:#00a8ff; letter-spacing:5px;'>STATUS DE CARGAS</div></div>", unsafe_allow_html=True)

    # Métricas de la Hoja 0 (Solo Instruidos)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>CANT. SO</p><p class='value-massive'>{len(df_valido)}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>TOTAL M3</p><p class='value-massive'>{int(df_valido['M3 Total'].sum()):,}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{df_valido['Proveedor'].nunique()}</p></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Mostrar Hoja de Reservas (Hoja 2)
    st.subheader("Detalle de Reservas (Hoja 276804813)")
    st.dataframe(df_reserva, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar Status de Cargas: {e}")
