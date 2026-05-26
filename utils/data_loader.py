"""
utils/data_loader.py
====================
Responsável por carregar, tratar e combinar os dados do Excel.

Princípios seguidos:
- Cache com @st.cache_data para não recarregar a cada interação
- Separação clara entre leitura e transformação
- Tratamento defensivo de valores nulos e tipos

CORREÇÕES v5.1:
    BUG CRÍTICO: tratar_autos_infracao() agora deduplica corretamente.
    A tabela autos_infracao tem uma linha por (auto_id × determinacao_id),
    ou seja, um auto com 5 determinações vinculadas aparece 5 vezes.
    Antes da correção, somar valor_preliminar sem deduplicar inflava os
    totais em até 60% (ex.: R$ 37 mi em vez de R$ 23 mi corretos).

    SOLUÇÃO: ao final de tratar_autos_infracao(), reduzimos a tabela
    para 1 linha por auto_id usando a estratégia de "manter o maior
    valor monetário por auto_id" (linhas com valor=0 são descartadas
    quando existe outra linha com valor real para o mesmo auto_id).

    Demais correções:
    - calcular_boletos_emitidos em metrics.py: usa aba 'boletos' separada
    - tratar_boletos: agora também deduplica (1 boleto real por auto_id)
"""

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# Caminho para o arquivo de dados (relativo à raiz do projeto)
CAMINHO_DADOS = Path(__file__).parent.parent / "data" / "base_fiscalizacao_normalizada_v5.xlsx"


# ─────────────────────────────────────────────
# FUNÇÕES DE LEITURA
# ─────────────────────────────────────────────

@st.cache_data
def carregar_todas_as_planilhas() -> dict[str, pd.DataFrame]:
    """
    Lê todas as abas do Excel de uma vez e retorna um dicionário.
    O cache garante que o arquivo só é lido uma vez por sessão.

    REFATORAÇÃO v6.0 — tratamento explícito de erros de arquivo:
        Antes: FileNotFoundError subia como traceback críptico na tela.
        Agora: st.error() exibe mensagem amigável e st.stop() interrompe
        a execução sem mostrar stack trace ao usuário final.
    """
    if not CAMINHO_DADOS.exists():
        # st.error() renderiza um bloco vermelho visível na interface
        st.error(
            f"⚠️ **Arquivo de dados não encontrado.**\n\n"
            f"Caminho esperado: `{CAMINHO_DADOS}`\n\n"
            "Verifique se a pasta `data/` existe na raiz do projeto "
            "e contém o arquivo `base_fiscalizacao_normalizada_v5.xlsx`."
        )
        st.stop()  # interrompe o script — não renderiza o resto da página

    try:
        return pd.read_excel(CAMINHO_DADOS, sheet_name=None)
    except Exception as e:
        st.error(
            f"⚠️ **Erro ao ler o arquivo Excel.**\n\n"
            f"Detalhe técnico: `{type(e).__name__}: {e}`\n\n"
            "Verifique se o arquivo não está aberto em outro programa "
            "ou se está corrompido."
        )
        st.stop()


@st.cache_data
def carregar_dados_tratados() -> dict[str, pd.DataFrame]:
    """
    Ponto de entrada principal.
    Retorna todas as tabelas já tratadas e prontas para uso.

    REFATORAÇÃO v6.0:
    - Tratamento de KeyError quando uma aba esperada não existe no Excel.
      Antes: KeyError críptico. Agora: mensagem clara com o nome da aba.

    ATUALIZADO (v5.1):
    - autos_infracao: deduplica para 1 linha por auto_id (CORREÇÃO CRÍTICA)
    - boletos: deduplica para 1 linha por auto_id com valor máximo
    """
    planilhas_brutas = carregar_todas_as_planilhas()

    # Abas obrigatórias no Excel — verificação antecipada com erro claro
    abas_obrigatorias = [
        "fiscalizacoes", "determinacoes", "autos_infracao",
        "julgamentos", "boletos", "municipios",
    ]
    abas_faltando = [a for a in abas_obrigatorias if a not in planilhas_brutas]
    if abas_faltando:
        st.error(
            f"⚠️ **Abas obrigatórias não encontradas no Excel:**\n\n"
            f"`{', '.join(abas_faltando)}`\n\n"
            "Verifique se o arquivo está na versão correta (v5 ou superior)."
        )
        st.stop()

    fiscalizacoes  = tratar_fiscalizacoes(planilhas_brutas["fiscalizacoes"])
    determinacoes  = tratar_determinacoes(planilhas_brutas["determinacoes"])
    autos_infracao = tratar_autos_infracao(planilhas_brutas["autos_infracao"])
    julgamentos    = tratar_julgamentos(planilhas_brutas["julgamentos"])
    boletos        = tratar_boletos(planilhas_brutas["boletos"])
    municipios     = tratar_municipios(planilhas_brutas["municipios"])

    return {
        "fiscalizacoes":  fiscalizacoes,
        "determinacoes":  determinacoes,
        "autos_infracao": autos_infracao,
        "julgamentos":    julgamentos,
        "boletos":        boletos,
        "municipios":     municipios,
    }


