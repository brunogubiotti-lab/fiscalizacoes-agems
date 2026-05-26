"""
utils/filters.py
================
Gerencia os filtros globais da barra lateral.

Centralizar filtros aqui garante que todas as páginas
se comportem da mesma forma sem duplicar código.

VERSÃO v6.0 — novo layout de sidebar:
    - Filtros em acordeões colapsáveis (expander do Streamlit)
    - Ano: multiselect com tags (comportamento padrão do widget)
    - Regional: selectbox — seleciona UMA regional por vez
    - Município: selectbox dependente da regional selecionada
      (carrega apenas os municípios da regional escolhida)
    - Filtro de Setor removido da sidebar; lógica interna mantida
      para compatibilidade — aplicar_todos_filtros() ainda o suporta,
      mas passa automaticamente todos os setores disponíveis.

Por que selectbox em vez de multiselect para Regional/Município?
    O padrão visual do mockup aprovado usa seleção única em cascata,
    o que simplifica a UX e evita combinações inválidas de filtros.
    Para análises multi-regional, o usuário pode escolher "Todas".

CORREÇÕES mantidas da v5.1:
    - autos_infracao deduplicado (1 linha por auto_id)
    - julgamentos deduplicado (1 linha por auto_id)
    - boletos deduplicado (1 linha por auto_id)
    - tem_boleto calculado via join com boletos filtrados
    - sem referência ao df 'andamento'
"""

import streamlit as st
import pandas as pd
from utils.data_loader import carregar_dados_tratados


def renderizar_filtros_sidebar() -> dict:
    """
    Renderiza os filtros na barra lateral em acordeões colapsáveis.

    Estrutura visual:
        [▼ Ano       ]  ← aberto por padrão, multiselect com todos os anos
        [▶ Regional  ]  ← fechado, selectbox com "Todas as regionais"
        [▶ Município ]  ← fechado, selectbox dependente da regional

    Returns:
        dict com chaves:
            'anos'      → list[int]  — anos selecionados
            'regionais' → list[str]  — lista com 1 regional ou todas
            'municipios'→ list[str]  — lista com 1 município ou todos
            'setores'   → list[str]  — TODOS os setores (sem filtro visual)
    """
    dados         = carregar_dados_tratados()
    fiscalizacoes = dados["fiscalizacoes"]
    determinacoes = dados["determinacoes"]

    # ── Label "FILTROS" — separa visualmente navegação de filtros ──
    # Injetado via st.sidebar.markdown() para garantir que aparece
    # no ponto exato certo da sidebar, independente do CSS.
    # A linha divisória (border-top) + uppercase criam a separação
    # clara entre os itens de navegação (acima) e os filtros (abaixo).
    st.sidebar.markdown("""
    <div style="
        border-top: 2px solid #E5E7EB;
        margin: 2px 0 6px 0;
        padding-top: 10px;
    ">
        <span style="
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: #9CA3AF;
            display: flex;
            align-items: center;
            gap: 5px;
        ">&#x2261;&nbsp;&nbsp;Filtros</span>
    </div>
    """, unsafe_allow_html=True)

    # ── FILTRO: ANO ───────────────────────────────────────────────
    # Expander aberto por padrão para o usuário ver os anos ativos.
    anos_disponiveis = sorted(fiscalizacoes["ano"].unique().tolist())

    with st.sidebar.expander("📅 Ano", expanded=False):
        # multiselect dentro do expander: cada ano aparece como tag
        anos_selecionados = st.multiselect(
            label="Anos",           # label obrigatório; ficará oculto
            options=anos_disponiveis,
            default=anos_disponiveis,
            label_visibility="collapsed",   # esconde o label visual
            help="Selecione um ou mais anos",
        )

    # Garante que nunca retorna lista vazia (evita DataFrames zerados)
    if not anos_selecionados:
        anos_selecionados = anos_disponiveis

    # ── FILTRO: REGIONAL ──────────────────────────────────────────
    # selectbox com opção "Todas as regionais" no topo.
    # Fechado por padrão para manter a sidebar compacta.
    regionais_disponiveis = sorted(
        fiscalizacoes["regional"].dropna().unique().tolist()
    )
    opcoes_regional = ["Todas as regionais"] + regionais_disponiveis

    with st.sidebar.expander("🗺️ Regional", expanded=False):
        regional_escolhida = st.selectbox(
            label="Regional",
            options=opcoes_regional,
            index=0,                        # padrão: "Todas as regionais"
            label_visibility="collapsed",
        )

    # Converte a seleção para lista — aplicar_todos_filtros() espera list
    if regional_escolhida == "Todas as regionais":
        regionais_selecionadas = regionais_disponiveis
    else:
        regionais_selecionadas = [regional_escolhida]

    # ── FILTRO: MUNICÍPIO ─────────────────────────────────────────
    # Carrega apenas os municípios da regional selecionada (cascata).
    # Se "Todas as regionais", mostra todos os municípios.
    municipios_da_regional = sorted(
        fiscalizacoes[
            fiscalizacoes["regional"].isin(regionais_selecionadas)
        ]["municipio"].dropna().unique().tolist()
    )
    opcoes_municipio = ["Todos os municípios"] + municipios_da_regional

    with st.sidebar.expander("🏙️ Município", expanded=False):
        municipio_escolhido = st.selectbox(
            label="Município",
            options=opcoes_municipio,
            index=0,                        # padrão: "Todos os municípios"
            label_visibility="collapsed",
        )

    # Converte para lista
    if municipio_escolhido == "Todos os municípios":
        municipios_selecionados = municipios_da_regional
    else:
        municipios_selecionados = [municipio_escolhido]

    # ── SETORES: sem filtro visual ────────────────────────────────
    # O filtro de setor foi removido da sidebar (decisão de UX v6.0).
    # A função aplicar_todos_filtros() continua recebendo 'setores',
    # mas passamos todos os valores disponíveis para não filtrar nada.
    setores_disponiveis = sorted(
        determinacoes["setor"].dropna().unique().tolist()
    )



    # Caption informativo no rodapé — abaixo de todos os filtros
    st.sidebar.caption("💡 Os filtros se aplicam a todas as abas")

    return {
        "anos":       anos_selecionados,
        "regionais":  regionais_selecionadas,
        "municipios": municipios_selecionados,
        "setores":    setores_disponiveis,   # todos — sem filtro visual
    }


