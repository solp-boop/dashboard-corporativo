# Dashboard Ejecutivo · Comercio Exterior / Logística Internacional

Tablero en Streamlit que lee directamente las planillas de Google Sheets
**Tablero LI** y **Cotización fletes internacionales**. Normaliza los datos,
recalcula los lead times desde las fechas y muestra KPIs, gráficos y tablas
con filtros globales dependientes.

Los datos se actualizan solos cada 10 minutos. El botón **Actualizar datos**
fuerza una lectura inmediata.

---

## 1. Estructura del proyecto

```
streamlit_app.py              Punto de entrada: navegación, sidebar, cabecera
config/
  settings.py                 IDs de planillas, caché, SLA, rangos válidos, paleta
  schema.py                   Columnas de cada solapa (alias de encabezados, tipo, obligatoria)
  mappings.py                 Alias de valores (empresas, puertos, forwarders, tipos de carga…)
services/
  google_sheets.py            Conexión (gspread) y lector de .xlsx local, sin lógica de negocio
  data_loader.py              Leer → tipar → normalizar → derivar → calidad. Caché
utils/
  data_cleaning.py            Parsers tolerantes de fecha, número, flag y texto
  calculations.py             Mediana/P25/P75, SLA, semáforo, cumplimiento
  filters.py                  FilterState + apply_filters() + opciones dependientes
  formatting.py               Formato es-AR: 1.234,5 · USD 18,2 M · 24 d · 52 %
  logger.py                   Logging centralizado
components/
  layout.py                   Cabecera, secciones, avisos, guard() para errores
  kpi_cards.py                Tarjetas KPI
  charts.py                   Estilo Plotly común
  tables.py                   Tabla con búsqueda, semáforo y exportación Excel/CSV
  filters.py                  Sidebar de filtros (dependientes + limpiar)
views/                        Una página por tema
  resumen.py                  ¿Cómo estamos? ¿Cumplimos SLA? ¿Qué requiere atención?
  pipeline.py                 Mercadería en origen (Planif cargas)
  embarques.py                Embarques en curso (Reservas)
  aereos.py                   Aéreos y courier
  lead_times.py               Lead times y SLA
  agentes.py                  Forwarders y analistas
  fletes.py                   Cotizaciones de fletes
  historico.py                Histórico mensual e interanual
  buscar.py                   Buscador por SO / embarque
  calidad.py                  Calidad de datos
assets/styles.css             Estilos
.streamlit/config.toml        Tema y configuración
.streamlit/secrets.toml.example
tests/                        pytest (datos, lógica, conector, app completa)
docs/                         Diagnóstico, auditoría de la planilla, arquitectura
```

> Las páginas están en `views/` y no en `pages/`. Con una carpeta `pages/`,
> Streamlit arma su navegación automática y choca con `st.navigation`.

## 2. Instalación y ejecución local

Requisitos: Python 3.10 o superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    ·    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Sin configurar nada, lee las planillas por el enlace público (ver sección 4).
Para trabajar sin conexión se puede usar un export .xlsx de las planillas
(Archivo → Descargar → Microsoft Excel). En `.streamlit/secrets.toml`:

```toml
[local_files]
tablero = "data/Tablero LI.xlsx"
cotizaciones = "data/Cotizacion fletes internacionales.xlsx"
```

## 3. Dependencias

| Paquete | Para qué |
|---|---|
| streamlit | Aplicación |
| pandas / numpy | Datos |
| plotly | Gráficos |
| gspread / google-auth | Lectura de Google Sheets |
| openpyxl | Exportación a Excel y lectura de .xlsx local |

## 4. Conexión a Google Sheets

Hay dos modos. El tablero elige solo según lo que haya en *Secrets*.

### Modo A — enlace público (por defecto, sin configurar nada)

Es el mismo acceso que usaba la app anterior. Lee cada solapa con su
exportación CSV (`…/export?format=csv&gid=…`). Requiere que las dos planillas
estén compartidas como **"Cualquier persona con el enlace puede ver"**.

Los `gid` de cada solapa están en `config/settings.py → SHEET_GIDS`. Si alguien
borra y vuelve a crear una solapa, su gid cambia: abrí la solapa, copiá el
número después de `gid=` en la URL y actualizalo ahí.

⚠️ En este modo, cualquiera que tenga el link de la planilla puede ver los datos.

### Modo B — cuenta de servicio (recomendado para datos sensibles)

Permite que las planillas **no** sean públicas.

