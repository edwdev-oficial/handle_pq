import base64
import streamlit as st
from pathlib import Path

def load_css():
    BASE_DIR = Path(__file__).parents[1]
    css_path = BASE_DIR / 'assets' / 'style.css'
    with open (css_path) as f:
        st.html(f'<style>{f.read()}</style>')

def logo_hilti_base64():

    def get_base64(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    BASE_DIR = Path(__file__).parents[1]
    logo_path = BASE_DIR / 'assets' / 'logoHilti.png'
    logo_base64 = get_base64(logo_path)
    return logo_base64        