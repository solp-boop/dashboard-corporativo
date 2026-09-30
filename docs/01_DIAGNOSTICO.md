# Etapa 1 — Diagnóstico del dashboard actual y de la planilla

Fecha de relevamiento: 30/09/2026.

## Alcance y limitaciones

- **Planilla "Tablero LI"**: se leyeron las 8 solapas completas, en modo solo lectura. No se modificó nada.
- **Dashboard publicado**: se recorrieron las 8 pestañas de la app en producción y se relevaron todas las métricas visibles.
- **Código fuente**: repositorio `solp-boop/dashboard-corporativo`, leído completo (ver 2.2).

---

## 1. Inventario funcional del dashboard actual

No se elimina nada sin identificar antes qué hace. La columna *Destino* indica qué pasa con cada elemento en la versión nueva.

| Pestaña actual | Qué muestra | Fuente probable | Qué decisión permite | Destino |
|---|---|---|---|---|
| **ORIGEN** | SO totales, M3, proveedores, FOB. Instruida vs. pendiente. Estructura mono/consolidado. "Tipo de negocio". Distribución por destino. M3 por puerto. Proyección mensual ETD/ETA en M3 y contenedores. Proyección por estructura de carga. | Planif cargas | Cuánto volumen viene y cuándo sale, para negociar espacio y tarifas | **Se mantiene** → página *Pipeline de origen* (corregida) |
| **MERCADERÍA EN PROCESO** | Aéreos activos por estadio y tipo de negocio. Reservas marítimas activas. Estado del ETD OK. Pendientes por agente. Mono/cons. In advance/spot. Consolidación mediana vs SLA. ETD de la semana. | Reservas + SEGUIMIENTO AEREOS | Qué hay que empujar esta semana y con qué agente | **Se mantiene** → *Embarques en curso* + *Aéreos* |
| **PERFORMANCE DE AGENTES Y ANALISTAS** | Por mes ETD: embarques, SO, proveedores, días promedio de consolidación por analista. Por forwarder: días instrucción→confirmación, ETD→BL, % de certificación de flete. | Reservas Historicas | Quién está demorando | **Se mantiene** → *Agentes y analistas*, con medianas |
| **FLETES, GASTOS Y CERTIFICACIONES** | Cotizaciones vigentes por FFWW, gastos locales, promedio de mercado, mejor oferta y target −15%. | **Otra planilla** (no está en Tablero LI) | Negociación de tarifas | **Pendiente**: requiere el ID de la planilla de cotizaciones (ver §6) |
| **PROYECCIÓN SEMANAL ETD** | M3, contenedores y SO por semana de un mes elegido | Planif cargas | Base para negociar tarifas | **Se integra** en *Pipeline de origen* (vista semanal) |
| **INDICADORES** | Por mes ETD: embarques, días promedio y % mono/cons. Cumplimiento SLA mono y cons por mes. Tramos aéreos por mes. | Reservas Historicas + Aéreos | ¿Cumplimos SLA? | **Se mantiene** → *Lead times y SLA* + *Aéreos* |
| **HISTÓRICO** | Embarcado 2026 por mes con Δ% vs mes anterior. Aéreo 2026. Tiempos por puerto vs targets de Validaciones. | Reservas Historicas + Aéreos + Validaciones | Tendencia y cuellos de botella por puerto | **Se mantiene** → *Histórico* + *Lead times y SLA* |
| **ASK COMEX** | Chat de IA "Capitán Comex" y buscador por SO o embarque | IA externa + planillas | Consulta rápida | Buscador: **se mantiene** (página *Buscar*). Chat IA: **pendiente de decisión** |
| Barra "PANORAMA DE MERCADO" | Mensaje fijo "Actualizando información…" | Externa | Ninguna: no muestra datos | **Se elimina** (no funciona) |

---

## 2. Errores encontrados en el dashboard actual

### 2.1 Errores de cálculo o de datos visibles