# ─────────────────────────────────────────────
# FUNÇÃO PRINCIPAL: APLICA TODOS OS FILTROS
# ─────────────────────────────────────────────

def aplicar_todos_filtros(dados: dict, filtros: dict) -> dict:
    """
    Ponto de entrada único para filtrar TODAS as tabelas de forma consistente.

    Lógica em cascata:
        1. Filtra fiscalizacoes por ano, regional, município
        2. Filtra determinacoes por setor + IDs do passo 1
        3. Refina fiscalizacoes para IDs com setor válido
        4. Filtra autos pelos IDs finais + recalcula tem_boleto
        5. Filtra julgamentos pelos auto_ids dos autos filtrados
        6. Filtra boletos pelos auto_ids dos autos filtrados

    Args:
        dados:   dict retornado por carregar_dados_tratados()
        filtros: dict retornado por renderizar_filtros_sidebar()

    Returns:
        dict com as mesmas chaves de 'dados', todos os DataFrames
        já filtrados e consistentes entre si.
    """

    # ── PASSO 1: Fiscalizações por ano, regional, município ───────
    mask_fisc = (
        dados["fiscalizacoes"]["ano"].isin(filtros["anos"]) &
        dados["fiscalizacoes"]["municipio"].isin(filtros["municipios"]) &
        dados["fiscalizacoes"]["regional"].isin(filtros["regionais"])
    )
    fiscalizacoes_parcial = dados["fiscalizacoes"][mask_fisc]
    ids_apos_fisc = set(fiscalizacoes_parcial["fiscalizacao_id"].tolist())

    # ── PASSO 2: Determinações pelo setor + IDs do passo 1 ────────
    # 'setor' só existe em determinacoes; o filtro propaga para as demais.
    det_filtradas = dados["determinacoes"][
        dados["determinacoes"]["setor"].isin(filtros["setores"]) &
        dados["determinacoes"]["fiscalizacao_id"].isin(ids_apos_fisc)
    ].copy()

    ids_com_setor = set(det_filtradas["fiscalizacao_id"].tolist())

    # ── PASSO 3: Refina fiscalizações para apenas IDs com setor ───
    fiscalizacoes_filtradas = fiscalizacoes_parcial[
        fiscalizacoes_parcial["fiscalizacao_id"].isin(ids_com_setor)
    ].copy()

    ids_finais = list(ids_com_setor)

    # ── PASSO 4: Filtra autos pelos IDs finais ────────────────────
    # autos_infracao já está deduplicado (1 linha por auto_id).
    autos_filtrados = dados["autos_infracao"][
        dados["autos_infracao"]["fiscalizacao_id"].isin(ids_finais)
    ].copy()

    auto_ids_filtrados = set(autos_filtrados["auto_id"].tolist())

    # ── PASSO 4b: Recalcula tem_boleto ────────────────────────────
    # Considera apenas boletos com valor > 0 (ignora linhas zeradas).
    boletos_temp = dados["boletos"][
        dados["boletos"]["auto_id"].isin(auto_ids_filtrados)
    ]
    autos_com_boleto_real = set(
        boletos_temp[boletos_temp["valor_boleto"] > 0]["auto_id"].unique()
    )
    autos_filtrados["tem_boleto"] = autos_filtrados["auto_id"].isin(
        autos_com_boleto_real
    )

    # ── PASSO 5: Julgamentos pelos auto_ids dos autos filtrados ───
    julgamentos_filtrados = dados["julgamentos"][
        dados["julgamentos"]["auto_id"].isin(auto_ids_filtrados)
    ].copy()

    # ── PASSO 6: Boletos pelos auto_ids dos autos filtrados ───────
    boletos_filtrados = dados["boletos"][
        dados["boletos"]["auto_id"].isin(auto_ids_filtrados)
    ].copy()

    return {
        "fiscalizacoes":  fiscalizacoes_filtradas,
        "determinacoes":  det_filtradas,
        "autos_infracao": autos_filtrados,
        "julgamentos":    julgamentos_filtrados,
        "boletos":        boletos_filtrados,
        "municipios":     dados["municipios"],  # tabela de referência, sem filtro
    }