1. En [Google Cloud Console](https://console.cloud.google.com/), creá un proyecto. Habilitá
   **Google Sheets API** y **Google Drive API**.
2. Creá una **cuenta de servicio** y generale una clave **JSON**.
3. Compartí **las dos planillas** con el `client_email` de la cuenta, con permiso de **Lector**.
4. Copiá los campos del JSON en `[gcp_service_account]` de los *Secrets* (ver `.streamlit/secrets.toml.example`).
5. Ya podés quitar el acceso público de las planillas.

Con la cuenta de servicio, el tablero lee solo las columnas que usa, con dos
llamadas a la API por planilla. Además muestra la hora de la última edición de
la planilla.

En los dos modos la lectura es **solo lectura**: el dashboard nunca modifica las planillas.

## 5. Secrets

| Sección | Obligatoria | Contenido |
|---|---|---|
| `[gcp_service_account]` | No (Modo B) | JSON de la cuenta de servicio |
| `[sheets]` | No | `tablero` y `cotizaciones`: IDs de planilla, si cambian |
| `[local_files]` | No | Rutas a .xlsx para desarrollo |

**Nunca** subas `.streamlit/secrets.toml` al repositorio. Ya está en `.gitignore`.

## 6. Deploy en Streamlit Community Cloud

1. Subí el proyecto a GitHub, sin `secrets.toml`.
2. En [share.streamlit.io](https://share.streamlit.io): **Create app** → repositorio, rama y `streamlit_app.py` como archivo principal.
   En **Advanced settings** elegí Python 3.11 o superior.
3. *(Solo Modo B)* En **Secrets**, pegá la sección `[gcp_service_account]`.
4. **Deploy.**

Para actualizar la app existente, alcanza con subir los archivos a la rama `main`
del mismo repositorio: Streamlit Cloud redeploya solo y mantiene la URL. El
archivo principal sigue siendo `streamlit_app.py`.

Los errores técnicos quedan en **Manage app → Logs**. El usuario nunca ve un traceback.

### App dormida ("Your app is in the oven")

Streamlit Community Cloud duerme las apps que no reciben visitas. Para evitarlo,
el workflow `.github/workflows/keep-awake.yml` abre el dashboard cada 6 horas y,
si lo encuentra dormido, lo despierta. Los links se configuran en `APP_URLS`
dentro de ese archivo.

GitHub solo ejecuta los workflows programados desde la rama principal (`main`).
Para probarlo a mano: pestaña *Actions* → "Mantener el dashboard despierto" → *Run workflow*.

## 7. Cómo funciona

```
Google Sheets → lectura (1 batch por planilla) → normalización → caché (10 min, compartida)
             → apply_filters() → KPIs / gráficos / tablas / exportación
```

- **Caché:** `st.cache_resource` con TTL, sobre los datos ya normalizados. Filtrar
  nunca vuelve a consultar Google. Si Google falla, se muestran los últimos datos
  válidos con un aviso.
- **Filtros:** una sola función, `utils/filters.apply_filters()`. La cascada es
  Empresa → Destino → Modo → Puerto → Forwarder → Estructura → Responsable.
  Las opciones de cada filtro dependen de los anteriores. Si un dataset no tiene
  un campo (por ejemplo, Planif cargas no tiene Empresa), el filtro se ignora
  ahí y la página lo aclara.
- **Tiempos:** se **recalculan desde las fechas**. No se usan las columnas
  calculadas de la planilla porque dan ±46.000 días cuando falta una fecha.
  Los valores fuera de rango (`DURATION_RANGES`) se descartan y se informan en
  *Calidad de datos*.
- **Mediana** como indicador principal, con P25–P75 y n en cada KPI.
  Con menos de `MIN_SAMPLE` datos el KPI muestra "—", y se indica
  "Datos disponibles: X de Y".
- **SLA de consolidación:** 7 d para monoproveedor; para consolidado, el target
  por puerto de Validaciones (por defecto 25 d). Semáforo: verde ≤ SLA,
  amarillo hasta +20 %, rojo por encima.

## 8. Mantenimiento habitual

| Cambio | Dónde |
|---|---|
| Alguien renombró una columna | Agregá el nombre nuevo a los alias en `config/schema.py` |
| Aparece una variante de escritura nueva (puerto, forwarder…) | `config/mappings.py` → `VALUE_ALIASES` |
| Cambia un SLA o la tolerancia del semáforo | `config/settings.py` |
| Cambia el nombre de una solapa o planilla | `config/settings.py` → `DATASET_SOURCES` / `SPREADSHEETS` |
| Falta una columna obligatoria | La página muestra cuál falta, y *Calidad de datos* también |

Los cambios de datos (filas nuevas, valores nuevos) **no requieren tocar código**.

## 9. Cómo agregar una métrica nueva

1. Si necesita una columna nueva, agregala al esquema en `config/schema.py`
   (`C("nombre", "Encabezado en la planilla", kind="date|number|category|text")`).
2. Si es un tiempo, agregala a `MARITIME_DURATIONS` o `AIR_DURATIONS` en
   `services/data_loader.py` y definí su rango válido en `settings.DURATION_RANGES`.
3. En la vista, calculala sobre el DataFrame **ya filtrado** y mostrala:

```python
from components.kpi_cards import KPI, kpi_row
from utils import calculations as calc, formatting as fmt

s = calc.describe(df["dias_nueva_metrica"])
kpi_row([KPI("Nueva métrica (mediana)", fmt.fmt_int(s.median) if s.enough else "—", unit="d")])
```

Envolvé cada bloque en `with guard("Nombre"):` para que un error no rompa el
resto de la página.

## 10. Cómo agregar una página

1. Creá `views/mi_pagina.py` con una función `render()`:

```python
from components.layout import guard, require, section
from views._common import ctx, filtered

def render():
    bundle, filters = ctx()
    if require(bundle, "reservas") is None:
        return
    df = filtered(bundle, "reservas", filters)
    section("Mi sección")
    with guard("Mi sección"):
        ...
```

2. Registrala en `PAGES` en `streamlit_app.py`:

```python
st.Page(mi_pagina.render, title="Mi página", icon=":material/star:", url_path="mi-pagina")
```

## 11. Tests

```bash
pip install pytest
python -m pytest -q                 # datos sintéticos
# contra un export real de la planilla:
DASHBOARD_TEST_XLSX="data/Tablero LI.xlsx" DASHBOARD_TEST_COTIZACIONES_XLSX="data/Cotizacion.xlsx" python -m pytest -q
```

Cubren parsers, normalización, columnas y solapas faltantes, planilla caída,
filtros dependientes, limpiar filtros, caché (filtrar no consulta Google),
buscador, exportación y el render de las 10 páginas.
