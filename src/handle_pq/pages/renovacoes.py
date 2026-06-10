import pandas as pd
import streamlit as st

from handle_pq.components import (
    create_filter
)
from handle_pq.utils import (
    gerar_excel, formatters
)

def show():

    df_renovacoes = st.session_state.df_pq_normalizado[
        (st.session_state.df_pq_normalizado['Grupo'] == 'Frota') 
        &
        (st.session_state.df_pq_normalizado['Status da Ferramenta'] != 'Roubado') 
    ]

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

    total_pago_gf = df_renovacoes['Mensalidade c/Imp'].sum()

    st.write('Parque de Máquinas Filtrado')
    st.dataframe(df_renovacoes)
    text_qtd_valor = f'{len(df_renovacoes)} máquinas, mensalidade total Gestão de Frotas: {formatters.br_num(
        total_pago_gf,
        2,
        True
    )}'
    st.markdown(
        f"""
            <div class="rodape-df">
                {text_qtd_valor}
            </div>
        """,
        unsafe_allow_html=True
    )
    st.subheader('', divider='red')

    df_renovacoes_group = (
        df_renovacoes
        .groupby(['Data de Término do Contrato', 'Tipo', 'Linha', 'Modelo'])
        .size()
        .reset_index(name='Quantidade')
    )

    st.write('Agrupado por vencimento e modelo')
    st.dataframe(df_renovacoes_group)
    st.subheader('', divider='red')

    df_lista = (
        df_renovacoes
        .groupby(['Data de Término do Contrato', 'Linha', 'Modelo'])['Número de série']
        .apply(lambda x: ' - '.join(x))
        .reset_index(name='Séries')
    )

    st.write('Relação dos números de série')
    st.dataframe(df_lista)

    gerar_excel.dowload(df_lista, 'lista_renovacoes.xlsx')