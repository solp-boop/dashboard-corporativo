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
    
    /* Estilos para KPI de Reservas */
    .reserva-box {
        background: rgba(0, 168, 255, 0.05);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #004080;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

try:
    # --- 3. CARGA DE DATOS ---
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"

    # Origen (GID 0)
    df = pd.read_csv(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")
    df.columns = df.columns.str.strip()

    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)

    # Procesamiento Fechas Origen
    df.iloc[:, 23] = df.iloc[:, 23].astype(str).str.strip()
    df.iloc[:, 24] = df.iloc[:, 24].astype(str).str.strip()
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], errors='coerce') 

    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)
    limite_proximo = hoy + timedelta(days=30)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        if fecha.year < 2024: return "PASADO/REALIZADO"
        if fecha < pivot: return "PASADO/REALIZADO"
        return fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    meses_eta = [m for m in df['Mes_ETA_Full'].unique() if m not in ["PASADO/REALIZADO", "SIN FECHA"]]
    meses_eta_ordenados = sorted(meses_eta, key=lambda x: datetime.strptime(x, '%m/%Y'))
    orden_final_eta = ["PASADO/REALIZADO"] + meses_eta_ordenados + ["SIN FECHA"]
    df['Mes_ETA_Full'] = pd.Categorical(df['Mes_ETA_Full'], categories=orden_final_eta, ordered=True)

    m3_totales_global = round(df['M3 Total'].sum())
    cant_so_global = len(df)
    cant_proveedores_global = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logistica Internacional</div></div>", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "CONTROL GESTIÓN RESERVAS", "INDICADORES", "AGENTES", "ANALISTAS", "FLETES"])

# --- SOLAPA 1: RANKING DE PROVEEDORES ---
    with tab1:
        st.subheader("🏆 Ranking de Proveedores")
        
        # Métrica para el ranking
        col_rank = st.selectbox(
            "Seleccionar métrica para ranking:",
            ['Cant. de SO', 'Total USD', 'Ahorro USD'],
            key='sel_rank_tab1'
        )

        # Procesamiento de datos para el ranking
        df_rank = df_filtrado.groupby('Proveedor').agg({
            'SO': 'count',
            'Total USD': 'sum',
            'Ahorro USD': 'sum'
        }).rename(columns={'SO': 'Cant. de SO'}).sort_values(by=col_rank, ascending=False).reset_index()

        # Mostrar Tabla de Ranking
        st.write(f"Detalle de proveedores ordenados por {col_rank}:")
        
        # LÍNEA 194 CORREGIDA: Se cierran los corchetes de la lista y el paréntesis de st.dataframe
        st.dataframe(df_rank[['Proveedor', 'Cant. de SO', 'Total USD', 'Ahorro USD']], use_container_width=True)

        st.markdown("---")

        # Gráfico de barras del Top 10
        st.subheader(f"Top 10 Proveedores por {col_rank}")
        fig_rank = px.bar(
            df_rank.head(10), 
            x='Proveedor', 
            y=col_rank, 
            color=col_rank,
            text_auto='.2s',
            color_continuous_scale='Blues',
            labels={col_rank: col_rank, 'Proveedor': 'Proveedor'}
        )
        fig_rank.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_rank, use_container_width=True)

        # Métricas rápidas del líder
        if not df_rank.empty:
            top_prov = df_rank.iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("Proveedor Líder", top_prov['Proveedor'])
            col2.metric(f"{col_rank} (Líder)", f"{top_prov[col_rank]:,.2f}")
            col3.metric("Participación", f"{(top_prov[col_rank] / df_rank[col_rank].sum() * 100):.1f}%")
