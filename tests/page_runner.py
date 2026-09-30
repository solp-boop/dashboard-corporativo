"""Script auxiliar para probar cada vista con AppTest (usa los mismos pasos que streamlit_app.py)."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from components.filters import render_filters  # noqa: E402
from components.layout import load_css, page_header  # noqa: E402
from services.data_loader import get_data  # noqa: E402

load_css()
bundle = get_data()
with st.sidebar:
    filters = render_filters(bundle)
page = st.secrets["test_page"]
page_header(page, bundle, filters)
importlib.import_module(f"views.{page}").render()
