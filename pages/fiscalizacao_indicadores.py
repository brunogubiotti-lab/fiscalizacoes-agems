"""
pages/fiscalizacao_indicadores.py
===================================
Fiscalização · Indicadores gerais
Timeline do processo + KPIs situacionais + tabela + evolução por ano.

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.
    - Removido import morto de carregar_todas_as_planilhas (nunca era chamado).

CORREÇÃO v6.1:
    - Eixo X do gráfico "TNs emitidos por ano" corrigido para tipo categórico.

REDESIGN v7.0:
    - Layout 3 colunas (distribuição do esboço 2) com estilo visual do sistema atual.
    - KPIs: fundo colorido suave + ícone desbotado à direita + sublabel descritivo.
    - Fluxo regulatório: timeline compacta com badges de prazo.
    - Evolução por ano: barras horizontais CSS puras (sem Plotly) + mini-gráfico
      de distribuição de responsabilidade por etapa.
    - Tabela de fiscalizações: coluna direita, tags coloridas por tipo de objeto.
    - Alerta de resumo: estilo "bulb" amarelo igual ao restante do sistema.
    - Todos os títulos de seção seguem o padrão: ícone emoji + linha hr + subtítulo cinza.

CORREÇÕES v7.1:

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline e blocos CSS da página.

CORREÇÕES v7.1 (mantidas):
    - KPIs: revertidos para o componente original kpi_card() do sistema (utils/ui_components).
    - Fluxo regulatório: fontes aumentadas (step-title 14px, step-meta 12px, num 12px).
    - Evolução por ano: fontes aumentadas (bar-year/bar-count 14px, barras mais altas 14px).
      Barras de responsabilidade também maiores (18px) com texto legível (11px).
    - Tabela: reconstruída com st.dataframe nativo do Streamlit para evitar
      o bug de renderização de HTML bruto na célula que apareceu em produção.
      A coluna "Objeto" é simplificada (texto curto) pois st.dataframe não aceita HTML.
"""

from collections import Counter

import pandas as pd
import streamlit as st

from utils.data_loader import carregar_dados_tratados
from utils.filters import renderizar_filtros_sidebar, aplicar_todos_filtros
from utils.metrics import (
    calcular_total_tns, calcular_total_determinacoes,
    calcular_total_autos, calcular_taxa_conversao_tn_ai,
)
from utils.ui_components import (
    kpi_card, secao_titulo, sem_dados, alerta_informacao,
)

# ─────────────────────────────────────────────────────────────
# CSS — apenas os componentes novos (timeline, barras, tabela).
# Os KPIs voltam a usar kpi_card() do sistema original.
# ─────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ── Título de seção ────────────────────────────────────────── */
.sec-title {
    font-size:16px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 2px;
}
.sec-sub {
    font-size:14px;
    color: #94a3b8;
    margin: 0 0 10px;
}

/* ── Timeline de etapas ─────────────────────────────────────── */
.step-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 9px 0;
    border-bottom: 0.5px solid #f1f5f9;
}
.step-row:last-child { border-bottom: none; }

/* Círculo numerado — aumentado para 26px */
.step-num {
    min-width: 26px; height: 26px;
    border-radius: 50%;
    font-size:14px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}
