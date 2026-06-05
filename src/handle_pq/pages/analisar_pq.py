import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from handle_pq.utils import formatters
from handle_pq.components import create_filter
from handle_pq.services import export_dashboard_pdf, get_data_ids, write_xls, export_dashboard_pdf_profissional


COLORS = {
    "red": "#d2051e",
    "beige": "#d7cebd",
    "dark": "#524f53",
    "taupe": "#887f6e",
    "wine": "#671c3e",
    "white": "#ffffff",
    "black": "#000000",
    # "bg": "#f5f3ef",
    "bg": "#fbfaf8",
    "green": "#008000",
    "card": "#F0F2F6",
}

CHART_PALETTE = [
    COLORS["red"],
    COLORS["dark"],
    COLORS["taupe"],
    COLORS["wine"],
    COLORS["beige"],
    COLORS["green"],
]


def inject_css():
    st.markdown(
        f"""
        <style>

            h1 {{
                font-size: 1.8rem !important;
                font-weight: 800 !important;
                color: {COLORS["dark"]};
                margin-bottom: 0.2rem;
            }}

            h2, h3 {{
                color: {COLORS["dark"]};
            }}

            section[data-testid="stSidebar"] {{
                background: #eceff3;
                border-right: 1px solid rgba(82,79,83,0.12);
            }}

            .block-container {{
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 2000px;
            }}

            .dashboard-subtitle {{
                color: {COLORS["taupe"]};
                font-size: 0.95rem;
                margin-bottom: 1.4rem;
            }}

            .kpi-card {{
                background: {COLORS["white"]};
                border: 1px solid rgba(82,79,83,0.12);
                border-left: 5px solid {COLORS["red"]};
                border-radius: 14px;
                padding: 18px 20px;
                box-shadow: 0 3px 12px rgba(0,0,0,0.04);
                min-height: 112px;
            }}

            .kpi-title {{
                font-size: 0.72rem;
                text-transform: uppercase;
                letter-spacing: 0.06rem;
                color: {COLORS["taupe"]};
                font-weight: 700;
                margin-bottom: 8px;
            }}

            .kpi-value {{
                font-size: 1.45rem;
                font-weight: 800;
                color: {COLORS["dark"]};
                line-height: 1.2;
            }}

            .kpi-caption {{
                font-size: 0.78rem;
                color: {COLORS["taupe"]};
                margin-top: 6px;
            }}

            div[data-testid="stVerticalBlockBorderWrapper"] {{
                background: {COLORS["white"]};
                border-radius: 14px;
                border: 1px solid rgba(82,79,83,0.12);
                box-shadow: 0 3px 12px rgba(0,0,0,0.04);
            }}

            .section-title {{
                font-size: 1rem;
                font-weight: 800;
                color: {COLORS["dark"]};
                margin: 0 0 0.4rem 0;
            }}

            .section-caption {{
                font-size: 0.82rem;
                color: {COLORS["taupe"]};
                margin-bottom: 1rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(title, value, caption=""):
    return f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-caption">{caption}</div>
        </div>
    """


def default_fig_layout(fig, title=None, height=360, showlegend=True):
    fig.update_layout(
        title=dict(
            text=title or "",
            font=dict(size=15, color=COLORS["dark"]),
            x=0,
            xanchor="left",
        ),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial",
            size=12,
            color=COLORS["dark"],
        ),
        margin=dict(t=55, b=30, l=25, r=25),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title="",
        ),
        showlegend=showlegend,
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(82,79,83,0.18)",
        tickfont=dict(color=COLORS["dark"]),
        title_font=dict(color=COLORS["taupe"]),
    )

    fig.update_yaxes(
        gridcolor="rgba(82,79,83,0.10)",
        zeroline=False,
        linecolor="rgba(82,79,83,0.18)",
        tickfont=dict(color=COLORS["dark"]),
        title_font=dict(color=COLORS["taupe"]),
    )

    return fig


