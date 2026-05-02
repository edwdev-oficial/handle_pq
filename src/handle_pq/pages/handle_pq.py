import re
import json
import pandas as pd
import streamlit as st
from io import BytesIO

from handle_pq.assets.colunas import colunas
from handle_pq.utils import (formatters, gerar_excel, handle_json)
from handle_pq.services import (
    write_xls,
    get_pq_normalizado
)
from handle_pq.components import (
    widgets
)


@st.cache_data(show_spinner="Carregando arquivos...")
def carregar_excel(file_bytes, sheet_name=0):
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)

def convert_col_df_to_number(df, colunas = []):
    for coluna in colunas:
        df[coluna] = df[coluna].fillna(0)
        df[coluna] = df[coluna].replace('-', 0)
        df[coluna] = df[coluna].astype(float)

def convert_col_df_to_date(df, colunas = []):
    for coluna in colunas:
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce')


def show():
    st.set_page_config(
        page_title='Handle Pq',
        page_icon='⛏️',
        layout='wide',
    )

    if 'df_pq' not in st.session_state:
        st.session_state.df_pq = pd.DataFrame()

    st.title('Handle Pq')
    st.write('App para formatar as planilhas de parque de máquinas')
    st.divider()

    files = st.file_uploader('Selecione os arquivos', type='xlsx', accept_multiple_files=True)

    cols_data = [
        'Data de Início do Contrato',
        'Data de Término do Contrato',
        'Último Reparo',
        'Data de compra',
        'Fim do período sem custo'
    ]

    if files:

        dfs = []

        for file in files:
            raz_id = file.name.split('-')[2:]
            df = carregar_excel(file.getvalue())
            df.insert(0, 'Razao Social', raz_id[0] )
            df.insert(0, 'Id', raz_id[1].replace('.xlsx', '') )
            dfs.append(df)

        df_pq = pd.concat(dfs)
        df_pq = df_pq.reindex(columns=df_pq.columns.union(colunas))
        df_pq = df_pq[colunas]
        
        convert_col_df_to_number(df_pq, ['Mensalidade', 'Custo de Reparo'])

        convert_col_df_to_date(
            df_pq,
            cols_data
        )
        df_pq = df_pq.fillna('')


        st.session_state.df_pq = df_pq


    if not st.session_state.df_pq.empty:

        df_pq = st.session_state.df_pq

        columns_config = {
            col: st.column_config.DateColumn(format='DD/MM/YYYY')
            for col in cols_data
        }

        df_pq = get_pq_normalizado.get(df_pq)

        df_not_normalizer = df_pq[df_pq[['Tipo', 'Linha', 'Modelo']].isna().any(axis=1)]
        if not df_not_normalizer.empty:
            
            st.warning('Normalize os itens abaixo')

            not_normalizer_uniq = list(df_not_normalizer['Descrição'].unique())

            df_normalizar = pd.DataFrame({
                'Descrição': not_normalizer_uniq,
                
            })
            df_normalizar[['Tipo', 'linha', 'modelo']] = ''
            df_normal_itens =handle_json.read_json('normal_itens')

            tlm = handle_json.read_json('tml', 'dict')

            def chave_ordenacao(valor):
                texto = str(valor)

                prefixo = re.search(r'^[A-Za-z]+', texto)
                numero = re.search(r'(\d+)', texto)

                prefixo = prefixo.group(0) if prefixo else texto
                numero = int(numero.group(1)) if numero else -1

                return (prefixo, numero, texto)

            tlm['tipos'] = sorted(tlm['tipos'], key=chave_ordenacao)
            tlm['linhas'] = sorted(tlm['linhas'], key=chave_ordenacao)
            tlm['modelos'] = sorted(tlm['modelos'], key=chave_ordenacao)

            df_editado = st.data_editor(
                df_normalizar,
                column_config={
                    'Tipo': widgets.column_config('Tipo', tlm['tipos']),
                    'linha': widgets.column_config('Linha', tlm['linhas']),
                    'modelo': widgets.column_config('Modelo', tlm['modelos'])
                },
                hide_index=True,
                use_container_width=True
            )

            df_editado.rename(columns={'linha': 'Linha', 'modelo': 'Modelo'}, inplace=True)

            if st.button('Salvar'):
                pass
                df_normal_itens = pd.concat([
                    df_normal_itens,
                    df_editado                    
                ]).reset_index(drop=True)
                result = handle_json.write_json(df_normal_itens, 'normal_itens')
                if result == 'success':
                    st.rerun()

        else:

            df_pq['Mensalidade'] = round(df_pq['Mensalidade'] / (1-0.0925), 2) 
            df_pq.rename(columns={'Mensalidade': 'Mensalidade c/Imp'}, inplace=True)

            arquivo_excel = write_xls.gerar_excel(df_pq)

            df_pq['Número de série'] = df_pq['Número de série'].astype(str).fillna('')
            df_pq['Duração do contrato'] = pd.to_numeric(
                df_pq['Duração do contrato'],
                errors='coerce'
            ).fillna(0).astype(int)
            st.dataframe(
                df_pq,
                column_config=columns_config
            )
            total_custo_gf = df_pq['Mensalidade c/Imp'].sum()
            total_custo_repair = df_pq['Custo de Reparo'].sum()
            st.write(f'Total Mensalidades G.F. c/Imp: {formatters.br_num(total_custo_gf, 2, True)}')
            st.write(f'Custo total de reparações: {formatters.br_num(total_custo_repair, 2, True)}')

            st.download_button(
                label="Baixar Excel",
                data=arquivo_excel,
                file_name="relatorio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )         
        

        # gerar_excel.dowload(df=df_pq, name='pq_maquinas')