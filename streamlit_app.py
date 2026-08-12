import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BIDCOM | Dashboard Ejecutivo", layout="wide", initial_sidebar_state="collapsed")

# Eliminar padding default de Streamlit
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { padding: 0 !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DISEÑO BIDCOM IMPACTO TOTAL (CSS) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;900&display=swap');

/* TIPO Y FONDO GENERAL */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
}
.block-container { 
    padding: 1rem 2rem !important;
    max-width: 100% !important;
}
.main .block-container {
    padding-top: 1rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}
section[data-testid="stSidebar"] { display: none !important; }
/* Force full width on all main containers */
div[data-testid="stAppViewContainer"] > section > div {
    max-width: 100% !important;
}
/* Force centered layout */
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
section[data-testid="stSidebar"] { display: none; }
.stMainBlockContainer { padding-top: 1rem !important; }

/* BOTONES COMPACTOS INDICADORES */
div[data-testid="stColumn"] div[data-testid="stButton"] button {
    height: 28px !important;
    min-height: 28px !important;
    padding: 0px 8px !important;
    font-size: 12px !important;
    border-radius: 6px !important;
}

/* DIVIDORES Y ESPACIOS */
hr { margin: 1rem 0 !important; opacity: 0.1; }

/* ANIMACIONES */
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-40px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(40px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0% { box-shadow: 0 0 20px rgba(0, 168, 255, 0.2); }
    50% { box-shadow: 0 0 40px rgba(0, 168, 255, 0.4); }
    100% { box-shadow: 0 0 20px rgba(0, 168, 255, 0.2); }
}

/* TABS */
.stTabs [data-baseweb="tab-list"] { 
    justify-content: center !important;
    gap: 6px !important;
    margin: 0 auto 40px auto !important;
    width: fit-content !important;
    min-width: 60% !important;
    max-width: 100% !important;
    display: flex !important;
    background: rgba(255,255,255,0.02) !important;
    border-radius: 16px !important;
    padding: 8px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    position: relative !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
}
.stTabs [data-baseweb="tab"] { 
    background-color: transparent !important;
    border-radius: 10px !important;
    border: 1px solid transparent !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    padding: 10px 18px !important;
    color: #475569 !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px;
    font-size: 11px !important;
    text-transform: uppercase;
    white-space: nowrap;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(0,168,255,0.06) !important;
    color: #94a3b8 !important;
    border-color: rgba(0,168,255,0.15) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,168,255,0.15), rgba(0,168,255,0.08)) !important;
    box-shadow: 0 4px 20px rgba(0,168,255,0.2), inset 0 0 12px rgba(0,168,255,0.08) !important;
    color: #00a8ff !important;
    border: 1px solid rgba(0,168,255,0.35) !important;
}
/* Hide default tab border bottom */
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ENCABEZADO */
.bidcom-header {
    background: linear-gradient(135deg, rgba(0,31,63,0.7) 0%, rgba(0,51,102,0.8) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 50px; 
    border-radius: 24px; 
    border: 1px solid rgba(0, 168, 255, 0.2);
    text-align: center; 
    margin-bottom: 40px;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6), inset 0 0 40px rgba(0,168,255,0.1);
    animation: fadeInDown 1s cubic-bezier(0.2, 0.8, 0.2, 1);
}
/* Force full-width centered layout */
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
section[data-testid="stSidebar"] { display: none; }
.stMainBlockContainer { padding-top: 1rem !important; }
.bidcom-header h1 { 
    font-size: 80px; 
    letter-spacing: 20px; 
    font-weight: 900; 
    margin: 0; 
    background: linear-gradient(180deg, #ffffff 0%, #00a8ff 150%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0px 10px 40px rgba(0, 168, 255, 0.5); 
}
.bidcom-subtitle { 
    font-size: 22px; 
    color: #00a8ff; 
    letter-spacing: 12px; 
    text-transform: uppercase; 
    font-weight: 600; 
    margin-top: 15px; 
    text-shadow: 0 0 15px rgba(0, 168, 255, 0.4);
}

/* KPIs PRINCIPALES MASIVOS */
.metric-container { 
    text-align: center; 
    padding: 20px 16px; 
    background: rgba(255,255,255,0.03);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.07);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}
.metric-container p:first-child { 
    font-size: 10px !important;
    color: #64748b !important; 
    letter-spacing: 3px !important;
    font-weight: 700 !important;
    margin-bottom: 8px !important;
    text-transform: uppercase;
}
.metric-container p:last-child { 
    font-size: 36px !important; 
    font-weight: 900 !important; 
    color: #f8fafc !important; 
    line-height: 1 !important; 
    margin: 0 !important;
}

/* TARJETAS GLASSMORPHISM STANDARDS */
.custom-card {
    background: rgba(255,255,255,0.02);
    padding: 20px; 
    border-radius: 14px; 
    border: 1px solid rgba(255,255,255,0.07);
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    margin-bottom: 16px;
}
.custom-card-title {
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 2px;
    margin-bottom: 14px;
    margin-top: 0;
    text-transform: uppercase;
}
.grid-2 {
    display: grid; 
    grid-template-columns: 1fr 1fr; 
    gap: 14px;
}
.grid-4 {
    display: grid; 
    grid-template-columns: 1fr 1fr 1fr 1fr; 
    gap: 14px;
}
.minicard-title {
    font-size: 10px; 
    color: #64748b; 
    letter-spacing: 2px;
    margin: 0 0 4px 0;
    font-weight: 600;
    text-transform: uppercase;
}
.minicard-value {
    font-size: 22px; 
    font-weight: 700; 
    margin: 0; 
    color: #f8fafc;
}

/* BOTONES GLOBALES Y FILTROS */
.stButton>button {
    border-radius: 16px !important; 
    color: #f8fafc !important;
    width: 100%; 
    height: 110px; 
    font-weight: 700 !important; 
    font-size: 15px !important;
    background: rgba(15, 23, 42, 0.4) !important; 
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    line-height: 1.4 !important;
    letter-spacing: 1px;
}
.stButton>button:hover { 
    background-color: rgba(0, 168, 255, 0.15) !important; 
    border-color: #00a8ff !important; 
    color: #ffffff !important; 
    box-shadow: 0 10px 30px rgba(0, 168, 255, 0.3), inset 0 0 20px rgba(0, 168, 255, 0.1) !important; 
    transform: translateY(-4px);
}

