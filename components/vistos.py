"""«Visto hoy» de la Bandeja de acción: qué casos ya revisó esta persona en el día.

Se guarda en el navegador (localStorage), sin escribir en la planilla: cada persona tiene sus propios vistos y
vale solo para el día. Al día siguiente, lo que siga sin resolverse vuelve a aparecer.
"""
from __future__ import annotations

import hashlib
import json

import pandas as pd
import streamlit as st

CLAVE_LS = "bidcom_bandeja_vistos_v1"

_JS = """
export default function(component) {
  const { data, setStateValue } = component;
  const KEY = '%s';
  try {
    if (data && typeof data.save === 'string') { window.localStorage.setItem(KEY, data.save); }
  } catch (e) {}
  let v = '';
  try { v = window.localStorage.getItem(KEY) || ''; } catch (e) {}
  setStateValue('vistos', v);
}
""" % CLAVE_LS

_store: dict = {}


def _componente():
    """Se registra una vez por runtime de Streamlit (en los tests hay varios runtimes en el mismo proceso)."""
    try:
        rt = id(st.runtime.get_instance())
    except Exception:
        rt = 0
    if rt not in _store:
        _store.clear()
        _store[rt] = st.components.v2.component("bandeja_vistos_store", js=_JS)
    return _store[rt]


def caso_id(df: pd.DataFrame) -> pd.Series:
    """Identificador estable de cada caso dentro del día: tipo + registro + SO + situación."""
    def h(*partes) -> str:
        return hashlib.md5("|".join("" if p is None or p != p else str(p) for p in partes).encode()).hexdigest()[:12]
    cols = [df[c] if c in df else pd.Series(None, index=df.index) for c in ("tipo", "embarque", "so", "situacion")]
    return pd.Series([h(*v) for v in zip(*cols)], index=df.index, dtype=object)


def _leer(txt: str | None, hoy: str) -> set[str]:
    try:
        d = json.loads(txt) if txt else {}
    except (ValueError, TypeError):
        return set()
    return set(d.get("ids", [])) if isinstance(d, dict) and d.get("fecha") == hoy else set()


def vistos(hoy: pd.Timestamp) -> set[str]:
    """Vistos de hoy en este navegador. Monta el componente que lee/escribe el localStorage."""
    dia = f"{hoy:%Y-%m-%d}"
    ss = st.session_state
    if ss.get("acc_vistos_dia") != dia:            # cambió el día: se empieza de cero
        ss["acc_vistos_dia"], ss["acc_vistos"], ss["acc_vistos_ok"] = dia, set(), False
    guardar = ss.pop("acc_vistos_guardar", None)
    r = _componente()(key="acc_vistos_store", data={"save": guardar}, on_vistos_change=lambda: None)
    leido = getattr(r, "vistos", None)
    if not ss["acc_vistos_ok"] and leido is not None:
        ss["acc_vistos"] = _leer(leido, dia) | ss["acc_vistos"]
        ss["acc_vistos_ok"] = True
    return set(ss["acc_vistos"])


def marcar(ids, hoy: pd.Timestamp, visto: bool = True) -> None:
    """Agrega (o quita) casos de los vistos de hoy y los deja listos para guardar en el navegador."""
    ss = st.session_state
    actual = set(ss.get("acc_vistos", set()))
    actual = actual | set(ids) if visto else actual - set(ids)
    ss["acc_vistos"] = actual
    ss["acc_vistos_guardar"] = json.dumps({"fecha": f"{hoy:%Y-%m-%d}", "ids": sorted(actual)})
