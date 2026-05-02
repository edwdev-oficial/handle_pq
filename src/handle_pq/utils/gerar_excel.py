import streamlit as st
import pandas as pd

def dowload(df: pd.DataFrame, name: str):
    @st.cache_data
    def gerar_excel(df):
        import io
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer

    buffer = gerar_excel(df)
    return st.download_button(
        label="Baixar Excel",
        data=buffer,
        file_name=f"{name}.xlsx"
    )