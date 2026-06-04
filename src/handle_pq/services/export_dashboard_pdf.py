from datetime import datetime
from math import cos, radians, sin

import pandas as pd


COLORS = {
    'red': (210, 5, 30),
    'beige': (215, 206, 189),
    'dark': (82, 79, 83),
    'taupe': (136, 127, 110),
    'wine': (103, 28, 62),
    'bg': (245, 243, 239),
    'card': (240, 242, 246),
}

CHART_PALETTE = [
    COLORS['red'],
    COLORS['dark'],
    COLORS['taupe'],
    COLORS['wine'],
    COLORS['beige'],
    COLORS['bg'],
]


def gerar_dashboard_pdf(df, filtros=None):
    filtros = filtros or {}
    df = df.copy()

    kpis = _criar_kpis(df)
    resumo_grupo = _criar_resumo_grupo(df)
    top_modelos = _criar_top_modelos(df)

    pdf = _SimplePDF()
    pdf.add_page()
    _desenhar_cabecalho(pdf, filtros)
    _desenhar_kpis(pdf, kpis)
    _desenhar_graficos_dashboard(pdf, df, top_modelos)

    pdf.add_page()
    y = 720
    y = _desenhar_tabela(
        pdf,
        'Resumo por grupo',
        ['Grupo', 'Maquinas', 'Reparacoes'],
        resumo_grupo,
        y
    )
    _desenhar_tabela(
        pdf,
        'Maquinas por modelo',
        ['Modelo', 'Quantidade'],
        top_modelos,
        y - 30
    )

    return pdf.render()


def _desenhar_graficos_dashboard(pdf, df, top_modelos):
    grupo_pizza = _criar_dados_pizza_grupo(df)
    grupo_barras = _criar_dados_barras_grupo(df)
    modelo_pizza = [
        (row[0], row[1], CHART_PALETTE[idx % len(CHART_PALETTE)])
        for idx, row in enumerate(top_modelos[:8])
    ]

    _desenhar_pizza(
        pdf,
        'Maquinas por grupo',
        grupo_pizza,
        center_x=135,
        center_y=490,
        radius=58,
        legend_x=215,
        legend_y=530
    )
    _desenhar_barras_duplas(
        pdf,
        'Ferramentas e reparacoes por grupo',
        grupo_barras,
        x=330,
        y=395,
        width=220,
        height=135
    )
    _desenhar_pizza(
        pdf,
        'Maquinas por modelo',
        modelo_pizza,
        center_x=150,
        center_y=245,
        radius=70,
        legend_x=255,
        legend_y=305
    )


def _criar_dados_pizza_grupo(df):
    if 'Grupo' not in df.columns:
        return []

    grupo = df['Grupo'].astype(str).str.lower().str.strip()
    return [
        ('Compradas', int(grupo.eq('comprado').sum()), COLORS['red']),
        ('Frota', int(grupo.eq('frota').sum()), COLORS['dark']),
    ]


def _criar_dados_barras_grupo(df):
    if 'Grupo' not in df.columns:
        return []

    if 'Quantidade de reparos' not in df.columns:
        df = df.copy()
        df['Quantidade de reparos'] = 0

    grupo_normalizado = df['Grupo'].astype(str).str.lower().str.strip()
    dados = []

    for valor_original, label in [('comprado', 'Compradas'), ('frota', 'Frota')]:
        grupo_df = df[grupo_normalizado.eq(valor_original)]
        dados.append({
            'grupo': label,
            'ferramentas': len(grupo_df),
            'reparacoes': _somar_coluna(grupo_df, 'Quantidade de reparos'),
        })

    return dados


def _criar_kpis(df):
    return [
        ('Qtd', len(df)),
        ('Mensal', _formatar_moeda(_somar_coluna(df, 'Mensalidade c/Imp'))),
        ('Qtd. Reparacoes', _somar_coluna(df, 'Quantidade de reparos')),
        ('Custo Reparacoes', _formatar_moeda(_somar_coluna(df, 'Custo de Reparo'))),
    ]


def _criar_resumo_grupo(df):
    if 'Grupo' not in df.columns:
        return []

    if 'Quantidade de reparos' not in df.columns:
        df['Quantidade de reparos'] = 0

    resumo = (
        df.assign(_grupo=df['Grupo'].astype(str).str.strip())
        .groupby('_grupo', dropna=False)
        .agg(
            Maquinas=('Grupo', 'size'),
            Reparacoes=('Quantidade de reparos', 'sum')
        )
        .reset_index()
    )
    resumo = resumo[resumo['_grupo'].ne('')]

    return [
        [row['_grupo'], int(row['Maquinas']), _formatar_numero(row['Reparacoes'])]
        for _, row in resumo.iterrows()
    ]


def _criar_top_modelos(df, limite=12):
    if 'Modelo' not in df.columns:
        return []

    modelos = (
        df['Modelo']
        .astype(str)
        .str.strip()
        .replace('', pd.NA)
        .dropna()
        .value_counts()
        .head(limite)
        .reset_index()
    )
    modelos.columns = ['Modelo', 'Quantidade']

    return [
        [row['Modelo'], int(row['Quantidade'])]
        for _, row in modelos.iterrows()
    ]


