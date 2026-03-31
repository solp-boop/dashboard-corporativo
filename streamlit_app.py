# --- PROCESAMIENTO DE FECHAS (OPTIMIZADO) ---
    # Usamos las columnas 23 (ETD) y 24 (ETA) 
    df['ETD_DT'] = pd.to_datetime(df.iloc[:, 23], errors='coerce')
    df['ETA_DT'] = pd.to_datetime(df.iloc[:, 24], errors='coerce')
    df['Fecha_Prior_DT'] = pd.to_datetime(df.iloc[:, 99], errors='coerce') 
    
    hoy = pd.Timestamp(datetime.now().date())
    inicio_mes = hoy.replace(day=1)

    def label_proyeccion(fecha, pivot):
        if pd.isna(fecha): return "SIN FECHA"
        if fecha.year < 2024: return "PASADO/REALIZADO" # Filtro de seguridad para años viejos
        if fecha < pivot: return "PASADO/REALIZADO"
        return fecha.strftime('%m/%Y')

    df['Mes_ETD_Full'] = df['ETD_DT'].apply(lambda x: label_proyeccion(x, inicio_mes))
    df['Mes_ETA_Full'] = df['ETA_DT'].apply(lambda x: label_proyeccion(x, hoy))

    # Ordenar categorías para que el gráfico sea una línea de tiempo
    cat_orden = sorted([m for m in df['Mes_ETA_Full'].unique() if m not in ["PASADO/REALIZADO", "SIN FECHA"]])
    orden_final = ["PASADO/REALIZADO"] + cat_orden + ["SIN FECHA"]
    df['Mes_ETA_Full'] = pd.Categorical(df['Mes_ETA_Full'], categories=orden_final, ordered=True)

    m3_totales_global = round(df['M3 Total'].sum())
    cant_so_global = len(df)
    cant_proveedores_global = df['Proveedor'].nunique() if 'Proveedor' in df.columns else 0

    # --- HEADER ---
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

        if st.session_state.get('f'):
            st.markdown("---")
            f = st.session_state.f
            if f == "inst":
                df_mostrar = df_instruidos_only[['SO', 'Proveedor', 'M3 Total', 'Fecha de Instruccion']].copy()
                t_so, t_prov, t_m3 = len(df_mostrar), df_mostrar['Proveedor'].nunique(), df_mostrar['M3 Total'].sum()
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {t_so}'], 'Proveedor': [f'TOTAL PROV: {t_prov}'], 'M3 Total': [t_m3], 'Fecha de Instruccion': ['']})
                df_final = pd.concat([df_mostrar, total_row.set_index(pd.Index(['TOTAL']))])
                st.dataframe(df_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif f == "pend":
                df_pend_list = df_pendientes_only.sort_values(by='Fecha_Prior_DT', ascending=True).copy()
                df_mostrar_pend = df_pend_list[['SO', 'Proveedor', df.columns[99], 'M3 Total']].copy()
                t_so_p, t_prov_p, t_m3_p = len(df_mostrar_pend), df_mostrar_pend['Proveedor'].nunique(), df_mostrar_pend['M3 Total'].sum()
                total_row = pd.DataFrame({'SO': [f'TOTAL SO: {t_so_p}'], 'Proveedor': [f'TOTAL PROV: {t_prov_p}'], df.columns[99]: [''], 'M3 Total': [t_m3_p]})
                df_final = pd.concat([df_mostrar_pend, total_row.set_index(pd.Index(['TOTAL']))])
                st.dataframe(df_final.style.apply(lambda s: ['background-color: #003366; font-weight: bold; color: white' if s.name == 'TOTAL' else '' for _ in s], axis=1).format({'M3 Total': '{:,.0f}'}), use_container_width=True)
            elif f == "estr":
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
            fig_p.update_layout(xaxis_title=None, yaxis_title=None, height=500)
            st.plotly_chart(fig_p, use_container_width=True)

        with g2:
            st.markdown("<p class='chart-title'>Proyección ETD (Salidas)</p>", unsafe_allow_html=True)
            etd_p = df.groupby('Mes_ETD_Full').agg({'M3 Total': 'sum'}).reset_index()
            fig_e = px.bar(etd_p, x='Mes_ETD_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#00ff88'], template='plotly_dark')
            fig_e.update_layout(xaxis_title=None, yaxis_title=None, height=500)
            st.plotly_chart(fig_e, use_container_width=True)

        with g3:
            st.markdown("<p class='chart-title'>Proyección ETA (Arribos)</p>", unsafe_allow_html=True)
            # Usamos el DataFrame agrupado por el orden categórico definido arriba
            eta_p = df.groupby('Mes_ETA_Full', observed=True).agg({'M3 Total': 'sum'}).reset_index()
            fig_a = px.bar(eta_p, x='Mes_ETA_Full', y='M3 Total', text_auto=',.0f', color_discrete_sequence=['#ff4b4b'], template='plotly_dark')
            fig_a.update_layout(xaxis_title=None, yaxis_title=None, height=500)
            st.plotly_chart(fig_a, use_container_width=True)
