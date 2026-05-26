"""
utils/charts.py
===============
Funções de criação de gráficos com Plotly.

Regras:
- Cada função retorna um objeto go.Figure (nunca chama st.plotly_chart aqui)
- Paleta de cores consistente
- Fundo sempre branco (paper_bgcolor, plot_bgcolor)
- Fonte escura (#374151)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ─── PALETA OFICIAL ───────────────────────────────────────────
COR_AZUL_ESCURO = "#1E3A8A"
COR_AZUL_CLARO  = "#3B82F6"
COR_VERDE       = "#16A34A"
COR_VERMELHO    = "#DC2626"
COR_LARANJA     = "#F59E0B"
COR_CINZA       = "#E5E7EB"
COR_TEXTO       = "#374151"
COR_FUNDO       = "#FFFFFF"
COR_FUNDO_SEC   = "#F8FAFC"

PALETA_CATEGORICA = [
    COR_AZUL_ESCURO, COR_AZUL_CLARO, COR_VERDE, COR_LARANJA,
    COR_VERMELHO, "#7C3AED", "#0891B2", "#BE185D", "#65A30D", "#9F580A"
]

# Configuração padrão de layout para todos os gráficos
LAYOUT_PADRAO = dict(
    paper_bgcolor=COR_FUNDO,
    plot_bgcolor=COR_FUNDO,
    font=dict(family="sans-serif", color=COR_TEXTO, size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        bgcolor=COR_FUNDO_SEC,
        bordercolor=COR_CINZA,
        borderwidth=1,
    ),
)


# ─────────────────────────────────────────────
# GRÁFICOS DE BARRAS
# ─────────────────────────────────────────────

def grafico_barras_horizontal(
    df: pd.DataFrame,
    coluna_x: str,
    coluna_y: str,
    titulo: str = "",
    cor: str = COR_AZUL_ESCURO,
    top_n: int = 10,
) -> go.Figure:
    """
    Gráfico de barras horizontais.
    Útil para comparações de municípios ou categorias.
    """
    df_plot = df.nlargest(top_n, coluna_x) if top_n else df
    df_plot = df_plot.sort_values(coluna_x, ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot[coluna_x],
        y=df_plot[coluna_y],
        orientation="h",
        marker_color=cor,
        text=df_plot[coluna_x],
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>{coluna_x}: %{{x}}<extra></extra>",
    ))

    fig.update_layout(
        **LAYOUT_PADRAO,
        title=dict(text=titulo, font=dict(size=14, color=COR_TEXTO)),
        xaxis=dict(showgrid=True, gridcolor=COR_CINZA, zeroline=False),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    return fig


def grafico_barras_vertical(
    df: pd.DataFrame,
    coluna_x: str,
    coluna_y: str,
    titulo: str = "",
    cor: str = COR_AZUL_ESCURO,
) -> go.Figure:
    """Gráfico de barras verticais."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[coluna_x],
        y=df[coluna_y],
        marker_color=cor,
        text=df[coluna_y],
        textposition="outside",
        hovertemplate=f"<b>%{{x}}</b><br>{coluna_y}: %{{y}}<extra></extra>",
    ))

    fig.update_layout(
        **LAYOUT_PADRAO,
        title=dict(text=titulo, font=dict(size=14, color=COR_TEXTO)),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=COR_CINZA, zeroline=False),
        bargap=0.35,
    )
    return fig


def grafico_barras_agrupadas(
    df: pd.DataFrame,
    coluna_x: str,
    colunas_y: list[str],
    nomes_series: list[str],
    cores: list[str],
    titulo: str = "",
) -> go.Figure:
    """Gráfico de barras agrupadas (múltiplas séries)."""
    fig = go.Figure()

    for coluna, nome, cor in zip(colunas_y, nomes_series, cores):
        fig.add_trace(go.Bar(
            name=nome,
            x=df[coluna_x],
            y=df[coluna],
            marker_color=cor,
            hovertemplate=f"<b>{nome}</b><br>%{{x}}: R$ %{{y:,.2f}}<extra></extra>",
        ))

    fig.update_layout(
        **LAYOUT_PADRAO,
        title=dict(text=titulo, font=dict(size=14, color=COR_TEXTO)),
        barmode="group",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=COR_CINZA, zeroline=False),
    )
    return fig


# ─────────────────────────────────────────────
# GRÁFICOS DE PIZZA / DONUT
# ─────────────────────────────────────────────

def grafico_donut(
    labels: list,
    values: list,
    titulo: str = "",
    cores: list = None,
) -> go.Figure:
    """
    Gráfico donut (rosca).
    Ideal para mostrar proporções de categorias.
    Estilo: labels externos com nome truncado + percentual, sem legenda lateral.
    """
    if cores is None:
        cores = [
            "#4A90D9", "#2ECC71", "#F39C12", "#9B59B6",
            "#E74C3C", "#1ABC9C", "#3498DB", "#E67E22",
            "#27AE60", "#8E44AD"
        ]

    # Trunca labels longos para caber externamente (máx 14 chars)
    def truncar(label: str, max_chars: int = 14) -> str:
        return label if len(label) <= max_chars else label[:max_chars] + "..."

    labels_curtos = [truncar(l) for l in labels]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels_curtos,
        values=values,
        hole=0.55,                          # buraco maior, mais limpo
        marker=dict(
            colors=cores[:len(labels)],
            line=dict(color="#FFFFFF", width=2),   # separador branco entre fatias
        ),
        textinfo="label+percent",
        textposition="outside",             # labels fora do anel
        textfont=dict(size=12, color=COR_TEXTO),
        outsidetextfont=dict(size=12),
        insidetextorientation="horizontal",
        hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>",
        pull=[0.03] * len(labels),          # leve separação entre fatias
    ))

    fig.update_layout(
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_FUNDO,
        font=dict(family="sans-serif", color=COR_TEXTO, size=12),
        margin=dict(l=60, r=60, t=50, b=40),
        title=dict(
            text=titulo,
            font=dict(size=14, color=COR_TEXTO),
            x=0,
            xanchor="left",
        ),
        showlegend=False,                   # sem legenda lateral separada
    )
    return fig


