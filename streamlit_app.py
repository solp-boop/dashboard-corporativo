import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- 2. ESTILOS CSS ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem; }
    .main { background-color: #040911; color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center !important; gap: 30px; margin-bottom: 40px; }
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
        box-shadow: 0 0 30px rgba(0, 168, 255, 0.3);
    }
    .bidcom-header h1 { font-size: 60px; letter-spacing: 10px; color: #ffffff; font-weight: 900; margin: 0; text-shadow: 2px 2px 15px rgba(0, 168, 255, 0.8); }
    .bidcom-subtitle { font-size: 18px; color: #00a8ff; letter-spacing: 4px; text-transform: uppercase; font-weight: 600; margin-top: 5px; text-align: center; }
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; margin-bottom: 5px; }
    .value-massive { font-size: 120px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 40px rgba(0,168,255,0.5); }
    .stButton>button { border-radius: 15px !important; color: white !important; width: 100%; height: 140px; font-weight: 800 !important; font-size: 18px !important; background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }
    .stButton>button:hover { background-color: #003366 !important; border-color: #00a8ff !important; }
    .chart-title { text-align: center; letter-spacing: 2px; color: #00a8ff; font-weight: 900; font-size: 20px; margin: 25px 0 15px 0; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

try:
    # --- 3. DATOS ---
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    csv_url = f"{base_url}/export?format=csv&gid=0&nocache={time.time()}"
    df = pd.read_csv(csv_url).apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        return "PASADO" if fecha < pivot else fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    # --- 4. RENDERIZADO ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logistica Internacional</div></div>", unsafe_allow_html=True)
    
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # MÉTRICAS
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{len(df)}</p></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(df['M3 Total'].sum()):,}</p></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0}</p></div>", unsafe_allow_html=True)

        # BOTONES
        st.markdown("<br>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns(4)
        df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
        
        if b1.button(f"CONSOLIDADO INSTRUIDO"): st.session_state.f = 'inst'
        if b2.button(f"PENDIENTE INSTRUCCIÓN"): st.session_state.f = 'pend'
        if b3.button("PRODUCTOS TOP RANKING"): st.session_state.f = 'rank'
        if b4.button("ESTRUCTURA DE CARGA"): st.session_state.f = 'estr'

        # TABLAS (DESPLEGABLES)
        if 'f' in st.session_state and st.session_state.f:
            st.markdown("---")
            if st.session_state.f == "rank":
                col_rank = df.columns[1]
                df_rank = df[(pd.to_numeric(df[col_rank], errors='coerce') >= 1) & (pd.to_numeric(df[col_rank], errors='coerce') <= 100)].sort_values(by=col_rank)
                st.dataframe(df_rank[['SO', col_rank, 'M3 Total', 'Puerto de Salida']], use_container_width=True)
            elif st.session_state.f == "inst":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            # (Otras opciones de filtro aquí si se desea)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # TABLA PAÍSES
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).sort_values(by='M3 Total', ascending=False)
        st.dataframe(res_p.style.format({'M3 Total': '{:,.0f}'}), use_container_width=True)

        # --- FILA ÚNICA DE GRÁFICOS ---
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns([1.2, 1, 1])

        with g1:
            st.markdown("<p class='chart-title'>Salida por Puerto</p>", unsafe_allow_html=True)
            p_df = df.groupby('Puerto de Salida').agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig1 = px.bar(p_df, y='Puerto de Salida', x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig1.update_layout(xaxis_title=None, yaxis_title=None, height=500, margin=dict(t=0, b=0))
            st.plotly_chart(fig1, use_container_width=True, key="grafico_puerto_unico")

        with g2:
            st.markdown("<p class='chart-title'>Proyección ETD</p>", unsafe_allow_html=True)
            e_df = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig2 = px.bar(e_df, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig2.update_layout(xaxis_title=None, yaxis_title=None, height=500, margin=dict(t=0, b=0))
            st.plotly_chart(fig2, use_container_width=True, key="grafico_etd_unico")

        with g3:
            st.markdown("<p class='chart-title'>Proyección ETA</p>", unsafe_allow_html=True)
            a_df = df.groupby('Mes_ETA_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig3 = px.bar(a_df, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig3.update_layout(xaxis_title=None, yaxis_title=None, height=500, margin=dict(t=0, b=0))
            st.plotly_chart(fig3, use_container_width=True, key="grafico_eta_unico")

    # REFRESH AUTOMÁTICO
    time.sleep(60)
    st.rerun()

except Exception as e:
    st.error(f"Error: {e}")
