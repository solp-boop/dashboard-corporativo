import time
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
    
    .stTabs [data-baseweb="tab-list"] { 
        justify-content: center !important; 
        gap: 30px; 
        margin-bottom: 40px;
    }

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

    .metric-container { text-align: center; padding: 20px; }
    .label-massive { font-size: 24px; color: #00a8ff; letter-spacing: 5px; text-transform: uppercase; font-weight: 800; margin-bottom: 5px; }
    .value-massive { font-size: 120px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 30px rgba(0,168,255,0.5); }

    .stButton>button {
        border-radius: 15px !important; 
        color: white !important;
        width: 100%; height: 140px; font-weight: 800 !important; font-size: 18px !important;
        background: rgba(255, 255, 255, 0.03) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease-in-out !important;
    }

    .stButton>button:hover { 
        background-color: rgba(0, 168, 255, 0.2) !important; 
        border-color: #00a8ff !important; 
        color: #00a8ff !important;
        box-shadow: 0 0 20px rgba(0, 168, 255, 0.4) !important;
    }
    
    .chart-title { text-align: center; letter-spacing: 2px; color: #00a8ff; font-weight: 900; font-size: 20px; margin: 25px 0 15px 0; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

try:
    # 1. Carga de Datos (Hoja Principal GID 0)
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    df = pd.read_csv(f"{base_url}/export?format=csv&gid=0")
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    
   # --- PROCESAMIENTO DE FECHAS (OPTIMIZADO PARA EVITAR "SIN FECHA") ---
    # Usamos las columnas 23 (ETD) y 24 (ETA) según tu estructura
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    
    # Fecha Prioritaria (Columna 99 / CV)
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], errors='coerce') 
    
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)

    def label_proyeccion(fecha, pivot):
        # Si después de 'coerce' sigue siendo NaT, es que realmente está vacío o el formato es irreconocible
        if pd.isna(fecha): 
            return "SIN FECHA"
        # Si la fecha es muy vieja (ej: año 1900 o error de carga), lo agrupamos en PASADO
        if fecha.year < 2020:
            return "PASADO/REALIZADO"
        if fecha < pivot: 
            return "PASADO/REALIZADO"
        return fecha.strftime('%m/%Y')

    # Aplicamos la lógica a las nuevas columnas de proyección
    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    # --- ORDENAMIENTO DE LAS COLUMNAS DEL GRÁFICO ---
    # Esto asegura que PASADO vaya al principio y SIN FECHA al final, no mezclados
    orden_meses = sorted([m for m in df['Mes_ETA_Full'].unique() if m not in ["PASADO/REALIZADO", "SIN FECHA"]])
    categoria_orden = ["PASADO/REALIZADO"] + orden_meses + ["SIN FECHA"]
    df['Mes_ETA_Full'] = pd.Categorical(df['Mes_ETA_Full'], categories=categoria_orden, ordered=True)
    # --- HEADER ---
    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logistica Internacional</div></div>", unsafe_allow_html=True)
    
    tabs = st.tabs(["ORIGEN", "STATUS CARGAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

    # --- TODO EN SOLAPA ORIGEN ---
    with tabs[0]:
        # --- BLOQUE 1: MÉTRICAS ---
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric-container'><p class='label-massive'>CANTIDAD DE SO</p><p class='value-massive'>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN TOTAL</p><p class='value-massive'>{int(m3_totales_global):,}</p></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BLOQUE 2: BOTONES ---
        b1_col, b2_col, b3_col, b4_col = st.columns(4)
        
        df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
        cond_pend = df['Fecha_Inst_DT'].isna() | (df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=True))
        
        df_instruidos_only = df[~cond_pend].copy()
        df_pendientes_only = df[cond_pend].copy()
        
        p_inst = round(df_instruidos_only['M3 Total'].sum() / m3_totales_global * 100) if m3_totales_global > 0 else 0

        col_cp = df.columns[93]
        df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).upper() == 'SI' else 'CONSOLIDADO')
        stats_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count'})
        p_mono_bot = round(stats_tipo.loc['MONOPROVEEDOR', 'SO'] / len(df) * 100) if 'MONOPROVEEDOR' in stats_tipo.index else 0

        with b1_col:
            if st.button(f"MERCADERIA INSTRUIDA \n {p_inst}%"):
                st.session_state.f = None if st.session_state.get('f') == 'inst' else 'inst'
        with b2_col:
            if st.button(f"PENDIENTE INSTRUCCIÓN \n {100-p_inst}%"):
                st.session_state.f = None if st.session_state.get('f') == 'pend' else 'pend'
        with b3_col:
            if st.button("PRODUCTOS TOP RANKING \n (1-100)"):
                st.session_state.f = None if st.session_state.get('f') == 'rank' else 'rank'
        with b4_col:
            if st.button(f"ESTRUCTURA DE CARGA \n Mono: {p_mono_bot}% | Cons: {100-p_mono_bot}%"):
                st.session_state.f = None if st.session_state.get('f') == 'estr' else 'estr'

        # --- LÓGICA DE DESPLEGABLES ---
        if st.session_state.get('f'):
            st.
            markdown("---")
            f = st.session_state.f
            
            if f == "inst":
                st.markdown("<h3 style='color:#00a8ff;'>Detalle: Mercaderia Instruida</h3>", unsafe_allow_html=True)
                df_mostrar = df_instruidos_only[['SO', 'Proveedor', 'M3 Total', 'Fecha de Instruccion']].copy()
                t_so, t_prov, t_m3 = len(df_mostrar), df_mostrar['Proveedor'].nunique(), df_mostrar['M3 Total'].sum()
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {t_so}'], 'Proveedor': [f'TOTAL PROV: {t_prov}'], 'M3 Total': [t_m3], 'Fecha de Instruccion': ['']})
                df_final = pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))])
                st.dataframe(df_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)

            elif f == "pend":
                st.markdown("<h3 style='color:#00a8ff;'>Detalle: Pendientes de Instrucción (Por Fecha Prioritaria)</h3>", unsafe_allow_html=True)
                df_pend_list = df_pendientes_only.sort_values(by='Fecha_Prior_DT', ascending=True).copy()
                df_mostrar_pend = df_pend_list[['SO', 'Proveedor', df.columns[99], 'M3 Total']].copy()
                t_so_p, t_prov_p, t_m3_p = len(df_mostrar_pend), df_mostrar_pend['Proveedor'].nunique(), df_mostrar_pend['M3 Total'].sum()
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {t_so_p}'], 'Proveedor': [f'TOTAL PROV: {t_prov_p}'], df.columns[99]: [''], 'M3 Total': [t_m3_p]})
                df_final = pd.concat([df_mostrar_pend, total_row.set_index(pd.Index(['TOTAL']))])
                st.dataframe(df_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)

            elif f == "rank":
                st.markdown("<h3 style='color:#00a8ff;'>Top 100: Prioridad de Salida</h3>", unsafe_allow_html=True)
                col_rank = df.columns[1]
                df[col_rank] = pd.to_numeric(df[col_rank], errors='coerce').fillna(0).astype(int)
                df_rank = df[(df[col_rank] >= 1) & (df[col_rank] <= 100)].sort_values(by=col_rank)
                df_mostrar = df_rank[['SO', col_rank, df.columns[99], 'Fecha de Instruccion', 'M3 Total', 'Puerto de Salida']].copy()
                t_m3_r = df_mostrar['M3 Total'].sum()
                total_row = pd.DataFrame({'SO': ['TOTAL'], col_rank: [''], df.columns[99]: [''], 'Fecha de Instruccion': [''], 'M3 Total': [t_m3_r], 'Puerto de Salida': ['']})
                df_final = pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))])
                st.dataframe(df_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)

            elif f == "estr":
                st.markdown("<h3 style='color:#00a8ff;'>Análisis Monoproveedor vs Consolidado</h3>", unsafe_allow_html=True)
                res_tipo = df.groupby('Tipo_Carga').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'Cant. SO', 'M3 Total': 'M3'})
                res_tipo['%'] = (res_tipo['M3'] / m3_totales_global * 100).round(0)
                res_total = pd.DataFrame({'Cant. SO': [res_tipo['Cant. SO'].sum()], 'M3': [res_tipo['M3'].sum()], '%': [100]}, index=['TOTAL'])
                res_final = pd.concat([res_tipo, res_total])
                st.table(res_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}', 'Cant. SO': '{:,.0f}', '%': '{:.0f}%'}))

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # --- BLOQUE 3: PARTICIPACIÓN PAÍS ---
        st.markdown("<p class='chart-title'>Participación por País de Destino</p>", unsafe_allow_html=True)
        res_p = df.groupby('Pais Destino').agg({'SO': 'count', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT. SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
        res_p['%'] = (res_p['M3'] / m3_totales_global * 100).round(0)
        df_total_p = pd.DataFrame({'CANT. SO': [res_p['CANT. SO'].sum()], 'M3': [res_p['M3'].sum()], '%': [100]}, index=['TOTAL GENERAL'])
        res_p_final = pd.concat([res_p, df_total_p])
        st.dataframe(res_p_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL GENERAL' else '' for _ in s], axis=1).format({'M3': '{:,.0f}', '%': '{:.0f}%', 'CANT. SO': '{:,.0f}'}), use_container_width=True)

        # --- BLOQUE 4: GRÁFICOS ---
        g1, g2, g3 = st.columns([1.2, 1, 1])
        with g1:
            st.markdown("<p class='chart-title'>Salida por Puerto</p>", unsafe_allow_html=True)
            col_puerto = 'Puerto de Salida' if 'Puerto de Salida' in df.columns else df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], template='plotly_dark')
            fig_p.update_traces(textfont_size=18, textfont_color="white", textposition='outside')
            fig_p.update_layout(xaxis_title=None, yaxis_title=None, height=500)
            st.plotly_chart(fig_p, use_container_width=True)

        with g2:
            st.markdown("<p class='chart-title'>Proyección ETD (Salidas)</p>", unsafe_allow_html=True)
            etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig_e.update_traces(textfont_size=18, textfont_color="white", textposition='outside')
            fig_e.update_layout(xaxis_title=None, yaxis_title=None, height=500)
            st.plotly_chart(fig_e, use_container_width=True)

        with g3:
            st.markdown("<p class='chart-title'>Proyección ETA (Arribos)</p>", unsafe_allow_html=True)
            eta_p = df.groupby('Mes_ETA_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig_a.update_traces(textfont_size=18, textfont_color="white", textposition='outside')
            fig_a.update_layout(xaxis_title=None, yaxis_title=None, height=500)
            st.plotly_chart(fig_a, use_container_width=True)

# --- SOLAPA 2: STATUS CARGAS ---
    with tabs[1]:
        try:
            # 1. CARGA DE DATOS ESPECÍFICA (Hoja Reservas GID 276804813)
            url_reserva = f"{base_url}/export?format=csv&gid=276804813"
            df_reserva = pd.read_csv(url_reserva)
            df_reserva.columns = df_reserva.columns.str.strip()

            # --- PROCESAMIENTO DE DATOS ---
            # Mapeo de TIPO (Columna F: "Tipo Carga")
            def categorizar_transporte(x):
                x = str(x).upper()
                if any(ext in x for ext in ['40 HQ', '40 ST', '20 ST', '40NOR', 'LCL']):
                    return "MARITIMO"
                if any(ext in x for ext in ['AVION', 'COURIER', 'AEREO']):
                    return "AVION / COURIER"
                return "OTROS"

            df_reserva['Categoria'] = df_reserva.iloc[:, 5].apply(categorizar_transporte) # Columna F

            # Fechas para cálculos (Columna K: ETD OK FFWW y Columna de Instrucción si existe)
            # Asumimos que la columna K es la fecha de confirmación real
            df_reserva['ETD_OK_DT'] = pd.to_datetime(df_reserva.iloc[:, 10], errors='coerce') # Columna K
            
            # 2. CÁLCULO DE INDICADORES
            total_inst = len(df_reserva)
            con_etd_ok = df_reserva['ETD_OK_DT'].notna().sum()
            sin_etd_ok = total_inst - con_etd_ok
            
            p_confirmado = (con_etd_ok / total_inst * 100) if total_inst > 0 else 0
            p_pendiente = 100 - p_confirmado

            # --- RENDERIZADO DE MÉTRICAS ---
            st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 3px;'>CONTROL DE GESTIÓN DE RESERVAS</h2>", unsafe_allow_html=True)
            
            # Fila 1: Totales de Confirmación
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("EMBARQUES CON ETD OK", f"{con_etd_ok}")
            m2.metric("SIN ETD OK", f"{sin_etd_ok}")
            m3.metric("% CONFIRMADO", f"{p_confirmado:.1f}%")
            m4.metric("% SIN CONFIRMACIÓN", f"{p_pendiente:.1f}%")

            st.markdown("---")

            # Fila 2: Desglose por Tipo (Marítimo vs Avion)
            st.markdown("<p class='chart-title'>Desglose por Tipo de Transporte</p>", unsafe_allow_html=True)
            tipo_cols = st.columns(2)
            
            for i, tipo in enumerate(["MARITIMO", "AVION / COURIER"]):
                df_tipo = df_reserva[df_reserva['Categoria'] == tipo]
                with tipo_cols[i]:
                    st.markdown(f"""
                        <div style='background: rgba(0, 168, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid #004080;'>
                            <h4 style='color: #00a8ff; margin: 0;'>{tipo}</h4>
                            <p style='font-size: 24px; font-weight: bold; margin: 10px 0;'>Total: {len(df_tipo)}</p>
                            <small>ETD OK: {df_tipo['ETD_OK_DT'].notna().sum()} | Pendientes: {df_tipo['ETD_OK_DT'].isna().sum()}</small>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 3. TABLA DETALLADA
            st.markdown("<p class='chart-title'>Detalle de la Hoja de Reservas</p>", unsafe_allow_html=True)
            busqueda = st.text_input("🔍 Filtrar en Reservas:", key="search_res_final")
            
            if busqueda:
                df_final = df_reserva[df_reserva.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
            else:
                df_final = df_reserva

            st.dataframe(df_final.drop(columns=['ETD_OK_DT', 'Categoria']), use_container_width=True, height=400)

        except Exception as e:
            st.error(f"Error en Status Cargas: {e}")

except Exception as e:
    st.error(f"Error: {e}")
