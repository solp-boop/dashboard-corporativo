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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* RESET & BASE */
html, body, [class*="css"] { font-family: 'Inter', 'DM Sans', -apple-system, sans-serif !important; }
.block-container { padding: 1.5rem 3rem 3rem 3rem !important; }
.main { background-color: #070c18; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 32px; background: transparent;
    justify-content: center !important; overflow-x: auto;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important; border-radius: 0 !important;
    padding: 10px 18px !important; color: #475569 !important;
    font-size: 11px !important; font-weight: 500 !important;
    letter-spacing: 0.8px !important; text-transform: uppercase;
    transition: all 0.2s ease; white-space: nowrap;
}
.stTabs [data-baseweb="tab"]:hover { color: #94a3b8 !important; }
.stTabs [aria-selected="true"] {
    background: transparent !important; border-bottom: 2px solid #3b82f6 !important;
    color: #f1f5f9 !important; box-shadow: none !important;
}

/* BOTONES */
div[data-testid="stColumn"] div[data-testid="stButton"] button {
    height: 28px !important; min-height: 28px !important;
    padding: 0px 10px !important; font-size: 11px !important; border-radius: 5px !important;
}
.stButton > button {
    border-radius: 8px !important; color: #94a3b8 !important; width: 100%;
    height: auto !important; min-height: 48px !important; font-weight: 500 !important;
    font-size: 12px !important; background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important; transition: all 0.15s ease !important;
    padding: 10px 16px !important; letter-spacing: 0.3px;
}
.stButton > button:hover {
    background: rgba(59,130,246,0.08) !important; border-color: rgba(59,130,246,0.3) !important;
    color: #e2e8f0 !important; transform: none !important; box-shadow: none !important;
}

/* KPI CARD */
.kpi-card {
    background: #0d1424; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 20px 24px; position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,0.35), transparent);
}
.kpi-label {
    font-size: 10px; font-weight: 600; color: #475569;
    letter-spacing: 1.2px; text-transform: uppercase; margin: 0 0 10px 0;
}
.kpi-value {
    font-size: 36px; font-weight: 700; color: #f1f5f9;
    line-height: 1; margin: 0; letter-spacing: -0.5px; font-variant-numeric: tabular-nums;
}
.kpi-sub { font-size: 11px; color: #334155; margin: 6px 0 0 0; font-weight: 400; }
.kpi-delta-up { font-size: 11px; color: #22c55e; font-weight: 500; margin: 6px 0 0 0; }
.kpi-delta-down { font-size: 11px; color: #ef4444; font-weight: 500; margin: 6px 0 0 0; }

/* SECTION CARD */
.section-card {
    background: #0d1424; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 24px; margin-bottom: 20px;
}
.section-title {
    font-size: 10px; font-weight: 600; color: #334155; letter-spacing: 1.5px;
    text-transform: uppercase; margin: 0 0 18px 0;
    padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* BADGES */
.badge-green {
    display: inline-block; background: rgba(34,197,94,0.08); color: #22c55e;
    border: 1px solid rgba(34,197,94,0.2); border-radius: 4px; padding: 2px 8px;
    font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-yellow {
    display: inline-block; background: rgba(245,158,11,0.08); color: #f59e0b;
    border: 1px solid rgba(245,158,11,0.2); border-radius: 4px; padding: 2px 8px;
    font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-red {
    display: inline-block; background: rgba(239,68,68,0.08); color: #ef4444;
    border: 1px solid rgba(239,68,68,0.2); border-radius: 4px; padding: 2px 8px;
    font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-blue {
    display: inline-block; background: rgba(59,130,246,0.08); color: #3b82f6;
    border: 1px solid rgba(59,130,246,0.2); border-radius: 4px; padding: 2px 8px;
    font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
}

/* METRIC CONTAINER (legacy) */
.metric-container {
    text-align: center; padding: 20px 16px; background: #0d1424;
    border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);
    position: relative; overflow: hidden;
}
.metric-container::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,0.25), transparent);
}
.metric-container p:first-child {
    font-size: 10px !important; color: #475569 !important; letter-spacing: 1.2px !important;
    font-weight: 600 !important; margin-bottom: 10px !important; text-transform: uppercase;
}
.metric-container p:last-child {
    font-size: 38px !important; font-weight: 700 !important; color: #f1f5f9 !important;
    line-height: 1 !important; margin: 0 !important; letter-spacing: -0.5px !important;
    text-shadow: none !important;
}

/* CUSTOM CARD (legacy) */
.custom-card {
    background: #0d1424; padding: 24px; border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;
}
.custom-card-title {
    font-weight: 600; font-size: 10px; letter-spacing: 1.5px;
    margin-bottom: 16px; margin-top: 0; text-transform: uppercase; color: #475569;
}
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 16px; }
.minicard-title {
    font-size: 10px; color: #475569; letter-spacing: 1px;
    margin: 0 0 4px 0; font-weight: 500; text-transform: uppercase;
}
.minicard-value { font-size: 22px; font-weight: 600; margin: 0; color: #e2e8f0; }

/* DIVIDERS */
.glow-divider { border: none; height: 1px; background: rgba(255,255,255,0.05); margin: 28px 0; }
.white-divider { border: none; height: 1px; background: rgba(255,255,255,0.04); margin: 20px 0; }
hr { margin: 1rem 0 !important; opacity: 0.06; }
</style>
""", unsafe_allow_html=True)
try:
    # --- 3. CARGA DE DATOS ---
    base_url = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI"
    @st.cache_data(ttl=60)
    def load_main_data(url):
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    df = load_main_data(f"{base_url}/export?format=csv&gid=0&nocache={time.time()}")
    if 'M3 Total' in df.columns:
        df['M3 Total'] = df['M3 Total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['M3 Total'] = pd.to_numeric(df['M3 Total'], errors='coerce').fillna(0)
    if 'Fob total Origen' in df.columns:
        def clean_val(x):
            if isinstance(x, (int, float)): return x
            x = str(x).replace('USD', '').replace('$', '').replace(' ', '')
            num = ''.join(c for c in x if c.isdigit() or c in '.,')
            if ',' in num and '.' in num:
                num = num.replace('.', '').replace(',', '.')
            elif ',' in num:
                num = num.replace(',', '.')
            return pd.to_numeric(num, errors='coerce')
        df['Fob total Origen'] = df['Fob total Origen'].apply(clean_val).fillna(0)
    df.iloc[:, 23] = df.iloc[:, 23].astype(str).str.strip()
    df.iloc[:, 24] = df.iloc[:, 24].astype(str).str.strip()
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], dayfirst=True, errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], dayfirst=True, errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], dayfirst=True, errors='coerce')
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
    df = df[df['SO'].notna() & (df['SO'].astype(str).str.strip() != "") & (df['SO'].astype(str).str.strip().str.lower() != "nan")]
    m3_totales_global = round(df['M3 Total'].sum())
    cant_so_global = df['SO'].nunique()
    cant_proveedores_global = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0
    # ─────────────────────────────────────────────────────────────────────────────
    # --- POP-UP ALERTA DE MERCADO (aparece una vez por sesión al ingresar) ---
    # ─────────────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────────
    # --- HEADER BIDCOM ---
    # ─────────────────────────────────────────────────────────────────────────────
    _fecha_hdr = hoy.strftime('%d %b %Y').upper()
    st.markdown(f"""
<div style='
    background: linear-gradient(135deg, rgba(0,20,50,0.85) 0%, rgba(0,35,80,0.9) 100%);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 16px;
    padding: 40px 60px;
    text-align: center;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
'>
<div style='
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,0.5), transparent);
'></div>
<h1 style='
    font-size: 64px;
    font-weight: 700;
    letter-spacing: 16px;
    margin: 0 0 12px 0;
    color: #f1f5f9;
    font-family: Inter, sans-serif;
'>BIDCOM</h1>
<p style='
    font-size: 13px;
    color: #3b82f6;
    letter-spacing: 6px;
    text-transform: uppercase;
    font-weight: 500;
    margin: 0 0 16px 0;
'>Tablero Logística Internacional</p>
<div style='
    width: 40px; height: 1px;
    background: rgba(59,130,246,0.3);
    margin: 0 auto 12px auto;
'></div>
<p style='font-size: 11px; color: #334155; margin: 0; font-weight: 400;'>{_fecha_hdr}</p>
</div>""", unsafe_allow_html=True)
    # ─────────────────────────────────────────────────────────────────────────────
    # --- BANNER ALERTA MERCADO (colapsable, siempre visible debajo del header) ---
    # ─────────────────────────────────────────────────────────────────────────────
    with st.expander("📡  PANORAMA DE MERCADO  ·  Actualizando datos...", expanded=False):
        st.markdown("""
<div style='padding:20px; background:rgba(255,255,255,0.02); border-radius:10px;
border:1px solid rgba(255,255,255,0.05); text-align:center;'>
<p style='color:#334155; font-size:13px; margin:0 0 6px 0;'>🔄 Actualizando información de mercado</p>
<p style='color:#1e293b; font-size:11px; margin:0;'>Los datos del panorama de mercado se actualizarán próximamente.</p>
</div>""", unsafe_allow_html=True)
    col_ref, _ = st.columns([1, 8])
    with col_ref:
        if st.button("↻ Actualizar", key="btn_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    tabs = st.tabs(["ORIGEN", "MERCADERÍA EN PROCESO", "PERFORMANCE ANALISTAS", "PERFORMANCE AGENTES", "FLETES & GASTOS", "PROYECCIÓN SEMANAL ETD", "INDICADORES", "ASK COMEX"])
    # --- SOLAPA 1: ORIGEN ---
    with tabs[0]:
        try:
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], dayfirst=True, errors='coerce')
            col_rank = df.columns[1]
            df['Rank_Num'] = df[col_rank].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Rank_Num'] = pd.to_numeric(df['Rank_Num'], errors='coerce').fillna(999999)
            col_cp = df.columns[94]  # CQ = ¿ES MONOPROVEEDOR?
            df['Tipo_Carga'] = df[col_cp].apply(lambda x: 'MONOPROVEEDOR' if str(x).strip().upper() in ['SI', 'SÍ', 'MONOPROVEEDOR'] else 'CONSOLIDADO')
            def get_tipo_repuesto(val):
                val_str = str(val).strip().lower()
                if val_str in ['', 'nan', 'none'] or pd.isna(val) or val_str == 'nan': return "Gadnic"
                if "muestra" in val_str: return "Muestras"
                if "sin planeamiento" in val_str: return "Marcas"
                return "Gadnic"
            df['Tipo_Repuesto'] = df['Repuestos'].apply(get_tipo_repuesto) if 'Repuestos' in df.columns else 'Gadnic'
            df['Pais Destino'] = df['Pais Destino'].fillna('SIN DEFINIR').astype(str).str.strip()
            df['Repuestos'] = df['Repuestos'].fillna('').astype(str).str.strip()
            cond_prioridad = (df['Pais Destino'].str.upper() == 'ARGENTINA') & (df['Tipo_Repuesto'] == 'Gadnic')
            cond_instruido = df['Fecha_Inst_DT'].notna() & ~(df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=False))
            cond_pendiente = ~cond_instruido
            cond_urgente = cond_pendiente & (df['Fecha_Prior_DT'] < hoy)
            cond_pd_futura = cond_pendiente & (df['Fecha_Prior_DT'] >= hoy)
            cond_acc_mono = cond_pd_futura & (df['Tipo_Carga'] == 'MONOPROVEEDOR') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=25))
            cond_acc_consol = cond_pd_futura & (df['Tipo_Carga'] == 'CONSOLIDADO') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=10))
            cond_accionar = cond_acc_mono | cond_acc_consol
            cond_futura = cond_pendiente & (~cond_urgente) & (~cond_accionar)
            df_inst = df[cond_instruido & cond_prioridad].sort_values(by='Rank_Num').copy()
            # Vencidos CON prioridad: Argentina + Gadnic + NO es DJI ni IFLIGHT
            cond_prov_no_prior = (
                df['Proveedor'].astype(str).str.upper().str.contains('DJI', na=False) |
                (df['Proveedor'].astype(str).str.strip().str.upper() == 'IFLIGHT TECHNOLOGY CO LTD')
            )
            cond_venc_prior = (
                cond_urgente &
                (df['Pais Destino'].str.upper() == 'ARGENTINA') &
                (df['Tipo_Repuesto'] == 'Gadnic') &
                ~cond_prov_no_prior
            )
            # Vencidos SIN prioridad: resto (otros países, repuestos, muestras, DJI, IFLIGHT, etc.)
            cond_venc_sinprior = cond_urgente & ~cond_venc_prior
            df_urgente_prior = df[cond_venc_prior].sort_values(by='Rank_Num').copy()
            df_urgente_sinprior = df[cond_venc_sinprior].sort_values(by=['Fecha_Prior_DT', 'Rank_Num']).copy()
            df_urgente = df_urgente_prior  # compatibilidad con m3_urgente abajo
            df_accionar = df[cond_accionar & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_futura = df[cond_futura & cond_prioridad].sort_values(by='Rank_Num').copy()
            m3_inst = df_inst['M3 Total'].sum()
            m3_urgente = df_urgente_prior['M3 Total'].sum() + df_urgente_sinprior['M3 Total'].sum()
            m3_accionar = df_accionar['M3 Total'].sum()
            m3_futura = df_futura['M3 Total'].sum()
            m3_pend_total = m3_urgente + m3_accionar + m3_futura
            p_inst_val = int(round(m3_inst / m3_totales_global * 100)) if m3_totales_global > 0 else 0
            p_pend_val = 100 - p_inst_val
            fob_total_global = df['Fob total Origen'].sum()
            st.markdown("<br>", unsafe_allow_html=True)
            o1, o2, o3, o4 = st.columns(4)
            with o1: st.markdown(f"<div class='metric-container'><p>CANTIDAD DE SO</p><p>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
            with o2: st.markdown(f"<div class='metric-container'><p>VOLUMEN TOTAL (M3)</p><p>{int(round(m3_totales_global)):,}</p></div>", unsafe_allow_html=True)
            with o3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)
            with o4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL (USD)</p><p>${int(round(fob_total_global)):,}</p></div>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin-bottom: 30px;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL DE STATUS DE MERCADERÍA</h2></div>", unsafe_allow_html=True)
            s1, _ = st.columns([1, 0.001])
            s2 = _
            filtro_actual = st.session_state.get('f')
            with s1:
                st.markdown(f"""
                    <div class="custom-card" style="border-top: 5px solid #00ff88; background: rgba(0,255,136,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                            <p class="custom-card-title" style="color:#00ff88; font-size:18px;">MERCADERÍA INSTRUIDA (LOGRADO)</p>
                            <p style="color:#00ff88; font-weight:900; font-size:32px; margin:0;">{p_inst_val}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">M3</span></p>
                        </div>
                        <div class="grid-2">
                            <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value" style="color:#00ff88;">{df_inst['SO'].nunique()}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{int(round(m3_inst)):,} M3</p></div>
                        </div>
                        <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:20px 0;">
                        <div class="grid-2">
                            <div>
                                <p class="minicard-title" style="color:#00a8ff;">ESTRUCTURA DE CARGA</p>
                                <p style="font-size:12px; margin:5px 0;">MONOPROVEEDOR: <b>{df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['SO'].nunique()} SO</b> ({int(round(df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['M3 Total'].sum()))} m3)</p>
                                <p style="font-size:12px; margin:5px 0;">CONSOLIDADOS: <b>{df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['SO'].nunique()} SO</b> ({int(round(df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['M3 Total'].sum()))} m3)</p>
                            </div>
                            <div>
                                <p class="minicard-title" style="color:#ffaa00;">TIPO DE INGRESO</p>
                                <p style="font-size:12px; margin:5px 0;">GADNIC: <b>{df_inst[df_inst['Tipo_Repuesto']=='Gadnic']['SO'].nunique()} SO</b></p>
                                <p style="font-size:12px; margin:5px 0;">MUESTRAS: <b>{df_inst[df_inst['Tipo_Repuesto']=='Muestras']['SO'].nunique()} SO</b></p>
                            </div>
                        </div>
                """, unsafe_allow_html=True)
                if st.button("VER DETALLE INSTRUIDO", key="btn_inst_new", use_container_width=True):
                    st.session_state.f = 'inst' if filtro_actual != 'inst' else None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with s2:
                df_pend_view = df[cond_pendiente]
                st.markdown(f"""
                    <div class="custom-card" style="border-top: 5px solid #94a3b8;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
                            <p class="custom-card-title" style="color:#f8fafc; font-size:18px;">MERCADERÍA PENDIENTE</p>
                            <p style="color:#f8fafc; font-weight:900; font-size:32px; margin:0;">{p_pend_val}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">M3</span></p>
                        </div>
                        <div class="grid-2" style="margin-bottom:20px;">
                            <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value">{df_pend_view['SO'].nunique()}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{int(round(m3_pend_total)):,} M3</p></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔴 NIVEL 1A: VENCIDA PRIORITARIA (ARG·GADNIC) - {int(round(df_urgente_prior['M3 Total'].sum()))} M3", key="btn_urg_new", use_container_width=True):
                    st.session_state.f = 'venc' if filtro_actual != 'venc' else None
                    st.rerun()
                if st.button(f"🟥 NIVEL 1B: VENCIDA SIN PRIORIDAD - {int(round(df_urgente_sinprior['M3 Total'].sum()))} M3", key="btn_urg_sp_new", use_container_width=True):
                    st.session_state.f = 'venc_sp' if filtro_actual != 'venc_sp' else None
                    st.rerun()
                if st.button(f"🟠 NIVEL 2: ACCIONAR (PRÓXIMA) - {int(round(df_accionar['M3 Total'].sum()))} M3", key="btn_acc_new", use_container_width=True):
                    st.session_state.f = 'px25' if filtro_actual != 'px25' else None
                    st.rerun()
                if st.button(f"🔵 NIVEL 3: PROGRAMADA (FUTURA) - {int(round(df_futura['M3 Total'].sum()))} M3", key="btn_rest_new", use_container_width=True):
                    st.session_state.f = 'rest' if filtro_actual != 'rest' else None
                    st.rerun()

            f = st.session_state.get('f')
            if f:
                st.markdown("<br>", unsafe_allow_html=True)
                if f in ["venc", "venc_sp", "px25", "rest"]:
                    if f == "inst": titulo, dff, color = "MERCADERIA INSTRUIDA (PRIORIDAD)", df_inst, "#00ff88"
                    elif f == "venc": titulo, dff, color = "VENCIDA CON PRIORIDAD (ARG · SIN REPUESTO)", df_urgente_prior, "#ff4b4b"
                    elif f == "venc_sp": titulo, dff, color = "VENCIDA SIN PRIORIDAD", df_urgente_sinprior, "#ff8c42"
                    elif f == "px25": titulo, dff, color = "PROXIMA A INSTRUIR (ACCIÓN)", df_accionar, "#ffaa00"
                    elif f == "rest": titulo, dff, color = "MERCADERIA PROGRAMADA (FUTURA)", df_futura, "#94a3b8"
                    cant_so_f = dff['SO'].nunique()
                    m3_f = int(round(dff['M3 Total'].sum()))
                    st.markdown(f"""
                            <div class="custom-card" style="border-left: 5px solid {color};">
                                <p class="custom-card-title" style="color:{color};">{titulo} ({int(round(m3_f/m3_totales_global*100)) if m3_totales_global > 0 else 0}%)</p>
                                <div class="grid-2">
                                    <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value">{cant_so_f}</p></div>
                                    <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{m3_f:,} M3</p></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    col_puerto = df.columns[41]
                    cols_to_show = ['SO', col_rank, 'Proveedor', col_puerto, 'Pais Destino', 'M3 Total', df.columns[99], 'Fecha de Instruccion']
                    if 'Repuestos' in df.columns:
                        cols_to_show.insert(4, 'Repuestos')
                    st.dataframe(dff[cols_to_show], use_container_width=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:18px; margin-bottom:25px; text-align:center;'>DISTRIBUCIÓN GEOGRÁFICA</p>", unsafe_allow_html=True)
            res_p = df.groupby('Pais Destino').agg({'SO': 'nunique', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT_SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
            total_so_p = res_p['CANT_SO'].sum()
            total_m3_p = res_p['M3'].sum()
            hp1, hp2, hp3, hp4 = st.columns([1.5, 1, 1, 0.8])
            hp1.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700;'>DESTINO</p>", unsafe_allow_html=True)
            hp2.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:center;'>VOLUMEN (M3)</p>", unsafe_allow_html=True)
            hp3.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:center;'>CANTIDAD SO</p>", unsafe_allow_html=True)
            hp4.markdown("<p style='color:#94a3b8; font-size:12px; letter-spacing:1px; font-weight:700; text-align:right;'>SHARE %</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0 0 10px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
            for pais, row in res_p.iterrows():
                m3_v = int(round(row['M3']))
                so_v = int(row['CANT_SO'])
                pct_v = int(round((m3_v / total_m3_p * 100))) if total_m3_p > 0 else 0
                color_texto = "#ffffff" if pais != "SIN DEFINIR" else "#64748b"
                cp1, cp2, cp3, cp4 = st.columns([1.5, 1, 1, 0.8])
                cp1.markdown(f"<p style='color:{color_texto}; font-weight:600; font-size:16px; margin:8px 0;'>{pais.upper()}</p>", unsafe_allow_html=True)
                cp2.markdown(f"<p style='color:#00a8ff; font-weight:400; font-size:20px; text-align:center; margin:8px 0;'>{m3_v:,}</p>", unsafe_allow_html=True)
                cp3.markdown(f"<p style='color:{color_texto}; font-weight:400; font-size:20px; text-align:center; margin:8px 0;'>{so_v}</p>", unsafe_allow_html=True)
                cp4.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:18px; text-align:right; margin:8px 0;'>{pct_v}%</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:15px 0; border: none; border-top: 1px solid rgba(255,255,255,0.4);'>", unsafe_allow_html=True)
            tp1, tp2, tp3, tp4 = st.columns([1.5, 1, 1, 0.8])
            tp1.markdown("<p style='color:#f8fafc; font-weight:800; font-size:18px;'>TOTAL GENERAL</p>", unsafe_allow_html=True)
            tp2.markdown(f"<p style='color:#00a8ff; font-weight:800; font-size:22px; text-align:center;'>{int(round(total_m3_p)):,}</p>", unsafe_allow_html=True)
            tp3.markdown(f"<p style='color:#f8fafc; font-weight:800; font-size:22px; text-align:center;'>{int(total_so_p)}</p>", unsafe_allow_html=True)
            tp4.markdown("<p style='color:#00ff88; font-weight:900; font-size:20px; text-align:right;'>100%</p>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            col_puerto = df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            total_m3_puertos = p_df['M3 Total'].sum()
            p_df['Pct'] = (p_df['M3 Total'] / total_m3_puertos * 100).round(1) if total_m3_puertos > 0 else 0
            p_df['label'] = p_df.apply(lambda r: f"{int(round(r['M3 Total'])):,} M3  ({r['Pct']}%)", axis=1)
            st.markdown(f"<p style='color:#00a8ff; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:20px;'>VOLUMEN POR PUERTO DE SALIDA <span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>| TOTAL: {int(round(total_m3_puertos)):,} M3</span></p>", unsafe_allow_html=True)
            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text='label', color_discrete_sequence=['#00a8ff'])
            fig_p.update_traces(textposition='outside', cliponaxis=False, textfont_size=14, textfont_color="#f8fafc", marker=dict(cornerradius=5))
            fig_p.update_layout(xaxis_visible=True, xaxis_title="Total M3", yaxis_title="Puerto", height=500, margin=dict(l=150, r=160, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_p.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig_p, use_container_width=True)
            ga, gb = st.columns(2)
            with ga:
                etd_all = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                etd_vencido = etd_all[etd_all['Mes_ETD_Full'] == 'PASADO/REALIZADO']
                etd_p = etd_all[~etd_all['Mes_ETD_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                if not etd_vencido.empty and etd_vencido['M3 Total'].sum() > 0:
                    m3_venc_etd = int(round(etd_vencido['M3 Total'].sum()))
                    st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>⚠️ VENCIDO/REALIZADO: {m3_venc_etd:,} M3 en meses anteriores (no se muestran en el gráfico)</p></div>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETD<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(round(etd_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'])
                fig_e.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                fig_e.update_layout(yaxis_visible=True, yaxis_title="Total M3", xaxis_title="Mes ETD", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_e.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_e, use_container_width=True)
            with gb:
                eta_all = df.groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                eta_vencido = eta_all[eta_all['Mes_ETA_Full'] == 'PASADO/REALIZADO']
                eta_p = eta_all[~eta_all['Mes_ETA_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                if not eta_vencido.empty and eta_vencido['M3 Total'].sum() > 0:
                    m3_venc_eta = int(round(eta_vencido['M3 Total'].sum()))
                    st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>⚠️ VENCIDO/REALIZADO: {m3_venc_eta:,} M3 en meses anteriores (no se muestran en el gráfico)</p></div>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#ff4b4b; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETA<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(round(eta_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'])
                fig_a.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                fig_a.update_layout(yaxis_visible=True, yaxis_title="Total M3", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                fig_a.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                st.plotly_chart(fig_a, use_container_width=True)
            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
            gc, gd = st.columns(2)
            with gc:
                col_mod_opciones = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
                col_mod = col_mod_opciones[0] if col_mod_opciones else 'Modalidad de Costeo Reposicion'
                if col_mod in df.columns:
                    mask_arg   = df['Pais Destino'].astype(str).str.strip().str.upper() == 'ARGENTINA'
                    mask_barco = (
                        df[col_mod].astype(str).str.upper().str.startswith("BARCO") |
                        df[col_mod].astype(str).str.upper().str.contains("COSTO HIBRIDO PUERTO ZFLP", na=False)
                    )
                    mask_cntr = mask_arg & mask_barco
                    df_c_etd_all = df[mask_cntr].groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                    df_c_etd_venc = df_c_etd_all[df_c_etd_all['Mes_ETD_Full'] == 'PASADO/REALIZADO']
                    df_c_etd = df_c_etd_all[~df_c_etd_all['Mes_ETD_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                    df_c_etd['Contenedores'] = (df_c_etd['M3 Total'] / 60).round().astype(int)
                    tot_cont_etd = df_c_etd['Contenedores'].sum()
                    if not df_c_etd_venc.empty and df_c_etd_venc['M3 Total'].sum() > 0:
                        cont_venc_etd = int(round(df_c_etd_venc['M3 Total'].sum() / 60))
                        st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>⚠️ VENCIDO: ~{cont_venc_etd} CNTR en meses anteriores (no se muestran)</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETD)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(tot_cont_etd):,} CNTR</span></p>", unsafe_allow_html=True)
                    fig_cetd = px.bar(df_c_etd, x='Mes_ETD_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_cetd.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_cetd.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETD", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_cetd.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_cetd, use_container_width=True)
                else:
                    st.warning(f"La columna requerida '{col_mod}' no se encuentra para calcular la proyección.")
            with gd:
                if col_mod in df.columns:
                    mask_arg   = df['Pais Destino'].astype(str).str.strip().str.upper() == 'ARGENTINA'
                    mask_barco = (
                        df[col_mod].astype(str).str.upper().str.startswith("BARCO") |
                        df[col_mod].astype(str).str.upper().str.contains("COSTO HIBRIDO PUERTO ZFLP", na=False)
                    )
                    mask_cntr = mask_arg & mask_barco
                    df_c_eta_all = df[mask_cntr].groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                    df_c_eta_venc = df_c_eta_all[df_c_eta_all['Mes_ETA_Full'] == 'PASADO/REALIZADO']
                    df_c_eta = df_c_eta_all[~df_c_eta_all['Mes_ETA_Full'].isin(['PASADO/REALIZADO', 'SIN FECHA'])]
                    df_c_eta['Contenedores'] = (df_c_eta['M3 Total'] / 60).round().astype(int)
                    tot_cont_eta = df_c_eta['Contenedores'].sum()
                    if not df_c_eta_venc.empty and df_c_eta_venc['M3 Total'].sum() > 0:
                        cont_venc_eta = int(round(df_c_eta_venc['M3 Total'].sum() / 60))
                        st.markdown(f"<div style='background:rgba(255,75,75,0.08); border-radius:8px; padding:8px 14px; border-left:3px solid #ff4b4b; margin-bottom:10px;'><p style='color:#ff4b4b; font-size:12px; font-weight:700; margin:0;'>⚠️ VENCIDO: ~{cont_venc_eta} CNTR en meses anteriores (no se muestran)</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETA)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL FUTURO: {int(tot_cont_eta):,} CNTR</span></p>", unsafe_allow_html=True)
                    fig_ceta = px.bar(df_c_eta, x='Mes_ETA_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_ceta.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_ceta.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_ceta.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_ceta, use_container_width=True)
        except Exception as e:
            st.error(f"Error en Solapa Origen: {e}")
    # --- SOLAPA 2: CONTROL GESTIÓN RESERVAS ---
    with tabs[1]:
        try:
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_reserva_data(url): return pd.read_csv(url, engine='python', on_bad_lines='skip')
            try: df_res = load_reserva_data(url_reserva)
            except Exception: df_res = pd.read_csv(url_reserva)
            df_res.columns = df_res.columns.str.strip()
            df_res['Fecha_Inst_H'] = df_res.iloc[:, 7].astype(str).str.strip()
            df_g = df_res[df_res['Fecha_Inst_H'].apply(lambda x: len(str(x)) > 4)].copy()
            df_g['DT_Inst'] = pd.to_datetime(df_g.iloc[:, 7], dayfirst=True, errors='coerce')
            df_g['ETD_Status_K'] = df_g.iloc[:, 10].astype(str).str.upper().str.strip()
            df_g['Espera'] = (pd.to_datetime('today') - df_g['DT_Inst']).dt.days
            df_g['Critico'] = (df_g['ETD_Status_K'] != "OK") & (df_g['Espera'] > 5)
            col_so_res = [c for c in df_g.columns if 'SO' in str(c).upper()][0] if any('SO' in str(c).upper() for c in df_g.columns) else df_g.columns[2]
            df_plan_res = df_inst[df_inst.iloc[:, 20].notna() & (df_inst.iloc[:, 20].astype(str).str.strip() != "")].copy()
            col_etd_plan = '¿ETD OK FFWW?' if '¿ETD OK FFWW?' in df_plan_res.columns else df_plan_res.columns[97]
            df_plan_res['Status_P'] = df_plan_res[col_etd_plan].astype(str).str.lower().str.strip()
            def safe_float_f(val):
                if isinstance(val, (int, float)): return float(val)
                if pd.isna(val) or str(val).strip() in ['', 'nan']: return 0.0
                try:
                    s = str(val).strip()
                    if ',' in s and '.' in s:
                        if s.find('.') < s.find(','): s = s.replace('.', '').replace(',', '.')
                        else: s = s.replace(',', '')
                    elif ',' in s: s = s.replace(',', '.')
                    return float(s)
                except: return 0.0
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4)
            m3_total_clean = df_inst['M3 Total'].apply(safe_float_f).sum()
            fob_total_clean = df_inst['Fob total Origen'].apply(safe_float_f).sum()
            with k1: st.markdown(f"<div class='metric-container'><p>SO INSTRUIDAS</p><p>{int(df_inst['SO'].nunique())}</p></div>", unsafe_allow_html=True)
            with k2: st.markdown(f"<div class='metric-container'><p>VOLUMEN (M3)</p><p>{int(round(m3_total_clean)):,}</p></div>", unsafe_allow_html=True)
            with k3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{int(df_inst['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)
            with k4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL (USD)</p><p>${int(round(fob_total_clean)):,}</p></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL GESTIÓN RESERVAS</h2></div>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            df_p_ok = df_plan_res[df_plan_res['Status_P'] == "ok"]
            df_p_pend = df_plan_res[df_plan_res['Status_P'] != "ok"]
            c_so_ok = df_p_ok.iloc[:, 0].nunique()
            c_emb_ok = df_p_ok.iloc[:, 16].nunique()
            prov_ok_p = df_p_ok.iloc[:, 30].nunique()
            m3_ok_p = df_p_ok['M3 Total'].apply(safe_float_f).sum()
            c_so_pend = df_p_pend.iloc[:, 0].nunique()
            c_emb_pend = df_p_pend.iloc[:, 16].nunique()
            prov_pend_p = df_p_pend.iloc[:, 30].nunique()
            m3_pend_p = df_p_pend['M3 Total'].apply(safe_float_f).sum()
            total_emb_p = df_plan_res.iloc[:, 16].nunique()
            pct_ok_p = round((c_emb_ok / total_emb_p * 100)) if total_emb_p > 0 else 0
            pct_pend_p = 100 - pct_ok_p if total_emb_p > 0 else 0
            st.markdown(f"""
                <div class="grid-2">
                    <div class="custom-card" style="border: 2px solid rgba(0,255,136,0.5); box-shadow: 0 0 30px rgba(0,255,136,0.15);">
                        <p style="font-size: 22px; font-weight: 800; color: #00ff88; margin-bottom: 20px; letter-spacing: 2px; text-transform: uppercase;">EMBARQUES CON ETD OK ({pct_ok_p}%)</p>
                        <div class="grid-2" style="text-align: center;">
                            <div><p class="minicard-title">CANTIDAD SOs</p><p style="font-size:45px; font-weight:900; color:#f8fafc; margin:0; text-shadow:0 0 15px rgba(0,255,136,0.4);">{c_so_ok}</p></div>
                            <div><p class="minicard-title">EMBARQUES</p><p style="font-size:45px; font-weight:600; color:#f8fafc; margin:0;">{c_emb_ok}</p></div>
                            <div><p class="minicard-title">PROVEEDORES</p><p style="font-size:45px; font-weight:600; color:#00ff88; margin:0;">{prov_ok_p}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p style="font-size:35px; font-weight:800; color:#f8fafc; margin:0;">{int(round(m3_ok_p)):,} <span style="font-size:16px;">M3</span></p></div>
                        </div>
                    </div>
                    <div class="custom-card" style="border: 2px solid rgba(255,75,75,0.5); box-shadow: 0 0 30px rgba(255,75,75,0.15);">
                        <p style="font-size: 22px; font-weight: 800; color: #ff4b4b; margin-bottom: 20px; letter-spacing: 2px; text-transform: uppercase;">EMBARQUES PENDIENTES ({pct_pend_p}%)</p>
                        <div class="grid-2" style="text-align: center;">
                            <div><p class="minicard-title">CANTIDAD SOs</p><p style="font-size:45px; font-weight:900; color:#f8fafc; margin:0; text-shadow:0 0 15px rgba(255,75,75,0.4);">{c_so_pend}</p></div>
                            <div><p class="minicard-title">EMBARQUES</p><p style="font-size:45px; font-weight:600; color:#f8fafc; margin:0;">{c_emb_pend}</p></div>
                            <div><p class="minicard-title">PROVEEDORES</p><p style="font-size:45px; font-weight:600; color:#ff4b4b; margin:0;">{prov_pend_p}</p></div>
                            <div><p class="minicard-title">VOLUMEN TOTAL</p><p style="font-size:35px; font-weight:800; color:#f8fafc; margin:0;">{int(round(m3_pend_p)):,} <span style="font-size:16px;">M3</span></p></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:16px;'>DESGLOSE POR TIPO DE TRANSPORTE</p>", unsafe_allow_html=True)
            def clasificar_transp_res(x):
                x = str(x).upper().strip()
                if any(m in x for m in ["40 HQ", "40 ST", "40 NOR", "20 ST", "40NOR"]): return "MARITIMO"
                if any(a in x for a in ["AVION", "COURIER", "COURRIER"]): return "AVION / COURIER"
                return "OTROS"
            df_g['Transporte'] = df_g.iloc[:, 5].apply(clasificar_transp_res)
            t1, t2 = st.columns(2)
            for i, tipo in enumerate(["MARITIMO", "AVION / COURIER"]):
                df_tipo = df_g[df_g['Transporte'] == tipo]
                total_t = df_tipo.iloc[:, 0].nunique()
                ok_t = df_tipo[df_tipo['ETD_Status_K'] == "OK"].iloc[:, 0].nunique()
                pend_t = total_t - ok_t
                crit_t = df_tipo[df_tipo['Critico']].iloc[:, 0].nunique()
                m3_t = df_tipo.iloc[:, 24].apply(safe_float_f).sum()
                cntr_t = df_tipo.iloc[:, 1].apply(safe_float_f).sum()
                pct_ok = round((ok_t / total_t * 100)) if total_t > 0 else 0
                pct_pend = 100 - pct_ok if total_t > 0 else 0
                color_status = "#00ff88" if ok_t >= pend_t and total_t > 0 else "#ff4b4b"
                flecha = "▲" if ok_t >= pend_t else "▼"
                with [t1, t2][i]:
                    st.markdown(f"""
                    <div class="custom-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <p class="custom-card-title" style="color: #00a8ff;">{tipo}</p>
                            <div style="text-align: right;">
                                <p style="color: {color_status}; font-weight: 700; margin: 0; font-size: 22px;">{flecha} {int(pct_ok)}% <span style="font-size:12px; color:#94a3b8;">OK</span></p>
                                <p style="color: #ff4b4b; font-weight: 600; margin: 0; font-size: 16px; opacity: 0.8;">{int(pct_pend)}% <span style="font-size:11px; color:#94a3b8;">PEND</span></p>
                            </div>
                        </div>
                        <p style="font-size: 35px; font-weight: 300; color: #f8fafc; margin-top: 15px; margin-bottom: 5px;">Emb: <span style="font-weight:700;">{total_t}</span></p>
                        <div style="display: flex; gap: 15px; margin-top: 5px;">
                            <p style="color: #94a3b8; font-size: 13px;">CTNRS: <span style="color: #f8fafc; font-weight: 600;">{int(cntr_t)}</span></p>
                            <p style="color: #94a3b8; font-size: 13px;">VOL: <span style="color: #f8fafc; font-weight: 600;">{int(round(m3_t)):,} M3</span></p>
                        </div>
                        <p style="font-size: 14px; color: #94a3b8; font-weight: 600; margin: 0;">
                            <span style="color: #00ff88;">Confirmados: {ok_t}</span> | <span style="color: #ff4b4b;">Pendientes: {pend_t}</span>
                        </p>
                        {f'<p style="font-size:13px; color:#ff4b4b; font-weight:700; margin-top:10px;">🚨 CRÍTICOS (>5d): {crit_t}</p>' if crit_t > 0 else ""}
                    </div>""", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            df_mar = df_g[df_g['Transporte'] == "MARITIMO"].copy()
            def clean_val_mar(value):
                if pd.isna(value): return 0
                s = str(value).replace('.', '').replace(',', '.')
                num = ''.join(c for c in s if c.isdigit() or c == '.')
                return pd.to_numeric(num, errors='coerce') if num else 0
            df_mar.iloc[:, 1] = pd.to_numeric(df_mar.iloc[:, 1], errors='coerce').fillna(0)
            df_mar.iloc[:, 29] = pd.to_numeric(df_mar.iloc[:, 29], errors='coerce').fillna(0)
            df_mar.iloc[:, 21] = df_mar.iloc[:, 21].apply(clean_val_mar).fillna(0)
            st.markdown("<div style='margin-bottom:10px;'>", unsafe_allow_html=True)
            if st.button("ANALISIS BOOKING IN ADVANCE", key="btn_adv", use_container_width=True): st.session_state.mode = 'adv' if st.session_state.get('mode') != 'adv' else None
            st.markdown("</div>", unsafe_allow_html=True)
            def renderizar_detalle(mask, etiquetas, is_adv):
                col_a, col_b = st.columns(2)
                tot_local = len(df_mar) if len(df_mar) > 0 else 1
                for i_b, (titulo, dff_loc) in enumerate(etiquetas):
                    c_emb = len(dff_loc)
                    c_rel = round((c_emb / tot_local) * 100)
                    c_adv = len(dff_loc[dff_loc.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"])
                    p_adv = round((c_adv / c_emb * 100)) if c_emb > 0 else 0
                    c_box = "#00a8ff" if i_b == 0 else "#94a3b8"
                    with [col_a, col_b][i_b]:
                        st.markdown(f"""
                            <div class="custom-card" style="border-left: 5px solid {c_box}; margin-bottom: 20px;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px;">
                                    <p class="custom-card-title" style="color:{c_box};">{titulo} ({int(c_rel)}%)</p>
                                    <div style="text-align: right;">
                                        <p style="font-size:11px; color:#00ff88; font-weight:700; margin:0; letter-spacing:1px;">ADVANCE: {int(p_adv)}%</p>
                                        <p style="font-size:11px; color:#ff4b4b; font-weight:700; margin:0; letter-spacing:1px;">SPOT: {int(100 - p_adv)}%</p>
                                    </div>
                                </div>
                                <div class="grid-4">
                                    <div><p class="minicard-title">CANT. SOs</p><p class="minicard-value" style="font-weight:600;">{int(c_emb)}</p></div>
                                    <div><p class="minicard-title">CONTS.</p><p class="minicard-value" style="font-weight:600;">{int(round(dff_loc.iloc[:, 1].sum()))}</p></div>
                                    <div><p class="minicard-title">PROM. CONS.</p><p class="minicard-value" style="font-weight:600; color:#00ff88;">{int(round(dff_loc.iloc[:, 29].mean() if c_emb > 0 else 0))}d</p></div>
                                    <div><p class="minicard-title">FOB USD</p><p class="minicard-value" style="font-size:22px;">{int(round(dff_loc.iloc[:, 21].sum())):,}</p></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
            mode = st.session_state.get('mode')
            if mode == 'adv':
                msk_adv = df_mar.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
                lbl_adv = [("Booked in Advance", df_mar[msk_adv]), ("No Booked in Advance", df_mar[~msk_adv])]
                renderizar_detalle(msk_adv, lbl_adv, True)
            st.markdown("<div style='margin-bottom:10px;'>", unsafe_allow_html=True)
            if st.button("ANALISIS MONOPROVEEDOR / CONSOLIDADO", key="btn_mono", use_container_width=True): st.session_state.mode = 'mono' if st.session_state.get('mode') != 'mono' else None
            st.markdown("</div>", unsafe_allow_html=True)
            if mode == 'mono':
                msk_mon = df_mar.iloc[:, 34].astype(str).str.strip() == "Monoproveedor"
                lbl_mon = [("Monoproveedor", df_mar[msk_mon]), ("Consolidado", df_mar[~msk_mon])]
                renderizar_detalle(msk_mon, lbl_mon, False)
        except Exception as e:
            st.error(f"Error en Gestión de Reservas: {e}")
    # --- SOLAPA 3: PERFORMANCE DE ANALISTAS ---
    with tabs[2]:
        try:
            @st.cache_data(ttl=120)
            def load_perf_data(base):
                rh = pd.read_csv(f"{base}/export?format=csv&gid=32771816", engine='python', on_bad_lines='skip')
                eh = pd.read_csv(f"{base}/export?format=csv&gid=50628730", engine='python', on_bad_lines='skip')
                rh.columns = [str(c).strip() for c in rh.columns]
                eh.columns = [str(c).strip() for c in eh.columns]
                return rh, eh

            df_rh, df_eh = load_perf_data(base_url)
            col_rh_emb   = df_rh.columns[0]
            col_rh_resp  = df_rh.columns[14]
            col_rh_mono  = df_rh.columns[24]
            col_rh_tcons = df_rh.columns[32]
            col_eh_so    = df_eh.columns[0]
            col_eh_emb   = df_eh.columns[4]
            col_eh_etd   = df_eh.columns[6]
            col_eh_prov  = df_eh.columns[18]

            df_eh['ETD_DT']   = pd.to_datetime(df_eh[col_eh_etd], dayfirst=True, errors='coerce')
            df_eh_2026        = df_eh[df_eh['ETD_DT'].dt.year == 2026].copy()
            df_eh_2026['Mes_Num']   = df_eh_2026['ETD_DT'].dt.month
            df_eh_2026['Mes_Label'] = df_eh_2026['ETD_DT'].dt.strftime('%B %Y').str.upper()
            df_rh['_emb_key'] = df_rh[col_rh_emb].astype(str).str.strip().str.upper()

            def clean_tcons(val):
                try: return float(str(val).replace(',','.').strip())
                except: return None

            if df_eh_2026.empty:
                st.warning("No se encontraron embarques históricos para 2026.")
            else:
                meses_disp  = df_eh_2026.drop_duplicates('Mes_Num').sort_values('Mes_Num')[['Mes_Num','Mes_Label']].values.tolist()
                opciones_mes = {lbl: num for num, lbl in meses_disp}
                # Default: mes más reciente
                default_mes = list(opciones_mes.keys())[-1]
                default_idx = len(opciones_mes) - 1

                # ── HEADER ──────────────────────────────────────────────
                st.markdown("""
<div style='text-align:center; padding:28px 20px 20px;
background:linear-gradient(135deg,rgba(0,168,255,0.08),rgba(0,255,136,0.03));
border-radius:20px; border:1px solid rgba(0,168,255,0.2); margin-bottom:32px;'>
<h2 style='color:#00a8ff; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>PERFORMANCE ANALISTAS</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:12px; letter-spacing:3px;'>RANKING · TIEMPOS DE CONSOLIDACIÓN · EVOLUCIÓN MENSUAL</p>
</div>""", unsafe_allow_html=True)

                col_sel, _ = st.columns([2, 3])
                with col_sel:
                    mes_sel_lbl = st.selectbox("📅 MES ETD:", list(opciones_mes.keys()),
                                               index=default_idx, key="perf_mes_sel")
                mes_sel_num = opciones_mes[mes_sel_lbl]
                df_eh_mes   = df_eh_2026[df_eh_2026['Mes_Num'] == mes_sel_num].copy()
                embs_mes    = df_eh_mes[col_eh_emb].astype(str).str.strip().str.upper().unique()
                df_rh_mes   = df_rh[df_rh['_emb_key'].isin(embs_mes)].copy()
                df_rh_mes['T_Cons_Num']  = df_rh_mes[col_rh_tcons].apply(clean_tcons)
                df_rh_mes['Tipo_Carga']  = df_rh_mes[col_rh_mono].astype(str).str.strip().str.upper().apply(
                    lambda x: 'MONOPROVEEDOR' if 'MONO' in x else 'CONSOLIDADO')
                df_rh_mes['Responsable'] = df_rh_mes[col_rh_resp].astype(str).str.strip()
                df_rh_mes = df_rh_mes[~df_rh_mes['Responsable'].isin(['','nan','NaN','None','-'])]

                # ── KPIs DEL MES ────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                total_embs  = len(embs_mes)
                total_sos   = df_eh_mes[col_eh_so].nunique()
                total_provs = df_eh_mes[col_eh_prov].nunique()
                avg_tc      = df_rh_mes['T_Cons_Num'].median()

                k1,k2,k3,k4 = st.columns(4)
                for col_k, val, lbl, color, sub in [
                    (k1, total_embs,  "EMBARQUES",    "#00a8ff", mes_sel_lbl),
                    (k2, total_sos,   "SOs TOTALES",  "#00ff88", mes_sel_lbl),
                    (k3, total_provs, "PROVEEDORES",  "#f8fafc", mes_sel_lbl),
                    (k4, f"{int(round(avg_tc)) if pd.notna(avg_tc) else '—'}d",
                         "MEDIANA CONSOLIDACIÓN", "#ffaa00", "días marítimos"),
                ]:
                    col_k.markdown(f"""
<div style='text-align:center; padding:24px 12px;
background:rgba(255,255,255,0.03); border-radius:18px;
border:1px solid rgba(255,255,255,0.07); border-top:4px solid {color};'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0 0 8px 0; text-transform:uppercase;'>{lbl}</p>
<p style='color:{color}; font-size:56px; font-weight:900; margin:0; line-height:1; letter-spacing:-2px;'>{val}</p>
<p style='color:#475569; font-size:10px; margin:6px 0 0 0;'>{sub}</p>
</div>""", unsafe_allow_html=True)

                # ── RANKING DE ANALISTAS ─────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='border-bottom:2px solid rgba(0,168,255,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#00a8ff; font-size:13px; font-weight:800; letter-spacing:5px;'>RANKING DE ANALISTAS</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>ORDENADO POR EMBARQUES · SLA: MONO 10d · CONSOLIDADO 25d</span>
</div>""", unsafe_allow_html=True)

                SLA_MONO = 10
                SLA_CONS = 25
                rows_rank = []
                for analista, grp in df_rh_mes.groupby('Responsable'):
                    embs_a    = grp['_emb_key'].unique()
                    df_eh_a   = df_eh_mes[df_eh_mes[col_eh_emb].astype(str).str.strip().str.upper().isin(embs_a)]
                    cant_embs = len(embs_a)
                    cant_sos  = df_eh_a[col_eh_so].nunique()
                    cant_mono = (grp['Tipo_Carga'] == 'MONOPROVEEDOR').sum()
                    cant_cons = (grp['Tipo_Carga'] == 'CONSOLIDADO').sum()
                    avg_tc_a  = grp['T_Cons_Num'].median()
                    es_azul   = analista.strip().upper() == 'AZUL'

                    # SLA compliance
                    if es_azul:
                        sla_pct = None
                    else:
                        grp_mono = grp[grp['Tipo_Carga'] == 'MONOPROVEEDOR']
                        grp_cons = grp[grp['Tipo_Carga'] == 'CONSOLIDADO']
                        ok_mono  = (grp_mono['T_Cons_Num'] <= SLA_MONO).sum() if len(grp_mono) > 0 else 0
                        ok_cons  = (grp_cons['T_Cons_Num'] <= SLA_CONS).sum() if len(grp_cons) > 0 else 0
                        total_tc = len(grp[grp['T_Cons_Num'].notna()])
                        sla_pct  = round((ok_mono + ok_cons) / total_tc * 100) if total_tc > 0 else None

                    rows_rank.append({
                        'analista': analista, 'embs': cant_embs, 'sos': cant_sos,
                        'mono': cant_mono, 'cons': cant_cons,
                        'tc': avg_tc_a, 'sla_pct': sla_pct, 'es_azul': es_azul
                    })

                rows_rank.sort(key=lambda x: x['embs'], reverse=True)

                COLORES_ANALISTAS = ['#00a8ff','#00ff88','#ffaa00','#a855f7','#ff4b4b','#06b6d4']
                cols_rank = st.columns(min(len(rows_rank), 3))

                for i, r in enumerate(rows_rank):
                    color_a = COLORES_ANALISTAS[i % len(COLORES_ANALISTAS)]
                    es_azul = r['es_azul']

                    if es_azul:
                        tc_str   = '✈️ Aéreo'
                        sla_html = "<p style='color:#a855f7; font-size:11px; font-weight:700; margin:0;'>✈️ Modalidad aérea</p>"
                    else:
                        tc_val   = int(round(r['tc'])) if pd.notna(r['tc']) else None
                        tc_str   = f"{tc_val}d" if tc_val else '—'
                        tc_color = '#00ff88' if tc_val and tc_val <= SLA_MONO else '#ffaa00' if tc_val and tc_val <= SLA_CONS else '#ff4b4b'
                        sla_val  = r['sla_pct']
                        if sla_val is not None:
                            sla_color = '#00ff88' if sla_val >= 80 else '#ffaa00' if sla_val >= 60 else '#ff4b4b'
                            sla_label = 'DENTRO SLA' if sla_val >= 80 else 'ATENCIÓN' if sla_val >= 60 else 'FUERA SLA'
                            sla_html  = f"""
<div style='height:6px; background:rgba(255,255,255,0.06); border-radius:3px; margin-bottom:6px;'>
<div style='height:6px; width:{sla_val}%; background:{sla_color}; border-radius:3px;'></div>
</div>
<div style='display:flex; justify-content:space-between;'>
<p style='color:{sla_color}; font-size:11px; font-weight:800; margin:0;'>{sla_val}% {sla_label}</p>
<p style='color:#475569; font-size:10px; margin:0;'>Cumpl. SLA</p>
</div>"""
                        else:
                            sla_html = "<p style='color:#475569; font-size:11px; margin:0;'>Sin datos SLA</p>"

                    with cols_rank[i % 3]:
                        st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:18px;
border:1px solid rgba(255,255,255,0.08); padding:22px;
border-top:5px solid {color_a}; margin-bottom:16px;'>
<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;'>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 4px 0;'>#{i+1} ANALISTA</p>
        <p style='color:{color_a}; font-size:20px; font-weight:900; margin:0; text-transform:uppercase;'>{r['analista']}</p>
    </div>
    <div style='text-align:right;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>EMBARQUES</p>
        <p style='color:#f8fafc; font-size:42px; font-weight:900; margin:0; line-height:1;'>{r['embs']}</p>
    </div>
</div>
<div style='display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:16px;'>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>SOs</p>
        <p style='color:#f8fafc; font-size:22px; font-weight:800; margin:0;'>{r['sos']}</p>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>MONO</p>
        <p style='color:#00a8ff; font-size:22px; font-weight:800; margin:0;'>{r['mono']}</p>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>CONS</p>
        <p style='color:#ffaa00; font-size:22px; font-weight:800; margin:0;'>{r['cons']}</p>
    </div>
</div>
{'<div style="text-align:center; background:rgba(168,85,247,0.06); border-radius:10px; padding:10px; margin-bottom:14px;"><p style="color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;">MODALIDAD</p><p style="color:#a855f7; font-size:18px; font-weight:800; margin:0;">✈️ AÉREO</p></div>' if es_azul else f'<div style="text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px; margin-bottom:14px;"><p style="color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;">MEDIANA CONSOLIDACIÓN</p><p style="color:{tc_color}; font-size:28px; font-weight:900; margin:0;">{tc_str}</p></div>'}
<div style='border-top:1px solid rgba(255,255,255,0.06); padding-top:12px;'>
{sla_html}
</div>
</div>""", unsafe_allow_html=True)

                # ── EVOLUCIÓN MES A MES ─────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='border-bottom:2px solid rgba(0,255,136,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#00ff88; font-size:13px; font-weight:800; letter-spacing:5px;'>EVOLUCIÓN MES A MES</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>EMBARQUES Y TIEMPOS DE CONSOLIDACIÓN POR ANALISTA</span>
</div>""", unsafe_allow_html=True)

                rows_evol = []
                for mes_num, mes_lbl in meses_disp:
                    df_eh_m = df_eh_2026[df_eh_2026['Mes_Num'] == mes_num]
                    embs_m  = df_eh_m[col_eh_emb].astype(str).str.strip().str.upper().unique()
                    df_rh_m = df_rh[df_rh['_emb_key'].isin(embs_m)].copy()
                    df_rh_m['T_Cons_Num']  = df_rh_m[col_rh_tcons].apply(clean_tcons)
                    df_rh_m['Responsable'] = df_rh_m[col_rh_resp].astype(str).str.strip()
                    df_rh_m = df_rh_m[~df_rh_m['Responsable'].isin(['','nan','NaN','None','-'])]
                    for analista, grp_a in df_rh_m.groupby('Responsable'):
                        embs_a = grp_a['_emb_key'].unique()
                        df_a   = df_eh_m[df_eh_m[col_eh_emb].astype(str).str.strip().str.upper().isin(embs_a)]
                        rows_evol.append({
                            'Mes_Num': mes_num, 'Mes': mes_lbl, 'Analista': analista,
                            'Embarques': len(embs_a),
                            'SOs': df_a[col_eh_so].nunique(),
                            'Días Cons.': round(grp_a['T_Cons_Num'].median(), 1) if grp_a['T_Cons_Num'].notna().any() else None,
                        })

                df_evol = pd.DataFrame(rows_evol)
                if not df_evol.empty:
                    analistas_disp = sorted(df_evol['Analista'].unique())
                    col_pick, _ = st.columns([2, 3])
                    with col_pick:
                        analista_sel = st.selectbox("VER EVOLUCIÓN DE:", analistas_disp, key="perf_analista_sel")

                    df_evol_a  = df_evol[df_evol['Analista'] == analista_sel].sort_values('Mes_Num')
                    es_azul_sel = analista_sel.strip().upper() == 'AZUL'
                    color_sel   = COLORES_ANALISTAS[analistas_disp.index(analista_sel) % len(COLORES_ANALISTAS)]

                    if es_azul_sel:
                        fig_ev = px.bar(df_evol_a, x='Mes', y='Embarques', text='Embarques',
                                        color_discrete_sequence=[color_sel])
                        fig_ev.update_traces(textposition='outside', textfont=dict(color='#f8fafc', size=13),
                                             marker=dict(cornerradius=6))
                        fig_ev.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)',
                                             plot_bgcolor='rgba(0,0,0,0)',
                                             font=dict(family='Outfit, sans-serif', color='#94a3b8'),
                                             xaxis=dict(showgrid=False), margin=dict(l=10,r=10,t=30,b=10),
                                             yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'))
                        st.plotly_chart(fig_ev, use_container_width=True)
                        st.info("✈️ Azul gestiona cargas aéreas — tiempos de consolidación marítima no aplican.")
                    else:
                        ev1, ev2 = st.columns(2)
                        with ev1:
                            fig_emb = px.bar(df_evol_a, x='Mes', y='Embarques', text='Embarques',
                                             color_discrete_sequence=[color_sel],
                                             title=f"Embarques — {analista_sel}")
                            fig_emb.update_traces(textposition='outside',
                                                  textfont=dict(color='#f8fafc', size=13),
                                                  marker=dict(cornerradius=6))
                            fig_emb.update_layout(height=360, paper_bgcolor='rgba(0,0,0,0)',
                                                  plot_bgcolor='rgba(0,0,0,0)',
                                                  font=dict(family='Outfit, sans-serif', color='#94a3b8'),
                                                  title_font_color=color_sel,
                                                  xaxis=dict(showgrid=False, tickangle=-30),
                                                  yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'),
                                                  margin=dict(l=10,r=10,t=50,b=10))
                            st.plotly_chart(fig_emb, use_container_width=True)
                        with ev2:
                            fig_tc = px.line(df_evol_a, x='Mes', y='Días Cons.',
                                             markers=True, text='Días Cons.',
                                             color_discrete_sequence=['#ffaa00'],
                                             title=f"Mediana Consolidación — {analista_sel}")
                            fig_tc.update_traces(
                                line=dict(width=3), marker=dict(size=10, line=dict(color='#fff', width=2)),
                                texttemplate='<b>%{text:.0f}d</b>', textposition='top center',
                                textfont=dict(size=12, color='#f8fafc'),
                                fill='tozeroy', fillcolor='rgba(255,170,0,0.06)')
                            # SLA reference lines
                            fig_tc.add_hline(y=SLA_MONO, line=dict(color='#00ff88', width=1, dash='dot'),
                                             annotation_text=f"SLA Mono {SLA_MONO}d",
                                             annotation_font=dict(color='#00ff88', size=10))
                            fig_tc.add_hline(y=SLA_CONS, line=dict(color='#ff4b4b', width=1, dash='dot'),
                                             annotation_text=f"SLA Cons {SLA_CONS}d",
                                             annotation_font=dict(color='#ff4b4b', size=10))
                            fig_tc.update_layout(height=360, paper_bgcolor='rgba(0,0,0,0)',
                                                 plot_bgcolor='rgba(0,0,0,0)',
                                                 font=dict(family='Outfit, sans-serif', color='#94a3b8'),
                                                 title_font_color='#ffaa00',
                                                 xaxis=dict(showgrid=False, tickangle=-30),
                                                 yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)',
                                                            title='Días (mediana)'),
                                                 margin=dict(l=10,r=10,t=50,b=10))
                            st.plotly_chart(fig_tc, use_container_width=True)

        except Exception as e:
            st.error(f"Error en Performance Analistas: {e}")
            import traceback
            st.code(traceback.format_exc())

    # --- SOLAPA 4: PERFORMANCE DE AGENTES ---
    with tabs[3]:
        try:
            try:
                _ = df_rh
            except NameError:
                @st.cache_data(ttl=120)
                def load_perf_data_ag(base):
                    rh = pd.read_csv(f"{base}/export?format=csv&gid=32771816", engine='python', on_bad_lines='skip')
                    rh.columns = [str(c).strip() for c in rh.columns]
                    return rh
                df_rh = load_perf_data_ag(base_url)
                df_rh['_emb_key'] = df_rh[df_rh.columns[0]].astype(str).str.strip().str.upper()

            col_ag_fwd       = df_rh.columns[6]
            col_ag_inst      = df_rh.columns[7]
            col_ag_etd       = df_rh.columns[11]
            col_ag_bl        = df_rh.columns[15]
            col_ag_conf      = df_rh.columns[18]
            col_ag_cntr      = df_rh.columns[1]
            col_ag_flete_pag = df_rh.columns[51] if len(df_rh.columns) > 51 else None
            col_ag_flete_cert= df_rh.columns[52] if len(df_rh.columns) > 52 else None
            col_ag_tipo      = df_rh.columns[5]

            df_rh['_inst_dt'] = pd.to_datetime(df_rh[col_ag_inst], dayfirst=True, errors='coerce')
            df_rh['_etd_dt']  = pd.to_datetime(df_rh[col_ag_etd],  dayfirst=True, errors='coerce')
            df_rh['_bl_dt']   = pd.to_datetime(df_rh[col_ag_bl],   dayfirst=True, errors='coerce')
            df_rh['_conf_dt'] = pd.to_datetime(df_rh[col_ag_conf], dayfirst=True, errors='coerce')

            TIPOS_MAR = ['40 HQ','20 ST','40 ST','40 NOR']
            df_rh_mar = df_rh[
                df_rh[col_ag_tipo].astype(str).str.strip().str.upper().isin([t.upper() for t in TIPOS_MAR]) &
                (df_rh['_etd_dt'].dt.year == 2026)
            ].copy()
            df_rh_mar['Mes_Num']   = df_rh_mar['_etd_dt'].dt.month
            df_rh_mar['Mes_Label'] = df_rh_mar['_etd_dt'].dt.strftime('%B %Y').str.upper()

            def safe_num(v):
                try: return float(str(v).replace(',','.').replace(' ','').strip())
                except: return None

            for col in [col_ag_flete_pag, col_ag_flete_cert, col_ag_cntr]:
                if col: df_rh_mar[col] = df_rh_mar[col].apply(safe_num)

            if df_rh_mar.empty:
                st.warning("Sin datos de agentes para 2026.")
            else:
                meses_ag    = df_rh_mar.drop_duplicates('Mes_Num').sort_values('Mes_Num')[['Mes_Num','Mes_Label']].values.tolist()
                opciones_ag = {lbl: num for num, lbl in meses_ag}
                default_ag  = list(opciones_ag.keys())[-1]
                default_ag_idx = len(opciones_ag) - 1

                # ── HEADER ───────────────────────────────────────────────
                st.markdown("""
<div style='text-align:center; padding:28px 20px 20px;
background:linear-gradient(135deg,rgba(255,170,0,0.08),rgba(168,85,247,0.04));
border-radius:20px; border:1px solid rgba(255,170,0,0.2); margin-bottom:32px;'>
<h2 style='color:#ffaa00; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>PERFORMANCE AGENTES</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:12px; letter-spacing:3px;'>RANKING COMBINADO · VELOCIDAD · CERTIFICACIÓN · MARÍTIMO 2026</p>
</div>""", unsafe_allow_html=True)

                col_ag_sel, _ = st.columns([2, 3])
                with col_ag_sel:
                    mes_ag_lbl = st.selectbox("📅 MES ETD:", list(opciones_ag.keys()),
                                              index=default_ag_idx, key="perf_ag_mes_sel")
                mes_ag_num = opciones_ag[mes_ag_lbl]
                df_mes_ag  = df_rh_mar[df_rh_mar['Mes_Num'] == mes_ag_num].copy()
                df_mes_ag['_dias_ic'] = (df_mes_ag['_conf_dt'] - df_mes_ag['_inst_dt']).dt.days
                df_mes_ag['_dias_bl'] = (df_mes_ag['_bl_dt']   - df_mes_ag['_etd_dt']).dt.days
                df_mes_ag['_fwd']     = df_mes_ag[col_ag_fwd].astype(str).str.strip()
                df_mes_ag = df_mes_ag[~df_mes_ag['_fwd'].isin(['','nan','NaN','None','-'])]

                # ── KPIs DEL MES ─────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                total_embs_ag = df_mes_ag[df_rh.columns[0]].nunique()
                total_cntr_ag = df_mes_ag[col_ag_cntr].sum() if col_ag_cntr else 0
                avg_ic        = df_mes_ag['_dias_ic'].median()
                avg_bl        = df_mes_ag['_dias_bl'].median()
                sum_fp        = df_mes_ag[col_ag_flete_pag].sum()  if col_ag_flete_pag  else 0
                sum_fc        = df_mes_ag[col_ag_flete_cert].sum() if col_ag_flete_cert else 0
                pct_cert_gbl  = round(sum_fc / sum_fp * 100, 1) if sum_fp and sum_fp > 0 else None
                cert_color    = '#00ff88' if pct_cert_gbl and pct_cert_gbl >= 75 else '#ff4b4b'

                k1,k2,k3,k4,k5 = st.columns(5)
                for col_k, val, lbl, color in [
                    (k1, total_embs_ag, "EMBARQUES",        "#00a8ff"),
                    (k2, int(total_cntr_ag) if pd.notna(total_cntr_ag) else 0, "CONTENEDORES", "#00ff88"),
                    (k3, f"{int(round(avg_ic)) if pd.notna(avg_ic) else '—'}d", "MED. INSTR-CONF", "#ffaa00"),
                    (k4, f"{int(round(avg_bl)) if pd.notna(avg_bl) else '—'}d", "MED. ETD-BL",    "#a855f7"),
                    (k5, f"{pct_cert_gbl}%" if pct_cert_gbl else "SD", "CERTIFICACIÓN", cert_color),
                ]:
                    col_k.markdown(f"""
<div style='text-align:center; padding:20px 10px;
background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); border-top:4px solid {color};'>
<p style='color:#64748b; font-size:9px; letter-spacing:2px; margin:0 0 6px 0; text-transform:uppercase;'>{lbl}</p>
<p style='color:{color}; font-size:44px; font-weight:900; margin:0; line-height:1; letter-spacing:-2px;'>{val}</p>
<p style='color:#475569; font-size:9px; margin:5px 0 0 0;'>{mes_ag_lbl}</p>
</div>""", unsafe_allow_html=True)

                # ── RANKING COMBINADO ────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='border-bottom:2px solid rgba(255,170,0,0.3); padding-bottom:10px; margin-bottom:8px;'>
<span style='color:#ffaa00; font-size:13px; font-weight:800; letter-spacing:5px;'>RANKING COMBINADO DE AGENTES</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>CERTIFICACIÓN 50% · VELOCIDAD BOOKING 25% · DÍAS ETD-BL 25%</span>
</div>""", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:8px 14px; background:rgba(255,255,255,0.02); border-radius:8px;
border-left:3px solid #334155; margin-bottom:20px;'>
<p style='color:#334155; font-size:11px; margin:0;'>
🔍 <b style='color:#475569;'>Score:</b> certificación (KPI ≥75% → 10 pts) · velocidad booking (menos días → mejor puntaje) · días ETD-BL · <b style='color:#475569;'>Escala 0–10</b>
</p></div>""", unsafe_allow_html=True)

                rows_ag = []
                for fwd, grp in df_mes_ag.groupby('_fwd'):
                    cant_embs = grp[df_rh.columns[0]].nunique()
                    cant_cntr = grp[col_ag_cntr].sum() if col_ag_cntr else 0
                    med_ic    = grp['_dias_ic'].median()
                    med_bl    = grp['_dias_bl'].median()
                    fp_f      = grp[col_ag_flete_pag].sum()  if col_ag_flete_pag  else 0
                    fc_f      = grp[col_ag_flete_cert].sum() if col_ag_flete_cert else 0
                    pct_f     = round(fc_f / fp_f * 100, 1)  if fp_f and fp_f > 0 else None

                    # Score certificación (50%)
                    sc_cert  = min((pct_f / 75) * 5, 5) if pct_f else 0

                    # Score velocidad booking (25%) — mejor = menos días, ref 7d = 2.5pts
                    if pd.notna(med_ic) and med_ic >= 0:
                        sc_vel = max(0, 2.5 - (med_ic / 7) * 1.25)
                    else:
                        sc_vel = 0

                    # Score ETD-BL (25%) — mejor = menos días, ref 5d = 2.5pts
                    if pd.notna(med_bl) and med_bl >= 0:
                        sc_bl = max(0, 2.5 - (med_bl / 5) * 1.25)
                    else:
                        sc_bl = 0

                    score = round(sc_cert + sc_vel + sc_bl, 1)

                    rows_ag.append({
                        'fwd': fwd, 'embs': cant_embs,
                        'cntr': int(cant_cntr) if pd.notna(cant_cntr) else 0,
                        'med_ic': med_ic, 'med_bl': med_bl,
                        'pct_cert': pct_f, 'score': score
                    })

                rows_ag.sort(key=lambda x: x['score'], reverse=True)

                for rank, r in enumerate(rows_ag):
                    score    = r['score']
                    color_r  = '#00ff88' if score >= 7 else '#ffaa00' if score >= 4 else '#ff4b4b'
                    badge    = '🏆 EXCELENTE' if score >= 7 else '⚠️ REGULAR' if score >= 4 else '🔴 BAJO'
                    pct_bar  = round(score / 10 * 100)

                    cert_str  = f"{r['pct_cert']}%" if r['pct_cert'] else "Sin datos"
                    cert_col  = '#00ff88' if r['pct_cert'] and r['pct_cert'] >= 75 else '#ff4b4b'
                    ic_str    = f"{int(round(r['med_ic']))}d" if pd.notna(r['med_ic']) else "—"
                    bl_str    = f"{int(round(r['med_bl']))}d" if pd.notna(r['med_bl']) else "—"
                    ic_col    = '#00ff88' if pd.notna(r['med_ic']) and r['med_ic'] <= 7 else '#ffaa00' if pd.notna(r['med_ic']) and r['med_ic'] <= 14 else '#ff4b4b'
                    bl_col    = '#00ff88' if pd.notna(r['med_bl']) and r['med_bl'] <= 5 else '#ffaa00' if pd.notna(r['med_bl']) and r['med_bl'] <= 10 else '#ff4b4b'

                    st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:20px 24px; margin-bottom:12px;