# ─────────────────────────────────────────────
# LIMPEZA DE CARACTERES CORROMPIDOS
# ─────────────────────────────────────────────

_MAPA_CHARS = {
    "\xa0": "",    # non-breaking space → vazio
    "\x93": "ô",   # byte corrompido do Windows-1252
    "\x87": "ç",   # byte corrompido do Windows-1252
}

_MAPA_NOMES = {
    "Anastcio":   "Anastácio",
    "Anast Cio":  "Anastácio",
    "Deodpolis":  "Deodápolis",
    "Deod Polis": "Deodápolis",
    "Corumbáá":   "Corumbá",
    "Corumba":    "Corumbá",
}

# Regex compilada uma única vez para colapsar espaços múltiplos.
# Usada dentro de _limpar_col() — mais rápida que " ".join(valor.split())
# aplicado linha a linha via .apply().
import re as _re
_ESPACOS_MULTIPLOS = _re.compile(r"\s+")


def _limpar_col(series: pd.Series) -> pd.Series:
    """
    Limpa toda uma coluna de strings de forma VETORIZADA.

    Estratégia (por que é mais rápida que .apply()):
        - pd.Series.str.replace() opera em C via NumPy/Pandas internamente,
          sem overhead de chamar uma função Python para cada linha.
        - .str.split().str.join() também é vetorizado — equivale a
          " ".join(valor.split()) mas para toda a coluna de uma vez.
        - .map() para substituição de nomes usa um dict hash-lookup (O(1))
          e opera sobre os valores únicos, não sobre todas as linhas.

    Antes: 1 chamada Python por linha → lento com 10.000+ linhas.
    Agora: operações em bloco sobre arrays → ~10× mais rápido.
    """
    s = series.astype(str)  # garante que a coluna é string

    # Passo 1 — substitui caracteres corrompidos (loop sobre o dicionário pequeno)
    for char_ruim, substituto in _MAPA_CHARS.items():
        s = s.str.replace(char_ruim, substituto, regex=False)

    # Passo 2 — colapsa espaços múltiplos e remove leading/trailing
    # .str.split() + .str.join() é equivalente vetorizado de " ".join(x.split())
    s = s.str.strip().str.split().str.join(" ")

    # Passo 3 — corrige nomes de municípios com erros conhecidos
    # .map() busca cada valor no dict; fillna(s) mantém o original quando não encontra
    s = s.str.title().map(_MAPA_NOMES).fillna(s.str.title())

    return s


# ─────────────────────────────────────────────
# FUNÇÕES DE TRATAMENTO POR TABELA
# ─────────────────────────────────────────────

def tratar_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de municípios e regionais."""
    df = df.copy()
    # _limpar_col() já aplica .str.strip() e .str.title() internamente
    df["municipio"] = _limpar_col(df["municipio"])
    df["regional"]  = _limpar_col(df["regional"])
    return df


def tratar_fiscalizacoes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trata a tabela principal de fiscalizações.

    ATUALIZADO (v5):
    - Campo 'termo' agora é 'termo_notificacao'
    - Campo 'ano' agora é 'ano_fiscalizacao'
    """
    df = df.copy()

    # Aliases para compatibilidade com código existente
    if "termo_notificacao" in df.columns:
        df["termo"] = df["termo_notificacao"]
    if "ano_fiscalizacao" in df.columns:
        df["ano"] = df["ano_fiscalizacao"]

    df["municipio"] = _limpar_col(df["municipio"])
    df["regional"]  = _limpar_col(df["regional"])
    df["objeto"]    = _limpar_col(df["objeto"])
    if "termo" in df.columns:
        df["termo"] = _limpar_col(df["termo"])

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").fillna(0).astype(int)

    if "data_recebimento_tn" in df.columns:
        df["data_recebimento_tn"] = pd.to_datetime(df["data_recebimento_tn"], errors="coerce")

    return df


