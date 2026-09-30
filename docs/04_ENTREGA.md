# Etapas 3 a 5 — Entrega: decisiones, mejoras y pruebas

## Principales decisiones

1. **Se mantiene Streamlit.** Los problemas eran de estructura, no de tecnología (ver `03_ARQUITECTURA.md`).
2. **Multipágina con `st.navigation`** en lugar de 8 `st.tabs`. Solo se ejecuta la página visible.
3. **Una lectura por solapa, en paralelo, una vez cada 10 minutos.** Sin credenciales se usa el mismo enlace público que la app anterior; con cuenta de servicio, un batch con solo las columnas usadas. No se leen Embarques Historicos, Importaciones2 ni Despachos, que no se usan.
4. **Caché global de 10 minutos sobre datos ya normalizados.** Si Google falla, se muestra la última carga válida con un aviso.
5. **Los tiempos se recalculan desde las fechas.** Las columnas calculadas de la planilla tienen ±46.000 días y TT = 0 cuando falta una fecha. Cada métrica tiene un rango válido; lo que queda afuera se descarta y se informa.
6. **Mediana + P25–P75 + n** en todos los tiempos. Los promedios solo se usan para precios.
7. **SLA definido en un solo lugar.** Monoproveedor 7 d. Consolidado según el target por puerto de Validaciones, con 25 d por defecto. Todo se configura en `config/settings.py`.
8. **Encabezados y valores por alias.** Si alguien corrige un typo en la planilla, el tablero no se rompe. Las 21 variantes de "Bidcom SRL" quedan como una sola.
9. **Filtros globales dependientes** con una única `apply_filters()`. La exportación descarga exactamente lo filtrado.
10. **Sin decoración de color.** El verde, el ámbar y el rojo solo indican cumplimiento, y siempre van con texto. Las series usan una paleta azul validada para daltonismo.

## Qué pasó con cada pestaña actual

| Antes | Ahora |
|---|---|
| ORIGEN | **Pipeline de origen**: meses en orden cronológico, estado de instrucción sin huecos, tipo de negocio corregido |
| MERCADERÍA EN PROCESO | **Embarques en curso** + **Aéreos** |
| PERFORMANCE AGENTES/ANALISTAS | **Agentes y analistas**: medianas, % SLA, desvío de ETD, % flete certificado con n visible |
| FLETES, GASTOS Y CERTIFICACIONES | **Fletes y cotizaciones**: lee la planilla de cotizaciones, solapa "Cotizaciones Maritimos Negociado" |
| PROYECCIÓN SEMANAL ETD | Integrada en **Pipeline de origen** (semana a semana) |
| INDICADORES | **Lead times y SLA** (marítimo) + **Aéreos** (tramos) |
| HISTÓRICO | **Histórico**, con comparación interanual además de la mensual |
| ASK COMEX | **Buscar SO / embarque**, reescrito. El chat IA se eliminó, según lo pedido |
| Barra "Panorama de mercado" | Eliminada: nunca mostró datos |
| — | Nuevo: **Resumen ejecutivo** con alertas de qué requiere atención |
| — | Nuevo: **Calidad de datos** |

## Mejoras realizadas

