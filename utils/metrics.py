"""
utils/metrics.py
================
Funções puras de cálculo de KPIs e métricas.

Regra: NENHUMA lógica de UI aqui.
Somente cálculos que retornam valores simples (float, int, str).

CORREÇÕES v5.1:
    - calcular_total_autos(): removido drop_duplicates() — a deduplicação
      já é feita em data_loader.tratar_autos_infracao(). Manter o drop_duplicates
      aqui era redundante (e correto), mas agora a tabela já chega limpa.
    - calcular_valor_preliminar_total(): idem — sem drop_duplicates.
    - calcular_boletos_emitidos(): CORRIGIDO — antes somava tem_boleto de
      autos_filtrados, que é uma flag calculada via join. Agora o cálculo
      está correto pois autos já vem deduplicado e tem_boleto atualizado
      em aplicar_todos_filtros(). Mantido como está pois o valor é confiável.
    - calcular_taxa_acatamento(): usava 'resultado_padronizado', que agora
      vem de tratar_julgamentos() (não mais de andamento). Mantido igual.
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────
# KPIs DE TERMOS DE NOTIFICAÇÃO
# ─────────────────────────────────────────────

def calcular_total_tns(df_fiscalizacoes: pd.DataFrame) -> int:
    """Retorna o número total de Termos de Notificação."""
    return len(df_fiscalizacoes)


def calcular_total_determinacoes(df_determinacoes: pd.DataFrame) -> int:
    """Retorna o número total de determinações."""
    return len(df_determinacoes)


def calcular_municipio_com_mais_tns(df_fiscalizacoes: pd.DataFrame) -> tuple[str, int]:
    """
    Retorna o município com maior número de TNs.

    Returns:
        Tuple (nome_municipio, quantidade)
    """
    if df_fiscalizacoes.empty:
        return ("N/A", 0)

    contagem  = df_fiscalizacoes.groupby("municipio").size()
    municipio = contagem.idxmax()
    quantidade = contagem.max()
    return (municipio, int(quantidade))


def calcular_media_determinacoes_por_tn(
    df_fiscalizacoes: pd.DataFrame,
    df_determinacoes: pd.DataFrame
) -> float:
    """Média de determinações por Termo de Notificação."""
    total_tns = len(df_fiscalizacoes)
    if total_tns == 0:
        return 0.0
    return round(len(df_determinacoes) / total_tns, 1)


# ─────────────────────────────────────────────
# KPIs DE AUTOS DE INFRAÇÃO
# ─────────────────────────────────────────────

def calcular_total_autos(df_autos: pd.DataFrame) -> int:
    """
    Total de autos emitidos (com número de auto válido).

    NOTA v5.1: df_autos já vem deduplicado (1 linha por auto_id)
    de data_loader.tratar_autos_infracao(). O drop_duplicates()
    anterior era uma salvaguarda que agora é desnecessária.
    """
    return int(df_autos["auto_emitido"].sum())


def calcular_valor_preliminar_total(df_autos: pd.DataFrame) -> float:
    """
    Soma do valor preliminar de todos os autos.

    NOTA v5.1: df_autos já vem deduplicado. A soma direta agora
    retorna o valor correto (sem inflação por duplicação de linhas).
    """
    return float(df_autos["valor_preliminar_num"].sum())


def calcular_taxa_conversao_tn_ai(
    df_fiscalizacoes: pd.DataFrame,
    df_autos: pd.DataFrame
) -> float:
    """
    Taxa de conversão: percentual de TNs que geraram ao menos 1 Auto de Infração.

    Lógica:
        - Conta fiscalizacao_ids únicos com pelo menos 1 auto com valor > 0
        - Divide pelo total de fiscalizações filtradas
    """
    total_tns = len(df_fiscalizacoes)
    if total_tns == 0:
        return 0.0

    # df_autos já deduplicado — 1 linha por auto_id
    tns_com_auto = df_autos[df_autos["valor_preliminar_num"] > 0]["fiscalizacao_id"].nunique()
    return round((tns_com_auto / total_tns) * 100, 1)


# ─────────────────────────────────────────────
# KPIs DE JULGAMENTOS / CÂMARA
# ─────────────────────────────────────────────

def calcular_distribuicao_resultados(df_julgamentos: pd.DataFrame) -> pd.Series:
    """Retorna contagem por resultado padronizado."""
    return df_julgamentos["resultado_padronizado"].value_counts()


def calcular_processos_pendentes(df_julgamentos: pd.DataFrame) -> int:
    """Total de processos com resultado 'Pendente de Análise'."""
    return int((df_julgamentos["resultado_padronizado"] == "Pendente de Análise").sum())


def calcular_taxa_acatamento(df_julgamentos: pd.DataFrame) -> float:
    """
    Percentual de processos acatados (total ou parcialmente).

    Usa resultado_padronizado, que reflete o estágio mais avançado
    do processo (câmara → diretoria).
    """
    total = len(df_julgamentos)
    if total == 0:
        return 0.0

    acatados = df_julgamentos[
        df_julgamentos["resultado_padronizado"].isin(["ACATADA", "ACATADA PARCIALMENTE"])
    ]
    return round((len(acatados) / total) * 100, 1)


# ─────────────────────────────────────────────
# KPIs FINANCEIROS
# ─────────────────────────────────────────────

def calcular_valor_definitivo_total(df_autos: pd.DataFrame) -> float:
    """
    Soma do valor definitivo de todos os autos.

    NOTA v5.1: df_autos já vem deduplicado.
    """
    return float(df_autos["valor_definitivo_num"].sum())


def calcular_boletos_emitidos(df_autos: pd.DataFrame) -> int:
    """
    Total de autos que possuem boleto emitido.

    CORREÇÃO v5.1:
        tem_boleto é atualizado em aplicar_todos_filtros() via join
        com a aba 'boletos'. df_autos já está deduplicado, então
        a soma direta retorna o número correto de boletos.
    """
    return int(df_autos["tem_boleto"].sum())


def calcular_reducao_valor(df_autos: pd.DataFrame) -> float:
    """
    Percentual de variação entre valor preliminar e definitivo.
    Negativo = houve redução (favorável ao fiscalizado).
    """
    total_preliminar = df_autos["valor_preliminar_num"].sum()
    total_definitivo = df_autos["valor_definitivo_num"].sum()

    if total_preliminar == 0:
        return 0.0

    reducao = ((total_definitivo - total_preliminar) / total_preliminar) * 100
    return round(float(reducao), 1)


def calcular_ticket_medio_por_categoria(
    df_autos: pd.DataFrame,
    df_determinacoes: pd.DataFrame
) -> pd.DataFrame:
    """
    Calcula o valor preliminar médio por categoria de determinação.

    Cruza autos (já deduplicados) com determinações via fiscalizacao_id.
    Usa a categoria predominante (moda) por fiscalizacao_id.
    """
    if df_autos.empty or df_determinacoes.empty:
        return pd.DataFrame()

    # Agrega valor por fiscalizacao_id (df_autos já deduplicado)
    autos_agg = (
        df_autos
        .groupby("fiscalizacao_id")["valor_preliminar_num"]
        .sum()
        .reset_index()
    )

    # Categoria predominante por fiscalizacao_id (moda)
    categoria_por_fis = (
        df_determinacoes
        .groupby("fiscalizacao_id")["categoria_padronizada"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
    )

    combinado = autos_agg.merge(categoria_por_fis, on="fiscalizacao_id", how="inner")
    ticket = (
        combinado
        .groupby("categoria_padronizada")["valor_preliminar_num"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={
            "categoria_padronizada": "Categoria",
            "valor_preliminar_num":  "Ticket Médio (R$)",
        })
        .sort_values("Ticket Médio (R$)", ascending=False)
    )
    return ticket


# ─────────────────────────────────────────────
# FORMATAÇÃO DE VALORES
# ─────────────────────────────────────────────

def formatar_moeda(valor: float) -> str:
    """
    Formata float como moeda brasileira.
    Exemplo: 1234.56 → 'R$ 1.234,56'
    """
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor: float) -> str:
    """
    Formata float como percentual.
    Exemplo: 42.5 → '42,5%'
    """
    return f"{valor:.1f}%".replace(".", ",")
