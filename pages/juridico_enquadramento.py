"""
pages/9_📜_Enquadramento_Legal.py
===================================
Página: Enquadramento Legal · Autos por portaria

STATUS: em construção — aguardando dados de enquadramento dos autos
nas portarias da AGEMS.

Quando os dados estiverem disponíveis, esta página exibirá:
    - Ranking de infrações por artigo/portaria
    - Distribuição dos autos por tipo de enquadramento legal
    - Correlação entre categoria de determinação e portaria aplicada
    - Tabela detalhada: auto × portaria × artigo × município

Como ativar o conteúdo:
    1. Adicionar coluna 'portaria' e 'artigo' à base de dados
       (aba autos_infracao ou nova aba enquadramento)
    2. Remover o banner de construção abaixo
    3. Implementar os gráficos usando os dados disponíveis

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline (components.html),
      blocos f-string e CSS embarcado em st.markdown.
    - Nenhuma lógica de dados ou layout foi alterada.
"""

import streamlit as st
from utils.ui_components import injetar_css_global, banner_wip, alerta_informacao
from utils.filters import renderizar_filtros_sidebar

# ── Configuração ───────────────────────────────────────────────
st.set_page_config(
    page_title="AGEMS · Enquadramento Legal",
    page_icon="📜",
    layout="wide",
)
injetar_css_global()

# ── Filtros sidebar ────────────────────────────────────────────
renderizar_filtros_sidebar()

# ─────────────────────────────────────────────
# BANNER: SEÇÃO EM CONSTRUÇÃO
# ─────────────────────────────────────────────
banner_wip(
    "O módulo de enquadramento legal aguarda a incorporação dos dados de "
    "portarias e artigos aos autos de infração. Quando disponíveis, será "
    "possível visualizar o ranking de infrações por portaria, a distribuição "
    "por artigo e a correlação com categorias de determinação."
)

# ─────────────────────────────────────────────
# PRÉVIA: O QUE ESTARÁ DISPONÍVEL
# ─────────────────────────────────────────────
st.markdown("""
<p style="font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 14px;">
    📋 Conteúdo planejado para este módulo:
</p>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

itens_col1 = [
    ("📊", "Ranking por portaria",          "Quais portarias concentram o maior número de autos lavrados"),
    ("📌", "Distribuição por artigo",        "Artigos mais acionados nos processos fiscalizatórios"),
    ("🔗", "Portaria × categoria",           "Correlação entre categoria de determinação e enquadramento legal"),
]
itens_col2 = [
    ("🏙️", "Enquadramento por município",   "Perfil legal das infrações por município e regional"),
    ("📅", "Evolução por ano",              "Tendência de enquadramentos ao longo dos anos fiscalizados"),
    ("📋", "Tabela detalhada",              "Auto · portaria · artigo · município · valor da multa"),
]

def card_previa(icone, titulo, descricao):
    return f"""
    <div style="
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
    ">
        <div style="font-size: 20px; flex-shrink: 0;">{icone}</div>
        <div>
            <p style="margin: 0 0 3px 0; font-weight: 600; font-size:14px; color: #111827;">{titulo}</p>
            <p style="margin: 0; font-size:14px; color: #6B7280; line-height: 1.5;">{descricao}</p>
        </div>
    </div>
    """

with col1:
    for icone, titulo, desc in itens_col1:
        st.markdown(card_previa(icone, titulo, desc), unsafe_allow_html=True)

with col2:
    for icone, titulo, desc in itens_col2:
        st.markdown(card_previa(icone, titulo, desc), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NOTA SOBRE OS DADOS NECESSÁRIOS
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="
    background-color: #EFF6FF;
    border-left: 4px solid #3B82F6;
    border-radius: 6px;
    padding: 14px 18px;
    color: #1E40AF;
    font-size:14px;
    line-height: 1.7;
">
    💡 <strong>Dados necessários para ativar este módulo:</strong><br>
    Incluir nas fichas de auto de infração as colunas <code>portaria</code>
    (ex: "Portaria AGEMS nº 151/2017") e <code>artigo</code>
    (ex: "Art. 13, inciso V") — ou criar uma aba separada
    <code>enquadramento</code> na planilha base com a relação
    <code>auto_id · portaria · artigo</code>.
</div>
""", unsafe_allow_html=True)