**Datos**
- Parser de fechas tolerante: d/m/aaaa, dd/mm/aa, doble barra, ISO, formato JS "Wed Apr 29 … 2026", número de serie. Los textos como "Pendiente" o "SI" quedan vacíos y se cuentan en Calidad de datos.
- Parser de números en formato argentino: "USD30.400,00", "0,10", "11,11 %", "(500)".
- Los errores de fórmula (#N/A, #REF!, #¡VALOR!…) se tratan como vacíos.
- Se excluyen filas de relleno (FCL 2759–2770, "AIR PROYECCION") y duplicados (AIR 199, FCL 2206).
- Estado de instrucción de SO: las 2.467 SO quedan clasificadas (742 instruidas y 1.725 pendientes). La versión anterior mostraba 716 instruidas: las 26 que faltaban son SO instruidas cuya fecha no se reconocía por el formato.
- Aéreos: el tramo WH→ETD de 156 d y el total de 172 d de septiembre eran fechas mal cargadas. Ahora ese mes da 30 d.

**Funcionalidad**
- Filtros globales dependientes: Empresa → Destino → Modo → Puerto → Forwarder → Estructura → Responsable.
- Período: presets más rango personalizado. Botón **Limpiar filtros**.
- Botón **Actualizar datos** y fecha de última actualización, tanto de la consulta como de la última edición de la planilla.
- Tablas con búsqueda, orden, semáforo y exportación a **Excel y CSV** (el CSV usa ";" y coma decimal para Excel en español).
- "Datos disponibles: X de Y" debajo de cada bloque de KPIs. Con menos de 5 datos el KPI muestra "—".
- Errores aislados por sección con mensajes amables y registro en el log.
- Buscador: tolera "38529", "SO-38529", "so38529"; "2679" no encuentra "26790"; cruza SO ↔ embarque.

**Performance** (medido con el export real de la planilla)
- Primera carga: ~3,5 s procesando 5 solapas y 23.000 filas (con Google se suma la latencia de la API).
- Cambiar un filtro o de página: menos de 1 s, sin consultar Google.

## Checklist de pruebas

`python -m pytest -q` → **90 tests OK**, sobre datos sintéticos y sobre el export real de la planilla.

| Área | Prueba | Resultado |
|---|---|---|
| Conexión | Lectura por columnas en 1 batch, render sin formato, 2 llamadas por planilla (API simulada) | ✅ |
| Conexión | Planilla caída sin datos previos → mensaje amable, sin traceback | ✅ |
| Conexión | Planilla caída con datos previos → últimos datos + aviso | ✅ |
| Conexión | Planilla de cotizaciones caída → el resto del tablero funciona | ✅ |
| Carga | Fechas (8 formatos), números (12 formatos), flags, textos basura | ✅ |
| Carga | Normalización de categorías, alias y escritura canónica | ✅ |
| Carga | Duplicados y filas de relleno excluidos | ✅ |
| Columnas faltantes | Columna obligatoria faltante → dataset deshabilitado con mensaje "Faltan columnas obligatorias…: ETD" | ✅ |
| Columnas faltantes | Columna opcional faltante → sigue funcionando | ✅ |
| Columnas faltantes | Solapa faltante → mensaje claro | ✅ |
| Columnas faltantes | Encabezado con mayúsculas o espacios distintos → se reconoce | ✅ |
| Datos nulos | Fechas 1900, ETD #N/A, tiempos fuera de rango → descartados y contados | ✅ |
| Filtros | `apply_filters` con período y selecciones; filtro no aplicable se ignora y se informa | ✅ |
| Filtros | Cascada dependiente, incluidos datasets sin el campo | ✅ |
| Filtros | Limpiar filtros | ✅ |
| Filtros | Período que deja todo vacío → las 10 páginas renderizan sin error | ✅ |
| KPIs | Mediana, P25, P75, n, muestra chica, semáforo, cumplimiento | ✅ |
| Gráficos | Las 10 páginas renderizan sin excepciones (AppTest y navegador real) | ✅ |
| Tablas / descarga | Búsqueda; Excel y CSV con las filas visibles | ✅ |
| Caché | Cambiar filtros 4 veces → 0 consultas nuevas; "Actualizar datos" → nueva consulta | ✅ |
| Buscador | Coincidencia tolerante y cruce SO ↔ embarque | ✅ |
| Visual | Revisión en navegador de las 10 páginas a 1440 px | ✅ |

**No probado en vivo:** la descarga real desde Google, porque este entorno no tiene salida a docs.google.com. Los dos conectores se probaron con respuestas simuladas, y todo el procesamiento se probó con el contenido real de ambas planillas, en formato Excel y en formato CSV argentino.

## Pendientes a confirmar

1. **Criterio de alertas del Resumen**: ETD en 7 días sin confirmar, zarpado hace más de 3 días sin Draft BL o PL final, consolidación proyectada fuera de SLA, instruido sin ETD. Se ajusta en `views/resumen.py → alerts()`.
2. **Privacidad**: el repositorio es público y las planillas se leen por enlace público, igual que en la versión anterior. Se recomienda:
   - hacer el repositorio privado;
   - borrar `cargas.csv`;
   - pasar al Modo B (cuenta de servicio) para quitar el acceso público de las planillas.

Confirmado: la app anterior leía la solapa "Cotizaciones Maritimos Negociado" (gid 0), la misma que usa esta versión.