def prepare_df():
    df_pq = st.session_state.df_pq_normalizado.copy()

    cols_to_drop = [
        "Tipo de Contrato",
        "Ferramenta de empréstimo permitida",
        "Cobertura de roubo",
        "Número do Equipamento",
    ]

    df_pq.drop(
        columns=[col for col in cols_to_drop if col in df_pq.columns],
        inplace=True,
    )

    df_pq = df_pq.fillna("").replace(
        {
            "None": "",
            "nan": "",
            "NaN": "",
        }
    )

    df_data_ids = get_data_ids.get()

    df_pq = pd.merge(
        df_pq,
        df_data_ids,
        on="Id",
        how="left",
    )

    for col_name in ["cliente", "UF"]:
        if col_name in df_pq.columns:
            col = df_pq.pop(col_name)
            df_pq.insert(0, col_name, col)

    df_pq["Data de compra"] = pd.to_datetime(
        df_pq["Data de compra"],
        errors="coerce",
    )

    # df_pq["idade_int (a)"] = (
    #     ((pd.Timestamp.now() - df_pq["Data de compra"]).dt.days // 30) // 12
    # )

    df_pq["idade_int (a)"] = df_pq["Data de compra"].apply(idade_anos_completos)

    df_pq["idade_int (a)"] = df_pq["idade_int (a)"].fillna(0).astype(int)

    df_pq['reparada'] = np.where(
        (df_pq['Último Reparo'].notna())
        &
        (df_pq['Último Reparo'].astype(str).str.strip() != ''),
        'Sim',
        'Não'
    )

    df_pq['Garantia'] = np.where(
        (df_pq['Garantia'].str.lower() == 'dentro')
        |
        (df_pq['Grupo'].str.lower() == 'frota'),
        'Sim',
        'Não'
    )

    return df_pq.reset_index(drop=True)

def aplicar_filtro_termino_contrato(
    df_pq: pd.DataFrame,
    grupo: str,
    col_data: str = "Data de Término do Contrato",
    key_prefix: str = "filtro_termino_contrato"
):
    if grupo == "Comprado":
        return df_pq

    df_pq = df_pq.copy()

    df_pq[col_data] = pd.to_datetime(
        df_pq[col_data],
        errors="coerce"
    )

    with st.sidebar.container(border=True):
        st.markdown("### Filtro término contrato G.F.")

        datas_validas = df_pq[col_data].dropna()

        key_incluir_sem_data = f"{key_prefix}_incluir_sem_data"
        key_data_exata = f"{key_prefix}_data_exata"
        key_date_input = f"{key_prefix}_date_input"

        if key_incluir_sem_data not in st.session_state:
            st.session_state[key_incluir_sem_data] = True

        if key_data_exata not in st.session_state:
            st.session_state[key_data_exata] = False

        incluir_sem_data = st.checkbox(
            "Incluir registros sem data",
            key=key_incluir_sem_data
        )

        data_exata = st.toggle(
            "Data exata",
            key=key_data_exata
        )

        if datas_validas.empty:
            st.warning("Não existem datas válidas em Data de Término do Contrato.")

            if not incluir_sem_data:
                df_pq = df_pq[df_pq[col_data].notna()]

            return df_pq

        data_min = datas_validas.min().date()
        data_max = datas_validas.max().date()

        if data_exata:
            title_filter = "em:"
            value_date_default = (pd.Timestamp.now() + pd.offsets.MonthEnd(0)).date()
        else:
            title_filter = "até:"
            value_date_default = data_max

        # Garante que a data default fica dentro do intervalo
        value_date_default = min(max(value_date_default, data_min), data_max)

        # Inicializa a data no session_state
        if key_date_input not in st.session_state:
            st.session_state[key_date_input] = value_date_default

        # Se filtros acima mudaram e a data salva saiu do intervalo, ajusta
        if st.session_state[key_date_input] < data_min:
            st.session_state[key_date_input] = data_min

        if st.session_state[key_date_input] > data_max:
            st.session_state[key_date_input] = data_max

        termino_contrato = st.date_input(
            f"Término Contrato G.F. {title_filter}",
            min_value=data_min,
            max_value=data_max,
            key=key_date_input
        )

        termino_contrato = pd.to_datetime(termino_contrato)

        coluna_normalizada = df_pq[col_data].dt.normalize()

        if data_exata:
            filtro_data = coluna_normalizada == termino_contrato
        else:
            filtro_data = coluna_normalizada <= termino_contrato

        if incluir_sem_data:
            filtro_data = filtro_data | df_pq[col_data].isna()

        df_pq = df_pq[filtro_data]

    return df_pq

