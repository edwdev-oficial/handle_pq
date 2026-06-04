from __future__ import annotations

from datetime import datetime
from io import BytesIO
from math import cos, radians, sin
from typing import Iterable

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from pathlib import Path
from reportlab.lib.utils import ImageReader

# Paleta Hilti / dashboard
COLORS = {
    "red": "#d2051e",
    "beige": "#d7cebd",
    "dark": "#524f53",
    "taupe": "#887f6e",
    "wine": "#671c3e",
    "white": "#ffffff",
    "black": "#000000",
    "bg": "#fbfaf8",
    "card": "#f0f2f6",
    "grid": "#e3e1dc",
    "border": "#d8d6d1",
}

CHART_PALETTE = [
    COLORS["red"],
    COLORS["dark"],
    COLORS["taupe"],
    COLORS["wine"],
    COLORS["beige"],
]

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LOGO_HILTI_PATH = ASSETS_DIR / "logoHilti.png"

# ========================================================
# API PRINCIPAL
# ========================================================
def gerar_dashboard_pdf(
    df: pd.DataFrame,
    filtros: dict | None = None,
    titulo: str = "Análise do Parque de Máquinas",
    subtitulo: str = "Visão consolidada do parque, composição por grupo, idade, reparações e custos.",
    fator_custo_reparo: float = 1.4,
) -> bytes:
    """
    Gera um PDF em bytes com layout profissional no padrão do dashboard Streamlit.

    Observação importante:
    - Esta função aplica fator_custo_reparo sobre a coluna 'Custo de Reparo'.
    - Se você já enviou o DataFrame com custo ajustado, chame com fator_custo_reparo=1.0.
    """
    filtros = filtros or {}
    df = _preparar_df(df)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    resumo = _criar_resumo(df, fator_custo_reparo=fator_custo_reparo)

    # Página 1 - dashboard executivo
    _draw_page_bg(pdf, width, height)
    _draw_header(pdf, width, height, titulo, subtitulo, filtros)
    _draw_kpis(pdf, width, height, resumo["kpis"])
    _draw_dashboard_charts(pdf, width, height, resumo)
    _draw_footer(pdf, width)
    pdf.showPage()

    # Página 2 - tabelas e ranking
    _draw_page_bg(pdf, width, height)
    _draw_simple_header(pdf, width, height, "Resumo analítico", subtitulo="Detalhamento dos principais agrupamentos")
    _draw_tables_page(pdf, width, height, resumo)
    _draw_footer(pdf, width)
    pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


