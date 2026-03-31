import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Status Cargas", layout="wide")

# --- ESTILOS VISUALES (Mantenemos la identidad BIDCOM) ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem; }
    .main { background-color: #040911; color: #ffffff; }
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
        box-shadow: 0 0 30px rgba(0, 168, 255, 0.3);
    }
    .bidcom-header h1 { font-size: 60px; letter-spacing: 10px; color: #ffffff; font-weight: 900; margin: 0; text-shadow: 2px 2px 15px rgba(0, 168, 255, 0.8); }
    .bidcom-subtitle { font-size: 18px; color: #00a8ff; letter-spacing: 4px; text-transform: uppercase; font-weight: 600; margin-top: 5px; }
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; margin-bottom: 5px; }
    .value-massive { font-size: 120px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 30px rgba(0,168,255,0.5); }
    </style>
    """, unsafe_allow_html=True)

try:
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    
    # 1. CARGA HOJA PRINCIPAL (GID 0) para métricas
    df_inst = pd.read_csv(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")
    df_inst.columns = df_inst.columns.str.strip()
    
    # 2. CARGA HOJA RESERVAS (GID 276804813)
    df_reserva = pd.read_csv(f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}")
    df_reserva.columns = df_reserva.columns.str.strip()

    # Procesamiento M3
    if 'M3 Total' in df_inst.columns:
        df_inst['M3 Total'] = df_inst['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_inst['M3 Total'] = pd.to_numeric(df_inst['M3 Total'], errors='coerce').fillna(0)

    # Filtro: Solo los que TIENEN fecha de instrucción
    df_inst['Fecha_Inst_DT'] = pd.to_datetime(df_inst['Fecha de Instruccion'], errors='coerce')
    df_valido = df_inst[df_inst['Fecha_Inst_DT'].notna()].copy()

    # --- HEADER ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Status de Cargas</div></div>", unsafe_allow_html=True)

    # --- MÉTRICAS MASIVAS (Mismo formato que ORIGEN) ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{len(df_valido)}</p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(df_valido['M3 Total'].sum()):,}</p></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{df_valido['Proveedor'].nunique()}</p></div>", unsafe_allow_html=True)

    st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

    # --- DATOS DE RESERVAS ---
    st.markdown("<h3 style='text-align:center; color:#00a8ff;'>DETALLE DE HOJA RESERVAS</h3>", unsafe_allow_html=True)
    st.dataframe(df_reserva, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
