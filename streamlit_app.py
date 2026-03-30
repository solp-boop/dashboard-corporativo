import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Dashboard Corporativo", layout="wide")
st.title("📊 Panel de Control Directo")

# Método alternativo directo si la otra librería falla
try:
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    # Intentamos leerlo como CSV público (más rápido y sin errores de módulos)
    csv_url = url.replace("/edit?gid=", "/export?format=csv&gid=")
    df = pd.read_csv(csv_url)
    
    st.success("✅ Conexión exitosa")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error: {e}")