/* DECORATIVOS: LINEAS DIVISORAS */
.glow-divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0,168,255,0.4), transparent);
    margin: 40px 0;
    opacity: 0.6;
}
.white-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    margin: 30px 0;
}
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

    st.markdown("<div class='bidcom-header'><h1>BIDCOM</h1><div class='bidcom-subtitle'>Tablero Logística Internacional</div></div>", unsafe_allow_html=True)
    col_ref, _ = st.columns([1, 5])
    with col_ref:
        if st.button("🔄 Actualizar datos", key="btn_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.expander("📡  PANORAMA DE MERCADO  |  Actualizando información · Próxima actualización disponible pronto", expanded=False):
        st.markdown("""
<div style='padding:20px 24px; background:rgba(255,255,255,0.02); border-radius:12px; text-align:center;'>
<p style='color:#475569; font-size:13px; letter-spacing:2px; margin:0 0 8px 0;'>⏳ ACTUALIZANDO INFORMACIÓN DE MERCADO</p>
<p style='color:#334155; font-size:12px; margin:0;'>Próximamente disponible · El equipo está consolidando los datos más recientes del mercado marítimo internacional.</p>
</div>
""", unsafe_allow_html=True)
    tabs = st.tabs(["ORIGEN", "MERCADERÍA EN PROCESO", "PERFORMANCE DE AGENTES Y ANALISTAS", "FLETES, GASTOS Y CERTIFICACIONES", "PROYECCIÓN SEMANAL ETD", "INDICADORES", "HISTÓRICO", "ASK COMEX"])

    # --- SOLAPA 1: ORIGEN ---
    with tabs[0]:
        try:
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], dayfirst=True, errors='coerce')
            col_rank = df.columns[1]
            df['Rank_Num'] = df[col_rank].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Rank_Num'] = pd.to_numeric(df['Rank_Num'], errors='coerce').fillna(999999)

            col_cp = df.columns[95]  # ¿ES MONOPROVEEDOR? columna CR
            df['Tipo_Carga'] = df[col_cp].astype(str).str.strip().str.upper().apply(
                lambda x: 'MONOPROVEEDOR' if x in ['SI', 'SÍ', 'S', 'MONOPROVEEDOR'] else 'CONSOLIDADO'
            )

            col_an = df.columns[39]  # Repuestos columna AN
            def get_tipo_negocio(val):
                v = str(val).strip()
                if v in ['', 'nan', 'None'] or pd.isna(val): return 'GADNIC'
                vl = v.lower()
                if 'muestra' in vl: return 'MUESTRAS'
                if 'sin planeamiento' in vl: return 'MARCAS'
                if 'repuesto' in vl: return 'REPUESTOS'
                return 'GADNIC'
            df['Tipo_Negocio'] = df[col_an].apply(get_tipo_negocio)

            df['Pais Destino'] = df['Pais Destino'].fillna('SIN DEFINIR').astype(str).str.strip()
            df['Repuestos'] = df['Repuestos'].fillna('').astype(str).str.strip()

            cond_prioridad = (df['Pais Destino'].str.upper() == 'ARGENTINA') & (df['Tipo_Negocio'] == 'GADNIC')
            cond_instruido = df['Fecha_Inst_DT'].notna() & ~(df['Fecha de Instruccion'].astype(str).str.upper().str.contains("SIN INSTRUCCION", na=False))
            cond_pendiente = ~cond_instruido
            cond_urgente = cond_pendiente & (df['Fecha_Prior_DT'] < hoy)
            cond_pd_futura = cond_pendiente & (df['Fecha_Prior_DT'] >= hoy)
            cond_acc_mono = cond_pd_futura & (df['Tipo_Carga'] == 'MONOPROVEEDOR') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=25))
            cond_acc_consol = cond_pd_futura & (df['Tipo_Carga'] == 'CONSOLIDADO') & (df['Fecha_Prior_DT'] <= hoy + timedelta(days=10))
            cond_accionar = cond_acc_mono | cond_acc_consol
            cond_futura = cond_pendiente & (~cond_urgente) & (~cond_accionar)

            df_inst = df[cond_instruido & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_urgente = df[cond_urgente & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_accionar = df[cond_accionar & cond_prioridad].sort_values(by='Rank_Num').copy()
            df_futura = df[cond_futura & cond_prioridad].sort_values(by='Rank_Num').copy()

            cond_complementario = cond_pendiente & (~cond_prioridad)
            df_complem = df[cond_complementario].sort_values(by=['Fecha_Prior_DT', 'Rank_Num']).copy()
            df_otros_p = df_complem[df_complem['Pais Destino'].str.upper() != 'ARGENTINA'].copy()
            df_repuestos = df_complem[df_complem['Tipo_Negocio'] != 'GADNIC'].copy()
            cant_demorados_comp = df_complem[df_complem['Fecha_Prior_DT'] < hoy]['SO'].nunique()

            m3_inst = df_inst['M3 Total'].sum()
            m3_urgente = df_urgente['M3 Total'].sum()
            m3_accionar = df_accionar['M3 Total'].sum()
            m3_futura = df_futura['M3 Total'].sum()
            m3_pend_total = m3_urgente + m3_accionar + m3_futura

            p_inst_val = int(round(m3_inst / m3_totales_global * 100)) if m3_totales_global > 0 else 0
            p_pend_val = 100 - p_inst_val
            fob_total_global = df['Fob total Origen'].sum()

            st.markdown("<br>", unsafe_allow_html=True)
            o1, o2, o3, o4 = st.columns(4)
            with o1: st.markdown(f"<div class='metric-container'><p>CANTIDAD DE SO</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{int(cant_so_global)}</p></div>", unsafe_allow_html=True)
            with o2: st.markdown(f"<div class='metric-container'><p>VOLUMEN TOTAL (M3)</p><p style='color:#00a8ff; font-size:32px; font-weight:900; margin:0;'>{int(round(m3_totales_global)):,}</p></div>", unsafe_allow_html=True)
            with o3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{int(cant_proveedores_global)}</p></div>", unsafe_allow_html=True)
            with o4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL (USD)</p><p style='color:#ffaa00; font-size:28px; font-weight:900; margin:0;'>USD {round(fob_total_global/1_000_000,1)}M</p></div>", unsafe_allow_html=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin-bottom: 30px;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>CONTROL DE STATUS DE MERCADERÍA</h2></div>", unsafe_allow_html=True)

            s1, s2 = st.columns(2)
            with s1:
                m3_mono_inst = df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['M3 Total'].sum()
                m3_cons_inst = df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['M3 Total'].sum()
                so_mono_inst = df_inst[df_inst['Tipo_Carga']=='MONOPROVEEDOR']['SO'].nunique()
                so_cons_inst = df_inst[df_inst['Tipo_Carga']=='CONSOLIDADO']['SO'].nunique()
                st.markdown(f"""
<div class="custom-card" style="border-top:5px solid #00ff88; background:rgba(0,255,136,0.02);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <p class="custom-card-title" style="color:#00ff88; font-size:18px; margin:0;">✅ MERCADERÍA INSTRUIDA</p>
        <p style="color:#00ff88; font-weight:900; font-size:36px; margin:0;">{p_inst_val}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">M3</span></p>
    </div>
    <div class="grid-2" style="margin-bottom:16px;">
        <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value" style="color:#00ff88;">{df_inst['SO'].nunique()}</p></div>
        <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{int(round(m3_inst)):,} M3</p></div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:14px 0;">
    <div class="grid-2">
        <div>
            <p class="minicard-title" style="color:#00a8ff;">ESTRUCTURA DE CARGA</p>
            <p style="font-size:12px; margin:5px 0;">MONOPROVEEDOR: <b style="color:#00a8ff;">{so_mono_inst} SO</b> · {int(round(m3_mono_inst)):,} M3</p>
            <p style="font-size:12px; margin:5px 0;">CONSOLIDADO: <b style="color:#ffaa00;">{so_cons_inst} SO</b> · {int(round(m3_cons_inst)):,} M3</p>
        </div>
        <div>
            <p class="minicard-title" style="color:#ffaa00;">TIPO DE NEGOCIO</p>
            <p style="font-size:12px; margin:4px 0;">GADNIC: <b>{df_inst[df_inst['Tipo_Negocio']=='GADNIC']['SO'].nunique()} SO</b></p>
            <p style="font-size:12px; margin:4px 0;">MUESTRAS: <b>{df_inst[df_inst['Tipo_Negocio']=='MUESTRAS']['SO'].nunique()} SO</b></p>
            <p style="font-size:12px; margin:4px 0;">MARCAS: <b>{df_inst[df_inst['Tipo_Negocio']=='MARCAS']['SO'].nunique()} SO</b></p>
            <p style="font-size:12px; margin:4px 0;">REPUESTOS: <b>{df_inst[df_inst['Tipo_Negocio']=='REPUESTOS']['SO'].nunique()} SO</b></p>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

            with s2:
                df_pend_view = df[cond_pendiente]
                m3_mono_pend = df_pend_view[df_pend_view['Tipo_Carga']=='MONOPROVEEDOR']['M3 Total'].sum()
                m3_cons_pend = df_pend_view[df_pend_view['Tipo_Carga']=='CONSOLIDADO']['M3 Total'].sum()
                so_mono_pend = df_pend_view[df_pend_view['Tipo_Carga']=='MONOPROVEEDOR']['SO'].nunique()
                so_cons_pend = df_pend_view[df_pend_view['Tipo_Carga']=='CONSOLIDADO']['SO'].nunique()
                st.markdown(f"""
<div class="custom-card" style="border-top:5px solid #94a3b8; background:rgba(148,163,184,0.02);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <p class="custom-card-title" style="color:#f8fafc; font-size:18px; margin:0;">⏳ MERCADERÍA PENDIENTE</p>
        <p style="color:#f8fafc; font-weight:900; font-size:36px; margin:0;">{p_pend_val}% <span style="font-size:14px; color:#94a3b8; font-weight:400;">M3</span></p>
    </div>
    <div class="grid-2" style="margin-bottom:16px;">
        <div><p class="minicard-title">CANTIDAD SO</p><p class="minicard-value">{df_pend_view['SO'].nunique()}</p></div>
        <div><p class="minicard-title">VOLUMEN TOTAL</p><p class="minicard-value">{int(round(m3_pend_total)):,} M3</p></div>
    </div>
    <hr style="border:none; border-top:1px solid rgba(255,255,255,0.08); margin:14px 0;">
    <div class="grid-2">
        <div>
            <p class="minicard-title" style="color:#00a8ff;">ESTRUCTURA DE CARGA</p>
            <p style="font-size:12px; margin:5px 0;">MONOPROVEEDOR: <b style="color:#00a8ff;">{so_mono_pend} SO</b> · {int(round(m3_mono_pend)):,} M3</p>
            <p style="font-size:12px; margin:5px 0;">CONSOLIDADO: <b style="color:#ffaa00;">{so_cons_pend} SO</b> · {int(round(m3_cons_pend)):,} M3</p>
        </div>
        <div>
            <p class="minicard-title" style="color:#ffaa00;">TIPO DE NEGOCIO</p>
            <p style="font-size:12px; margin:4px 0;">GADNIC: <b>{df_pend_view[df_pend_view['Tipo_Negocio']=='GADNIC']['SO'].nunique()} SO</b></p>
            <p style="font-size:12px; margin:4px 0;">MUESTRAS: <b>{df_pend_view[df_pend_view['Tipo_Negocio']=='MUESTRAS']['SO'].nunique()} SO</b></p>
            <p style="font-size:12px; margin:4px 0;">MARCAS: <b>{df_pend_view[df_pend_view['Tipo_Negocio']=='MARCAS']['SO'].nunique()} SO</b></p>
            <p style="font-size:12px; margin:4px 0;">REPUESTOS: <b>{df_pend_view[df_pend_view['Tipo_Negocio']=='REPUESTOS']['SO'].nunique()} SO</b></p>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; letter-spacing:4px; font-size:18px; margin-bottom:25px; text-align:center;'>DISTRIBUCIÓN GEOGRÁFICA</p>", unsafe_allow_html=True)

            res_p = df.groupby('Pais Destino').agg({'SO': 'nunique', 'M3 Total': 'sum'}).rename(columns={'SO': 'CANT_SO', 'M3 Total': 'M3'}).sort_values(by='M3', ascending=False)
            total_so_p = res_p['CANT_SO'].sum()
            total_m3_p = res_p['M3'].sum()

            # Mono/Cons por país
            mono_por_pais = df.groupby(['Pais Destino', 'Tipo_Carga'])['SO'].nunique().unstack(fill_value=0)
            if 'MONOPROVEEDOR' not in mono_por_pais.columns: mono_por_pais['MONOPROVEEDOR'] = 0
            if 'CONSOLIDADO'   not in mono_por_pais.columns: mono_por_pais['CONSOLIDADO']   = 0

            hp1, hp2, hp3, hp4, hp5 = st.columns([1.5, 0.9, 0.9, 1.2, 0.7])
            hp1.markdown("<p style='color:#94a3b8; font-size:11px; letter-spacing:1px; font-weight:700;'>DESTINO</p>", unsafe_allow_html=True)
            hp2.markdown("<p style='color:#94a3b8; font-size:11px; letter-spacing:1px; font-weight:700; text-align:center;'>VOLUMEN (M3)</p>", unsafe_allow_html=True)
            hp3.markdown("<p style='color:#94a3b8; font-size:11px; letter-spacing:1px; font-weight:700; text-align:center;'>CANTIDAD SO</p>", unsafe_allow_html=True)
            hp4.markdown("<p style='color:#94a3b8; font-size:11px; letter-spacing:1px; font-weight:700; text-align:center;'>MONO / CONSOLIDADO</p>", unsafe_allow_html=True)
            hp5.markdown("<p style='color:#94a3b8; font-size:11px; letter-spacing:1px; font-weight:700; text-align:right;'>SHARE %</p>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:0 0 10px 0; border:none; border-top:1px solid rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

            for pais, row in res_p.iterrows():
                m3_v  = int(round(row['M3']))
                so_v  = int(row['CANT_SO'])
                pct_v = int(round(m3_v / total_m3_p * 100)) if total_m3_p > 0 else 0
                color_texto = "#ffffff" if pais != "SIN DEFINIR" else "#64748b"
                n_mono = int(mono_por_pais.loc[pais, 'MONOPROVEEDOR']) if pais in mono_por_pais.index else 0
                n_cons = int(mono_por_pais.loc[pais, 'CONSOLIDADO'])   if pais in mono_por_pais.index else 0
                total_mc = n_mono + n_cons
                pct_mono = round(n_mono / total_mc * 100) if total_mc > 0 else 0
                pct_cons = 100 - pct_mono
                cp1, cp2, cp3, cp4, cp5 = st.columns([1.5, 0.9, 0.9, 1.2, 0.7])
                cp1.markdown(f"<p style='color:{color_texto}; font-weight:600; font-size:15px; margin:8px 0;'>{pais.upper()}</p>", unsafe_allow_html=True)
                cp2.markdown(f"<p style='color:#00a8ff; font-size:18px; text-align:center; margin:8px 0;'>{m3_v:,}</p>", unsafe_allow_html=True)
                cp3.markdown(f"<p style='color:{color_texto}; font-size:18px; text-align:center; margin:8px 0;'>{so_v}</p>", unsafe_allow_html=True)
                cp4.markdown(f"<p style='text-align:center; margin:8px 0; font-size:13px;'><span style='color:#00a8ff; font-weight:700;'>MONO {pct_mono}%</span> <span style='color:#334155;'>·</span> <span style='color:#ffaa00; font-weight:700;'>CONS {pct_cons}%</span></p>", unsafe_allow_html=True)
                cp5.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:16px; text-align:right; margin:8px 0;'>{pct_v}%</p>", unsafe_allow_html=True)

            st.markdown("<hr style='margin:15px 0; border:none; border-top:1px solid rgba(255,255,255,0.4);'>", unsafe_allow_html=True)
            tp1, tp2, tp3, tp4, tp5 = st.columns([1.5, 0.9, 0.9, 1.2, 0.7])
            tp1.markdown("<p style='color:#f8fafc; font-weight:800; font-size:17px;'>TOTAL GENERAL</p>", unsafe_allow_html=True)
            tp2.markdown(f"<p style='color:#00a8ff; font-weight:800; font-size:20px; text-align:center;'>{int(round(total_m3_p)):,}</p>", unsafe_allow_html=True)
            tp3.markdown(f"<p style='color:#f8fafc; font-weight:800; font-size:20px; text-align:center;'>{int(total_so_p)}</p>", unsafe_allow_html=True)
            tp4.markdown("", unsafe_allow_html=True)
            tp5.markdown("<p style='color:#00ff88; font-weight:900; font-size:18px; text-align:right;'>100%</p>", unsafe_allow_html=True)

            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

            col_puerto = df.columns[41]
            p_df = df.groupby(col_puerto).agg({'M3 Total': 'sum'}).reset_index().sort_values(by='M3 Total')
            st.markdown(f"<p style='color:#00a8ff; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:20px;'>VOLUMEN POR PUERTO DE SALIDA <span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>| TOTAL: {int(round(p_df['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)

            fig_p = px.bar(p_df, y=col_puerto, x='M3 Total', orientation='h', text_auto=',.0f', color_discrete_sequence=['#00a8ff'])
            fig_p.update_traces(textposition='outside', cliponaxis=False, textfont_size=16, textfont_color="#f8fafc", marker=dict(cornerradius=5))
            fig_p.update_layout(xaxis_visible=True, xaxis_title="Total M3", yaxis_title="Puerto", height=500, margin=dict(l=150, r=100, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_p.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig_p, use_container_width=True)

            ga, gb = st.columns(2)
            with ga:
                etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum', 'Fob total Origen': 'sum'}).reset_index()
                etd_p['_fob_clean'] = etd_p['Fob total Origen'].apply(lambda x: safe_float(x) if 'safe_float' in dir() else (float(str(x).replace(',','.').replace('USD','').strip()) if str(x).strip() not in ['','nan'] else 0))
                st.markdown(f"<p style='color:#00ff88; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETD<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(round(etd_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                import plotly.graph_objects as go
                fig_e = go.Figure()
                fig_e.add_trace(go.Bar(
                    x=etd_p['Mes_ETD_Full'], y=etd_p['M3 Total'],
                    name='M3', marker_color='#00ff88', marker_cornerradius=5,
                    text=etd_p['M3 Total'].apply(lambda x: f"{int(round(x)):,}"),
                    textposition='inside', textfont=dict(size=13, color='#fff'),
                ))
                # FOB como anotación encima de cada barra
                for _, row in etd_p.iterrows():
                    fob_v = row['_fob_clean']
                    fob_str = f"USD {fob_v/1_000_000:.1f}M" if fob_v >= 1_000_000 else f"USD {fob_v/1_000:.0f}K"
                    fig_e.add_annotation(
                        x=row['Mes_ETD_Full'], y=row['M3 Total'],
                        text=f"<b>{fob_str}</b>",
                        showarrow=False, yshift=18,
                        font=dict(size=11, color='#ffaa00', family='Outfit, sans-serif')
                    )
                fig_e.update_layout(
                    height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=13, family='Outfit, sans-serif', color='#94a3b8'),
                    margin=dict(l=20, r=20, t=50, b=20), showlegend=False,
                    yaxis=dict(title='M3', showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
                    xaxis=dict(title='Mes ETD'),
                )
                st.plotly_chart(fig_e, use_container_width=True)

            with gb:
                eta_p = df.groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum', 'Fob total Origen': 'sum'}).reset_index()
                eta_p['_fob_clean'] = eta_p['Fob total Origen'].apply(lambda x: safe_float(x) if 'safe_float' in dir() else (float(str(x).replace(',','.').replace('USD','').strip()) if str(x).strip() not in ['','nan'] else 0))
                st.markdown(f"<p style='color:#ff4b4b; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN MENSUAL ETA<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(round(eta_p['M3 Total'].sum())):,} M3</span></p>", unsafe_allow_html=True)
                fig_a = go.Figure()
                fig_a.add_trace(go.Bar(
                    x=eta_p['Mes_ETA_Full'], y=eta_p['M3 Total'],
                    name='M3', marker_color='#ff4b4b', marker_cornerradius=5,
                    text=eta_p['M3 Total'].apply(lambda x: f"{int(round(x)):,}"),
                    textposition='inside', textfont=dict(size=13, color='#fff'),
                ))
                for _, row in eta_p.iterrows():
                    fob_v = row['_fob_clean']
                    fob_str = f"USD {fob_v/1_000_000:.1f}M" if fob_v >= 1_000_000 else f"USD {fob_v/1_000:.0f}K"
                    fig_a.add_annotation(
                        x=row['Mes_ETA_Full'], y=row['M3 Total'],
                        text=f"<b>{fob_str}</b>",
                        showarrow=False, yshift=18,
                        font=dict(size=11, color='#ffaa00', family='Outfit, sans-serif')
                    )
                fig_a.update_layout(
                    height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=13, family='Outfit, sans-serif', color='#94a3b8'),
                    margin=dict(l=20, r=20, t=50, b=20), showlegend=False,
                    yaxis=dict(title='M3', showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
                    xaxis=dict(title='Mes ETA'),
                )
                st.plotly_chart(fig_a, use_container_width=True)

            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)

            gc, gd = st.columns(2)
            with gc:
                col_mod_opciones = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
                col_mod = col_mod_opciones[0] if col_mod_opciones else 'Modalidad de Costeo Reposicion'
                if col_mod in df.columns:
                    # Filtro alineado con Proyección Semanal: Argentina + Barco + Costo Hibrido Puerto ZFLP
                    mask_arg   = df['Pais Destino'].astype(str).str.strip().str.upper() == 'ARGENTINA'
                    mask_barco = (
                        df[col_mod].astype(str).str.upper().str.startswith("BARCO") |
                        df[col_mod].astype(str).str.upper().str.contains("COSTO HIBRIDO PUERTO ZFLP", na=False)
                    )
                    mask_cntr = mask_arg & mask_barco
                    df_c_etd = df[mask_cntr].groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
                    df_c_etd['Contenedores'] = (df_c_etd['M3 Total'] / 60).round().astype(int)
                    tot_cont_etd = df_c_etd['Contenedores'].sum()
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETD)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(tot_cont_etd):,} CNTR</span></p>", unsafe_allow_html=True)
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
                    df_c_eta = df[mask_cntr].groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
                    df_c_eta['Contenedores'] = (df_c_eta['M3 Total'] / 60).round().astype(int)
                    tot_cont_eta = df_c_eta['Contenedores'].sum()
                    st.markdown(f"<p style='color:#ffaa00; font-weight:700; font-size:16px; text-align:center; letter-spacing:2px; margin-bottom:20px;'>PROYECCIÓN CONTENEDORES (ETA)<br><span style='font-size:14px; font-weight:400; color:#f8fafc; text-shadow:none;'>TOTAL: {int(tot_cont_eta):,} CNTR</span></p>", unsafe_allow_html=True)
                    fig_ceta = px.bar(df_c_eta, x='Mes_ETA_Full', y='Contenedores', text_auto=',.0f', color_discrete_sequence=['#ffaa00'])
                    fig_ceta.update_traces(textfont_size=16, textposition='outside', textfont_color="#f8fafc", marker=dict(cornerradius=5))
                    fig_ceta.update_layout(yaxis_visible=True, yaxis_title="Cant. Cont", xaxis_title="Mes ETA", height=450, margin=dict(l=20, r=20, t=20, b=20), font=dict(size=14, family='Outfit, sans-serif'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig_ceta.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)')
                    st.plotly_chart(fig_ceta, use_container_width=True)

            # ── PROYECCIÓN M3 POR ESTRUCTURA DE CARGA (MONO vs CONSOLIDADO) ──
            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:16px; text-align:center; letter-spacing:3px; margin-bottom:20px;'>PROYECCIÓN M3 POR ESTRUCTURA DE CARGA</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:#475569; font-size:11px; text-align:center; margin-bottom:20px;'>Argentina · Barco / Costo Híbrido Puerto ZFLP · Solo meses futuros</p>", unsafe_allow_html=True)

            try:
                col_mod_mono = [c for c in df.columns if 'MODALIDAD' in str(c).upper() and 'COSTEO' in str(c).upper()]
                col_mod_mono = col_mod_mono[0] if col_mod_mono else 'Modalidad de Costeo Reposicion'
                col_mono_orig = df.columns[95]  # ¿ES MONOPROVEEDOR? columna CR

                if col_mod_mono in df.columns:
                    # Mismo dataset que PROYECCIÓN MENSUAL ETD/ETA — sin filtro adicional
                    df_mono_proy = df.copy()

                    # Solo meses futuros ETD — igual que el gráfico ETD general
                    df_mono_proy_etd = df_mono_proy[
                        ~df_mono_proy['Mes_ETD_Full'].astype(str).isin(['PASADO/REALIZADO', 'SIN FECHA'])
                    ].copy()
                    # Solo meses futuros ETA — igual que el gráfico ETA general
                    df_mono_proy_eta = df_mono_proy[
                        ~df_mono_proy['Mes_ETA_Full'].astype(str).isin(['PASADO/REALIZADO', 'SIN FECHA'])
                    ].copy()

                    # Clasificar estructura en ambos
                    for dff in [df_mono_proy_etd, df_mono_proy_eta]:
                        dff['Estructura'] = dff[col_mono_orig].astype(str).str.strip().str.upper().apply(
                            lambda x: 'MONOPROVEEDOR' if x in ['SI', 'SÍ', 'S', 'MONOPROVEEDOR'] else 'CONSOLIDADO'
                        )

                    color_map = {'MONOPROVEEDOR': '#00a8ff', 'CONSOLIDADO': '#ffaa00'}

                    # ── UN SOLO RESUMEN ARRIBA ───────────────────────────
                    resumen_unico = df_mono_proy_etd.groupby('Estructura').agg(
                        M3_Total=('M3 Total', 'sum'), SOs=('SO', 'nunique')
                    ).reset_index() if not df_mono_proy_etd.empty else pd.DataFrame()

                    if not resumen_unico.empty:
                        resumen_unico['Share %'] = (resumen_unico['M3_Total'] / resumen_unico['M3_Total'].sum() * 100).round(1)
                        resumen_unico['CNTRS']   = (resumen_unico['M3_Total'] / 60).round(0).astype(int)
                        cols_res = st.columns(len(resumen_unico))
                        for idx, (_, row_r) in enumerate(resumen_unico.iterrows()):
                            color_r = '#00a8ff' if row_r['Estructura'] == 'MONOPROVEEDOR' else '#ffaa00'
                            with cols_res[idx]:
                                st.markdown(f"""
<div style='text-align:center; padding:14px 12px; background:rgba(255,255,255,0.02);
border-radius:12px; border-top:3px solid {color_r}; border:1px solid rgba(255,255,255,0.06); margin-bottom:14px;'>
<p style='color:#64748b; font-size:9px; letter-spacing:2px; margin:0 0 4px 0; text-transform:uppercase;'>{row_r['Estructura']}</p>
<p style='color:{color_r}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(row_r['M3_Total'])):,} <span style='font-size:11px; color:#475569;'>M3</span></p>
<div style='display:flex; justify-content:center; gap:14px; margin-top:6px;'>
    <span style='color:#94a3b8; font-size:10px;'>{row_r['Share %']}%</span>
    <span style='color:#94a3b8; font-size:10px;'>{row_r['CNTRS']} CNTRS</span>
    <span style='color:#94a3b8; font-size:10px;'>{row_r['SOs']} SOs</span>
</div>
</div>""", unsafe_allow_html=True)

                    ge1, ge2 = st.columns(2)

                    # ── GRÁFICO ETD con total M3 por mes ─────────────────
                    with ge1:
                        if not df_mono_proy_etd.empty:
                            df_stack_etd = df_mono_proy_etd.groupby(['Mes_ETD_Full', 'Estructura'])['M3 Total'].sum().reset_index()
                            df_stack_etd.columns = ['Mes', 'Estructura', 'M3']
                            # Total por mes para anotación
                            total_etd_mes = df_stack_etd.groupby('Mes')['M3'].sum().reset_index()
                            total_etd_mes.columns = ['Mes', 'Total']

                            fig_etd_m = px.bar(df_stack_etd, x='Mes', y='M3', color='Estructura',
                                barmode='stack', text='M3', color_discrete_map=color_map,
                                labels={'M3': 'M3 Total', 'Mes': '', 'Estructura': ''},
                                title='Por ETD')
                            fig_etd_m.update_traces(texttemplate='%{text:,.0f}', textposition='inside',
                                textfont=dict(size=11, color='#fff', family='Outfit, sans-serif'),
                                marker=dict(cornerradius=4))
                            # Agregar total encima de cada barra
                            for _, r in total_etd_mes.iterrows():
                                fig_etd_m.add_annotation(
                                    x=r['Mes'], y=r['Total'],
                                    text=f"<b>{int(round(r['Total'])):,}</b>",
                                    showarrow=False, yshift=10,
                                    font=dict(size=11, color='#f8fafc', family='Outfit, sans-serif')
                                )
                            fig_etd_m.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(size=12, family='Outfit, sans-serif', color='#94a3b8'),
                                title_font_color='#00ff88', title_font_size=13,
                                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text=''),
                                xaxis=dict(showgrid=False, tickangle=-30),
                                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)', title='M3'),
                                margin=dict(l=10, r=10, t=50, b=20))
                            st.plotly_chart(fig_etd_m, use_container_width=True)

                    # ── GRÁFICO ETA con total M3 por mes ─────────────────
                    with ge2:
                        if not df_mono_proy_eta.empty:
                            df_stack_eta = df_mono_proy_eta.groupby(['Mes_ETA_Full', 'Estructura'], observed=True)['M3 Total'].sum().reset_index()
                            df_stack_eta.columns = ['Mes', 'Estructura', 'M3']
                            total_eta_mes = df_stack_eta.groupby('Mes')['M3'].sum().reset_index()
                            total_eta_mes.columns = ['Mes', 'Total']

                            fig_eta_m = px.bar(df_stack_eta, x='Mes', y='M3', color='Estructura',
                                barmode='stack', text='M3', color_discrete_map=color_map,
                                labels={'M3': 'M3 Total', 'Mes': '', 'Estructura': ''},
                                title='Por ETA')
                            fig_eta_m.update_traces(texttemplate='%{text:,.0f}', textposition='inside',
                                textfont=dict(size=11, color='#fff', family='Outfit, sans-serif'),
                                marker=dict(cornerradius=4))
                            for _, r in total_eta_mes.iterrows():
                                fig_eta_m.add_annotation(
                                    x=r['Mes'], y=r['Total'],
                                    text=f"<b>{int(round(r['Total'])):,}</b>",
                                    showarrow=False, yshift=10,
                                    font=dict(size=11, color='#f8fafc', family='Outfit, sans-serif')
                                )
                            fig_eta_m.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(size=12, family='Outfit, sans-serif', color='#94a3b8'),
                                title_font_color='#ff4b4b', title_font_size=13,
                                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text=''),
                                xaxis=dict(showgrid=False, tickangle=-30),
                                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)', title='M3'),
                                margin=dict(l=10, r=10, t=50, b=20))
                            st.plotly_chart(fig_eta_m, use_container_width=True)

                    if df_mono_proy_etd.empty and df_mono_proy_eta.empty:
                        st.info("No hay carga futura proyectada con los filtros aplicados.")
            except Exception as e_mono:
                st.error(f"Error en proyección Mono/Consolidado: {e_mono}")


        except Exception as e:
            st.error(f"Error en Solapa Origen: {e}")

    # --- SOLAPA 2: COORDINACIÓN ACTIVA ---
    with tabs[1]:
        try:
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"

            @st.cache_data(ttl=60)
            def load_reserva_data(url):
                return pd.read_csv(url, engine='python', on_bad_lines='skip')

            try:
                df_res = load_reserva_data(url_reserva)
            except Exception:
                df_res = pd.read_csv(url_reserva)
            df_res.columns = df_res.columns.str.strip()

            df_g = df_res[df_res.iloc[:, 7].astype(str).apply(lambda x: len(str(x)) > 4)].copy()
            df_g['DT_Inst']      = pd.to_datetime(df_g.iloc[:, 7], dayfirst=True, errors='coerce')
            df_g['ETD_Status_K'] = df_g.iloc[:, 10].astype(str).str.upper().str.strip()
            df_g['Espera']       = (pd.to_datetime('today') - df_g['DT_Inst']).dt.days
            df_g['DT_ETD']       = pd.to_datetime(df_g.iloc[:, 12], dayfirst=True, errors='coerce')

            df_inst_s2 = df[cond_instruido].copy()

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

            m3_total_clean  = df_inst_s2['M3 Total'].apply(safe_float_f).sum()
            fob_total_clean = df_inst_s2['Fob total Origen'].apply(safe_float_f).sum()

            def clasificar_transp_res(x):
                x = str(x).upper().strip()
                if any(m in x for m in ["40 HQ", "40 ST", "40 NOR", "20 ST", "40NOR"]): return "MARITIMO"
                if any(a in x for a in ["AVION", "COURIER", "COURRIER"]): return "AEREO"
                return "OTROS"

            df_g['Transporte'] = df_g.iloc[:, 5].apply(clasificar_transp_res)
            df_mar = df_g[df_g['Transporte'] == "MARITIMO"].copy()
            df_mar.iloc[:, 1] = pd.to_numeric(df_mar.iloc[:, 1], errors='coerce').fillna(0)

            def clean_val_mar(value):
                if pd.isna(value): return 0
                s = str(value).replace('.', '').replace(',', '.')
                num = ''.join(c for c in s if c.isdigit() or c == '.')
                return pd.to_numeric(num, errors='coerce') if num else 0

            df_mar.iloc[:, 21] = df_mar.iloc[:, 21].apply(clean_val_mar).fillna(0)

            total_mar  = df_mar.iloc[:, 0].nunique()
            ok_mar     = df_mar[df_mar['ETD_Status_K'] == "OK"].iloc[:, 0].nunique()
            pend_mar   = total_mar - ok_mar
            m3_mar     = df_mar.iloc[:, 23].apply(safe_float_f).sum()
            cntr_mar   = df_mar.iloc[:, 1].apply(safe_float_f).sum()
            pct_ok_mar = round(ok_mar / total_mar * 100) if total_mar > 0 else 0

            mask_arg_mar  = df_mar.iloc[:, 3].astype(str).str.strip().str.upper() == 'ARGENTINA'
            emb_arg       = df_mar[mask_arg_mar].iloc[:, 0].nunique()
            emb_otros     = df_mar[~mask_arg_mar].iloc[:, 0].nunique()
            total_emb_dest = emb_arg + emb_otros
            pct_arg       = round(emb_arg / total_emb_dest * 100) if total_emb_dest > 0 else 0
            pct_otros     = 100 - pct_arg

            msk_mono  = df_mar.iloc[:, 32].astype(str).str.strip().str.upper().isin(['SI', 'SÍ', 'S', 'MONOPROVEEDOR'])
            df_mono_m = df_mar[msk_mono]; df_cons_m = df_mar[~msk_mono]
            tot_mc    = len(df_mono_m) + len(df_cons_m)
            pct_mono_m = round(len(df_mono_m) / tot_mc * 100) if tot_mc > 0 else 0
            pct_cons_m = 100 - pct_mono_m

            msk_adv  = df_mar.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
            pct_adv  = round(msk_adv.sum() / total_mar * 100) if total_mar > 0 else 0
            pct_spot = 100 - pct_adv

            _col_cons_name = df_res.columns[28]
            df_mar['_dias_cons'] = df_res.loc[df_mar.index, _col_cons_name].apply(safe_float_f) if _col_cons_name in df_res.columns else pd.Series(0.0, index=df_mar.index)

            def safe_median(series):
                s = series[series > 0]
                return s.median() if not s.empty else 0

            dias_mono_raw   = df_mar.loc[msk_mono, '_dias_cons']
            dias_cons_raw   = df_mar.loc[~msk_mono, '_dias_cons']
            dias_adv_raw    = df_mar.loc[msk_adv, '_dias_cons']
            dias_spot_raw   = df_mar.loc[~msk_adv, '_dias_cons']
            mediana_mono    = safe_median(dias_mono_raw)
            mediana_cons    = safe_median(dias_cons_raw)
            mediana_adv     = safe_median(dias_adv_raw)
            mediana_spot    = safe_median(dias_spot_raw)

            lunes_semana   = hoy - timedelta(days=hoy.weekday())
            domingo_semana = lunes_semana + timedelta(days=6)
            df_mar_ok      = df_mar[df_mar['ETD_Status_K'] == "OK"].copy()
            mask_semana    = (
                df_mar_ok['DT_ETD'].notna() &
                (df_mar_ok['DT_ETD'] >= pd.Timestamp(lunes_semana)) &
                (df_mar_ok['DT_ETD'] <= pd.Timestamp(domingo_semana))
            )
            df_etd_semana  = df_mar_ok[mask_semana].copy()
            cant_etd_sem   = df_etd_semana.iloc[:, 0].nunique()
            cntr_etd_sem   = df_etd_semana.iloc[:, 1].sum()
            m3_etd_sem     = df_etd_semana.iloc[:, 23].apply(safe_float_f).sum()

            msk_adv_sem  = df_etd_semana.iloc[:, 8].astype(str).str.strip() == "Booked in Advance"
            df_adv_sem   = df_etd_semana[msk_adv_sem]
            df_spot_sem  = df_etd_semana[~msk_adv_sem]

            med_adv_sem  = safe_median(df_adv_sem['_dias_cons']) if not df_adv_sem.empty else 0
            med_spot_sem = safe_median(df_spot_sem['_dias_cons']) if not df_spot_sem.empty else 0

            if pct_ok_mar >= 70:
                semaforo_color = "#00ff88"; semaforo_label = "SITUACION CONTROLADA"
            elif pct_ok_mar >= 40:
                semaforo_color = "#ffaa00"; semaforo_label = "ATENCION REQUERIDA"
            else:
                semaforo_color = "#ff4b4b"; semaforo_label = "ALERTA OPERATIVA"

            def color_dias(d, sla):
                if d <= sla: return "#00ff88"
                elif d <= sla * 1.4: return "#ffaa00"
                else: return "#ff4b4b"

            H_ROW1  = "260px"
            H_ROW2  = "180px"
            H_ROW3  = "170px"
            H_AE    = "240px"

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding:20px; background:rgba(0,168,255,0.05); border-radius:20px; margin-bottom:30px;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>COORDINACIÓN ACTIVA</h2></div>", unsafe_allow_html=True)

            k1, k2, k3, k4 = st.columns(4)
            # KPIs aéreos — se completan después de cargar df_ae_activos
            _kpi_ae_placeholder = st.columns(4)
            _kpi_ae_cols = _kpi_ae_placeholder

            # BLOQUE AEREO
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding:20px; background:rgba(168,85,247,0.05); border-radius:20px; margin-bottom:24px;'><h2 style='color:#a855f7; font-weight:800; letter-spacing:5px; margin:0;'>GESTIÓN AÉREA</h2></div>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(168,85,247,0.3); padding-bottom:10px; margin-bottom:28px;'>
<span style='color:#a855f7; font-size:13px; font-weight:800; letter-spacing:5px; text-transform:uppercase;'>AEREO</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:16px;'>SEGUIMIENTO ACTIVO</span>
</div>""", unsafe_allow_html=True)

            try:
                @st.cache_data(ttl=60)
                def load_aereos(base):
                    url_ae = f"{base}/export?format=csv&gid=88538385"
                    df_ae  = pd.read_csv(url_ae, engine='python', on_bad_lines='skip', header=0)
                    df_ae.columns = [str(c).strip() for c in df_ae.columns]
                    return df_ae

                df_ae = load_aereos(base_url)
                col_ae_estadio  = df_ae.columns[0]
                col_ae_emb      = df_ae.columns[1]
                col_ae_empresa  = df_ae.columns[2]
                col_ae_partic   = df_ae.columns[8]
                col_ae_m3       = df_ae.columns[21]
                col_ae_cant     = df_ae.columns[23]
                col_ae_tt_total = df_ae.columns[55]  # BD: Total P2P

                ORDEN_ESTADIOS = ['WAREHOUSE', 'EN ORIGEN', 'COORDINANDO', 'EN TRANSITO', 'EN TRÁNSITO', 'ARRIBADO', 'NACIONALIZADO', 'NACIONAZALIDO']
                COLORES_ESTADIOS = {
                    'WAREHOUSE': '#06b6d4', 'EN ORIGEN': '#ffaa00', 'COORDINANDO': '#f97316',
                    'EN TRANSITO': '#00a8ff', 'EN TRÁNSITO': '#00a8ff',
                    'ARRIBADO': '#a855f7', 'NACIONALIZADO': '#00ff88', 'NACIONAZALIDO': '#00ff88',
                }

                df_ae_clean = df_ae.copy()
                df_ae_clean[col_ae_estadio] = df_ae_clean[col_ae_estadio].astype(str).str.strip().str.upper()
                df_ae_activos = df_ae_clean[
                    df_ae_clean[col_ae_estadio].notna() &
                    (df_ae_clean[col_ae_estadio] != '') &
                    (df_ae_clean[col_ae_estadio] != 'NAN') &
                    (~df_ae_clean[col_ae_estadio].isin(['ENTREGADO']))
                ].copy()

                def safe_num_ae(v):
                    try: return float(str(v).replace(',', '.').strip())
                    except: return 0.0

                def safe_tt(v):
                    try:
                        val = float(str(v).replace(',', '.').strip())
                        return val if val > 0 else None
                    except: return None

                df_ae_activos[col_ae_m3]  = df_ae_activos[col_ae_m3].apply(safe_num_ae)
                df_ae_activos[col_ae_cant] = df_ae_activos[col_ae_cant].apply(safe_num_ae)
                df_ae_activos['_tt_total'] = df_ae_activos[col_ae_tt_total].apply(safe_tt)
                df_ae_activos['_partic']   = df_ae_activos[col_ae_partic].astype(str).str.strip()
                df_ae_activos['_partic']   = df_ae_activos['_partic'].replace({'': 'SIN CLASIFICAR', 'nan': 'SIN CLASIFICAR'})

                total_ae    = df_ae_activos[col_ae_emb].nunique()
                m3_ae       = df_ae_activos[col_ae_m3].sum()
                cant_ae     = df_ae_activos[col_ae_cant].sum()
                empresas_ae = df_ae_activos[col_ae_empresa].nunique()

                # FOB y Kilos para KPIs
                col_ae_fob_act = df_ae.columns[19]   # T: FOB SIMI TOTAL
                col_ae_cw_act  = df_ae.columns[57]   # BF: Chargeable Weight
                def safe_ae_num(v):
                    try:
                        s = str(v).strip().replace(' ','')
                        if s in ['','nan','None','-']: return 0.0
                        if ',' in s and '.' in s:
                            if s.index('.') < s.index(','): s = s.replace('.','').replace(',','.')
                            else: s = s.replace(',','')
                        elif ',' in s: s = s.replace(',','.')
                        return float(s)
                    except: return 0.0
                fob_ae_act = df_ae_activos[col_ae_fob_act].apply(safe_ae_num).sum()
                cw_ae_act  = df_ae_activos[col_ae_cw_act].apply(safe_ae_num).sum()

                # Llenar KPIs aéreos arriba
                with _kpi_ae_cols[0]: st.markdown(f"<div class='metric-container'><p>EMBARQUES AÉREOS</p><p style='color:#a855f7; font-size:22px; font-weight:900; margin:0;'>{total_ae}</p></div>", unsafe_allow_html=True)
                with _kpi_ae_cols[1]: st.markdown(f"<div class='metric-container'><p>VOLUMEN</p><p style='color:#a855f7; font-size:22px; font-weight:900; margin:0;'>{int(round(m3_ae)):,} <span style='font-size:13px; color:#475569;'>M3</span></p></div>", unsafe_allow_html=True)
                with _kpi_ae_cols[2]: st.markdown(f"<div class='metric-container'><p>FOB AÉREO</p><p style='color:#ffaa00; font-size:20px; font-weight:900; margin:0;'>USD {fob_ae_act/1_000_000:.1f}M</p></div>", unsafe_allow_html=True)
                with _kpi_ae_cols[3]: st.markdown(f"<div class='metric-container'><p>CHARGEABLE WEIGHT</p><p style='color:#00a8ff; font-size:20px; font-weight:900; margin:0;'>{int(round(cw_ae_act)):,} <span style='font-size:13px; color:#475569;'>kg</span></p></div>", unsafe_allow_html=True)

                H_AE_PX = 260
                col_ae_num, col_ae_estadios = st.columns([1, 2])
                with col_ae_num:
                    st.markdown(f"""
