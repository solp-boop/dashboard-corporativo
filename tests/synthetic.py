"""Genera planillas sintéticas (con "suciedad" realista) para los tests de la app."""
from __future__ import annotations

import datetime as dt
import random
from pathlib import Path

import pandas as pd

PORTS = ["Ningbo", "Shenzhen", "SHEKOU", "Shekou", "Hong Kong", "Yantian", "Qingdao"]
FFWW = ["DELFIN GROUP", "Delfin Group", "NIP", "Green Company", "Rhenus"]
TIPOS = ["40 HQ", "40 ST", "40ST", "20 ST", "40 NOR"]


def _d(x: dt.date | None, short: bool = False):
    if not x:
        return ""
    return f"{x.day}/{x.month}/{x.year}" if short else x.strftime("%d/%m/%Y")


def write_synthetic(folder: Path) -> dict[str, str]:
    rnd = random.Random(7)
    today = dt.date.today()
    folder = Path(folder)

    def shipment(i, hist=False):
        etd = today + dt.timedelta(days=rnd.randint(-40 if not hist else -500, 45 if not hist else -1))
        pk = etd - dt.timedelta(days=rnd.randint(3, 45))
        ins = pk + dt.timedelta(days=rnd.randint(-5, 15))
        eta = etd + dt.timedelta(days=rnd.randint(30, 55))
        mono = rnd.random() < .35
        return {
            "Embarque": f"FCL {2600 + i}" if not hist else f"FCL {1000 + i}",
            "Empresa": rnd.choice(["Bidcom SRL", "Bidcom srl", "BIdcom SRL", "Foretec SRL"]),
            "Destino": rnd.choice(["Argentina", "argentina", "Mexico"]),
            "Puerto / Aeropuerto": rnd.choice(PORTS),
            "Tipo Carga": rnd.choice(TIPOS),
            "Forwarder": rnd.choice(FFWW),
            "Booked in Advance": rnd.choice(["Booked in Advance", "No Booked in Advance", ""]),
            "ETD": _d(etd) if rnd.random() > .03 else "#N/A",
            "ETA": _d(eta),
            "ETD estimada": _d(etd - dt.timedelta(days=rnd.randint(-3, 7))),
            "F.Packeo Min": _d(pk) if rnd.random() > .05 else "01/01/1900",
            "F.Packeo Max": _d(pk + dt.timedelta(days=rnd.randint(0, 10))),
            "M3": f"{rnd.uniform(5, 70):.2f}".replace(".", ","),
            "Fob SIMI Total": f"USD{rnd.randint(5, 150) * 1000:,}".replace(",", ".") + ",00",
            "Responsable de la carga": rnd.choice(["Sol", "Sofi", "David", "Azul"]),
            "¿ES MONOPROVEEDOR?": ("Monoproveedor" if mono else "Consolidado") if not hist else
                                  ("MONOPROVEEDOR" if mono else "CONSOLIDADO"),
            "Tipo de demora": rnd.choice(["", "", "", "Proveedor", "Marítima", "Maritima", "climatico"]),
            "_ins": _d(ins) if rnd.random() > .05 else "Pendiente",
        }

    res = []
    for i in range(80):
        r = shipment(i)
        r["Fecha de Instrucción"] = r.pop("_ins")
        r["Cant. Contenedores"] = rnd.choice([1, 1, 2])
        r["ETD OK FFWW"] = rnd.choice(["Ok", ""])
        r["FOB Total Real"] = rnd.choice(["0", "12.500,00"])
        r["DRAFT BL"] = rnd.choice(["SI", "NO", "incompleto"])
        r["PACKING LIST FINAL"] = rnd.choice(["SI", "NO"])
        r["Cotizacion agente? "] = ""
        res.append(r)
    res[79]["Embarque"] = "FCL 2679"
    res += [{"Embarque": "FCL 2770", "M3": "0"}, {"Embarque": "AIR PROYECCION", "Empresa": "Bidcom SRL"}]

    hist = []
    for i in range(400):
        r = shipment(i, hist=True)
        r["Fecha de Instruccion"] = r.pop("_ins")
        r["Cant CTNRS"] = rnd.choice([1, 1, 2, 3])
        r["Flete Int PAGADO"] = rnd.choice(["", "USD 3.500,00", "4200"])
        r["Flete Certificado"] = rnd.choice(["", "3000", "USD 2.000,00"])
        r["Flete Int unitario PAGADO"] = rnd.choice(["", "1.800,00", "2500"])
        r["Gastos Locales"] = rnd.choice(["", "805", "USD 1.610,00"])
        r["TOTAL GASTOS ORIGEN"] = rnd.choice(["0", "", "390"])
        r["Resultado Validación"] = rnd.choice(["VALIDADO", "OBSERVADO", ""])
        r["Motivo de Observación"] = rnd.choice(["", "Diferencia en el Flete "])
        r["Linea Maritima"] = rnd.choice(["MSC", "Maersk"])
        r["Índice de carga completa"] = rnd.choice(["0,9", "0.75", ""])
        r["Shipper"] = rnd.choice(["Electro Trade LLC", "#N/A", "#REF!"])
        hist.append(r)
    hist.append(dict(hist[0]))  # duplicado

    aer = []
    for i in range(60):
        etd = today + dt.timedelta(days=rnd.randint(-200, 20))
        pk = etd - dt.timedelta(days=rnd.randint(5, 30))
        aer.append({
            "Estadio": rnd.choice(["ENTREGADO", "ENTREGADO", "COORDINANDO", "EN ORIGEN", "NACIONAZALIDO"]),
            "Embarque": f"AIR {300 + i}", "Empresa": "Bidcom SRL", "Shipper": "DJI",
            "Puerto / Aeropuerto": rnd.choice(["Hong Kong", "Shenzhen", "Miami"]), "Destino": "Argentina",
            "Tipo Carga": rnd.choice(["Avión", "Courrier"]), "Forwarder": rnd.choice(["Caduceus Air", "DHL"]),
            "Parcipacion de DJI + miami +consolidado aereo": rnd.choice(["DJI", "Repuestos", "MUESTRAS"]),
            "F.Packeo Min": _d(pk), "Fecha ingreso al WH": _d(pk + dt.timedelta(days=rnd.randint(0, 10))),
            "ETD": _d(etd), "ETA": _d(etd + dt.timedelta(days=rnd.randint(2, 8))),
            "ETA Caldas": _d(etd + dt.timedelta(days=rnd.randint(8, 14))),
            "FOB SIMI TOTAL": rnd.randint(1000, 60000), "M3": round(rnd.uniform(.1, 3), 2),
            "Cantidad unidades": rnd.choice([10, 200, "N/A"]), "Chargeable Weight": rnd.randint(20, 900),
        })

    planif = []
    for i in range(300):
        etd = today + dt.timedelta(days=rnd.randint(-30, 150))
        inst = rnd.random() < .4
        emb = f"FCL {2600 + rnd.randint(0, 79)}" if inst else ""
        planif.append({
            "SO": f"SO-{38000 + i}", "Embarque": emb if i != 5 else "FCL 2679",
            "Pais Destino": rnd.choice(["Argentina", "Mexico"]),
            "Fecha de Instruccion": _d(etd - dt.timedelta(days=20), short=True) if inst else
                                    rnd.choice(["SIN INSTRUCCION", "SIN INSTRUCCION", "Revisar"]),
            "Tipo Carga": rnd.choice(TIPOS + [""]), "ETD": _d(etd, short=True),
            "ETA": _d(etd + dt.timedelta(days=45)), "Category": rnd.choice(["B Hiriart", "F Sanz"]),
            "Proveedor": rnd.choice(["Proveedor A", "Proveedor B", "DJI"]),
            "Marca": rnd.choice(["GADNIC", "DJI", "Cuk by Gadnic", ""]),
            "Repuestos": rnd.choice(["", "", "Muestra", "Repuestos"]),
            "Puerto de Salida": rnd.choice(PORTS), "M3 Total": f"{rnd.uniform(.1, 20):.2f}".replace(".", ","),
            "Fob Total SIMI": "USD0,00", "Fob Total Real": f"{rnd.randint(1, 90)}.100,00",
            "¿ES MONOPROVEEDOR?": rnd.choice(["SI", "NO", "NO"]),
            "Responsable de la carga": rnd.choice(["Asignacion Pendiente", "Sol", "Sofi"]),
            "Status Final": "Pendiente",
        })

    val = pd.DataFrame([
        ["Bidcom srl", "20 ST", "Shenzhen", None, "Shenzhen", 30, 50, 80],
        ["Foretec SRL", "40 ST", "Hong Kong", None, "Hong Kong", 7, 17, 24],
        [None, None, None, None, "Ningbo", 25, 50, 75],
        [None, None, None, None, "Shekou", 25, 50, 75],
    ], columns=["Empresa", "Tipo de Embarque", "Puertos", "", "Puertos ", "Consolidacion", "Transito ARG", "Total"])

    tablero = folder / "tablero.xlsx"
    with pd.ExcelWriter(tablero) as xw:
        pd.DataFrame(res).to_excel(xw, sheet_name="Reservas", index=False)
        pd.DataFrame(planif).to_excel(xw, sheet_name="Planif cargas", index=False)
        pd.DataFrame(hist).to_excel(xw, sheet_name="Reservas Historicas", index=False)
        pd.DataFrame(aer).to_excel(xw, sheet_name="SEGUIMIENTO AEREOS", index=False)
        val.to_excel(xw, sheet_name="Validaciones", index=False)

    cot = []
    for i in range(300):
        desde = today - dt.timedelta(days=rnd.randint(0, 300))
        cot.append({
            "Tipo de transporte": "Maritimo", "FFWW": rnd.choice(FFWW + ["Gestion Forward"]),
            "Agente": "X", "Valor Flete": f"USD{rnd.randint(15, 90)}00,00", "POL": rnd.choice(PORTS),
            "TT": rnd.choice(["40,00", "TBC", ""]), "Tipo de Servicio": "Directo", "Linea": "MSC",
            "POD": "BUENOS AIRES", "Transbordo": "", "Validez Quincena Desde": _d(desde),
            "Validez Quincena Hasta": _d(desde + dt.timedelta(days=15)), "Dias libres": "14",
            "Pagadero": "COLLECT", "Locales ARG": rnd.choice(["USD 850,00", "", "USD  790,00"]),
            "Tipo Ctnr": rnd.choice(["40ST/40HQ", "20ST", "40NOR", "40 ST / 40 HQ"]),
        })
    cotiz = folder / "cotizaciones.xlsx"
    with pd.ExcelWriter(cotiz) as xw:
        pd.DataFrame(cot).to_excel(xw, sheet_name="Cotizaciones Maritimos Negociado"[:31], index=False)
    return {"tablero": str(tablero), "cotizaciones": str(cotiz)}