# --- SOLAPA 2: CONTROL GESTIÓN RESERVAS ---
    with tabs[1]:
        try:
            # 1. CARGA DE DATOS CON GESTIÓN DE ERRORES (REINTENTOS)
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"

            @st.cache_data(ttl=60)  # Caché de 1 minuto para evitar IncompleteRead constantes
            def load_reserva_data(url):
                # Intentamos cargar con un motor de lectura más robusto
                return pd.read_csv(url, engine='python', on_bad_lines='skip')

            try:
                df_res = load_reserva_data(url_reserva)
            except Exception:
                # Si falla el caché o la red, forzamos una lectura limpia
                df_res = pd.read_csv(url_reserva)

            df_res.columns = df_res.columns.str.strip()

            # Filtrar solo lo instruido (Columna H = índice 7)
            df_res['Fecha_Inst_H'] = df_res.iloc[:, 7].astype(str).str.strip()
            df_g = df_res[df_res['Fecha_Inst_H'].apply(lambda x: len(str(x)) > 4)].copy()

            # --- BLOQUE 1: KPIs GRANDES ---
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>SO INSTRUIDAS</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(len(df_inst))}</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>VOLUMEN (M3)</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(round(df_inst['M3 Total'].sum())):,}</p></div>", unsafe_allow_html=True)
            with k3: st.markdown(f"<div class='metric-container'><p style='font-size: 22px; color: #00a8ff; letter-spacing: 4px; font-weight: 700; margin-bottom: 0;'>PROVEEDORES</p><p style='font-size: 90px; font-weight: 900; color: #00a8ff; line-height: 1; margin: 0; text-shadow: 0 0 25px rgba(0,168,255,0.4);'>{int(df_inst['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)

            st.markdown("<br><hr style='opacity:0.1;'><br>", unsafe_allow_html=True)

            # --- BLOQUE 2: PERFORMANCE GLOBAL ---
            df_g['ETD_Status_K'] = df_g.iloc[:, 10].astype(str).str.upper().str.strip()
            confirmados_glob = len(df_g[df_g['ETD_Status_K'] == "OK"])
            pendientes_glob = len(df_g) - confirmados_glob
            p_ok_glob = round((confirmados_glob / len(df_g) * 100)) if len(df_g) > 0 else 0

            _, c_mid, _ = st.columns([0.1, 1, 0.1])
            with c_mid:
                m1, m2, m3, m4 = st.columns(4)
                m1.markdown(f"<div style='text-align:center;'><p style='font-weight:700; font-size:14px; margin:0;'>ETD OK (TOTAL)</p><p style='font-weight:300; font-size:32px; margin:0;'>{confirmados_glob} Emb.</p></div>", unsafe_allow_html=True)
                m2.markdown(f"<div style='text-align:center;'><p style='font-weight:700; font-size:14px; margin:0;'>PENDIENTES (TOTAL)</p><p style='font-weight:300; font-size:32px; margin:0;'>{pendientes_glob} Emb.</p></div>", unsafe_allow_html=True)
                m3.markdown(f"<div style='text-align:center;'><p style='font-weight:700; font-size:14px; margin:0;'>% EFECTIVIDAD</p><p style='font-weight:300; font-size:32px; margin:0;'>{int(p_ok_glob)}%</p></div>", unsafe_allow_html=True)
                m4.markdown(f"<div style='text-align:center;'><p style='font-weight:700; font-size:14px; margin:0;'>% PENDIENTE</p><p style='font-weight:300; font-size:32px; margin:0;'>{int(100 - p_ok_glob)}%</p></div>", unsafe_allow_html=True)

            st.markdown("<br><p style='text-align:center; color:#00a8ff; font-weight:700; letter-spacing:2px; font-size:12px;'>DESGLOSE POR TIPO DE TRANSPORTE</p>", unsafe_allow_html=True)

            # --- BLOQUE 3: MARITIMO VS AEREO ---
            def clasificar_transporte(x):
                x = str(x).upper()
                if any(m in x for m in ["40 HQ", "40 ST", "20 ST", "40NOR"]): return "MARITIMO"
                if any(a in x for a in ["AVION", "COURIER", "COURRIER"]): return "AVION / COURIER"
                return "OTROS"

            df_g['Transporte'] = df_g.iloc[:, 5].apply(clasificar_transporte) 
            t1, t2 = st.columns(2)
            for i, tipo in enumerate(["MARITIMO", "AVION / COURIER"]):
                df_tipo = df_g[df_g['Transporte'] == tipo]
                total_t = len(df_tipo)
                ok_t = len(df_tipo[df_tipo['ETD_Status_K'] == "OK"])
                pend_t = total_t - ok_t
                pct_ok = round((ok_t / total_t * 100)) if total_t > 0 else 0
                pct_pend = 100 - pct_ok if total_t > 0 else 0
                color_status = "#00ff88" if ok_t >= pend_t and total_t > 0 else "#ff4b4b"
                flecha = "▲" if ok_t >= pend_t else "▼"
                with [t1, t2][i]:
                    st.markdown(f"""<div style="background: #040911; padding: 20px; border-radius: 10px; border: 1px solid #1e293b; min-height: 140px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <p style="color: #00a8ff; font-weight: 700; margin: 0; font-size: 16px;">{tipo}</p>
                            <div style="text-align: right;">
                                <p style="color: {color_status}; font-weight: 300; margin: 0; font-size: 18px;">{flecha} {int(pct_ok)}% <span style="font-size:12px; color:#8899A6; margin-left:5px;">OK</span></p>
                                <p style="color: #ff4b4b; font-weight: 300; margin: 0; font-size: 14px; opacity: 0.8;">{int(pct_pend)}% <span style="font-size:10px; color:#8899A6;">PEND</span></p>
                            </div>
                        </div>
                        <p style="font-size: 28px; font-weight: 300; color: #ffffff; margin-top: 10px; margin-bottom: 5px;">Total: {total_t}</p>
                        <p style="font-size: 12px; color: #94a3b8; font-weight: 300; margin: 0;"><span style="color: #00ff88;">Confirmados: {ok_t}</span> | <span style="color: #ff4b4b;">Pendientes: {pend_t}</span></p>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- BLOQUE 4: ANÁLISIS MARÍTIMO (BOTONES CON TOGGLE) ---
            df_mar = df_g[df_g['Transporte'] == "MARITIMO"].copy()

            def clean_val(value):
                if pd.isna(value): return 0
                s = str(value).replace('.', '').replace(',', '.')
                num = ''.join(c for c in s if c.isdigit() or c == '.')
                return pd.to_numeric(num, errors='coerce') if num else 0

            df_mar.iloc[:, 1] = pd.to_numeric(df_mar.iloc[:, 1], errors='coerce').fillna(0)
            df_mar.iloc[:, 29] = pd.to_numeric(df_mar.iloc[:, 29], errors='coerce').fillna(0)
            df_mar.iloc[:, 21] = df_mar.iloc[:, 21].apply(clean_val).fillna(0)

            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("ANALISIS BOOKING IN ADVANCE", key="btn_adv", use_container_width=True):
                st.session_state.mode = 'adv' if st.session_state.get('mode') != 'adv' else None
            if c_btn2.button("ANALISIS MONOPROVEEDOR / CONSOLIDADO", key="btn_mono", use_container_width=True):
                st.session_state.mode = 'mono' if st.session_state.get('mode') != 'mono' else None

            mode = st.session_state.get('mode')
            if mode:
                st.markdown("<br>", unsafe_allow_html=True)
                col_a, col_b = st.columns(2)

                if mode == 'adv':
                    mask = df_mar.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
                    labels = [("Booked in Advance", df_mar[mask]), ("No Booked in Advance", df_mar[~mask])]
                else:
                    mask = df_mar.iloc[:, 34].astype(str).str.strip() == "Monoproveedor"
                    labels = [("Monoproveedor", df_mar[mask]), ("Consolidado", df_mar[~mask])]

                total_m = len(df_mar) if len(df_mar) > 0 else 1
                for i, (titulo, dff) in enumerate(labels):
                    cant_emb = len(dff)
                    pct_rel = round((cant_emb / total_m) * 100)
                    mask_adv_check = dff.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
                    cant_adv = len(dff[mask_adv_check])
                    pct_adv = round((cant_adv / cant_emb * 100)) if cant_emb > 0 else 0
                    pct_no_adv = 100 - pct_adv if cant_emb > 0 else 0

                    with [col_a, col_b][i]:
                        color_box = "#00a8ff" if i == 0 else "#8899A6"
                        st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.02); padding: 25px; border-radius: 10px; border-left: 5px solid {color_box};">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                                    <p style="font-weight:700; color:{color_box}; margin:0; font-size:14px; letter-spacing:1px;">{titulo.upper()} ({int(pct_rel)}%)</p>
                                    <div style="text-align: right;">
                                        <p style="font-size:10px; color:#00ff88; font-weight:700; margin:0;">ADVANCE: {int(pct_adv)}%</p>
                                        <p style="font-size:10px; color:#ff4b4b; font-weight:700; margin:0;">SPOT: {int(pct_no_adv)}%</p>
                                    </div>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                    <div><p style="font-size:11px; color:#8899A6; margin:0;">EMBARQUES</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{int(cant_emb)}</p></div>
                                    <div><p style="font-size:11px; color:#8899A6; margin:0;">CONTENEDORES</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{int(round(dff.iloc[:, 1].sum()))}</p></div>
                                    <div><p style="font-size:11px; color:#8899A6; margin:0;">PROM. CONSOLIDACIÓN</p><p style="font-size:26px; font-weight:300; margin:0; color:#ffffff;">{int(round(dff.iloc[:, 29].mean() if cant_emb > 0 else 0))}d</p></div>
                                    <div><p style="font-size:11px; color:#8899A6; margin:0;">FOB TOTAL</p><p style="font-size:22px; font-weight:300; margin:0; color:#ffffff;">USD {int(round(dff.iloc[:, 21].sum())):,}</p></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Gestión de Reservas: {e}")
# ==========================================
    # SOLAPA 3: INDICADORES (SLA & CONSOLIDACIÓN)
    # SOLAPA 3: INDICADORES (VERSIÓN EJECUTIVA COMPLETA)
    # ==========================================
    with tabs[2]:
        # CSS AISLADO: Solo afecta a los botones dentro de este contenedor específico
        # CSS AISLADO: Micro-botones y estados profesionales
        st.markdown("""
            <style>
            /* Micro-botones exclusivos para la Solapa 3 */
            .stTabs [data-testid="stVerticalBlock"] div[data-testid="stColumn"] button {
                height: 25px !important;
                min-height: 25px !important;
                width: 100% !important;
                padding: 0px !important;
                font-size: 10px !important;
                margin-top: 10px !important;
                border-radius: 4px !important;
                background: rgba(0, 168, 255, 0.1) !important;
                border: 1px solid rgba(0, 168, 255, 0.3) !important;
            }
            .kpi-highlight {
                font-size: 22px !important;
                font-weight: 900 !important;
                margin: 0;
            }
            .sla-badge {
            .kpi-highlight { font-size: 20px !important; font-weight: 900 !important; margin: 0; }
            .sla-status {
                text-align: center;
                border-radius: 5px;
                margin-top: 10px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
                border-radius: 6px;
                margin-top: 8px;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 0;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            </style>
        """, unsafe_allow_html=True)

        try:
            # 1. CARGA DE DATOS (Reservas Historicas GID 32771816)
            # --- 1. PREPARACIÓN DE DATOS ---
            url_hist = f"{base_url}/export?format=csv&gid=32771816&nocache={time.time()}"
            df_h = pd.read_csv(url_hist, engine='python')
            df_h.columns = df_h.columns.str.strip()

            nombres_meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

            # Limpieza de fechas y conversión AE(30), AF(31), AG(32)
            df_h['ETD_DT'] = pd.to_datetime(df_h.iloc[:, 11], dayfirst=True, errors='coerce')
            for i in [30, 31, 32]:
                df_h.iloc[:, i] = pd.to_numeric(df_h.iloc[:, i].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

            def es_maritimo(x):
                return any(m in str(x).upper() for m in ["40 HQ", "40 ST", "20 ST", "40NOR", "MARITIMO"])

            df_ind = df_h[(df_h['ETD_DT'].dt.year == 2026) & (df_h.iloc[:, 5].apply(es_maritimo))].copy()
            df_ind['Mes_Num'] = df_ind['ETD_DT'].dt.month

            # --- FUNCIÓN DIALOG (MODAL DE SLA) ---
            # --- 2. MODAL DE ANÁLISIS ---
            @st.dialog("ANÁLISIS DE SLA POR PUERTO", width="large")
            def mostrar_detalle(df_f, nombre_mes, meta_val):
                st.subheader(f"Performance: {nombre_mes} 2026")
                st.info(f"Meta SLA: <= {meta_val} días")
                
                puerto_col = df_ind.columns[4] # Columna E
                tiempo_col = df_ind.columns[32] # Columna AG

                df_p = df_f.groupby(puerto_col).agg(
                    Total_Emb=(df_ind.columns[0], 'count'),
                    Prom_Consol=(tiempo_col, 'mean'),
                    Dentro_SLA=(tiempo_col, lambda x: (x <= meta_val).sum()),
                    Fuera_SLA=(tiempo_col, lambda x: (x > meta_val).sum())
                ).reset_index()

                df_p['Dentro SLA %'] = (df_p['Dentro_SLA'] / df_p['Total_Emb'] * 100)
                df_p['Fuera SLA %'] = (df_p['Fuera_SLA'] / df_p['Total_Emb'] * 100)
                
                # Fila de Totales del Mes
                t_e = df_p["Total_Emb"].sum()
                t_row = pd.DataFrame({
                    puerto_col: ["TOTAL MENSUAL"], "Total_Emb": [t_e],
                    "Prom_Consol": [df_f[tiempo_col].mean()],
                    "Dentro SLA %": [(df_p['Dentro_SLA'].sum()/t_e*100) if t_e>0 else 0],
                    "Fuera SLA %": [(df_p['Fuera_SLA'].sum()/t_e*100) if t_e>0 else 0]
                })

                df_final_modal = pd.concat([df_p[[puerto_col, "Total_Emb", "Prom_Consol", "Dentro SLA %", "Fuera SLA %"]], t_row], ignore_index=True)
                st.dataframe(df_final_modal.style.format(precision=0).set_properties(subset=pd.IndexSlice[df_final_modal.index[-1], :], **{'background-color': '#001f3f'}), use_container_width=True, hide_index=True)

            # --- SECCIÓN 1: CONSOLIDACIÓN GENERAL (AZUL) ---
                puerto_col = df_ind.columns[4]
                tiempo_col = df_ind.columns[32]
                df_p = df_f.groupby(puerto_col).agg(Cant=(df_ind.columns[0],'count'), Prom=(tiempo_col,'mean'), 
                                                  OK=(tiempo_col, lambda x: (x<=meta_val).sum())).reset_index()
                df_p['SLA %'] = (df_p['OK'] / df_p['Cant'] * 100)
                st.dataframe(df_p.style.format(precision=0), use_container_width=True, hide_index=True)

            # --- 3. SECCIÓN 1: CONSOLIDACIÓN GENERAL (AZUL) ---
            st.markdown("<br><p style='color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:22px; text-align:center;'>INDICADORES DE CONSOLIDACIÓN 2026</p>", unsafe_allow_html=True)
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1, 0.8, 1, 1, 1.3, 0.8, 0.8, 0.4])
            
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1, 0.8, 1, 1, 1.3, 0.8, 0.8, 0.5])
            headers = ["MES", "EMBARQUES", "T. COMEX", "T. AGENTE", "TIEMPO TOTAL", "% MONO", "% CONSOL", "INFO"]
            for i, col in enumerate([h1, h2, h3, h4, h5, h6, h7, h8]):
                col.markdown(f"<p style='color:#8899A6; font-size:10px; font-weight:700; text-align:center;'>{headers[i]}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border-top: 2px solid #00a8ff;'>", unsafe_allow_html=True)

            res_gen = df_ind.groupby('Mes_Num').agg({df_ind.columns[0]:'count', df_ind.columns[30]:'mean', df_ind.columns[31]:'mean', df_ind.columns[32]:'mean'}).reset_index()
            
            for _, row in res_gen.iterrows():
                m_idx = int(row['Mes_Num'])
                df_m = df_ind[df_ind['Mes_Num'] == m_idx]
                p_mono = int(round((len(df_m[df_m.iloc[:, 24].astype(str).str.upper().str.contains("SI|MONO", na=False)])/len(df_m))*100)) if len(df_m)>0 else 0
                r1, r2, r3, r4, r5, r6, r7, r8 = st.columns([1, 0.8, 1, 1, 1.3, 0.8, 0.8, 0.4])
                
                r1, r2, r3, r4, r5, r6, r7, r8 = st.columns([1, 0.8, 1, 1, 1.3, 0.8, 0.8, 0.5])
                r1.markdown(f"<p style='text-align:center; font-weight:700; margin-top:12px;'>{nombres_meses.get(m_idx)}</p>", unsafe_allow_html=True)
                r2.markdown(f"<p style='text-align:center; margin-top:12px;'>{int(row.iloc[1])}</p>", unsafe_allow_html=True)
                r3.markdown(f"<p style='text-align:center; margin-top:12px; color:#8899A6;'>{int(round(row.iloc[2]))}d</p>", unsafe_allow_html=True)
                r4.markdown(f"<p style='text-align:center; margin-top:12px; color:#8899A6;'>{int(round(row.iloc[3]))}d</p>", unsafe_allow_html=True)
                r5.markdown(f"<p class='kpi-highlight' style='text-align:center; color:#00a8ff; margin-top:5px;'>{int(round(row.iloc[4]))}d</p>", unsafe_allow_html=True)
                r6.markdown(f"<p style='text-align:center; margin-top:12px;'>{p_mono}%</p>", unsafe_allow_html=True)
                r7.markdown(f"<p style='text-align:center; margin-top:12px;'>{100-p_mono}%</p>", unsafe_allow_html=True)
                with r8:
                    if st.button("VER", key=f"g_ind_{m_idx}"): mostrar_detalle(df_m, nombres_meses[m_idx], 25)
                st.markdown("<hr style='margin:0; opacity:0.1;'>", unsafe_allow_html=True)

            # --- SECCIÓN 2: MONOPROVEEDOR (VERDE - SLA DINÁMICO) ---
            # --- 4. SECCIÓN 2: MONOPROVEEDOR (VERDE - SLA DINÁMICO) ---
            st.markdown("<br><br><p style='color:#00ff88; font-weight:700; letter-spacing:4px; font-size:22px; text-align:center;'>INDICADORES MONOPROVEEDOR 2026</p>", unsafe_allow_html=True)
            df_mono = df_ind[df_ind.iloc[:, 24].astype(str).str.upper().str.contains("SI|MONOPROVEEDOR", na=False)].copy()
            m1, m2, m3, m4, m5, m6 = st.columns([1, 1, 1, 1, 1.5, 0.4])
            
            m1, m2, m3, m4, m5, m6 = st.columns([1, 1, 1, 1, 1.5, 0.5])
            for i, col in enumerate([m1, m2, m3, m4, m5, m6]):
                col.markdown(f"<p style='color:#8899A6; font-size:10px; font-weight:700; text-align:center;'>{['MES', 'EMBARQUES', 'META SLA', 'PROM. MES', 'ESTADO SLA', 'INFO'][i]}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border-top: 2px solid #00ff88;'>", unsafe_allow_html=True)

            res_mono = df_mono.groupby('Mes_Num').agg({df_mono.columns[0]:'count', df_mono.columns[32]:'mean'}).reset_index()
            for _, row in res_mono.iterrows():
                m_idx = int(row['Mes_Num']); df_m_mono = df_mono[df_mono['Mes_Num'] == m_idx]
                meta_act = 15 if m_idx <= 2 else 7
                cumple = row.iloc[2] <= meta_act; c_st = "#00ff88" if cumple else "#ff4b4b"
                r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 1.5, 0.4])
                
                r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 1.5, 0.5])
                r1.markdown(f"<p style='text-align:center; font-weight:700; margin-top:12px;'>{nombres_meses.get(m_idx)}</p>", unsafe_allow_html=True)
                r2.markdown(f"<p style='text-align:center; margin-top:12px;'>{int(row.iloc[1])}</p>", unsafe_allow_html=True)
                r3.markdown(f"<p style='text-align:center; margin-top:12px; color:#8899A6;'>{meta_act} días</p>", unsafe_allow_html=True)
                r4.markdown(f"<p class='kpi-highlight' style='text-align:center; color:{c_st}; margin-top:5px;'>{int(round(row.iloc[2]))}d</p>", unsafe_allow_html=True)
                r5.markdown(f"<div class='sla-badge' style='background:{c_st}22; color:{c_st}; border:1px solid {c_st}44;'>{'OK' if cumple else 'FAIL'}</div>", unsafe_allow_html=True)
                status_html = f"background: {c_st}22; color: {c_st}; border: 1px solid {c_st}44;"
                r5.markdown(f"<div class='sla-status' style='{status_html}'>{'ALCANZADO' if cumple else 'EXCEDIDO'}</div>", unsafe_allow_html=True)
                with r6:
                    if st.button("VER", key=f"m_ind_{m_idx}"): mostrar_detalle(df_m_mono, nombres_meses[m_idx], meta_act)
                    if st.button("VER", key=f"mon_{m_idx}"): mostrar_detalle(df_m_mono, nombres_meses[m_idx], meta_act)
                st.markdown("<hr style='margin:0; opacity:0.1;'>", unsafe_allow_html=True)

            # --- SECCIÓN 3: CONSOLIDADOS (NARANJA - SLA 25d) ---
            # --- 5. SECCIÓN 3: CONSOLIDADOS (NARANJA - SLA 25d) ---
            st.markdown("<br><br><p style='color:#ffaa00; font-weight:700; letter-spacing:4px; font-size:22px; text-align:center;'>INDICADORES CONSOLIDADOS 2026</p>", unsafe_allow_html=True)
            df_cons = df_ind[~df_ind.iloc[:, 24].astype(str).str.upper().str.contains("SI|MONOPROVEEDOR", na=False)].copy()
            c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.5, 0.4])
            
            c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1.5, 0.5])
            for i, col in enumerate([c1, c2, c3, c4, c5, c6]):
                col.markdown(f"<p style='color:#8899A6; font-size:10px; font-weight:700; text-align:center;'>{['MES', 'EMBARQUES', 'META SLA', 'PROM. MES', 'ESTADO SLA', 'INFO'][i]}</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0; border-top: 2px solid #ffaa00;'>", unsafe_allow_html=True)

            res_cons = df_cons.groupby('Mes_Num').agg({df_cons.columns[0]:'count', df_cons.columns[32]:'mean'}).reset_index()
            for _, row in res_cons.iterrows():
                m_idx = int(row['Mes_Num']); df_m_cons = df_cons[df_cons['Mes_Num'] == m_idx]
                meta_c = 25; cumple_c = row.iloc[2] <= meta_c; c_st_c = "#00ff88" if cumple_c else "#ff4b4b"
                r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 1.5, 0.4])
                
                r1, r2, r3, r4, r5, r6 = st.columns([1, 1, 1, 1, 1.5, 0.5])
                r1.markdown(f"<p style='text-align:center; font-weight:700; margin-top:12px;'>{nombres_meses.get(m_idx)}</p>", unsafe_allow_html=True)
                r2.markdown(f"<p style='text-align:center; margin-top:12px;'>{int(row.iloc[1])}</p>", unsafe_allow_html=True)
                r3.markdown(f"<p style='text-align:center; margin-top:12px; color:#8899A6;'>25 días</p>", unsafe_allow_html=True)
                r4.markdown(f"<p class='kpi-highlight' style='text-align:center; color:#ffaa00; margin-top:5px;'>{int(round(row.iloc[2]))}d</p>", unsafe_allow_html=True)
                r5.markdown(f"<div class='sla-badge' style='background:{c_st_c}22; color:{c_st_c}; border:1px solid {c_st_c}44;'>{'OK' if cumple_c else 'FAIL'}</div>", unsafe_allow_html=True)
                status_html_c = f"background: {c_st_c}22; color: {c_st_c}; border: 1px solid {c_st_c}44;"
                r5.markdown(f"<div class='sla-status' style='{status_html_c}'>{'ALCANZADO' if cumple_c else 'EXCEDIDO'}</div>", unsafe_allow_html=True)
                with r6:
                    if st.button("VER", key=f"c_ind_{m_idx}"): mostrar_detalle(df_m_cons, nombres_meses[m_idx], meta_c)
                    if st.button("VER", key=f"con_{m_idx}"): mostrar_detalle(df_m_cons, nombres_meses[m_idx], meta_c)
                st.markdown("<hr style='margin:0; opacity:0.1;'>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Indicadores: {e}")
except Exception as e:
    st.error(f"Error crítico: {e}")

# ==========================================
# SOLAPA 4: PERFORMANCE AGENTES (UNITARIO)
# ==========================================
    with tabs[3]:
        st.markdown("<h3 style='text-align:center; color:#00a8ff;'>MONITOR DE GESTIÓN POR AGENTE</h3>", unsafe_allow_html=True)
        try:
            # 1. CARGA INDEPENDIENTE
            u_ag = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=276804813"
            df_ag_raw = pd.read_csv(u_ag, engine='python')
            df_ag_raw.columns = [str(c).strip() for c in df_ag_raw.columns]

            # 2. DEFINICIÓN DE COLUMNAS SEGÚN TU EXCEL
            # Col H (7) = Instrucción | Col F (5) = Transporte | Col G (6) = Forwarder 
            # Col Y (24) = M3 | Col K (10) = Status | Col L (11) = ETD
            
            # Filtro: Solo lo que tiene fecha en Columna H (Instrucción)
            df_ag_raw['DT_Inst'] = pd.to_datetime(df_ag_raw.iloc[:, 7], dayfirst=True, errors='coerce')
            df_a = df_ag_raw[df_ag_raw['DT_Inst'].notna()].copy()

            if df_a.empty:
                st.warning("No se encontraron fechas de instrucción en la columna H de la hoja Reservas.")
            else:
                # 3. FILTRO TRANSPORTE
                df_a['Tipo_T'] = df_a.iloc[:, 5].apply(lambda x: "MARITIMO" if any(m in str(x).upper() for m in ["40", "20", "MARITIMO"]) else "AVION / COURIER")
                t_sel = st.radio("Filtrar por medio:", ["MARITIMO", "AVION / COURIER"], horizontal=True, key="ag_radio_fixed")
                
                df_f = df_a[df_a['Tipo_T'] == t_sel].copy()

                # 4. CÁLCULOS
                hoy_f = pd.Timestamp("2026-04-02")
                df_f['DT_ETD'] = pd.to_datetime(df_f.iloc[:, 11], dayfirst=True, errors='coerce')
                df_f['Status_K'] = df_f.iloc[:, 10].astype(str).str.upper().str.strip()

                df_f['Gestion'] = (df_f['DT_ETD'] - df_f['DT_Inst']).dt.days
                df_f['Espera'] = (hoy_f - df_f['DT_Inst']).dt.days

                # 5. AGRUPACIÓN
                col_ffww = df_f.columns[6]
                res_ag = df_f.groupby(col_ffww).agg(
                    SO=(df_f.columns[0], 'count'),
                    M3=(df_f.columns[24], lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.'), errors='coerce').sum()),
                    Confirmados=('Status_K', lambda x: (x == "OK").sum()),
                    Prom_Gest=('Gestion', 'mean'),
                    Prom_Esp=('Espera', lambda x: x[df_f.loc[x.index, 'Status_K'] != "OK"].mean())
                ).reset_index()

                res_ag['%_OK'] = (res_ag['Confirmados'] / res_ag['SO'] * 100).fillna(0)
                res_ag = res_ag.sort_values('SO', ascending=False)

                # 6. TABLA
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(
                    res_ag,
                    column_config={
                        col_ffww: "Forwarder",
                        "SO": "Cant. SO",
                        "M3": st.column_config.NumberColumn("M3 Total", format="%.1f"),
                        "Prom_Gest": st.column_config.NumberColumn("Gestión (Días)", format="%d"),
                        "Prom_Esp": st.column_config.NumberColumn("Espera (Días)", format="%d"),
                        "%_OK": st.column_config.ProgressColumn("Efectividad %", min_value=0, max_value=100, format="%d%%")
                    },
                    use_container_width=True, hide_index=True
                )

        except Exception as e:
            st.error(f"Error en Solapa Agentes: {e}")

# --- SOLAPAS RESTANTES VACÍAS PARA EVITAR ERRORES ---
    with tabs[4]: st.info("Módulo Analistas en desarrollo.")
    with tabs[5]: st.info("Módulo Fletes en desarrollo.")

except Exception as e:
    st.error(f"Error crítico en el Tablero: {e}")