<div style='background:linear-gradient(145deg,rgba(168,85,247,0.07),rgba(168,85,247,0.02));
border-radius:20px; border:1px solid rgba(168,85,247,0.15); padding:24px;
height:{H_AE_PX}px; box-sizing:border-box;
display:flex; flex-direction:column; justify-content:space-between;'>
<div>
    <p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0 0 4px 0; text-transform:uppercase;'>Embarques aereos activos</p>
    <p style='color:#f8fafc; font-size:80px; font-weight:900; margin:0; line-height:1; letter-spacing:-4px;'>{total_ae}</p>
</div>
<div style='display:flex; gap:16px; flex-wrap:wrap;'>
    <div><p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 2px 0;'>VOLUMEN</p><p style='color:#a855f7; font-size:18px; font-weight:800; margin:0;'>{int(round(m3_ae)):,} M3</p></div>
    <div><p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 2px 0;'>UNIDADES</p><p style='color:#a855f7; font-size:18px; font-weight:800; margin:0;'>{int(cant_ae):,}</p></div>
    <div><p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 2px 0;'>EMPRESAS</p><p style='color:#a855f7; font-size:18px; font-weight:800; margin:0;'>{empresas_ae}</p></div>
</div>
</div>""", unsafe_allow_html=True)

                # Participación por tipo — fila completa debajo
                st.markdown("<br>", unsafe_allow_html=True)
                COLORES_PARTIC = ['#a855f7', '#00a8ff', '#ffaa00', '#00ff88', '#ff4b4b', '#06b6d4']
                conteo_partic = df_ae_activos.groupby('_partic').agg(
                    Embarques=(col_ae_emb, 'nunique'),
                    M3=(col_ae_m3, 'sum'),
                    Unidades=(col_ae_cant, 'sum')
                ).reset_index().sort_values('Embarques', ascending=False).reset_index(drop=True)
                # Agregar tiempo punta a punta (col BB idx 53)
                tt_por_tipo = df_ae_activos.groupby('_partic')['_tt_total'].median().reset_index()
                tt_por_tipo.columns = ['_partic', 'TT_Med']
                conteo_partic = conteo_partic.merge(tt_por_tipo, on='_partic', how='left')
                total_emb_ae = conteo_partic['Embarques'].sum()

                # Cards por tipo para director comercial
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='border-bottom:1px solid rgba(168,85,247,0.2); padding-bottom:8px; margin-bottom:20px;'>
<span style='color:#a855f7; font-size:11px; font-weight:800; letter-spacing:4px; text-transform:uppercase;'>PARTICIPACIÓN POR TIPO DE NEGOCIO</span>
</div>""", unsafe_allow_html=True)

                tt_global_med = conteo_partic['TT_Med'].median()

                # Headers tabla
                hh1,hh2,hh3,hh4,hh5,hh6 = st.columns([1.4, 0.7, 0.7, 0.7, 0.8, 0.7])
                hh1.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700;'>TIPO DE NEGOCIO</p>", unsafe_allow_html=True)
                hh2.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>EMBARQUES</p>", unsafe_allow_html=True)
                hh3.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>%</p>", unsafe_allow_html=True)
                hh4.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>M3</p>", unsafe_allow_html=True)
                hh5.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>UNIDADES</p>", unsafe_allow_html=True)
                hh6.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>✈️ P2P</p>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0 8px 0; border:none; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)

                for pi, (_, rp) in enumerate(conteo_partic.sort_values('Embarques', ascending=False).iterrows()):
                    col_p = COLORES_PARTIC[pi % len(COLORES_PARTIC)]
                    pct_p = round(rp['Embarques'] / total_emb_ae * 100) if total_emb_ae > 0 else 0
                    tt_val = rp.get('TT_Med')
                    if pd.notna(tt_val) and tt_val:
                        tt_num = int(round(tt_val))
                        if tt_global_med and pd.notna(tt_global_med):
                            if tt_num <= tt_global_med:       tt_color = '#00ff88'
                            elif tt_num <= tt_global_med*1.3: tt_color = '#ffaa00'
                            else:                             tt_color = '#ff4b4b'
                        else: tt_color = '#94a3b8'
                        tt_str = f"{tt_num}d"
                    else:
                        tt_str = '—'; tt_color = '#475569'

                    cc1,cc2,cc3,cc4,cc5,cc6 = st.columns([1.4, 0.7, 0.7, 0.7, 0.8, 0.7])
                    cc1.markdown(f"<p style='color:{col_p}; font-size:14px; font-weight:800; margin:6px 0;'>{rp['_partic']}</p>", unsafe_allow_html=True)
                    m3_val_ae  = int(round(rp['M3']))
                    uni_val_ae = int(round(rp['Unidades']))
                    cc2.markdown(f"<p style='color:#f8fafc; font-size:15px; font-weight:900; text-align:center; margin:6px 0;'>{int(rp['Embarques'])}</p>", unsafe_allow_html=True)
                    cc3.markdown(f"<p style='color:{col_p}; font-size:14px; font-weight:700; text-align:center; margin:6px 0;'>{pct_p}%</p>", unsafe_allow_html=True)
                    cc4.markdown(f"<p style='color:#00a8ff; font-size:14px; font-weight:700; text-align:center; margin:6px 0;'>{m3_val_ae:,}</p>", unsafe_allow_html=True)
                    cc5.markdown(f"<p style='color:#94a3b8; font-size:14px; text-align:center; margin:6px 0;'>{uni_val_ae:,}</p>", unsafe_allow_html=True)
                    cc6.markdown(f"<p style='color:{tt_color}; font-size:15px; font-weight:900; text-align:center; margin:6px 0;'>{tt_str}</p>", unsafe_allow_html=True)

                st.markdown("<hr style='margin:8px 0 16px 0; border:none; border-top:1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)



                with col_ae_estadios:
                    st.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:4px; font-weight:700; text-transform:uppercase; margin:0 0 6px 0;'>ESTADIOS DE LAS CARGAS</p>", unsafe_allow_html=True)
                    orden_idx = {e: i for i, e in enumerate(ORDEN_ESTADIOS)}
                    conteo_e = df_ae_activos.groupby(col_ae_estadio).agg(
                        Embarques=(col_ae_emb, 'nunique'),
                        M3=(col_ae_m3, 'sum')
                    ).reset_index()
                    conteo_e.columns = ['Estadio', 'Embarques', 'M3']
                    conteo_e['_ord'] = conteo_e['Estadio'].map(lambda x: orden_idx.get(x, 99))
                    conteo_e = conteo_e.sort_values('_ord').reset_index(drop=True)
                    conteo_e['Color'] = conteo_e['Estadio'].map(lambda x: COLORES_ESTADIOS.get(x, '#94a3b8'))
                    conteo_e['Label'] = conteo_e.apply(lambda r: f"  {int(r['Embarques'])} emb · {int(round(r['M3']))} M3", axis=1)

                    fig_ae = px.bar(conteo_e, y='Estadio', x='Embarques', orientation='h',
                        text='Label', color='Estadio',
                        color_discrete_map={r['Estadio']: r['Color'] for _, r in conteo_e.iterrows()})
                    fig_ae.update_traces(textposition='outside', cliponaxis=False,
                        textfont=dict(size=11, color='#94a3b8', family='Outfit, sans-serif'),
                        marker=dict(cornerradius=5))
                    fig_ae.update_layout(height=H_AE_PX, showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Outfit, sans-serif', color='#94a3b8', size=11),
                        margin=dict(l=0, r=150, t=0, b=0),
                        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)',
                                   zeroline=False, showticklabels=False, title=''),
                        yaxis=dict(showgrid=False, title='',
                                   tickfont=dict(size=11, color='#94a3b8'),
                                   categoryorder='array',
                                   categoryarray=conteo_e['Estadio'].tolist()[::-1]))
                    st.plotly_chart(fig_ae, use_container_width=True)

            except Exception as e_ae:
                st.error(f"Error en seccion Aereos: {e_ae}")
                import traceback; st.code(traceback.format_exc())

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding:20px; background:rgba(0,168,255,0.05); border-radius:20px; margin-bottom:24px;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>GESTIÓN MARÍTIMA</h2></div>", unsafe_allow_html=True)
            # KPIs marítimos
            km1,km2,km3,km4 = st.columns(4)
            with km1: st.markdown(f"<div class='metric-container'><p>SO EN PROCESO</p><p style='color:#f8fafc; font-size:22px; font-weight:900; margin:0;'>{int(df_inst_s2['SO'].nunique())}</p></div>", unsafe_allow_html=True)
            with km2: st.markdown(f"<div class='metric-container'><p>VOLUMEN TOTAL</p><p style='color:#00a8ff; font-size:22px; font-weight:900; margin:0;'>{int(round(m3_total_clean)):,} <span style='font-size:13px; color:#475569;'>M3</span></p></div>", unsafe_allow_html=True)
            with km3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p style='color:#f8fafc; font-size:22px; font-weight:900; margin:0;'>{int(df_inst_s2['Proveedor'].nunique())}</p></div>", unsafe_allow_html=True)
            with km4: st.markdown(f"<div class='metric-container'><p>FOB EN PROCESO</p><p style='color:#ffaa00; font-size:20px; font-weight:900; margin:0;'>USD {round(fob_total_clean/1_000_000,1)}M</p></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
<div style='border-bottom:2px solid rgba(0,168,255,0.3); padding-bottom:10px; margin-bottom:28px;'>
<span style='color:#00a8ff; font-size:13px; font-weight:800; letter-spacing:5px; text-transform:uppercase;'>MARITIMO</span>
<span style='color:#475569; font-size:11px; letter-spacing:2px; margin-left:16px;'>RESERVAS ACTIVAS</span>
</div>""", unsafe_allow_html=True)

            col_big, col_sem = st.columns([1.2, 1])
            with col_big:
                st.markdown(f"""
<div style='background:linear-gradient(145deg, rgba(0,168,255,0.07), rgba(0,168,255,0.02));
border-radius:20px; border:1px solid rgba(0,168,255,0.15); padding:28px;
min-height:260px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<div>
    <p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 6px 0; text-transform:uppercase;'>Embarques bajo gestion</p>
    <p style='color:#f8fafc; font-size:88px; font-weight:900; margin:0; line-height:1; letter-spacing:-4px;'>{total_mar}</p>
</div>
<div style='display:flex; gap:28px; margin-top:12px;'>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>CONTENEDORES</p>
        <p style='color:#00a8ff; font-size:22px; font-weight:800; margin:0;'>{int(cntr_mar)}</p>
    </div>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>VOLUMEN</p>
        <p style='color:#00a8ff; font-size:22px; font-weight:800; margin:0;'>{int(round(m3_mar)):,} M3</p>
    </div>
</div>
<div style='border-top:1px solid rgba(255,255,255,0.07); padding-top:14px; display:flex; gap:24px;'>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>ARGENTINA</p>
        <p style='color:#f8fafc; font-size:17px; font-weight:800; margin:0;'>{pct_arg}% <span style='font-size:12px; color:#475569; font-weight:400;'>({emb_arg} emb)</span></p>
    </div>
    <div>
        <p style='color:#64748b; font-size:10px; letter-spacing:1px; margin:0 0 3px 0;'>OTROS DESTINOS</p>
        <p style='color:#f8fafc; font-size:17px; font-weight:800; margin:0;'>{pct_otros}% <span style='font-size:12px; color:#475569; font-weight:400;'>({emb_otros} emb)</span></p>
    </div>
</div>
</div>""", unsafe_allow_html=True)

            with col_sem:
                # Forwarders pendientes (sin ETD OK)
                col_fwd_res = df_res.columns[6]  # G: Forwarder
                df_pend_fwd = df_mar[df_mar['ETD_Status_K'] != 'OK'].copy()
                fwd_pend = df_pend_fwd.groupby(df_pend_fwd.iloc[:,6].astype(str).str.strip()).agg(
                    Pend=(df_mar.columns[0], 'nunique')
                ).reset_index()
                fwd_pend.columns = ['Forwarder', 'Pend']
                fwd_pend = fwd_pend[fwd_pend['Forwarder'].str.upper() != 'NAN'].sort_values('Pend', ascending=False)
                fwd_pend['Pct'] = (fwd_pend['Pend'] / fwd_pend['Pend'].sum() * 100).round(0).astype(int)

                fwd_rows = ''.join([
                    f"<div style='display:flex; justify-content:space-between; margin:3px 0;'>"
                    f"<span style='color:#94a3b8; font-size:11px;'>{r['Forwarder']}</span>"
                    f"<span style='color:#ff4b4b; font-size:11px; font-weight:700;'>{int(r['Pend'])} emb · {r['Pct']}%</span>"
                    f"</div>"
                    for _, r in fwd_pend.iterrows()
                ])

                st.markdown(f"""
<div style='background:rgba(255,255,255,0.02); border-radius:20px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
min-height:260px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<div>
    <p style='color:#64748b; font-size:11px; letter-spacing:3px; margin:0 0 8px 0; text-transform:uppercase;'>Estado ETD</p>
    <div style='display:flex; align-items:baseline; gap:12px;'>
        <p style='color:{semaforo_color}; font-size:52px; font-weight:900; margin:0; line-height:1;'>{pct_ok_mar}%</p>
        <div>
            <p style='color:{semaforo_color}; font-size:11px; font-weight:800; letter-spacing:2px; margin:0;'>{semaforo_label}</p>
            <p style='color:#475569; font-size:10px; margin:3px 0 0 0;'>{ok_mar} OK · {pend_mar} pendientes</p>
        </div>
    </div>
    <div style='height:4px; background:rgba(255,255,255,0.07); border-radius:2px; margin:10px 0 12px 0;'>
        <div style='height:4px; width:{pct_ok_mar}%; background:{semaforo_color}; border-radius:2px;'></div>
    </div>
    <p style='color:#64748b; font-size:9px; letter-spacing:2px; margin:0 0 6px 0; text-transform:uppercase;'>Pendientes por agente</p>
    {fwd_rows}
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col_est, col_book, col_cons = st.columns(3)
            with col_est:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
min-height:180px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0; text-transform:uppercase;'>Estructura de carga</p>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#00a8ff; font-size:12px; font-weight:700; margin:0;'>MONOPROVEEDOR</p>
        <p style='color:#00a8ff; font-size:20px; font-weight:900; margin:0;'>{pct_mono_m}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_mono_m}%; background:#00a8ff; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:11px; margin:4px 0 0 0;'>{len(df_mono_m)} embarques</p>
</div>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#ffaa00; font-size:12px; font-weight:700; margin:0;'>CONSOLIDADO</p>
        <p style='color:#ffaa00; font-size:20px; font-weight:900; margin:0;'>{pct_cons_m}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_cons_m}%; background:#ffaa00; border-radius:3px;'></div>
    </div>
    <p style='color:#334155; font-size:11px; margin:4px 0 0 0;'>{len(df_cons_m)} embarques</p>
</div>
</div>""", unsafe_allow_html=True)

            with col_book:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
min-height:180px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0; text-transform:uppercase;'>Modalidad de booking</p>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#00ff88; font-size:12px; font-weight:700; margin:0;'>IN ADVANCE</p>
        <p style='color:#00ff88; font-size:20px; font-weight:900; margin:0;'>{pct_adv}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_adv}%; background:#00ff88; border-radius:3px;'></div>
    </div>
</div>
<div>
    <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
        <p style='color:#94a3b8; font-size:12px; font-weight:700; margin:0;'>SPOT</p>
        <p style='color:#94a3b8; font-size:20px; font-weight:900; margin:0;'>{pct_spot}%</p>
    </div>
    <div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
        <div style='height:5px; width:{pct_spot}%; background:#94a3b8; border-radius:3px;'></div>
    </div>
</div>
</div>""", unsafe_allow_html=True)

            with col_cons:
                cm = color_dias(mediana_mono, 7)
                cc = color_dias(mediana_cons, 25)
                ca = color_dias(mediana_adv, 20)
                cs = color_dias(mediana_spot, 20)
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:24px;
min-height:180px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:3px; margin:0; text-transform:uppercase;'>Tiempo de consolidacion (mediana)</p>
<div style='display:grid; grid-template-columns:1fr 1fr; gap:8px; flex:1; align-content:center;'>
    <div style='background:rgba(0,168,255,0.07); border-radius:10px; padding:10px; text-align:center;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>MONO</p>
        <p style='color:{cm}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_mono))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>SLA: 7d</p>
    </div>
    <div style='background:rgba(255,170,0,0.07); border-radius:10px; padding:10px; text-align:center;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>CONSOLIDADO</p>
        <p style='color:{cc}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_cons))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>SLA: 25d</p>
    </div>
    <div style='background:rgba(0,255,136,0.06); border-radius:10px; padding:10px; text-align:center;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>IN ADVANCE</p>
        <p style='color:{ca}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_adv))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>ref: 20d</p>
    </div>
    <div style='background:rgba(148,163,184,0.06); border-radius:10px; padding:10px; text-align:center;'>
        <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>SPOT</p>
        <p style='color:{cs}; font-size:26px; font-weight:900; margin:0; line-height:1;'>{int(round(mediana_spot))}d</p>
        <p style='color:#334155; font-size:9px; margin:3px 0 0 0;'>ref: 20d</p>
    </div>
