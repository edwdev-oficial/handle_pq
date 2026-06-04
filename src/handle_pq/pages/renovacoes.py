import pandas as pd
import streamlit as st

from handle_pq.components import (
    create_filter
)
from handle_pq.utils.gerar_excel import (
    dowload)

def show():

    df_renovacoes = st.session_state.df_pq_normalizado[
        (st.session_state.df_pq_normalizado['Grupo'] == 'Frota') 
        &
        (st.session_state.df_pq_normalizado['Status da Ferramenta'] != 'Roubado') 
    ]


    st.write(f'Qtd: {len(df_renovacoes)}')

    cliente = create_filter.create_filter(df_renovacoes, 'Razao Social', 'Cliente', True, 'multiselect')
    if cliente:
        df_renovacoes = df_renovacoes[df_renovacoes['Razao Social'].isin(cliente)]

    datas = create_filter.create_filter(df_renovacoes, 'Data de Término do Contrato', 'Data de Término do Contrato', True, 'multiselect')
    datas = [pd.Timestamp(data) for data in datas] if datas else []
    if datas:
        df_renovacoes = df_renovacoes[df_renovacoes['Data de Término do Contrato'].isin(datas)]

    status = create_filter.create_filter(df_renovacoes, 'Status da Ferramenta', 'Status da Ferramenta', True, 'multiselect')
    if status:
        df_renovacoes = df_renovacoes[df_renovacoes['Status da Ferramenta'].isin(status)]    

    st.dataframe(df_renovacoes)
    
    df_renovacoes_group = (
        df_renovacoes
        .groupby(['Data de Término do Contrato', 'Tipo', 'Linha', 'Modelo'])
        .size()
        .reset_index(name='Quantidade')
    )

    st.dataframe(df_renovacoes_group)
    st.write(f'Qtd: {df_renovacoes_group["Quantidade"].sum()}')

    df_lista = (
        df_renovacoes
        .groupby(['Data de Término do Contrato', 'Linha', 'Modelo'])['Número de série']
        .apply(lambda x: ' - '.join(x))
        .reset_index(name='Séries')
    )

    st.dataframe(df_lista)

    dowload(df_lista, 'lista_renovacoes.xlsx')