border-left:6px solid {color_r};'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;'>
    <div style='display:flex; align-items:center; gap:16px;'>
        <p style='color:#1e293b; font-size:28px; font-weight:900; margin:0; min-width:40px;'>#{rank+1}</p>
        <div>
            <p style='color:#f8fafc; font-size:18px; font-weight:800; margin:0;'>{r['fwd']}</p>
            <p style='color:{color_r}; font-size:11px; font-weight:800; margin:3px 0 0 0; letter-spacing:1px;'>{badge}</p>
        </div>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.04); border-radius:14px; padding:10px 20px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:2px; margin:0 0 2px 0;'>SCORE</p>
        <p style='color:{color_r}; font-size:36px; font-weight:900; margin:0; line-height:1;'>{score}</p>
        <p style='color:#334155; font-size:9px; margin:2px 0 0 0;'>/ 10</p>
    </div>
</div>
<div style='height:6px; background:rgba(255,255,255,0.05); border-radius:3px; margin-bottom:16px;'>
    <div style='height:6px; width:{pct_bar}%; background:{color_r}; border-radius:3px;'></div>
</div>
<div style='display:grid; grid-template-columns:repeat(5,1fr); gap:10px;'>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>EMBARQUES</p>
        <p style='color:#f8fafc; font-size:20px; font-weight:800; margin:0;'>{r['embs']}</p>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>CNTRS</p>
        <p style='color:#f8fafc; font-size:20px; font-weight:800; margin:0;'>{r['cntr']}</p>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>CERTIF.</p>
        <p style='color:{cert_col}; font-size:20px; font-weight:800; margin:0;'>{cert_str}</p>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>INSTR-CONF</p>
        <p style='color:{ic_col}; font-size:20px; font-weight:800; margin:0;'>{ic_str}</p>
    </div>
    <div style='text-align:center; background:rgba(255,255,255,0.03); border-radius:10px; padding:10px;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>ETD-BL</p>
        <p style='color:{bl_col}; font-size:20px; font-weight:800; margin:0;'>{bl_str}</p>
    </div>