1. **Meses ordenados como texto.** Los ejes de "Proyección mensual ETD/ETA" muestran `01/2027, 08/2027, 09/2026, 10/2026…`. El 2027 aparece antes que el 2026 porque ordena el texto y no la fecha.
2. **Totales que no cierran.** En ORIGEN hay 2.467 SO, pero instruidas (716) + pendientes (1.725) suman 2.441. Quedan 26 SO sin clasificar que no se informan. Al recalcular, son SO **instruidas** cuya fecha de instrucción no se reconocía por el formato (742 instruidas reales).
3. **"Tipo de negocio" mal clasificado.** Las 716 SO instruidas aparecen como GADNIC, con 0 muestras, 0 marcas y 0 repuestos. Planif cargas tiene 151 SO de DJI y 65 de muestras courier, así que la regla de clasificación no está leyendo bien la columna.
4. **Puertos duplicados por escritura.** "Zhonshan" (2 M3) y "Zhongshan" (45 M3) aparecen como puertos distintos. Hong Kong / HONG KONG y Shekou / SHEKOU tienen el mismo problema en el histórico.
5. **Outliers que rompen promedios.** En "Indicadores aéreos" de septiembre 2026, el tramo WH→ETD da **156 días** y el total **172 días**, cuando el resto de los meses da ~30. Son fechas mal cargadas que el promedio no filtra.
6. **Se usan promedios para tiempos.** INDICADORES e HISTÓRICO muestran "DIAS AVG". Con esta distribución de datos la mediana es más representativa.
7. **SLA definido de dos formas.** En MERCADERÍA EN PROCESO el SLA de consolidación está fijo en código (mono 7d, cons 25d). En HISTÓRICO se usan los targets por puerto de Validaciones. Por eso un mismo embarque puede aparecer "en SLA" en una pestaña y "fuera de SLA" en otra.
8. **Puertos sin target.** Singapur y Xingang muestran "—d": no están en la tabla de Validaciones y no hay valor por defecto.
9. **Proyección de meses lejanos.** Hay ETD en 08/2027 y ETA en 09/2027. Son fechas mal cargadas (año equivocado) que se muestran como proyección real.
10. **Barra "Panorama de mercado".** Siempre dice "Actualizando información · Próxima actualización disponible pronto". No trae datos.
11. **% certificación "SD".** En Performance de agentes el KPI principal dice "Sin datos suficientes", pero la tarjeta se muestra igual, sin decir cuántos datos hay.

### 2.2 Confirmado en el código (`streamlit_app.py`, 3.145 líneas)

- **El caché nunca funciona.** Las URLs se arman con `&nocache={time.time()}`. Como `st.cache_data` guarda por parámetro y la URL cambia en cada ejecución, **cada clic vuelve a descargar la planilla**. Eso incluye Planif cargas completa (5.774 filas × 112 columnas). Es la causa principal de "está pensando".
- **Hay 16 descargas separadas** (`pd.read_csv`) de 8 solapas distintas, repartidas por todo el código. Algunas bajan varias veces la misma solapa (por ejemplo, gid 32771816 se baja 4 veces). Además se descargan Embarques Historicos (30.000 filas), Importaciones2 y Despachos.
- **Columnas leídas por posición.** Hay 31 lugares con `df.iloc[:, 23]` o similar. Si alguien agrega o mueve una columna en la planilla, los indicadores leen otra columna sin avisar.
- **Tracebacks en pantalla.** Se muestran con `st.error(f"... {e}")` y `st.code(traceback.format_exc())`: esos son "los códigos" que aparecen.
- **Conexión sin credenciales.** Usa la exportación CSV pública de Google, así que las planillas tienen que ser accesibles para cualquiera con el enlace.
- **El repositorio es público** e incluye `cargas.csv`, con 2.300 filas de datos de SO, proveedores y montos. Cualquiera puede verlo en GitHub.
- `requirements.txt` incluye `google-generativeai` (para el chat IA) y `st-gsheets-connection`, que no se usa.
- En la raíz hay scripts de depuración (`check_*.py`, `debug_*.py`, `find_*.py`) y un `pages/Status_Cargas.py` que duplica la lógica de Reservas.

### 2.3 Arquitectura (observado en el comportamiento)

- **Una sola página con 8 `st.tabs`.** Streamlit ejecuta el código de **todas** las pestañas en cada interacción, aunque solo se vea una. Cualquier filtro o selector re-ejecuta los 8 tableros. Esa es la principal causa de lentitud.
- **Filtros locales por pestaña** ("Seleccionar mes ETD", "Seleccionar FFWW", "Mes / Tipo CNT"). No hay filtros globales, así que los KPIs de una pestaña no se pueden cruzar con otra y aparecen números que parecen contradictorios.
- **Caché**: al abrir una sesión nueva aparece "Running load_main_data(...)", con una carga de ~10 s. Indica un `st.cache_data` con TTL corto o por sesión. Además lee solapas grandes que no se usan (Embarques Historicos, 30 mil filas; Importaciones2, 19 mil filas con duplicados).
- **HTML armado a mano** para cada tarjeta, con estilos en línea. El texto es muy chico (etiquetas de ~7 px en pantalla de notebook) y el contraste es bajo sobre fondo oscuro.
- **Columnas calculadas leídas desde la planilla** (Tiempo Comex, Tiempo Agente, TT). Cuando falta una fecha, la planilla devuelve ±46.000 días o TT = 0, y eso entra en los KPIs.

