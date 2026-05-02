import streamlit as st
import pandas as pd
from io import BytesIO

from handle_pq.utils import (
    carregar_xlsx,
    handle_json,
    file_uploader
)
from handle_pq.services import (
    get_pq_normalizado
)


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

def show(df):
    st.title('Test Dev')
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
    normal_itens_from_json(df)