</div>
</div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Performance Agentes: {e}")
            import traceback
            st.code(traceback.format_exc())

    # --- SOLAPA 4: FLETES & GASTOS LOCALES ---
    with tabs[4]:
        try:
            SHEET_URL   = "https://docs.google.com/spreadsheets/d/1UJ1bDyDQdIQSSVQ6dyChVKbMX1d69G68ji_dpsOzfHg"
            POD_EXCLUIR = ['LÁZARO CÁRDENAS','LAZARO CARDENAS','MANZANILLO',
                           'MANZANILLO / LAZARO CARDENAS','MONTEVIDEO',
                           'MONTEVIDEO/SANTOS','MVD/SSZ','SANTOS','URUGUAY']

            @st.cache_data(ttl=300)
            def load_fletes_v2(url):
                df_f = pd.read_csv(f"{url}/export?format=csv&gid=0", header=0, dtype=str, on_bad_lines='skip')
                df_f.columns = [str(c).strip() for c in df_f.columns]
                return df_f

            df_fl = load_fletes_v2(SHEET_URL)

            def parse_usd(v):
                try:
                    s = str(v).replace('USD','').replace('$','').replace(' ','').strip()
                    return float(s.replace('.','').replace(',','.'))
                except: return None

            col_agente  = df_fl.columns[1]
            col_pod     = df_fl.columns[8]
            col_flete   = df_fl.columns[3]
            col_desde   = df_fl.columns[10]
            col_hasta   = df_fl.columns[11]
            col_local   = df_fl.columns[14]
            col_cnt     = df_fl.columns[15]

            df_fl['_desde']  = pd.to_datetime(df_fl[col_desde], dayfirst=True, errors='coerce')
            df_fl['_hasta']  = pd.to_datetime(df_fl[col_hasta], dayfirst=True, errors='coerce')
            df_fl['_flete']  = df_fl[col_flete].apply(parse_usd)
            df_fl['_local']  = df_fl[col_local].apply(parse_usd)
            df_fl['_cnt']    = df_fl[col_cnt].astype(str).str.strip().str.upper()
            df_fl['_agente'] = df_fl[col_agente].astype(str).str.strip()
            df_fl['_anio']   = df_fl['_desde'].dt.year
            df_fl['_mes']    = df_fl['_desde'].dt.month
            df_fl['_pod']    = df_fl[col_pod].astype(str).str.strip().str.upper()

            # Excluir PODs no deseados
            mask_pod = ~df_fl['_pod'].str.upper().str.contains(
                '|'.join(['LAZARO','CÁRDENAS','CARDENAS','MANZANILLO','MONTEVIDEO','SANTOS','URUGUAY','MVD']),
                na=False)
            df_fl = df_fl[mask_pod & df_fl['_flete'].notna() &
                          (df_fl['_cnt'] != 'NAN') & (df_fl['_cnt'] != '')].copy()

            TIPOS_CNT   = ['40ST/40HQ', '20ST', '40NOR']
            TARGET_PCT  = 0.85
            COLORES_CNT = {'40ST/40HQ':'#00a8ff','20ST':'#00ff88','40NOR':'#ffaa00'}
            COLORES_AG  = ['#00a8ff','#00ff88','#ffaa00','#ff4b4b','#a855f7','#06b6d4','#f97316','#ec4899']

            df_vig = df_fl[(df_fl['_desde'] <= hoy) & (df_fl['_hasta'] >= hoy)].copy()
            if df_vig.empty:
                ult = df_fl['_desde'].max()
                if pd.notna(ult):
                    df_vig = df_fl[df_fl['_desde'] == ult].copy()

            # ═══════════════════════════════════════════════════════════
            # HEADER
            # ═══════════════════════════════════════════════════════════
            st.markdown("""
<div style='text-align:center; padding:28px 20px 20px 20px;
background:linear-gradient(135deg,rgba(255,170,0,0.08),rgba(0,168,255,0.04));
border-radius:20px; border:1px solid rgba(255,170,0,0.2); margin-bottom:32px;'>
<h2 style='color:#ffaa00; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>FLETES & GASTOS LOCALES</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:12px; letter-spacing:3px;'>
MERCADO MARÍTIMO · ANÁLISIS ESTRATÉGICO · MEDIANA DE TARIFAS</p>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 1 — SITUACIÓN HOY
            # ═══════════════════════════════════════════════════════════
            st.markdown("""
<div style='border-bottom:2px solid rgba(255,170,0,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#ffaa00; font-size:13px; font-weight:800; letter-spacing:5px;'>01 · SITUACIÓN HOY</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>COTIZACIONES VIGENTES · MEDIANA DE MERCADO</span>
</div>""", unsafe_allow_html=True)

            if not df_vig.empty:
                cols_kpi = st.columns(len(TIPOS_CNT))
                for i, cnt in enumerate(TIPOS_CNT):
                    df_c = df_vig[df_vig['_cnt'] == cnt]
                    if df_c.empty:
                        with cols_kpi[i]:
                            st.markdown(f"<div style='text-align:center;padding:20px;border-radius:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);'><p style='color:#475569;font-size:13px;margin:0;'>{cnt}</p><p style='color:#475569;font-size:13px;'>Sin datos</p></div>", unsafe_allow_html=True)
                        continue

                    med_hoy   = df_c['_flete'].median()
                    min_hoy   = df_c['_flete'].min()
                    ag_min    = df_c.loc[df_c['_flete'].idxmin(), '_agente']
                    target    = med_hoy * TARGET_PCT
                    ok        = min_hoy <= target
                    color_cnt = COLORES_CNT.get(cnt, '#94a3b8')
                    semaforo  = '#00ff88' if ok else '#ff4b4b'
                    etiqueta  = '✅ DENTRO DEL TARGET' if ok else '🔴 POR ENCIMA DEL TARGET'

                    # vs 2025 mismo mes
                    df_25 = df_fl[(df_fl['_anio'] == 2025) & (df_fl['_mes'] == hoy.month) & (df_fl['_cnt'] == cnt)]
                    med_25 = df_25['_flete'].median() if not df_25.empty else None
                    if med_25 and med_25 > 0:
                        delta_pct = round((med_hoy - med_25) / med_25 * 100, 1)
                        delta_str = f"{'▲' if delta_pct > 0 else '▼'} {abs(delta_pct)}% vs mismo mes 2025"
                        delta_col = '#ff4b4b' if delta_pct > 0 else '#00ff88'
                    else:
                        delta_str = '— sin dato 2025'
                        delta_col = '#475569'

                    with cols_kpi[i]:
                        st.markdown(f"""
<div style='text-align:center; padding:24px 16px;
background:linear-gradient(145deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));
border-radius:20px; border:1px solid rgba(255,255,255,0.08);
border-top:5px solid {color_cnt}; margin-bottom:8px;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0 0 6px 0; text-transform:uppercase;'>{cnt}</p>
<p style='color:{color_cnt}; font-size:52px; font-weight:900; margin:0; line-height:1; letter-spacing:-2px;'>
USD {int(round(med_hoy)):,}</p>
<p style='color:#475569; font-size:10px; margin:6px 0 0 0;'>mediana de mercado hoy</p>
<hr style='border:none; border-top:1px solid rgba(255,255,255,0.06); margin:14px 0;'>
<div style='display:flex; justify-content:space-between; align-items:center;'>
    <div style='text-align:left;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>MEJOR OFERTA</p>
        <p style='color:#f8fafc; font-size:18px; font-weight:800; margin:0;'>USD {int(round(min_hoy)):,}</p>
        <p style='color:#64748b; font-size:9px; margin:2px 0 0 0;'>{ag_min}</p>
    </div>
    <div style='text-align:right;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>TARGET −15%</p>
        <p style='color:{semaforo}; font-size:18px; font-weight:800; margin:0;'>USD {int(round(target)):,}</p>
        <p style='color:{semaforo}; font-size:9px; font-weight:700; margin:2px 0 0 0;'>{etiqueta}</p>
    </div>