</div>
</div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
<div style='border-bottom:1px solid rgba(0,168,255,0.15); padding-bottom:8px; margin-bottom:20px;'>
<span style='color:#64748b; font-size:11px; font-weight:700; letter-spacing:4px; text-transform:uppercase;'>ETD ESTA SEMANA</span>
<span style='color:#334155; font-size:11px; letter-spacing:2px; margin-left:14px;'>{lunes_semana.strftime("%d/%m")} al {domingo_semana.strftime("%d/%m/%Y")}</span>
</div>""", unsafe_allow_html=True)

            cma = color_dias(med_adv_sem, 20)
            cms = color_dias(med_spot_sem, 20)
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.markdown(f"""
<div style='background:linear-gradient(145deg, rgba(0,168,255,0.07), rgba(0,168,255,0.02));
border-radius:16px; border:1px solid rgba(0,168,255,0.15); padding:22px;
min-height:170px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Embarques con ETD OK</p>
<p style='color:#f8fafc; font-size:58px; font-weight:900; margin:0; line-height:1; letter-spacing:-2px;'>{cant_etd_sem}</p>
<div>
    <p style='color:#64748b; font-size:10px; margin:0 0 2px 0;'>CONTENEDORES</p>
    <p style='color:#00a8ff; font-size:18px; font-weight:800; margin:0;'>{int(cntr_etd_sem)}</p>
</div>
</div>""", unsafe_allow_html=True)
            with col_s2:
                st.markdown(f"""
<div style='background:rgba(255,255,255,0.03); border-radius:16px;
border:1px solid rgba(255,255,255,0.07); padding:22px;
min-height:170px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Volumen a zarpar</p>
<p style='color:#f8fafc; font-size:48px; font-weight:900; margin:0; line-height:1;'>{int(round(m3_etd_sem)):,}</p>
<p style='color:#475569; font-size:13px; font-weight:600; margin:0;'>M3 esta semana</p>
</div>""", unsafe_allow_html=True)
            with col_s3:
                st.markdown(f"""
<div style='background:rgba(0,255,136,0.04); border-radius:16px;
border:1px solid rgba(0,255,136,0.1); padding:22px;
min-height:170px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Consolidacion In Advance (mediana)</p>
<div>
    <p style='color:{cma}; font-size:52px; font-weight:900; margin:0; line-height:1;'>{int(round(med_adv_sem))}d</p>
    <p style='color:#334155; font-size:10px; margin:6px 0 0 0;'>{len(df_adv_sem)} embarques · ref: 20d</p>
