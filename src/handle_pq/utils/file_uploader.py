import streamlit as st

def upload(multiple_files:bool, tipo:str):
    return st.file_uploader('Enviar arquivo', accept_multiple_files=multiple_files, type=tipo)