</div>
<div style='margin-top:12px; padding:8px 10px; background:rgba(255,255,255,0.03);
border-radius:8px; border-left:3px solid {delta_col};'>
<p style='color:{delta_col}; font-size:11px; font-weight:700; margin:0;'>{delta_str}</p>
</div>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 2 — BATTLE DE AGENTES
            # ═══════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(0,168,255,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#00a8ff; font-size:13px; font-weight:800; letter-spacing:5px;'>02 · BATTLE DE AGENTES</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>RANKING DE TARIFAS VIGENTES HOY · DE MÁS BARATO A MÁS CARO</span>
</div>""", unsafe_allow_html=True)

            col_cnt_sel, _ = st.columns([2, 3])
            with col_cnt_sel:
                cnt_battle = st.selectbox("TIPO DE CONTENEDOR:", TIPOS_CNT, key="battle_cnt_sel")

            df_battle = df_vig[df_vig['_cnt'] == cnt_battle].copy()
            if df_battle.empty:
                st.info(f"No hay cotizaciones vigentes para {cnt_battle}.")
            else:
                med_mkt  = df_battle['_flete'].median()
                target_b = med_mkt * TARGET_PCT

                ag_summary = df_battle.groupby('_agente')['_flete'].median().reset_index()
                ag_summary.columns = ['Agente', 'Tarifa']
                ag_summary = ag_summary.sort_values('Tarifa').reset_index(drop=True)
                max_tar = ag_summary['Tarifa'].max()

                st.markdown(f"""