.num-agems   { background:#dbeafe; color:#1d4ed8; }
.num-sanesul { background:#fef9c3; color:#a16207; }
.num-doe     { background:#f1f5f9; color:#64748b; }

/* Textos da etapa — aumentados para leitura confortável */
.step-title { font-size: 14px; color: #1e293b; font-weight: 500; line-height: 1.4; }
.step-meta  { font-size:14px; color: #94a3b8; margin-top: 2px; }

.badge-prazo {
    background:#dbeafe; color:#1d4ed8;
    font-size:14px; padding: 2px 8px;
    border-radius: 99px; font-weight: 600;
    display: inline-block; margin-left: 6px;
    vertical-align: middle;
}

/* ── Legenda de responsáveis ────────────────────────────────── */
.legend-row  { display: flex; gap: 14px; margin-bottom: 14px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size:14px; color: #64748b; }
.legend-dot  { width: 9px; height: 9px; border-radius: 50%; }

/* ── Barras horizontais de evolução ─────────────────────────── */
.bar-row { margin-bottom: 14px; }
.bar-header {
    display: flex; justify-content: space-between;
    font-size: 14px; margin-bottom: 5px;
}
.bar-year  { font-weight: 600; color: #334155; }
.bar-count { font-weight: 700; color: #1d4ed8; }
.bar-track {
    height: 14px; background: #f1f5f9;
    border-radius: 99px; overflow: hidden;
}
.bar-fill  { height: 100%; background: #1e3a8a; border-radius: 99px; }

/* ── Barras de responsabilidade ─────────────────────────────── */
.resp-section { margin-top: 18px; padding-top: 14px; border-top: 1px solid #f1f5f9; }
.resp-label {
    font-size:14px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: #94a3b8; margin-bottom: 10px;
}
.resp-row    { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.resp-name   { font-size:14px; color: #64748b; min-width: 56px; font-weight: 500; }
.resp-track  {
    flex: 1; height: 18px; background: #f1f5f9;
    border-radius: 99px; overflow: hidden;
}
.resp-fill {
    height: 100%; border-radius: 99px;
    display: flex; align-items: center;
    justify-content: flex-end; padding-right: 8px;
    min-width: 60px;
}
.fill-agems   { background:#dbeafe; }
.fill-sanesul { background:#fef9c3; }
.fill-doe     { background:#e2e8f0; }
.resp-count   { font-size:14px; font-weight: 700; }
.count-agems   { color:#1d4ed8; }
.count-sanesul { color:#a16207; }
.count-doe     { color:#64748b; }

/* ── Alerta informativo ─────────────────────────────────────── */
.alert-info {
    display: flex; align-items: flex-start; gap: 8px;
    background: #fffbeb; border: 1px solid #fde68a;
    border-left: 4px solid #f59e0b;
    border-radius: 8px; padding: 10px 14px;
    font-size:14px; color: #92400e;
    margin-top: 16px;
}
</style>
"""


# ─────────────────────────────────────────────────────────────
# Dados estáticos do fluxo regulatório
# ─────────────────────────────────────────────────────────────
_ETAPAS = [
    (1,  "Fiscalização inicial",                 "AGEMS",   "-"),
    (2,  "Formalização do Termo de Notificação", "AGEMS",   "Sem prazo legal"),
    (3,  "Manifestação da Sanesul ao TN",        "Sanesul", "20 dias"),
    (4,  "Análise da manifestação pela AGEMS",   "AGEMS",   "Sem prazo legal"),
    (5,  "Lavratura do Auto de Infração (AI)",   "AGEMS",   "Sem prazo legal"),
    (6,  "1º Recurso da Sanesul",                "Sanesul", "20 dias"),
    (7,  "Julgamento pela Câmara",               "AGEMS",   "Sem prazo legal"),
    (8,  "Publicação no DOE",                    "DOE-MS",  "-"),
    (9,  "Último recurso da Sanesul",            "Sanesul", "20 dias"),
    (10, "Decisão da Diretoria",                 "AGEMS",   "Sem prazo legal"),
    (11, "Publicação no DOE",                    "DOE-MS",  "-"),
    (12, "Emissão de boleto",                    "AGEMS",   "-"),
]

_RESP_CONTAGEM = Counter(r for _, _, r, _ in _ETAPAS)
_RESP_MAX      = max(_RESP_CONTAGEM.values())


# ─────────────────────────────────────────────────────────────
# Funções auxiliares de renderização
# ─────────────────────────────────────────────────────────────

def _secao_titulo(titulo: str, subtitulo: str = "") -> None:
    """Cabeçalho de seção: título + hr + subtítulo cinza."""
    sub_html = f'<p class="sec-sub">{subtitulo}</p>' if subtitulo else ""
    st.markdown(
        f'<p class="sec-title">{titulo}</p>{sub_html}',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<hr style='border:none;border-top:1.5px solid #e2e8f0;margin:0 0 14px'>",
        unsafe_allow_html=True,
    )


def _num_class(responsavel: str) -> str:
    """Classe CSS do círculo numerado por responsável."""
    if responsavel == "AGEMS":
        return "num-agems"
    if responsavel == "Sanesul":
        return "num-sanesul"
    return "num-doe"


def _step_html(num: int, titulo: str, responsavel: str, prazo: str) -> str:
    """
    Gera HTML de uma etapa da timeline.
    Badge de prazo só aparece quando há valor concreto (não '-' nem 'Sem prazo legal').
    """
    cls   = _num_class(responsavel)
    badge = ""
    if prazo not in ("-", "") and "Sem prazo" not in prazo:
        badge = f'<span class="badge-prazo">{prazo}</span>'

    return f"""
    <div class="step-row">
        <div class="step-num {cls}">{num}</div>
        <div>
            <div class="step-title">{titulo}{badge}</div>
            <div class="step-meta">{responsavel}</div>
        </div>
    </div>
    """


def _barra_horizontal(ano: str, qtd: int, max_qtd: int) -> str:
    """
    Barra horizontal proporcional ao valor máximo.
    Mínimo de 4% para barras pequenas ficarem visíveis.
    """
    pct = max(4, round(qtd / max_qtd * 100, 1)) if max_qtd else 0
    return f"""
    <div class="bar-row">
        <div class="bar-header">
            <span class="bar-year">{ano}</span>
            <span class="bar-count">{qtd}</span>
        </div>
        <div class="bar-track">
            <div class="bar-fill" style="width:{pct}%"></div>
        </div>
    </div>
    """


def _classificar_objeto(texto: str) -> str:
    """
    Retorna uma string curta e limpa para exibição na coluna Objeto.
    Usa st.dataframe (nativo), que não suporta HTML — por isso retorna texto puro.
    A coluna é estilizada via st.dataframe column_config.
    """
    t = texto.lower()
    if "condi" in t:
        return "Condições Gerais"
    if "denúncia" in t or "denuncia" in t or "extravasamento" in t:
        return "Denúncia"
    if "obra" in t:
        return "Obras SES"
    if "rompimento" in t:
        return "Rompimento"
    # Fallback: primeiras 25 letras do original com Title Case
    return texto[:25].title()


# ─────────────────────────────────────────────────────────────
# Carrega dados e aplica filtros
# ─────────────────────────────────────────────────────────────
filtros = renderizar_filtros_sidebar()
dados   = carregar_dados_tratados()

dados_filtrados         = aplicar_todos_filtros(dados, filtros)
fiscalizacoes_filtradas = dados_filtrados["fiscalizacoes"]
autos_filtrados         = dados_filtrados["autos_infracao"]
julgamentos_filtrados   = dados_filtrados["julgamentos"]
det_filtradas           = dados_filtrados["determinacoes"]

if fiscalizacoes_filtradas.empty:
    sem_dados()
    st.stop()

# Injeta CSS da página
st.markdown(_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# KPIs — usa kpi_card() original do sistema (revertido da v7.0)
# ─────────────────────────────────────────────────────────────
total_tns       = len(fiscalizacoes_filtradas)
total_det       = len(det_filtradas)
total_autos     = int(autos_filtrados["auto_emitido"].sum())
total_pendentes = (
    int((julgamentos_filtrados["resultado_padronizado"] == "Pendente de Análise").sum())
    if not julgamentos_filtrados.empty else 0
)

col1, col2, col3, col4 = st.columns(4)

# kpi_card() é o componente original de utils/ui_components — mantém o visual
# que o usuário já aprovava: fundo colorido + ícone + valor em destaque.
with col1:
    kpi_card("TNs emitidos", str(total_tns), "📋",
             cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A")
with col2:
    kpi_card("Determinações", str(total_det), "📌",
             cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E")
with col3:
    kpi_card("Autos de infração", str(total_autos), "⚖️",
             cor_fundo="#FEF2F2", cor_borda="#DC2626", cor_valor="#DC2626")
with col4:
    kpi_card("Processos pendentes", str(total_pendentes), "⏳",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Layout 3 colunas
#   col_fluxo  → Timeline do processo regulatório
#   col_chart  → Evolução por ano + distribuição por responsável
#   col_tabela → Lista de fiscalizações (st.dataframe nativo)
# ─────────────────────────────────────────────────────────────
col_fluxo, col_chart, col_tabela = st.columns([1.05, 1.0, 1.2])


# ── Coluna 1: Fluxo do processo ──────────────────────────────
with col_fluxo:
    _secao_titulo(
        "🔀 Fluxo do processo regulatório",
        "Etapas desde a fiscalização até a decisão final",
    )

    # Legenda de cores
    st.markdown("""
    <div class="legend-row">
        <div class="legend-item">
            <div class="legend-dot" style="background:#1d4ed8"></div>AGEMS
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background:#ca8a04"></div>Sanesul
        </div>
        <div class="legend-item">
            <div class="legend-dot" style="background:#94a3b8"></div>DOE-MS
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Todas as etapas em um único bloco HTML — evita múltiplos st.markdown
    steps_html = "".join(
        _step_html(num, titulo, responsavel, prazo)
        for num, titulo, responsavel, prazo in _ETAPAS
    )
    st.markdown(steps_html, unsafe_allow_html=True)


# ── Coluna 2: Evolução por ano + responsabilidade ────────────
with col_chart:
    _secao_titulo(
        "📈 Evolução por ano",
        "TNs emitidos · Fonte: Painel de Indicadores",
    )

    # Prepara dados anuais:
    # dropna()     → remove NaN gerados pelo left join
    # astype(int)  → garante inteiro limpo (sem "2022.0")
    # astype(str)  → converte APÓS int → "2022" sem decimais
    fiscalizacoes_ok = fiscalizacoes_filtradas.dropna(subset=["ano"]).copy()
    fiscalizacoes_ok["ano"] = fiscalizacoes_ok["ano"].astype(int).astype(str)

    por_ano = (
        fiscalizacoes_ok
        .groupby("ano")
        .size()
        .reset_index(name="qtd")
    )

    max_qtd = int(por_ano["qtd"].max()) if not por_ano.empty else 1

    # Barras horizontais CSS — sem Plotly, carregamento instantâneo
    barras_html = "".join(
        _barra_horizontal(row["ano"], int(row["qtd"]), max_qtd)
        for _, row in por_ano.iterrows()
    )
    st.markdown(barras_html, unsafe_allow_html=True)

    # Mini-gráfico: etapas por responsável + alerta de período
    # -------------------------------------------------------
    # CORREÇÃO v7.2: st.markdown escapa HTML quando a string combina
    # atributos class= e style= com hífens (ex: "fill-sanesul" style="width:X%").
    # Solução: usar st.components.v1.html() que injeta HTML puro sem escape,
    # com CSS inline (sem classes externas) para total independência.
    # -------------------------------------------------------

    # Monta dados das barras
    _RESP_DADOS = [
        ("AGEMS",   "#dbeafe", "#1d4ed8"),
        ("Sanesul", "#fef9c3", "#a16207"),
        ("DOE-MS",  "#e2e8f0", "#64748b"),
    ]

    linhas_resp = ""
    for resp, cor_bg, cor_txt in _RESP_DADOS:
        qtd = _RESP_CONTAGEM.get(resp, 0)
        # Mínimo 55% para o label de texto sempre caber na barra
        pct = max(55, round(qtd / _RESP_MAX * 90, 1))
        linhas_resp += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <div style="font-size:14px;color:#64748b;font-weight:500;min-width:56px;">{resp}</div>
            <div style="flex:1;height:18px;background:#f1f5f9;border-radius:99px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{cor_bg};border-radius:99px;
                            display:flex;align-items:center;justify-content:flex-end;padding-right:8px;">
                    <span style="font-size:14px;font-weight:700;color:{cor_txt};">{qtd} etapas</span>
                </div>
            </div>
        </div>
        """

    # Alerta de período
    alerta_html = ""
    if not fiscalizacoes_ok.empty:
        ano_min = fiscalizacoes_ok["ano"].min()
        ano_max = fiscalizacoes_ok["ano"].max()
        alerta_html = f"""
        <div style="display:flex;align-items:flex-start;gap:8px;background:#fffbeb;
                    border:1px solid #fde68a;border-left:4px solid #f59e0b;
                    border-radius:8px;padding:10px 14px;font-size:14px;color:#92400e;margin-top:16px;">
            💡 Período {ano_min} a {ano_max} · {total_tns} termos emitidos no total
        </div>
        """

    # HTML completo do bloco — injetado via components.v1.html para evitar escape
    import streamlit.components.v1 as components
    components.html(f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:0.08em;color:#94a3b8;margin-bottom:10px;">
            Etapas por responsável
        </div>
        {linhas_resp}
        {alerta_html}
    </div>
    """, height=160)


# ── Coluna 3: Lista de fiscalizações ─────────────────────────
with col_tabela:
    _secao_titulo(
        "📋 Lista de fiscalizações",
        "Todos os TNs no período filtrado",
    )

    # Monta DataFrame de exibição
    # _classificar_objeto() retorna texto puro (sem HTML) pois st.dataframe
    # não renderiza HTML nas células — isso corrige o bug da v7.0.
    df_fisc = fiscalizacoes_filtradas[
        ["termo", "ano", "municipio", "regional", "objeto"]
    ].copy()

    # Converte "ano" para inteiro seguro (sem NaN → string "—")
    df_fisc["ano"] = df_fisc["ano"].apply(
        lambda v: str(int(v)) if pd.notna(v) else "—"
    )

    # Classifica objeto em categorias curtas e legíveis
    df_fisc["objeto"] = df_fisc["objeto"].astype(str).apply(_classificar_objeto)

    # Renomeia para exibição
    df_fisc.columns = ["Termo", "Ano", "Município", "Regional", "Objeto"]

    # st.dataframe nativo — sem risco de HTML bruto aparecer como texto
    # height=490 para preencher a altura das outras colunas
    st.dataframe(
        df_fisc,
        use_container_width=True,
        height=490,
        hide_index=True,
    )