</div>
<div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
    <div style='height:5px; width:{min(int(round(med_adv_sem/20*100)), 100)}%; background:{cma}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)
            with col_s4:
                st.markdown(f"""
<div style='background:rgba(148,163,184,0.04); border-radius:16px;
border:1px solid rgba(148,163,184,0.1); padding:22px;
min-height:170px; height:auto; box-sizing:border-box; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
<p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0; text-transform:uppercase;'>Consolidacion Spot (mediana)</p>
<div>
    <p style='color:{cms}; font-size:52px; font-weight:900; margin:0; line-height:1;'>{int(round(med_spot_sem))}d</p>
    <p style='color:#334155; font-size:10px; margin:6px 0 0 0;'>{len(df_spot_sem)} embarques · ref: 20d</p>
</div>
<div style='height:5px; background:rgba(255,255,255,0.06); border-radius:3px;'>
    <div style='height:5px; width:{min(int(round(med_spot_sem/20*100)), 100)}%; background:{cms}; border-radius:3px;'></div>
</div>
</div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error en Coordinacion Activa: {e}")
            import traceback
            st.code(traceback.format_exc())


    # --- SOLAPA 3: PERFORMANCE DE ANALISTAS ---
    with tabs[2]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>PERFORMANCE DE ANALISTAS</h2><p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>BASADO EN RESERVAS HISTÓRICAS · 2026</p></div>", unsafe_allow_html=True)
        try:
            @st.cache_data(ttl=120)
            def load_perf_data(base):
                url_res_hi = f"{base}/export?format=csv&gid=32771816"
                url_emb_hi = f"{base}/export?format=csv&gid=50628730"
                rh = pd.read_csv(url_res_hi, engine='python', on_bad_lines='skip', header=0)
                eh = pd.read_csv(url_emb_hi, engine='python', on_bad_lines='skip', header=0)
                rh.columns = [str(c).strip() for c in rh.columns]
                eh.columns = [str(c).strip() for c in eh.columns]
                return rh, eh

            df_rh, df_eh = load_perf_data(base_url)

            # Columnas Reservas Historicas
            # col A (0)=Embarque, col O (14)=Responsable, col Y (24)=Monoproveedor, col AG (32)=Tiempo cons
            col_rh_emb   = df_rh.columns[0]
            col_rh_resp  = df_rh.columns[14]
            col_rh_mono  = df_rh.columns[24]
            col_rh_tcons = df_rh.columns[32]

            # Columnas Embarques Historicos
            # col A (0)=SO, col E (4)=Embarque, col G (6)=ETD, col S (18)=Proveedor
            col_eh_so   = df_eh.columns[0]
            col_eh_emb  = df_eh.columns[4]
            col_eh_etd  = df_eh.columns[6]
            col_eh_prov = df_eh.columns[18]

            df_eh['ETD_DT'] = pd.to_datetime(df_eh[col_eh_etd], dayfirst=True, errors='coerce')
            df_eh_2026 = df_eh[df_eh['ETD_DT'].dt.year == 2026].copy()
            df_eh_2026['Mes_Num']   = df_eh_2026['ETD_DT'].dt.month
            df_eh_2026['Mes_Label'] = df_eh_2026['ETD_DT'].dt.strftime('%B %Y').str.upper()

            if df_eh_2026.empty:
                st.warning("No se encontraron embarques históricos para 2026.")
            else:
                meses_disp = df_eh_2026.drop_duplicates('Mes_Num').sort_values('Mes_Num')[['Mes_Num','Mes_Label']].values.tolist()
                opciones_mes = {lbl: num for num, lbl in meses_disp}

                col_sel, _ = st.columns([2, 3])
                with col_sel:
                    mes_sel_lbl = st.selectbox("SELECCIONAR MES ETD:", list(opciones_mes.keys()), key="perf_mes_sel")
                mes_sel_num = opciones_mes[mes_sel_lbl]

                df_eh_mes = df_eh_2026[df_eh_2026['Mes_Num'] == mes_sel_num].copy()
                embs_mes  = df_eh_mes[col_eh_emb].astype(str).str.strip().str.upper().unique()

                df_rh['_emb_key'] = df_rh[col_rh_emb].astype(str).str.strip().str.upper()
                df_rh_mes = df_rh[df_rh['_emb_key'].isin(embs_mes)].copy()

                def clean_tcons(val):
                    try: return float(str(val).replace(',','.').strip())
                    except: return None

                df_rh_mes['T_Cons_Num'] = df_rh_mes[col_rh_tcons].apply(clean_tcons)
                df_rh_mes['Tipo_Carga'] = df_rh_mes[col_rh_mono].astype(str).str.strip().str.upper().apply(
                    lambda x: 'MONOPROVEEDOR' if 'MONO' in x else 'CONSOLIDADO'
                )
                df_rh_mes['Responsable'] = df_rh_mes[col_rh_resp].astype(str).str.strip()
                df_rh_mes = df_rh_mes[~df_rh_mes['Responsable'].isin(['', 'nan', 'NaN', 'None', '-', 'nan'])]

                if df_rh_mes.empty:
                    st.warning(f"No se encontraron datos para {mes_sel_lbl}.")
                else:
                    total_embs_mes  = len(embs_mes)
                    total_sos_mes   = df_eh_mes[col_eh_so].nunique()
                    total_provs_mes = df_eh_mes[col_eh_prov].nunique()
                    total_mono_mes  = (df_rh_mes['Tipo_Carga'] == 'MONOPROVEEDOR').sum()
                    total_cons_mes  = (df_rh_mes['Tipo_Carga'] == 'CONSOLIDADO').sum()
                    avg_tcons_mes   = df_rh_mes['T_Cons_Num'].mean()

                    st.markdown("<br>", unsafe_allow_html=True)
                    k1, k2, k3, k4, k5 = st.columns(5)
                    with k1: st.markdown(f"<div class='metric-container'><p>EMBARQUES</p><p>{total_embs_mes}</p></div>", unsafe_allow_html=True)
                    with k2: st.markdown(f"<div class='metric-container'><p>SOs TOTALES</p><p>{total_sos_mes}</p></div>", unsafe_allow_html=True)
                    with k3: st.markdown(f"<div class='metric-container'><p>PROVEEDORES</p><p>{total_provs_mes}</p></div>", unsafe_allow_html=True)
                    with k4: st.markdown(f"<div class='metric-container'><p>MONO / CONS</p><p style='font-size:40px !important;'>{total_mono_mes} / {total_cons_mes}</p></div>", unsafe_allow_html=True)
                    with k5: st.markdown(f"<div class='metric-container'><p>DIAS PROM. CONS.</p><p>{int(round(avg_tcons_mes)) if pd.notna(avg_tcons_mes) else 0}</p></div>", unsafe_allow_html=True)

                    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#00a8ff; font-weight:800; letter-spacing:4px; font-size:16px; margin-bottom:20px; text-align:center;'>DESEMPENO POR ANALISTA</p>", unsafe_allow_html=True)

                    rows_analistas = []
                    for analista, grp_a in df_rh_mes.groupby('Responsable'):
                        embs_a   = grp_a['_emb_key'].unique()
                        df_eh_a  = df_eh_mes[df_eh_mes[col_eh_emb].astype(str).str.strip().str.upper().isin(embs_a)]
                        cant_embs    = len(embs_a)
                        cant_sos     = df_eh_a[col_eh_so].nunique()
                        cant_provs   = df_eh_a[col_eh_prov].nunique()
                        cant_mono    = (grp_a['Tipo_Carga'] == 'MONOPROVEEDOR').sum()
                        cant_cons    = (grp_a['Tipo_Carga'] == 'CONSOLIDADO').sum()
                        avg_tcons    = grp_a['T_Cons_Num'].mean()
                        avg_so_emb   = round(cant_sos / cant_embs, 1) if cant_embs > 0 else 0
                        prov_por_emb = df_eh_a.groupby(
                            df_eh_a[col_eh_emb].astype(str).str.strip().str.upper()
                        )[col_eh_prov].nunique()
                        avg_prov_emb = round(prov_por_emb.mean(), 1) if not prov_por_emb.empty else 0

                        # AZUL: aéreos, sin metodología de consolidación marítima
                        es_azul = analista.strip().upper() == 'AZUL'
                        dias_cons_val = "✈️ En preparación" if es_azul else (f"{round(avg_tcons, 1)} d" if pd.notna(avg_tcons) else "—")

                        rows_analistas.append({
                            'Analista'         : analista,
                            'Embarques'        : cant_embs,
                            'SOs'              : cant_sos,
                            'Proveedores'      : cant_provs,
                            'Monoproveedor'    : int(cant_mono),
                            'Consolidado'      : int(cant_cons),
                            'Dias Prom. Cons.' : dias_cons_val,
                            'SO por Embarque'  : avg_so_emb,
                            'Prov por Embarque': avg_prov_emb,
                        })

                    df_analistas = pd.DataFrame(rows_analistas).sort_values('Embarques', ascending=False)
                    st.dataframe(
                        df_analistas, use_container_width=True, hide_index=True,
                        column_config={
                            'Analista'         : st.column_config.TextColumn("Analista"),
                            'Embarques'        : st.column_config.NumberColumn("Embarques", format="%d"),
                            'SOs'              : st.column_config.NumberColumn("SOs", format="%d"),
                            'Proveedores'      : st.column_config.NumberColumn("Proveedores", format="%d"),
                            'Monoproveedor'    : st.column_config.NumberColumn("Mono", format="%d"),
                            'Consolidado'      : st.column_config.NumberColumn("Consolidado", format="%d"),
                            'Dias Prom. Cons.' : st.column_config.TextColumn("Dias Prom. Cons."),
                            'SO por Embarque'  : st.column_config.NumberColumn("SO/Emb", format="%.1f"),
                            'Prov por Embarque': st.column_config.NumberColumn("Prov/Emb", format="%.1f"),
                        }
                    )

                    st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#00ff88; font-weight:800; letter-spacing:4px; font-size:16px; margin-bottom:20px; text-align:center;'>EVOLUCION MES A MES POR ANALISTA</p>", unsafe_allow_html=True)

                    rows_evol = []
                    for mes_num, mes_lbl in meses_disp:
                        df_eh_m = df_eh_2026[df_eh_2026['Mes_Num'] == mes_num]
                        embs_m  = df_eh_m[col_eh_emb].astype(str).str.strip().str.upper().unique()
                        df_rh_m = df_rh[df_rh['_emb_key'].isin(embs_m)].copy()
                        df_rh_m['T_Cons_Num'] = df_rh_m[col_rh_tcons].apply(clean_tcons)
                        df_rh_m['Tipo_Carga'] = df_rh_m[col_rh_mono].astype(str).str.strip().str.upper().apply(
                            lambda x: 'MONOPROVEEDOR' if 'MONO' in x else 'CONSOLIDADO'
                        )
                        df_rh_m['Responsable'] = df_rh_m[col_rh_resp].astype(str).str.strip()
                        df_rh_m = df_rh_m[~df_rh_m['Responsable'].isin(['', 'nan', 'NaN', 'None', '-', 'nan'])]
                        for analista, grp_a in df_rh_m.groupby('Responsable'):
                            embs_a  = grp_a['_emb_key'].unique()
                            df_eh_a = df_eh_m[df_eh_m[col_eh_emb].astype(str).str.strip().str.upper().isin(embs_a)]
                            avg_tc  = grp_a['T_Cons_Num'].mean()
                            rows_evol.append({
                                'Mes_Num'   : mes_num,
                                'Mes'       : mes_lbl,
                                'Analista'  : analista,
                                'Embarques' : len(embs_a),
                                'SOs'       : df_eh_a[col_eh_so].nunique(),
                                'Dias Cons.': round(avg_tc, 1) if pd.notna(avg_tc) else None,
                            })

                    df_evol = pd.DataFrame(rows_evol)
                    if not df_evol.empty:
                        analistas_disp = sorted(df_evol['Analista'].unique())
                        col_pick, _ = st.columns([2, 3])
                        with col_pick:
                            analista_sel = st.selectbox("VER EVOLUCION DE:", analistas_disp, key="perf_analista_sel")
                        df_evol_a = df_evol[df_evol['Analista'] == analista_sel].sort_values('Mes_Num')

                        es_azul_sel = analista_sel.strip().upper() == 'AZUL'

                        if es_azul_sel:
                            # AZUL: solo gráfico de embarques, sin consolidación
                            st.plotly_chart(
                                px.bar(df_evol_a, x='Mes', y='Embarques', text_auto=',.0f',
                                       color_discrete_sequence=['#00a8ff'],
                                       title=f"Embarques - {analista_sel}"
                                ).update_traces(textposition='outside', textfont_color='#f8fafc', marker=dict(cornerradius=5)
                                ).update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                                font=dict(family='Outfit, sans-serif', color='#94a3b8'),
                                                title_font_color='#00a8ff',
                                                xaxis=dict(showgrid=False, tickangle=-30),
                                                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'),
                                                margin=dict(l=10,r=10,t=50,b=40)),
                                use_container_width=True
                            )
                            st.info("✈️ Azul gestiona cargas aéreas — los tiempos de consolidación marítima no aplican a su metodología.")
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.dataframe(
                                df_evol_a[['Mes','Embarques','SOs']].reset_index(drop=True),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'Mes'      : st.column_config.TextColumn("Mes ETD"),
                                    'Embarques': st.column_config.NumberColumn("Embarques", format="%d"),
                                    'SOs'      : st.column_config.NumberColumn("SOs", format="%d"),
                                }
                            )
                        else:
                            ev1, ev2 = st.columns(2)
                            with ev1:
                                fig_ev_emb = px.bar(df_evol_a, x='Mes', y='Embarques', text_auto=',.0f', color_discrete_sequence=['#00a8ff'], title=f"Embarques - {analista_sel}")
                                fig_ev_emb.update_traces(textposition='outside', textfont_color='#f8fafc', marker=dict(cornerradius=5))
                                fig_ev_emb.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Outfit, sans-serif', color='#94a3b8'), title_font_color='#00a8ff', xaxis=dict(showgrid=False, tickangle=-30), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'), margin=dict(l=10,r=10,t=50,b=40))
                                st.plotly_chart(fig_ev_emb, use_container_width=True)
                            with ev2:
                                fig_ev_tc = px.bar(df_evol_a, x='Mes', y='Dias Cons.', text_auto=',.1f', color_discrete_sequence=['#00ff88'], title=f"Dias Prom. Consolidacion - {analista_sel}")
                                fig_ev_tc.update_traces(textposition='outside', textfont_color='#f8fafc', marker=dict(cornerradius=5))
                                fig_ev_tc.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family='Outfit, sans-serif', color='#94a3b8'), title_font_color='#00ff88', xaxis=dict(showgrid=False, tickangle=-30), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)'), margin=dict(l=10,r=10,t=50,b=40))
                                st.plotly_chart(fig_ev_tc, use_container_width=True)

                            st.markdown("<br>", unsafe_allow_html=True)
                            st.dataframe(
                                df_evol_a[['Mes','Embarques','SOs','Dias Cons.']].reset_index(drop=True),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'Mes'       : st.column_config.TextColumn("Mes ETD"),
                                    'Embarques' : st.column_config.NumberColumn("Embarques", format="%d"),
                                    'SOs'       : st.column_config.NumberColumn("SOs", format="%d"),
                                    'Dias Cons.': st.column_config.NumberColumn("Dias Prom. Cons.", format="%.1f d"),
                                }
                            )

        except Exception as e:
            st.error(f"Error en Performance Analistas: {e}")
            import traceback
            st.code(traceback.format_exc())

        # PERFORMANCE DE AGENTES (FORWARDERS)
        st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(255,170,0,0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#ffaa00; font-weight:800; letter-spacing:5px; margin:0;'>PERFORMANCE DE AGENTES (FORWARDERS)</h2><p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>BASADO EN RESERVAS HISTORICAS 2026</p></div>", unsafe_allow_html=True)
        try:
            try:
                _ = df_rh
            except NameError:
                df_rh, df_eh = load_perf_data(base_url)

            col_ag_fwd        = df_rh.columns[6]
            col_ag_inst       = df_rh.columns[7]
            col_ag_etd        = df_rh.columns[11]
            col_ag_bl         = df_rh.columns[15]
            col_ag_conf       = df_rh.columns[18]
            col_ag_cntr       = df_rh.columns[1]   # col B = cant contenedores
            col_ag_linea      = df_rh.columns[59]  if len(df_rh.columns) > 59 else None
            col_ag_gto_origen = df_rh.columns[38]  if len(df_rh.columns) > 38 else None
            col_ag_flete_pag  = df_rh.columns[51]  if len(df_rh.columns) > 51 else None
            col_ag_flete_cert = df_rh.columns[52]  if len(df_rh.columns) > 52 else None
            col_ag_gto_local  = df_rh.columns[54]  if len(df_rh.columns) > 54 else None

            df_rh['_ag_inst_dt'] = pd.to_datetime(df_rh[col_ag_inst], dayfirst=True, errors='coerce')
            df_rh['_ag_etd_dt']  = pd.to_datetime(df_rh[col_ag_etd],  dayfirst=True, errors='coerce')
            df_rh['_ag_bl_dt']   = pd.to_datetime(df_rh[col_ag_bl],   dayfirst=True, errors='coerce')
            df_rh['_ag_conf_dt'] = pd.to_datetime(df_rh[col_ag_conf], dayfirst=True, errors='coerce')

            df_rh_ag_2026 = df_rh[df_rh['_ag_etd_dt'].dt.year == 2026].copy()
            # Filtrar solo tipos maritimos por columna F (índice 5)
            TIPOS_MAR_AG = ['40 HQ', '20 ST', '40 ST', '40 NOR']
            df_rh_ag_2026 = df_rh_ag_2026[
                df_rh_ag_2026[df_rh.columns[5]].astype(str).str.strip().str.upper().isin(
                    [t.upper() for t in TIPOS_MAR_AG]
                )
            ].copy()
            df_rh_ag_2026['Mes_Num_Ag']   = df_rh_ag_2026['_ag_etd_dt'].dt.month
            df_rh_ag_2026['Mes_Label_Ag'] = df_rh_ag_2026['_ag_etd_dt'].dt.strftime('%B %Y').str.upper()

            def safe_num_ag(val):
                try: return float(str(val).replace(',','.').replace(' ','').strip())
                except: return None

            for col in [col_ag_gto_origen, col_ag_flete_pag, col_ag_flete_cert, col_ag_gto_local, col_ag_cntr]:
                if col: df_rh_ag_2026[col] = df_rh_ag_2026[col].apply(safe_num_ag)

            if df_rh_ag_2026.empty:
                st.warning("No se encontraron datos maritimos de agentes para 2026.")
            else:
                meses_ag = df_rh_ag_2026.drop_duplicates('Mes_Num_Ag').sort_values('Mes_Num_Ag')[['Mes_Num_Ag','Mes_Label_Ag']].values.tolist()
                opciones_ag = {lbl: num for num, lbl in meses_ag}

                col_sel_ag, _ = st.columns([2, 3])
                with col_sel_ag:
                    mes_ag_lbl = st.selectbox("SELECCIONAR MES ETD (AGENTES):", list(opciones_ag.keys()), key="perf_ag_mes_sel")
                mes_ag_num = opciones_ag[mes_ag_lbl]

                df_ag_mes = df_rh_ag_2026[df_rh_ag_2026['Mes_Num_Ag'] == mes_ag_num].copy()
                df_ag_mes['_dias_instr_conf'] = (df_ag_mes['_ag_conf_dt'] - df_ag_mes['_ag_inst_dt']).dt.days
                df_ag_mes['_dias_etd_bl']     = (df_ag_mes['_ag_bl_dt']   - df_ag_mes['_ag_etd_dt']).dt.days
                df_ag_mes['_fwd_clean']        = df_ag_mes[col_ag_fwd].astype(str).str.strip()
                df_ag_mes = df_ag_mes[~df_ag_mes['_fwd_clean'].isin(['', 'nan', 'NaN', 'None', '-'])]

                total_embs_ag   = df_ag_mes[df_rh.columns[0]].nunique()
                total_cntrs_ag  = df_ag_mes[col_ag_cntr].sum()
                avg_dias_ic     = df_ag_mes['_dias_instr_conf'].mean()
                avg_dias_bl     = df_ag_mes['_dias_etd_bl'].mean()
                # Para el KPI global usamos promedio por embarque
                # KPI global: suma total certificado / suma total pagado x 100. Objetivo >= 75%
                sum_fp_global   = df_ag_mes[col_ag_flete_pag].sum()  if col_ag_flete_pag  else 0
                sum_fc_global   = df_ag_mes[col_ag_flete_cert].sum() if col_ag_flete_cert else 0
                pct_cert_global = round(sum_fc_global / sum_fp_global * 100, 1) if sum_fp_global and sum_fp_global > 0 else None
                color_cert = "#00ff88" if pct_cert_global and pct_cert_global >= 75 else "#ff4b4b"
                st.markdown("<br>", unsafe_allow_html=True)
                kg1, kg2, kg3, kg4, kg5 = st.columns(5)
                with kg1: st.markdown(f"<div class='metric-container'><p>EMBARQUES</p><p>{total_embs_ag}</p></div>", unsafe_allow_html=True)
                with kg2: st.markdown(f"<div class='metric-container'><p>CONTENEDORES</p><p>{int(total_cntrs_ag)}</p></div>", unsafe_allow_html=True)
                with kg3: st.markdown(f"<div class='metric-container'><p>DIAS INSTR-CONF</p><p>{int(round(avg_dias_ic)) if pd.notna(avg_dias_ic) else 0}</p></div>", unsafe_allow_html=True)
                with kg4: st.markdown(f"<div class='metric-container'><p>DIAS ETD-BL</p><p>{int(round(avg_dias_bl)) if pd.notna(avg_dias_bl) else 0}</p></div>", unsafe_allow_html=True)
                with kg5:
                    val_cert = f"{pct_cert_global}%" if pct_cert_global else "SD"
                    st.markdown(f"<div class='metric-container' style='border:1px solid {color_cert}44;'><p>PCT CERTIFICACION</p><p style='color:{color_cert} !important;'>{val_cert}</p></div>", unsafe_allow_html=True)

                st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
                st.markdown("<p style='color:#ffaa00; font-weight:800; letter-spacing:4px; font-size:15px; margin-bottom:20px; text-align:center;'>DESEMPENO POR AGENTE</p>", unsafe_allow_html=True)

                rows_ag = []
                for fwd, grp_f in df_ag_mes.groupby('_fwd_clean'):
                    cant_embs_f  = grp_f[df_rh.columns[0]].nunique()
                    cant_cntrs_f = grp_f[col_ag_cntr].sum()
                    avg_ic = grp_f['_dias_instr_conf'].mean()
                    avg_bl = grp_f['_dias_etd_bl'].mean()
                    if col_ag_linea:
                        lineas = grp_f[col_ag_linea].dropna().astype(str).str.strip()
                        lineas = lineas[~lineas.isin(['', 'nan', 'None', '-'])]
                        lineas_str = ", ".join(sorted(lineas.unique())) if not lineas.empty else "Sin datos"
                    else:
                        lineas_str = "Sin datos"
                    # Promedios por embarque
                    # Certificacion por agente: suma certif / suma pagado x 100. Objetivo >= 75%
                    avg_fp = grp_f[col_ag_flete_pag].mean()  if col_ag_flete_pag  else 0
                    avg_fc = grp_f[col_ag_flete_cert].mean() if col_ag_flete_cert else 0
                    avg_gl = grp_f[col_ag_gto_local].mean()  if col_ag_gto_local  else 0
                    avg_go = grp_f[col_ag_gto_origen].mean() if col_ag_gto_origen else 0
                    sum_fp_f = grp_f[col_ag_flete_pag].sum()  if col_ag_flete_pag  else 0
                    sum_fc_f = grp_f[col_ag_flete_cert].sum() if col_ag_flete_cert else 0
                    pct_f    = round(sum_fc_f / sum_fp_f * 100, 1) if sum_fp_f and sum_fp_f > 0 else None
                    kpi_str  = ("OK >=75%" if pct_f >= 75 else "BAJO <75%") if pct_f else "Sin datos"
                    rows_ag.append({
                        'Agente'              : fwd,
                        'Embarques'           : cant_embs_f,
                        'Contenedores'        : int(cant_cntrs_f) if pd.notna(cant_cntrs_f) else 0,
                        'Dias Instr-Conf'     : round(avg_ic, 1) if pd.notna(avg_ic) else None,
                        'Dias ETD-BL'         : round(avg_bl, 1) if pd.notna(avg_bl) else None,
                        'Lineas Maritimas'    : lineas_str,
                        'Prom Flete Pag USD'  : round(avg_fp, 0) if avg_fp else None,
                        'Prom Flete Cert USD' : round(avg_fc, 0) if avg_fc else None,
                        'Prom Gtos Local USD' : round(avg_gl, 0) if avg_gl else None,
                        'Prom Gtos Orig USD'  : round(avg_go, 0) if avg_go else None,
                        'Pct Certif'          : f"{pct_f}%" if pct_f else "Sin datos",
                        'KPI Certif'          : kpi_str,
                    })

                df_ag_tabla = pd.DataFrame(rows_ag).sort_values('Embarques', ascending=False)
                st.dataframe(
                    df_ag_tabla, use_container_width=True, hide_index=True,
                    column_config={
                        'Agente'              : st.column_config.TextColumn("Agente"),
                        'Embarques'           : st.column_config.NumberColumn("Embarques", format="%d"),
                        'Contenedores'        : st.column_config.NumberColumn("CTNRS", format="%d"),
                        'Dias Instr-Conf'     : st.column_config.NumberColumn("Dias Instr-Conf", format="%.1f d"),
                        'Dias ETD-BL'         : st.column_config.NumberColumn("Dias ETD-BL", format="%.1f d"),
                        'Lineas Maritimas'    : st.column_config.TextColumn("Lineas Maritimas"),
                        'Prom Flete Pag USD'  : st.column_config.NumberColumn("Prom Flete Pag", format="$ %,.0f"),
                        'Prom Flete Cert USD' : st.column_config.NumberColumn("Prom Flete Cert", format="$ %,.0f"),
                        'Prom Gtos Local USD' : st.column_config.NumberColumn("Prom Gtos Locales", format="$ %,.0f"),
                        'Prom Gtos Orig USD'  : st.column_config.NumberColumn("Prom Gtos Origen", format="$ %,.0f"),
                        'Pct Certif'          : st.column_config.TextColumn("% Certif."),
                        'KPI Certif'          : st.column_config.TextColumn("KPI >=75%"),
                    }
                )

                estado_nota = "OBJETIVO CUMPLIDO" if pct_cert_global and pct_cert_global >= 75 else "POR DEBAJO DEL OBJETIVO - revisar certificacion"
                val_nota = f"{pct_cert_global}% - {estado_nota}" if pct_cert_global else "Sin datos suficientes"
                st.markdown(
                    "<div style='margin-top:15px; padding:12px 18px; background:rgba(255,255,255,0.02);"
                    f"border-radius:10px; border-left:4px solid {color_cert};'>"
                    f"<p style='color:#94a3b8; font-size:12px; margin:0;'>"
                    f"KPI CERTIFICACION: objetivo >= 75%. "
                    f"Total Flete Certificado / Total Flete Pagado x 100. "
                    f"Resultado del mes: "
                    f"<b style='color:{color_cert};'>{val_nota}</b> "
                    f"| Meta: lograr que la totalidad de las cargas tengan flete certificado al menos en un 75% del valor pagado."
                    f"</p></div>",
                    unsafe_allow_html=True
                )

        except Exception as e:
            st.error(f"Error en Performance Agentes: {e}")
            import traceback
            st.code(traceback.format_exc())


    # --- SOLAPA 4: CONTROL DE FLETES, GASTOS Y CERTIFICACIONES ---
    with tabs[3]:
        try:
            st.markdown("""
<div style='text-align:center; padding:25px; background:linear-gradient(135deg,rgba(255,170,0,0.08),rgba(0,168,255,0.05));
border-radius:20px; border:1px solid rgba(255,170,0,0.2); margin-bottom:30px;'>
<h2 style='color:#ffaa00; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>FLETES & GASTOS LOCALES</h2>
<p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>MARITIMO 2026 - COTIZACIONES EN TIEMPO REAL</p>
</div>""", unsafe_allow_html=True)

            SHEET_URL = "https://docs.google.com/spreadsheets/d/1UJ1bDyDQdIQSSVQ6dyChVKbMX1d69G68ji_dpsOzfHg"

            @st.cache_data(ttl=300)
            def load_fletes_data(url):
                csv_url = f"{url}/export?format=csv&gid=0"
                df_f = pd.read_csv(csv_url, header=0, dtype=str, on_bad_lines='skip')
                df_f.columns = [str(c).strip() for c in df_f.columns]
                return df_f

            df_fl = load_fletes_data(SHEET_URL)

            def parse_usd_fl(val):
                try:
                    s = str(val).replace('USD','').replace('$','').replace(' ','').strip()
                    s = s.replace('.','').replace(',','.')
                    return float(s)
                except:
                    return None

            # Columnas por indice segun estructura confirmada
            # A(0)=Tipo transporte, B(1)=FFWW, C(2)=Agente, D(3)=Valor Flete
            # K(10)=Validez Desde, L(11)=Validez Hasta, O(14)=Locales ARG, P(15)=Tipo Ctnr
            col_fl_tipo   = df_fl.columns[0]
            col_fl_agente = df_fl.columns[1]
            col_fl_flete  = df_fl.columns[3]
            col_fl_desde  = df_fl.columns[10]
            col_fl_hasta  = df_fl.columns[11]
            col_fl_local  = df_fl.columns[14]
            col_fl_cnt    = df_fl.columns[15]

            df_fl['_desde_dt'] = pd.to_datetime(df_fl[col_fl_desde], dayfirst=True, errors='coerce')
            df_fl['_hasta_dt'] = pd.to_datetime(df_fl[col_fl_hasta], dayfirst=True, errors='coerce')
            df_fl['_flete']    = df_fl[col_fl_flete].apply(parse_usd_fl)
            df_fl['_local']    = df_fl[col_fl_local].apply(parse_usd_fl)
            df_fl['_cnt']      = df_fl[col_fl_cnt].astype(str).str.strip().str.upper()
            df_fl['_agente']   = df_fl[col_fl_agente].astype(str).str.strip()
            df_fl['_mes_num']  = df_fl['_desde_dt'].dt.month
            df_fl['_mes_label']= df_fl['_desde_dt'].dt.strftime('%B %Y').str.upper()
            df_fl['_anio']     = df_fl['_desde_dt'].dt.year

            # Solo 2026 y con flete valido, excluir POD Lazaro Cardenas
            df_fl_2026 = df_fl[
                (df_fl['_anio'] == 2026) &
                df_fl['_flete'].notna() &
                (df_fl['_cnt'] != 'NAN') &
                (df_fl['_cnt'] != '') &
                ~df_fl[df_fl.columns[8]].astype(str).str.strip().str.upper().str.contains('LAZARO|CARDENAS|CÁRDENAS', na=False)
            ].copy()

            TIPOS_CNT  = ['40ST/40HQ', '20ST', '40NOR']
            TARGET_PCT = 0.85
            COLORES_CNT = {'40ST/40HQ': '#00a8ff', '20ST': '#00ff88', '40NOR': '#ffaa00'}

            if df_fl_2026.empty:
                st.warning("No se encontraron cotizaciones validas para 2026.")
            else:
                # ── BLOQUE 1: COTIZACIONES VIGENTES HOY ─────────────────────
                df_vig = df_fl_2026[
                    (df_fl_2026['_desde_dt'] <= hoy) &
                    (df_fl_2026['_hasta_dt'] >= hoy)
                ].copy()

                st.markdown(f"""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #00ff88; margin-bottom:20px;'>
<p style='color:#00ff88; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
COTIZACIONES VIGENTES HOY {hoy.strftime('%d/%m/%Y')}</p>
<p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>
Validez Quincena Desde menor o igual a hoy y Validez Quincena Hasta mayor o igual a hoy</p>
</div>""", unsafe_allow_html=True)

                if df_vig.empty:
                    st.info("No hay cotizaciones vigentes para hoy. Mostrando el periodo mas reciente disponible.")
                    ultimo_desde = df_fl_2026['_desde_dt'].max()
                    if pd.notna(ultimo_desde):
                        df_vig = df_fl_2026[df_fl_2026['_desde_dt'] == ultimo_desde].copy()

                if not df_vig.empty:
                    cant_agentes_vig = df_vig['_agente'].nunique()
                    v1, v2 = st.columns([1, 3])
                    with v1:
                        st.markdown(f"""
<div class='custom-card' style='border-top:3px solid #00ff88; text-align:center;'>
<p class='minicard-title'>AGENTES COTIZADOS</p>
<p style='font-size:52px; font-weight:900; color:#00ff88; margin:0;'>{cant_agentes_vig}</p>
</div>""", unsafe_allow_html=True)

                    with v2:
                        # Tabla por tipo CNT
                        rows_vig = []
                        for cnt in TIPOS_CNT:
                            df_cnt = df_vig[df_vig['_cnt'] == cnt]
                            if df_cnt.empty: continue
                            prom   = df_cnt['_flete'].mean()
                            minimo = df_cnt['_flete'].min()
                            ag_min = df_cnt.loc[df_cnt['_flete'].idxmin(), '_agente']
                            target = prom * TARGET_PCT
                            vs_tgt = round((minimo - target) / target * 100, 1) if target > 0 else None
                            ok     = minimo <= target
                            rows_vig.append({
                                'Tipo CNT'       : cnt,
                                'Agentes'        : df_cnt['_agente'].nunique(),
                                'Prom. Mercado'  : round(prom, 0),
                                'Target -15%'    : round(target, 0),
                                'Mejor Oferta'   : round(minimo, 0),
                                'Agente Ganador' : ag_min,
                                'Vs Target'      : f"{'OK' if ok else 'ALTO'} {vs_tgt:+.1f}%" if vs_tgt else "SD",
                            })

                        if rows_vig:
                            df_vig_tabla = pd.DataFrame(rows_vig)
                            st.dataframe(
                                df_vig_tabla, use_container_width=True, hide_index=True,
                                column_config={
                                    'Tipo CNT'      : st.column_config.TextColumn("Tipo CNT"),
                                    'Agentes'       : st.column_config.NumberColumn("Agentes", format="%d"),
                                    'Prom. Mercado' : st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                                    'Target -15%'   : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                                    'Mejor Oferta'  : st.column_config.NumberColumn("Mejor Oferta", format="$ %,.0f"),
                                    'Agente Ganador': st.column_config.TextColumn("Agente Ganador"),
                                    'Vs Target'     : st.column_config.TextColumn("Vs Target"),
                                }
                            )

                # Selector FFWW para ver tarifas por forwarder
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #00a8ff; margin-bottom:15px;'>
<p style='color:#00a8ff; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
TARIFAS POR FORWARDER (FFWW)</p>
<p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>
Seleccioná un agente para ver sus tarifas vigentes por tipo de CNT</p>
</div>""", unsafe_allow_html=True)

                ffww_opciones = sorted(df_vig['_agente'].dropna().astype(str).str.strip().unique().tolist()) if not df_vig.empty else []
                ffww_opciones = [f for f in ffww_opciones if f.lower() not in ['', 'nan', 'none']]

                if ffww_opciones:
                    col_ffww, _ = st.columns([2, 3])
                    with col_ffww:
                        ffww_sel = st.selectbox("SELECCIONAR FFWW:", ["COMPARATIVA GENERAL"] + ffww_opciones, key="ffww_sel")

                    if ffww_sel == "COMPARATIVA GENERAL":
                        # Una fila por FFWW x tipo CNT con su tarifa vs prom mercado
                        rows_ffww = []
                        for agente in ffww_opciones:
                            df_ag = df_vig[df_vig['_agente'].astype(str).str.strip() == agente]
                            for cnt in TIPOS_CNT:
                                df_c = df_ag[df_ag['_cnt'] == cnt]
                                if df_c.empty: continue
                                tarifa   = df_c['_flete'].mean()
                                prom_mkt = df_vig[df_vig['_cnt'] == cnt]['_flete'].mean()
                                target   = prom_mkt * TARGET_PCT
                                vs_tgt   = round((tarifa - target) / target * 100, 1) if target > 0 else None
                                ok       = tarifa <= target
                                rows_ffww.append({
                                    'FFWW'         : agente,
                                    'Tipo CNT'     : cnt,
                                    'Su Tarifa'    : round(tarifa, 0),
                                    'Prom. Mercado': round(prom_mkt, 0),
                                    'Target -15%'  : round(target, 0),
                                    'Vs Target'    : ("✅ OK " if ok else "🔴 ALTO ") + f"{vs_tgt:+.1f}%" if vs_tgt is not None else "SD",
                                })
                        if rows_ffww:
                            st.dataframe(
                                pd.DataFrame(rows_ffww),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'FFWW'         : st.column_config.TextColumn("FFWW"),
                                    'Tipo CNT'     : st.column_config.TextColumn("Tipo CNT"),
                                    'Su Tarifa'    : st.column_config.NumberColumn("Su Tarifa", format="$ %,.0f"),
                                    'Prom. Mercado': st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                                    'Target -15%'  : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                                    'Vs Target'    : st.column_config.TextColumn("Vs Target"),
                                }
                            )
                    else:
                        # Detalle de FFWW específico
                        df_ffww = df_vig[df_vig['_agente'].astype(str).str.strip() == ffww_sel]
                        rows_ffww = []
                        for cnt in TIPOS_CNT:
                            df_c = df_ffww[df_ffww['_cnt'] == cnt]
                            if df_c.empty: continue
                            tarifa   = df_c['_flete'].mean()
                            prom_mkt = df_vig[df_vig['_cnt'] == cnt]['_flete'].mean()
                            target   = prom_mkt * TARGET_PCT
                            vs_tgt   = round((tarifa - target) / target * 100, 1) if target > 0 else None
                            ok       = tarifa <= target
                            rows_ffww.append({
                                'Tipo CNT'     : cnt,
                                'Tarifa FFWW'  : round(tarifa, 0),
                                'Prom. Mercado': round(prom_mkt, 0),
                                'Target -15%'  : round(target, 0),
                                'Vs Target'    : ("✅ OK " if ok else "🔴 ALTO ") + f"{vs_tgt:+.1f}%" if vs_tgt is not None else "SD",
                            })
                        if rows_ffww:
                            st.dataframe(
                                pd.DataFrame(rows_ffww),
                                use_container_width=True, hide_index=True,
                                column_config={
                                    'Tipo CNT'     : st.column_config.TextColumn("Tipo CNT"),
                                    'Tarifa FFWW'  : st.column_config.NumberColumn("Tarifa FFWW", format="$ %,.0f"),
                                    'Prom. Mercado': st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                                    'Target -15%'  : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                                    'Vs Target'    : st.column_config.TextColumn("Vs Target"),
                                }
                            )
                        else:
                            st.info(f"No hay tarifas vigentes para {ffww_sel}.")
                else:
                    st.info("No hay forwarders disponibles en el período vigente.")

                # Gastos locales vigentes
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #a855f7; margin-bottom:20px;'>
<p style='color:#a855f7; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
GASTOS LOCALES ARG - VIGENTES HOY</p>
</div>""", unsafe_allow_html=True)

                df_loc_vig = df_fl_2026[
                    (df_fl_2026['_desde_dt'] <= hoy) &
                    (df_fl_2026['_hasta_dt'] >= hoy) &
                    df_fl_2026['_local'].notna()
                ].copy()

                if df_loc_vig.empty:
                    ultimo_l = df_fl_2026[df_fl_2026['_local'].notna()]['_desde_dt'].max()
                    if pd.notna(ultimo_l):
                        df_loc_vig = df_fl_2026[
                            (df_fl_2026['_desde_dt'] == ultimo_l) &
                            df_fl_2026['_local'].notna()
                        ].copy()

                if not df_loc_vig.empty:
                    prom_loc = df_loc_vig['_local'].mean()
                    min_loc  = df_loc_vig['_local'].min()
                    max_loc  = df_loc_vig['_local'].max()
                    ag_loc   = df_loc_vig.loc[df_loc_vig['_local'].idxmin(), '_agente']
                    la, lb, lc, ld = st.columns(4)
                    for col_card, valor, label, color in [
                        (la, f"USD {prom_loc:,.0f}", "PROM. LOCALES",     "#a855f7"),
                        (lb, f"USD {min_loc:,.0f}",  "MENOR LOCAL",       "#00ff88"),
                        (lc, ag_loc,                  "AGENTE MAS BARATO", "#f8fafc"),
                        (ld, f"USD {max_loc:,.0f}",  "MAYOR LOCAL",       "#ff4b4b"),
                    ]:
                        col_card.markdown(f"""