<div style='display:flex; gap:20px; margin-bottom:20px;'>
<div style='padding:12px 20px; background:rgba(255,255,255,0.03); border-radius:12px;
border-left:4px solid #94a3b8;'>
<p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>MEDIANA MERCADO</p>
<p style='color:#f8fafc; font-size:20px; font-weight:800; margin:0;'>USD {int(round(med_mkt)):,}</p>
</div>
<div style='padding:12px 20px; background:rgba(255,170,0,0.06); border-radius:12px;
border-left:4px solid #ffaa00;'>
<p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>TARGET −15%</p>
<p style='color:#ffaa00; font-size:20px; font-weight:800; margin:0;'>USD {int(round(target_b)):,}</p>
</div>
<div style='padding:12px 20px; background:rgba(255,255,255,0.03); border-radius:12px;
border-left:4px solid #475569;'>
<p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>AGENTES COTIZANDO</p>
<p style='color:#f8fafc; font-size:20px; font-weight:800; margin:0;'>{len(ag_summary)}</p>
</div>
</div>""", unsafe_allow_html=True)

                for rank, (_, row) in enumerate(ag_summary.iterrows()):
                    ag      = row['Agente']
                    tarifa  = row['Tarifa']
                    pct_bar = round(tarifa / max_tar * 100) if max_tar > 0 else 0
                    ok_ag   = tarifa <= target_b
                    color_ag = '#00ff88' if ok_ag else ('#ffaa00' if tarifa <= med_mkt else '#ff4b4b')
                    badge   = '✅ DENTRO DEL TARGET' if ok_ag else ('⚠️ CERCA DEL TARGET' if tarifa <= med_mkt else '🔴 CARO')
                    ahorro  = int(round(tarifa - ag_summary['Tarifa'].iloc[0]))
                    ahorro_str = f"+USD {ahorro:,} vs más barato" if ahorro > 0 else "🏆 MÁS BARATO"
                    ahorro_col = '#ff4b4b' if ahorro > 0 else '#00ff88'

                    st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:14px;
border:1px solid rgba(255,255,255,0.06); padding:16px 20px; margin-bottom:10px;
border-left:5px solid {color_ag};'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
    <div style='display:flex; align-items:center; gap:14px;'>
        <p style='color:#334155; font-size:22px; font-weight:900; margin:0; width:32px;'>#{rank+1}</p>
        <div>
            <p style='color:#f8fafc; font-size:16px; font-weight:700; margin:0;'>{ag}</p>
            <p style='color:{color_ag}; font-size:10px; font-weight:700; margin:2px 0 0 0;'>{badge}</p>
        </div>
    </div>
    <div style='text-align:right;'>
        <p style='color:{color_ag}; font-size:28px; font-weight:900; margin:0; line-height:1;'>USD {int(round(tarifa)):,}</p>
        <p style='color:{ahorro_col}; font-size:11px; font-weight:700; margin:3px 0 0 0;'>{ahorro_str}</p>
    </div>
</div>
<div style='height:6px; background:rgba(255,255,255,0.05); border-radius:3px;'>
    <div style='height:6px; width:{pct_bar}%; background:{color_ag}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 3 — 2025 vs 2026
            # ═══════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(168,85,247,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#a855f7; font-size:13px; font-weight:800; letter-spacing:5px;'>03 · EVOLUCIÓN 2025 vs 2026</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>MEDIANA MENSUAL · DETECTÁ ESTACIONALIDAD Y TENDENCIA</span>
</div>""", unsafe_allow_html=True)

            col_cnt_h, _ = st.columns([2, 3])
            with col_cnt_h:
                cnt_hist = st.selectbox("TIPO DE CONTENEDOR:", TIPOS_CNT, key="hist_cnt_v2")

            df_hist = df_fl[df_fl['_cnt'] == cnt_hist].copy()
            df_hist = df_hist[df_hist['_anio'].isin([2025, 2026])].copy()

            if df_hist.empty:
                st.info("Sin datos históricos suficientes.")
            else:
                meses_dict = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
                              7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
                df_hist['_mes_label'] = df_hist['_mes'].map(meses_dict)

                res_hist = df_hist.groupby(['_anio','_mes','_mes_label'])['_flete'].median().reset_index()
                res_hist.columns = ['Año','Mes_Num','Mes','Mediana']
                res_hist['Año'] = res_hist['Año'].astype(str)
                res_hist = res_hist.sort_values(['Año','Mes_Num'])

                fig_hist = px.line(
                    res_hist, x='Mes', y='Mediana', color='Año',
                    markers=True, text='Mediana',
                    color_discrete_map={'2025':'#475569','2026':'#a855f7'},
                    labels={'Mediana':'USD (mediana)','Mes':''},
                    category_orders={'Mes': list(meses_dict.values())}
                )
                fig_hist.update_traces(
                    line=dict(width=3),
                    marker=dict(size=10, line=dict(color='#fff', width=1.5)),
                    texttemplate='<b>%{text:,.0f}</b>',
                    textposition='top center',
                    textfont=dict(size=11, family='Outfit, sans-serif'),
                )
                # Área bajo 2026 más visible
                fig_hist.for_each_trace(lambda t: t.update(
                    fill='tozeroy', fillcolor='rgba(168,85,247,0.06)'
                ) if t.name == '2026' else t.update(
                    fill='none', line=dict(dash='dot', width=2)
                ))
                fig_hist.update_layout(
                    height=420,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=12),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02,
                                xanchor='right', x=1, title_text='',
                                font=dict(size=13)),
                    xaxis=dict(showgrid=False, tickfont=dict(size=13, color='#94a3b8')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)',
                               title='USD mediana', tickfont=dict(size=12)),
                    margin=dict(l=20, r=20, t=50, b=20),
                )
                # Línea vertical en mes actual
                mes_actual_label = meses_dict.get(hoy.month)
                if mes_actual_label in res_hist['Mes'].values:
                    fig_hist.add_vline(
                        x=mes_actual_label,
                        line=dict(color='rgba(255,255,255,0.15)', width=1, dash='dash')
                    )
                    fig_hist.add_annotation(
                        x=mes_actual_label, y=res_hist['Mediana'].max(),
                        text="HOY", showarrow=False,
                        font=dict(color='#475569', size=10, family='Outfit, sans-serif'),
                        yshift=14
                    )
                st.plotly_chart(fig_hist, use_container_width=True)

                # Mini tabla comparativa
                pivot = res_hist.pivot(index='Mes', columns='Año', values='Mediana')
                pivot.index = pd.Categorical(pivot.index, categories=list(meses_dict.values()), ordered=True)
                pivot = pivot.sort_index().reset_index()
                if '2025' in pivot.columns and '2026' in pivot.columns:
                    pivot['Δ vs 2025'] = pivot.apply(
                        lambda r: f"{'▲' if r['2026'] > r['2025'] else '▼'} {abs(round((r['2026']-r['2025'])/r['2025']*100,1))}%"
                        if pd.notna(r.get('2025')) and pd.notna(r.get('2026')) and r['2025'] > 0 else '—', axis=1)
                    pivot['2025'] = pivot['2025'].apply(lambda x: f"USD {int(round(x)):,}" if pd.notna(x) else '—')
                    pivot['2026'] = pivot['2026'].apply(lambda x: f"USD {int(round(x)):,}" if pd.notna(x) else '—')
                    st.dataframe(pivot.rename(columns={'Mes':'Mes','2025':'Mediana 2025','2026':'Mediana 2026'}),
                                 use_container_width=True, hide_index=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 4 — GASTOS LOCALES
            # ═══════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(6,182,212,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#06b6d4; font-size:13px; font-weight:800; letter-spacing:5px;'>04 · GASTOS LOCALES ARG</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>VIGENTES HOY · COSTO EN DESTINO</span>
</div>""", unsafe_allow_html=True)

            df_loc = df_fl[(df_fl['_desde'] <= hoy) & (df_fl['_hasta'] >= hoy) & df_fl['_local'].notna()].copy()
            if df_loc.empty:
                ult_l = df_fl[df_fl['_local'].notna()]['_desde'].max()
                if pd.notna(ult_l):
                    df_loc = df_fl[(df_fl['_desde'] == ult_l) & df_fl['_local'].notna()].copy()

            if not df_loc.empty:
                med_loc = df_loc['_local'].median()
                min_loc = df_loc['_local'].min()
                max_loc = df_loc['_local'].max()
                ag_min_loc = df_loc.loc[df_loc['_local'].idxmin(), '_agente']
                ag_max_loc = df_loc.loc[df_loc['_local'].idxmax(), '_agente']

                lc1, lc2, lc3, lc4 = st.columns(4)
                for col_card, valor, label, color, sub in [
                    (lc1, f"USD {int(round(med_loc)):,}", "MEDIANA MERCADO", "#06b6d4", "referencia del mercado"),
                    (lc2, f"USD {int(round(min_loc)):,}", "MÁS BARATO", "#00ff88", ag_min_loc),
                    (lc3, f"USD {int(round(max_loc)):,}", "MÁS CARO", "#ff4b4b", ag_max_loc),
                    (lc4, f"USD {int(round(max_loc - min_loc)):,}", "DIFERENCIA MAX", "#ffaa00", "entre agentes"),
                ]:
                    col_card.markdown(f"""
<div style='text-align:center; padding:22px 12px;
background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); border-top:4px solid {color};'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 8px 0; text-transform:uppercase;'>{label}</p>
<p style='color:{color}; font-size:30px; font-weight:900; margin:0; line-height:1;'>{valor}</p>
<p style='color:#475569; font-size:10px; margin:6px 0 0 0;'>{sub}</p>
</div>""", unsafe_allow_html=True)

                # Ranking gastos locales
                st.markdown("<br>", unsafe_allow_html=True)
                ag_loc = df_loc.groupby('_agente')['_local'].median().reset_index()
                ag_loc.columns = ['Agente','Gasto Local']
                ag_loc = ag_loc.sort_values('Gasto Local').reset_index(drop=True)
                max_gl = ag_loc['Gasto Local'].max()

                for rank, (_, row) in enumerate(ag_loc.iterrows()):
                    pct_gl  = round(row['Gasto Local'] / max_gl * 100) if max_gl > 0 else 0
                    color_gl = '#00ff88' if rank == 0 else ('#ffaa00' if row['Gasto Local'] <= med_loc else '#ff4b4b')
                    dif_gl  = int(round(row['Gasto Local'] - ag_loc['Gasto Local'].iloc[0]))
                    dif_str = f"+USD {dif_gl:,} vs más barato" if dif_gl > 0 else "🏆 MÁS BARATO"
                    dif_col = '#ff4b4b' if dif_gl > 0 else '#00ff88'

                    st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:12px;
border:1px solid rgba(255,255,255,0.05); padding:14px 18px; margin-bottom:8px;
border-left:4px solid {color_gl};'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
    <div style='display:flex; align-items:center; gap:12px;'>
        <p style='color:#334155; font-size:18px; font-weight:900; margin:0; width:28px;'>#{rank+1}</p>
        <p style='color:#f8fafc; font-size:15px; font-weight:700; margin:0;'>{row['Agente']}</p>
    </div>
    <div style='text-align:right;'>
        <p style='color:{color_gl}; font-size:22px; font-weight:900; margin:0;'>USD {int(round(row["Gasto Local"])):,}</p>
        <p style='color:{dif_col}; font-size:10px; font-weight:700; margin:2px 0 0 0;'>{dif_str}</p>
    </div>
</div>
<div style='height:5px; background:rgba(255,255,255,0.05); border-radius:3px;'>
    <div style='height:5px; width:{pct_gl}%; background:{color_gl}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)
            else:
                st.info("No hay gastos locales disponibles para el período vigente.")

        except Exception as e:
            st.error(f"Error en Fletes y Gastos: {e}")
            import traceback
            st.code(traceback.format_exc())

    # --- SOLAPA 5: PROYECCIÓN SEMANAL ETD ---
    with tabs[5]:
        st.markdown("""
<div style='text-align:center; padding:25px; background:linear-gradient(135deg,rgba(0,168,255,0.08),rgba(0,255,136,0.04));
border-radius:20px; border:1px solid rgba(0,168,255,0.2); margin-bottom:30px;'>
<h2 style='color:#00a8ff; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>PROYECCIÓN SEMANAL ETD</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>CARGA MARÍTIMA ARGENTINA · PRÓXIMAS SEMANAS DE ZARPE</p>
</div>""", unsafe_allow_html=True)
        try:
            def find_col_proy(df, keywords):
                for kw in keywords:
                    matches = [c for c in df.columns if kw.upper() in str(c).upper()]
                    if matches: return matches[0]
                return None
            col_etd_proy    = find_col_proy(df, ['ETD']) or df.columns[23]
            col_mod_proy    = find_col_proy(df, ['MODALIDAD DE COSTEO', 'MODALIDAD COSTEO']) or df.columns[68]
            col_puerto_proy = find_col_proy(df, ['PUERTO DE SALIDA', 'PUERTO SALIDA', 'PUERTO']) or df.columns[41]
            col_pais_proy   = df.columns[18]

            df_proy = df.copy()
            df_proy['_m3'] = pd.to_numeric(df_proy['M3 Total'], errors='coerce').fillna(0)
            mask_pais = df_proy[col_pais_proy].astype(str).str.strip().str.upper() == 'ARGENTINA'
            mask_mod  = (
                df_proy[col_mod_proy].astype(str).str.strip().str.upper().str.startswith('BARCO') |
                df_proy[col_mod_proy].astype(str).str.strip().str.upper().str.contains('COSTO HIBRIDO PUERTO ZFLP', na=False)
            )
            df_proy = df_proy[mask_pais & mask_mod].copy()
            df_proy['_etd_dt'] = pd.to_datetime(df_proy[col_etd_proy], dayfirst=True, errors='coerce')
            df_proy = df_proy[df_proy['_etd_dt'].notna() & (df_proy['_etd_dt'] >= hoy)].copy()
            df_proy['_semana_inicio'] = df_proy['_etd_dt'].dt.to_period('W').apply(lambda p: p.start_time)
            df_proy['_mes_num']       = df_proy['_etd_dt'].dt.month
            df_proy['_mes_label']     = df_proy['_etd_dt'].dt.strftime('%B %Y').str.upper()
            df_proy['_puerto']        = df_proy[col_puerto_proy].astype(str).str.strip().str.upper().fillna('SIN DEFINIR')

            if df_proy.empty:
                st.warning("No hay carga futura proyectada.")
            else:
                meses_proy    = df_proy.drop_duplicates('_mes_num').sort_values('_mes_num')[['_mes_num','_mes_label']].values.tolist()
                opciones_proy = {lbl: num for num, lbl in meses_proy}
                mes_actual  = hoy.month
                default_lbl = next((lbl for lbl, num in opciones_proy.items() if num == mes_actual),
                                   list(opciones_proy.keys())[0])
                default_idx = list(opciones_proy.keys()).index(default_lbl)

                col_sp, _ = st.columns([2, 3])
                with col_sp:
                    mes_proy_lbl = st.selectbox("📅 SELECCIONAR MES:", list(opciones_proy.keys()),
                                                index=default_idx, key="proy_mes_sel")
                mes_proy_num = opciones_proy[mes_proy_lbl]
                df_mes = df_proy[df_proy['_mes_num'] == mes_proy_num].copy()

                total_m3   = df_mes['_m3'].sum()
                total_cntr = round(total_m3 / 60)
                total_so   = df_mes['SO'].nunique() if 'SO' in df_mes.columns else 0
                total_sem  = df_mes['_semana_inicio'].nunique()

                # ── KPI CARDS ──────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:linear-gradient(145deg,rgba(0,168,255,0.1),rgba(0,168,255,0.03));
border-radius:20px; border:1px solid rgba(0,168,255,0.2);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Contenedores estimados</p>
<p style='color:#00a8ff; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{int(total_cntr)}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>CNTRS 40\'HC · {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)
                with k2:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:linear-gradient(145deg,rgba(0,255,136,0.07),rgba(0,255,136,0.02));
border-radius:20px; border:1px solid rgba(0,255,136,0.15);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Volumen total</p>
<p style='color:#00ff88; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{int(round(total_m3)):,}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>M3 · {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)
                with k3:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:rgba(255,255,255,0.03); border-radius:20px; border:1px solid rgba(255,255,255,0.07);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Órdenes de compra</p>
<p style='color:#f8fafc; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{total_so}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>SOs con zarpe en {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)
                with k4:
                    st.markdown(f"""
<div style='text-align:center; padding:28px 16px;
background:rgba(255,255,255,0.03); border-radius:20px; border:1px solid rgba(255,255,255,0.07);'>
<p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 10px 0; text-transform:uppercase;'>Semanas activas</p>
<p style='color:#f8fafc; font-size:72px; font-weight:900; margin:0; line-height:1; letter-spacing:-3px;'>{total_sem}</p>
<p style='color:#475569; font-size:12px; margin:8px 0 0 0;'>Semanas con carga en {mes_proy_lbl}</p>
</div>""", unsafe_allow_html=True)

                # ── GRÁFICO: LÍNEA DE CONTENEDORES POR SEMANA ──────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='border-bottom:1px solid rgba(0,168,255,0.15); padding-bottom:8px; margin-bottom:24px;'>
<span style='color:#00a8ff; font-size:12px; font-weight:800; letter-spacing:4px; text-transform:uppercase;'>EVOLUCIÓN DE CONTENEDORES POR SEMANA</span>
<span style='color:#475569; font-size:11px; margin-left:14px;'>estimado: 1 contenedor = 60 M3</span>
</div>""", unsafe_allow_html=True)

                df_linea = df_mes.groupby('_semana_inicio')['_m3'].sum().reset_index()
                df_linea['Semana'] = df_linea['_semana_inicio'].apply(
                    lambda d: d.strftime('%d/%m') + ' — ' + (d + pd.Timedelta(days=6)).strftime('%d/%m')
                )
                df_linea['CNTRS'] = (df_linea['_m3'] / 60).round(0).astype(int)

                fig = px.line(
                    df_linea, x='Semana', y='CNTRS',
                    markers=True,
                    text='CNTRS',
                    labels={'CNTRS': 'Contenedores estimados', 'Semana': ''},
                )
                fig.update_traces(
                    line=dict(color='#00a8ff', width=3),
                    marker=dict(size=12, color='#00a8ff', line=dict(color='#ffffff', width=2)),
                    texttemplate='<b>%{text}</b> CNTR',
                    textposition='top center',
                    textfont=dict(size=13, color='#f8fafc', family='Outfit, sans-serif'),
                    fill='tozeroy',
                    fillcolor='rgba(0,168,255,0.08)',
                )
                fig.update_layout(
                    height=420,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=13),
                    showlegend=False,
                    xaxis=dict(
                        showgrid=False,
                        tickfont=dict(size=13, color='#94a3b8'),
                        title='',
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(255,255,255,0.07)',
                        title='Contenedores estimados',
                        tickfont=dict(size=12),
                        rangemode='tozero',
                    ),
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)

                # ── CARDS POR SEMANA (mismo tamaño fijo, números redondos) ──
                st.markdown("""
<div style='border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:8px; margin-bottom:24px;'>
<span style='color:#94a3b8; font-size:12px; font-weight:800; letter-spacing:4px; text-transform:uppercase;'>DESGLOSE POR SEMANA Y PUERTO</span>
</div>""", unsafe_allow_html=True)

                COLORES_PORTO = ['#00a8ff','#00ff88','#ffaa00','#ff4b4b','#a855f7','#06b6d4','#f97316']
                puertos_orden = df_mes.groupby('_puerto')['_m3'].sum().sort_values(ascending=False).index.tolist()
                semanas = sorted(df_mes['_semana_inicio'].unique())
                CARD_H = '320px'

                for fila_start in range(0, len(semanas), 4):
                    fila_sems = semanas[fila_start:fila_start+4]
                    # Siempre 4 columnas para coherencia
                    cols_fila = st.columns(4)
                    for idx in range(4):
                        with cols_fila[idx]:
                            if idx >= len(fila_sems):
                                # columna vacía para mantener alineación
                                st.markdown("<div></div>", unsafe_allow_html=True)
                                continue
                            sem = fila_sems[idx]
                            sem_fin   = sem + pd.Timedelta(days=6)
                            sem_label = sem.strftime('%d/%m') + ' AL ' + sem_fin.strftime('%d/%m')
                            df_sem    = df_mes[df_mes['_semana_inicio'] == sem]
                            m3_sem    = df_sem['_m3'].sum()
                            cntr_sem  = round(m3_sem / 60)   # entero
                            so_sem    = df_sem['SO'].nunique() if 'SO' in df_sem.columns else 0

                            puertos_html = ''
                            for pi, puerto in enumerate(puertos_orden):
                                m3_p = df_sem[df_sem['_puerto'] == puerto]['_m3'].sum()
                                if m3_p == 0: continue
                                pct_p  = round(m3_p / m3_sem * 100) if m3_sem > 0 else 0
                                cntr_p = round(m3_p / 60)   # entero
                                col_p  = COLORES_PORTO[pi % len(COLORES_PORTO)]
                                puertos_html += f"""
<div style='margin-bottom:9px;'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;'>
<p style='color:#94a3b8; font-size:10px; font-weight:600; margin:0;
white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:110px;'>{puerto}</p>
<p style='color:{col_p}; font-size:11px; font-weight:800; margin:0;'>{cntr_p} CNTR</p>
</div>
<div style='height:4px; background:rgba(255,255,255,0.06); border-radius:2px;'>
<div style='height:4px; width:{pct_p}%; background:{col_p}; border-radius:2px;'></div>
</div>
</div>"""

                            st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.08); padding:20px; margin-bottom:16px;