def _somar_coluna(df, coluna):
    if coluna not in df.columns:
        return 0

    return pd.to_numeric(df[coluna], errors='coerce').fillna(0).sum()


def _formatar_numero(valor):
    if pd.isna(valor):
        return '0'

    if float(valor).is_integer():
        return str(int(valor))

    return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _formatar_moeda(valor):
    return f'R$ {_formatar_numero(valor)}'


def _desenhar_cabecalho(pdf, filtros):
    pdf.set_fill_color(*COLORS['red'])
    pdf.rect(0, 792 - 76, 612, 76, fill=True)
    pdf.set_text_color(255, 255, 255)
    pdf.text(40, 742, 'Analise do Parque de Maquinas', size=20, bold=True)
    pdf.text(40, 720, f'Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', size=9)

    if filtros:
        filtros_texto = ' | '.join(
            f'{chave}: {valor}'
            for chave, valor in filtros.items()
            if valor
        )
        pdf.text(40, 704, filtros_texto[:120], size=8)

    pdf.set_text_color(*COLORS['dark'])


def _desenhar_kpis(pdf, kpis):
    card_w = 126
    card_h = 78
    gap = 12
    x = 40
    y = 625

    for titulo, valor in kpis:
        pdf.set_fill_color(*COLORS['card'])
        pdf.rect(x, y, card_w, card_h, fill=True)
        pdf.set_fill_color(*COLORS['red'])
        pdf.rect(x, y, 5, card_h, fill=True)
        pdf.set_text_color(*COLORS['taupe'])
        pdf.text(x + 14, y + card_h - 24, str(titulo).upper(), size=8, bold=True)
        pdf.set_text_color(*COLORS['dark'])
        pdf.text(x + 14, y + 28, str(valor), size=16, bold=True)
        x += card_w + gap


def _desenhar_pizza(pdf, titulo, dados, center_x, center_y, radius, legend_x, legend_y):
    dados = [item for item in dados if item[1] > 0]

    pdf.set_text_color(*COLORS['wine'])
    pdf.text(center_x - radius, center_y + radius + 28, titulo, size=13, bold=True)

    if not dados:
        pdf.set_text_color(*COLORS['taupe'])
        pdf.text(center_x - 35, center_y, 'Sem dados', size=10)
        return

    total = sum(valor for _, valor, _ in dados)
    start_angle = 90

    for label, valor, color in dados:
        angle = 360 * valor / total
        end_angle = start_angle - angle
        points = [(center_x, center_y)]
        steps = max(8, int(abs(angle) / 8))

        for step in range(steps + 1):
            current = start_angle + (end_angle - start_angle) * step / steps
            points.append((
                center_x + radius * cos(radians(current)),
                center_y + radius * sin(radians(current))
            ))

        pdf.set_fill_color(*color)
        pdf.polygon(points, fill=True)
        start_angle = end_angle

    item_y = legend_y
    pdf.set_text_color(*COLORS['dark'])
    for label, valor, color in dados:
        percent = valor / total * 100
        pdf.set_fill_color(*color)
        pdf.rect(legend_x, item_y, 9, 9, fill=True)
        pdf.text(legend_x + 15, item_y + 1, f'{label}: {valor} ({percent:.1f}%)', size=8)
        item_y -= 16


def _desenhar_barras_duplas(pdf, titulo, dados, x, y, width, height):
    pdf.set_text_color(*COLORS['wine'])
    pdf.text(x, y + height + 35, titulo, size=13, bold=True)

    if not dados:
        pdf.set_text_color(*COLORS['taupe'])
        pdf.text(x, y + height / 2, 'Sem dados', size=10)
        return

    max_valor = max(
        max(item['ferramentas'], item['reparacoes'])
        for item in dados
    ) or 1
    chart_h = height - 35
    chart_y = y + 26
    group_w = width / len(dados)
    bar_w = 22

    pdf.set_fill_color(*COLORS['taupe'])
    pdf.rect(x, chart_y, width, 1, fill=True)

    for idx, item in enumerate(dados):
        group_x = x + idx * group_w + 22
        ferramentas_h = chart_h * item['ferramentas'] / max_valor
        reparacoes_h = chart_h * item['reparacoes'] / max_valor

        pdf.set_fill_color(*COLORS['red'])
        pdf.rect(group_x, chart_y, bar_w, ferramentas_h, fill=True)
        pdf.set_text_color(*COLORS['dark'])
        pdf.text(group_x + 2, chart_y + ferramentas_h + 5, _formatar_numero(item['ferramentas']), size=7)

        pdf.set_fill_color(*COLORS['dark'])
        pdf.rect(group_x + bar_w + 6, chart_y, bar_w, reparacoes_h, fill=True)
        pdf.set_text_color(*COLORS['dark'])
        pdf.text(group_x + bar_w + 8, chart_y + reparacoes_h + 5, _formatar_numero(item['reparacoes']), size=7)

        pdf.text(group_x, y + 4, item['grupo'], size=8)

    legend_y = y + height + 12
    pdf.set_fill_color(*COLORS['red'])
    pdf.rect(x, legend_y, 9, 9, fill=True)
    pdf.set_text_color(*COLORS['dark'])
    pdf.text(x + 14, legend_y + 1, 'Ferramentas', size=8)
    pdf.set_fill_color(*COLORS['dark'])
    pdf.rect(x + 90, legend_y, 9, 9, fill=True)
    pdf.text(x + 104, legend_y + 1, 'Reparacoes', size=8)