<div style='text-align:center; padding:16px 8px; background:rgba(255,255,255,0.02);
border-radius:14px; border-top:3px solid {color};'>
<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 6px 0;'>{label}</p>
<p style='color:{color}; font-size:22px; font-weight:900; margin:0;'>{valor}</p>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No hay gastos locales disponibles para el periodo vigente.")

                # ── BLOQUE 2: HISTORICO 2026 ────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<hr style='border:none; border-top:2px solid rgba(255,170,0,0.15); margin:10px 0 25px 0;'>", unsafe_allow_html=True)
                st.markdown("""
<div style='padding:14px 20px; background:rgba(255,255,255,0.02); border-radius:12px;
border-left:4px solid #ffaa00; margin-bottom:20px;'>
<p style='color:#ffaa00; font-weight:800; font-size:15px; letter-spacing:3px; margin:0;'>
HISTORICO 2026 - EVOLUCION MENSUAL POR TIPO DE CNT</p>
<p style='color:#94a3b8; font-size:11px; margin:4px 0 0 0;'>
Promedio de mercado, mejor oferta y target -15% por mes y tipo de contenedor</p>
</div>""", unsafe_allow_html=True)

                # Construir tabla historica completa (todos los meses x todos los CNTs)
                rows_hist = []
                meses_ord = df_fl_2026.drop_duplicates('_mes_num').sort_values('_mes_num')[['_mes_num','_mes_label']].values.tolist()
                for mes_num, mes_lbl in meses_ord:
                    df_mes = df_fl_2026[df_fl_2026['_mes_num'] == mes_num]
                    for cnt in TIPOS_CNT:
                        df_c = df_mes[df_mes['_cnt'] == cnt]
                        if df_c.empty: continue
                        prom   = df_c['_flete'].mean()
                        minimo = df_c['_flete'].min()
                        target = prom * TARGET_PCT
                        dif    = round(prom - minimo, 0)
                        desv   = round((minimo - prom) / prom * 100, 1) if prom > 0 else None
                        vs_tgt = round((minimo - target) / target * 100, 1) if target > 0 else None
                        rows_hist.append({
                            'Mes'           : mes_lbl,
                            '_mes_num'      : mes_num,
                            'Tipo CNT'      : cnt,
                            'Prom. Mercado' : round(prom, 0),
                            'Target -15%'   : round(target, 0),
                            'Mejor Oferta'  : round(minimo, 0),
                            'Dif. USD'      : round(dif, 0),
                            '% Desvio'      : f"{desv:+.1f}%" if desv is not None else "SD",
                            'Vs Target'     : f"{vs_tgt:+.1f}%" if vs_tgt is not None else "SD",
                        })

                df_hist = pd.DataFrame(rows_hist)
                if not df_hist.empty:
                    # ── SELECTORES ───────────────────────────────────────────
                    meses_disponibles = ["TODOS"] + [m for _, m in meses_ord]
                    cnts_disponibles  = ["TODOS"] + TIPOS_CNT

                    fh1, fh2 = st.columns(2)
                    with fh1:
                        mes_sel_hist = st.selectbox(
                            "MES:", meses_disponibles, key="hist_mes_sel"
                        )
                    with fh2:
                        cnt_sel_hist = st.selectbox(
                            "TIPO CNT:", cnts_disponibles, key="hist_cnt_sel"
                        )

                    # Aplicar filtros a la tabla
                    df_hist_fil = df_hist.copy()
                    if mes_sel_hist != "TODOS":
                        df_hist_fil = df_hist_fil[df_hist_fil['Mes'] == mes_sel_hist]
                    if cnt_sel_hist != "TODOS":
                        df_hist_fil = df_hist_fil[df_hist_fil['Tipo CNT'] == cnt_sel_hist]

                    # KPIs del filtro actual
                    if not df_hist_fil.empty:
                        avg_prom  = df_hist_fil['Prom. Mercado'].mean()
                        avg_mejor = df_hist_fil['Mejor Oferta'].mean()
                        avg_tgt   = df_hist_fil['Target -15%'].mean()
                        avg_dif   = df_hist_fil['Dif. USD'].mean()

                        kh1, kh2, kh3, kh4 = st.columns(4)
                        color_dif = "#00ff88" if avg_dif > 0 else "#ff4b4b"
                        for col_k, valor, label, color in [
                            (kh1, f"USD {int(avg_prom):,}",  "PROM. MERCADO", "#f8fafc"),
                            (kh2, f"USD {int(avg_mejor):,}", "MEJOR OFERTA",  "#00ff88"),
                            (kh3, f"USD {int(avg_tgt):,}",   "TARGET -15%",   "#ffaa00"),
                            (kh4, f"USD {int(avg_dif):,}",   "AHORRO PROM.",  color_dif),
                        ]:
                            col_k.markdown(f"""
<div style='text-align:center; padding:12px 8px; background:rgba(255,255,255,0.02);
border-radius:12px; border-top:2px solid {color};'>
<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; margin:0 0 4px 0;'>{label}</p>
<p style='color:{color}; font-size:18px; font-weight:800; margin:0;'>{valor}</p>
</div>""", unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)

                    # Tabla filtrada
                    st.dataframe(
                        df_hist_fil.drop(columns=['_mes_num']),
                        use_container_width=True, hide_index=True,
                        column_config={
                            'Mes'          : st.column_config.TextColumn("Mes"),
                            'Tipo CNT'     : st.column_config.TextColumn("Tipo CNT"),
                            'Prom. Mercado': st.column_config.NumberColumn("Prom. Mercado", format="$ %,.0f"),
                            'Target -15%'  : st.column_config.NumberColumn("Target -15%", format="$ %,.0f"),
                            'Mejor Oferta' : st.column_config.NumberColumn("Mejor Oferta", format="$ %,.0f"),
                            'Dif. USD'     : st.column_config.NumberColumn("Dif. USD", format="$ %,.0f"),
                            '% Desvio'     : st.column_config.TextColumn("% Desvio"),
                            'Vs Target'    : st.column_config.TextColumn("Vs Target"),
                        }
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ── GRAFICO EVOLUCION ─────────────────────────────────────
                    # Siempre sobre todos los meses; filtrado solo por CNT
                    df_hist_graf = df_hist.copy()
                    if cnt_sel_hist != "TODOS":
                        df_hist_graf = df_hist_graf[df_hist_graf['Tipo CNT'] == cnt_sel_hist]

                    titulo_graf = f"Evolucion de Costos - {'Todos los tipos CNT' if cnt_sel_hist == 'TODOS' else cnt_sel_hist}"
                    fig_evol = px.line(
                        df_hist_graf.sort_values(['_mes_num','Tipo CNT']),
                        x='Mes', y='Prom. Mercado', color='Tipo CNT',
                        markers=True, color_discrete_map=COLORES_CNT,
                        text='Prom. Mercado',
                        labels={'Prom. Mercado': 'USD Promedio de Mercado', 'Mes': ''},
                        title=titulo_graf
                    )
                    fig_evol.update_traces(
                        line_width=3, marker_size=10,
                        texttemplate='USD %{text:,.0f}',
                        textposition='top center',
                        textfont=dict(size=11, family='Outfit, sans-serif'),
                    )
                    fig_evol.update_layout(
                        height=480, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12, family='Outfit, sans-serif', color='#94a3b8'),
                        title_font_color='#ffaa00', title_font_size=14,
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text=''),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)', title='USD'),
                        margin=dict(l=20, r=20, t=100, b=40)
                    )
                    # Marcar mes seleccionado con vrect si no es TODOS (vline no funciona con eje categorico)
                    if mes_sel_hist != "TODOS":
                        fig_evol.add_vrect(
                            x0=mes_sel_hist, x1=mes_sel_hist,
                            fillcolor="rgba(255,255,255,0.08)",
                            layer="below", line_width=0,
                        )
                    st.plotly_chart(fig_evol, use_container_width=True)

        except Exception as e:
            st.error(f"Error en Fletes y Gastos: {e}")
            import traceback
            st.code(traceback.format_exc())



    # --- SOLAPA 5: PROYECCIÓN SEMANAL ETD ---
    with tabs[4]:
        st.markdown("<div style='text-align:center; padding:25px; background:linear-gradient(135deg,rgba(0,168,255,0.08),rgba(0,255,136,0.04)); border-radius:20px; border:1px solid rgba(0,168,255,0.2); margin-bottom:30px;'><h2 style='color:#00a8ff; font-weight:900; letter-spacing:6px; margin:0; font-size:26px;'>PROYECCION SEMANAL ETD</h2><p style='color:#94a3b8; margin:8px 0 0 0; font-size:13px; letter-spacing:2px;'>VOLUMEN Y CONTENEDORES FUTUROS - BASE PARA NEGOCIACION DE TARIFAS</p></div>", unsafe_allow_html=True)
        try:
            # Buscar columnas por nombre para evitar desplazamientos de índice
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

            paises_unicos = df_proy[col_pais_proy].astype(str).str.strip().str.upper().unique()
            mods_unicas   = df_proy[col_mod_proy].astype(str).str.strip().str.upper().unique()

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
                st.warning("No hay carga futura proyectada con los filtros aplicados.")
                with st.expander("🔍 Diagnóstico de columnas (para verificar)"):
                    st.write(f"**Columna País Destino usada:** `{col_pais_proy}` (índice 18)")
                    st.write(f"**Columna Modalidad usada:** `{col_mod_proy}`")
                    st.write(f"**Columna ETD usada:** `{col_etd_proy}`")
                    st.write(f"**Columna Puerto usada:** `{col_puerto_proy}`")
                    st.write(f"**M3 Total: usando columna 'M3 Total' ya limpia del dataframe principal**")
                    st.write("**Valores únicos de País Destino (primeros 15):**")
                    st.write(list(paises_unicos[:15]))
                    st.write("**Valores únicos de Modalidad (primeros 15):**")
                    st.write(list(mods_unicas[:15]))
                    df_debug = df.copy()
                    n_pais = (df_debug[col_pais_proy].astype(str).str.strip().str.upper() == 'ARGENTINA').sum()
                    n_mod  = (
                        df_debug[col_mod_proy].astype(str).str.strip().str.upper().str.startswith('BARCO') |
                        df_debug[col_mod_proy].astype(str).str.strip().str.upper().str.contains('COSTO HIBRIDO PUERTO ZFLP', na=False)
                    ).sum()
                    st.write(f"**Filas que pasan filtro Argentina:** {n_pais}")
                    st.write(f"**Filas que pasan filtro Modalidad (Barco/ZFLP):** {n_mod}")
            else:
                meses_proy  = df_proy.drop_duplicates('_mes_num').sort_values('_mes_num')[['_mes_num','_mes_label']].values.tolist()
                opciones_proy = {lbl: num for num, lbl in meses_proy}

                col_sp, _ = st.columns([2, 3])
                with col_sp:
                    mes_proy_lbl = st.selectbox("SELECCIONAR MES ETD:", list(opciones_proy.keys()), key="proy_mes_sel")
                mes_proy_num = opciones_proy[mes_proy_lbl]

                df_mes_proy = df_proy[df_proy['_mes_num'] == mes_proy_num].copy()

                total_m3_mes   = df_mes_proy['_m3'].sum()
                total_cntr_mes = total_m3_mes / 60
                total_so_mes   = df_mes_proy['SO'].nunique() if 'SO' in df_mes_proy.columns else 0
                semanas_mes    = df_mes_proy['_semana_inicio'].nunique()

                st.markdown("<br>", unsafe_allow_html=True)
                pm1, pm2, pm3, pm4 = st.columns(4)
                with pm1: st.markdown(f"<div class='metric-container'><p>M3 TOTALES</p><p style='color:#00a8ff; font-size:32px; font-weight:900; margin:0;'>{int(round(total_m3_mes)):,}</p></div>", unsafe_allow_html=True)
                with pm2: st.markdown(f"<div class='metric-container'><p>CONTENEDORES</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{int(round(total_cntr_mes))}</p></div>", unsafe_allow_html=True)
                with pm3: st.markdown(f"<div class='metric-container'><p>SOs</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{total_so_mes}</p></div>", unsafe_allow_html=True)
                with pm4: st.markdown(f"<div class='metric-container'><p>SEMANAS</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{semanas_mes}</p></div>", unsafe_allow_html=True)

                st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)

                # Grafico barras apiladas M3 por semana y puerto
                df_stack = df_mes_proy.groupby(['_semana_inicio','_puerto'])['_m3'].sum().reset_index()
                df_stack['Semana'] = df_stack['_semana_inicio'].apply(
                    lambda d: d.strftime('%d/%m') + ' - ' + (d + pd.Timedelta(days=6)).strftime('%d/%m')
                )

                fig_stack = px.bar(
                    df_stack, x='Semana', y='_m3', color='_puerto',
                    text='_m3', barmode='stack',
                    color_discrete_sequence=['#00a8ff','#00ff88','#ffaa00','#ff4b4b','#a855f7','#06b6d4','#f97316'],
                    labels={'_m3': 'M3', '_puerto': 'Puerto', 'Semana': ''},
                    title='M3 por Semana ETD - ' + mes_proy_lbl
                )
                fig_stack.update_traces(texttemplate='%{text:,.0f}', textposition='inside', textfont_size=11, textfont_color='#fff')
                fig_stack.update_layout(
                    height=420, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=12),
                    title_font_color='#00a8ff', title_font_size=14,
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, title_text='Puerto'),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)', title='M3'),
                    margin=dict(l=20,r=20,t=60,b=20)
                )
                st.plotly_chart(fig_stack, use_container_width=True)

                # Grafico contenedores por semana
                df_cntr_sem = df_mes_proy.groupby('_semana_inicio')['_m3'].sum().reset_index()
                df_cntr_sem['Semana'] = df_cntr_sem['_semana_inicio'].apply(
                    lambda d: d.strftime('%d/%m') + ' - ' + (d + pd.Timedelta(days=6)).strftime('%d/%m')
                )
                df_cntr_sem['Contenedores'] = (df_cntr_sem['_m3'] / 60).round(1)

                fig_cntr = px.bar(
                    df_cntr_sem, x='Semana', y='Contenedores', text='Contenedores',
                    color_discrete_sequence=['#ffaa00'],
                    title='Contenedores estimados por Semana ETD - ' + mes_proy_lbl
                )
                fig_cntr.update_traces(
                    texttemplate='%{text:.1f} CNTR', textposition='outside',
                    textfont_color='#f8fafc', marker=dict(cornerradius=5)
                )
                fig_cntr.update_layout(
                    height=380, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Outfit, sans-serif', color='#94a3b8', size=12),
                    title_font_color='#ffaa00', title_font_size=14,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.07)', title='Contenedores'),
                    margin=dict(l=20,r=20,t=60,b=20)
                )
                st.plotly_chart(fig_cntr, use_container_width=True)

        except Exception as e:
            st.error(f"Error en Proyeccion Semanal ETD: {e}")
            import traceback
            st.code(traceback.format_exc())


    # --- SOLAPA 6: INDICADORES (SLA & CONSOLIDACIÓN) ---
    with tabs[5]:
        st.markdown("<div style='text-align:center; padding: 20px; background: rgba(0, 255, 136, 0.05); border-radius: 20px; margin: 30px 0;'><h2 style='color:#00ff88; font-weight:800; letter-spacing:5px; margin:0;'>INDICADORES DE CONSOLIDACIÓN Y SLA</h2></div>", unsafe_allow_html=True)
        try:
            url_hi = f"{base_url}/export?format=csv&gid=32771816&nocache={time.time()}"
            @st.cache_data(ttl=60)
            def load_hi_vfinal(u): return pd.read_csv(u, engine='python')

            df_hi = load_hi_vfinal(url_hi)
            df_hi.columns = [str(c).strip() for c in df_hi.columns]

            df_hi['ETD_DT'] = pd.to_datetime(df_hi.iloc[:, 11], dayfirst=True, errors='coerce')
            # Filtrar 2026: combinamos año en ETD parseado Y columna Z (Año ETD) para máxima cobertura
            mask_anio_etd = df_hi['ETD_DT'].dt.year == 2026
            mask_anio_col = df_hi.iloc[:, 25].astype(str).str.strip() == '2026'
            df_2026 = df_hi[mask_anio_etd | mask_anio_col].copy()
            # Asegurar que ETD_DT esté completo usando columna Z como respaldo
            df_2026.loc[df_2026['ETD_DT'].isna(), 'ETD_DT'] = pd.to_datetime(
                df_2026.loc[df_2026['ETD_DT'].isna(), df_hi.columns[11]], dayfirst=True, errors='coerce'
            )

            if not df_2026.empty:
                # Asegurar columna Mes para todas las filas
                df_2026['Mes'] = df_2026['ETD_DT'].dt.month
                # Para filas sin ETD parseado, intentar extraer mes de columna L directamente
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
                    res_p = df_sub.groupby(col_puerto_hi).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
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
                            limit = (15 if mes_num <= 2 else 7) if is_mono else 25
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
                for i, h in enumerate(["MES ETD", "EMBS", "DIAS AVG", "% MONO", "% CONS", "DETALLE"]):
                    thc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)

                res_mensual = df_mar.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
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
                    for i, h in enumerate(["MES ETD", "EMBS", "DIAS AVG", "CUMPLIMIENTO SLA", "DETALLE"]):
                        mhc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                    res_m = df_mono_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
                    for _, rm in res_m.iterrows():
                        df_sub_m = df_mono_v4[df_mono_v4['Mes'] == rm['Mes']].copy()
                        lim_m = 15 if rm['Mes'] <= 2 else 7
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
                    for i, h in enumerate(["MES ETD", "EMBS", "DIAS AVG", "CUMPLIMIENTO SLA", "DETALLE"]):
                        chc[i].markdown(f"<p style='color:#94a3b8; font-size:11px; font-weight:800; text-align:center;'>{h}</p>", unsafe_allow_html=True)
                    res_c = df_cons_v4.groupby(['Mes', 'Mes_Nombre']).agg({df_hi.columns[0]: 'count', col_cons_hi: 'mean'}).reset_index()
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

            # ── BLOQUE AÉREO ─────────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<hr class='glow-divider'>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center; padding:20px; background:rgba(168,85,247,0.05); border-radius:20px; margin-bottom:24px;'><h2 style='color:#a855f7; font-weight:800; letter-spacing:5px; margin:0;'>INDICADORES AÉREOS</h2><p style='color:#94a3b8; margin:8px 0 0 0; font-size:12px; letter-spacing:2px;'>Por tipo de negocio · ETD desde mayo 2026 · Seguimiento Aéreos</p></div>", unsafe_allow_html=True)
            try:
                @st.cache_data(ttl=60)
                def load_ae_ind(base):
                    url = f"{base}/export?format=csv&gid=88538385"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                df_ae_ind = load_ae_ind(base_url)

                col_ae_tipo   = df_ae_ind.columns[8]
                col_ae_etd    = df_ae_ind.columns[14]
                col_ae_fpmin  = df_ae_ind.columns[9]
                col_ae_fwh    = df_ae_ind.columns[11]
                col_ae_eta    = df_ae_ind.columns[15]
                col_ae_etacal = df_ae_ind.columns[16]

                def parse_dt_ae(v):
                    return pd.to_datetime(v, dayfirst=True, errors='coerce')

                df_ae_ind['_etd_dt']    = df_ae_ind[col_ae_etd].apply(parse_dt_ae)
                df_ae_ind['_fpmin_dt']  = df_ae_ind[col_ae_fpmin].apply(parse_dt_ae)
                df_ae_ind['_fwh_dt']    = df_ae_ind[col_ae_fwh].apply(parse_dt_ae)
                df_ae_ind['_eta_dt']    = df_ae_ind[col_ae_eta].apply(parse_dt_ae)
                df_ae_ind['_etacal_dt'] = df_ae_ind[col_ae_etacal].apply(parse_dt_ae)
                df_ae_ind['_tipo']      = df_ae_ind[col_ae_tipo].astype(str).str.strip().replace({'': 'SIN CLASIFICAR', 'nan': 'SIN CLASIFICAR'})

                col_ae_estadio_ind = df_ae_ind.columns[0]  # A: Estadio
                hoy_ae = pd.Timestamp.now().normalize()
                df_ae_f = df_ae_ind[
                    (df_ae_ind['_etd_dt'] >= pd.Timestamp('2026-05-01')) &
                    (df_ae_ind['_etd_dt'] <= hoy_ae) &
                    (df_ae_ind[col_ae_estadio_ind].astype(str).str.strip().str.upper() == 'ENTREGADO')
                ].copy()

                def dias(a, b):
                    d = (b - a).dt.days
                    return d.apply(lambda x: x if pd.notna(x) and x >= 0 else None)

                df_ae_f['_tt1'] = dias(df_ae_f['_fpmin_dt'], df_ae_f['_fwh_dt'])
                df_ae_f['_tt2'] = dias(df_ae_f['_fwh_dt'],   df_ae_f['_etd_dt'])
                df_ae_f['_tt3'] = dias(df_ae_f['_etd_dt'],   df_ae_f['_eta_dt'])
                df_ae_f['_tt4'] = dias(df_ae_f['_eta_dt'],   df_ae_f['_etacal_dt'])
                df_ae_f['_mes_ae'] = df_ae_f['_etd_dt'].dt.to_period('M').astype(str)

                COLORES_AE_IND = ['#a855f7','#00a8ff','#ffaa00','#00ff88','#ff4b4b','#06b6d4']

                def med_val(s):
                    v = s.dropna().median()
                    return v if pd.notna(v) else None

                def med_str_v(v):
                    return f"{int(round(v))}d" if v is not None else "—"

                def render_ae_detalle(df_sub, key_sfx):
                    tipos_ae = df_sub['_tipo'].value_counts().index.tolist()
                    h1,h2,h3,h4,h5,h6 = st.columns([1.5, 0.8, 0.8, 0.8, 0.8, 0.8])
                    h1.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700;'>TIPO DE NEGOCIO</p>", unsafe_allow_html=True)
                    h2.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>📦 Packeo→WH</p>", unsafe_allow_html=True)
                    h3.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>🏭 WH→ETD</p>", unsafe_allow_html=True)
                    h4.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>✈️ ETD→ETA</p>", unsafe_allow_html=True)
                    h5.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>🏠 ETA→Caldas</p>", unsafe_allow_html=True)
                    h6.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>⏱ TOTAL</p>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin:4px 0 8px 0; border:none; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)
                    for pi, tipo in enumerate(tipos_ae):
                        df_t = df_sub[df_sub['_tipo'] == tipo]
                        col_p = COLORES_AE_IND[pi % len(COLORES_AE_IND)]
                        v1,v2,v3,v4 = med_val(df_t['_tt1']), med_val(df_t['_tt2']), med_val(df_t['_tt3']), med_val(df_t['_tt4'])
                        tot = sum(v for v in [v1,v2,v3,v4] if v is not None)
                        c1,c2,c3,c4,c5,c6 = st.columns([1.5, 0.8, 0.8, 0.8, 0.8, 0.8])
                        c1.markdown(f"<p style='color:{col_p}; font-size:13px; font-weight:800; margin:5px 0;'>{tipo}</p>", unsafe_allow_html=True)
                        c2.markdown(f"<p style='color:#94a3b8; font-size:13px; text-align:center; margin:5px 0;'>{med_str_v(v1)}</p>", unsafe_allow_html=True)
                        c3.markdown(f"<p style='color:#94a3b8; font-size:13px; text-align:center; margin:5px 0;'>{med_str_v(v2)}</p>", unsafe_allow_html=True)
                        c4.markdown(f"<p style='color:#00a8ff; font-size:13px; font-weight:700; text-align:center; margin:5px 0;'>{med_str_v(v3)}</p>", unsafe_allow_html=True)
                        c5.markdown(f"<p style='color:#94a3b8; font-size:13px; text-align:center; margin:5px 0;'>{med_str_v(v4)}</p>", unsafe_allow_html=True)
                        tot_ae_str = f"{int(round(tot))}d" if tot > 0 else "—"
                        c6.markdown(f"<p style='color:#a855f7; font-size:14px; font-weight:900; text-align:center; margin:5px 0;'>{tot_ae_str}</p>", unsafe_allow_html=True)

                # Por mes
                meses_ae = sorted(df_ae_f['_mes_ae'].dropna().unique())
                st.markdown("<br>", unsafe_allow_html=True)

                MESES_ES = {'01':'ENE','02':'FEB','03':'MAR','04':'ABR','05':'MAY','06':'JUN','07':'JUL','08':'AGO','09':'SEP','10':'OCT','11':'NOV','12':'DIC'}

                # Encabezados de columna
                eh1,eh2,eh3,eh4,eh5,eh6,eh7 = st.columns([1.5, 0.8, 0.8, 0.8, 0.8, 0.9, 0.5])
                eh1.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:1px; font-weight:700;'>MES ETD</p>", unsafe_allow_html=True)
                eh2.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>📦 Packeo→WH</p>", unsafe_allow_html=True)
                eh3.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>🏭 WH→ETD</p>", unsafe_allow_html=True)
                eh4.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>✈️ ETD→ETA</p>", unsafe_allow_html=True)
                eh5.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>🏠 ETA→Caldas</p>", unsafe_allow_html=True)
                eh6.markdown("<p style='color:#64748b; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>⏱ TOTAL</p>", unsafe_allow_html=True)
                eh7.markdown("", unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0 8px 0; border:none; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)

                @st.dialog("✈️ DETALLE AÉREO POR TIPO DE NEGOCIO", width="large")
                def show_detalle_ae(df_sub, mes_lbl):
                    st.markdown(f"**Análisis AÉREO - {mes_lbl}**")
                    tipos_d = df_sub['_tipo'].value_counts().index.tolist()
                    import pandas as _pd2
                    rows = []
                    for tipo in tipos_d:
                        df_t = df_sub[df_sub['_tipo'] == tipo]
                        v1 = med_val(df_t['_tt1']); v2 = med_val(df_t['_tt2'])
                        v3 = med_val(df_t['_tt3']); v4 = med_val(df_t['_tt4'])
                        tot = sum(v for v in [v1,v2,v3,v4] if v is not None)
                        rows.append({
                            'Tipo': tipo,
                            'Embs': len(df_t),
                            'Packeo→WH': med_str_v(v1),
                            'WH→ETD': med_str_v(v2),
                            'ETD→ETA': med_str_v(v3),
                            'ETA→Caldas': med_str_v(v4),
                            'Total': f"{int(round(tot))}d" if tot > 0 else "—"
                        })
                    st.dataframe(
                        _pd2.DataFrame(rows),
                        use_container_width=True,
                        hide_index=True
                    )

                for mes in meses_ae:
                    df_mes_ae = df_ae_f[df_ae_f['_mes_ae'] == mes]
                    n_emb_ae  = len(df_mes_ae)
                    partes    = mes.split('-')
                    mes_label = f"{MESES_ES.get(partes[1], partes[1])} {partes[0]}" if len(partes)==2 else mes

                    # Medianas globales del mes
                    v1g = med_val(df_mes_ae['_tt1']); v2g = med_val(df_mes_ae['_tt2'])
                    v3g = med_val(df_mes_ae['_tt3']); v4g = med_val(df_mes_ae['_tt4'])
                    tot_g = sum(v for v in [v1g,v2g,v3g,v4g] if v is not None)

                    cr1,cr2,cr3,cr4,cr5,cr6,cr7 = st.columns([1.5, 0.8, 0.8, 0.8, 0.8, 0.9, 0.5])
                    cr1.markdown(f"<p style='color:#f8fafc; font-size:14px; font-weight:800; margin:8px 0;'>{mes_label}</p><p style='color:#475569; font-size:10px; margin:0 0 8px 0;'>{n_emb_ae} embarques</p>", unsafe_allow_html=True)
                    cr2.markdown(f"<p style='color:#94a3b8; font-size:13px; text-align:center; margin:8px 0;'>{med_str_v(v1g)}</p>", unsafe_allow_html=True)
                    cr3.markdown(f"<p style='color:#94a3b8; font-size:13px; text-align:center; margin:8px 0;'>{med_str_v(v2g)}</p>", unsafe_allow_html=True)
                    cr4.markdown(f"<p style='color:#00a8ff; font-size:13px; font-weight:700; text-align:center; margin:8px 0;'>{med_str_v(v3g)}</p>", unsafe_allow_html=True)
                    cr5.markdown(f"<p style='color:#94a3b8; font-size:13px; text-align:center; margin:8px 0;'>{med_str_v(v4g)}</p>", unsafe_allow_html=True)
                    cr6.markdown(f"<p style='color:#a855f7; font-size:14px; font-weight:900; text-align:center; margin:8px 0;'>{int(round(tot_g))}d</p>", unsafe_allow_html=True)
                    with cr7:
                        if st.button("🔍 VER", key=f"btn_ae_det_{mes}", use_container_width=True):
                            show_detalle_ae(df_mes_ae, mes_label)

                    st.markdown("<hr style='margin:4px 0; border:none; border-top:1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

            except Exception as e_ae_ind:
                st.error(f"Error en Indicadores Aéreos: {e_ae_ind}")
                import traceback; st.code(traceback.format_exc())

        except Exception as e:
            st.error(f"Error en Indicadores: {e}")

    # --- SOLAPA 7: ALERTAS ESTRATÉGICAS ---

    # --- SOLAPA 7: HISTÓRICO ---
    with tabs[6]:
        try:
            st.markdown("<div style='text-align:center; padding:20px; background:rgba(0,168,255,0.05); border-radius:20px; margin:30px 0;'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:5px; margin:0;'>HISTÓRICO</h2></div>", unsafe_allow_html=True)

            # ── EMBARCADO 2026 ─────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:6px;'>EMBARCADO 2026</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:#475569; font-size:11px; text-align:center; margin-bottom:24px;'>Reservas Históricas · Solo marítimos · ETD 2026</p>", unsafe_allow_html=True)
            try:
                @st.cache_data(ttl=60)
                def load_rh_emb(base):
                    url = f"{base}/export?format=csv&gid=32771816"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)
                df_rh_emb = load_rh_emb(base_url)
                col_emb_b   = df_rh_emb.columns[1]   # B: Cant CTNRs
                col_emb_f   = df_rh_emb.columns[5]   # F: Tipo Carga
                col_emb_l   = df_rh_emb.columns[11]  # L: ETD
                col_emb_ah  = df_rh_emb.columns[33]  # AH: FOB SIMI Total
                col_emb_ai  = df_rh_emb.columns[34]  # AI: M3
                excluir_e   = ['AVION','AVIÓN','COURIER','COURRIER','AIR']
                mask_mar_e  = ~df_rh_emb[col_emb_f].astype(str).str.upper().str.strip().apply(lambda x: any(e in x for e in excluir_e))
                df_rh_emb['_etd_e'] = pd.to_datetime(df_rh_emb[col_emb_l], dayfirst=True, errors='coerce')
                mask_2026_e = df_rh_emb['_etd_e'].dt.year == 2026
                df_emb26    = df_rh_emb[mask_mar_e & mask_2026_e].copy()
                def safe_n(v):
                    try:
                        s = str(v).strip().replace(' ','')
                        if s in ['', 'nan', 'None', '-']: return 0.0
                        # Handle European format: 1.234,56 → 1234.56
                        if ',' in s and '.' in s:
                            if s.index('.') < s.index(','): s = s.replace('.','').replace(',','.')
                            else: s = s.replace(',','')
                        elif ',' in s: s = s.replace(',','.')
                        return float(s)
                    except: return 0.0
                df_emb26['_cntrs'] = df_emb26[col_emb_b].apply(safe_n)
                df_emb26['_fob']   = df_emb26[col_emb_ah].apply(safe_n)
                df_emb26['_m3']    = df_emb26[col_emb_ai].apply(safe_n)
                df_emb26['_embarque'] = df_emb26.iloc[:,0].astype(str)
                df_emb26['_mes'] = df_emb26['_etd_e'].dt.to_period('M').astype(str)

                # KPIs globales
                tot_emb   = df_emb26['_embarque'].nunique()
                tot_cntrs = int(df_emb26['_cntrs'].sum())
                tot_m3    = df_emb26['_m3'].sum()
                tot_fob   = df_emb26['_fob'].sum()
                k1,k2,k3,k4 = st.columns(4)
                with k1: st.markdown(f"<div class='metric-container'><p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 6px 0;'>EMBARQUES</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{tot_emb}</p></div>", unsafe_allow_html=True)
                with k2: st.markdown(f"<div class='metric-container'><p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 6px 0;'>CONTENEDORES</p><p style='color:#f8fafc; font-size:32px; font-weight:900; margin:0;'>{tot_cntrs:,}</p></div>", unsafe_allow_html=True)
                with k3: st.markdown(f"<div class='metric-container'><p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 6px 0;'>VOLUMEN TOTAL</p><p style='color:#00a8ff; font-size:32px; font-weight:900; margin:0;'>{int(round(tot_m3)):,} <span style='font-size:16px; color:#475569;'>M3</span></p></div>", unsafe_allow_html=True)
                with k4: st.markdown(f"<div class='metric-container'><p style='color:#64748b; font-size:10px; letter-spacing:2px; margin:0 0 6px 0;'>FOB TOTAL</p><p style='color:#ffaa00; font-size:28px; font-weight:900; margin:0;'>USD {tot_fob/1_000_000:.1f}M</p></div>", unsafe_allow_html=True)

                # Tabla mensual
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:14px; letter-spacing:3px; margin-bottom:16px;'>DESGLOSE MENSUAL · M3 incluye variación Δ vs mes anterior</p>", unsafe_allow_html=True)

                mes_df = df_emb26.groupby('_mes').agg(
                    Embarques=('_embarque', 'nunique'),
                    Contenedores=('_cntrs', 'sum'),
                    M3=('_m3', 'sum'),
                    FOB=('_fob', 'sum'),
                ).reset_index().sort_values('_mes')
                mes_df['Delta_M3'] = mes_df['M3'].diff()
                mes_df['Delta_Pct'] = (mes_df['M3'].pct_change() * 100).round(1)

                # Headers
                h1,h2,h3,h4,h5,h6 = st.columns([1.2, 0.8, 0.8, 0.9, 0.9, 0.9])
                h1.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700;'>MES ETD</p>", unsafe_allow_html=True)
                h2.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>EMBARQUES</p>", unsafe_allow_html=True)
                h3.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>CNTRS</p>", unsafe_allow_html=True)
                h4.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>M3</p>", unsafe_allow_html=True)
                h5.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>Δ% vs anterior</p>", unsafe_allow_html=True)
                h6.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>FOB USD</p>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0 8px 0; border:none; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)

                for _, r in mes_df.iterrows():
                    pct = r['Delta_Pct']
                    if pd.isna(pct):
                        pct_str = "—"
                    else:
                        pct_str = f"+{pct:.1f}%" if pct > 0 else f"{pct:.1f}%"
                    fob_str = f"USD {r['FOB']/1_000_000:.1f}M" if r['FOB'] >= 1_000_000 else f"USD {r['FOB']/1_000:.0f}K"
                    c1,c2,c3,c4,c5,c6 = st.columns([1.2, 0.8, 0.8, 0.9, 0.9, 0.9])
                    c1.markdown(f"<p style='color:#f8fafc; font-size:14px; font-weight:600; margin:6px 0;'>{r['_mes']}</p>", unsafe_allow_html=True)
                    c2.markdown(f"<p style='color:#94a3b8; font-size:14px; text-align:center; margin:6px 0;'>{int(r['Embarques'])}</p>", unsafe_allow_html=True)
                    c3.markdown(f"<p style='color:#94a3b8; font-size:14px; text-align:center; margin:6px 0;'>{int(r['Contenedores'])}</p>", unsafe_allow_html=True)
                    c4.markdown(f"<p style='color:#00a8ff; font-size:15px; font-weight:700; text-align:center; margin:6px 0;'>{int(round(r['M3'])):,}</p>", unsafe_allow_html=True)
                    c5.markdown(f"<p style='color:#94a3b8; font-size:14px; text-align:center; margin:6px 0;'>{pct_str}</p>", unsafe_allow_html=True)
                    c6.markdown(f"<p style='color:#ffaa00; font-size:14px; font-weight:600; text-align:center; margin:6px 0;'>{fob_str}</p>", unsafe_allow_html=True)

                # Total row
                st.markdown("<hr style='margin:8px 0; border:none; border-top:1px solid rgba(255,255,255,0.3);'>", unsafe_allow_html=True)
                t1,t2,t3,t4,t5,t6 = st.columns([1.2, 0.8, 0.8, 0.9, 0.9, 0.9])
                t1.markdown("<p style='color:#f8fafc; font-size:15px; font-weight:800; margin:6px 0;'>TOTAL 2026</p>", unsafe_allow_html=True)
                t2.markdown(f"<p style='color:#f8fafc; font-size:15px; font-weight:800; text-align:center; margin:6px 0;'>{tot_emb}</p>", unsafe_allow_html=True)
                t3.markdown(f"<p style='color:#f8fafc; font-size:15px; font-weight:800; text-align:center; margin:6px 0;'>{tot_cntrs:,}</p>", unsafe_allow_html=True)
                t4.markdown(f"<p style='color:#00a8ff; font-size:16px; font-weight:900; text-align:center; margin:6px 0;'>{int(round(tot_m3)):,}</p>", unsafe_allow_html=True)
                t5.markdown("<p style='color:#475569; font-size:14px; text-align:center; margin:6px 0;'>—</p>", unsafe_allow_html=True)
                t6.markdown(f"<p style='color:#ffaa00; font-size:15px; font-weight:800; text-align:center; margin:6px 0;'>USD {tot_fob/1_000_000:.1f}M</p>", unsafe_allow_html=True)

                # ── BLOQUE AÉREO ─────────────────────────────────────────────
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<p style='color:#a855f7; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:6px;'>AÉREO 2026</p>", unsafe_allow_html=True)
                st.markdown("<p style='color:#475569; font-size:11px; text-align:center; margin-bottom:24px;'>Seguimiento Aéreos · ETD 2026</p>", unsafe_allow_html=True)
                try:
                    @st.cache_data(ttl=60)
                    def load_ae_hist(base):
                        url = f"{base}/export?format=csv&gid=88538385"
                        return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                    df_ae_h = load_ae_hist(base_url)
                    col_aeh_emb  = df_ae_h.columns[1]   # B: Embarque
                    col_aeh_etd  = df_ae_h.columns[14]  # O: ETD
                    col_aeh_m3   = df_ae_h.columns[21]  # V: M3
                    col_aeh_uni  = df_ae_h.columns[23]  # X: Unidades
                    col_aeh_fob  = df_ae_h.columns[19]  # T: FOB SIMI TOTAL
                    col_aeh_cw   = df_ae_h.columns[57]  # BF: Chargeable Weight

                    df_ae_h['_etd_h'] = pd.to_datetime(df_ae_h[col_aeh_etd], dayfirst=True, errors='coerce')
                    mask_ae_2026 = df_ae_h['_etd_h'].dt.year == 2026
                    df_ae_h2 = df_ae_h[mask_ae_2026].copy()

                    def safe_n_ae(v):
                        try:
                            s = str(v).strip().replace(' ','')
                            if s in ['','nan','None','-']: return 0.0
                            if ',' in s and '.' in s:
                                if s.index('.') < s.index(','): s = s.replace('.','').replace(',','.')
                                else: s = s.replace(',','')
                            elif ',' in s: s = s.replace(',','.')
                            return float(s)
                        except: return 0.0

                    df_ae_h2['_m3']  = df_ae_h2[col_aeh_m3].apply(safe_n_ae)
                    df_ae_h2['_uni'] = df_ae_h2[col_aeh_uni].apply(safe_n_ae)
                    df_ae_h2['_fob'] = df_ae_h2[col_aeh_fob].apply(safe_n_ae)
                    df_ae_h2['_cw']  = df_ae_h2[col_aeh_cw].apply(safe_n_ae)
                    df_ae_h2['_mes'] = df_ae_h2['_etd_h'].dt.to_period('M').astype(str)

                    # KPIs aéreos
                    tot_ae_emb = df_ae_h2[col_aeh_emb].nunique()
                    tot_ae_m3  = df_ae_h2['_m3'].sum()
                    tot_ae_uni = df_ae_h2['_uni'].sum()
                    tot_ae_fob = df_ae_h2['_fob'].sum()

                    ka1,ka2,ka3,ka4 = st.columns(4)
                    with ka1: st.markdown(f"<div class='metric-container'><p>EMBARQUES</p><p>{tot_ae_emb}</p></div>", unsafe_allow_html=True)
                    with ka2: st.markdown(f"<div class='metric-container'><p>VOLUMEN</p><p style='color:#a855f7; font-size:36px; font-weight:900; margin:0;'>{int(round(tot_ae_m3)):,} <span style='font-size:16px; color:#475569;'>M3</span></p></div>", unsafe_allow_html=True)
                    with ka3: st.markdown(f"<div class='metric-container'><p>UNIDADES</p><p>{int(tot_ae_uni):,}</p></div>", unsafe_allow_html=True)
                    with ka4: st.markdown(f"<div class='metric-container'><p>FOB TOTAL</p><p style='color:#ffaa00; font-size:28px; font-weight:900; margin:0;'>USD {tot_ae_fob/1_000_000:.1f}M</p></div>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Tabla mensual aéreos
                    mes_ae = df_ae_h2.groupby('_mes').agg(
                        Embarques=(col_aeh_emb, 'nunique'),
                        M3=('_m3', 'sum'),
                        Unidades=('_uni', 'sum'),
                        FOB=('_fob', 'sum'),
                        CW=('_cw', 'sum'),
                    ).reset_index().sort_values('_mes')

                    ha1,ha2,ha3,ha4,ha5 = st.columns([1.2, 0.8, 0.8, 0.9, 0.9])
                    ha1.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700;'>MES ETD</p>", unsafe_allow_html=True)
                    ha2.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>EMBARQUES</p>", unsafe_allow_html=True)
                    ha3.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>M3</p>", unsafe_allow_html=True)
                    ha4.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>CHARGEABLE W.</p>", unsafe_allow_html=True)
                    ha5.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>FOB USD</p>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin:4px 0 8px 0; border:none; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)

                    for _, r in mes_ae.iterrows():
                        cw_str  = f"{int(round(r['CW'])):,} kg" if r['CW'] > 0 else "—"
                        fob_a_str = f"USD {r['FOB']/1_000_000:.1f}M" if r['FOB'] >= 1_000_000 else f"USD {r['FOB']/1_000:.0f}K"
                        ca1,ca2,ca3,ca4,ca5 = st.columns([1.2, 0.8, 0.8, 0.9, 0.9])
                        ca1.markdown(f"<p style='color:#f8fafc; font-size:14px; font-weight:600; margin:6px 0;'>{r['_mes']}</p>", unsafe_allow_html=True)
                        ca2.markdown(f"<p style='color:#94a3b8; font-size:14px; text-align:center; margin:6px 0;'>{int(r['Embarques'])}</p>", unsafe_allow_html=True)
                        ca3.markdown(f"<p style='color:#a855f7; font-size:15px; font-weight:700; text-align:center; margin:6px 0;'>{int(round(r['M3'])):,}</p>", unsafe_allow_html=True)
                        ca4.markdown(f"<p style='color:#00a8ff; font-size:14px; font-weight:700; text-align:center; margin:6px 0;'>{cw_str}</p>", unsafe_allow_html=True)
                        ca5.markdown(f"<p style='color:#ffaa00; font-size:14px; font-weight:600; text-align:center; margin:6px 0;'>{fob_a_str}</p>", unsafe_allow_html=True)

                    tot_ae_cw = df_ae_h2['_cw'].sum()
                    st.markdown("<hr style='margin:8px 0; border:none; border-top:1px solid rgba(255,255,255,0.3);'>", unsafe_allow_html=True)
                    ta1,ta2,ta3,ta4,ta5 = st.columns([1.2, 0.8, 0.8, 0.9, 0.9])
                    ta1.markdown("<p style='color:#f8fafc; font-size:15px; font-weight:800; margin:6px 0;'>TOTAL 2026</p>", unsafe_allow_html=True)
                    ta2.markdown(f"<p style='color:#f8fafc; font-size:15px; font-weight:800; text-align:center; margin:6px 0;'>{tot_ae_emb}</p>", unsafe_allow_html=True)
                    ta3.markdown(f"<p style='color:#a855f7; font-size:16px; font-weight:900; text-align:center; margin:6px 0;'>{int(round(tot_ae_m3)):,}</p>", unsafe_allow_html=True)
                    ta4.markdown(f"<p style='color:#00a8ff; font-size:15px; font-weight:800; text-align:center; margin:6px 0;'>{int(round(tot_ae_cw)):,} kg</p>", unsafe_allow_html=True)
                    ta5.markdown(f"<p style='color:#ffaa00; font-size:15px; font-weight:800; text-align:center; margin:6px 0;'>USD {tot_ae_fob/1_000_000:.1f}M</p>", unsafe_allow_html=True)

                except Exception as e_ae_h:
                    st.error(f"Error en Aéreo Histórico: {e_ae_h}")
                    import traceback; st.code(traceback.format_exc())

            except Exception as e_emb:
                st.error(f"Error en Embarcado 2026: {e_emb}")
                import traceback; st.code(traceback.format_exc())


            # ── TIEMPOS POR PUERTO: CONSOLIDACIÓN + TRANSIT TIME ──────────────
            st.markdown("<hr class='white-divider'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#00a8ff; font-weight:700; font-size:18px; text-align:center; letter-spacing:4px; margin-bottom:6px;'>TIEMPOS POR PUERTO DE ORIGEN</p>", unsafe_allow_html=True)
            st.markdown("<p style='color:#475569; font-size:11px; text-align:center; margin-bottom:24px;'>Mediana de Consolidación + Transit Time real · Comparativa vs targets 2026 · Solo embarques marítimos</p>", unsafe_allow_html=True)

            try:
                @st.cache_data(ttl=60)
                def load_rh_tiempos(base):
                    url = f"{base}/export?format=csv&gid=32771816"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                @st.cache_data(ttl=60)
                def load_val_tiempos(base):
                    url = f"{base}/export?format=csv&gid=889641786"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                df_rh_t = load_rh_tiempos(base_url)
                df_val_t = load_val_tiempos(base_url)

                # ── RESERVAS HISTÓRICAS: limpiar y filtrar ───────────────────
                col_rh_puerto   = df_rh_t.columns[4]   # E: Puerto/Aeropuerto
                col_rh_tipo     = df_rh_t.columns[5]   # F: Tipo Carga
                col_rh_etd      = df_rh_t.columns[11]  # L: ETD
                col_rh_mono     = df_rh_t.columns[24]  # Y: ¿ES MONOPROVEEDOR?
                col_rh_consol   = df_rh_t.columns[32]  # AG: T.Consolidación
                col_rh_tt       = df_rh_t.columns[74]  # BW: TT real (índice 74)

                # Excluir aéreos/courier
                excluir_tipo = ['AVION', 'AVIÓN', 'COURIER', 'COURRIER', 'AIR']
                mask_mar_rh = ~df_rh_t[col_rh_tipo].astype(str).str.upper().str.strip().apply(
                    lambda x: any(e in x for e in excluir_tipo)
                )

                # Filtrar 2026 por ETD
                df_rh_t['_etd_dt'] = pd.to_datetime(df_rh_t[col_rh_etd], dayfirst=True, errors='coerce')
                mask_2026 = df_rh_t['_etd_dt'].dt.year == 2026

                df_rh_t2 = df_rh_t[mask_mar_rh & mask_2026].copy()

                def safe_num_rh(v):
                    try: return float(str(v).replace(',','.').strip())
                    except: return None

                df_rh_t2['_consol'] = df_rh_t2[col_rh_consol].apply(safe_num_rh)
                df_rh_t2['_tt']     = df_rh_t2[col_rh_tt].apply(safe_num_rh)
                df_rh_t2['_es_mono'] = df_rh_t2[col_rh_mono].astype(str).str.strip().str.upper().isin(['SI','SÍ','S','MONOPROVEEDOR'])
                df_rh_t2['_puerto'] = df_rh_t2[col_rh_puerto].astype(str).str.strip().str.title()

                # ── VALIDACIONES: parsear targets ────────────────────────────
                # Col E=idx4: Puerto-tipo, F=idx5: Consol target, G=idx6: TT target, H=idx7: Total target
                col_v_puerto = df_val_t.columns[4]
                col_v_consol = df_val_t.columns[5]
                col_v_tt     = df_val_t.columns[6]
                col_v_total  = df_val_t.columns[7]

                targets = {}
                for _, vr in df_val_t.iterrows():
                    raw = str(vr[col_v_puerto]).strip()
                    if raw in ['', 'nan', 'Puertos']: continue
                    es_mono_v = 'MONO' in raw.upper() or 'MONOPRO' in raw.upper()
                    puerto_v  = raw.split('-')[0].strip()
                    try: tc = float(str(vr[col_v_consol]).replace(',','.'))
                    except: tc = None
                    try: tt = float(str(vr[col_v_tt]).replace(',','.'))
                    except: tt = None
                    try: tot = float(str(vr[col_v_total]).replace(',','.'))
                    except: tot = None
                    key = (puerto_v.upper(), 'MONO' if es_mono_v else 'CONS')
                    targets[key] = {'consol': tc, 'tt': tt, 'total': tot}

                def semaforo_color(real, target):
                    if real is None or target is None: return '#475569', '—'
                    if real <= target: return '#00ff88', '✅'
                    elif real <= target * 1.15: return '#ffaa00', '⚠️'
                    else: return '#ff4b4b', '🔴'

                def render_tabla_puertos(df_sub, tipo_label, tipo_key):
                    puertos_data = df_sub.groupby('_puerto').agg(
                        med_consol=('_consol', 'median'),
                        med_tt=('_tt', 'median'),
                        n=('_consol', 'count')
                    ).reset_index()
                    puertos_data = puertos_data[puertos_data['n'] >= 2].sort_values('med_consol', ascending=False)
                    if puertos_data.empty:
                        st.info(f"Sin datos suficientes para {tipo_label}")
                        return

                    # ── RESUMEN GLOBAL ───────────────────────────────────
                    med_consol_g = df_sub['_consol'].dropna().median()
                    med_tt_g     = df_sub['_tt'].dropna().median()
                    total_g      = (med_consol_g if med_consol_g == med_consol_g else 0) + (med_tt_g if med_tt_g == med_tt_g else 0)
                    color_tipo   = '#00a8ff' if tipo_key == 'MONO' else '#ffaa00'

                    st.markdown(f"""
            <div style='background:rgba(255,255,255,0.02); border-radius:14px; border-left:4px solid {color_tipo};
            padding:18px 24px; margin-bottom:20px; display:flex; gap:32px; align-items:center; flex-wrap:wrap;'>
            <div>
                <p>{tipo_label} · Mediana Global 2026</p>
                <p style='color:{color_tipo}; font-size:28px; font-weight:900; margin:0; line-height:1;'>{int(round(total_g))}d <span style='font-size:13px; color:#475569; font-weight:400;'>total</span></p>
            </div>
            <div style='width:1px; background:rgba(255,255,255,0.08); align-self:stretch;'></div>
            <div>
                <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>CONSOLIDACIÓN</p>
                <p style='color:#00a8ff; font-size:20px; font-weight:800; margin:0;'>{int(round(med_consol_g)) if med_consol_g==med_consol_g else '—'}d</p>
            </div>
            <div style='color:#334155; font-size:20px;'>+</div>
            <div>
                <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>TRANSIT TIME</p>
                <p style='color:#ffaa00; font-size:20px; font-weight:800; margin:0;'>{int(round(med_tt_g)) if med_tt_g==med_tt_g else '—'}d</p>
            </div>
            <div style='color:#334155; font-size:20px;'>=</div>
            <div>
                <p style='color:#64748b; font-size:9px; letter-spacing:1px; margin:0 0 3px 0;'>TOTAL</p>
                <p style='color:{color_tipo}; font-size:20px; font-weight:900; margin:0;'>{int(round(total_g))}d</p>
            </div>
            </div>""", unsafe_allow_html=True)

                    # Headers
                    h1,h2,h3,h4,h5,h6,h7 = st.columns([1.4, 0.6, 0.8, 0.8, 0.8, 0.8, 0.5])
                    h1.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700;'>PUERTO</p>", unsafe_allow_html=True)
                    h2.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>EMB.</p>", unsafe_allow_html=True)
                    h3.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>CONSOL (real)</p>", unsafe_allow_html=True)
                    h4.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>TT (real)</p>", unsafe_allow_html=True)
                    h5.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>TOTAL (real)</p>", unsafe_allow_html=True)
                    h6.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>T. VALIDACIONES</p>", unsafe_allow_html=True)
                    h7.markdown("<p style='color:#94a3b8; font-size:10px; letter-spacing:1px; font-weight:700; text-align:center;'>🚦</p>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin:4px 0 8px 0; border:none; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)

                    for _, pr in puertos_data.iterrows():
                        puerto_n = pr['_puerto']
                        mc = pr['med_consol']
                        mt = pr['med_tt']
                        n_emb = int(pr['n'])
                        total_real = (mc if mc == mc else 0) + (mt if mt == mt else 0)
                        tgt = targets.get((puerto_n.upper(), tipo_key), targets.get((puerto_n.title().upper(), tipo_key), {}))
                        tgt_total = tgt.get('total')
                        color_sem, ico = semaforo_color(total_real, tgt_total)
                        c1,c2,c3,c4,c5,c6,c7 = st.columns([1.4, 0.6, 0.8, 0.8, 0.8, 0.8, 0.5])
                        c1.markdown(f"<p style='color:#f8fafc; font-size:14px; font-weight:600; margin:6px 0;'>{puerto_n}</p>", unsafe_allow_html=True)
                        c2.markdown(f"<p style='color:#64748b; font-size:13px; font-weight:600; text-align:center; margin:6px 0;'>{n_emb}</p>", unsafe_allow_html=True)
                        c3.markdown(f"<p style='color:#00a8ff; font-size:15px; font-weight:700; text-align:center; margin:6px 0;'>{int(round(mc)) if mc==mc else '—'}d</p>", unsafe_allow_html=True)
                        c4.markdown(f"<p style='color:#ffaa00; font-size:15px; font-weight:700; text-align:center; margin:6px 0;'>{int(round(mt)) if mt==mt else '—'}d</p>", unsafe_allow_html=True)
                        c5.markdown(f"<p style='color:{color_sem}; font-size:16px; font-weight:900; text-align:center; margin:6px 0;'>{int(round(total_real))}d</p>", unsafe_allow_html=True)
                        c6.markdown(f"<p style='color:#475569; font-size:14px; text-align:center; margin:6px 0;'>{int(tgt_total) if tgt_total else '—'}d</p>", unsafe_allow_html=True)
                        c7.markdown(f"<p style='font-size:18px; text-align:center; margin:6px 0;'>{ico}</p>", unsafe_allow_html=True)

                tab_mono, tab_cons = st.tabs(["🔵 MONOPROVEEDOR", "🟡 CONSOLIDADO"])
                with tab_mono:
                    st.markdown("<br>", unsafe_allow_html=True)
                    render_tabla_puertos(df_rh_t2[df_rh_t2['_es_mono']], "Monoproveedor", "MONO")
                with tab_cons:
                    st.markdown("<br>", unsafe_allow_html=True)
                    render_tabla_puertos(df_rh_t2[~df_rh_t2['_es_mono']], "Consolidado", "CONS")

            except Exception as e_tp:
                st.error(f"Error en Tiempos por Puerto: {e_tp}")
                import traceback; st.code(traceback.format_exc())



        except Exception as e:
            st.error(f"Error en Histórico: {e}")


    # --- SOLAPA 8: ASK COMEX ---
    with tabs[7]:
        st.markdown("<div style='text-align:center; padding: 40px; background: rgba(0, 168, 255, 0.05); border-radius: 20px; border: 2px dashed rgba(0, 168, 255, 0.2);'><h2 style='color:#00a8ff; font-weight:800; letter-spacing:10px;'>ASK COMEX</h2><p style='color:#94a3b8; font-size:18px; margin-top:20px;'>Inteligencia Operativa en Tiempo Real.</p></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            with st.popover("💬 Hablar con Capitán Comex (IA)", use_container_width=False):
                st.markdown("🚧 Estamos trabajando en esta funcionalidad", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            search_query = st.text_input("🔍 Buscar por N° de SO o N° de Embarque", placeholder="Ej: GAD-2026-0001  ó  EMB-123456", key="ask_search")

            if search_query and search_query.strip():
                sq = search_query.strip()

                @st.cache_data(ttl=60)
                def load_impo2(base):
                    url = f"{base}/export?format=csv&gid=131563120"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                @st.cache_data(ttl=60)
                def load_ddp(base):
                    url = f"{base}/export?format=csv&gid=2050674215"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                @st.cache_data(ttl=60)
                def load_hist_ask(base):
                    url = f"{base}/export?format=csv&gid=50628730"
                    return pd.read_csv(url, engine='python', on_bad_lines='skip', header=0)

                df_impo2   = load_impo2(base_url)
                df_ddp     = load_ddp(base_url)
                df_hist_ask = load_hist_ask(base_url)

                def get_estadio_impo2(emb, df_i2, df_d):
                    emb_str = str(emb).strip()
                    # Check DDP
                    ddp_match = df_d[df_d.iloc[:,5].astype(str).str.strip() == emb_str]
                    if not ddp_match.empty:
                        f_retiro = str(ddp_match.iloc[0,1]).strip()
                        f_ofi    = str(ddp_match.iloc[0,3]).strip()
                        if f_retiro not in ['','nan','None']: return 8, f_retiro, f_ofi
                        if f_ofi    not in ['','nan','None']: return 7, f_retiro, f_ofi
                    # Check Impo2
                    i2_match = df_i2[df_i2.iloc[:,0].astype(str).str.strip() == emb_str]
                    if not i2_match.empty:
                        f_salida = str(i2_match.iloc[0,1]).strip()
                        f_arribo = str(i2_match.iloc[0,2]).strip()
                        if f_arribo not in ['','nan','None']: return 6, f_salida, f_arribo
                        if f_salida not in ['','nan','None']: return 5, f_salida, ''
                    return None, '', ''

                # Search in df (Planif Cargas)
                col_so_pc   = 'SO'
                col_emb_pc  = df.columns[16]   # Q
                col_inst_pc = df.columns[20]    # U
                col_etd_ok  = df.columns[97]    # ETD OK FFWW
                col_etd_pc  = df.columns[23]    # X
                col_eta_pc  = df.columns[24]    # Y
                col_pais_pc = df.columns[18]    # S
                col_sku_pc  = df.columns[32]    # AG
                col_inv_pc  = df.columns[29]    # AD
                col_fprod_pc = df.columns[99]   # CV
                col_prov_pc = df.columns[18]    # Proveedor
                col_analista_ask = next((c for c in df.columns if 'ANALISTA' in str(c).upper() or 'RESPONSABLE' in str(c).upper()), None)

                mask_so  = df[col_so_pc].astype(str).str.upper().str.contains(sq.upper(), na=False)
                mask_emb = df[col_emb_pc].astype(str).str.strip() == sq
                df_found = df[mask_so | mask_emb].copy()

                # Fallback to historical
                used_hist = False
                if df_found.empty:
                    col_emb_h = df_hist_ask.columns[4]
                    col_so_h  = df_hist_ask.columns[0]
                    mh = (df_hist_ask[col_emb_h].astype(str).str.strip() == sq) | \
                         (df_hist_ask[col_so_h].astype(str).str.upper().str.contains(sq.upper(), na=False))
                    if mh.any():
                        used_hist = True
                        embs_hist = df_hist_ask[mh][col_emb_h].unique()
                        df_found  = df[df[col_emb_pc].astype(str).str.strip().isin([str(e) for e in embs_hist])].copy()

                if df_found.empty:
                    st.warning(f"No se encontraron resultados para: **{sq}**")
                else:
                    sos_found = df_found[col_so_pc].unique()
                    st.markdown(f"<p style='color:#94a3b8; font-size:12px;'>Se encontraron <b style='color:#00a8ff;'>{len(sos_found)} SO</b> {'(desde histórico)' if used_hist else ''}</p>", unsafe_allow_html=True)

                    ESTADIOS = [
                        "PENDIENTE DE INSTRUCCION",
                        "EN PROCESO DE CONSOLIDACION",
                        "INSTRUCCION ENVIADA - ESPERA BOOKING",
                        "BOOKING CONFIRMADO",
                        "EN TRANSITO",
                        "ARRIBADO",
                        "NACIONALIZADO",
                        "ENTREGADO EN DEPOSITO",
                    ]
                    COLORES_EST = ['#ff4b4b','#ffaa00','#f97316','#00a8ff','#06b6d4','#a855f7','#00ff88','#00ff88']

                    resultados = []
                    for so_val in sos_found:
                        rows_so = df_found[df_found[col_so_pc] == so_val]
                        row = rows_so.iloc[0]
                        val_emb   = str(row[col_emb_pc]).strip()
                        val_inst  = str(row[col_inst_pc]).strip()
                        val_etdok = str(row[col_etd_ok]).strip().upper()
                        val_etd   = str(row[col_etd_pc]).strip()
                        val_eta   = str(row[col_eta_pc]).strip()
                        val_sku   = str(row[col_sku_pc]).strip()
                        val_inv   = str(row[col_inv_pc]).strip()
                        val_fprod = str(row[col_fprod_pc]).strip() if col_fprod_pc in df.columns else '—'
                        val_prov  = str(row.iloc[18]).strip()
                        val_analista = str(row[col_analista_ask]).strip() if col_analista_ask else '—'
                        if val_analista.lower() in ['nan','none','']: val_analista = '—'
                        cantidad_mostrar = rows_so['M3 Total'].apply(lambda x: safe_float(x) if 'safe_float' in dir() else 0).sum()
                        label_cant = 'M3'

                        etd_dt = pd.to_datetime(val_etd, dayfirst=True, errors='coerce')
                        eta_dt = pd.to_datetime(val_eta, dayfirst=True, errors='coerce')
                        etd_display = etd_dt.strftime('%d/%m/%Y') if pd.notna(etd_dt) else '—'
                        eta_display = eta_dt.strftime('%d/%m/%Y') if pd.notna(eta_dt) else '—'

                        # Determine estadio
                        sin_emb  = val_emb in ['','nan','None']
                        sin_inst = val_inst in ['','nan','None'] or 'SIN INSTRUCCION' in val_inst.upper()
                        etd_ok   = val_etdok == 'OK'
                        hoy_ts   = pd.Timestamp.now().normalize()
                        etd_past = pd.notna(etd_dt) and etd_dt < hoy_ts

                        estadio_num, f_sal, f_arr = get_estadio_impo2(val_emb, df_impo2, df_ddp)

                        if estadio_num == 8:   est_idx = 7
                        elif estadio_num == 7: est_idx = 6
                        elif estadio_num == 6: est_idx = 5
                        elif estadio_num == 5: est_idx = 4
                        elif sin_emb:          est_idx = 0
                        elif sin_inst:         est_idx = 1
                        elif not etd_ok:       est_idx = 2
                        elif not etd_past:     est_idx = 3
                        else:                  est_idx = 4

                        resultados.append({
                            "so": so_val, "emb": val_emb, "prov": val_prov,
                            "cant": round(cantidad_mostrar, 1), "label_cant": label_cant,
                            "fecha_inst": val_inst[:10] if len(val_inst) >= 10 else val_inst,
                            "fin_prod": val_fprod[:10] if len(val_fprod) >= 10 else val_fprod,
                            "etd": etd_display, "eta": eta_display,
                            "analista": val_analista,
                            "sku": val_sku, "invoice": val_inv,
                            "estadio": est_idx, "f_sal": f_sal, "f_arr": f_arr,
                        })

                    for r in sorted(resultados, key=lambda x: x['estadio']):
                        est_idx = r['estadio']
                        c_est   = COLORES_EST[est_idx]
                        pct     = round((est_idx + 1) / 8 * 100)
                        st.markdown(
                            f"<div class='custom-card' style='border-top:5px solid {c_est};'>"
                            f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;'>"
                            f"<div><p style='color:{c_est}; font-weight:900; font-size:20px; margin:0;'>{ESTADIOS[est_idx]}</p>"
                            f"<p style='color:#64748b; font-size:11px; margin:4px 0 0 0;'>Estadio {est_idx+1} de 8</p></div>"
                            f"<div style='text-align:right;'><p style='color:{c_est}; font-size:28px; font-weight:900; margin:0;'>{pct}%</p></div></div>"
                            f"<div style='height:6px; background:rgba(255,255,255,0.07); border-radius:3px; margin-bottom:16px;'>"
                            f"<div style='height:6px; width:{pct}%; background:{c_est}; border-radius:3px;'></div></div>"
                            f"<div class='grid-2'>"
                            f"<div><p class='minicard-title'>SO</p><p style='font-size:18px; font-weight:700; color:#f8fafc; margin:0;'>{r['so']}</p></div>"
                            f"<div><p class='minicard-title'>EMBARQUE</p><p style='font-size:18px; font-weight:700; color:#f8fafc; margin:0;'>{r['emb'] if r['emb'] not in ['','nan'] else '—'}</p></div>"
                            f"<div><p class='minicard-title'>PROVEEDOR</p><p style='font-size:14px; color:#f8fafc; margin:0; font-weight:600;'>{r['prov']}</p></div>"
                            f"<div><p class='minicard-title'>TOTAL {r['label_cant']}</p><p style='font-size:24px; color:#00ff88; font-weight:900; margin:0;'>{r['cant']}</p></div>"
                            f"<div><p class='minicard-title'>ANALISTA</p><p style='font-size:14px; color:#a855f7; margin:0; font-weight:700;'>{r.get('analista','—')}</p></div>"
                            f"<div></div>"
                            f"</div>"
                            f"<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:12px; border-top:1px solid rgba(255,255,255,0.06); padding-top:12px;'>"
                            f"<div><p class='minicard-title'>F. INSTRUCCIÓN</p><p style='color:#f8fafc; font-size:13px; margin:0;'>{r['fecha_inst'] if r['fecha_inst'] not in ['','nan'] else '—'}</p></div>"
                            f"<div><p class='minicard-title'>FIN PRODUCCIÓN</p><p style='color:#f8fafc; font-size:13px; margin:0;'>{r['fin_prod'] if r['fin_prod'] not in ['','nan'] else '—'}</p></div>"
                            f"<div><p class='minicard-title'>ETD</p><p style='color:#00ff88; font-size:13px; font-weight:700; margin:0;'>{r['etd']}</p></div>"
                            f"<div><p class='minicard-title'>ETA</p><p style='color:#ffaa00; font-size:13px; font-weight:700; margin:0;'>{r['eta']}</p></div>"
                            f"</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
        except Exception as e:
            st.error(f"Error en ASK COMEX: {e}")
            import traceback; st.code(traceback.format_exc())

except Exception as e:
    st.error(f"Error general al cargar el dashboard: {e}")
    import traceback
    st.code(traceback.format_exc())