def apply_sidebar_filters(df_pq):
    st.sidebar.markdown("### Filtros")

    mostrar_baixadas = st.sidebar.toggle("Incluir baixadas por B.O.")

    if not mostrar_baixadas:
        df_pq = df_pq[df_pq["Status da Ferramenta"] != "Roubado"]

    cliente = create_filter.create_filter(
        df=df_pq,
        coluna="cliente",
        tilte="Cliente",
        sidebar=True,
        type='selectbox',
        key="filtro_cliente"
    )
    if cliente:
        df_pq = df_pq[df_pq["cliente"] == cliente]

    uf = create_filter.create_filter(
        df=df_pq,
        coluna="UF",
        tilte="UF",
        sidebar=True,
        type='selectbox',
        key="filtro_uf"
    )
    if uf:
        df_pq = df_pq[df_pq["UF"] == uf]

    grupo = create_filter.create_filter(
        df=df_pq,
        coluna="Grupo",
        tilte="Grupo",
        sidebar=True,
        type="selectbox",
        key="filtro_grupo"
    )
    if grupo:
        df_pq = df_pq[df_pq["Grupo"] == grupo]

    status = create_filter.create_filter(
        df=df_pq,
        coluna="Status da Ferramenta",
        tilte="Status",
        sidebar=True,
        type="multiselect",
        key="filtro_status",
        default_all=True
    )
    if status:
        df_pq = df_pq[df_pq["Status da Ferramenta"].isin(status)]

    tipo = create_filter.create_filter(
        df=df_pq,
        coluna="Tipo",
        tilte="Tipo",
        sidebar=True,
        type='selectbox',
        key='filtro_tipo'
    )
    if tipo:
        df_pq = df_pq[df_pq["Tipo"] == tipo]

    linha = create_filter.create_filter(
        df=df_pq,
        coluna="Linha",
        tilte="Linha",
        sidebar=True,
        type='multiselect',
        key='filtro_linha',
        default_all=True
    )
    if linha:
        df_pq = df_pq[df_pq["Linha"].isin(linha)]

    modelo = create_filter.create_filter(
        df=df_pq,
        coluna="Modelo",
        tilte="Modelo",
        sidebar=True,
        type='multiselect',
        key='filtro_modelo',
        default_all=True
    )
    if modelo:
        df_pq = df_pq[df_pq["Modelo"].isin(modelo)]

    reparadas = create_filter.create_filter(
        df=df_pq,
        coluna='reparada',
        tilte='Reparadas',
        sidebar=True,
        type='selectbox',
        key='filtro_reparadas'
    )
    if reparadas:
        df_pq = df_pq[df_pq['reparada'] == reparadas]

    garantia = create_filter.create_filter(
        df=df_pq,
        coluna='Garantia',
        tilte='Garantia',
        sidebar=True,
        type='selectbox',
        key='filtro_garantia'
    )
    if garantia:
        df_pq = df_pq[df_pq['Garantia'] == garantia]

    col_data = 'Data de Término do Contrato'

    df_pq[col_data] = pd.to_datetime(
        df_pq[col_data],
        errors='coerce'
    )

    df_pq = aplicar_filtro_termino_contrato(
        df_pq=df_pq,
        grupo=grupo,
        col_data="Data de Término do Contrato",
        key_prefix="filtro_termino_contrato"
    )    

    idades = create_filter.create_filter(
        df=df_pq,
        coluna='idade_int (a)',
        tilte='Idade',
        sidebar=True,
        type='multiselect',
        key='filter_idade',
        default_all=True
    )
    if idades:
        df_pq = df_pq[df_pq['idade_int (a)'].astype(str).isin(idades)]

    return df_pq.reset_index(drop=True), 'foo'#modelo


def make_group_donut(df_pq):
    df_grupo = (
        df_pq.assign(
            Grupo_Grafico=df_pq["Grupo"].str.lower().map(
                {
                    "comprado": "Compradas",
                    "frota": "Frota",
                }
            )
        )
        .dropna(subset=["Grupo_Grafico"])
        .groupby("Grupo_Grafico")
        .size()
        .reset_index(name="Quantidade")
    )

    fig = px.pie(
        df_grupo,
        values="Quantidade",
        names="Grupo_Grafico",
        hole=0.58,
        color="Grupo_Grafico",
        color_discrete_map={
            "Compradas": COLORS["red"],
            "Frota": COLORS["dark"],
        },
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>Qtd: %{value}<br>%{percent}<extra></extra>",
        marker=dict(line=dict(color=COLORS["white"], width=2)),
    )

    fig = default_fig_layout(
        fig,
        title="Composição do parque",
        height=330,
        showlegend=True,
    )

    return fig