def _desenhar_tabela(pdf, titulo, colunas, linhas, y):
    pdf.set_text_color(*COLORS['wine'])
    pdf.text(40, y, titulo, size=14, bold=True)

    y -= 26
    col_widths = [260, 120, 120][:len(colunas)]
    x = 40

    pdf.set_fill_color(*COLORS['dark'])
    pdf.rect(x, y, sum(col_widths), 22, fill=True)
    pdf.set_text_color(255, 255, 255)

    col_x = x
    for idx, coluna in enumerate(colunas):
        pdf.text(col_x + 8, y + 7, coluna, size=8, bold=True)
        col_x += col_widths[idx]

    y -= 22
    pdf.set_text_color(*COLORS['dark'])

    for i, linha in enumerate(linhas):
        if y < 70:
            pdf.add_page()
            y = 720

        if i % 2 == 0:
            pdf.set_fill_color(*COLORS['card'])
            pdf.rect(x, y, sum(col_widths), 20, fill=True)

        col_x = x
        for idx, valor in enumerate(linha):
            texto = str(valor)
            if idx == 0 and len(texto) > 44:
                texto = f'{texto[:41]}...'
            pdf.text(col_x + 8, y + 6, texto, size=8)
            col_x += col_widths[idx]

        y -= 20

    return y


class _SimplePDF:
    def __init__(self):
        self.pages = []
        self.commands = []
        self.text_color = COLORS['dark']
        self.fill_color = COLORS['card']

    def add_page(self):
        if self.commands:
            self.pages.append('\n'.join(self.commands))
        self.commands = []

    def set_text_color(self, r, g, b):
        self.text_color = (r, g, b)

    def set_fill_color(self, r, g, b):
        self.fill_color = (r, g, b)

    def text(self, x, y, text, size=10, bold=False):
        r, g, b = _rgb(self.text_color)
        font = '/F2' if bold else '/F1'
        safe_text = _escape_pdf_text(str(text))
        self.commands.append(
            f'BT {r} {g} {b} rg {font} {size} Tf {x} {y} Td ({safe_text}) Tj ET'
        )

    def rect(self, x, y, w, h, fill=False):
        r, g, b = _rgb(self.fill_color)
        operator = 'f' if fill else 'S'
        self.commands.append(f'{r} {g} {b} rg {x} {y} {w} {h} re {operator}')

    def polygon(self, points, fill=False):
        if not points:
            return

        r, g, b = _rgb(self.fill_color)
        operator = 'f' if fill else 'S'
        start_x, start_y = points[0]
        path = [f'{r} {g} {b} rg {start_x:.2f} {start_y:.2f} m']

        for point_x, point_y in points[1:]:
            path.append(f'{point_x:.2f} {point_y:.2f} l')

        path.append(f'h {operator}')
        self.commands.append(' '.join(path))

    def render(self):
        if self.commands:
            self.pages.append('\n'.join(self.commands))
            self.commands = []

        objects = [
            '<< /Type /Catalog /Pages 2 0 R >>',
            None,
            '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
            '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>',
        ]
        page_refs = []

        for content in self.pages:
            content_obj_id = len(objects) + 1
            objects.append(f'<< /Length {len(content.encode("latin-1", errors="replace"))} >>\nstream\n{content}\nendstream')

            page_obj_id = len(objects) + 1
            page_refs.append(f'{page_obj_id} 0 R')
            objects.append(
                '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
                '/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> '
                f'/Contents {content_obj_id} 0 R >>'
            )

        objects[1] = f'<< /Type /Pages /Kids [{" ".join(page_refs)}] /Count {len(page_refs)} >>'

        pdf = ['%PDF-1.4\n']
        offsets = [0]
        for idx, obj in enumerate(objects, start=1):
            offsets.append(sum(len(part.encode('latin-1', errors='replace')) for part in pdf))
            pdf.append(f'{idx} 0 obj\n{obj}\nendobj\n')

        xref_offset = sum(len(part.encode('latin-1', errors='replace')) for part in pdf)
        pdf.append(f'xref\n0 {len(objects) + 1}\n')
        pdf.append('0000000000 65535 f \n')
        for offset in offsets[1:]:
            pdf.append(f'{offset:010d} 00000 n \n')
        pdf.append(
            'trailer\n'
            f'<< /Size {len(objects) + 1} /Root 1 0 R >>\n'
            'startxref\n'
            f'{xref_offset}\n'
            '%%EOF'
        )

        return ''.join(pdf).encode('latin-1', errors='replace')


def _rgb(color):
    return tuple(round(channel / 255, 4) for channel in color)


def _escape_pdf_text(text):
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
