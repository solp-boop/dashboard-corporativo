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

    /* MÉTRICAS MASIVAS Y CENTRADAS */
    .metric-container { text-align: center; padding: 20px; }
    .label-massive { 
        font-size: 22px; 
        color: #00a8ff; 
        letter-spacing: 5px; 
        text-transform: uppercase; 
        font-weight: 800; 
        margin-bottom: 5px; 
    }
    .value-massive { 
        font-size: 120px; /* Tamaño Masivo Restaurado */
        font-weight: 900; 
        color: #ffffff; 
        line-height: 1; 
        margin: 0; 
        text-shadow: 0 0 40px rgba(0,168,255,0.4); 
    }
    .unit-massive { font-size: 40px; color: #ffffff; font-weight: 300; vertical-align: middle; }

    /* BOTONES INTERACTIVOS (4 en línea) */
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

    # Procesamiento de M3
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica Estructura de Carga (Monoproveedor vs Consolidado)
    col_cp = df.columns[93] # Columna CP
    df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
    
    # Cálculos rápidos
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    cant_proveedores = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0
    
    stats_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count'})
    p_mono = (stats_tipo.loc['MONOPROVEEDOR', 'SO'] / len(df) * 100) if 'MONOPROVEEDOR' in stats_tipo.index else 0
    p_cons = 100 - p_mono

    # --- DASHBOARD ---
    st.markdown("<h1 style='text-align: center; color: white; letter-spacing: 10px; font-weight: 900; margin-bottom:20px;'>BIDCOM</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- MÉTRICAS MASIVAS (DESTACADAS Y CENTRADAS) ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales):,}<span class='unit-massive'> M3</span></p></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTONES DE ACCIÓN (4 EN LÍNEA) ---
        b1, b2, b3, b4 = st.columns(4)
        
        df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
        p_inst = (df[df['Es_Instruido'] == True]['M3 Total'].sum() / m3_totales * 100) if m3_totales > 0 else 0

        with b1:
            if st.button(f"CONSOLIDADO INSTRUIDO {int(p_inst)}%"):
                st.session_state.v = 'instruido'
        with b2:
            if st.button(f"PENDIENTE INSTRUCCIÓN {int(100-p_inst)}%"):
                st.session_state.v = 'pendiente'
        with b3:
            if st.button("PRODUCTOS TOP RANKING (1-100)"):
                st.session_state.v = 'ranking'
        with b4:
            if st.button(f"ESTRUCTURA DE CARGA \n Mono: {int(p_mono)}% | Cons: {int(p_cons)}%"):
                st.session_state.v = 'estructura'

        # --- DESPLIEGUE DE TABLAS ---
        if 'v' in st.session_state:
            st.markdown("---")
            if st.session_state.v == "estructura":
                st.markdown("<p class='chart-title'>Desglose: Monoproveedor vs Consolidado</p>", unsafe_allow_html=True)
                res = df.groupby('Tipo_Carga').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3'})
                res['%'] = (res['M3'] / m3_totales * 100).round(1)
                st.table(res.style.format({'M3': '{:,.2f}', '%': '{:.1f}%'}))
            elif st.session_state.v == "ranking":
                col_rank = df.columns[1]
                df_rank = df[(pd.to_numeric(df[col_rank], errors='coerce') >= 1) & (pd.to_numeric(df[col_rank], errors='coerce') <= 100)].sort_values(by=col_rank)
                st.dataframe(df_rank[['SO', col_rank, df.columns[99], 'M3 Total', df.columns[93], 'Puerto de Salida']], use_container_width=True)
            elif st.session_state.v == "instruido":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            elif st.session_state.v == "pendiente":
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- TABLA Y GRÁFICOS INFERIORES ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
        st.dataframe(res_p.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == res_p.index[0] else '' for _ in s], axis=1).format({'M3': '{:,.0f}'}), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns([1.2, 1, 1])
        with g1:
            p_df = df.groupby('Puerto de Salida').agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig = px.bar(p_df, y='Puerto de Salida', x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig.update_layout(height=450, xaxis_title=None, yaxis_title=None, margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        # (Aquí siguen los otros gráficos ETD/ETA del mismo modo)

except Exception as e:
    st.error(f"Error: {e}")
