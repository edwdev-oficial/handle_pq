import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.graph_objects as go
import numpy as np

from handle_pq.utils import (
    carregar_xlsx,
    handle_json,
    file_uploader
)
from handle_pq.services import (
    get_pq_normalizado
)
from handle_pq.components import (
    create_filter
)
from handle_pq.database.database import get_database


def formatar_colunas_data(
    df,
    worksheet,
    workbook,
    colunas_data,
    largura=13,
    formato_data_excel="dd/mm/yyyy",
    cor_linha='#D9D9D9'
):
    formato_data = workbook.add_format({
        "num_format": formato_data_excel,
        "align": "center",
        "valign": "vcenter",
        "bottom": 5,
        "bottom_color": cor_linha,
        "font_name": "Nunito",
        "font_size": 10,
    })

    for coluna in colunas_data:
        if coluna not in df.columns:
            continue

        # Garante que a coluna esteja como datetime
        df[coluna] = pd.to_datetime(df[coluna], errors="coerce")

        idx_coluna = df.columns.get_loc(coluna)

        # Define largura e formato da coluna
        worksheet.set_column(idx_coluna, idx_coluna, largura, formato_data)

        # Reescreve as células com write_datetime para o formato pegar corretamente
        for row_num, valor in enumerate(df[coluna], start=1):
            if pd.notna(valor):
                worksheet.write_datetime(
                    row_num,
                    idx_coluna,
                    valor.to_pydatetime(),
                    formato_data
                )
            else:
                worksheet.write_blank(
                    row_num,
                    idx_coluna,
                    None,
                    formato_data
                )


