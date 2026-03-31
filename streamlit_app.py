import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide")

# --- 2. DISEÑO BIDCOM IMPACTO TOTAL (CSS) ---
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
    # --- 3. CARGA DE DATOS ---
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    df = pd.read_csv(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
    # --- PROCESAMIENTO FECHAS ---
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], errors='coerce') 
    
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)
    limite_proximo = hoy + timedelta(days=30)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        if fecha < pivot: return "PASADO/REALIZADO"
        return fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    m3_totales_global = round(df['M3 Total'].sum())
    cant_so_global = len(df)
    cant_proveedores_global = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logistica Internacional</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    with tabs[0]:
        # --- BLOQUE 1: MÉTRICAS ---
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales_global):,}</p></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE 2: BOTONES ---
        b1_col, b2_col, b3_col, b4_col, b5_col = st.columns(5)
        
        df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
        cond_instruido = df['Fecha_Inst_DT'].notna() & ~(df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=False))
        
        cond_critico = (~cond_instruido) & (df['Fecha_Prior_DT'] <= limite_proximo)
        cond_resto = (~cond_instruido) & (~cond_critico)

        df_inst = df[cond_instruido].copy()
        df_criticos = df[cond_critico].copy()
        df_resto = df[cond_resto].copy()

        p_inst = round(df_inst['M3 Total'].sum() / m3_totales_global * 100) if m3_totales_global > 0 else 0
        p_critico = round(df_criticos['M3 Total'].sum() / m3_totales_global * 100) if m3_totales_global > 0 else 0
        p_resto = round(df_resto['M3 Total'].sum() / m3_totales_global * 100) if m3_totales_global > 0 else 0

        if b1_col.button(f"MERCADERIA INSTRUIDA \n {p_inst}%", key="btn_inst"):
            st.session_state.f = 'inst' if st.session_state.get('f') != 'inst' else None
        if b2_col.button(f"PRÓXIMO A INSTRUIR \n {p_critico}%", key="btn_crit"):
            st.session_state.f = 'crit' if st.session_state.get('f') != 'crit' else None
        if b3_col.button(f"RESTO PENDIENTE \n {p_resto}%", key="btn_rest"):
            st.session_state.f = 'rest' if st.session_state.get('f') != 'rest' else None
        if b4_col.button("TOP RANKING \n (1-100)", key="btn_rank"):
            st.session_state.f = 'rank' if st.session_state.get('f') != 'rank' else None
        if b5_col.button("ESTRUCTURA \n CARGA", key="btn_estr"):
            st.session_state.f = 'estr' if st.session_state.get('f') != 'estr' else None

        # --- DESPLEGABLES ---
        if st.session_state.get('f'):
            st.markdown("---")
            f = st.session_state.f
            if f == "inst":
                st.markdown("<h3 style='color:#00a8ff;'>Detalle: Mercadería Instruida</h3>", unsafe_allow_html=True)
                df_mostrar = df_inst[['SO', 'Proveedor', 'M3 Total', 'Fecha de Instruccion']].copy()
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {len(df_mostrar)}'], 'Proveedor': [f'TOTAL PROV: {df_mostrar["Proveedor"].nunique()}'], 'M3 Total': [df_mostrar['M3 Total'].sum()], 'Fecha de Instruccion': ['']})
                st.dataframe(pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))]).style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif f == "crit":
                st.markdown("<h3 style='color:#ff4b4b;'>⚠️ Detalle: Próximo a Instruir</h3>", unsafe_allow_html=True)
                df_mostrar = df_criticos[['SO', 'Proveedor', df.columns[99], 'M3 Total']].sort_values(by=df.columns[99])
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {len(df_mostrar)}'], 'Proveedor': [f'TOTAL PROV: {df_mostrar["Proveedor"].nunique()}'], df.columns[99]: [''], 'M3 Total': [df_mostrar['M3 Total'].sum()]})
                st.dataframe(pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))]).style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif f == "rest":
                st.markdown("<h3 style='color:#00a8ff;'>Detalle: Resto Pendiente</h3>", unsafe_allow_html=True)
                df_mostrar = df_resto[['SO', 'Proveedor', df.columns[99], 'M3 Total']]
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {len(df_mostrar)}'], 'Proveedor': [f'TOTAL PROV: {df_mostrar["Proveedor"].nunique()}'], df.columns[99]: [''], 'M3 Total': [df_mostrar['M3 Total'].sum()]})
                st.dataframe(pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))]).style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif f == "rank":
                st.markdown("<h3 style='color:#00a8ff;'>Top 100 Ranking</h3>", unsafe_allow_html=True)
                col_rank = df.columns[1]
                df[col_rank] = pd.to_numeric(df[col_rank], errors='coerce').fillna(0).astype(int)
                df_rank = df[(df[col_rank] >= 1) & (df[col_rank] <= 100)].sort_values(by=col_rank)
                df_mostrar = df_rank[['SO', col_rank, 'M3 Total']].copy()
                total_row = pd.DataFrame({'SO': ['TOTAL'], col_rank: [''], 'M3 Total': [df_mostrar['M3 Total'].sum()]})
                st.dataframe(pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))]).style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif f == "estr":
                st.markdown("<h3 style='color:#00a8ff;'>Estructura de Carga</h3>", unsafe_allow_html=True)
                col_cp = df.columns[93]
                df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
                res_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3'})
                res_total = pd.DataFrame({'Cant. SO': [res_tipo['Cant. SO'].sum()], 'M3': [res_tipo['M3'].sum()]}, index=['TOTAL'])
                st.table(pd.concat([res_tipo, res_total]).style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}'}))

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- PARTICIPACIÓN PAÍS ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
        res_p['%'] = (res_p['M3'] / m3_totales_global * 100).round(0)
        df_total_p = pd.DataFrame({'CANT. SO': [res_p['CANT. SO'].sum()], 'M3': [res_p['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        st.dataframe(pd.concat([res_p, df_total_p]).style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL GENERAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}', '%': '{:.0f}%', 'CANT. SO': '{:,.0f}'}), use_container_width=True)
        
        # --- GRÁFICOS ---
        g1, g2, g3 = st.columns([1.2, 1, 1])
        with g1:
            st.markdown("<p class='chart-title'>Salida por Puerto</p>", unsafe_allow_html=True)
            col_puerto = df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_traces(textfont_size=14, textposition='outside', cliponaxis=False)
            fig_p.update_layout(xaxis_visible=False, yaxis_title=None, height=450)
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            st.markdown("<p class='chart-title'>Proyección ETD</p>", unsafe_allow_html=True)
            etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig_e.update_traces(textfont_size=14, textposition='outside')
            fig_e.update_layout(yaxis_visible=False, xaxis_title=None, height=450)
            st.plotly_chart(fig_e, use_container_width=True)
        with g3:
            st.markdown("<p class='chart-title'>Proyección ETA</p>", unsafe_allow_html=True)
            eta_p = df.groupby('Mes_ETA_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig_a.update_traces(textfont_size=14, textposition='outside')
            fig_a.update_layout(yaxis_visible=False, xaxis_title=None, height=450)
            st.plotly_chart(fig_a, use_container_width=True)

    with tabs[1]:
        # --- STATUS CARGAS ---
        df_reserva = pd.read_csv(f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}")
        df_reserva.columns = df_reserva.columns.str.strip()
        st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 3px;'>MONITOREO DE RESERVAS</h2>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-container'><p class='label-massive'>SO INSTRUIDAS</p><p class='value-massive'>{int(len(df_inst))}</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN (M3)</p><p class='value-massive'>{int(df_inst['M3 Total'].sum()):,}</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(df_inst['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)
        st.dataframe(df_reserva, use_container_width=True, height=500)

except Exception as e:
    st.error(f"Error general: {e}")
