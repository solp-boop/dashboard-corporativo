"""Parámetros generales del dashboard.

Todo lo que un analista podría querer ajustar sin tocar la lógica vive acá:
fuente de datos, caché, SLA, rangos válidos y paleta.
"""
from __future__ import annotations

import datetime as dt

# --------------------------------------------------------------------------
# Fuente de datos
# --------------------------------------------------------------------------
# Planillas fuente. Se pueden sobrescribir desde secrets:
#   [sheets]
#   tablero = "..."
#   cotizaciones = "..."
SPREADSHEETS: dict[str, str] = {
    "tablero": "1uDV3-CK5aeb-PI81uNc54t4L50HhscHe5xkp-pL9SyI",       # Tablero LI
    "cotizaciones": "1UJ1bDyDQdIQSSVQ6dyChVKbMX1d69G68ji_dpsOzfHg",  # Cotización fletes internacionales
}

# Dataset -> (planilla, solapa). La solapa se busca sin importar mayúsculas,
# acentos ni espacios. Solo se leen estas solapas (y solo las columnas que
# usa el dashboard), lo que hace la carga mucho más rápida.
DATASET_SOURCES: dict[str, tuple[str, str]] = {
    "reservas": ("tablero", "Reservas"),
    "historicas": ("tablero", "Reservas Historicas"),
    "aereos": ("tablero", "SEGUIMIENTO AEREOS"),
    "planif": ("tablero", "Planif cargas"),
    "validaciones": ("tablero", "Validaciones"),
    "emb_hist": ("tablero", "Embarques Historicos"),
    "cotizaciones": ("cotizaciones", "Cotizaciones Maritimos Negociado"),
    "cot_sin_negociar": ("cotizaciones", "Cotizaciones Maritimos SIN NEGOCIAR"),
}

# gid de cada solapa (el número "gid=" de la URL al abrir la solapa). Se usa
# en el modo sin credenciales (exportación CSV pública). Si alguien borra y
# vuelve a crear una solapa, su gid cambia: actualizarlo acá.
SHEET_GIDS: dict[str, dict[str, int]] = {
    "tablero": {
        "Planif cargas": 0,
        "Reservas": 276804813,
        "Reservas Historicas": 32771816,
        "SEGUIMIENTO AEREOS": 88538385,
        "Validaciones": 889641786,
        "Embarques Historicos": 50628730,
    },
    "cotizaciones": {
        "Cotizaciones Maritimos Negociado": 0,
        "Cotizaciones Maritimos SIN NEGOCIAR": 1339275364,
    },
}

# Fletes: el target es el promedio de mercado menos este porcentaje.
TARGET_DESCUENTO_FLETE = 0.15

# Caché de datos normalizados (segundos). El botón "Actualizar datos" lo limpia.
CACHE_TTL_SECONDS = 600

TIMEZONE = "America/Argentina/Buenos_Aires"

# --------------------------------------------------------------------------
# Limpieza
# --------------------------------------------------------------------------
# Valores que se interpretan como celda vacía (se comparan en minúsculas).
NULL_TOKENS = {
    "", "-", "--", "—", "n/a", "na", "n.a.", "nan", "nat", "none", "null",
    "sin dato", "sin datos", "s/d", "#n/a", "#ref!", "#value!", "#div/0!",
    "#name?", "#num!", "#null!", "#error!", "#¡valor!", "#¡ref!", "#¡div/0!",
    "#n/d", "*", "?",
}
# En columnas de fecha y número, cualquier texto que no se pueda convertir
# ("Pendiente", "SI", "No aplica"...) queda vacío y se cuenta en Calidad de datos.

# Fechas fuera de este rango se consideran errores de carga.
DATE_MIN = dt.date(2018, 1, 1)
DATE_MAX_DAYS_AHEAD = 548  # ~18 meses hacia adelante