# ========================================================
# PREPARAÇÃO DOS DADOS
# ========================================================
def _preparar_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Garante colunas mínimas sem quebrar o PDF
    defaults = {
        "Grupo": "",
        "Modelo": "",
        "Quantidade de reparos": 0,
        "Custo de Reparo": 0,
        "Mensalidade c/Imp": 0,
        "idade_int (a)": 0,
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    for col in ["Quantidade de reparos", "Custo de Reparo", "Mensalidade c/Imp", "idade_int (a)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ["Grupo", "Modelo"]:
        df[col] = df[col].astype("string").fillna("").str.strip()

    return df


def _criar_resumo(df: pd.DataFrame, fator_custo_reparo: float) -> dict:
    qtd_total = len(df)
    mensalidade_total = _sum(df, "Mensalidade c/Imp")
    qtd_reparacoes = _sum(df, "Quantidade de reparos")
    custo_reparo = _sum(df, "Custo de Reparo") * fator_custo_reparo

    grupo_norm = df["Grupo"].astype(str).str.lower().str.strip()
    qtd_compradas = int(grupo_norm.eq("comprado").sum())
    qtd_frota = int(grupo_norm.eq("frota").sum())

    resumo_grupo = (
        df.assign(_grupo=df["Grupo"].astype(str).str.strip().replace("", pd.NA))
        .dropna(subset=["_grupo"])
        .groupby("_grupo", as_index=False)
        .agg(
            Maquinas=("Grupo", "size"),
            Reparacoes=("Quantidade de reparos", "sum"),
            Mensalidade=("Mensalidade c/Imp", "sum"),
            Custo=("Custo de Reparo", "sum"),
        )
        .sort_values("Maquinas", ascending=False)
    )
    resumo_grupo["Custo"] = resumo_grupo["Custo"] * fator_custo_reparo

    top_modelos = (
        df[df["Modelo"].astype(str).str.strip().ne("")]
        .groupby("Modelo", as_index=False)
        .agg(
            Quantidade=("Modelo", "size"),
            Reparacoes=("Quantidade de reparos", "sum"),
            Custo=("Custo de Reparo", "sum"),
        )
        .sort_values("Quantidade", ascending=False)
        .head(10)
    )
    top_modelos["Custo"] = top_modelos["Custo"] * fator_custo_reparo

    custo_modelos = (
        df[df["Modelo"].astype(str).str.strip().ne("")]
        .groupby("Modelo", as_index=False)
        .agg(
            Custo=("Custo de Reparo", "sum"),
            Reparacoes=("Quantidade de reparos", "sum"),
            Quantidade=("Modelo", "size"),
        )
        .sort_values("Custo", ascending=False)
        .head(10)
    )
    custo_modelos["Custo"] = custo_modelos["Custo"] * fator_custo_reparo

    idade = (
        df.groupby("idade_int (a)", as_index=False)
        .size()
        .rename(columns={"size": "Quantidade"})
        .sort_values("idade_int (a)")
    )

    grupo_barras = pd.DataFrame({
        "Grupo": ["Compradas", "Frota"],
        "Ferramentas": [qtd_compradas, qtd_frota],
        "Reparações": [
            _sum(df[grupo_norm.eq("comprado")], "Quantidade de reparos"),
            _sum(df[grupo_norm.eq("frota")], "Quantidade de reparos"),
        ],
    })

    return {
        "kpis": [
            ("Máquinas", _fmt_int(qtd_total), "Quantidade total filtrada"),
            ("Mensalidade G.F.", _fmt_money(mensalidade_total), "Valor mensal com impostos"),
            ("Reparações", _fmt_int(qtd_reparacoes), "Quantidade total de reparos"),
            ("Custo reparações", _fmt_money(custo_reparo), f"Net Price * {fator_custo_reparo:g}"),
        ],
        "grupo_donut": [("Compradas", qtd_compradas, COLORS["red"]), ("Frota", qtd_frota, COLORS["dark"])],
        "grupo_barras": grupo_barras,
        "top_modelos": top_modelos,
        "custo_modelos": custo_modelos,
        "idade": idade,
        "resumo_grupo": resumo_grupo,
    }


def _sum(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return 0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


# ========================================================
# DESENHO GERAL
# ========================================================
def _draw_page_bg(pdf: canvas.Canvas, width: float, height: float):
    pdf.setFillColor(_hex(COLORS["bg"]))
    pdf.rect(0, 0, width, height, stroke=0, fill=1)

def _draw_hilti_logo(c, x, y, width=88):
    if not LOGO_HILTI_PATH.exists():
        return

    logo = ImageReader(str(LOGO_HILTI_PATH))
    img_w, img_h = logo.getSize()

    ratio = img_h / img_w
    height = width * ratio

    c.drawImage(
        logo,
        x,
        y,
        width=width,
        height=height,
        mask="auto"
    )

# def _draw_header(pdf: canvas.Canvas, width: float, height: float, titulo: str, subtitulo: str, filtros: dict):
#     margin = 34
#     y = height - 34

#     _draw_hilti_logo(
#         pdf,
#         x=margin,
#         y=y - 42,
#         width=100
#     )

#     pdf.setFillColor(_hex(COLORS["dark"]))
#     pdf.setFont("Helvetica-Bold", 19)
#     pdf.drawRightString(width - margin, y - 10, titulo)

#     pdf.setFillColor(_hex(COLORS["taupe"]))
#     pdf.setFont("Helvetica", 8.5)
#     pdf.drawRightString(width - margin, y - 27, subtitulo)

#     pdf.setFont("Helvetica", 7.5)
#     pdf.drawRightString(width - margin, y - 43, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

#     filtros_txt = _format_filters(filtros)
#     if filtros_txt:
#         pdf.setFillColor(_hex(COLORS["card"]))
#         pdf.roundRect(margin, y - 70, width - 2 * margin, 18, 6, stroke=0, fill=1)
#         pdf.setFillColor(_hex(COLORS["taupe"]))
#         pdf.setFont("Helvetica", 7)
#         pdf.drawString(margin + 10, y - 64, filtros_txt[:170])


def _draw_header(
    pdf: canvas.Canvas,
    width: float,
    height: float,
    titulo: str,
    subtitulo: str,
    filtros: dict
):
    margin = 34
    top_y = height - 28

    # Logo alinhada no topo esquerdo, sem invadir os KPIs
    _draw_hilti_logo(
        pdf,
        x=margin,
        y=top_y - 32,
        width=92
    )

    # Título no topo direito
    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.setFont("Helvetica-Bold", 19)
    pdf.drawRightString(
        width - margin,
        top_y - 8,
        titulo
    )

    pdf.setFillColor(_hex(COLORS["taupe"]))
    pdf.setFont("Helvetica", 8.5)
    pdf.drawRightString(
        width - margin,
        top_y - 25,
        subtitulo
    )

    pdf.setFont("Helvetica", 7.5)
    pdf.drawRightString(
        width - margin,
        top_y - 40,
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )

    filtros_txt = _format_filters(filtros)

    if filtros_txt:
        pdf.setFillColor(_hex(COLORS["card"]))
        pdf.roundRect(
            margin,
            top_y - 68,
            width - 2 * margin,
            18,
            6,
            stroke=0,
            fill=1
        )

        pdf.setFillColor(_hex(COLORS["taupe"]))
        pdf.setFont("Helvetica", 7)
        pdf.drawString(
            margin + 10,
            top_y - 62,
            filtros_txt[:170]
        )

# def _draw_simple_header(pdf: canvas.Canvas, width: float, height: float, titulo: str, subtitulo: str = ""):
#     margin = 34
#     y = height - 36

#     # pdf.setFillColor(_hex(COLORS["red"]))
#     # pdf.roundRect(margin, y - 20, 70, 22, 2, stroke=0, fill=1)
#     # pdf.setFillColor(_hex(COLORS["white"]))
#     # pdf.setFont("Helvetica-Bold", 13)
#     # pdf.drawCentredString(margin + 35, y - 15, "HILTI")

#     pdf.setFillColor(_hex(COLORS["dark"]))
#     pdf.setFont("Helvetica-Bold", 18)
#     pdf.drawString(margin + 90, y - 5, titulo)

#     pdf.setFillColor(_hex(COLORS["taupe"]))
#     pdf.setFont("Helvetica", 9)
#     pdf.drawString(margin + 90, y - 22, subtitulo)

def _draw_simple_header(
    pdf: canvas.Canvas,
    width: float,
    height: float,
    titulo: str,
    subtitulo: str = ""
):
    margin = 34
    top_y = height - 28

    _draw_hilti_logo(
        pdf,
        x=margin,
        y=top_y - 32,
        width=92
    )

    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawRightString(
        width - margin,
        top_y - 8,
        titulo
    )

    if subtitulo:
        pdf.setFillColor(_hex(COLORS["taupe"]))
        pdf.setFont("Helvetica", 8.5)
        pdf.drawRightString(
            width - margin,
            top_y - 25,
            subtitulo
        )


def _draw_footer(pdf: canvas.Canvas, width: float):
    pdf.setFillColor(_hex(COLORS["taupe"]))
    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(width - 34, 18, "Parque de Máquinas - relatório gerado automaticamente")


# ========================================================
# KPIS
# ========================================================
def _draw_kpis(pdf: canvas.Canvas, width: float, height: float, kpis: list[tuple[str, str, str]]):
    margin = 34
    gap = 12
    card_w = (width - 2 * margin - 3 * gap) / 4
    card_h = 62
    y = height - 153

    for idx, (title, value, caption) in enumerate(kpis):
        x = margin + idx * (card_w + gap)
        _rounded_card(pdf, x, y, card_w, card_h)
        pdf.setFillColor(_hex(COLORS["red"]))
        pdf.roundRect(x, y, 5, card_h, 3, stroke=0, fill=1)

        pdf.setFillColor(_hex(COLORS["taupe"]))
        pdf.setFont("Helvetica-Bold", 6.8)
        pdf.drawCentredString(x + card_w / 2, y + card_h - 18, title.upper())

        pdf.setFillColor(_hex(COLORS["dark"]))
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawCentredString(x + card_w / 2, y + 27, str(value))

        pdf.setFillColor(_hex(COLORS["taupe"]))
        pdf.setFont("Helvetica", 6.5)
        pdf.drawCentredString(x + card_w / 2, y + 12, caption)


# ========================================================
# GRÁFICOS
# ========================================================
def _draw_dashboard_charts(pdf: canvas.Canvas, width: float, height: float, resumo: dict):
    margin = 34
    gap = 12
    top_y = height - 178

    left_w = 330
    right_w = width - 2 * margin - gap - left_w

    # Linha 1
    _draw_chart_card(pdf, margin, top_y - 160, left_w, 160, "Composição do parque")
    _draw_donut(pdf, resumo["grupo_donut"], margin + 95, top_y - 82, 50, inner=28)
    _draw_legend(pdf, resumo["grupo_donut"], margin + 178, top_y - 60)

    _draw_chart_card(pdf, margin + left_w + gap, top_y - 160, right_w, 160, "Ferramentas x reparações")
    _draw_grouped_bars(pdf, resumo["grupo_barras"], margin + left_w + gap + 34, top_y - 132, right_w - 68, 95)

    # Linha 2
    y2 = top_y - 178
    _draw_chart_card(pdf, margin, y2 - 210, left_w + 105, 200, "Top 10 modelos por quantidade")
    _draw_horizontal_bars(
        pdf,
        resumo["top_modelos"],
        label_col="Modelo",
        value_col="Quantidade",
        x=margin + 38,
        y=y2 - 188,
        w=left_w + 45,
        h=150,
        color=COLORS["red"],
        value_fmt=_fmt_int,
    )

    _draw_chart_card(pdf, margin + left_w + 117, y2 - 210, width - margin - (margin + left_w + 117), 200, "Distribuição por idade")
    _draw_age_bars(
        pdf,
        resumo["idade"],
        x=margin + left_w + 150,
        y=y2 - 178,
        w=width - margin - (margin + left_w + 170),
        h=135,
    )


def _draw_chart_card(pdf, x, y, w, h, title):
    _rounded_card(pdf, x, y, w, h)
    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x + 12, y + h - 18, title)


def _draw_donut(pdf, data: list[tuple[str, int, str]], cx: float, cy: float, radius: float, inner: float):
    data = [(label, int(value), color) for label, value, color in data if value > 0]
    total = sum(v for _, v, _ in data)

    if not data or total == 0:
        _draw_empty(pdf, cx - radius, cy, "Sem dados")
        return

    start = 90
    for label, value, color in data:
        extent = -360 * value / total
        pdf.setFillColor(_hex(color))
        pdf.wedge(cx - radius, cy - radius, cx + radius, cy + radius, start, extent, stroke=0, fill=1)
        start += extent

    pdf.setFillColor(_hex(COLORS["white"]))
    pdf.circle(cx, cy, inner, stroke=0, fill=1)

    # percentual maior no centro
    major = max(data, key=lambda x: x[1])
    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(cx, cy + 3, f"{major[1] / total:.0%}")
    pdf.setFillColor(_hex(COLORS["taupe"]))
    pdf.setFont("Helvetica", 6.5)
    pdf.drawCentredString(cx, cy - 10, "maior grupo")


def _draw_legend(pdf, data: list[tuple[str, int, str]], x: float, y: float):
    total = sum(v for _, v, _ in data) or 1
    for idx, (label, value, color) in enumerate(data):
        line_y = y - idx * 17
        pdf.setFillColor(_hex(color))
        pdf.rect(x, line_y, 7, 7, stroke=0, fill=1)
        pdf.setFillColor(_hex(COLORS["dark"]))
        pdf.setFont("Helvetica", 7.5)
        pdf.drawString(x + 11, line_y - 0.5, f"{label}: {_fmt_int(value)} ({value / total:.1%})")


def _draw_grouped_bars(pdf, df: pd.DataFrame, x: float, y: float, w: float, h: float):
    if df.empty:
        _draw_empty(pdf, x, y + h / 2, "Sem dados")
        return

    max_val = max(float(df["Ferramentas"].max()), float(df["Reparações"].max()), 1)
    groups = df.to_dict("records")
    group_w = w / len(groups)
    bar_w = min(22, group_w * 0.18)

    # legenda
    legend_y = y + h + 12
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(_hex(COLORS["red"]))
    pdf.rect(x, legend_y, 7, 7, stroke=0, fill=1)
    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.drawString(x + 10, legend_y - 0.5, "Ferramentas")
    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.rect(x + 80, legend_y, 7, 7, stroke=0, fill=1)
    pdf.drawString(x + 90, legend_y - 0.5, "Reparações")

    # eixo base
    pdf.setStrokeColor(_hex(COLORS["grid"]))
    pdf.line(x, y, x + w, y)

    for idx, item in enumerate(groups):
        gx = x + idx * group_w + group_w / 2
        vals = [("Ferramentas", item["Ferramentas"], COLORS["red"]), ("Reparações", item["Reparações"], COLORS["dark"])]
        for j, (_, val, color) in enumerate(vals):
            bh = h * float(val) / max_val
            bx = gx - bar_w - 3 + j * (bar_w + 6)
            pdf.setFillColor(_hex(color))
            pdf.rect(bx, y, bar_w, bh, stroke=0, fill=1)
            pdf.setFillColor(_hex(COLORS["dark"]))
            pdf.setFont("Helvetica", 6.5)
            pdf.drawCentredString(bx + bar_w / 2, y + bh + 5, _fmt_int(val))

        pdf.setFont("Helvetica", 7)
        pdf.setFillColor(_hex(COLORS["dark"]))
        pdf.drawCentredString(gx, y - 13, item["Grupo"])


def _draw_horizontal_bars(pdf, df: pd.DataFrame, label_col: str, value_col: str, x: float, y: float, w: float, h: float, color: str, value_fmt):
    if df.empty:
        _draw_empty(pdf, x, y + h / 2, "Sem dados")
        return

    df = df.copy().head(10).sort_values(value_col, ascending=True)
    max_val = max(float(df[value_col].max()), 1)
    row_h = h / max(len(df), 1)

    for i, row in enumerate(df.to_dict("records")):
        yy = y + i * row_h + 2
        label = str(row[label_col])[:18]
        val = float(row[value_col])
        bw = (w - 85) * val / max_val

        pdf.setFillColor(_hex(COLORS["dark"]))
        pdf.setFont("Helvetica", 6.8)
        pdf.drawRightString(x + 58, yy + row_h * 0.28, label)

        pdf.setFillColor(_hex(color))
        pdf.roundRect(x + 63, yy, bw, row_h * 0.52, 2, stroke=0, fill=1)

        pdf.setFillColor(_hex(COLORS["dark"]))
        pdf.setFont("Helvetica", 6.5)
        pdf.drawString(x + 67 + bw, yy + row_h * 0.12, value_fmt(val))


def _draw_age_bars(pdf, df: pd.DataFrame, x: float, y: float, w: float, h: float):
    if df.empty:
        _draw_empty(pdf, x, y + h / 2, "Sem dados")
        return

    df = df.copy().sort_values("idade_int (a)")
    max_val = max(float(df["Quantidade"].max()), 1)
    n = len(df)
    gap = 6
    bar_w = max(8, (w - gap * (n - 1)) / max(n, 1))

    pdf.setStrokeColor(_hex(COLORS["grid"]))
    pdf.line(x, y, x + w, y)

    for i, row in enumerate(df.to_dict("records")):
        val = float(row["Quantidade"])
        bh = h * val / max_val
        bx = x + i * (bar_w + gap)
        pdf.setFillColor(_hex(COLORS["wine"]))
        pdf.roundRect(bx, y, bar_w, bh, 2, stroke=0, fill=1)

        pdf.setFillColor(_hex(COLORS["dark"]))
        pdf.setFont("Helvetica", 6.2)
        pdf.drawCentredString(bx + bar_w / 2, y + bh + 5, _fmt_int(val))

        pdf.setFillColor(_hex(COLORS["taupe"]))
        pdf.setFont("Helvetica", 5.7)
        pdf.drawCentredString(bx + bar_w / 2, y - 11, f"{int(row['idade_int (a)'])}a")


# ========================================================
# PÁGINA DE TABELAS
# ========================================================
def _draw_tables_page(pdf: canvas.Canvas, width: float, height: float, resumo: dict):
    margin = 34
    y_top = height - 100

    left_w = 365
    right_w = width - margin * 2 - left_w - 14

    _draw_table_card(
        pdf,
        title="Resumo por grupo",
        df=resumo["resumo_grupo"].rename(columns={"_grupo": "Grupo"}),
        columns=["Grupo", "Maquinas", "Reparacoes", "Mensalidade", "Custo"],
        x=margin,
        y=y_top - 170,
        w=left_w,
        h=170,
        money_cols={"Mensalidade", "Custo"},
        int_cols={"Maquinas", "Reparacoes"},
    )

    _draw_table_card(
        pdf,
        title="Top modelos por custo",
        df=resumo["custo_modelos"],
        columns=["Modelo", "Quantidade", "Reparacoes", "Custo"],
        x=margin + left_w + 14,
        y=y_top - 260,
        w=right_w,
        h=260,
        money_cols={"Custo"},
        int_cols={"Quantidade", "Reparacoes"},
    )

    _draw_table_card(
        pdf,
        title="Top modelos por quantidade",
        df=resumo["top_modelos"],
        columns=["Modelo", "Quantidade", "Reparacoes", "Custo"],
        x=margin,
        y=y_top - 470,
        w=left_w,
        h=260,
        money_cols={"Custo"},
        int_cols={"Quantidade", "Reparacoes"},
    )


def _draw_table_card(pdf, title: str, df: pd.DataFrame, columns: list[str], x: float, y: float, w: float, h: float, money_cols: set[str] | None = None, int_cols: set[str] | None = None):
    money_cols = money_cols or set()
    int_cols = int_cols or set()

    _rounded_card(pdf, x, y, w, h)
    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x + 12, y + h - 18, title)

    columns = [col for col in columns if col in df.columns]
    if not columns:
        _draw_empty(pdf, x + 12, y + h / 2, "Sem dados")
        return

    df = df[columns].head(12).copy()

    table_x = x + 12
    table_y = y + h - 45
    table_w = w - 24
    header_h = 18
    row_h = 16
    col_w = table_w / len(columns)

    pdf.setFillColor(_hex(COLORS["dark"]))
    pdf.roundRect(table_x, table_y, table_w, header_h, 3, stroke=0, fill=1)

    pdf.setFillColor(_hex(COLORS["white"]))
    pdf.setFont("Helvetica-Bold", 6.5)
    for i, col in enumerate(columns):
        pdf.drawString(table_x + i * col_w + 5, table_y + 6, _label(col))

    pdf.setFont("Helvetica", 6.5)
    for r, row in enumerate(df.to_dict("records")):
        yy = table_y - (r + 1) * row_h
        if yy < y + 10:
            break

        if r % 2 == 0:
            pdf.setFillColor(_hex(COLORS["card"]))
            pdf.rect(table_x, yy, table_w, row_h, stroke=0, fill=1)

        pdf.setFillColor(_hex(COLORS["dark"]))
        for i, col in enumerate(columns):
            val = row.get(col, "")
            if col in money_cols:
                txt = _fmt_money(val)
            elif col in int_cols:
                txt = _fmt_int(val)
            else:
                txt = str(val)
            if len(txt) > 22:
                txt = txt[:20] + "..."
            pdf.drawString(table_x + i * col_w + 5, yy + 5, txt)


# ========================================================
# UTILITÁRIOS VISUAIS
# ========================================================
def _rounded_card(pdf: canvas.Canvas, x: float, y: float, w: float, h: float):
    pdf.setFillColor(_hex(COLORS["white"]))
    pdf.setStrokeColor(_hex(COLORS["border"]))
    pdf.roundRect(x, y, w, h, 8, stroke=1, fill=1)


def _draw_empty(pdf: canvas.Canvas, x: float, y: float, text: str):
    pdf.setFillColor(_hex(COLORS["taupe"]))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(x, y, text)


def _hex(value: str):
    from reportlab.lib.colors import HexColor
    return HexColor(value)


def _fmt_int(value) -> str:
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return "0"


def _fmt_num(value, casas: int = 2) -> str:
    try:
        txt = f"{float(value):,.{casas}f}"
        return txt.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00"


def _fmt_money(value) -> str:
    return f"R$ {_fmt_num(value, 2)}"


def _label(col: str) -> str:
    return (
        col.replace("Maquinas", "Máquinas")
        .replace("Reparacoes", "Reparações")
        .replace("Mensalidade", "Mensalidade")
    )


def _format_filters(filtros: dict) -> str:
    if not filtros:
        return ""
    partes = []
    for key, value in filtros.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, (list, tuple, set)):
            value = ", ".join(map(str, value))
        partes.append(f"{key}: {value}")
    return "Filtros - " + " | ".join(partes) if partes else ""
