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
        font-size: 120px; 
        font-weight: 900; 
        color: #ffffff; 
        line-height: 1; 
        margin: 0; 
        text-shadow: 0 0 40px rgba(0,168,255,0.4); 
    }
    .unit-massive { font-size: 40px; color: #ffffff; font-weight: 300; vertical-align: middle; }

    /* BOTONES INTERACTIVOS (Ajustados para 4 en línea) */
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
        line-height: 1.2;
    }
    .stButton>button:hover { background-color: #003366 !important; border-color: #00a8ff !important; }
    
    .chart-title { text-align: center; letter-spacing: 2px; color: #ffffff; font-weight: bold; font-size: 16px; margin-bottom: 15px; text-transform: uppercase; }
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
    
    # Lógica Monoproveedor (Columna CP / índice 93)
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

    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    cant_proveedores = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    st.markdown("<h1 style='text-align: center; color: white; letter-spacing: 10px; font-weight: 900; margin-bottom:20px;'>BIDCOM</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- BLOQUE 1: MÉTRICAS MASIVAS ---
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales):,}<span class='unit-massive'> M3</span></p></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE 2: BOTONES (4 EN LÍNEA) ---
        b1, b2, b3, b4 = st.columns(4)
        
        df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
        instruidos_m3 = df[df['Es_Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        
        stats_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count'})
        p_mono = (stats_tipo.loc['MONOPROVEEDOR', 'SO'] / len(df) * 100) if 'MONOPROVEEDOR' in stats_tipo.index else 0
        p_cons = 100 - p_mono

        with b1:
            if st.button(f"CONSOLIDADO INSTRUIDO {int(perc_instruido)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'instruido' else 'instruido'
        with b2:
            if st.button(f"PENDIENTE INSTRUCCIÓN {int(100-perc_instruido)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'pendiente' else 'pendiente'
        with b3:
            if st.button("PRODUCTOS TOP RANKING (1-100)"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'ranking' else 'ranking'
        with b4:
            if st.button(f"ESTRUCTURA DE CARGA \n Mono: {int(p_mono)}% | Cons: {int(p_cons)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'estructura' else 'estructura'

        # --- DESPLIEGUE DE TABLAS (CONTRACCIÓN/EXPANSIÓN) ---
        if st.session_state.get('filtro'):
            st.markdown("---")
            f = st.session_state.filtro
            if f == "instruido":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            elif f == "pendiente":
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)
            elif f == "ranking":
                col_ranking = df.columns[1]
                col_puerto = 'Puerto de Salida' if 'Puerto de Salida' in df.columns else df.columns[41]
                df_ranking = df[(pd.to_numeric(df[col_ranking], errors='coerce') >= 1) & (pd.to_numeric(df[col_ranking], errors='coerce') <= 100)].sort_values(by=col_ranking)
                st.dataframe(df_ranking[['SO', col_ranking, df.columns[99], 'M3 Total', df.columns[93], col_puerto]], use_container_width=True)
            elif f == "estructura":
                st.markdown("<h3 style='text-align:center;'>Resumen Monoproveedor vs Consolidado</h3>", unsafe_allow_html=True)
                resumen_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cantidad SO', 'M3 Total': 'M3 Total'})
                resumen_tipo['% Participación'] = (resumen_tipo['M3 Total'] / m3_totales * 100).round(1)
                st.table(resumen_tipo.style.format({'M3 Total': '{:,.2f}', '% Participación': '{:.1f}%'}))
                st.dataframe(df[['SO', 'Proveedor', 'M3 Total', 'Tipo_Carga', 'Puerto de Salida']], use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- BLOQUE 3: CUADRO RESUMEN ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        df_total = pd.DataFrame({'CANT. SO': [resumen['CANT. SO'].sum()], 'M3': [resumen['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        resumen_final = pd.concat([resumen, df_total])
        st.dataframe(resumen_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL GENERAL' else '' for _ in s], axis=1).format({'CANT. SO': '{:,.0f}', 'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # --- BLOQUE 4: GRÁFICOS ---
        g1, g2, g3 = st.columns([1.2, 1, 1])
        with g1:
            st.markdown("<p class='chart-title'>Distribución por Puerto</p>", unsafe_allow_html=True)
            col_puerto = 'Puerto de Salida' if 'Puerto de Salida' in df.columns else df.columns[41]
            df[col_puerto] = df[col_puerto].fillna('SIN DEFINIR')
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500)
            fig_p.update_traces(textposition='outside', textfont_size=14)
            st.plotly_chart(fig_p, use_container_width=True)

        with g2:
            st.markdown(f"<p class='chart-title'>ETD (Desde {hoy.strftime('%m/%Y')})</p>", unsafe_allow_html=True)
            etd_plot = df_proyeccion_etd.groupby('Mes_ETD').agg({'M3 Total': 'sum'}).reset_index().sort_values('Mes_ETD')
            fig_etd = px.bar(etd_plot, x='Mes_ETD', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig_etd.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500)
            fig_etd.update_traces(textposition='outside', textfont_size=14)
            st.plotly_chart(fig_etd, use_container_width=True)

        with g3:
            st.markdown("<p class='chart-title'>ETA (Futuro)</p>", unsafe_allow_html=True)
            eta_plot = df_proyeccion_eta.groupby('Mes_ETA').agg({'M3 Total': 'sum'}).reset_index().sort_values('Mes_ETA')
            fig_eta = px.bar(eta_plot, x='Mes_ETA', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig_eta.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500)
            fig_eta.update_traces(textposition='outside', textfont_size=14)
            st.plotly_chart(fig_eta, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
