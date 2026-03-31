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
        padding: 20px; border-radius: 15px; border: 1px solid #004080;
        text-align: center; margin-bottom: 20px;
    }
    .bidcom-header h1 { font-size: 40px; letter-spacing: 8px; color: #ffffff; font-weight: 900; margin:0; }
    
    /* Ajuste para 4 botones en línea */
    .stButton>button {
        border-radius: 15px !important; color: white !important;
        width: 100%; height: 140px; font-weight: 800 !important; font-size: 16px !important;
        background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
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

    # --- PROCESAMIENTO DE DATOS ---
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Lógica Monoproveedor (Columna CP / índice 93)
    col_monoprov = df.columns[93]
    df['Tipo_Carga'] = df[col_monoprov].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
    
    # Cálculos para el botón de Monoproveedor
    stats_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count', 'M3 Total': 'sum'})
    total_so = len(df)
    perc_mono = (stats_tipo.loc['MONOPROVEEDOR', 'SO'] / total_so * 100) if 'MONOPROVEEDOR' in stats_tipo.index else 0
    perc_cons = 100 - perc_mono

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

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1></div>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- MÉTRICAS SUPERIORES ---
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='big-metric-card'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='big-metric-card'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales):,} M3</p></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='big-metric-card'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE DE 4 BOTONES ---
        b1, b2, b3, b4 = st.columns(4)
        
        df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
        instruidos_m3 = df[df['Es_Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0

        with b1:
            if st.button(f"CONSOLIDADO INSTRUIDO\n{int(perc_instruido)}%"):
                st.session_state.filtro = 'instruido'
        with b2:
            if st.button(f"PENDIENTE INSTRUCCIÓN\n{int(100-perc_instruido)}%"):
                st.session_state.filtro = 'pendiente'
        with b3:
            if st.button("PRODUCTOS TOP RANKING\n(1-100)"):
                st.session_state.filtro = 'ranking'
        with b4:
            if st.button(f"ESTRUCTURA DE CARGA\nMono: {int(perc_mono)}% | Cons: {int(perc_cons)}%"):
                st.session_state.filtro = 'estructura'

        # --- DESGLOSE DE TABLAS SEGÚN BOTÓN ---
        if st.session_state.get('filtro'):
            st.markdown("---")
            if st.session_state.filtro == "estructura":
                st.markdown("<h3 style='text-align:center;'>Resumen Monoproveedor vs Consolidado</h3>", unsafe_allow_html=True)
                # Cuadro de resumen solicitado
                resumen_tipo = df.groupby('Tipo_Carga').agg({
                    'SO': 'count',
                    'M3 Total': 'sum'
                }).rename(columns={'SO': 'Cantidad SO', 'M3 Total': 'M3 Total'})
                resumen_tipo['% Participación'] = (resumen_tipo['M3 Total'] / m3_totales * 100).round(1)
                st.table(resumen_tipo.style.format({'M3 Total': '{:,.2f}', '% Participación': '{:.1f}%'}))
                
                # Detalle de Monoproveedores
                st.dataframe(df[df['Tipo_Carga'] == 'MONOPROVEEDOR'][['SO', 'Proveedor', 'M3 Total', 'Puerto de Salida']], use_container_width=True)

            elif st.session_state.filtro == "ranking":
                col_ranking = df.columns[1]
                df_ranking = df[(pd.to_numeric(df[col_ranking], errors='coerce') >= 1) & (pd.to_numeric(df[col_ranking], errors='coerce') <= 100)].sort_values(by=col_ranking)
                st.dataframe(df_ranking[['SO', col_ranking, df.columns[99], 'M3 Total', col_monoprov, 'Puerto de Salida']], use_container_width=True)
            
            elif st.session_state.filtro == "instruido":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            
            elif st.session_state.filtro == "pendiente":
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- BLOQUE DE PARTICIPACIÓN POR PAÍS ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        resumen_pais = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
        st.dataframe(resumen_pais.style.format({'M3': '{:,.0f}'}), use_container_width=True)

        # --- BLOQUE DE GRÁFICOS ---
        g1, g2, g3 = st.columns([1.2, 1, 1])
        with g1:
            p_df = df.groupby('Puerto de Salida').agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(p_df, y='Puerto de Salida', x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            etd_plot = df_proyeccion_etd.groupby('Mes_ETD').agg({'M3 Total': 'sum'}).reset_index()
            fig_etd = px.bar(etd_plot, x='Mes_ETD', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            st.plotly_chart(fig_etd, use_container_width=True)
        with g3:
            eta_plot = df_proyeccion_eta.groupby('Mes_ETA').agg({'M3 Total': 'sum'}).reset_index()
            fig_eta = px.bar(eta_plot, x='Mes_ETA', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            st.plotly_chart(fig_eta, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