# Rango válido (días) de cada lead time. Fuera de rango -> se descarta y se
# informa en Calidad de datos.
DURATION_RANGES: dict[str, tuple[int, int]] = {
    "dias_comex": (-120, 180),          # Instrucción - Packeo mín.
    "dias_agente": (0, 180),            # ETD - Instrucción
    "dias_consolidacion": (0, 240),     # ETD - Packeo mín.
    "dias_tt": (1, 120),                # ETA - ETD
    "dias_total": (1, 360),             # ETA - Packeo mín.
    "desvio_etd": (-90, 120),           # ETD - ETD estimada
    "dias_espera": (0, 240),            # Packeo máx. - Packeo mín.
    # Aéreos
    "dias_packeo_wh": (0, 120),
    "dias_wh_etd": (0, 90),
    "dias_etd_eta": (0, 45),
    "dias_eta_caldas": (0, 45),
    "dias_total_aereo": (0, 240),
    "tiempo_consolidacion_so": (1, 240),   # negativos y 0 = sin dato   # 0 = la planilla no lo calculó (sin dato)
}

# --------------------------------------------------------------------------
# SLA
# --------------------------------------------------------------------------
# Consolidación (ETD - Packeo mín.). Monoproveedor usa un SLA fijo según la fecha de ETD;
# consolidado usa el target por puerto de la solapa Validaciones.
# Vigencias del SLA monoproveedor (desde ETD, días): 15 hasta feb-2026, 10 de marzo a septiembre 2026,
# 12 desde octubre 2026.
SLA_MONO_VIGENCIAS = [("1900-01-01", 15), ("2026-03-01", 10), ("2026-10-01", 12)]
SLA_CONSOLIDACION_MONO = SLA_MONO_VIGENCIAS[-1][1]   # el vigente hoy (para textos)
SLA_CONSOLIDACION_DEFAULT = 25   # si el puerto no tiene target
# Embarques en curso (Reservas): tope fijo 25 d consolidado / 15 d monoproveedor, sin SLA por puerto.
SLA_EN_CURSO_FIJO = True
SLA_TT_DEFAULT = 50
SLA_TOTAL_DEFAULT = 75
# Tolerancia para "amarillo": hasta +20 % sobre el SLA.
SLA_WARNING_TOLERANCE = 0.20

# Referencia de consolidación para in advance / spot (sin SLA formal).
REF_CONSOLIDACION_BOOKING = 20

# --------------------------------------------------------------------------
# Validaciones de KPIs
# --------------------------------------------------------------------------
# Con menos registros válidos que esto, el KPI se muestra como "muestra chica".
MIN_SAMPLE = 5
# Si la cobertura (válidos / total) es menor, se muestra la advertencia.
MIN_COVERAGE = 0.6

# Días hacia adelante considerados "próximos" para alertas.
ALERT_HORIZON_DAYS = 7

# --------------------------------------------------------------------------
# Paleta (sobria; semáforo solo para cumplimiento)
# --------------------------------------------------------------------------
COLORS = {
    "navy": "#15294B",
    "blue": "#2A5CAA",
    "blue_light": "#8FB0DE",
    "slate": "#5B6675",
    "grey": "#A9B1BC",
    "grey_light": "#E7EAEE",
    "bg": "#F6F7F9",
    "white": "#FFFFFF",
    "text": "#1B2330",
    "green": "#2E8B57",
    "amber": "#D99A1E",
    "red": "#C0392B",
}
# Series categóricas, en orden fijo (validadas para daltonismo). Máximo 4 por
# gráfico; el resto se agrupa en "Otros" (gris neutro).
SERIES = ["#2456A6", "#6E9BDB", "#5E4AA0", "#B07A2A"]
SERIES_OTHER = "#A9B1BC"

# Flete certificado = lo que certificamos por fuera: flete certificado / flete pagado.
# Menos es mejor; por encima del máximo está mal.
KPI_CERTIFICACION_MAX = 0.60

# Recomendación de forwarder: un ETD se considera "en fecha" si el ETD real
# difiere de la ETD estimada en hasta estos días.
ETD_TOLERANCIA_DIAS = 3

# Proyección de contenedores para SO sin embarque asignado: m³ / este valor
# (mismo criterio que la versión anterior del tablero).
M3_POR_CONTENEDOR = 60