def tratar_determinacoes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trata a tabela de determinações.

    ATUALIZADO (v5):
    - Aliases: termo_notificacao → termo, num_determinacao → num_det, etc.
    """
    df = df.copy()

    if "termo_notificacao" in df.columns:
        df["termo"] = df["termo_notificacao"]
    if "num_determinacao" in df.columns:
        df["num_det"] = df["num_determinacao"]
    if "desc_determinacao" in df.columns:
        df["desc_det"] = df["desc_determinacao"]
    if "num_constatacao" in df.columns:
        df["num_cons"] = df["num_constatacao"]

    df["categoria"] = df["categoria"].str.strip()
    df["setor"]     = df["setor"].str.strip().str.upper()

    mapa_categorias = {
        "Infraestrutura, instalações e funcionamento (SES)": "Infraestrutura",
        "Infraestrutura, instalações e funcionamento":       "Infraestrutura",
        "Envio de documentação (SES)":                       "Documentação",
        "Envio de documentação":                             "Documentação",
        "Controle de ativos regulatórios":                   "Controle Ativo",
        "Controle de inventário patrimonial":                "Controle Inventário",
        "Georreferenciamento de ativos":                     "Georreferenciamento",
        "Análise da qualidade da água (SES)":                "Qualidade da Água",
        "Análise da qualidade da água (SAA)":                "Qualidade da Água",
        "Faturamento":                                       "Faturamento",
        "Atendimento ao público":                            "Atendimento",
        "Condições do macromedidor":                         "Infraestrutura",
        "Recursos humanos":                                  "Recursos Humanos",
        "Recursos humanos (SES)":                            "Recursos Humanos",
        "Segurana patrimonial":                              "Segurança Patrimonial",
        "Segurana patrimonial (SES)":                        "Segurança Patrimonial",
        "Armazenamento de produtos":                         "Outras",
    }
    df["categoria_padronizada"] = df["categoria"].map(mapa_categorias).fillna("Outras")
    return df


def tratar_autos_infracao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trata a tabela de autos de infração.

    ══════════════════════════════════════════════════════════════
    CORREÇÃO CRÍTICA v5.1 — DEDUPLICAÇÃO POR auto_id
    ══════════════════════════════════════════════════════════════
    PROBLEMA:
        A aba 'autos_infracao' tem uma linha por combinação
        (auto_id × determinacao_id). Um auto vinculado a 7
        determinações aparece 7 vezes — MAS o valor monetário
        fica registrado em apenas algumas linhas desse grupo.
        Somar sem deduplicar infla os totais em ~60%.

    CAUSA RAIZ (observada nos dados):
        Para um mesmo auto_id, o valor aparece repetido em linhas
        onde determinacao_id é o mesmo (duplicação vertical da
        chave de relacionamento). Ex.: auto_id=32 tem 9 linhas,
        com o valor 125.000,00 nas 3 primeiras e 0 nas demais.

    SOLUÇÃO:
        1. Converter valores monetários primeiro (string → float).
        2. Para cada auto_id, manter apenas o valor MÁXIMO de
           valor_preliminar e valor_definitivo (a linha com valor
           real é a que tem o maior número).
        3. Fazer groupby('auto_id').agg() para colapsar para
           1 linha por auto, preservando fiscalizacao_id, termo,
           num_auto e as flags derivadas.

    RESULTADO:
        Valor preliminar correto: R$ 23.220.733,18
        (antes da correção: R$ 37.043.582,34 — 59% inflado)
    ══════════════════════════════════════════════════════════════
    """
    df = df.copy()

    # ── Aliases de compatibilidade ───────────────────────────────
    if "termo_notificacao" in df.columns:
        df["termo"] = df["termo_notificacao"]
    if "num_auto" in df.columns:
        df["auto_num"] = df["num_auto"]

    # ── Conversão de valores monetários ─────────────────────────
    def converter_valor_monetario(valor) -> float:
        """
        Converte valor monetário para float, suportando dois formatos:

        1. Float nativo do pandas/Excel (mais comum nesta base):
           449.55 → 449.55  |  1234.56 → 1234.56
           O Excel já entrega os valores como float; nenhuma transformação
           de string é necessária.

        2. String no formato BR (caso existam células textuais):
           '449,55' → 449.55  |  '1.234,56' → 1234.56

        BUG ANTERIOR (converter_valor_monetario v5.0):
           O código fazia str(float).replace('.','').replace(',','.')
           para um float como 449.55:
             str(449.55)          → '449.55'
             .replace('.','')     → '44955'    ← eliminou o separador decimal!
             .replace(',','.')    → '44955'
             float()              → 44955.0    ← 100× maior que o correto
           Isso inflava todos os valores em ~100x para valores com 2 casas
           decimais (ex.: 449.55 → 44.955,00).
        """
        if pd.isna(valor) or str(valor).strip() in ["-", "", "nan"]:
            return 0.0

        # Caminho rápido: valor já é numérico (float/int do pandas)
        if isinstance(valor, (int, float, np.integer, np.floating)):
            return float(valor)

        # Caminho para strings no formato BR: '1.234,56' → 1234.56
        valor_str = str(valor).strip()
        if not valor_str or valor_str in ["-", "nan"]:
            return 0.0
        try:
            # Verifica se é formato BR (vírgula decimal)
            if "," in valor_str:
                valor_str = valor_str.replace(".", "").replace(",", ".")
            return float(valor_str)
        except ValueError:
            return 0.0

    # Aplica conversão em todas as linhas (ainda com duplicatas)
    df["valor_preliminar_num"] = df["valor_preliminar"].apply(converter_valor_monetario)
    df["valor_definitivo_num"] = df["valor_definitivo"].apply(converter_valor_monetario)

    # ── Flag se o auto foi emitido ────────────────────────────────
    # (True quando num_auto tem um número de auto válido)
    df["auto_emitido"] = df["num_auto"].apply(
        lambda x: str(x).strip() not in ["-", "", "nan"] and pd.notna(x)
    )

    # ── DEDUPLICAÇÃO: 1 linha por auto_id ────────────────────────
    # Para cada auto_id, agrega pegando:
    #   - max de valores monetários (captura a linha que tem o valor real)
    #   - first de metadados (fiscalizacao_id, termo, num_auto, auto_num)
    #   - any de auto_emitido (True se pelo menos uma linha foi emitida)
    # tem_boleto começa como False; é atualizado em aplicar_todos_filtros()
    # via join com a aba 'boletos'.
    df_dedup = (
        df.groupby("auto_id")
        .agg(
            fiscalizacao_id      = ("fiscalizacao_id",      "first"),
            termo                = ("termo",                 "first"),
            num_auto             = ("num_auto",              "first"),
            auto_num             = ("auto_num",              "first"),
            valor_preliminar_num = ("valor_preliminar_num",  "max"),
            valor_definitivo_num = ("valor_definitivo_num",  "max"),
            auto_emitido         = ("auto_emitido",          "any"),
        )
        .reset_index()
    )

    # ── Flags derivadas ───────────────────────────────────────────
    df_dedup["tem_valor_definitivo"] = df_dedup["valor_definitivo_num"] > 0
    # tem_boleto é placeholder; será sobrescrito via join com aba 'boletos'
    df_dedup["tem_boleto"] = False

    return df_dedup