border-top:4px solid #00a8ff; height:{CARD_H}; box-sizing:border-box;
display:flex; flex-direction:column; justify-content:space-between;'>
<div>
    <p style='color:#00a8ff; font-size:11px; font-weight:800; letter-spacing:2px;
    margin:0 0 14px 0; text-transform:uppercase;'>📅 {sem_label}</p>
    <div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:14px;'>
        <div>
            <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>CONTENEDORES</p>
            <p style='color:#00a8ff; font-size:42px; font-weight:900; margin:0; line-height:1;'>{int(cntr_sem)}</p>
        </div>
        <div style='text-align:right;'>
            <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>M3</p>
            <p style='color:#f8fafc; font-size:20px; font-weight:700; margin:0; line-height:1;'>{int(round(m3_sem)):,}</p>
            <p style='color:#475569; font-size:10px; margin:4px 0 0 0;'>{so_sem} SOs</p>
        </div>
    </div>
</div>
<div style='border-top:1px solid rgba(255,255,255,0.06); padding-top:12px; flex:1; overflow:hidden;'>
{puertos_html}
</div>
</div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Proyeccion Semanal ETD: {e}")
            import traceback
            st.code(traceback.format_exc())

    # --- SOLAPA 6: INDICADORES (SLA & CONSOLIDACIÓN) ---
    with tabs[6]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 255, 136, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00ff88; font-weight:800; letter-spacing:5px; margin:0;'>INDICADORES DE CONSOLIDACIÓN Y SLA</h2><p style='color:#64748b; font-size:11px; letter-spacing:2px; margin:10px 0 0 0;'>📊 DÍAS MOSTRADOS: MEDIANA · SLA MONO: 15d (ene-feb) / 10d (resto) · SLA CONSOLIDADO: 25d</p></div>", unsafe_allow_html=True)
        try:
            url_hi = f"{base_url}/export?format=csv&gid=32771816&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_hi_vfinal(u): return pd.read_csv(u, engine='python')
            df_hi = load_hi_vfinal(url_hi)
            df_hi.columns = [str(c).strip() for c in df_hi.columns]
            df_hi['ETD_DT'] = pd.to_datetime(df_hi.iloc[:, 11], dayfirst=True, errors='coerce')
            mask_anio_etd = df_hi['ETD_DT'].dt.year == 2026
            mask_anio_col = df_hi.iloc[:, 25].astype(str).str.strip() == '2026'
            df_2026 = df_hi[mask_anio_etd | mask_anio_col].copy()
            df_2026.loc[df_2026['ETD_DT'].isna(), 'ETD_DT'] = pd.to_datetime(
                df_2026.loc[df_2026['ETD_DT'].isna(), df_hi.columns[11]], dayfirst=True, errors='coerce'
            )
            if not df_2026.empty:
                df_2026['Mes'] = df_2026['ETD_DT'].dt.month
                mask_sin_mes = df_2026['Mes'].isna()
                if mask_sin_mes.any():
                    df_2026.loc[mask_sin_mes, 'ETD_DT'] = pd.to_datetime(
                        df_2026.loc[mask_sin_mes, df_hi.columns[11]], dayfirst=True, errors='coerce'
                    )
                    df_2026.loc[mask_sin_mes, 'Mes'] = df_2026.loc[mask_sin_mes, 'ETD_DT'].dt.month
                df_2026 = df_2026[df_2026['Mes'].notna()].copy()
                df_2026['Mes'] = df_2026['Mes'].astype(int)
                col_tipo_carga_hi = df_hi.columns[5]
                df_mar = df_2026[~df_2026[col_tipo_carga_hi].astype(str).str.upper().str.contains('AVION|COURRIER', na=False)].copy()
                meses_dict = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
                df_mar['Mes_Nombre'] = df_mar['Mes'].map(meses_dict)
                col_mono_hi  = df_hi.columns[24]
                col_puerto_hi = df_hi.columns[4]
                col_cons_hi  = df_hi.columns[32]
                def clean_n_hi(val):
                    if pd.isna(val) or str(val).strip() in ['', 'nan']: return 0.0
                    try:
                        s = str(val).replace(',', '.').replace(' ', '').strip()
                        return pd.to_numeric(s, errors='coerce')
                    except: return 0.0
                df_mar[col_cons_hi] = df_mar[col_cons_hi].apply(clean_n_hi).fillna(0.0).round(0)
                @st.dialog("🚢 DETALLE POR PUERTO Y SLA", width="large")
                def show_detalle_mes(df_sub, mes_lbl, mode="mixed"):
                    st.markdown(f"### Análisis {mes_lbl.upper()}")
                    res_p = df_sub.groupby(col_puerto_hi).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                    p_rows = []
                    for _, r in res_p.iterrows():
                        df_p_t = df_sub[df_sub[col_puerto_hi] == r[col_puerto_hi]].copy()
                        tp_p = r[df_hi.columns[0]]
                        def check_sla(row):
                            days = row[col_cons_hi]
                            is_mono = "MONOPROVEEDOR" in str(row[col_mono_hi]).upper()
                            try:
                                mes_num = int(row['Mes'])
                            except:
                                mes_num = 3
                            limit = (15 if mes_num <= 2 else 10) if is_mono else 25
                            return days <= limit
                        df_p_t['SLA_OK'] = df_p_t.apply(check_sla, axis=1)
                        pct_sla = int((len(df_p_t[df_p_t['SLA_OK']]) / tp_p) * 100) if tp_p > 0 else 0
                        row_data = {"Puerto": r[col_puerto_hi], "Embs": tp_p, "Días Avg": int(round(r[col_cons_hi])), "% Cumple SLA": f"{pct_sla}%", "% Fuera SLA": f"{100 - pct_sla}%", "TOTAL": "100%"}
                        if mode == "mixed":
                            cm_p = len(df_p_t[df_p_t[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)])
                            row_data["% Mono"] = f"{int((cm_p/tp_p)*100)}%"
                            row_data["% Cons"] = f"{int((1-(cm_p/tp_p))*100)}%"
                        p_rows.append(row_data)
                    st.dataframe(pd.DataFrame(p_rows).sort_values("Embs", ascending=False), use_container_width=True, hide_index=True)
                st.markdown("<div style='background: rgba(0, 168, 255, 0.05); padding: 15px 25px; border-radius: 20px; border: 1px solid rgba(0, 168, 255, 0.2); margin: 15px 0;'><h3 style='color:#00a8ff; margin:0; text-align:center; letter-spacing:5px; text-transform:uppercase; font-weight:900;'>RESUMEN MES CERRADO (MARÍTIMOS 2026)</h3></div>", unsafe_allow_html=True)
                thc = st.columns([1.5, 1, 1.2, 1, 1, 0.8])
                for i, h in enumerate(["MES ETD", "EMBS", "MEDIANA", "% MONO", "% CONS", "DETALLE"]):
                    thc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                res_mensual = df_mar.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                for _, row in res_mensual.iterrows():
                    df_m_temp = df_mar[df_mar['Mes'] == row['Mes']].copy()
                    tot_m = len(df_m_temp)
                    df_m_mono = df_m_temp[df_m_temp[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)]
                    p_mono = (len(df_m_mono) / tot_m) if tot_m > 0 else 0
                    tr1, tr2, tr3, tr4, tr5, tr6 = st.columns([1.5, 1, 1.2, 1, 1, 0.8])
                    tr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center; margin-top:5px;'>{row['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                    tr2.markdown(f"<p style='text-align:center; margin-top:5px;'>{tot_m}</p>", unsafe_allow_html=True)
                    tr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center; margin-top:5px;'>{int(round(row[col_cons_hi]))}d</p>", unsafe_allow_html=True)
                    tr4.markdown(f"<p style='color:#00a8ff; text-align:center; margin-top:5px;'>{int(p_mono*100)}%</p>", unsafe_allow_html=True)
                    tr5.markdown(f"<p style='color:#94a3b8; text-align:center; margin-top:5px;'>{int((1-p_mono)*100)}%</p>", unsafe_allow_html=True)
                    with tr6:
                        if st.button("🔍 VER", key=f"btn_res_{row['Mes']}", use_container_width=True):
                            show_detalle_mes(df_m_temp, row['Mes_Nombre'], mode="mixed")
                st.markdown("<br><div style='background: rgba(0, 168, 255, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #00a8ff; margin-bottom:15px;'><h4 style='color:#00a8ff; margin:0; letter-spacing:2px; font-size:16px;'>1. SOLAMENTE MONOPROVEEDOR (MARÍTIMOS 2026)</h4></div>", unsafe_allow_html=True)
                df_mono_v4 = df_mar[df_mar[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)].copy()
                if not df_mono_v4.empty:
                    mhc = st.columns([1.5, 1, 1.2, 2, 0.8])
                    for i, h in enumerate(["MES ETD", "EMBS", "MEDIANA", "CUMPLIMIENTO SLA", "DETALLE"]):
                        mhc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                    res_m = df_mono_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                    for _, rm in res_m.iterrows():
                        df_sub_m = df_mono_v4[df_mono_v4['Mes'] == rm['Mes']].copy()
                        lim_m = 15 if rm['Mes'] <= 2 else 10
                        pct_m = int((len(df_sub_m[df_sub_m[col_cons_hi] <= lim_m]) / len(df_sub_m)) * 100) if len(df_sub_m) > 0 else 0
                        mr1, mr2, mr3, mr4, mr5 = st.columns([1.5, 1, 1.2, 2, 0.8])
                        mr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center;'>{rm['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                        mr2.markdown(f"<p style='text-align:center;'>{int(rm.iloc[2])}</p>", unsafe_allow_html=True)
                        mr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center;'>{int(round(rm.iloc[3]))}d</p>", unsafe_allow_html=True)
                        mr4.markdown(f"<div style='background:rgba(0,168,255,0.1); border-radius:10px; text-align:center; padding:2px; border:1px solid rgba(0,168,255,0.2);'><span style='color:#00a8ff; font-weight:800; font-size:12px;'>SLA {pct_m}%</span></div>", unsafe_allow_html=True)
                        with mr5:
                            if st.button("🔍 VER", key=f"btn_m_v4_{rm['Mes']}", use_container_width=True):
                                show_detalle_mes(df_sub_m, f"MONO - {rm['Mes_Nombre']}", mode="specific")
                st.markdown("<br><div style='background: rgba(0, 255, 136, 0.05); padding: 15px; border-radius: 12px; border-left: 5px solid #00ff88; margin-bottom:15px;'><h4 style='color:#00ff88; margin:0; letter-spacing:2px; font-size:16px;'>2. SOLAMENTE CONSOLIDADO (MARÍTIMOS 2026)</h4></div>", unsafe_allow_html=True)
                df_cons_v4 = df_mar[~df_mar[col_mono_hi].astype(str).str.upper().str.contains('MONOPROVEEDOR', na=False)].copy()
                if not df_cons_v4.empty:
                    chc = st.columns([1.5, 1, 1.2, 2, 0.8])
                    for i, h in enumerate(["MES ETD", "EMBS", "MEDIANA", "CUMPLIMIENTO SLA", "DETALLE"]):
                        chc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                    res_c = df_cons_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'median'}).reset_index()
                    for _, rc in res_c.iterrows():
                        df_sub_c = df_cons_v4[df_cons_v4['Mes'] == rc['Mes']].copy()
                        pct_c = int((len(df_sub_c[df_sub_c[col_cons_hi] <= 25]) / len(df_sub_c)) * 100) if len(df_sub_c) > 0 else 0
                        cr1, cr2, cr3, cr4, cr5 = st.columns([1.5, 1, 1.2, 2, 0.8])
                        cr1.markdown(f"<p style='font-weight:700; color:#fff; text-align:center;'>{rc['Mes_Nombre'].upper()}</p>", unsafe_allow_html=True)
                        cr2.markdown(f"<p style='text-align:center;'>{int(rc.iloc[2])}</p>", unsafe_allow_html=True)
                        cr3.markdown(f"<p style='color:#00ff88; font-weight:700; text-align:center;'>{int(round(rc.iloc[3]))}d</p>", unsafe_allow_html=True)
                        cr4.markdown(f"<div style='background:rgba(0,255,136,0.1); border-radius:10px; text-align:center; padding:2px; border:1px solid rgba(0,255,136,0.2);'><span style='color:#00ff88; font-weight:800; font-size:12px;'>SLA {pct_c}%</span></div>", unsafe_allow_html=True)
                        with cr5:
                            if st.button("🔍 VER", key=f"btn_c_v4_{rc['Mes']}", use_container_width=True):
                                show_detalle_mes(df_sub_c, f"CONS - {rc['Mes_Nombre']}", mode="specific")
            else:
                st.warning("No se encontraron registros marítimos para el año 2026.")
        except Exception as e:
            st.error(f"Error en Indicadores: {e}")
    # --- SOLAPA 8: ASK COMEX ---
    with tabs[7]:
        st.markdown("<div style='text-align:center; padding: 40px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; border: 2px dashed rgba(0, 168, 255, 0.2);'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:10px;'>ASK COMEX</h2><p style='color:#94a3b8; font-size:18px; margin-top:20px;'>Inteligencia Operativa en Tiempo Real.</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            with st.popover("💬 Hablar con Capitán Comex (IA)", use_container_width=False):
                st.markdown("<h4 style='color:#00ff88; margin-bottom:0;'>🚢 Capitán Comex</h4>", unsafe_allow_html=True)
                st.caption("Asistente Logístico con IA (Google Gemini)")
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = [{"role": "assistant", "content": "¡Hola! Soy Capitán Comex. ¿Qué embarque buscamos o qué duda operativa tienes?"}]
                chat_container = st.container(height=400)
                with chat_container:
                    for msg in st.session_state.chat_history:
                        avatar = "🚢" if msg["role"] == "assistant" else "👤"
                        with st.chat_message(msg["role"], avatar=avatar):
                            st.markdown(msg["content"])
                if prompt := st.chat_input("Hazle una pregunta a la IA..."):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    with chat_container:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(prompt)
                        with st.chat_message("assistant", avatar="🚢"):
                            resp_placeholder = st.empty()
                            resp_placeholder.markdown("Pensando... ⏳")
                            try:
                                respuesta_ia = "🚧 Estamos trabajando en esta funcionalidad. Volvé a intentarlo pronto."
                            except Exception as e:
                                respuesta_ia = "🚧 Estamos trabajando en esta funcionalidad. Volvé a intentarlo pronto."
                            resp_placeholder.markdown(respuesta_ia)
                            st.session_state.chat_history.append({"role": "assistant", "content": respuesta_ia})
        except AttributeError:
            st.error("⚠️ Para usar este chat flotante, necesitamos actualizar Streamlit. (Requiere versión 1.33 o superior).")
        st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
        @st.cache_data(ttl=60)
        def load_ask_comex_data():
            url_reserva = f"{base_url}/export?format=csv&gid=276804813"
            url_hist = f"{base_url}/export?format=csv&gid=32771816"
            url_emb_hist = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=50628730"
            url_ddp   = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=2050674215"
            url_impo2 = "https://docs.google.com/spreadsheets/d/1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI/export?format=csv&gid=131563120"
            try: res = pd.read_csv(url_reserva, engine='python', on_bad_lines='skip')
            except: res = pd.DataFrame()
            try: hi = pd.read_csv(url_hist, engine='python', on_bad_lines='skip')
            except: hi = pd.DataFrame()
            try: emb_hi = pd.read_csv(url_emb_hist, engine='python', on_bad_lines='skip')
            except: emb_hi = pd.DataFrame()
            try: ddp = pd.read_csv(url_ddp, engine='python', on_bad_lines='skip')
            except: ddp = pd.DataFrame()
            try: impo2 = pd.read_csv(url_impo2, engine='python', on_bad_lines='skip')
            except: impo2 = pd.DataFrame()
            return res, hi, emb_hi, ddp, impo2
        df_res_ask, df_hi_ask, df_emb_hi_ask, df_ddp_ask, df_impo2_ask = load_ask_comex_data()
        if not df_ddp_ask.empty:
            df_ddp_ask.columns = [str(c).strip() for c in df_ddp_ask.columns]
            df_ddp_ask['_emb_key'] = df_ddp_ask.iloc[:, 5].astype(str).str.strip().str.upper()
        if not df_impo2_ask.empty:
            df_impo2_ask.columns = [str(c).strip() for c in df_impo2_ask.columns]
            df_impo2_ask['_emb_key'] = df_impo2_ask.iloc[:, 0].astype(str).str.strip().str.upper()
        st.markdown("<br>", unsafe_allow_html=True)
        def get_estadio_impo2(emb, eta_str, df_impo2, hoy_d, historico=False):
            suffix = " (HISTORICO)" if historico else ""
            def es_vacio(v): return str(v).strip().lower() in ['', 'nan', 'none', '-', 'n/a']
            if df_impo2.empty:
                return 5, "EN PROCESO DE NACIONALIZACION" + suffix, "#ffaa00", "Carga arribada. Sin informacion de despacho aun. (ETA: " + str(eta_str) + ")"
            emb_key = str(emb).strip().upper()
            match = df_impo2[df_impo2['_emb_key'] == emb_key]
            if match.empty:
                return 5, "EN PROCESO DE NACIONALIZACION" + suffix, "#ffaa00", "Carga arribada. Sin registro en Despachos Directo Puerto aun."
            row_i = match.iloc[0]
            val_orden    = str(row_i.iloc[0]).strip() if len(row_i) > 0 else ""
            val_retiro   = str(row_i.iloc[1]).strip() if len(row_i) > 1 else ""
            val_ofi      = str(row_i.iloc[3]).strip() if len(row_i) > 3 else ""
            val_despacho = str(row_i.iloc[4]).strip() if len(row_i) > 4 else ""
            try:
                dt_retiro = pd.to_datetime(val_retiro, dayfirst=True).date()
                retiro_cumplido = dt_retiro <= hoy_d
            except:
                dt_retiro = None
                retiro_cumplido = False
            orden_txt    = (" | Orden WMS: " + val_orden)     if not es_vacio(val_orden)    else ""
            despacho_txt = (" | N Despacho: " + val_despacho) if not es_vacio(val_despacho) else ""
            ofi_txt      = (" | Fecha OFI: " + val_ofi)       if not es_vacio(val_ofi)      else ""
            retiro_txt   = (" | Retiro: " + val_retiro)        if not es_vacio(val_retiro)   else ""
            if not es_vacio(val_retiro) and retiro_cumplido:
                return 7, "ENTREGADO EN DEPOSITO", "#00ff88", "Carga retirada y entregada al deposito." + orden_txt + despacho_txt + ofi_txt + retiro_txt
            elif not es_vacio(val_retiro) and not retiro_cumplido:
                return 6, "NACIONALIZADO / RETIRO COORDINADO", "#a855f7", "Despacho oficializado. Retiro coordinado para: " + val_retiro + "." + orden_txt + despacho_txt + ofi_txt
            elif not es_vacio(val_ofi):
                return 6, "NACIONALIZADO / COORDINANDO RETIRO", "#a855f7", "Despacho oficializado el " + val_ofi + ". Pendiente coordinar retiro." + orden_txt + despacho_txt
            else:
                return 5, "EN PROCESO DE NACIONALIZACION" + suffix, "#ffaa00", "Carga arribada. Pendiente de oficializacion del despacho." + orden_txt
        query = st.text_input("🔍 INGRESE SO O N° DE EMBARQUE:", placeholder="Ej: SO-12345 o EMB-999...")
        if query:
            query = str(query).strip().upper()
            col_so         = [c for c in df.columns if c.strip().upper() == 'SO'][0] if any(c.strip().upper() == 'SO' for c in df.columns) else df.columns[0]
            col_emb_pc     = df.columns[16]
            is_historical = False
            df_found = pd.DataFrame()
            mask_so  = df[col_so].astype(str).str.upper().str.contains(query, na=False)
            mask_emb_pc = df[col_emb_pc].astype(str).str.strip().str.upper() == query
            df_found = df[mask_so | mask_emb_pc]
            if df_found.empty and not df_emb_hi_ask.empty:
                col_eh_emb = df_emb_hi_ask.columns[4]
                col_eh_so  = df_emb_hi_ask.columns[0]
                m_emb = df_emb_hi_ask[col_eh_emb].astype(str).str.strip().str.upper() == query
                m_so  = df_emb_hi_ask[col_eh_so].astype(str).str.upper().str.contains(query, na=False)
                df_found = df_emb_hi_ask[m_emb | m_so]
                if not df_found.empty: is_historical = True
            if df_found.empty:
                st.warning(f"No se encontraron registros para '{query}'.")
                st.info("Verificá que el SO o número de embarque esté exactamente como aparece en el sistema (ej: FCL 2050, AIR 152).")
            else:
                origen = "Embarques Históricos" if is_historical else "Planif Cargas"
                st.success(f"✅ Registro encontrado — {len(df_found)} coincidencias en {origen}")
                if len(df_found) > 50:
                    st.warning(f"⚠️ Se encontraron {len(df_found)} resultados. Procesando los primeros 50.")
                    df_found = df_found.head(50)
                resultados_procesados = []
                for i, row in df_found.iterrows():
                    if is_historical:
                        val_so  = str(row.iloc[0]).strip()
                        val_sku = str(row.iloc[5]).strip() if len(row) > 5 else "—"
                        val_inv = str(row.iloc[17]).strip() if len(row) > 17 else "—"
                        if val_sku.lower() in ["nan","none",""]: val_sku = "—"
                        if val_inv.lower() in ["nan","none",""]: val_inv = "—"
                        val_emb = str(row.iloc[4]).strip()
                        if val_emb.lower() in ['nan', 'none', '']: val_emb = "Sin Asignar"
                        val_prov = str(row.iloc[18])
                        val_etd_gso = str(row.iloc[6]).strip(); val_eta_gso = str(row.iloc[7]).strip()
                        val_fin_prod = str(row.iloc[2]).strip()
                        if val_fin_prod.lower() == 'nan' or val_fin_prod == '': val_fin_prod = "Sin Info"
                        try: val_cant_emb = float(str(row.iloc[9]).replace(',', '.').strip())
                        except: val_cant_emb = 0.0
                        cantidad_mostrar = int(val_cant_emb); label_cant = "CANTIDAD EMB"
                        val_fecha_inst = "Pendiente"
                        if not df_hi_ask.empty and len(df_hi_ask.columns) > 7:
                            col_hi_emb = df_hi_ask.columns[0]
                            hi_match = df_hi_ask[df_hi_ask[col_hi_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                            if not hi_match.empty:
                                val_f = str(hi_match.iloc[0].iloc[7]).strip()
                                if val_f.lower() != 'nan' and val_f != '': val_fecha_inst = val_f
                        hoy_d = datetime.now().date()
                        try:
                            dt_eta_parsed = pd.to_datetime(val_eta_gso, dayfirst=True)
                            dt_eta = dt_eta_parsed.date() if pd.notna(dt_eta_parsed) else None
                        except: dt_eta = None
                        if dt_eta is not None and dt_eta < hoy_d:
                            estadio_ddp, desc_ddp, color_ddp, info_ddp = get_estadio_impo2(val_emb, val_eta_gso, df_ddp_ask, hoy_d, historico=True)
                            if estadio_ddp == 5:
                                estadio = 6; desc_estadio = "ARRIBADO (HISTORICO)"; color_estadio = "#00ff88"
                                info_extra = "La carga ha llegado a destino. Pendiente proceso de aduana. ETA: " + str(val_eta_gso)
                            else:
                                estadio = estadio_ddp + 1
                                desc_estadio = desc_ddp; color_estadio = color_ddp; info_extra = info_ddp
                        else:
                            estadio = 4; desc_estadio = "EN TRÁNSITO (HISTÓRICO)"; color_estadio = "#00a8ff"
                            info_extra = f"La carga figura despachada en registros históricos pero su ETA es futura. (ETA: {val_eta_gso})"
                        etd_display = val_etd_gso if val_etd_gso and str(val_etd_gso).lower() not in ["nan","none",""] else "Sin fecha"
                        eta_display = val_eta_gso if val_eta_gso and str(val_eta_gso).lower() not in ["nan","none",""] else "Sin fecha"
                    else:
                        val_so  = str(row[col_so]).strip()
                        val_sku = str(row[df.columns[32]]).strip() if len(df.columns) > 32 else ""
                        val_inv = str(row[df.columns[29]]).strip() if len(df.columns) > 29 else ""
                        if val_sku.lower() in ["nan","none",""]: val_sku = "—"
                        if val_inv.lower() in ["nan","none",""]: val_inv = "—"
                        col_prov = [c for c in df.columns if 'PROVEEDOR' in c.upper()][0] if any('PROVEEDOR' in c.upper() for c in df.columns) else df.columns[30]
                        val_prov = str(row[col_prov])
                        col_emb = [c for c in df.columns if 'EMBARQUE' in c.upper()][0] if any('EMBARQUE' in c.upper() for c in df.columns) else df.columns[16]
                        val_emb = str(row[col_emb]).strip()
                        if val_emb.lower() == 'nan': val_emb = "Sin Asignar"
                        col_inst = [c for c in df.columns if 'INSTRUCCION' in c.upper() or 'INSTRUCCIÓN' in c.upper()][0] if any('INSTRUCCION' in c.upper() or 'INSTRUCCIÓN' in c.upper() for c in df.columns) else df.columns[20]
                        val_inst = str(row[col_inst]).strip()
                        col_fin_prod = df.columns[99]
                        val_fin_prod = str(row[col_fin_prod]).strip()
                        if val_fin_prod.lower() == 'nan' or val_fin_prod == '': val_fin_prod = "Sin Info"
                        val_fecha_inst = val_inst if (val_inst != "" and val_inst.lower() != "nan" and "sin instruccion" not in val_inst.lower()) else "Pendiente"
                        val_etd_gso = str(row[df.columns[23]]).strip()
                        val_eta_gso = str(row[df.columns[24]]).strip()
                        col_cant_pend = [c for c in df.columns if 'CANTIDAD PENDIENTE DE EMBARCAR' in c.upper()][0] if any('CANTIDAD PENDIENTE DE EMBARCAR' in c.upper() for c in df.columns) else df.columns[21]
                        col_cant_emb = [c for c in df.columns if 'CANTIDAD EMB' in c.upper() and 'PREVENTA' not in c.upper()][0] if any('CANTIDAD EMB' in c.upper() and 'PREVENTA' not in c.upper() for c in df.columns) else df.columns[60]
                        try: val_cant_pend = float(str(row[col_cant_pend]).replace(',', '.').strip())
                        except: val_cant_pend = 0.0
                        try: val_cant_emb = float(str(row[col_cant_emb]).replace(',', '.').strip())
                        except: val_cant_emb = 0.0
                        if val_cant_pend == 0:
                            cantidad_mostrar = int(val_cant_emb); label_cant = "CANTIDAD EMB"
                        else:
                            cantidad_mostrar = int(val_cant_pend); label_cant = "CANT. PENDIENTE"
                        col_etd_ok_ask = next((c for c in df.columns if "ETD OK FFWW" in str(c).upper() or "ETD OK" in str(c).upper()), df.columns[97])
                        val_etd_ok = str(row[col_etd_ok_ask]).strip().upper() if col_etd_ok_ask in df.columns else ""
                        hoy_d = datetime.now().date()
                        try:
                            _p = pd.to_datetime(val_eta_gso, dayfirst=True)
                            dt_eta_gso = _p.date() if pd.notna(_p) else None
                        except: dt_eta_gso = None
                        try:
                            _p = pd.to_datetime(val_etd_gso, dayfirst=True)
                            dt_etd_gso = _p.date() if pd.notna(_p) else None
                        except: dt_etd_gso = None
                        in_historical = False
                        if not df_hi_ask.empty:
                            df_hi_ask.columns = df_hi_ask.columns.str.strip()
                            col_hi_emb = df_hi_ask.columns[0]
                            hi_match = df_hi_ask[df_hi_ask[col_hi_emb].astype(str).str.strip().str.upper() == val_emb.upper()]
                            if not hi_match.empty: in_historical = True
                        tiene_emb  = val_emb not in ["Sin Asignar", "", "nan", "NAN"]
                        tiene_inst = val_fecha_inst != "Pendiente"
                        etd_ok     = val_etd_ok == "OK"
                        etd_display = val_etd_gso if val_etd_gso and str(val_etd_gso).lower() not in ["nan","none",""] else "Sin fecha"
                        eta_display = val_eta_gso if val_eta_gso and str(val_eta_gso).lower() not in ["nan","none",""] else "Sin fecha"
                        f_salida_origen = ""; f_arribo_aduana = ""
                        if not df_impo2_ask.empty and val_emb not in ["Sin Asignar","","nan","NAN"]:
                            impo2_match = df_impo2_ask[df_impo2_ask["_emb_key"] == val_emb.upper()]
                            if not impo2_match.empty:
                                f_salida_origen = str(impo2_match.iloc[0].iloc[1]).strip()
                                f_arribo_aduana = str(impo2_match.iloc[0].iloc[2]).strip()
                                if f_salida_origen.lower() in ["nan","none",""]: f_salida_origen = ""
                                if f_arribo_aduana.lower() in ["nan","none",""]: f_arribo_aduana = ""
                        if in_historical or (dt_eta_gso and dt_eta_gso <= hoy_d):
                            estadio_ddp, desc_ddp, color_ddp, info_ddp = get_estadio_impo2(val_emb, val_eta_gso, df_ddp_ask, hoy_d, historico=False)
                            if estadio_ddp == 5:
                                estadio = 6; desc_estadio = "ARRIBADO"; color_estadio = "#00ff88"
                                arribo_txt = " | Arribo a aduana: " + f_arribo_aduana if f_arribo_aduana else ""
                                info_extra = "La carga ha llegado a destino. ETA: " + eta_display + arribo_txt
                            else:
                                estadio = estadio_ddp + 1
                                desc_estadio = desc_ddp; color_estadio = color_ddp; info_extra = info_ddp
                        elif dt_etd_gso and dt_etd_gso <= hoy_d and etd_ok:
                            estadio = 5; desc_estadio = "EN TRANSITO"; color_estadio = "#00a8ff"
                            salida_txt = " | Salida origen: " + f_salida_origen if f_salida_origen else ""
                            arribo_txt = " | Arribo estimado aduana: " + f_arribo_aduana if f_arribo_aduana else " | ETA: " + eta_display
                            info_extra = "La carga esta navegando. ETD: " + (dt_etd_gso.strftime("%d/%m/%Y") if dt_etd_gso else "SD") + salida_txt + arribo_txt
                        elif etd_ok and (not dt_etd_gso or dt_etd_gso > hoy_d):
                            estadio = 4; desc_estadio = "BOOKING CONFIRMADO"; color_estadio = "#a855f7"
                            info_extra = "Espacio confirmado. Esperando zarpada. ETD: " + etd_display + " | ETA estimada: " + eta_display
                        elif tiene_inst and not etd_ok:
                            estadio = 3; desc_estadio = "INSTRUCCION ENVIADA - ESPERA BOOKING"; color_estadio = "#ffaa00"
                            info_extra = "Instruccion enviada el " + val_inst + ". Esperando confirmacion de booking. ETA estimada: " + eta_display
                        elif tiene_emb and not tiene_inst:
                            estadio = 2; desc_estadio = "EN PROCESO DE CONSOLIDACION"; color_estadio = "#06b6d4"
                            info_extra = "SO asignado al embarque " + val_emb + ". Pendiente de instruccion al agente."
                        else:
                            estadio = 1; desc_estadio = "PENDIENTE DE INSTRUCCION"; color_estadio = "#94a3b8"
                            info_extra = "Sin embarque asignado. Carga en origen sin gestion iniciada."
                    resultados_procesados.append({
                        "estadio": estadio, "desc_estadio": desc_estadio, "color_estadio": color_estadio,
                        "info_extra": info_extra, "so": val_so, "inv": val_inv, "sku": val_sku,
                        "emb": val_emb, "prov": val_prov, "cant": cantidad_mostrar,
                        "label_cant": label_cant, "fecha_inst": val_fecha_inst, "fin_prod": val_fin_prod,
                        "etd": etd_display, "eta": eta_display
                    })
                st.session_state.ultimos_resultados = resultados_procesados
                st.success(f"📌 {len(resultados_procesados)} SO(s) encontrados.")
                for r in resultados_procesados:
                    etd_val = r.get('etd', 'Sin fecha')
                    eta_val = r.get('eta', 'Sin fecha')
                    c_est   = r['color_estadio']
                    st.markdown(
                        "<div class='custom-card' style='border-top:5px solid " + c_est + ";'>"
                        "<h3 style='color:" + c_est + "; text-transform:uppercase; letter-spacing:2px; margin-bottom:10px;'>"
                        "ESTADIO " + str(r['estadio']) + ": " + r['desc_estadio'] + "</h3>"
                        "<p style='color:#f8fafc; font-size:14px; margin-bottom:15px;'>" + r['info_extra'] + "</p>"
                        "<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:15px 0;'>"
                        "<div class='grid-4' style='align-items:start;'>"
                        "<div><p class='minicard-title'>SO</p><p style='font-size:18px; font-weight:700; color:#f8fafc; margin:0;'>" + r['so'] + "</p></div>"
                        "<div><p class='minicard-title'>EMBARQUE</p><p style='font-size:18px; font-weight:700; color:#00a8ff; margin:0;'>" + r['emb'] + "</p></div>"
                        "<div><p class='minicard-title'>SKU / CÓDIGO</p><p style='font-size:16px; font-weight:600; color:#f8fafc; margin:0;'>" + r['sku'] + "</p></div>"
                        "<div><p class='minicard-title'>N° INVOICE</p><p style='font-size:16px; font-weight:600; color:#f8fafc; margin:0;'>" + r['inv'] + "</p></div>"
                        "</div>"
                        "<div class='grid-4' style='margin-top:15px; padding-top:15px; border-top:1px dashed rgba(255,255,255,0.1);'>"
                        "<div><p class='minicard-title'>ETD</p><p style='font-size:15px; color:#ffaa00; margin:0;'>" + etd_val + "</p></div>"
                        "<div><p class='minicard-title'>ETA</p><p style='font-size:15px; color:#00a8ff; margin:0;'>" + eta_val + "</p></div>"
                        "<div><p class='minicard-title'>F. INSTRUCCION</p><p style='font-size:15px; color:#f8fafc; margin:0;'>" + r['fecha_inst'] + "</p></div>"
                        "<div><p class='minicard-title'>FIN PRODUCCION</p><p style='font-size:15px; color:#f8fafc; margin:0;'>" + r['fin_prod'] + "</p></div>"
                        "</div>"
                        "<div class='grid-4' style='margin-top:15px; padding-top:15px; border-top:1px dashed rgba(255,255,255,0.1);'>"
                        "<div><p class='minicard-title'>PROVEEDOR</p><p style='font-size:14px; color:#f8fafc; margin:0; font-weight:600;'>" + r['prov'] + "</p></div>"
                        "<div><p class='minicard-title'>TOTAL " + r['label_cant'] + "</p><p style='font-size:24px; color:#00ff88; font-weight:900; margin:0;'>" + str(r['cant']) + "</p></div>"
                        "<div></div><div></div>"
                        "</div></div>",
                        unsafe_allow_html=True
                    )
                    pct_p = round(r['estadio'] / 8 * 100)
                    c1 = '#fff' if r['estadio'] >= 1 else '#64748b'
                    c2 = '#fff' if r['estadio'] >= 2 else '#64748b'
                    c3 = '#fff' if r['estadio'] >= 3 else '#64748b'
                    c4 = '#fff' if r['estadio'] >= 4 else '#64748b'
                    c5 = '#fff' if r['estadio'] >= 5 else '#64748b'
                    c6 = '#fff' if r['estadio'] >= 6 else '#64748b'
                    c7 = '#fff' if r['estadio'] >= 7 else '#64748b'
                    c8 = '#fff' if r['estadio'] >= 8 else '#64748b'
                    st.markdown(
                        "<div style='width:100%; background-color:rgba(255,255,255,0.1); border-radius:10px; margin-top:15px; height:10px;'>"
                        "<div style='width:" + str(pct_p) + "%; background-color:" + c_est + "; height:10px; border-radius:10px;'></div></div>"
                        "<div style='display:flex; justify-content:space-between; margin-top:8px; padding:0 5px;'>"
                        "<span style='font-size:9px; font-weight:700; color:" + c1 + ";'>1.PENDIENTE</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c2 + ";'>2.CONSOLID.</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c3 + ";'>3.INSTRUC.</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c4 + ";'>4.BOOKING</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c5 + ";'>5.TRANSITO</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c6 + ";'>6.ARRIBADO</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c7 + ";'>7.NACIONALIZ.</span>"
                        "<span style='font-size:9px; font-weight:700; color:" + c8 + ";'>8.ENTREGADO</span>"
                        "</div><br>",
                        unsafe_allow_html=True
                    )
except Exception as e:
    st.error(f"Error general al cargar el dashboard: {e}")
    import traceback
    st.code(traceback.format_exc())
    # --- SOLAPA 4: FLETES & GASTOS LOCALES ---
    with tabs[4]:
        try:
            SHEET_URL   = "https://docs.google.com/spreadsheets/d/1UJ1bDyDQdIQSSVQ6dyChVKbMX1d69G68ji_dpsOzfHg"
            POD_EXCLUIR = ['LÁZARO CÁRDENAS','LAZARO CARDENAS','MANZANILLO',
                           'MANZANILLO / LAZARO CARDENAS','MONTEVIDEO',
                           'MONTEVIDEO/SANTOS','MVD/SSZ','SANTOS','URUGUAY']

            @st.cache_data(ttl=300)
            def load_fletes_v2(url):
                df_f = pd.read_csv(f"{url}/export?format=csv&gid=0", header=0, dtype=str, on_bad_lines='skip')
                df_f.columns = [str(c).strip() for c in df_f.columns]
                return df_f

            df_fl = load_fletes_v2(SHEET_URL)

            def parse_usd(v):
                try:
                    s = str(v).replace('USD','').replace('$','').replace(' ','').strip()
                    return float(s.replace('.','').replace(',','.'))
                except: return None

            col_agente  = df_fl.columns[1]
            col_pod     = df_fl.columns[8]
            col_flete   = df_fl.columns[3]
            col_desde   = df_fl.columns[10]
            col_hasta   = df_fl.columns[11]
            col_local   = df_fl.columns[14]
            col_cnt     = df_fl.columns[15]

            df_fl['_desde']  = pd.to_datetime(df_fl[col_desde], dayfirst=True, errors='coerce')
            df_fl['_hasta']  = pd.to_datetime(df_fl[col_hasta], dayfirst=True, errors='coerce')
            df_fl['_flete']  = df_fl[col_flete].apply(parse_usd)
            df_fl['_local']  = df_fl[col_local].apply(parse_usd)
            df_fl['_cnt']    = df_fl[col_cnt].astype(str).str.strip().str.upper()
            df_fl['_agente'] = df_fl[col_agente].astype(str).str.strip()
            df_fl['_anio']   = df_fl['_desde'].dt.year
            df_fl['_mes']    = df_fl['_desde'].dt.month
            df_fl['_pod']    = df_fl[col_pod].astype(str).str.strip().str.upper()

            # Excluir PODs no deseados
            mask_pod = ~df_fl['_pod'].str.upper().str.contains(
                '|'.join(['LAZARO','CÁRDENAS','CARDENAS','MANZANILLO','MONTEVIDEO','SANTOS','URUGUAY','MVD']),
                na=False)
            df_fl = df_fl[mask_pod & df_fl['_flete'].notna() &
                          (df_fl['_cnt'] != 'NAN') & (df_fl['_cnt'] != '')].copy()

            TIPOS_CNT   = ['40ST/40HQ', '20ST', '40NOR']
            TARGET_PCT  = 0.85
            COLORES_CNT = {'40ST/40HQ':'#00a8ff','20ST':'#00ff88','40NOR':'#ffaa00'}
            COLORES_AG  = ['#00a8ff','#00ff88','#ffaa00','#ff4b4b','#a855f7','#06b6d4','#f97316','#ec4899']

            df_vig = df_fl[(df_fl['_desde'] <= hoy) & (df_fl['_hasta'] >= hoy)].copy()
            if df_vig.empty:
                ult = df_fl['_desde'].max()
                if pd.notna(ult):
                    df_vig = df_fl[df_fl['_desde'] == ult].copy()

            # ═══════════════════════════════════════════════════════════
            # HEADER
            # ═══════════════════════════════════════════════════════════
            st.markdown("""
<div style='text-align:center; padding:28px 20px 20px 20px;
background:linear-gradient(135deg,rgba(255,170,0,0.08),rgba(0,168,255,0.04));
border-radius:20px; border:1px solid rgba(255,170,0,0.2); margin-bottom:32px;'>
<h2 style='color:#ffaa00; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>FLETES & GASTOS LOCALES</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:12px; letter-spacing:3px;'>
MERCADO MARÍTIMO · ANÁLISIS ESTRATÉGICO · MEDIANA DE TARIFAS</p>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 1 — SITUACIÓN HOY
            # ═══════════════════════════════════════════════════════════
            st.markdown("""
<div style='border-bottom:2px solid rgba(255,170,0,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#ffaa00; font-size:13px; font-weight:800; letter-spacing:5px;'>01 · SITUACIÓN HOY</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>COTIZACIONES VIGENTES · MEDIANA DE MERCADO</span>
</div>""", unsafe_allow_html=True)

            if not df_vig.empty:
                cols_kpi = st.columns(len(TIPOS_CNT))
                for i, cnt in enumerate(TIPOS_CNT):
                    df_c = df_vig[df_vig['_cnt'] == cnt]
                    if df_c.empty:
                        with cols_kpi[i]:
                            st.markdown(f"<div style='text-align:center;padding:20px;border-radius:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);'><p style='color:#475569;font-size:13px;margin:0;'>{cnt}</p><p style='color:#475569;font-size:13px;'>Sin datos</p></div>", unsafe_allow_html=True)
                        continue

                    med_hoy   = df_c['_flete'].median()
                    min_hoy   = df_c['_flete'].min()
                    ag_min    = df_c.loc[df_c['_flete'].idxmin(), '_agente']
                    target    = med_hoy * TARGET_PCT
                    ok        = min_hoy <= target
                    color_cnt = COLORES_CNT.get(cnt, '#94a3b8')
                    semaforo  = '#00ff88' if ok else '#ff4b4b'
                    etiqueta  = '✅ DENTRO DEL TARGET' if ok else '🔴 POR ENCIMA DEL TARGET'

                    # vs 2025 mismo mes
                    df_25 = df_fl[(df_fl['_anio'] == 2025) & (df_fl['_mes'] == hoy.month) & (df_fl['_cnt'] == cnt)]
                    med_25 = df_25['_flete'].median() if not df_25.empty else None
                    if med_25 and med_25 > 0:
                        delta_pct = round((med_hoy - med_25) / med_25 * 100, 1)
                        delta_str = f"{'▲' if delta_pct > 0 else '▼'} {abs(delta_pct)}% vs mismo mes 2025"
                        delta_col = '#ff4b4b' if delta_pct > 0 else '#00ff88'
                    else:
                        delta_str = '— sin dato 2025'
                        delta_col = '#475569'

                    with cols_kpi[i]:
                        st.markdown(f"""
<div style='text-align:center; padding:24px 16px;
background:linear-gradient(145deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01));
border-radius:20px; border:1px solid rgba(255,255,255,0.08);
border-top:5px solid {color_cnt}; margin-bottom:8px;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0 0 6px 0; text-transform:uppercase;'>{cnt}</p>
<p style='color:{color_cnt}; font-size:52px; font-weight:900; margin:0; line-height:1; letter-spacing:-2px;'>
USD {int(round(med_hoy)):,}</p>
<p style='color:#475569; font-size:10px; margin:6px 0 0 0;'>mediana de mercado hoy</p>
<hr style='border:none; border-top:1px solid rgba(255,255,255,0.06); margin:14px 0;'>
<div style='display:flex; justify-content:space-between; align-items:center;'>
    <div style='text-align:left;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>MEJOR OFERTA</p>
        <p style='color:#f8fafc; font-size:18px; font-weight:800; margin:0;'>USD {int(round(min_hoy)):,}</p>
        <p style='color:#64748b; font-size:9px; margin:2px 0 0 0;'>{ag_min}</p>
    </div>
    <div style='text-align:right;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 2px 0;'>TARGET −15%</p>
        <p style='color:{semaforo}; font-size:18px; font-weight:800; margin:0;'>USD {int(round(target)):,}</p>
        <p style='color:{semaforo}; font-size:9px; font-weight:700; margin:2px 0 0 0;'>{etiqueta}</p>
    </div>
</div>
<div style='margin-top:12px; padding:8px 10px; background:rgba(255,255,255,0.03);
border-radius:8px; border-left:3px solid {delta_col};'>
<p style='color:{delta_col}; font-size:11px; font-weight:700; margin:0;'>{delta_str}</p>
</div>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 2 — BATTLE DE AGENTES
            # ═══════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(0,168,255,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#00a8ff; font-size:13px; font-weight:800; letter-spacing:5px;'>02 · BATTLE DE AGENTES</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>RANKING DE TARIFAS VIGENTES HOY · DE MÁS BARATO A MÁS CARO</span>
</div>""", unsafe_allow_html=True)

            col_cnt_sel, _ = st.columns([2, 3])
            with col_cnt_sel:
                cnt_battle = st.selectbox("TIPO DE CONTENEDOR:", TIPOS_CNT, key="battle_cnt_sel")

            df_battle = df_vig[df_vig['_cnt'] == cnt_battle].copy()
            if df_battle.empty:
                st.info(f"No hay cotizaciones vigentes para {cnt_battle}.")
            else:
                med_mkt  = df_battle['_flete'].median()
                target_b = med_mkt * TARGET_PCT

                ag_summary = df_battle.groupby('_agente')['_flete'].median().reset_index()
                ag_summary.columns = ['Agente', 'Tarifa']
                ag_summary = ag_summary.sort_values('Tarifa').reset_index(drop=True)
                max_tar = ag_summary['Tarifa'].max()

                st.markdown(f"""
<div style='display:flex; gap:20px; margin-bottom:20px;'>
<div style='padding:12px 20px; background:rgba(255,255,255,0.03); border-radius:12px;
border-left:4px solid #94a3b8;'>
<p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>MEDIANA MERCADO</p>
<p style='color:#f8fafc; font-size:20px; font-weight:800; margin:0;'>USD {int(round(med_mkt)):,}</p>
</div>
<div style='padding:12px 20px; background:rgba(255,170,0,0.06); border-radius:12px;
border-left:4px solid #ffaa00;'>
<p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>TARGET −15%</p>
<p style='color:#ffaa00; font-size:20px; font-weight:800; margin:0;'>USD {int(round(target_b)):,}</p>
</div>
<div style='padding:12px 20px; background:rgba(255,255,255,0.03); border-radius:12px;
border-left:4px solid #475569;'>
<p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>AGENTES COTIZANDO</p>
<p style='color:#f8fafc; font-size:20px; font-weight:800; margin:0;'>{len(ag_summary)}</p>
</div>
</div>""", unsafe_allow_html=True)

                for rank, (_, row) in enumerate(ag_summary.head(4).iterrows()):
                    ag      = row['Agente']
                    tarifa  = row['Tarifa']
                    pct_bar = round(tarifa / max_tar * 100) if max_tar > 0 else 0
                    ok_ag   = tarifa <= target_b
                    color_ag = '#00ff88' if ok_ag else ('#ffaa00' if tarifa <= med_mkt else '#ff4b4b')
                    badge   = '✅ DENTRO DEL TARGET' if ok_ag else ('⚠️ CERCA DEL TARGET' if tarifa <= med_mkt else '🔴 CARO')
                    ahorro  = int(round(tarifa - ag_summary['Tarifa'].iloc[0]))
                    ahorro_str = f"+USD {ahorro:,} vs más barato" if ahorro > 0 else "🏆 MÁS BARATO"
                    ahorro_col = '#ff4b4b' if ahorro > 0 else '#00ff88'

                    st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:14px;
border:1px solid rgba(255,255,255,0.06); padding:16px 20px; margin-bottom:10px;
border-left:5px solid {color_ag};'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
    <div style='display:flex; align-items:center; gap:14px;'>
        <p style='color:#334155; font-size:22px; font-weight:900; margin:0; width:32px;'>#{rank+1}</p>
        <div>
            <p style='color:#f8fafc; font-size:16px; font-weight:700; margin:0;'>{ag}</p>
            <p style='color:{color_ag}; font-size:10px; font-weight:700; margin:2px 0 0 0;'>{badge}</p>
        </div>
    </div>
    <div style='text-align:right;'>
        <p style='color:{color_ag}; font-size:28px; font-weight:900; margin:0; line-height:1;'>USD {int(round(tarifa)):,}</p>
        <p style='color:{ahorro_col}; font-size:11px; font-weight:700; margin:3px 0 0 0;'>{ahorro_str}</p>
    </div>
</div>
<div style='height:6px; background:rgba(255,255,255,0.05); border-radius:3px;'>
    <div style='height:6px; width:{pct_bar}%; background:{color_ag}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 3 — 2025 vs 2026
            # ═══════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(168,85,247,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#a855f7; font-size:13px; font-weight:800; letter-spacing:5px;'>03 · EVOLUCIÓN 2025 vs 2026</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>MEDIANA MENSUAL · DETECTÁ ESTACIONALIDAD Y TENDENCIA</span>
</div>""", unsafe_allow_html=True)

            col_cnt_h, _ = st.columns([2, 3])
            with col_cnt_h:
                cnt_hist = st.selectbox("TIPO DE CONTENEDOR:", TIPOS_CNT, key="hist_cnt_v2")

            df_hist = df_fl[df_fl['_cnt'] == cnt_hist].copy()
            df_hist = df_hist[df_hist['_anio'].isin([2025, 2026])].copy()

            # Nota de filtros aplicados
            st.markdown("""
<div style='display:flex; align-items:flex-start; gap:10px; padding:10px 16px;
background:rgba(255,255,255,0.02); border-radius:10px;
border-left:3px solid #334155; margin-bottom:20px;'>
<p style='color:#334155; font-size:18px; margin:0;'>🔍</p>
<div>
<p style='color:#475569; font-size:11px; font-weight:700; letter-spacing:1px; margin:0 0 3px 0;'>FILTROS APLICADOS</p>
<p style='color:#334155; font-size:11px; margin:0; line-height:1.6;'>
Destino: <b style='color:#475569;'>Argentina</b> · 
Excluidos: <b style='color:#475569;'>Lázaro Cárdenas · Manzanillo · Montevideo · Santos · Uruguay · MVD/SSZ</b> · 
Tipo de flete: <b style='color:#475569;'>Marítimo</b> · 
Métrica: <b style='color:#475569;'>Mediana mensual</b>
</p>
</div>
</div>""", unsafe_allow_html=True)

            if df_hist.empty:
                st.info("Sin datos históricos suficientes.")
            else:
                meses_dict = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
                              7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
                df_hist['_mes_label'] = df_hist['_mes'].map(meses_dict)

                res_hist = df_hist.groupby(['_anio','_mes','_mes_label'])['_flete'].median().reset_index()
                res_hist.columns = ['Año','Mes_Num','Mes','Mediana']
                res_hist['Año'] = res_hist['Año'].astype(str)
                res_hist = res_hist.sort_values(['Año','Mes_Num'])

                fig_hist = px.line(
                    res_hist, x='Mes', y='Mediana', color='Año',
                    markers=True, text='Mediana',
                    color_discrete_map={'2025':'#475569','2026':'#a855f7'},
                    labels={'Mediana':'USD (mediana)','Mes':''},
                    category_orders={'Mes': list(meses_dict.values())}
                )
                fig_hist.update_traces(
                    line=dict(width=3),
                    marker=dict(size=10, line=dict(color='#fff', width=1.5)),
                    texttemplate='<b>%{text:,.0f}</b>',
                    textposition='top center',
                    textfont=dict(size=11, family='Outfit, sans-serif'),
                )
                # Área bajo 2026 más visible
                fig_hist.for_each_trace(lambda t: t.update(
                    fill='tozeroy', fillcolor='rgba(168,85,247,0.06)'
                ) if t.name == '2026' else t.update(
                    fill='none', line=dict(dash='dot', width=2)
                ))
                fig_hist.update_layout(
                    height=420,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=12),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02,
                                xanchor='right', x=1, title_text='',
                                font=dict(size=13)),
                    xaxis=dict(showgrid=False, tickfont=dict(size=13, color='#94a3b8')),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)',
                               title='USD mediana', tickfont=dict(size=12)),
                    margin=dict(l=20, r=20, t=50, b=20),
                )
                # Línea vertical en mes actual
                mes_actual_label = meses_dict.get(hoy.month)
                if mes_actual_label in res_hist['Mes'].values:
                    fig_hist.add_vline(
                        x=mes_actual_label,
                        line=dict(color='rgba(255,255,255,0.15)', width=1, dash='dash')
                    )
                    fig_hist.add_annotation(
                        x=mes_actual_label, y=res_hist['Mediana'].max(),
                        text="HOY", showarrow=False,
                        font=dict(color='#475569', size=10, family='Outfit, sans-serif'),
                        yshift=14
                    )
                st.plotly_chart(fig_hist, use_container_width=True)

                # Mini tabla comparativa
                pivot = res_hist.pivot(index='Mes', columns='Año', values='Mediana')
                pivot.index = pd.Categorical(pivot.index, categories=list(meses_dict.values()), ordered=True)
                pivot = pivot.sort_index().reset_index()
                if '2025' in pivot.columns and '2026' in pivot.columns:
                    pivot['Δ vs 2025'] = pivot.apply(
                        lambda r: f"{'▲' if r['2026'] > r['2025'] else '▼'} {abs(round((r['2026']-r['2025'])/r['2025']*100,1))}%"
                        if pd.notna(r.get('2025')) and pd.notna(r.get('2026')) and r['2025'] > 0 else '—', axis=1)
                    pivot['2025'] = pivot['2025'].apply(lambda x: f"USD {int(round(x)):,}" if pd.notna(x) else '—')
                    pivot['2026'] = pivot['2026'].apply(lambda x: f"USD {int(round(x)):,}" if pd.notna(x) else '—')
                    st.dataframe(pivot.rename(columns={'Mes':'Mes','2025':'Mediana 2025','2026':'Mediana 2026'}),
                                 use_container_width=True, hide_index=True)

            # ═══════════════════════════════════════════════════════════
            # BLOQUE 4 — GASTOS LOCALES
            # ═══════════════════════════════════════════════════════════
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(6,182,212,0.3); padding-bottom:10px; margin-bottom:24px;'>
<span style='color:#06b6d4; font-size:13px; font-weight:800; letter-spacing:5px;'>04 · GASTOS LOCALES ARG</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:14px;'>VIGENTES HOY · COSTO EN DESTINO</span>
</div>""", unsafe_allow_html=True)

            df_loc = df_fl[(df_fl['_desde'] <= hoy) & (df_fl['_hasta'] >= hoy) & df_fl['_local'].notna()].copy()
            if df_loc.empty:
                ult_l = df_fl[df_fl['_local'].notna()]['_desde'].max()
                if pd.notna(ult_l):
                    df_loc = df_fl[(df_fl['_desde'] == ult_l) & df_fl['_local'].notna()].copy()

            if not df_loc.empty:
                med_loc = df_loc['_local'].median()
                min_loc = df_loc['_local'].min()
                max_loc = df_loc['_local'].max()
                ag_min_loc = df_loc.loc[df_loc['_local'].idxmin(), '_agente']
                ag_max_loc = df_loc.loc[df_loc['_local'].idxmax(), '_agente']

                lc1, lc2, lc3, lc4 = st.columns(4)
                for col_card, valor, label, color, sub in [
                    (lc1, f"USD {int(round(med_loc)):,}", "MEDIANA MERCADO", "#06b6d4", "referencia del mercado"),
                    (lc2, f"USD {int(round(min_loc)):,}", "MÁS BARATO", "#00ff88", ag_min_loc),
                    (lc3, f"USD {int(round(max_loc)):,}", "MÁS CARO", "#ff4b4b", ag_max_loc),
                    (lc4, f"USD {int(round(max_loc - min_loc)):,}", "DIFERENCIA MAX", "#ffaa00", "entre agentes"),
                ]:
                    col_card.markdown(f"""
