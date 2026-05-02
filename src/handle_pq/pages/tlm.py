import pandas as pd
import streamlit as st

from handle_pq.utils import (
    handle_json
)

def show():
    st.title('Cadastro de Tipos, Linhas e Modelos')
    st.divider()

    if 'input_tipo' not in st.session_state:
        st.session_state.input_tipo = ''
    if 'input_linha' not in st.session_state:
        st.session_state.input_linha = ''
    if 'input_modelo' not in st.session_state:
        st.session_state.input_modelo = ''

    df_normal_itens = handle_json.read_json('normal_itens')[['Tipo', 'Linha', 'Modelo']]

    tml = {
        'tipos': df_normal_itens['Tipo'].unique().tolist(),
        'linhas': df_normal_itens['Linha'].unique().tolist(),
        'modelos': df_normal_itens['Modelo'].unique().tolist()
    }

    def salvar():
        tipo = st.session_state.input_tipo
        linha = st.session_state.input_linha
        modelo = st.session_state.input_modelo    

        if tipo:
            tml['tipos'].append(tipo)
        if linha:
            tml['linhas'].append(linha)
        if modelo:
            tml['modelos'].append(modelo)

        st.session_state.input_tipo = ''
        st.session_state.input_linha = ''
        st.session_state.input_modelo = ''

        if tipo or linha or modelo:
            data = handle_json.write_json(tml, 'tml')
            st.write(data)

    col1, col2, col3 = st.columns(3)

    with col1:
        tipo = st.text_input('Tipo', key='input_tipo')

    with col2:
        linha = st.text_input('Linha', key='input_linha')

    with col3:
        modelo = st.text_input('Modelo', key='input_modelo')
    
    st.button('Salvar', on_click=salvar)

    # st.dataframe(df_normal_itens)