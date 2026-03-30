import streamlit as st
import pandas as pd
import plotly.express as px

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
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 20px; }

    .big-metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 40px 10px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin: 5px;
    }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 4px; text-transform: uppercase; font-weight: 800; margin-bottom: 15px; }
    .value-massive { font-size: 110px; font-weight: 900; color: #ffffff; line-height: 1; text-shadow: 0 0 40px rgba(0,168,255,0.4); }

    .stButton>button {
        border-radius: 15px !important; color: white !important;
        width: 100%; height: 120px; font-weight: 800 !important; font-size: 20px !important;
        background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .stButton>button:hover { background-color: #003366 !important; border-color: #00a8ff !important; }
    
    /* Estilo para los títulos de los gráficos */
    .chart-title { text-align: center; letter-spacing: 2px; color: #ffffff; font-weight: bold; font-size: 18px; margin-bottom: 10px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Carga de Datos
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    GID_HOJA = "0" 
    csv_url = f"{base_url}/export?format=csv&gid={GID_HOJA}"
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()

    # --- LIMPIEZA DE DATOS ---
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # Procesar fechas ETD (Col X) y ETA (Col Y)
    df['ETD'] = pd.to_datetime(df.iloc[:, 23], errors='coerce') # Columna X (index 23)
    df['ETA'] = pd.to_datetime(df.iloc[:, 24], errors='coerce') # Columna Y (index 24)
    
    # Crear columnas de Mes-Año para agrupar
    df['Mes_ETD'] = df['ETD'].dt.strftime('%Y-%m')
    df['Mes_ETA'] = df['ETA'].dt.strftime('%Y-%m')

    df['Es_Instruido'] = df['Fecha de Instruccion'].notna() & (df['Fecha de Instruccion'].astype(str).str.upper() != 'SIN INSTRUCCION')
    
    m3_totales = df['M3 Total'].sum()
    cant_so = df['SO'].nunique() if 'SO' in df.columns else len(df)
    cant_proveedores = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1></div>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- BLOQUE SUPERIOR ---
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='big-metric-card'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so)}</p></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='big-metric-card'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales):,} M3</p></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='big-metric-card'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTONES ---
        _, b1_col, b2_col, _ = st.columns([0.5, 2, 2, 0.5])
        instruidos_m3 = df[df['Es_Instruido'] == True]['M3 Total'].sum()
        perc_instruido = (instruidos_m3 / m3_totales * 100) if m3_totales > 0 else 0
        perc_pendiente = 100 - perc_instruido

        with b1_col:
            if st.button(f"CONSOLIDADO INSTRUIDO \n {int(perc_instruido)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'instruido' else 'instruido'
        with b2_col:
            if st.button(f"PENDIENTE INSTRUCCIÓN \n {int(perc_pendiente)}%"):
                st.session_state.filtro = None if st.session_state.get('filtro') == 'pendiente' else 'pendiente'

        filtro = st.session_state.get('filtro')
        if filtro:
            st.markdown("---")
            if filtro == "instruido":
                st.dataframe(df[df['Es_Instruido'] == True][['SO', 'Pais Destino', 'M3 Total', 'Fecha de Instruccion']], use_container_width=True)
            else:
                st.dataframe(df[df['Es_Instruido'] == False][['SO', 'Pais Destino', 'M3 Total', 'Status Pago']], use_container_width=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- SECCIÓN DE TABLA Y GRÁFICOS INFERIORES ---
        # Primero la tabla de participación a ancho completo
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        resumen = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'})
        resumen['%'] = ((resumen['M3'] / m3_totales) * 100).round(0)
        resumen = resumen.sort_values(by='M3', ascending=False)
        df_total = pd.DataFrame({'CANT. SO': [resumen['CANT. SO'].sum()], 'M3': [resumen['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        resumen_final = pd.concat([resumen, df_total])
        st.dataframe(resumen_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL GENERAL' else '' for _ in s], axis=1).format({'CANT. SO': '{:,.0f}', 'M3': '{:,.0f}', '%': '{:.0f}%'}), use_container_width=True)

        st.markdown("<br><br>", unsafe_allow_html=True)

        # --- FILA DE GRÁFICOS (3 COLUMNAS) ---
        g1, g2, g3 = st.columns(3)

        with g1:
            st.markdown("<p class='chart-title'>Puerto de Salida</p>", unsafe_allow_html=True)
            col_puerto = 'Puerto de Salida' if 'Puerto de Salida' in df.columns else df.columns[41]
            df[col_puerto] = df[col_puerto].fillna('SIN DEFINIR').replace('', 'SIN DEFINIR')
            puertos_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(puertos_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig_p, use_container_width=True)

        with g2:
            st.markdown("<p class='chart-title'>Proyección ETD (Salida)</p>", unsafe_allow_html=True)
            etd_df = df.groupby('Mes_ETD').agg({'M3 Total': 'sum'}).reset_index().dropna()
            fig_etd = px.bar(etd_df, x='Mes_ETD', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig_etd.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig_etd, use_container_width=True)

        with g3:
            st.markdown("<p class='chart-title'>Proyección ETA (Arribo)</p>", unsafe_allow_html=True)
            eta_df = df.groupby('Mes_ETA').agg({'M3 Total': 'sum'}).reset_index().dropna()
            fig_eta = px.bar(eta_df, x='Mes_ETA', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig_eta.update_layout(xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig_eta, use_container_width=True)

except Exception as e:
    st.error(f"Error de sistema: {e}")}")