def show(df=pd.DataFrame()):

    if 'subtitle_page' not in st.session_state:
        st.session_state.subtitle_page = 'Página para testes e desenvolvimento'

    st.title('Test Dev')
    st.subheader(st.session_state.subtitle_page)
    st.divider()

    # ========================================================
    # region GERAR EXCEL
    # ========================================================
    def gerar_excel(df):
        output = BytesIO()

        colunas_data = [
            'Data de Início do Contrato',
            'Data de Término do Contrato',
            'Último Reparo',
            'Data de compra',
            'Fim do período sem custo'
        ]    

        df['Número de série'] = pd.to_numeric(
            df['Número de série'],
            errors='coerce'
        ).astype("Int64")

        st.dataframe(df)        

        # ========================================================
        # region RASCUNHOS
        # ========================================================
        # # with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            
        # #     df.to_excel(
        # #         writer,
        # #         sheet_name="Relatório",
        # #         index=False,
        # #         startrow=0
        # #     )

        # #     workbook = writer.book
        # #     worksheet = writer.sheets["Relatório"]

        # #     worksheet.hide_gridlines(2)
        # #     worksheet.autofit()

        # #     # formato_titulo = workbook.add_format({
        # #     #     "bold": True,
        # #     #     "font_size": 16,
        # #     #     "align": "center",
        # #     #     "valign": "vcenter"
        # #     # })

        # #     # formato_cabecalho = workbook.add_format({
        # #     #     "bold": True,
        # #     #     "bg_color": "#D9EAF7",
        # #     #     "border": 1,
        # #     #     "align": "center",
        # #     #     "valign": "vcenter"
        # #     # })

        # #     formato_moeda = workbook.add_format({
        # #         "num_format": 'R$ #,##0.00',
        # #         "border": 1
        # #     })

        # #     formato_numero = workbook.add_format({
        # #         "num_format": "#,##0",
        # #         "border": 1
        # #     })

        # #     formato_data = workbook.add_format({
        # #         "num_format": "dd/mm/yyyy",
        # #         "border": 1
        # #     })

        # #     # worksheet.merge_range(
        # #     #     0, 0, 0, len(df.columns) - 1,
        # #     #     "Relatório de Equipamentos",
        # #     #     formato_titulo
        # #     # )

        # #     for col_num, coluna in enumerate(df.columns):
        # #         # worksheet.write(0, col_num, coluna, formato_cabecalho)
        # #         worksheet.write(0, col_num, coluna)

        # #     # worksheet.set_column("A:A", 20)
        # #     # worksheet.set_column("B:B", 12, formato_numero)
        # #     # worksheet.set_column("C:C", 15, formato_moeda)
        # #     # worksheet.set_column("D:D", 15, formato_data)

        # #     # worksheet.freeze_panes(2, 0)
        # #     # worksheet.autofilter(1, 0, len(df) + 1, len(df.columns) - 1)
        # endregion
        # ========================================================

        linha_tenue = '#D9D9D9'
        linha_forte = ''

        with pd.ExcelWriter(
            output,
            engine="xlsxwriter",
            datetime_format="dd/mm/yyyy",
            date_format="dd/mm/yyyy"        
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="Relatório",
                index=False
            )

            worksheet = writer.sheets["Relatório"]
            worksheet.hide_gridlines(2)
            worksheet.set_default_row(30)
            worksheet.set_zoom(80)
            workbook = writer.book


            formato_data = workbook.add_format({
                "num_format": "dd/mm/yyyy",
                "align": "center",
                "font_name": "Nunito",
                "font_size": 10,
            })

            formato_numero_int = workbook.add_format({
                "num_format": "0",
                "align": "center",
                "font_name": "Nunito",
                "font_size": 10,                
            })

            formato_centralizado = workbook.add_format({
                "align": "center",
                "valign": "vcenter",
                "bottom": 5,
                "bottom_color": linha_tenue,
                "font_name": "Nunito",
                "font_size": 10,                
            })

            formato_geral = workbook.add_format({
                "valign": "vcenter",
                "bottom": 5,
                "bottom_color": linha_tenue,
                "font_name": "Nunito",
                "font_size": 10,                
            })

            formato_primeira_linha = workbook.add_format({
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bottom": 5,
                "bottom_color": "#808080",
                "font_name": "Nunito",
                "font_size": 10,                
            })            

            formato_linha = workbook.add_format({
                "bottom": 5,
                "bottom_color": linha_tenue
            })            

            worksheet.set_column("A:X", None, formato_linha)
            worksheet.set_column(0, len(df.columns) - 1, None, formato_geral)
            worksheet.set_column("K:K", 12, formato_data)
            worksheet.set_column("G:G", 10, formato_numero_int)
            worksheet.set_column("X:X", 10, formato_centralizado)
            worksheet.set_column("A:A", 10, formato_centralizado)
            worksheet.set_column("D:D", 10, formato_centralizado)
            worksheet.set_column("E:G", 10, formato_centralizado)
            worksheet.set_column("I:J", 10, formato_centralizado)
            worksheet.set_column("M:O", 10, formato_centralizado)
            worksheet.set_column("S:T", 10, formato_centralizado)

            formatar_colunas_data(
                df=df,
                worksheet=worksheet,
                workbook=workbook,
                colunas_data=colunas_data,
                largura=13,
                cor_linha=linha_tenue
            )

            for col in range(0, 24):  # A até X
                valor = df.columns[col] if col < len(df.columns) else ""
                worksheet.write(0, col, valor, formato_primeira_linha)

            worksheet.autofit()       


        output.seek(0)
        # return output

        arquivo_excel = output

        st.download_button(
            label="Baixar Excel",
            data=arquivo_excel,
            file_name="relatorio.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # endregion
    # ========================================================
    # gerar_excel(df)

    # ========================================================
    # region NORMAL ITENS FROM EXCEL
    # ========================================================
    def normal_itens_from_excel(df):
        st.dataframe(df)

        file = file_uploader.upload(multiple_files=False, tipo='xlsx')
        if file:
            df_normal_itens = carregar_xlsx.read(file=file)
            st.dataframe(df_normal_itens)

            df_merge = pd.merge(
                df,
                df_normal_itens,
                on=['Descrição'],
                how='left'
            )

            st.dataframe(df_merge)

            # st.write(handle_json.read_json())
            if st.button('Salvar JSON'):
                handle_json.write_json(df_normal_itens, 'normal_itens')

    # endregion
    # ========================================================
    # normal_itens_from_excel(df)

    # ========================================================
    # region NORMAL ITENS FROM JSON
    # ========================================================
    def normal_itens_from_json(df:pd.DataFrame):

        df_pq = get_pq_normalizado.get(df)
        st.subheader('Parque Normalizado')
        st.dataframe(df_pq)
    
    # endregion
    # ========================================================
    # normal_itens_from_json(df)

    # ========================================================
    # region GRAPH WATERFALL
    # ========================================================
    def graph_waterfall():
        x = [
            'Product<br>Revenue',
            'Services<br>Revenue',
            'Total<br>Revenue',
            'Fixed<br>Costs',
            'Variable<br>Costs',
            'Total<br>Costs',
            'Total'
        ]

        y_text_position = [400, 660, 660, 590, 400, 400, 340]

        base = [0, 430, 0, 570, 370, 370, 0]
        revenue = [430, 260, 690, 0, 0, 0, 0]
        costs = [0, 0, 0, 120, 200, 320, 0]
        profit = [0, 0, 0, 0, 0, 0, 370]

        text = ['$430K', '$260K', '$690K', '$-120K', '$-200K', '$-320K', '$370K']

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=x,
            y=base,
            marker=dict(color='rgba(1,1,1,0.0)'),
            hoverinfo='skip',
            showlegend=False
        ))

        fig.add_trace(go.Bar(
            x=x,
            y=revenue,
            marker=dict(
                color='rgba(55, 128, 191, 0.7)',
                line=dict(color='rgba(55, 128, 191, 0.7)', width=2)
            ),
            name='Revenue',
            showlegend=False
        ))

        fig.add_trace(go.Bar(
            x=x,
            y=costs,
            marker=dict(
                color='rgba(219, 64, 82, 0.7)',
                line=dict(color='rgba(219, 64, 82, 1.0)', width=2)
            ),
            name='Costs',
            showlegend=False
        ))

        fig.add_trace(go.Bar(
            x=x,
            y=profit,
            marker=dict(
                color='rgba(50, 171, 96, 0.7)',
                line=dict(color='rgba(50, 171, 96, 1.0)', width=2)
            ),
            name='Profit',
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=x,
            y=y_text_position,
            text=text,
            mode='text',
            textfont=dict(
                family='Arial',
                size=14,
                color='white'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig.update_layout(
            title='Annual Profit - 2015',
            barmode='stack',
            xaxis=dict(title=''),
            yaxis=dict(title=''),
            paper_bgcolor='rgba(245, 246, 249, 1)',
            plot_bgcolor='rgba(245, 246, 249, 1)',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
    # endregion
    # ========================================================
    # graph_waterfall()

    # ========================================================
    # region COPARAR PQS MAQUINA
    # ========================================================
    def comparar_pqs_maquina():
        st.session_state.subtitle_page = 'Comparar PQs por número de série da máquina'
        
        files = file_uploader.upload(multiple_files=True, tipo='xlsx')

        if files and len(files) == 2:

            xlsx_1 = pd.ExcelFile(BytesIO(files[0].getvalue()))
            xlsx_2 = pd.ExcelFile(BytesIO(files[1].getvalue()))

            list_abas_1 = xlsx_1.sheet_names
            list_abas_2 = xlsx_2.sheet_names

            abas_1 = ['']
            abas_2 = ['']
            abas_1.extend(list_abas_1)
            abas_2.extend(list_abas_2)

            aba1 = st.sidebar.selectbox('Selecione a aba do primeiro arquivo', abas_1, key='aba_1')
            aba2 = st.sidebar.selectbox('Selecione a aba do segundo arquivo', abas_2, key='aba_2')

            if aba1 and aba2:
                df1 = pd.read_excel(BytesIO(files[0].getvalue()), sheet_name=aba1)
                df2 = pd.read_excel(BytesIO(files[1].getvalue()), sheet_name=aba2)

                colunas_df1 = ['']
                colunas_df2 = ['']
                colunas_df1.extend(df1.columns.tolist())
                colunas_df2.extend(df2.columns.tolist())

                show_colunas_df1 = st.sidebar.multiselect('Selecione as colunas do primeiro arquivo', colunas_df1, default=colunas_df1[1:], key='colunas_df1')
                show_colunas_df2 = st.sidebar.multiselect('Selecione as colunas do segundo arquivo', colunas_df2, default=colunas_df2[1:], key='colunas_df2')

                if len(show_colunas_df1) > 0 and len(show_colunas_df2) > 0:
                    df1 = df1[show_colunas_df1]
                    df2 = df2[show_colunas_df2]

                    st.subheader('PQs Carregados')
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write('Pq 1')
                        colunas_df1 = ['']
                        values_colunas_df1 = df1.columns.tolist()
                        colunas_df1.extend(values_colunas_df1)
                        filtrar_por = st.selectbox('Filtrar pela coluna', colunas_df1, key='filtrar_coluna_df1')
                        valores_filtrar = df1[filtrar_por].dropna().unique().tolist() if filtrar_por else ['']
                        valor_selecionado = st.selectbox('Valor para filtrar', valores_filtrar, key='valor_filtrar_df1')
                        if valor_selecionado:
                            df1 = df1[df1[filtrar_por] == valor_selecionado]
                        st.dataframe(df1)
                        st.write(f'Qtd registros: {len(df1)}')
                    with col2:
                        st.write('Pq 2')
                        colunas_df2 = ['']                        
                        values_colunas_df2 = df2.columns.tolist()
                        colunas_df2.extend(values_colunas_df2)
                        filtrar_por = st.selectbox('Filtrar pela coluna', colunas_df2, key='filtrar_coluna_df2')
                        valores_filtrar = df2[filtrar_por].dropna().unique().tolist() if filtrar_por else ['']
                        valor_selecionado = st.selectbox('Valor para filtrar', valores_filtrar, key='valor_filtrar_df2')
                        if valor_selecionado:
                            df2 = df2[df2[filtrar_por] == valor_selecionado]
                        st.dataframe(df2)
                        st.write(f'Qtd registros: {len(df2)}')
                    st.divider()

                    coluna_comparar_df1 = st.selectbox('Selecione a coluna para comparar do primeiro arquivo', df1.columns.tolist(), key='coluna_comparar_df1')
                    coluna_comparar_df2 = st.selectbox('Selecione a coluna para comparar do segundo arquivo', df2.columns.tolist(), key='coluna_comparar_df2')

                    if coluna_comparar_df1 and coluna_comparar_df2:
                        # Comparar os DataFrames
                        df_comparacao = pd.merge(
                            df1,
                            df2,
                            left_on=coluna_comparar_df1,
                            right_on=coluna_comparar_df2,
                            how='outer',
                            suffixes=('_Pq1', '_Pq2'),
                            indicator=True
                        )

                    st.subheader('Comparação dos PQs')
                    st.dataframe(df_comparacao)
                    st.write(f'Qtd registros: {len(df_comparacao)}')

                    st.subheader('', divider="red")
                    st.subheader('DataFrame para tratar')
                    df_tratar = df_comparacao[df_comparacao['_merge'] != 'both'].reset_index(drop=True)
                    st.dataframe(df_tratar)
                    st.write(f'Qtd registros: {len(df_tratar)}')

                    # df_unicos = df_tratar.drop_duplicates(keep='first').reset_index(drop=True)
                    # st.subheader('', divider="red")
                    # st.subheader('DataFrame para tratar - registros únicos')
                    # st.dataframe(df_unicos)
                    # st.write(f'Qtd registros: {len(df_unicos)}')

                    # df_duplicados = df_tratar[df_tratar.duplicated(keep='first')].reset_index(drop=True)
                    # st.subheader('', divider="red")
                    # st.subheader('DataFrame para tratar - registros duplicados')
                    # st.dataframe(df_duplicados)
                    # st.write(f'Qtd registros: {len(df_duplicados)}')

                    # series_duplicadas = df_duplicados['Número de série'].to_list()
                    # st.subheader('', divider="red")
                    # st.subheader('Séries duplicadas')
                    # st.write(series_duplicadas)

    # endregion
    # ========================================================
    # comparar_pqs_maquina()

    # ========================================================
    # region ANALISAR PQ MAQUINAS
    # ========================================================
    def analisar_pq_maquinas():
        st.session_state.subtitle_page = 'Analisar PQs por número de série da máquina'
        file = file_uploader.upload(multiple_files=False, tipo='xlsx')
        if file:
            df = carregar_xlsx.read(file=file, sheet_name='tb_pq_maquinas')
            df.drop(columns=[
                'Referência Organizacional',
                'Tipo de Contrato',
                'Ferramenta de empréstimo permitida',
                'Cobertura de roubo'
            ], inplace=True, errors='ignore')
            df = df.fillna('')

            baixadas_bo = st.sidebar.toggle('Incluir máquinas baixadas por B.O.', value=False)

            cliente = create_filter.create_filter(
                df=df,
                coluna='cliente',
                tilte='Filtrar por cliente',
                sidebar=True,
                type='selectbox'
            )
            if cliente:
                df = df[df['cliente'] == cliente].reset_index(drop=True)

            uf = create_filter.create_filter(
                df=df,
                coluna='UF',
                tilte='Filtrar por UF',
                sidebar=True,
                type='selectbox'
            )
            if uf:
                df = df[df['UF'] == uf].reset_index(drop=True)

            grupo = create_filter.create_filter(
                df=df,
                coluna='Grupo',
                tilte='Filtrar por grupo',
                sidebar=True,
                type='selectbox'
            )
            if grupo:
                df = df[df['Grupo'] == grupo].reset_index(drop=True)                

            tipo = create_filter.create_filter(
                df=df,
                coluna='Tipo',
                tilte='Filtrar por tipo',
                sidebar=True,
                type='selectbox'
            )
            if tipo:
                df = df[df['Tipo'] == tipo].reset_index(drop=True)

            linha = create_filter.create_filter(
                df=df,
                coluna='Linha',
                tilte='Filtrar por linha',
                sidebar=True,
                type='selectbox'
            )
            if linha:
                df = df[df['Linha'] == linha].reset_index(drop=True)

            modelo = create_filter.create_filter(
                df=df,
                coluna='Modelo',
                tilte='Filtrar por modelo',
                sidebar=True,
                type='selectbox'
            )
            if modelo:
                df = df[df['Modelo'] == modelo].reset_index(drop=True)                                

            if not baixadas_bo:
                df = df[~df['Status da Ferramenta'].str.contains('Roubado', case=False, na=False)].reset_index(drop=True)
            else:
                with st.expander('Máquinas baixadas por B.O.', expanded=False):
                    st.warning('Incluindo máquinas baixadas por B.O.')
                    df_roubadas = df[df['Status da Ferramenta'].str.contains('Roubado', case=False, na=False)].reset_index(drop=True)
                    st.subheader('Máquinas baixadas por B.O.')
                    st.dataframe(df_roubadas)
                    st.write(f'Qtd registros: {len(df_roubadas)}')


            df['Idade (a)'] = pd.to_numeric(
                df['Idade (a)'].replace('', pd.NA),
                errors='coerce'
            ).fillna(0)
            df['EM LTS'] = np.where(
                (df['Grupo'] == 'Comprado') & (df['Idade (a)'] < 2),
                'Sim',
                'Não'
            ) 

            st.dataframe(df)
            st.write(f'Qtd registros: {len(df)}')
            st.write(f'Custo total de reparações: R$ {df["Custo de Reparo c/Imp"].sum():,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    # endregion
    # ========================================================
    # analisar_pq_maquinas()

    # ========================================================
    # region INSERT DATA CCs SRCBA - BRASILIA
    # ========================================================
    def insert_data_srcb_brasilia():
        st.session_state.subtitle_page = 'Inserir dados lojas CCs Sorocaba e Brasilia' 


        file = file_uploader.upload(multiple_files=False, tipo='xlsx')

        if file:
            df = carregar_xlsx.read(file)
            df = df[['UF', 'cliente', 'codClie']]
            st.dataframe(df)

            data_send = df.to_dict(orient='records')
            # st.write(data_send)

            db = get_database()
            collection_data_ids = db['ccs_sorocaba_brasilia_ids']
            if st.button('Salvar'):

                collection_data_ids.insert_many(data_send)

            df_datas = pd.DataFrame(collection_data_ids.find().to_list())
            st.dataframe(df_datas)

    # endregion
    # ========================================================
    # insert_data_srcb_brasilia()