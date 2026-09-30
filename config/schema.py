"""Esquema de cada solapa: columna canónica <- encabezados posibles.

- Los encabezados se comparan "plegados": sin mayúsculas, acentos, signos ni
  espacios extra. "Cotizacion agente? " y "Cotización Agente" son lo mismo.
- Si alguien corrige un typo en la planilla (p. ej. "Parcipacion" ->
  "Participacion"), agregá el nuevo nombre a la lista de alias y listo.
- required=True: sin esa columna el dataset no se puede usar y se muestra un
  mensaje indicando cuál falta. El resto son opcionales: si faltan, se
  desactivan solo los indicadores que las usan.

Tipos: id | text | category | date | number | flag
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Col:
    name: str
    aliases: tuple[str, ...]
    kind: str = "text"
    required: bool = False
    label: str = ""  # nombre legible para mensajes

    @property
    def display(self) -> str:
        return self.label or self.aliases[0]


@dataclass(frozen=True)
class DatasetSchema:
    key: str
    title: str
    columns: tuple[Col, ...]
    id_column: str | None = None
    date_ref: str = "etd"          # fecha que usa el filtro de período
    extra: dict = field(default_factory=dict)

    def col(self, name: str) -> Col:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)


def C(name, *aliases, kind="text", required=False, label=""):
    return Col(name=name, aliases=tuple(aliases), kind=kind, required=required, label=label)


# ---------------------------------------------------------------------------
RESERVAS = DatasetSchema(
    key="reservas",
    title="Reservas (embarques en curso)",
    id_column="embarque",
    columns=(
        C("embarque", "Embarque", kind="id", required=True),
        C("contenedores", "Cant. Contenedores", "Cant CTNRS", "Cantidad Contenedores", kind="number"),
        C("empresa", "Empresa", kind="category"),
        C("destino", "Destino", kind="category"),
        C("puerto", "Puerto / Aeropuerto", "Puerto", "Puerto de Salida", kind="category"),
        C("tipo_carga", "Tipo Carga", "Tipo de Carga", kind="category"),
        C("forwarder", "Forwarder", "FFWW", "Agente", kind="category"),
        C("f_instruccion", "Fecha de Instrucción", "Fecha de Instruccion", kind="date"),
        C("booking", "Booked in Advance", kind="category"),
        C("cutoff", "Cut Off", kind="date"),
        C("etd_ok", "ETD OK FFWW", kind="flag"),
        C("etd_estimada", "ETD estimada", kind="date"),
        C("etd", "ETD", kind="date", required=True),
        C("eta", "ETA", kind="date"),
        C("bl", "N° BL", "Nro BL", "BL", kind="text"),
        C("f_packeo_min", "F.Packeo Min", "Fecha Packeo Min", kind="date"),
        C("f_packeo_max", "F.Packeo Max", "Fecha Packeo Max", kind="date"),
        C("shipper", "Shipper", kind="category"),
        C("fob_simi", "Fob SIMI Total", "FOB SIMI TOTAL", kind="number"),
        C("fob_real", "FOB Total Real", "Fob Total Real", kind="number"),
        C("m3", "M3", "M3 Total", kind="number"),
        C("observaciones", "Observaciones", kind="text"),
        C("responsable", "Responsable de la carga", "Responsable", kind="category"),
        C("estructura", "¿ES MONOPROVEEDOR?", "ES MONOPROVEEDOR", "Monoproveedor", kind="category"),
        C("draft_bl", "DRAFT BL", kind="category"),
        C("pl_final", "PACKING LIST FINAL", kind="category"),
        C("fotos", "FOTOS EMBARQUE", kind="category"),
        C("doc_imo", "DOC IMO (MSDS)", kind="category"),
        C("carga_imo", "CARGA IMO", kind="category"),
        C("f_bl_final", "FECHA ENVIO DEL BL FINAL", kind="date"),
        C("f_confirmacion", "Fecha de confirmación de Salida agente", kind="date"),
        C("tipo_demora", "Tipo de demora", kind="category"),
    ),
)

HISTORICAS = DatasetSchema(
    key="historicas",
    title="Reservas Históricas",
    id_column="embarque",
    columns=(
        C("embarque", "Embarque", kind="id", required=True),
        C("contenedores", "Cant CTNRS", "Cant. Contenedores", kind="number"),
        C("empresa", "Empresa", kind="category"),
        C("destino", "Destino", kind="category"),
        C("puerto", "Puerto / Aeropuerto", "Puerto", kind="category"),
        C("tipo_carga", "Tipo Carga", kind="category"),
        C("forwarder", "Forwarder", kind="category"),
        C("f_instruccion", "Fecha de Instruccion", "Fecha de Instrucción", kind="date"),
        C("booking", "Booked in Advance", kind="category"),
        C("etd_estimada", "ETD estimada", kind="date"),
        C("shipper", "Shipper", kind="category"),
        C("etd", "ETD", kind="date", required=True),
        C("eta", "ETA", kind="date"),
        C("bl", "N° BL", kind="text"),
        C("responsable", "Responsable de la carga", kind="category"),
        C("f_bl_final", "FECHA ENVIO DEL BL FINAL", kind="date"),
        C("f_confirmacion", "Fecha de confirmacion de reserva", "Fecha de confirmación de reserva", kind="date"),
        C("tipo_demora", "Tipo de demora", kind="category"),
        C("observaciones", "OBSERVACIONES", kind="text"),
        C("estructura", "¿ES MONOPROVEEDOR?", kind="category"),
        C("f_packeo_min", "F.Packeo Min", kind="date"),
        C("f_packeo_max", "F.Packeo Max", kind="date"),
        C("fob_simi", "Fob SIMI Total", kind="number"),
        C("m3", "M3", kind="number"),
        C("gastos_origen", "TOTAL GASTOS ORIGEN", kind="number"),
        C("flete_pagado", "Flete Int PAGADO", kind="number"),
        C("flete_unitario", "Flete Int unitario PAGADO", kind="number"),
        C("flete_certificado", "Flete Certificado", kind="number"),
        C("gastos_locales", "Gastos Locales", kind="number"),
        C("flete_cotizado", "Flete Cotizado control", kind="number"),
        C("resultado_validacion", "Resultado Validación", "Resultado Validacion", kind="category"),
        C("motivo_observacion", "Motivo de Observación", "Motivo de Observacion", kind="category"),
        C("capacidad", "Capacidad contenedor", kind="number"),
        C("indice_carga", "Índice de carga completa", "Indice de carga completa", kind="number"),
        C("linea", "Linea Maritima", "Línea Marítima", kind="category"),
        C("medio", "Barco/Avión", "Barco/Avion", kind="category"),
    ),
)

AEREOS = DatasetSchema(
    key="aereos",
    title="Seguimiento Aéreos",
    id_column="embarque",
    columns=(
        C("estadio", "Estadio", "Estado", kind="category"),
        C("embarque", "Embarque", kind="id", required=True),
        C("empresa", "Empresa", kind="category"),
        C("shipper", "Shipper", kind="category"),
        C("puerto", "Puerto / Aeropuerto", kind="category"),
        C("destino", "Destino", kind="category"),
        C("tipo_carga", "Tipo Carga", kind="category"),
        C("forwarder", "Forwarder", kind="category"),
        C("tipo_negocio", "Parcipacion de DJI + miami +consolidado aereo",
          "Participacion de DJI + miami +consolidado aereo", "Tipo de negocio", kind="category"),
        C("f_packeo_min", "F.Packeo Min", kind="date"),
        C("f_packeo_max", "F.Packeo Max", kind="date"),
        C("f_ingreso_wh", "Fecha ingreso al WH", kind="date"),
        C("f_instruccion", "Fecha instruccion", "Fecha de Instruccion", kind="date"),
        C("etd_ok", "ETD OK FFWW", kind="flag"),
        C("etd", "ETD", kind="date", required=True),
        C("eta", "ETA", kind="date"),
        C("eta_caldas", "ETA Caldas", kind="date"),
        C("guia", "N° Guia", "N° Guía", kind="text"),
        C("fob_simi", "FOB SIMI TOTAL", "Fob SIMI Total", kind="number"),
        C("gross_weight", "Gross Weight", kind="number"),
        C("m3", "M3", kind="number"),
        C("unidades", "Cantidad unidades", kind="number"),
        C("chargeable", "Chargeable Weight", kind="number"),
        C("tipo_demora", "Tipo de demora", kind="category"),
        C("observaciones", "observaciones", kind="text"),
        C("aerolinea", "AEROLINEA", kind="category"),
        C("flete_pagado", "Flete total", kind="number"),
        C("flete_certificado", "Flete certificado", kind="number"),
        C("gastos_origen", "Gastos en Origen", kind="number"),
        C("gastos_locales", "Gastos Locales", kind="number"),
    ),
)

PLANIF = DatasetSchema(
    key="planif",
    title="Planificación de cargas (SO)",
    id_column="so",
    columns=(
        C("so", "SO", kind="id", required=True),
        C("embarque", "Embarque", kind="text"),
        C("destino", "Pais Destino", "País Destino", kind="category"),
        C("f_instruccion_raw", "Fecha de Instruccion", "Fecha de Instrucción", kind="text"),
        C("tipo_carga", "Tipo Carga", kind="category"),
        C("etd", "ETD", kind="date", required=True),
        C("eta", "ETA", kind="date"),
        C("category_manager", "Category", kind="category"),
        C("proveedor", "Proveedor", kind="category"),
        C("marca", "Marca", kind="category"),
        C("clase", "Repuestos", kind="category"),
        C("puerto", "Puerto de Salida", kind="category"),
        C("m3", "M3 Total", kind="number"),
        C("fob_simi", "Fob Total SIMI", kind="number"),
        C("fob_real", "Fob Total Real", kind="number"),
        C("estructura", "¿ES MONOPROVEEDOR?", kind="category"),
        C("responsable", "Responsable de la carga", kind="category"),
        C("status_final", "Status Final", kind="category"),
        C("f_packeo", "Unificacion Fecha de Packeo", "Fecha de Packeo", kind="date"),
        C("modalidad", "Modalidad de Costeo Reposicion", "Modalidad de Costeo Reposición", kind="category"),
    ),
)

COTIZACIONES = DatasetSchema(
    key="cotizaciones",
    title="Cotizaciones de fletes marítimos",
    id_column=None,
    date_ref="validez_desde",
    columns=(
        C("forwarder", "FFWW", "Forwarder", kind="category", required=True),
        C("agente", "Agente", kind="category"),
        C("flete", "Valor Flete", kind="number", required=True),
        C("puerto", "POL", "Puerto", kind="category"),
        C("tt", "TT", kind="number"),
        C("servicio", "Tipo de Servicio", kind="category"),
        C("linea", "Linea", "Línea", kind="category"),
        C("pod", "POD", kind="category"),
        C("transbordo", "Transbordo", kind="category"),
        C("validez_desde", "Validez Quincena Desde", "Validez Desde", kind="date", required=True),
        C("validez_hasta", "Validez Quincena Hasta", "Validez Hasta", kind="date", required=True),
        C("dias_libres", "Dias libres", "Días libres", kind="text"),
        C("pagadero", "Pagadero", kind="category"),
        C("locales_arg", "Locales ARG", kind="number"),
        C("tipo_ctnr", "Tipo Ctnr", "Tipo Contenedor", kind="category", required=True),
        C("comentarios", "Comentarios", kind="text"),
    ),
)

SCHEMAS: dict[str, DatasetSchema] = {
    s.key: s for s in (RESERVAS, HISTORICAS, AEREOS, PLANIF, COTIZACIONES)
}

# Solapa Validaciones: se interpreta por posición relativa porque tiene
# encabezados repetidos ("Puertos" aparece 3 veces). Se busca la columna
# "Consolidacion" y se toma la de su izquierda como puerto.
VALIDACIONES_SLA_ANCHOR = ("Consolidacion", "Consolidación")
VALIDACIONES_SLA_COLUMNS = ("consolidacion", "transito", "total")
