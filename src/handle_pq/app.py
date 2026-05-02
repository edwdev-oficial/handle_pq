import streamlit as st
from streamlit_option_menu import option_menu

from handle_pq.pages import (
    handle_pq, test_dev, tlm
)

def app():
    st.set_page_config(
        page_title='Handle Pq',
        page_icon='⛏️',
        layout='wide',
    )

    def handle_pq_show():
        handle_pq.show()

    def cadastrar_show():
        tlm.show()        

    def test_dev_show():
        if not st.session_state.df_pq.empty:
            test_dev.show(st.session_state.df_pq)
        else:
            handle_pq.show()
            st.warning('Carregue os arquivos de parque de máquinas baixados no HOL')

    with st.sidebar:
        selected = option_menu(
            'Páginas',
            [
                'Handle Pq',
                'Cadastrar',
                # '---',
                # 'Test Dev',
            ],
            icons=[
                'tools',
                'r-circle',
                # None,
                # 'filetype-py'
            ]
        )

    root = {
        'Handle Pq': handle_pq_show,
        'Cadastrar': cadastrar_show,
        'Test Dev': test_dev_show
    }        

    root[selected]()

