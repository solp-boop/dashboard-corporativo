"""Alias de valores para unificar categorías.

Las diferencias de mayúsculas, acentos y espacios se resuelven solas (se
elige la escritura más frecuente). Acá van solo los casos que no se
resuelven así: typos, abreviaturas y sinónimos.

Las claves se escriben en minúsculas y sin acentos.
"""
from __future__ import annotations

VALUE_ALIASES: dict[str, dict[str, str]] = {
    "empresa": {
        "bidcom srl": "Bidcom SRL",
        "bidcom": "Bidcom SRL",
        "bemotec": "Bemotec SRL",
        "bemotec srl": "Bemotec SRL",
        "foretec": "Foretec SRL",
        "foretec srl": "Foretec SRL",
        "caba": "CABA Innovaciones SRL",
        "caba innovaciones": "CABA Innovaciones SRL",
        "caba innovaciones srl": "CABA Innovaciones SRL",
        "rc online": "RC Online",
        "biggertech": "BIGGERTECH",
        "calitec": "Calitec SRL",
        "calitec srl": "Calitec SRL",
        "baynal": "Baynal",
    },
    "puerto": {
        "zhonshan": "Zhongshan",
        "shanghai": "Shanghai",
        "beijao": "Beijiao",
        "hongkong": "Hong Kong",
        "hk": "Hong Kong",
        "xingang": "Xingang",
        "nangtong": "Nantong",
        "singapure": "Singapur",
        "singapore": "Singapur",
        "qindao": "Qingdao",
        "huang pu": "Huangpu",
        "xiangang": "Xingang",
        "chonqing": "Chongqing",
        "shenzhen yantian": "Yantian",
    },
    "forwarder": {
        "delfin group": "DELFIN GROUP",
        "delfin": "DELFIN GROUP",
        "cargo": "Cargo SA",
        "cargo sa": "Cargo SA",
        "rdm logisitca": "RDM Logística",
        "rdm logistica": "RDM Logística",
        "k n": "K+N",
        "kuehne nagel": "K+N",
        "nip cargo": "NIP",
        "gestion forward": "Gestion Forward",
        "gestion f": "Gestion Forward",
        "mediterraneo cargo": "Mediterraneo",
        "seaside logistic sa": "Seaside",
        "seaside logistic": "Seaside",
    },
    "responsable": {
        "asignacion pendiente": "Sin asignar",
    },
    "tipo_ctnr": {
        "40 st 40 hq": "40ST/40HQ",
        "40st 40hq": "40ST/40HQ",
        "20 st": "20ST",
        "40 nor": "40NOR",
    },
    "tipo_carga": {
        "40st": "40 ST",
        "40 st": "40 ST",
        "40hq": "40 HQ",
        "40 hq": "40 HQ",
        "40hc": "40 HQ",
        "40 hc": "40 HQ",
        "40nor": "40 NOR",
        "20st": "20 ST",
        "20 st": "20 ST",
        "20gp": "20 ST",
        "courrier": "Courier",
        "courier": "Courier",
        "avion": "Avión",
        "avion zflp": "Avión",
        "carguero": "Avión",
        "camion": "Camión",
        "lcl": "LCL",
    },
    "destino": {
        "argentina": "Argentina",
        "mexico": "México",
        "brasil": "Brasil",
        "uruguay": "Uruguay",
        "bolivia": "Bolivia",
    },
    "estructura": {
        "consolidado": "Consolidado",
        "monoproveedor": "Monoproveedor",
        "mono": "Monoproveedor",
        "si": "Monoproveedor",      # Planif cargas: ¿ES MONOPROVEEDOR? = SI
        "no": "Consolidado",
    },
    "booking": {
        "booked in advance": "In advance",
        "no booked in advance": "Spot",
        "in advance": "In advance",
        "spot": "Spot",
    },
    "tipo_demora": {
        "maritima": "Marítima",
        "climatico": "Climático",
        "congestion en puerto de origen": "Congestión en puerto de origen",
    },
    "estadio": {
        "nacionazalido": "NACIONALIZADO",
    },
}

# Valores de "estructura" que no son mono ni consolidado -> sin dato.
ESTRUCTURA_VALIDAS = {"Consolidado", "Monoproveedor"}

# Modo de transporte derivado del tipo de carga (clave plegada).
MODO_POR_TIPO_CARGA: dict[str, str] = {
    "40 hq": "Marítimo FCL", "40 st": "Marítimo FCL", "40 nor": "Marítimo FCL",
    "20 st": "Marítimo FCL", "40hc 20gp": "Marítimo FCL",
    "lcl": "Marítimo LCL",
    "avion": "Aéreo",
    "courier": "Courier",
    "camion": "Terrestre",
}
# Si no hay tipo de carga, se usa el prefijo del embarque.
MODO_POR_PREFIJO: dict[str, str] = {
    "FCL": "Marítimo FCL", "LCL": "Marítimo LCL", "AIR": "Aéreo",
    "AEREO": "Aéreo", "COU": "Courier", "TRUCK": "Terrestre",
}
MODOS_MARITIMOS = {"Marítimo FCL", "Marítimo LCL"}

# Estadios aéreos que se consideran cerrados.
ESTADIOS_CERRADOS = {"ENTREGADO", "NACIONALIZADO"}

# Embarques que no son operaciones reales (filas de relleno).
EMBARQUES_NO_OPERATIVOS = {"air proyeccion", "proyeccion"}

# Tipo de carga (Reservas) -> tipo de contenedor de las cotizaciones.
CTNR_POR_TIPO_CARGA = {
    "40 hq": "40ST/40HQ", "40 st": "40ST/40HQ", "20 st": "20ST", "40 nor": "40NOR",
}

# Aerolíneas escritas de distintas formas.
VALUE_ALIASES["aerolinea"] = {"british": "British Airways", "british airways": "British Airways"}
VALUE_ALIASES["resultado_validacion"] = {"validado": "Validado", "observado": "Observado"}
VALUE_ALIASES["motivo_observacion"] = {"diferencia en el flete": "Diferencia en el flete"}

# Puerto de destino (POD) de las cotizaciones -> país de destino.
# Se busca en orden: la primera palabra que aparece define el país.
DESTINO_POR_POD = [
    ("buenos aires", "Argentina"), ("la plata", "Argentina"), ("tecplata", "Argentina"),
    ("manzanillo", "México"), ("lazaro", "México"), ("veracruz", "México"),
    ("montevideo", "Uruguay"), ("mvd", "Uruguay"),
    ("santos", "Brasil"), ("ssz", "Brasil"),
]
