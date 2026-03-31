# --- SOLAPA 2: STATUS CARGAS ---
   
    with tabs[1]:
        try:
            # 1. CARGA DE DATOS ESPECÍFICA (Hoja Reservas GID 276804813)
            # Usamos nocache para que los cambios en el Excel se vean rápido
            url_reserva = f"{base_url}/export?format=csv&gid=276804813&nocache={time.time()}"
            df_reserva = pd.read_csv(url_reserva)
            df_reserva.columns = df_reserva.columns.str.strip()

            # 2. MÉTRICAS DE CONTROL (Basadas en lo que ya está Instruido en la Hoja 0)
            # Estas métricas vienen del df que cargamos al principio del archivo
            df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
            df_solo_instruidos = df[df['Fecha_Inst_DT'].notna()].copy()
            
            m_so_inst = len(df_solo_instruidos)
            m_m3_inst = df_solo_instruidos['M3 Total'].sum()
            m_prov_inst = df_solo_instruidos['Proveedor'].nunique()

            # Renderizado de Cabecera de la Solapa
            st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 3px;'>MONITOREO DE RESERVAS</h2>", unsafe_allow_html=True)
            
            # Cuadros de métricas en formato BIDCOM
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.markdown(f"<div class='metric-container'><p class='label-massive'>SO INSTRUIDAS</p><p class='value-massive'>{int(m_so_inst)}</p></div>", unsafe_allow_html=True)
            with col_s2:
                st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN (M3)</p><p class='value-massive'>{int(m_m3_inst):,}</p></div>", unsafe_allow_html=True)
            with col_s3:
                st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(m_prov_inst)}</p></div>", unsafe_allow_html=True)

            st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

            # 3. INTERFAZ DE LA TABLA DE RESERVAS
            st.markdown("<p class='chart-title'>Consolidado de Reservas y Bookings (Hoja Reservas)</p>", unsafe_allow_html=True)
            
            # Buscador para filtrar la tabla de reservas
            busqueda = st.text_input("🔍 Filtrar Reservas (escribe SO, Proveedor o Nro de Booking):", key="search_status_tab")
            
            if busqueda:
                # Filtra en todas las columnas de la hoja de reservas
                mask_res = df_reserva.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
                df_res_final = df_reserva[mask_res]
            else:
                df_res_final = df_reserva

            # Visualización de la tabla
            st.dataframe(
                df_res_final, 
                use_container_width=True,
                height=550
            )

            # Pie de tabla con info de carga
            st.markdown(f"**Líneas totales en Reservas:** {len(df_reserva)} | **Resultados encontrados:** {len(df_res_final)}")

        except Exception as e:
            st.error(f"Error al conectar con la Hoja de Reservas: {e}")

        # 2. MÉTRICAS DE CONTROL (Basadas en lo Instruido de la Hoja 0)
        # Filtramos lo que tiene fecha de instrucción
        df['Fecha_Inst_DT'] = pd.to_datetime(df['Fecha de Instruccion'], errors='coerce')
        df_inst_status = df[df['Fecha_Inst_DT'].notna()].copy()
        
        m_so = len(df_inst_status)
        m_m3 = df_inst_status['M3 Total'].sum()
        m_prov = df_inst_status['Proveedor'].nunique()

        # Render métricas masivas en la parte superior
        st.markdown("<h2 style='text-align: center; color: #ffffff; letter-spacing: 3px;'>MONITOREO DE RESERVAS</h2>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>SO INSTRUIDAS</p><p class='value-massive'>{int(m_so)}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>VOLUMEN (M3)</p><p class='value-massive'>{int(m_m3):,}</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-container'><p class='label-massive'>PROVEEDORES</p><p class='value-massive'>{int(m_prov)}</p></div>", unsafe_allow_html=True)

        st.markdown("<br><hr style='opacity:0.1'><br>", unsafe_allow_html=True)

        # 3. INTERFAZ DE RESERVAS (Hoja 2)
        st.markdown("<p class='chart-title'>Consolidado de Reservas y Bookings</p>", unsafe_allow_html=True)
        
        # Buscador rápido para la tabla de reservas
        search_res = st.text_input("🔍 Buscar por SO, Proveedor o Booking en Reservas:", "")
        
        if search_res:
            # Filtro dinámico en todas las columnas
            df_res_filt = df_reserva[df_reserva.astype(str).apply(lambda x: x.str.contains(search_res, case=False)).any(axis=1)]
        else:
            df_res_filt = df_reserva

        # Tabla de Reservas con estilo BIDCOM
        st.dataframe(
            df_res_filt.style.format(precision=0), 
            use_container_width=True,
            height=600
        )

        # 4. RESUMEN RÁPIDO DE LA HOJA DE RESERVAS (Totales al pie)
        st.markdown("---")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            # Contamos cuántas reservas hay por Analista o por Status (ajustar según tus columnas de la Hoja 2)
            st.markdown("**Resumen de Registros en Hoja Reservas:**")
            st.write(f"Total de líneas cargadas: {len(df_reserva)}")
