import streamlit as st

def column_config(title:str, lista:list):
    return st.column_config.SelectboxColumn(
        title,
        options=lista
    )
