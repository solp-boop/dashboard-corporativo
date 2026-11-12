import pandas as pd

from services.data_loader import prepare_emb_hist


def test_etd_vacia_se_completa_con_reservas_historicas():
    eh = pd.DataFrame({
        "so": ["SO-1", "SO-2"],
        "embarque": ["FCL 10", "FCL 11"],
        "etd": [pd.NaT, pd.Timestamp("2026-02-10")],
        "fin_produccion": [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-01")],
        "f_packeo_act": [pd.NaT, pd.NaT],
        "tiempo_consolidacion": [-46000.0, 9.0],
        "sku_nuevo": ["NO", "NO"], "ranking": ["", ""],
        "estructura_eh": ["CONSOLIDADO", "CONSOLIDADO"], "destino": ["Argentina", "Argentina"],
    })
    hist = pd.DataFrame({"embarque": ["FCL 10"], "etd": [pd.Timestamp("2026-01-20")],
                         "estructura": [None], "destino": ["Argentina"]})
    prepare_emb_hist(eh, hist)
    assert eh.loc[0, "etd"] == pd.Timestamp("2026-01-20")
    assert eh.loc[0, "tiempo_consolidacion"] == 19
    assert eh.loc[1, "tiempo_consolidacion"] == 9