def tratar_julgamentos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trata a tabela de julgamentos (substitui antiga 'andamento').

    CORREÇÃO v5.1:
        Deduplica para 1 julgamento por auto_id (mantém o mais avançado).
        A tabela bruta replica linhas pelo mesmo motivo de autos_infracao.
    """
    df = df.copy()

    # ── Normalização de resultados ───────────────────────────────
    df["resultado_agems"] = df["resultado_agems"].str.strip().str.upper()

    df["resultado_camara_original"] = df["resultado_camara"]
    df["resultado_camara"] = df["resultado_camara"].str.strip().str.upper()

    mapa_camara = {
        "ACATADA INTEGRALMENTE":                              "ACATADA",
        "ACATADA - CONVERTER EM ADVERTÊNCIA":                 "ACATADA",
        "PARCIALMENTE ACATADA - APLICAR ATENUANTE DE 1/6":    "ACATADA PARCIALMENTE",
        "PARCIALMENTE ACATADA - APLICAR ATENUANTE":           "ACATADA PARCIALMENTE",
        "NÃO ACATADA":                                        "NÃO ACATADA",
        "NÃO SE APLICA":                                      "NÃO SE APLICA",
        "-":                                                  "PENDENTE",
    }
    df["resultado_camara_padronizado"] = df["resultado_camara"].map(
        lambda x: mapa_camara.get(x, "OUTROS")
    )

    df["resultado_diretoria_original"] = df["resultado_diretoria"]
    df["resultado_diretoria"] = df["resultado_diretoria"].str.strip().str.upper()

    mapa_diretoria = {
        "ACATADA":                                           "ACATADA",
        "PARCIALMENTE ACATADA - APLICAR ATENUANTE":          "ACATADA PARCIALMENTE",
        "NÃO ACATADA":                                       "NÃO ACATADA",
        "NÃO SE APLICA":                                     "NÃO SE APLICA",
        "-":                                                 "PENDENTE",
        "O JULGAMENTO NÃO FOI PUBLICADO ATÉ O MOMENTO":      "PENDENTE",
        "0":                                                 "PENDENTE",
    }
    df["resultado_diretoria_padronizado"] = df["resultado_diretoria"].map(
        lambda x: mapa_diretoria.get(x, "OUTROS")
    )

    # ── Conversão de datas ───────────────────────────────────────
    for col_data in ["data_analise_agems", "data_publicacao_camara", "data_publicacao_diretoria"]:
        df[col_data] = df[col_data].replace("-", pd.NaT)
        df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

    # ── Flags de pendência ────────────────────────────────────────
    df["pendente_camara"] = (
        (df["resultado_camara_padronizado"] == "PENDENTE") |
        df["data_publicacao_camara"].isna()
    )
    df["pendente_diretoria"] = (
        (df["resultado_diretoria_padronizado"] == "PENDENTE") |
        df["data_publicacao_diretoria"].isna()
    )
    df["processo_pendente"] = df["pendente_camara"] | df["pendente_diretoria"]

    # ── resultado_padronizado (compatibilidade com código antigo) ─
    #
    # REFATORAÇÃO v6.0 — np.select() em vez de df.apply(resultado_geral, axis=1)
    #
    # Por que np.select() é melhor que .apply(func, axis=1)?
    #
    #   .apply(func, axis=1) itera linha a linha em Python puro:
    #   cada linha vira um objeto pd.Series, a função é chamada N vezes.
    #   Para 5.000 linhas: ~5.000 chamadas de função Python → lento.
    #
    #   np.select() avalia condições como arrays booleanos NumPy de uma vez:
    #   nenhuma iteração Python — operação em bloco sobre vetores → ~10× mais rápido.
    #
    # Lógica (idêntica ao resultado_geral original):
    #   Condição 1: diretoria tem resultado definitivo → usa ele
    #   Condição 2: câmara tem resultado definitivo    → usa ela
    #   Condição 3: processo_pendente == True          → "Pendente de Análise"
    #   Default:                                       → "Outros"
    _sem_resultado = {"NÃO SE APLICA", "PENDENTE", "OUTROS"}  # conjunto para busca O(1)

    # Máscara booleana para cada condição — aplicada sobre toda a coluna de uma vez
    _dir_definitivo = ~df["resultado_diretoria_padronizado"].isin(_sem_resultado)
    _cam_definitivo = ~df["resultado_camara_padronizado"].isin(_sem_resultado)

    df["resultado_padronizado"] = np.select(
        condlist=[
            _dir_definitivo,           # condição de maior prioridade
            _cam_definitivo,
            df["processo_pendente"],
        ],
        choicelist=[
            df["resultado_diretoria_padronizado"],  # usa valor da diretoria
            df["resultado_camara_padronizado"],      # usa valor da câmara
            "Pendente de Análise",
        ],
        default="Outros",              # nenhuma condição atendida
    )

    # ── DEDUPLICAÇÃO: 1 julgamento por auto_id ────────────────────
    # Critério: manter a linha com o julgamento mais avançado.
    # Ordem de prioridade de resultado: ACATADA > ACATADA PARCIALMENTE
    # > NÃO ACATADA > NÃO SE APLICA > PENDENTE > OUTROS.
    # Na prática, ordenamos por julgamento_id DESC e pegamos o primeiro,
    # que corresponde ao registro mais recente/completo do processo.
    df_dedup = (
        df.sort_values("julgamento_id", ascending=False)
          .drop_duplicates(subset=["auto_id"], keep="first")
          .reset_index(drop=True)
    )

    return df_dedup


def tratar_boletos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trata a tabela de boletos (NOVA na v5).

    CORREÇÃO v5.1:
        Deduplica para 1 boleto por auto_id (mantém o de maior valor).
        A tabela bruta tem o mesmo padrão de duplicação de autos_infracao.
    """
    df = df.copy()

    df["numero_boleto"] = df["numero_boleto"].astype(str).str.strip()
    df["valor_boleto"]  = pd.to_numeric(df["valor_boleto"], errors="coerce").fillna(0.0)
    df["boleto_valido"] = df["valor_boleto"] > 0

    # Deduplica: para cada auto_id, mantém o boleto com maior valor
    # (elimina duplicatas resultantes da relação auto × determinação)
    df_dedup = (
        df.sort_values("valor_boleto", ascending=False)
          .drop_duplicates(subset=["auto_id"], keep="first")
          .reset_index(drop=True)
    )

    return df_dedup


