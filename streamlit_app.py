import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- DISEÑO BIDCOM IMPACTO TOTAL (CSS) ---
st.markdown("""
    <style>
    .block-container { padding: 1rem 2rem; }
    .main { background-color: #040911; color: #ffffff; }
    
    /* Centrado de Solapas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { 
        justify-content: center !important; 
        gap: 30px; 
        margin-bottom: 40px;
    }

    /* Header BIDCOM con Sombreado Azul/Celeste */
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
        box-shadow: 0 0 30px rgba(0, 168, 255, 0.3);
    }
    .bidcom-header h1 { 
        font-size: 60px; 
        letter-spacing: 10px; 
        color: #ffffff; 
        font-weight: 900; 
        margin: 0;
        text-shadow: 2px 2px 15px rgba(0, 168, 255, 0.8);
    }
    .bidcom-subtitle {
        font-size: 18px; color: #00a8ff; letter-spacing: 4px;
        text-transform: uppercase; font-weight: 600; margin-top: 5px;
    }

    /* MÉTRICAS MASIVAS (Formato Unificado Celeste) */
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { 
        font-size: 24px; 
        color: #00a8ff; 
        letter-spacing: 5px; 
        text-transform: uppercase; 
        font-weight: 800; 
        margin-bottom: 5px; 
    }
    .value-massive { 
        font-size: 120px; 
        font-weight: 900; 
        color: #00a8ff; 
        line-height: 1; 
        margin: 0; 
        text-shadow: 0 0 40px rgba(0,168,255,0.5); 
    }

    /* BOTONES INTERACTIVOS */
    .stButton { display: flex; justify-content: center; }
    .stButton>button {
        border-radius: 15px !important; 
        color: white !important;
        width: 100%; 
        height: 140px; 
        font-weight: 800 !important; 
        font-size: 18px !important;
        background: rgba(255, 255, 255, 0.03) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stButton>button:hover { background-color: #003366 !important; border-color: #00a8ff !important; }
    
    .chart-title { text-align: center; letter-spacing: 2px; color: #00a8ff; font-weight: 900; font-size: 20px; margin: 25px 0 15px 0; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. CARGA DE DATOS CON ANTI-CACHÉ
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}&nocache={time.time()}"
    
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Procesamiento Fechas
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        if fecha < pivot: return "PASADO/REALIZADO"
        return fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    m3_totales = df['M3 Total'].sum()
    cant_so = len(df)
    cant_proveedores = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    # --- HEADER ---
    st.markdown("""
        <div class='bidcom-header'>
            <h1>BIDCOM</h1>
            <div class='bidcom-subtitle'>Tablero Logistica Internacional</div>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- BLOQUE 1: MÉTRICAS MASIVAS ---
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales):,}</p></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE 2: BOTONES ---
        b1, b2, b3, b4 = st.columns(4)
        df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
        p_inst = round(df[df['Es_Instruido'] == True]['M3 Total'].sum() / m3_totales * 100) if m3_totales > 0 else 0
        
        # Monoproveedor (Columna CP / índice 93)
        col_cp = df.columns[93]
        stats_tipo = df.groupby(col_cp).size()
        p_mono = round(stats_tipo.get('SI', 0) / len(df) * 100)

        with b1:
            if st.button(f"CONSOLIDADO INSTRUIDO {p_inst}%"):
                st.session_state.f = None if st.session_state.get('f') == 'inst' else 'inst'
        with b2:
            if st.button(f"PENDIENTE INSTRUCCIÓN {100-p_inst}%"):
                st.session_state.f = None if st.session_state.get('f') == 'pend' else 'pend'
        with b3:
            if st.button("PRODUCTOS TOP RANKING (1-100)"):
                st.session_state.f = None if st.session_state.get('f') == 'rank' else 'rank'
        with b4:
            if st.button(f"ESTRUCTURA DE CARGA \n Mono: {p_mono}% | Cons: {100-p_mono}%"):
                st.session_state.f = None if st.session_state.get('f') == 'estr' else 'estr'

        # --- BLOQUE DE TABLAS DESPLEGABLES ---
        if st.session_state.get('f'):
            st.markdown("---")
            if st.session_state.f == "estr":
                res = df.groupby(col_cp).agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3'})
                st.table(res.style.format({'M3': '{:,.2f}'}))
            elif st.session_state.f == "rank":
                col_rank = df.columns[1]
                df_rank = df[(pd.to_numeric(df[col_rank], errors='coerce') >= 1) & (pd.to_numeric(df[col_rank], errors='coerce') <= 100)].sort_values(by=col_rank)
                st.dataframe(df_rank[['SO', col_rank, df.columns[99], 'M3 Total', col_cp, 'Puerto de Salida']], use_container_width=True)
            elif st.session_state.f == "inst":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            elif st.session_state.f == "pend":
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- BLOQUE 3: CUADRO PARTICIPACIÓN ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
        res_p['%'] = (res_p['M3'] / m3_totales * 100).round(0)
        df_total = pd.DataFrame({'CANT. SO': [res_p['CANT. SO'].sum()], 'M3': [res_p['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        res_p_final = pd.concat([res_p, df_total])
        st.dataframe(res_p_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL GENERAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE 4: GRÁFICOS (RESTAURADOS ABAJO) ---
        g1, g2, g3 = st.columns([1.2, 1, 1])

        with g1:
            st.markdown("<p class='chart-title'>Salida por Puerto</p>", unsafe_allow_html=True)
            col_puerto = 'Puerto de Salida' if 'Puerto de Salida' in df.columns else df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_traces(textfont_size=18, textfont_color="white", textposition='outside')
            fig_p.update_layout(xaxis_title=None, yaxis_title=None, height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_p, use_container_width=True)

        with g2:
            st.markdown("<p class='chart-title'>Proyección ETD (Salidas)</p>", unsafe_allow_html=True)
            etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig_e.update_traces(textfont_size=18, textfont_color="white", textposition='outside')
            fig_e.update_layout(xaxis_title=None, yaxis_title=None, height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_e, use_container_width=True)

        with g3:
            st.markdown("<p class='chart-title'>Proyección ETA (Arribos)</p>", unsafe_allow_html=True)
            eta_p = df.groupby('Mes_ETA_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig_a.update_traces(textfont_size=18, textfont_color="white", textposition='outside')
            fig_a.update_layout(xaxis_title=None, yaxis_title=None, height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_a, use_container_width=True)

    # --- AUTO-REFRESH (SE EJECUTA AL FINAL) ---
    time.sleep(60)
    st.rerun()

except Exception as e:
    st.error(f"Error: {e}")