def make_group_bar(df_pq):
    df_grupo_barras = (
        df_pq.assign(
            Grupo_Grafico=df_pq["Grupo"].str.lower().map(
                {
                    "comprado": "Compradas",
                    "frota": "Frota",
                }
            )
        )
        .dropna(subset=["Grupo_Grafico"])
        .groupby("Grupo_Grafico")
        .agg(
            Ferramentas=("Grupo", "size"),
            Reparações=("Quantidade de reparos", "sum"),
        )
        .reset_index()
        .melt(
            id_vars="Grupo_Grafico",
            value_vars=["Ferramentas", "Reparações"],
            var_name="Indicador",
            value_name="Quantidade",
        )
    )

    fig = px.bar(
        df_grupo_barras,
        x="Grupo_Grafico",
        y="Quantidade",
        color="Indicador",
        barmode="group",
        text="Quantidade",
        color_discrete_map={
            "Ferramentas": COLORS["red"],
            "Reparações": COLORS["dark"],
        },
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>",
    )

    fig = default_fig_layout(
        fig,
        title="Ferramentas x reparações",
        height=330,
        showlegend=True,
    )

    fig.update_yaxes(
        title="",
        showticklabels=False,
        showgrid=True,
    )

    fig.update_xaxes(title="")

    return fig


def make_model_ranking(df_pq, top_n=10):
    df_modelos = (
        df_pq.groupby("Modelo")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        df_modelos,
        x="Quantidade",
        y="Modelo",
        orientation="h",
        text="Quantidade",
        color_discrete_sequence=[COLORS["red"]],
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<extra></extra>",
    )

    fig.update_layout(yaxis=dict(autorange="reversed"))

    fig = default_fig_layout(
        fig,
        title=f"Top {top_n} modelos por quantidade",
        height=390,
        showlegend=False,
    )

    fig.update_xaxes(
        title="",
        showticklabels=False,
        showgrid=True,
    )

    fig.update_yaxes(title="")

    return fig


def make_age_bar(df_pq):
    df_idade = (
        df_pq.groupby("idade_int (a)")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("idade_int (a)")
    )

    df_idade["Idade"] = df_idade["idade_int (a)"].astype(str) + " ano(s)"

    fig = px.bar(
        df_idade,
        x="Idade",
        y="Quantidade",
        text="Quantidade",
        color_discrete_sequence=[COLORS["wine"]],
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Quantidade: %{y}<extra></extra>",
    )

    fig = default_fig_layout(
        fig,
        title="Distribuição por idade",
        height=390,
        showlegend=False,
    )

    fig.update_yaxes(
        title="",
        showticklabels=False,
        showgrid=True,
    )

    fig.update_xaxes(title="")

    return fig


def make_repair_cost_by_model(df_pq, top_n=10):
    df_custos = (
        df_pq.groupby("Modelo")
        .agg(
            Custo_Reparo=("Custo de Reparo", "sum"),
            Reparações=("Quantidade de reparos", "sum"),
        )
        .reset_index()
    )

    df_custos["Custo_Reparo_Ajustado"] = df_custos["Custo_Reparo"] * 1.4

    df_custos = (
        df_custos.sort_values("Custo_Reparo_Ajustado", ascending=False)
        .head(top_n)
    )

    fig = px.bar(
        df_custos,
        x="Custo_Reparo_Ajustado",
        y="Modelo",
        orientation="h",
        text=df_custos["Custo_Reparo_Ajustado"].apply(
            lambda x: formatters.br_num(x, 0, True)
        ),
        color_discrete_sequence=[COLORS["taupe"]],
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Custo: R$ %{x:,.2f}<extra></extra>",
    )

    fig.update_layout(yaxis=dict(autorange="reversed"))

    fig = default_fig_layout(
        fig,
        title=f"Top {top_n} modelos por custo de reparo",
        height=390,
        showlegend=False,
    )

    fig.update_xaxes(
        title="",
        showticklabels=False,
        showgrid=True,
    )

    fig.update_yaxes(title="")

    return fig