# ─────────────────────────────────────────────
# FUNÇÃO DE JUNÇÃO (JOIN) ENTRE TABELAS
# ─────────────────────────────────────────────

@st.cache_data
def construir_base_unificada() -> pd.DataFrame:
    """
    Cria uma visão desnormalizada (flat) para análises cruzadas.
    Junta: fiscalizacoes + determinacoes + autos_infracao + julgamentos + boletos

    ATUALIZADO (v5.1): todas as tabelas já vêm deduplicadas de carregar_dados_tratados().
    """
    dados = carregar_dados_tratados()

    fiscalizacoes  = dados["fiscalizacoes"]
    determinacoes  = dados["determinacoes"]
    autos_infracao = dados["autos_infracao"]   # já 1 linha por auto_id
    julgamentos    = dados["julgamentos"]       # já 1 linha por auto_id
    boletos        = dados["boletos"]           # já 1 linha por auto_id

    # Atualiza tem_boleto em autos via join com boletos
    autos_com_boleto = set(boletos[boletos["valor_boleto"] > 0]["auto_id"].unique())
    autos_infracao = autos_infracao.copy()
    autos_infracao["tem_boleto"] = autos_infracao["auto_id"].isin(autos_com_boleto)

    # Agrega autos por fiscalizacao_id (pode haver múltiplos autos por TN)
    autos_agregados = (
        autos_infracao
        .groupby("fiscalizacao_id")
        .agg(
            total_autos          = ("auto_id",              "count"),
            autos_com_valor      = ("valor_preliminar_num", lambda x: (x > 0).sum()),
            valor_preliminar_sum = ("valor_preliminar_num", "sum"),
            valor_definitivo_sum = ("valor_definitivo_num", "sum"),
            tem_boleto_algum     = ("tem_boleto",           "any"),
        )
        .reset_index()
    )

    # Agrega julgamentos por fiscalizacao_id via join com autos
    autos_fisc_map = autos_infracao[["auto_id", "fiscalizacao_id"]].drop_duplicates()
    julgamentos_com_fisc = julgamentos.merge(autos_fisc_map, on="auto_id", how="left")

    julgamentos_agg = (
        julgamentos_com_fisc
        .groupby("fiscalizacao_id")
        .agg(
            total_julgamentos    = ("julgamento_id",                  "count"),
            processos_pendentes  = ("processo_pendente",              "sum"),
            resultados_camara    = ("resultado_camara_padronizado",   lambda x: "|".join(x.unique())),
            resultados_diretoria = ("resultado_diretoria_padronizado", lambda x: "|".join(x.unique())),
        )
        .reset_index()
    )

    # Agrega boletos por fiscalizacao_id
    boletos_com_fisc = boletos.merge(autos_fisc_map, on="auto_id", how="left")
    boletos_agg = (
        boletos_com_fisc
        .groupby("fiscalizacao_id")
        .agg(
            total_boletos     = ("boleto_id",    "count"),
            valor_boletos_sum = ("valor_boleto", "sum"),
        )
        .reset_index()
    )

    # Conta determinações por fiscalizacao_id
    det_count = (
        determinacoes
        .groupby("fiscalizacao_id")
        .agg(total_determinacoes=("determinacao_id", "count"))
        .reset_index()
    )

    # Junta tudo na tabela principal
    base = (
        fiscalizacoes
        .merge(det_count,       on="fiscalizacao_id", how="left")
        .merge(autos_agregados, on="fiscalizacao_id", how="left")
        .merge(julgamentos_agg, on="fiscalizacao_id", how="left")
        .merge(boletos_agg,     on="fiscalizacao_id", how="left")
    )

    colunas_numericas = [
        "total_determinacoes", "total_autos", "autos_com_valor",
        "valor_preliminar_sum", "valor_definitivo_sum",
        "total_julgamentos", "processos_pendentes",
        "total_boletos", "valor_boletos_sum",
    ]
    base[colunas_numericas] = base[colunas_numericas].fillna(0)
    base["tem_boleto_algum"] = base["tem_boleto_algum"].fillna(False)

    return base