# ─────────────────────────────────────────────
# GRÁFICO DE PARETO
# ─────────────────────────────────────────────

def grafico_pareto(
    df: pd.DataFrame,
    coluna_categoria: str,
    coluna_valor: str,
    titulo: str = "",
    top_n: int = 15,
) -> go.Figure:
    """
    Gráfico de Pareto: barras + linha de acumulado %.
    Usado para mostrar concentração (ex: 80% do valor em X municípios).
    """
    df_plot = (
        df.groupby(coluna_categoria)[coluna_valor]
        .sum()
        .reset_index()
        .sort_values(coluna_valor, ascending=False)
        .head(top_n)
    )

    total = df_plot[coluna_valor].sum()
    df_plot["acumulado_pct"] = (df_plot[coluna_valor].cumsum() / total * 100).round(1)

    fig = go.Figure()

    # Barras
    fig.add_trace(go.Bar(
        x=df_plot[coluna_categoria],
        y=df_plot[coluna_valor],
        name="Valor (R$)",
        marker_color=COR_AZUL_ESCURO,
        hovertemplate="<b>%{x}</b><br>Valor: R$ %{y:,.2f}<extra></extra>",
        yaxis="y",
    ))

    # Linha acumulada
    fig.add_trace(go.Scatter(
        x=df_plot[coluna_categoria],
        y=df_plot["acumulado_pct"],
        name="Acumulado (%)",
        mode="lines+markers",
        line=dict(color=COR_LARANJA, width=2),
        marker=dict(size=6, color=COR_LARANJA),
        hovertemplate="<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>",
        yaxis="y2",
    ))

    # Linha dos 80%
    fig.add_hline(
        y=80, line_dash="dash", line_color=COR_VERMELHO,
        annotation_text="80%", yref="y2",
    )

    # Monta layout sem 'legend' do LAYOUT_PADRAO para evitar argumento duplicado
    layout = {k: v for k, v in LAYOUT_PADRAO.items() if k != "legend"}
    fig.update_layout(
        **layout,
        title=dict(text=titulo, font=dict(size=14, color=COR_TEXTO)),
        yaxis=dict(title="Valor (R$)", showgrid=True, gridcolor=COR_CINZA),
        yaxis2=dict(
            title="Acumulado (%)",
            overlaying="y",
            side="right",
            range=[0, 105],
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ─────────────────────────────────────────────
# GRÁFICO DE CONVERSÃO (FUNIL SIMPLIFICADO)
# ─────────────────────────────────────────────

def grafico_conversao(
    determinacoes: int,
    tns: int,
    autos: int,
) -> go.Figure:
    """
    Gráfico de barras comparando etapas do funil de conversão.
    """
    categorias = ["Determinações", "TNs Emitidos", "Autos de Infração"]
    valores    = [determinacoes, tns, autos]
    cores      = [COR_AZUL_ESCURO, COR_AZUL_CLARO, COR_LARANJA]

    fig = go.Figure()
    for cat, val, cor in zip(categorias, valores, cores):
        fig.add_trace(go.Bar(
            name=cat,
            x=[cat],
            y=[val],
            marker_color=cor,
            text=[val],
            textposition="outside",
        ))

    fig.update_layout(
        **LAYOUT_PADRAO,
        title=dict(text="Funil de Conversão: Determinações → TNs → Autos", font=dict(size=14)),
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor=COR_CINZA),
        xaxis=dict(showgrid=False),
    )
    return fig


# ─────────────────────────────────────────────
# GRÁFICO DE LINHA (EVOLUÇÃO ANUAL)
# ─────────────────────────────────────────────

def grafico_evolucao_anual(
    df: pd.DataFrame,
    coluna_ano: str,
    colunas_valor: list[str],
    nomes_series: list[str],
    titulo: str = "",
) -> go.Figure:
    """Gráfico de linha para evolução ao longo dos anos."""
    cores_linha = [COR_AZUL_ESCURO, COR_LARANJA, COR_VERDE]

    fig = go.Figure()
    for coluna, nome, cor in zip(colunas_valor, nomes_series, cores_linha):
        fig.add_trace(go.Scatter(
            x=df[coluna_ano],
            y=df[coluna],
            name=nome,
            mode="lines+markers",
            line=dict(color=cor, width=2),
            marker=dict(size=8, color=cor),
        ))

    fig.update_layout(
        **LAYOUT_PADRAO,
        title=dict(text=titulo, font=dict(size=14)),
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(showgrid=True, gridcolor=COR_CINZA),
    )
    return fig
