import streamlit as st
from streamlit_option_menu import option_menu

from handle_pq.pages import (
    handle_pq, tlm, analisar_pq, renovacoes
)

from handle_pq.utils import loaders


def render_header(subtitle: str):
    logo_base64 = loaders.logo_hilti_base64()

    st.markdown(
        f"""
        <div class="header-container">
            <img src="data:image/png;base64,{logo_base64}">
            <div class="header-title">
                Análise do Parque de Máquinas
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def app():
    st.set_page_config(
        page_title='Handle Pq',
        page_icon='⛏️',
        layout='wide',
    )

    # hide_streamlit_style = """
    # <style>
    # #MainMenu {visibility: hidden;}
    # header {visibility: hidden;}
    # footer {visibility: hidden;}
    # </style>

    # """
    # st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    pages = {
        'Carregar dados': {
            'icon': 'box-arrow-in-down',
            'subtitle': 'Carregar dados',
            'show': handle_pq.show
        },
        'Analisar Pq': {
            'icon': 'search',
            'subtitle': 'Visão consolidada do parque, composição por grupo, idade, reparações e custos.',
            'show': analisar_pq.show
        },
        'Renovações': {
            'icon': 'r-square',
            'subtitle': 'Renovações Gestão de Frotas',
            'show': renovacoes.show
        },
        'Cadastrar TLM': {
            'icon': 'book',
            'subtitle': 'Cadastro de tipos, linhas e modelos',
            'show': tlm.show
        },
    }

    with st.sidebar:
        selected = option_menu(
            'Páginas',
            list(pages.keys()),
            icons=[page['icon'] for page in pages.values()]
        )

    current_page = pages[selected]

    render_header(current_page['subtitle'])

    current_page['show']()