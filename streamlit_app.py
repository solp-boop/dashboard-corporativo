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
    
    /* Centrado de Solapas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { 
        justify-content: center !important; 
        gap: 30px; 
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 40px;
    }

    /* Header BIDCOM con Sombreado Azul/Celeste */
    .bidcom-header {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 30px; border-radius: 20px; border: 1px solid #004080;
        text-align: center; margin-bottom: 30px;
        box-shadow: 0 0 30px rgba(0, 168, 255, 0.2);
    }
    .bidcom-header h1 { 
        font-size: 60px; 
        letter-spacing: 10px; 
        color: #ffffff; 
        font-weight: 900; 
        margin: 0;
        text-shadow: 2px 2px 15px rgba(0, 168, 255, 0.6);
    }
    .bidcom-subtitle {
        font-size: 18px;
        color: #00a8ff;
        letter-spacing: 4px;
        text-transform: uppercase;
        font-weight: 600;
        margin-top: 5px;
    }

    /* MÉTRICAS MASIVAS (Formato Unificado) */
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { 
        font-size: 24px; 
        color: #ffffff; /* Unificado a blanco */
        letter-spacing: 5px; 
        text-transform: uppercase; 
        font-weight: 800; 
        margin-bottom: 5px; 
    }
    .value-massive { 
        font-size: 120px; 
        font-weight: 900; 
        color: #ffffff; 
        line-height: 1; 
        margin: 0; 
        text-shadow: 0 0 40px rgba(0,168,255,0.4); 
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
    
    .chart-title { text-align: center; letter-spacing: 2px; color: #ffffff; font-weight: bold; font-size: 18px; margin-bottom: 15px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Carga de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Procesamiento de Tipos de Carga
    col_cp = df.columns[93]
    df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
    
    # Fechas ETD y ETA
    df['ETD'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)

    df_proyeccion_etd = df[df['ETD'] >= inicio_mes].copy()
    df_proyeccion_eta = df[df['ETA'] >= hoy].copy()
    df_proyeccion_etd['Mes_ETD'] = df_proyeccion_etd['ETD'].dt.strftime('%m/%Y')
    df_proyeccion_eta['Mes_ETA'] = df_proyeccion_eta['ETA'].dt.strftime('%m/%Y')

    # Cálculos Redondeados
    m3_totales = round(df['M3 Total'].sum())
    cant_so = len(df)
    cant_proveedores = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0
    
    stats_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count'})
    p_mono = round(stats_tipo.loc['MONOPROVEEDOR', 'SO'] / len(df) * 100) if 'MONOPROVEEDOR' in stats_tipo.index else 0
    p_cons = 100 - p_mono

    # --- HEADER ---
    st.markdown("""
        <div class='bidcom-header'>
            <h1>BIDCOM</h1>
            <div class='bidcom-subtitle'>Tablero Logistica Internacional</div>
        </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- BLOQUE 1: MÉTRICAS (UNIFICADAS) ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales):,}</p></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE 2: BOTONES ---
        b1, b2, b3, b4 = st.columns(4)
        df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
        p_inst = round(df[df['Es_Instruido'] == True]['M3 Total'].sum() / m3_totales * 100) if m3_totales > 0 else 0

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
            if st.button(f"ESTRUCTURA DE CARGA \n Mono: {p_mono}% | Cons: {p_cons}%"):
                st.session_state.f = None if st.session_state.get('f') == 'estr' else 'estr'

        # --- TABLAS DESPLEGABLES ---
        if st.session_state.get('f'):
            st.markdown("---")
            if st.session_state.f == "estr":
                res = df.groupby('Tipo_Carga').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3'})
                res['%'] = (res['M3'] / m3_totales * 100).round(0)
                st.table(res.style.format({'M3': '{:,.0f}', '%': '{:.0f}%'}))
            elif st.session_state.f == "rank":
                col_rank = df.columns[1]
                df_rank = df[(pd.to_numeric(df[col_rank], errors='coerce') >= 1) & (pd.to_numeric(df[col_rank], errors='coerce') <= 100)].sort_values(by=col_rank)
                st.dataframe(df_rank[['SO', col_rank, df.columns[99], 'M3 Total', df.columns[93], 'Puerto de Salida']], use_container_width=True)
            elif st.session_state.f == "inst":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            elif st.session_state.f == "pend":
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- BLOQUE 3: CUADRO PARTICIPACIÓN ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
        st.dataframe(res_p.style.format({'M3': '{:,.0f}'}), use_container_width=True)

        # --- BLOQUE 4: GRÁFICOS ---
        g1, g2, g3 = st.columns([1.2, 1, 1])
        with g1:
            p_df = df.groupby('Puerto de Salida').agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(p_df, y='Puerto de Salida', x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_layout(height=500, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            etd_p = df_proyeccion_etd.groupby('Mes_ETD').agg({'M3 Total': 'sum'}).reset_index().sort_values('Mes_ETD')
            fig_e = px.bar(etd_p, x='Mes_ETD', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            st.plotly_chart(fig_e, use_container_width=True)
        with g3:
            eta_p = df_proyeccion_eta.groupby('Mes_ETA').agg({'M3 Total': 'sum'}).reset_index().sort_values('Mes_ETA')
            fig_a = px.bar(eta_p, x='Mes_ETA', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            st.plotly_chart(fig_a, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
