import pandas as pd
import streamlit as st
from bson import ObjectId

from handle_pq.utils import (
    handle_json, ordenar
)
from handle_pq.database import database

def show():
    st.title('Cadastro de Tipos, Linhas e Modelos')
    st.divider()

    if 'input_tipo' not in st.session_state:
        st.session_state.input_tipo = ''
    if 'input_linha' not in st.session_state:
        st.session_state.input_linha = ''
    if 'input_modelo' not in st.session_state:
        st.session_state.input_modelo = ''

    db = database.get_database()
    col_tlm = db['tlm']
    tlm = col_tlm.find().to_list()[0]

    id_documento = tlm['_id']

    tlm['tipos'] = sorted(tlm['tipos'], key=ordenar.chave_ordenacao)
    tlm['linhas'] = sorted(tlm['linhas'], key=ordenar.chave_ordenacao)
    tlm['modelos'] = sorted(tlm['modelos'], key=ordenar.chave_ordenacao)

    df_tipos = pd.DataFrame(tlm['tipos'], columns=['Tipos'])
    df_linhas = pd.DataFrame(tlm['linhas'], columns=['Linhas'])
    df_modelos = pd.DataFrame(tlm['modelos'], columns=['Modelos'])

    def show_df_card(titulo, df, altura=500):
        st.markdown(f"**{titulo}**")
        st.dataframe(
            df,
            height=altura,
            use_container_width=True,
            hide_index=True
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        # st.dataframe(df_tipos, height=500, use_container_width=True)
        show_df_card('Tipos', df_tipos)
    with col2:
        # st.dataframe(df_linhas, height=500, use_container_width=True)
        show_df_card('Linhas', df_linhas)
    with col3:
        # st.dataframe(df_modelos, height=500, use_container_width=True)
        show_df_card('Linhas', df_modelos)

    # # df_normal_itens = handle_json.read_json('normal_itens')[['Tipo', 'Linha', 'Modelo']]

    # # tlm = {
    # #     'tipos': df_normal_itens['Tipo'].unique().tolist(),
    # #     'linhas': df_normal_itens['Linha'].unique().tolist(),
    # #     'modelos': df_normal_itens['Modelo'].unique().tolist()
    # # }

    # # st.write(tlm)

    def salvar():
        tipo = st.session_state.input_tipo
        linha = st.session_state.input_linha
        modelo = st.session_state.input_modelo

        dados = {
            'tipos': tipo,
            'linhas': linha,
            'modelos': modelo
        }

        # add_to_set = {
        #     campo: valor
        #     for campo, valor in dados.items()
        #     if valor not in (None, '')
        # }

        add_to_set = {
            campo: valor.strip()
            for campo, valor in dados.items()
            if isinstance(valor, str) and valor.strip()
        }

        st.session_state.input_tipo = ''
        st.session_state.input_linha = ''
        st.session_state.input_modelo = ''

        if add_to_set:
            resultado = col_tlm.update_one(
                {"_id": id_documento},
                {"$addToSet": add_to_set}
            )
        else:
            resultado = None

        if resultado and resultado.acknowledged:
            st.success('Dados inseridos com sucesso.')


    with col1:

        tipo = st.text_input('Tipo', key='input_tipo')

    with col2:
        linha = st.text_input('Linha', key='input_linha')

    with col3:
        modelo = st.text_input('Modelo', key='input_modelo')
    
    st.button('Salvar', on_click=salvar)
