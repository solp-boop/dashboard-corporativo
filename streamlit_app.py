import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- DISEÑO BIDCOM IMPACTO TOTAL (CSS) ---
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
    .bidcom-header h1 { 
        font-size: 60px; letter-spacing: 10px; color: #ffffff; 
        font-weight: 900; margin: 0; text-shadow: 2px 2px 15px rgba(0, 168, 255, 0.8);
    }
    .bidcom-subtitle { font-size: 18px; color: #00a8ff; letter-spacing: 4px; text-transform: uppercase; font-weight: 600; margin-top: 5px; }
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; margin-bottom: 5px; }
    .value-massive { font-size: 120px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 30px rgba(0,168,255,0.5); }
    .stButton>button {
        border-radius: 15px !important; color: white !important;
        width: 100%; height: 140px; font-weight: 800 !important; font-size: 18px !important;
        background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease-in-out !important;
    }
    .stButton>button:hover { background-color: rgba(0, 168, 255, 0.2) !important; border-color: #00a8ff !important; color: #00a8ff !important; box-shadow: 0 0 20px rgba(0, 168, 255, 0.4) !important; }
    .chart-title { text-align: center; letter-spacing: 2px; color: #00a8ff; font-weight: 900; font-size: 20px; margin: 25px 0 15px 0; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Carga de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    df = pd.read_csv(f"{base_url}/export?format=csv&gid=0")
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = pd.to_numeric(df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    
    # Procesamiento Fechas
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], errors='coerce') 
    hoy, inicio_mes = pd.Timestamp(datetime.now().date()), pd.Timestamp(datetime.now().date()).replace(day=1)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        return "PASADO" if fecha < pivot else fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))
    m3_totales_global = round(df['M3 Total'].sum())

    # --- HEADER ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logistica Internacional | ORIGEN</div></div>", unsafe_allow_html=True)
    
    # --- BLOQUE 1: MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{len(df)}</p></div>", unsafe_allow_html=True)
    m2.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales_global):,}</p></div>", unsafe_allow_html=True)
    m3.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{df['Proveedor'].nunique()}</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- BLOQUE 2: BOTONES ---
    b1, b2, b3, b4 = st.columns(4)
    df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
    cond_pend = df['Fecha_Inst_DT'].isna() | (df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=True))
    df_inst, df_pend = df[~cond_pend].copy(), df[cond_pend].copy()
    p_inst = round(df_inst['M3 Total'].sum() / m3_totales_global * 100) if m3_totales_global > 0 else 0
    p_mono = round(df[df[df.columns[93]].str.upper() == 'SI'].shape[0] / len(df) * 100)

    if b1.button(f"MERCADERIA INSTRUIDA \n {p_inst}%"): st.session_state.f = 'inst'
    if b2.button(f"PENDIENTE INSTRUCCIÓN \n {100-p_inst}%"): st.session_state.f = 'pend'
    if b3.button("PRODUCTOS TOP RANKING \n (1-100)"): st.session_state.f = 'rank'
    if b4.button(f"ESTRUCTURA DE CARGA \n Mono: {p_mono}% | Cons: {100-p_mono}%"): st.session_state.f = 'estr'

    if st.session_state.get('f'):
        st.markdown("---")
        f = st.session_state.f
        if f == "inst":
            df_mostrar = df_inst[['SO', 'Proveedor', 'M3 Total', 'Fecha de Instruccion']].copy()
            total_row = pd.DataFrame({'SO': [f'TOTAL SO: {len(df_mostrar)}'], 'Proveedor': [f'TOTAL PROV: {df_mostrar["Proveedor"].nunique()}'], 'M3 Total': [df_mostrar['M3 Total'].sum()], 'Fecha de Instruccion': ['']})
            st.dataframe(pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))]).style.apply(lambda s: ['background-color: #003366; font-weight: bold' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
        elif f == "estr":
            res = df.groupby(df.columns[93]).agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3'})
            res['%'] = (res['M3'] / m3_totales_global * 100).round(0)
            res_total = pd.DataFrame({'Cant. SO': [res['Cant. SO'].sum()], 'M3': [res['M3'].sum()], '%': [100]}, index=['TOTAL'])
            st.table(pd.concat([res, res_total]).style.apply(lambda s: ['background-color: #003366; font-weight: bold' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}', '%': '{:.0f}%'}))
        # (Aquí pueden ir los demás desplegables de Origen...)

    st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)
    st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
    res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
    res_p['%'] = (res_p['M3'] / m3_totales_global * 100).round(0)
    st.dataframe(pd.concat([res_p, pd.DataFrame({'CANT. SO': [res_p['CANT. SO'].sum()], 'M3': [res_p['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])]).style.apply(lambda s: ['background-color: #003366; font-weight: bold' if s.name == 'TOTAL GENERAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