def idade_anos_completos(data_compra):
    hoje = pd.Timestamp.today().normalize()

    idade = hoje.year - data_compra.year

    ainda_nao_fez_aniversario = (
        (hoje.month < data_compra.month)
        or (hoje.month == data_compra.month and hoje.day < data_compra.day)
    )

    if ainda_nao_fez_aniversario:
        idade -= 1

    return idade

def show():

    inject_css()

    if "df_pq_normalizado" not in st.session_state:
        st.warning("Carregue os arquivos do parque de máquinas do HOL.")
        return

    df_pq = prepare_df()


    df_pq, modelo_filtrado = apply_sidebar_filters(df_pq)

    if df_pq.empty:
        st.info("Nenhum registro encontrado para os filtros selecionados.")
        return

    qtd_total = len(df_pq)
    mensalidade_total = df_pq["Mensalidade c/Imp"].sum()
    qtd_reparacoes = df_pq["Quantidade de reparos"].sum()
    custo_reparo = df_pq["Custo de Reparo"].sum() * 1.4

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(
            kpi_card(
                "Máquinas",
                f"{qtd_total:,.0f}".replace(",", "."),
                "Quantidade total filtrada",
            ),
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            kpi_card(
                "Mensalidade G.F.",
                formatters.br_num(mensalidade_total, 2, True),
                "Valor mensal com impostos",
            ),
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            kpi_card(
                "Reparações",
                f"{qtd_reparacoes:,.0f}".replace(",", "."),
                "Quantidade total de reparos",
            ),
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            kpi_card(
                "Custo reparações",
                formatters.br_num(custo_reparo, 2, True),
                "Net Price * 1.4",
            ),
            unsafe_allow_html=True,
        )

    st.write("")

    tab_geral, tab_modelos, tab_dados = st.tabs(
        ["Visão geral", "Modelos e custos", "Base filtrada"]
    )

    with tab_geral:
        col1, col2 = st.columns([1, 1.55])

        with col1:
            with st.container(border=True):
                st.plotly_chart(
                    make_group_donut(df_pq),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        with col2:
            with st.container(border=True):
                st.plotly_chart(
                    make_group_bar(df_pq),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        col3, col4 = st.columns([1.25, 1])

        with col3:
            with st.container(border=True):
                st.plotly_chart(
                    make_model_ranking(df_pq, top_n=10),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        with col4:
            with st.container(border=True):
                st.plotly_chart(
                    make_age_bar(df_pq),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    with tab_modelos:
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.plotly_chart(
                    make_model_ranking(df_pq, top_n=15),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        with col2:
            with st.container(border=True):
                st.plotly_chart(
                    make_repair_cost_by_model(df_pq, top_n=15),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    with tab_dados:
        # st.dataframe(df_pq)
        colunas_exibir = [
            "cliente",
            "UF",
            "Grupo",
            "Status da Ferramenta",
            "Tipo",
            "Linha",
            "Modelo",
            "Número de série",
            "Data de compra",
            "idade_int (a)",
            "Mensalidade c/Imp",
            "Data de Término do Contrato",
            "Quantidade de reparos",
            "Custo de Reparo",
            "Garantia"
        ]

        colunas_exibir = [col for col in colunas_exibir if col in df_pq.columns]

        df_pq['Custo de Reparo'] = df_pq['Custo de Reparo'] * 1.4

        st.dataframe(
            df_pq[colunas_exibir],
            use_container_width=True,
            hide_index=True,
        )

        arquivo_excel = write_xls.gerar_excel(df_pq)
        date = pd.to_datetime('now')
        year = str(date.year).zfill(4)
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        hour = str(date.hour).zfill(2)
        min = str(date.minute).zfill(2)
        sec = str(date.second).zfill(2)
        file_name = f'pqMaquinas_{year}_{month}_{day}_{hour}_{min}_{sec}'
        st.download_button(
            label="Baixar Excel",
            data=arquivo_excel,
            file_name=f'{file_name}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )        

    pdf = export_dashboard_pdf_profissional.gerar_dashboard_pdf(df_pq)

    st.sidebar.divider()

    st.sidebar.download_button(
        "Exportar PDF",
        data=pdf,
        file_name="dashboard_pq.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
