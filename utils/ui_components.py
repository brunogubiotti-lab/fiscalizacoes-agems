"""
utils/ui_components.py
======================
Componentes visuais reutilizáveis para o dashboard.

Inclui:
- KPI Cards com HTML/CSS
- CSS Global (light mode forçado)
- Helpers de exibição de tabelas

CORREÇÃO v6.1:
    Bloco CSS de remoção de <hr> na sidebar expandido com 4 camadas
    de seletores para eliminar a linha duplicada que aparecia entre
    o grupo "Outros" (Lead time) e o label "FILTROS".

    Causa raiz: o Streamlit injeta um <hr> nativo após o bloco
    stSidebarNav que não era coberto pelos seletores anteriores
    em certas versões/builds do Streamlit.

    Solução: seletores em cascata crescente (Abordagens 1–4) que
    cobrem <hr> em qualquer posição dentro da sidebar, além de
    divs com classes "separator"/"divider".

    A linha visível antes dos filtros (em filters.py) é um <div>
    com border-top inline — NÃO é afetada por estes seletores.
"""

import streamlit as st
import pandas as pd
import io


# ─────────────────────────────────────────────
# CSS GLOBAL (LIGHT MODE FORÇADO)
# ─────────────────────────────────────────────

def injetar_css_global():
    """
    Injeta CSS para garantir o tema light em toda a aplicação.
    Sobrescreve qualquer herança do tema dark do Streamlit.
    """
    st.markdown("""
    <style>
        /* ── Fundo geral ── */
        body, .stApp, [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF !important;
            color: #111827 !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background-color: #F8FAFC !important;
            border-right: 1px solid #E5E7EB;
        }
        [data-testid="stSidebar"] * {
            color: #111827 !important;
        }

        /* ── Header do Streamlit ── */
        header[data-testid="stHeader"] {
            background-color: #FFFFFF !important;
        }

        /* ── Métricas padrão do Streamlit ── */
        [data-testid="metric-container"] {
            background-color: #F8FAFC !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 10px !important;
            padding: 16px !important;
        }
        [data-testid="metric-container"] label {
            color: #6B7280 !important;
        }
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #111827 !important;
        }

        /* ── Tabelas ── */
        .dataframe {
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
        }
        .dataframe th {
            background-color: #1E3A8A !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        .dataframe td {
            color: #374151 !important;
            background-color: #FFFFFF !important;
        }
        .dataframe tr:nth-child(even) td {
            background-color: #F8FAFC !important;
        }

        /* ── Selectbox / Multiselect ── */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #1E3A8A !important;
        }

        /* força texto branco em TODOS os filhos */
        .stMultiSelect [data-baseweb="tag"] * {
            color: #FFFFFF !important;
        }

        /* garante que spans internos não herdem cor preta */
        .stMultiSelect [data-baseweb="tag"] span {
            color: #FFFFFF !important;
        }

        /* botão de remover (X) */
        .stMultiSelect [data-baseweb="tag"] svg {
            fill: #FFFFFF !important;
        }

        /* ── Abas (tabs) ── */
        [data-testid="stTabs"] button {
            color: #374151 !important;
            font-weight: 500;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: #1E3A8A !important;
            border-bottom-color: #1E3A8A !important;
            font-weight: 700;
        }

        /* ── Separadores gerais (fora da sidebar) ── */
        hr {
            border-color: #E5E7EB !important;
        }

        /* ══════════════════════════════════════════════════════════
           REMOVE LINHAS <hr> AUTOMÁTICAS DA SIDEBAR — v6.1
           ══════════════════════════════════════════════════════════

           O Streamlit injeta um <hr> nativo após o bloco de
           navegação (stSidebarNav), criando uma segunda linha
           separadora entre "Lead time" e o label "FILTROS".

           A linha DESEJADA vem de filters.py: é um <div> com
           border-top inline — NÃO é um <hr> — logo não é afetada.

           Usamos 4 abordagens em cascata para cobrir todas as
           versões/builds do Streamlit sem quebrar a linha do filtro.
        ══════════════════════════════════════════════════════════ */

        /* Abordagem 1 — <hr> em qualquer posição dentro da sidebar
           (seletor amplo, cobre a maioria dos casos)              */
        [data-testid="stSidebar"] hr {
            display: none !important;
            height: 0 !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            visibility: hidden !important;
        }

        /* Abordagem 2 — <hr> dentro dos containers diretos
           (stSidebarContent é o wrapper interno em Streamlit ≥1.30) */
        [data-testid="stSidebar"] > div hr,
        [data-testid="stSidebar"] section hr,
        [data-testid="stSidebarContent"] hr {
            display: none !important;
            height: 0 !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            visibility: hidden !important;
        }

        /* Abordagem 3 — <hr> irmão ou descendente de irmão do bloco
           de navegação (cobre o <hr> injetado logo após stSidebarNav) */
        [data-testid="stSidebarNav"] ~ * hr,
        [data-testid="stSidebarNav"] + hr,
        [data-testid="stSidebarNav"] ~ hr,
        [data-testid="stSidebarNavItems"] + div hr,
        [data-testid="stSidebarNav"] ~ div hr {
            display: none !important;
            height: 0 !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            visibility: hidden !important;
        }

        /* Abordagem 4 — divs com classes "separator" ou "divider"
           (Streamlit moderno às vezes usa div com border-top
           em vez de <hr> — zeramos borda e espaço)               */
        [data-testid="stSidebarNav"] + div [class*="separator"],
        [data-testid="stSidebarNav"] + div [class*="divider"],
        [data-testid="stSidebar"] [class*="separator"],
        [data-testid="stSidebar"] [class*="divider"] {
            display: none !important;
            height: 0 !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #F8FAFC; }
        ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }

        /* ── Botões ── */
        .stButton > button {
            background-color: #1E3A8A !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 6px !important;
        }
        .stButton > button:hover {
            background-color: #3B82F6 !important;
        }

        /* ══════════════════════════════════════════════
           SIDEBAR — Opção 1 · Cards com borda
           ══════════════════════════════════════════════

           Cada item de navegação vira um "card" com borda sutil
           e bordas arredondadas (8px).
           Item ativo: fundo navy #1E3A8A, texto branco.
           Hover: fundo azul claro #EFF6FF, borda azul.
           Filtros (expanders): agrupados numa caixinha com borda
           própria, separada da navegação por divisor visual.

           Seletores principais:
           [data-testid="stSidebarNavLink"]              itens nav
           [aria-current="page"]                         item ativo
           [data-testid="stSidebarNavSeparator"]         labels de grupo
           [data-testid="stExpander"] na sidebar         filtros
        */

        /* Item de navegação: card com borda */
        [data-testid="stSidebarNavLink"] {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 7px 10px !important;
            margin: 2px 8px !important;
            border-radius: 8px !important;
            border: 1px solid #E5E7EB !important;
            background-color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 400 !important;
            color: #374151 !important;
            text-decoration: none !important;
            transition: background-color 0.15s, border-color 0.15s !important;
        }

        /* Hover: borda azul + fundo azul claro */
        [data-testid="stSidebarNavLink"]:hover {
            background-color: #EFF6FF !important;
            border-color: #BFDBFE !important;
            color: #1E3A8A !important;
        }

        /* Item ativo: navy sólido */
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background-color: #1E3A8A !important;
            border-color: #1E3A8A !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Texto e ícone dentro do item ativo: branco */
        [data-testid="stSidebarNavLink"][aria-current="page"] * {
            color: #FFFFFF !important;
        }

        /* Labels de grupo (ex: "Fiscalização", "Outros") */
        [data-testid="stSidebarNavSeparator"] {
            margin: 10px 8px 4px !important;
            padding: 4px 4px 0 !important;
            font-size: 10px !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: #9CA3AF !important;
            /* border-top removido — linha aparecia após o último grupo
               (Lead time) gerando separador duplicado antes dos filtros.
               A separação visual entre grupos é dada pelo margin-top.
               A linha única antes dos filtros vem do filters.py. */
        }

        /* Zona de filtros: cada expander vira uma caixinha */
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
            margin: 2px 8px !important;
            overflow: hidden !important;
        }

        /* Cabeçalho clicável do expander */
        [data-testid="stSidebar"] [data-testid="stExpander"] summary,
        [data-testid="stSidebar"] [data-testid="stExpander"] > div:first-child {
            background-color: #F8FAFC !important;
            padding: 7px 12px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            color: #374151 !important;
            border-radius: 8px 8px 0 0 !important;
        }

    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# KPI CARD
# ─────────────────────────────────────────────

def kpi_card(
    titulo: str,
    valor: str,
    icone: str = "📊",
    cor_fundo: str = "#EFF6FF",
    cor_borda: str = "#BFDBFE",
    cor_valor: str = "#1E3A8A",
    subtitulo: str = "",
):
    """
    Renderiza um card de KPI com HTML customizado.

    Args:
        titulo:    Rótulo do KPI (ex: "Total de TNs")
        valor:     Valor exibido em destaque (ex: "98")
        icone:     Emoji ou ícone (ex: "📋")
        cor_fundo: Cor de fundo do card
        cor_borda: Cor da borda esquerda
        cor_valor: Cor do texto do valor
        subtitulo: Texto secundário opcional
    """
    subtitulo_html = (
        f'<p style="margin:3px 0 0 0;font-size:11px;color:#9CA3AF;">{subtitulo}</p>'
        if subtitulo else ""
    )
    font_size_valor = "18px" if len(valor) > 10 else "22px"
    html = (
        f'<div style="background-color:{cor_fundo};border-left:4px solid {cor_borda};'
        f'border-radius:10px;padding:12px 14px;margin-bottom:8px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.08);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div style="min-width:0;flex:1;">'
        f'<p style="margin:0;font-size:11px;font-weight:600;color:#6B7280;'
        f'text-transform:uppercase;letter-spacing:0.04em;white-space:nowrap;'
        f'overflow:hidden;text-overflow:ellipsis;">{titulo}</p>'
        f'<p style="margin:3px 0 0 0;font-size:{font_size_valor};font-weight:700;'
        f'color:{cor_valor};line-height:1.2;word-break:break-word;">{valor}</p>'
        f'{subtitulo_html}'
        f'</div>'
        f'<div style="font-size:32px;opacity:0.7;">{icone}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEÇÃO COM TÍTULO
# ─────────────────────────────────────────────

def secao_titulo(titulo: str, subtitulo: str = ""):
    """Renderiza um título de seção estilizado."""
    sub_html = (
        f'<p style="color:#6B7280;font-size:13px;margin:4px 0 0 0;">{subtitulo}</p>'
        if subtitulo else ""
    )
    html = (
        f'<div style="margin:24px 0 12px 0;">'
        f'<h3 style="color:#1E3A8A;margin:0;font-size:18px;font-weight:700;'
        f'border-bottom:2px solid #E5E7EB;padding-bottom:8px;">{titulo}</h3>'
        f'{sub_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABELA COM EXPORTAÇÃO
# ─────────────────────────────────────────────

def tabela_com_exportacao(
    df: pd.DataFrame,
    nome_arquivo: str = "dados",
    altura: int = 400,
    colunas_moeda: list[str] = None,
):
    """
    Exibe uma tabela formatada com botão de exportação para Excel.

    Args:
        df:            DataFrame a exibir
        nome_arquivo:  Nome base do arquivo Excel para download
        altura:        Altura da tabela em pixels
        colunas_moeda: Lista de colunas para formatar como R$
    """
    # Formata colunas de moeda se especificadas
    df_exibicao = df.copy()
    if colunas_moeda:
        for col in colunas_moeda:
            if col in df_exibicao.columns:
                df_exibicao[col] = df_exibicao[col].apply(
                    lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    if pd.notna(v) else "-"
                )

    # Exibe a tabela
    st.dataframe(df_exibicao, use_container_width=True, height=altura)

    # Botão de download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")

    st.download_button(
        label="📥 Exportar para Excel",
        data=buffer.getvalue(),
        file_name=f"{nome_arquivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ─────────────────────────────────────────────
# ALERTA / DESTAQUE
# ─────────────────────────────────────────────

def alerta_informacao(mensagem: str):
    """Exibe um bloco de informação estilizado."""
    st.markdown(f"""
    <div style="
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #1E40AF;
        font-size: 14px;
    ">💡 {mensagem}</div>
    """, unsafe_allow_html=True)


def alerta_atencao(mensagem: str):
    """Exibe um bloco de atenção/alerta estilizado."""
    st.markdown(f"""
    <div style="
        background-color: #FFFBEB;
        border-left: 4px solid #F59E0B;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        color: #92400E;
        font-size: 14px;
    ">⚠️ {mensagem}</div>
    """, unsafe_allow_html=True)


def sem_dados():
    """Exibe mensagem quando não há dados para o filtro selecionado."""
    st.markdown("""
    <div style="
        background-color: #F9FAFB;
        border: 2px dashed #E5E7EB;
        border-radius: 10px;
        padding: 40px;
        text-align: center;
        color: #9CA3AF;
    ">
        <p style="font-size: 32px; margin: 0;">📭</p>
        <p style="font-size: 16px; margin: 8px 0 0 0;">Nenhum dado encontrado para os filtros selecionados.</p>
        <p style="font-size: 13px; margin: 4px 0 0 0;">Tente ampliar os filtros na barra lateral.</p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BANNER WIP
# ─────────────────────────────────────────────

def banner_wip(mensagem: str = ""):
    """
    Exibe o banner padrão de 'seção em construção'.

    Usado em todas as páginas e sub-abas ainda não implementadas.
    O padrão visual é idêntico ao do app.py e ao do colega de referência.

    Args:
        mensagem: Texto descritivo opcional exibido abaixo do título padrão.
                  Se vazio, usa a mensagem genérica de prazo.

    Exemplo de uso:
        from utils.ui_components import banner_wip
        banner_wip("Este módulo aguarda os dados de enquadramento legal.")
    """
    # Mensagem padrão se nenhuma for fornecida
    corpo = mensagem or (
        "Em breve: esta seção será implementada com os dados e "
        "visualizações planejados para este módulo."
    )
    st.markdown(f"""
    <div style="
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 24px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    ">
        <div style="font-size: 20px; line-height: 1; flex-shrink: 0;">🚧</div>
        <div>
            <p style="margin: 0 0 4px 0; font-weight: 600; color: #92400E; font-size: 14px;">
                Esta seção está em construção
            </p>
            <p style="margin: 0; color: #92400E; font-size: 13px; line-height: 1.6;">
                {corpo}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