# ─────────────────────────────────────────────
# FUNÇÕES LEGADAS (mantidas para compatibilidade)
# ─────────────────────────────────────────────

def aplicar_filtros_fiscalizacoes(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    """
    [LEGADO] Filtra fiscalizações por ano, município e regional.

    ⚠️  NÃO aplica filtro de setor. Use aplicar_todos_filtros().
    """
    mascara = (
        df["ano"].isin(filtros["anos"]) &
        df["municipio"].isin(filtros["municipios"]) &
        df["regional"].isin(filtros["regionais"])
    )
    return df[mascara].copy()


def aplicar_filtros_determinacoes(
    df_det: pd.DataFrame, ids_fiscalizacao: list
) -> pd.DataFrame:
    """
    [LEGADO] Filtra determinações pelos IDs de fiscalização.

    ⚠️  NÃO aplica filtro de setor. Use aplicar_todos_filtros().
    """
    return df_det[df_det["fiscalizacao_id"].isin(ids_fiscalizacao)].copy()


def aplicar_filtros_por_ids(
    df: pd.DataFrame, ids_fiscalizacao: list
) -> pd.DataFrame:
    """
    Filtra qualquer tabela que tenha a coluna 'fiscalizacao_id'
    com base nos IDs passados.
    """
    return df[df["fiscalizacao_id"].isin(ids_fiscalizacao)].copy()