### 2.4 UX

- 8 pestañas horizontales en mayúsculas y letra chica. No hay jerarquía clara ni una página de resumen.
- Fondo negro con acentos neón, brillos y bordes de colores. Verde, naranja y celeste se usan como decoración, así que el semáforo pierde significado.
- No hay filtros globales, ni botón "Limpiar filtros", ni fecha de última actualización.
- No se pueden descargar los datos filtrados.
- No se informa cuántos registros respaldan cada KPI.

---

## 3. Problemas de datos en la planilla

(El detalle columna por columna se entregó por separado: no se sube al repositorio porque es público.)

| Problema | Ejemplo | Impacto | Tratamiento en la versión nueva |
|---|---|---|---|
| Variantes de escritura | "Bidcom srl" / "BIdcom SRL"; "DELFIN GROUP" / "Delfin Group"; "Courrier" / "Courier"; "40ST" | Opciones duplicadas en filtros y totales partidos | Normalización con diccionario de alias en `config/mappings.py` y unificación automática de mayúsculas |
| Fechas con texto | "Pendiente", "SI", "No aplica", "*", "#N/A" en columnas de fecha | La conversión falla y la columna entera queda como texto | Parser tolerante: lo que no es fecha queda vacío y se cuenta en *Calidad de datos* |
| Fechas basura | años 1900, 1969 y 0202; "23/11//2024"; "Wed Apr 29 … GMT-03:00 2026" | Ejes que arrancan en 1900; lead times de ±46.000 días | Rango válido 2018 → hoy+18 meses; formato JS reconocido; doble barra corregida |
| Números en formato argentino como texto | "USD30.400,00", "0,10", "11,11%" (toda la solapa Planif cargas) | Sumas en 0 o valores multiplicados por 100 | Parser que detecta coma decimal, punto de miles, USD y $ |
| Errores de fórmula | #N/A, #REF!, #VALUE!, #DIV/0!, "#¡VALOR!" | Aparecen como una categoría más | Se tratan como vacío |
| Calculados rotos | TT = 0 sin ETA; consolidación 46.000 d | Distorsionan medianas y promedios | **Se recalcula todo desde las fechas**, con rangos válidos por métrica |
| Filas de relleno | FCL 2759–2770 sin datos; "AIR PROYECCION" | Inflan los conteos | Se excluyen las filas sin datos de negocio |
| Duplicados | AIR 199 y FCL 2206 en Históricas | Doble conteo | Se deduplica por Embarque y se informa |
| Encabezados inestables | "Cotizacion agente? " con espacio al final; "Parcipacion"; "reserverva" | Si alguien corrige el typo en la planilla, el código se rompe | Se busca cada columna por una lista de alias, sin importar mayúsculas, acentos ni espacios |
| Solapas no usadas y pesadas | Embarques Historicos (30 mil filas), Importaciones2 | Lentitud | No se leen |

---

## 4. Performance

| Causa | Efecto | Solución |
|---|---|---|
| 8 tabs se ejecutan siempre | Cada clic re-renderiza todo | Navegación multipágina (`st.navigation`): solo corre la página visible |
| Se leen solapas pesadas que no se usan | Carga de ~10 s | Solo se leen 5 solapas, en **una sola llamada** a la API (`values_batch_get`) |
| Caché corto o por sesión | Cada usuario nuevo espera la carga | `st.cache_data` global con TTL de 10 min, sobre los datos **ya normalizados** |
| Normalización en cada rerun | CPU en cada filtro | La normalización ocurre una sola vez, dentro de la función cacheada |
| HTML por tarjeta | DOM pesado | CSS en un solo archivo y componentes reutilizables |

---

## 5. Lo que está bien y se conserva

- Los conceptos de negocio: mono vs consolidado, booked in advance vs spot, ETD OK FFWW, targets por puerto de Validaciones, tramos aéreos (Packeo→WH→ETD→ETA→Caldas), Δ vs mes anterior, documentación (Draft BL, PL final, fotos).
- La idea de "ETD de esta semana".
- El buscador por SO o embarque.

## 6. Decisiones que necesito de tu parte

1. **Fletes y cotizaciones**: los datos no están en Tablero LI. Necesito el link de la planilla de cotizaciones para migrar la pestaña.
2. **Chat IA "Capitán Comex"**: ¿se mantiene? Depende de una API key y de un proveedor externo. Queda fuera del núcleo del tablero y se puede sumar como página opcional.
3. **SLA de consolidación**: la versión nueva usa por defecto el target por puerto de Validaciones, con 7 días para monoproveedor como en la versión actual. Se cambia en `config/settings.py`.