# Objetivo de cumplimiento de SLA (% de embarques dentro del SLA). Mientras sea
# None, el cumplimiento se muestra sin semáforo ni línea de objetivo.
# Ejemplo: CUMPLIMIENTO_OBJETIVO = 0.80 y CUMPLIMIENTO_MINIMO = 0.60
CUMPLIMIENTO_OBJETIVO = 0.50
CUMPLIMIENTO_MINIMO = 0.50   # igual al objetivo: verde desde 50 %, rojo por debajo

# --------------------------------------------------------------------------
# SLA aéreo: columna "Total" de SEGUIMIENTO AEREOS, por tipo de negocio
# (columna "Parcipacion de DJI + miami +consolidado aereo").
# --------------------------------------------------------------------------
SLA_AEREO_POR_TIPO = {
    "GADNIC": 24,
    "DJI": 24,
    "REPUESTOS": 24,
    "MUESTRAS": 30,
    "DJI AGRAS": 26,
    "MARCAS": 16,
}
# Variantes que usan el SLA de otro tipo (clave y valor en mayúsculas).
SLA_AEREO_ALIAS = {"DJI RCONLINE": "DJI", "DJI BAYNAL": "DJI"}
# El SLA aéreo rige para embarques con ETD desde esta fecha; antes solo se
# muestran los tiempos.
SLA_AEREO_DESDE = dt.date(2026, 8, 1)

# --------------------------------------------------------------------------
# Productos nuevos y top ranking: objetivo de reducir la consolidación
# --------------------------------------------------------------------------
TOP_RANKING_MAX = 100                    # posición en "Demanda Efectiva -Ranking Utilidad Total"
REDUCCION_OBJETIVO = 0.15                # −15 % contra la base
BASE_DESDE = dt.date(2026, 1, 1)         # período base (mes de ETD)
BASE_HASTA = dt.date(2026, 3, 31)
COMPARACION_MESES = 3                    # últimos N meses cerrados contra la base

# ---------------------------------------------------------------------------
# Resumen · Velocidad, eficiencia y cargas especiales
# ---------------------------------------------------------------------------
# Transit time marítimo (ETD → ETA): umbral de casos largos.
TT_MARITIMO_UMBRAL = 45
# Transit time aéreo (ETD → ETA, solo «Aéreo», sin courier): umbral de casos fuera de rango.
# A confirmar con el área; se cambia acá.
TT_AEREO_UMBRAL = 7
# Ocupación de contenedores = m³ / (contenedores × capacidad). La capacidad sale de la columna
# «Capacidad contenedor» de Reservas Históricas; si falta, se usa esta tabla.
CAPACIDAD_CTNR = {"20 ST": 30, "40 ST": 60, "40 HQ": 68, "40 NOR": 60}
OCUPACION_UMBRAL = 0.70
# Valores de la columna de prioridad que justifican un 20 ST con baja ocupación.
PRIORIDAD_JUSTIFICA = {"si", "alta", "urgente", "prioritaria", "prioridad", "critica", "crítica"}

# Consolidación por SO (Embarques Históricos): solo embarques con este destino (None = todos).
PRODUCTOS_DESTINO = "Argentina"


# Shippers (Resumen · FOB por mes de ETA): valores que no son un trader y se sacan del cuadro.
# Se comparan sin mayúsculas ni acentos. «Directo Bidcom» = operación directa sin trader.
SHIPPERS_EXCLUIR = ("no aplica", "sin shipper", "no encontrado", "directo bidcom", "wacom")
# Palabras societarias que no distinguen a un shipper («DROP TRADING LIMITED» = «Drop Trading»).
SHIPPERS_SUFIJOS = ("LIMITED", "LTD", "LLC", "INC", "CO", "CORP", "COMPANY", "SA", "SRL")

# Salud de datos (health check)
SALUD_DIAS_SIN_SO = 15                  # un embarque zarpado hace más de esto debería tener sus SO en Embarques Históricos
SALUD_DIAS_HABILES_SIN_EDICION = 2      # planilla sin ediciones por más de esto = desactualizada

# Panorama: pagado vs mercado. Verde ≤ 0 % (pagamos menos que la mediana de mercado), ámbar hasta esta tolerancia.
PAGADO_VS_MERCADO_TOLERANCIA = 0.05
