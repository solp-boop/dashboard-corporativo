import time


def test_vencida_se_sigue_mostrando_y_se_recarga_en_fondo(monkeypatch):
    from services import data_loader
    from tests.fakes import FakeSource, tablero

    monkeypatch.setattr(data_loader.settings, "DATASET_SOURCES",
                        {"reservas": ("tablero", "Reservas"), "validaciones": ("tablero", "Validaciones")})
    src = FakeSource(tablero())
    monkeypatch.setattr(data_loader, "make_source", lambda: src)
    store = data_loader._last_good()
    store.clear()
    primero = data_loader.get_data()
    assert data_loader.get_data() is primero                    # vigente: no relee
    llamadas = src.calls
    store["cargado"] = time.time() - data_loader.settings.CACHE_TTL_SECONDS - 1
    assert data_loader.get_data() is primero                    # vencida: responde ya con la carga actual…
    for _ in range(100):                                        # …y relee en otro hilo
        if store.get("bundle") is not primero:
            break
        time.sleep(0.05)
    assert store["bundle"] is not primero and src.calls > llamadas
    assert data_loader.get_data() is store["bundle"]
    antes, llamadas = store["bundle"], src.calls
    data_loader.clear_cache()                                   # «Actualizar datos»: relee y espera
    assert data_loader.get_data() is not antes and src.calls > llamadas
    store.clear()
