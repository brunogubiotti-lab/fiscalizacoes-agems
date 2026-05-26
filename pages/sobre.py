"""
pages/sobre.py
===============
Página inicial: Sobre o sistema.
Banner wip + cards de acesso rápido para todas as sub-páginas do sistema,
organizados por grupo com título de seção.

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline (components.html),
      blocos f-string e CSS embarcado em st.markdown.
    - Nenhuma lógica de dados ou layout foi alterada.
"""

import streamlit as st
from utils.ui_components import injetar_css_global, banner_wip
from utils.filters import renderizar_filtros_sidebar

injetar_css_global()
renderizar_filtros_sidebar()

banner_wip(
    "Em breve: apresentação do sistema, fontes de dados, metodologia e "
    "contatos da equipe de fiscalização AGEMS."
)

# ── Helpers ───────────────────────────────────────────────────────
VERDE_BG, VERDE_C = "#D1FAE5", "#065F46"
AMBER_BG, AMBER_C = "#FEF3C7", "#92400E"
GRAY_BG,  GRAY_C  = "#F3F4F6", "#6B7280"

def _secao(titulo):
    st.markdown(
        f'<p style="font-size:14px;font-weight:600;color:#6B7280;'
        f'text-transform:uppercase;letter-spacing:.06em;'
        f'margin:20px 0 8px 0;border-bottom:1px solid #E5E7EB;'
        f'padding-bottom:6px;">{titulo}</p>',
        unsafe_allow_html=True,
    )

def _card(icone, titulo, descricao, status, status_cor, status_bg):
    return (
        f'<div style="border:1px solid #E5E7EB;border-radius:10px;'
        f'padding:16px 18px 14px;margin-bottom:8px;min-height:160px;">'
        f'<div style="font-size:22px;margin-bottom:8px;">{icone}</div>'
        f'<p style="font-weight:600;font-size:16px;color:#111827;margin:0 0 4px;">{titulo}</p>'
        f'<p style="font-size:14px;color:#6B7280;margin:0 0 10px;line-height:1.6;">{descricao}</p>'
        f'<span style="font-size:14px;padding:2px 8px;border-radius:99px;'
        f'background-color:{status_bg};color:{status_cor};font-size:14px;">{status}</span>'
        f'</div>'
    )

# ── GRUPO: Fiscalização ───────────────────────────────────────────
_secao("Fiscalização")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(_card(
        "📊", "Indicadores gerais",
        "Timeline completa do ciclo regulatório (TN → AI → Câmara → Diretoria). "
        "KPIs de situação atual: total de TNs, determinações, autos emitidos e processos pendentes.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/fiscalizacao_indicadores.py", label="Abrir →", use_container_width=True)

with c2:
    st.markdown(_card(
        "📋", "Termos de Notificação",
        "Volume de TNs e determinações por município, categoria e setor responsável. "
        "Inclui tabela detalhada com termo, determinação e constatação vinculada.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/fiscalizacao_termos.py", label="Abrir →", use_container_width=True)

with c3:
    st.markdown(_card(
        "⚖️", "Autos de Infração",
        "Taxa de conversão TN→AI, valor preliminar total e análise de risco regulatório "
        "por município. Análise de recorrência nas constatações por nuvem de palavras.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/fiscalizacao_autos.py", label="Abrir →", use_container_width=True)

with c4:
    st.markdown(_card(
        "📁", "Acervo de documentos",
        "Árvore navegável por município com link direto para a pasta do Google Drive. "
        "Estrutura padrão: RFP/RFE → Respostas ao TN, AM, AI, Defesa, Julgamento, Boleto.",
        "em construção", AMBER_C, AMBER_BG), unsafe_allow_html=True)
    st.page_link("pages/fiscalizacao_acervo.py", label="Abrir →", use_container_width=True)

# ── GRUPO: Painel jurídico ────────────────────────────────────────
_secao("Painel jurídico")
c5, c6, c7, c8 = st.columns(4)

with c5:
    st.markdown(_card(
        "🏛️", "Decisões: câmara",
        "Resultados dos julgamentos da câmara de 1º recurso: acatadas, não acatadas "
        "e pendentes. Distribuição por ano e categorias com maior índice de rejeição.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/juridico_camara.py", label="Abrir →", use_container_width=True)

with c6:
    st.markdown(_card(
        "🎯", "Decisões: diretoria",
        "Análise da conversão de valor preliminar para definitivo após julgamento final. "
        "Efetividade regulatória por ano e comparativo de valores por município.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/juridico_diretoria.py", label="Abrir →", use_container_width=True)

with c7:
    st.markdown(_card(
        "📜", "Enquadramento legal",
        "Ranking de infrações por portaria e artigo aplicado. "
        "Correlação entre categoria de determinação e enquadramento legal. "
        "Aguarda incorporação dos dados de portarias.",
        "em construção", AMBER_C, AMBER_BG), unsafe_allow_html=True)
    st.page_link("pages/juridico_enquadramento.py", label="Abrir →", use_container_width=True)

with c8:
    st.markdown("", unsafe_allow_html=True)  # espaço vazio para manter alinhamento

# ── GRUPO: Painel financeiro ──────────────────────────────────────
_secao("Painel financeiro")
c9, c10, c11, c12 = st.columns(4)

with c9:
    st.markdown(_card(
        "💳", "Valores de multas",
        "Comparativo anual preliminar × definitivo. Pareto por município mostrando "
        "concentração financeira e ticket médio por categoria de determinação.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/financeiro_multas.py", label="Abrir →", use_container_width=True)

with c10:
    st.markdown(_card(
        "🧾", "Boletos emitidos",
        "Controle de boletos por auto de infração: quantidade, valor total e "
        "evolução anual. Tabela detalhada com município, regional e valor por boleto.",
        "disponível", VERDE_C, VERDE_BG), unsafe_allow_html=True)
    st.page_link("pages/financeiro_boletos.py", label="Abrir →", use_container_width=True)

with c11:
    st.markdown("", unsafe_allow_html=True)

with c12:
    st.markdown("", unsafe_allow_html=True)

# ── GRUPO: Outros ─────────────────────────────────────────────────
_secao("Outros")
c13, c14, c15, c16 = st.columns(4)

with c13:
    st.markdown(_card(
        "⏱️", "Lead time",
        "Tempo médio em dias entre cada etapa do ciclo: TN → Auto, Auto → Câmara, "
        "Câmara → Diretoria e ciclo total. Gráficos por ano e por regional.",
        "em construção", AMBER_C, AMBER_BG), unsafe_allow_html=True)
    st.page_link("pages/lead_time.py", label="Abrir →", use_container_width=True)

with c14:
    st.markdown("", unsafe_allow_html=True)
with c15:
    st.markdown("", unsafe_allow_html=True)
with c16:
    st.markdown("", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("⚡ Dados carregados com cache · base_fiscalizacao_normalizada_v5.xlsx")
