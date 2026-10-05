# Etapa 2 — Propuesta de arquitectura

## Comparación de alternativas

| Criterio | A. Streamlit bien estructurado | B. Streamlit + componentes HTML/JS | C. Front HTML/JS + backend Python (FastAPI) | D. Looker Studio conectado a la planilla |
|---|---|---|---|---|
| Ventajas | Un solo lenguaje, deploy actual, caché nativo, tablas con búsqueda, orden y descarga incluidos | Control visual total de algunas piezas | Máximo control de UX y rendimiento en el cliente | Cero código, conexión nativa a Sheets |
| Desventajas | Menos libertad visual; modelo de rerun | Dos lenguajes; los componentes custom se rompen con cada versión de Streamlit; el estado cruza iframes | Dos proyectos (API + front), autenticación, CORS y hosting propios | La lógica de limpieza (fechas mixtas, alias, recálculo de tiempos) es casi imposible de mantener; los filtros dependientes y las medianas por grupo son limitados |
| Complejidad | Baja | Media-alta | Alta | Baja al inicio, alta al corregir datos sucios |
| Mantenimiento | Alto: Python modular | Medio | Bajo: requiere perfil full-stack | Bajo en lo visual, pésimo en lógica |
| Velocidad | Buena, con caché global y multipágina | Buena | Muy buena | Buena |
| Estabilidad | Alta | Media | Alta, si hay equipo que la sostenga | Alta |
| Actualización de datos | Caché con TTL + botón | Igual que A | Hay que programarla | Automática |
| Deploy | Streamlit Community Cloud, gratis, desde GitHub | Igual que A | Servidor propio o PaaS | Inmediato |
| Google Sheets | gspread + service account | Igual que A | Igual que A | Nativa |

**Elección: Opción A.** Los problemas actuales no vienen de Streamlit. Vienen de la estructura: 8 tabs que se ejecutan siempre, caché mal ubicado, fechas y números sin normalizar, filtros por pestaña y cálculos tomados de columnas rotas. Todo eso se resuelve dentro de Streamlit. El HTML queda limitado a un CSS de ~200 líneas y a tarjetas KPI simples, sin componentes JS.

## Estructura del proyecto

```
streamlit_app.py                      Punto de entrada: config, header, sidebar, navegación
config/settings.py          Parámetros: ID de planilla, TTL, SLA, rangos válidos, paleta
config/schema.py            Esquema por solapa: nombre canónico ← alias de encabezado, tipo, obligatorio
config/mappings.py          Alias de valores (empresas, puertos, forwarders, tipo de carga…)
services/google_sheets.py   Lectura de la fuente (gspread / xlsx local), sin lógica de negocio
services/data_loader.py     Orquesta: leer → normalizar → derivar → validar. Caché
utils/data_cleaning.py      Parsers de fecha, número, texto, flags; normalización de categorías
utils/calculations.py       Lead times, percentiles, SLA, agregaciones
utils/filters.py            FilterState, apply_filters(), opciones dependientes
utils/formatting.py         Números es-AR, USD, días, %, fechas
utils/logger.py             Logging centralizado
components/layout.py        Header, secciones, mensajes, sección segura
components/kpi_cards.py     Tarjetas KPI
components/charts.py        Plantilla Plotly y gráficos reutilizables
components/tables.py        Tabla con búsqueda y exportación CSV/Excel
components/filters.py       Sidebar de filtros (dependientes + limpiar)
views/*.py                  Una página por tema
assets/styles.css
.streamlit/config.toml, secrets.toml.example
tests/                      pytest + AppTest de Streamlit
```

`views/` reemplaza a `pages/`. Si se usa `pages/`, Streamlit activa la navegación multipágina automática, y eso choca con `st.navigation`.

## Flujo de datos

```
Google Sheets (5 solapas, 1 llamada batch)
   ↓  services/google_sheets.py  → dict[str, DataFrame de texto]
   ↓  services/data_loader.py
        · resolver encabezados por alias (config/schema.py)
        · parsear tipos (fecha / número / flag / categoría)
        · normalizar categorías (config/mappings.py)
        · excluir filas vacías y de relleno, deduplicar
        · recalcular lead times desde fechas
        · reporte de calidad y de columnas faltantes
   ↓  @st.cache_data(ttl=600)  ← UNA sola vez para todos los usuarios
   ↓  apply_filters(df, filtros)   ← en memoria, milisegundos
   ↓  KPIs · gráficos · tablas · exportación
```

- **Caché**: `get_data()` se cachea globalmente con TTL de 10 minutos, con los datos ya normalizados. Los filtros nunca vuelven a consultar Google.
- **Botón "Actualizar datos"**: ejecuta `get_data.clear()` y hace un rerun.
- **Última versión válida**: si Google falla, se muestran los últimos datos cargados con un aviso, en lugar de romper la app.
- **Última actualización**: se muestra la hora de consulta a la fuente y, si la API lo permite, la hora de última edición de la planilla.

## Lógica de filtros

- Hay un único estado de filtros en `st.session_state`, definido en `utils/filters.py`, y es global a todas las páginas.
- **Dependientes**: Empresa → Destino → Modo → Puerto → Forwarder, más Estructura y Responsable. Las opciones de cada filtro salen de los datos ya filtrados por los filtros anteriores. Si una selección deja de ser compatible, se descarta sola.
- **Período**: rango de fechas sobre la fecha de referencia de cada dataset (ETD).
- **`apply_filters(df, filters)`**: es la única función que filtra. Si un dataset no tiene la columna de un filtro, ese filtro se ignora para ese dataset y la página lo avisa.
- **Limpiar filtros**: vuelve todos los filtros al estado por defecto.
- **Exportación**: se exporta exactamente el DataFrame ya filtrado que se ve en pantalla.
