import pandas as pd

from views import buscar


class B:
    def __init__(self, **d):
        self.d = d

    def get(self, k):
        return self.d.get(k)


def test_busca_por_sku_descripcion_y_completa_fechas():
    planif = pd.DataFrame({"so": ["SO-1", "SO-2"], "embarque": [None, "FCL 10"], "codigo": ["RCDJI070", "XX1"],
                           "descripcion": ["Osmo Action 5 Pro", "Otro"], "marca": ["DJI", "Z"], "cantidad": [5, 1],
                           "etd": pd.to_datetime(["2026-11-01", None]), "eta": pd.NaT, "status_final": ["Pendiente", "x"]})
    eh = pd.DataFrame({"so": ["SO-0"], "embarque": ["AIR 208"], "codigo": ["RCDJI070"], "etd": pd.NaT})
    aer = pd.DataFrame({"embarque": ["AIR 208"], "etd": pd.to_datetime(["2026-05-05"]),
                        "eta": pd.to_datetime(["2026-05-09"])})
    b = B(planif=planif, emb_hist=eh, aereos=aer)
    r = buscar.buscar(b, "RCDJI070")
    p = r["productos"]
    assert len(p) == 2 and set(p["so"]) == {"SO-1", "SO-0"}
    hist = p[p["so"] == "SO-0"].iloc[0]
    assert hist["descripcion"] == "Osmo Action 5 Pro" and hist["marca"] == "DJI"       # completa desde Planif
    assert hist["etd"] == pd.Timestamp("2026-05-05")                                   # fecha del embarque
    assert [x[0]["embarque"] for x in r["found"]] == ["AIR 208"]
    assert len(buscar.buscar(b, "osmo action")["productos"]) == 1                      # por descripción (Planif)
    assert buscar.buscar(b, "FCL 10")["productos"].empty
