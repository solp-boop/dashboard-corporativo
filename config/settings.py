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
    "cotizaciones": ("cotizaciones", "Cotizaciones Maritimos Negociado"),
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
    },
    "cotizaciones": {
        "Cotizaciones Maritimos Negociado": 0,
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
}

# --------------------------------------------------------------------------
# SLA
# --------------------------------------------------------------------------
# Consolidación (ETD - Packeo mín.). Monoproveedor usa un SLA fijo; consolidado
# usa el target por puerto de la solapa Validaciones.
SLA_CONSOLIDACION_MONO = 7
SLA_CONSOLIDACION_DEFAULT = 25   # si el puerto no tiene target
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

# Certificación de fletes: flete certificado / flete pagado (objetivo mínimo).
KPI_CERTIFICACION_TARGET = 0.75

# Recomendación de forwarder: un ETD se considera "en fecha" si el ETD real
# difiere de la ETD estimada en hasta estos días.
ETD_TOLERANCIA_DIAS = 3