<div style='text-align:center; padding:22px 12px;
background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); border-top:4px solid {color};'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 8px 0; text-transform:uppercase;'>{label}</p>
<p style='color:{color}; font-size:30px; font-weight:900; margin:0; line-height:1;'>{valor}</p>
<p style='color:#475569; font-size:10px; margin:6px 0 0 0;'>{sub}</p>
</div>""", unsafe_allow_html=True)

                # Ranking gastos locales
                st.markdown("<br>", unsafe_allow_html=True)
                ag_loc = df_loc.groupby('_agente')['_local'].median().reset_index()
                ag_loc.columns = ['Agente','Gasto Local']
                ag_loc = ag_loc.sort_values('Gasto Local').reset_index(drop=True)
                max_gl = ag_loc['Gasto Local'].max()

                for rank, (_, row) in enumerate(ag_loc.head(4).iterrows()):
                    pct_gl  = round(row['Gasto Local'] / max_gl * 100) if max_gl > 0 else 0
                    color_gl = '#00ff88' if rank == 0 else ('#ffaa00' if row['Gasto Local'] <= med_loc else '#ff4b4b')
                    dif_gl  = int(round(row['Gasto Local'] - ag_loc['Gasto Local'].iloc[0]))
                    dif_str = f"+USD {dif_gl:,} vs más barato" if dif_gl > 0 else "🏆 MÁS BARATO"
                    dif_col = '#ff4b4b' if dif_gl > 0 else '#00ff88'

                    st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:12px;
border:1px solid rgba(255,255,255,0.05); padding:14px 18px; margin-bottom:8px;
border-left:4px solid {color_gl};'>
<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
    <div style='display:flex; align-items:center; gap:12px;'>
        <p style='color:#334155; font-size:18px; font-weight:900; margin:0; width:28px;'>#{rank+1}</p>
        <p style='color:#f8fafc; font-size:15px; font-weight:700; margin:0;'>{row['Agente']}</p>
    </div>
    <div style='text-align:right;'>
        <p style='color:{color_gl}; font-size:22px; font-weight:900; margin:0;'>USD {int(round(row["Gasto Local"])):,}</p>
        <p style='color:{dif_col}; font-size:10px; font-weight:700; margin:2px 0 0 0;'>{dif_str}</p>
    </div>
</div>
<div style='height:5px; background:rgba(255,255,255,0.05); border-radius:3px;'>
    <div style='height:5px; width:{pct_gl}%; background:{color_gl}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)
            else:
                st.info("No hay gastos locales disponibles para el período vigente.")

        except Exception as e:
            st.error(f"Error en Fletes y Gastos: {e}")
            import traceback
            st.code(traceback.format_exc())
