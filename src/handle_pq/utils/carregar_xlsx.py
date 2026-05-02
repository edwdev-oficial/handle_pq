import pandas as pd
import streamlit as st
from io import BytesIO

@st.cache_data(show_spinner="Carregando arquivo xlsx...")
def carregar_excel(file_bytes, sheet_name=0):
    return pd.read_excel(BytesIO(file_bytes),sheet_name=sheet_name)

def read(file:BytesIO):
    return carregar_excel(file.getvalue())