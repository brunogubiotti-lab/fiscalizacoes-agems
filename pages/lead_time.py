"""
pages/lead_time.py
===================
Página: Lead Time · Tempo médio por etapa do ciclo regulatório

REDESIGN v7.0 — Esboço 2 "Funil + barras horizontais + tabela":
    - KPIs: mantidos (kpi_card original, 4 colunas).
    - Gráfico 1: Cards coloridos em sequência (funil horizontal)
      mostrando o fluxo TN → Auto → Câmara → Diretoria com dias.
      Renderizado via components.html() com estilos inline.
    - Gráfico 2: Barras horizontais CSS puras por etapa,
      substituindo o Plotly — mais leve e consistente com o estilo
      das outras abas. Também via components.html().
    - Análise por regional REMOVIDA conforme solicitado.
    - Tabela detalhada: mantida como st.dataframe nativo
      com exportação Excel.
    - st.set_page_config() e injetar_css_global() REMOVIDOS —
      centralizados em app.py.

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline (components.html),
      blocos f-string e CSS embarcado em st.markdown.
    - Nenhuma lógica de dados ou layout foi alterada.
"""

import io
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

from utils.data_loader import carregar_dados_tratados
from utils.filters import renderizar_filtros_sidebar, aplicar_todos_filtros
from utils.ui_components import (
    kpi_card, secao_titulo,
    alerta_informacao, alerta_atencao, sem_dados, banner_wip,
)
from utils.charts import LAYOUT_PADRAO

# ─────────────────────────────────────────────────────────────
# Banner de WIP + filtros
# ─────────────────────────────────────────────────────────────
banner_wip(
    "Os cálculos de lead time dependem das datas de análise e publicação registradas "
    "nos processos. Resultados parciais são esperados enquanto os dados históricos "
    "estiverem sendo consolidados."
)

filtros = renderizar_filtros_sidebar()

# ─────────────────────────────────────────────────────────────
# Carrega e filtra dados
# ─────────────────────────────────────────────────────────────
dados           = carregar_dados_tratados()
dados_filtrados = aplicar_todos_filtros(dados, filtros)

fiscalizacoes = dados_filtrados["fiscalizacoes"]
julgamentos   = dados_filtrados["julgamentos"]
autos         = dados_filtrados["autos_infracao"]

if fiscalizacoes.empty:
    sem_dados()
    st.stop()

# ─────────────────────────────────────────────────────────────
# Monta base unificada com todas as datas
# ─────────────────────────────────────────────────────────────
base = (
    julgamentos
    .merge(autos[["auto_id", "fiscalizacao_id"]], on="auto_id", how="left")
    .merge(
        fiscalizacoes[["fiscalizacao_id", "data_recebimento_tn",
                        "municipio", "regional", "ano"]],
        on="fiscalizacao_id", how="left",
    )
)

colunas_data = [
    "data_recebimento_tn", "data_analise_agems",
    "data_publicacao_camara", "data_publicacao_diretoria",
]
for col in colunas_data:
    if col in base.columns:
        base[col] = pd.to_datetime(base[col], errors="coerce")


def dias_entre(df, col_inicio, col_fim):
    """Dias entre duas colunas de data. NaN se alguma faltar ou negativo."""
    if col_inicio not in df.columns or col_fim not in df.columns:
        return pd.Series([pd.NA] * len(df), index=df.index)
    dias = (df[col_fim] - df[col_inicio]).dt.days
    return dias.where(dias >= 0)


base["dias_tn_auto"]     = dias_entre(base, "data_recebimento_tn",    "data_analise_agems")
base["dias_auto_camara"] = dias_entre(base, "data_analise_agems",     "data_publicacao_camara")
base["dias_camara_dir"]  = dias_entre(base, "data_publicacao_camara", "data_publicacao_diretoria")
base["dias_total"]       = dias_entre(base, "data_recebimento_tn",    "data_publicacao_diretoria")


def media_dias(serie: pd.Series) -> float:
    v = serie.dropna()
    return round(float(v.mean()), 1) if len(v) > 0 else 0.0


def contagem_valida(serie: pd.Series) -> int:
    return int(serie.notna().sum())


# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "⏱️ Tempo médio por etapa do ciclo regulatório",
    "Calculado apenas para processos com ambas as datas da etapa preenchidas",
)

m_tn_auto     = media_dias(base["dias_tn_auto"])
m_auto_camara = media_dias(base["dias_auto_camara"])
m_camara_dir  = media_dias(base["dias_camara_dir"])
m_total       = media_dias(base["dias_total"])

n_tn_auto     = contagem_valida(base["dias_tn_auto"])
n_auto_camara = contagem_valida(base["dias_auto_camara"])
n_camara_dir  = contagem_valida(base["dias_camara_dir"])
n_total       = contagem_valida(base["dias_total"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("TN → Auto de infração",
             f"{m_tn_auto:.0f} dias" if n_tn_auto > 0 else "Sem dados",
             "📋", cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A",
             subtitulo=f"{n_tn_auto} processos calculados")
with col2:
    kpi_card("Auto → Câmara",
             f"{m_auto_camara:.0f} dias" if n_auto_camara > 0 else "Sem dados",
             "🏛️", cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E",
             subtitulo=f"{n_auto_camara} processos calculados")
with col3:
    kpi_card("Câmara → Diretoria",
             f"{m_camara_dir:.0f} dias" if n_camara_dir > 0 else "Sem dados",
             "🎯", cor_fundo="#F5F3FF", cor_borda="#7C3AED", cor_valor="#5B21B6",
             subtitulo=f"{n_camara_dir} processos calculados")
with col4:
    kpi_card("Ciclo total (TN → Diretoria)",
             f"{m_total:.0f} dias" if n_total > 0 else "Sem dados",
             "⏱️", cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D",
             subtitulo=f"{n_total} processos calculados")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Gráfico: Funil horizontal + barras horizontais CSS
# Renderizado via components.html() — estilos inline para evitar
# bug de escape do st.markdown com class+style na mesma tag.
# ─────────────────────────────────────────────────────────────
secao_titulo("📊 Comparativo de lead time entre etapas")

# Dados das etapas para o gráfico
_ETAPAS = [
    ("TN → Auto de infração", m_tn_auto,     n_tn_auto,     "#1E3A8A"),
    ("Auto → Câmara",         m_auto_camara, n_auto_camara, "#F59E0B"),
    ("Câmara → Diretoria",    m_camara_dir,  n_camara_dir,  "#7C3AED"),
    ("Ciclo total",           m_total,       n_total,       "#16A34A"),
]

# Valor máximo para escala das barras horizontais
max_dias = max(e[1] for e in _ETAPAS if e[1] > 0) or 1


def _html_funil_e_barras(etapas, max_val):
    """
    Gera o painel completo com:
    1. Cards coloridos em sequência (funil) — fluxo visual do ciclo
    2. Barras horizontais CSS proporcional ao maior valor
       Cada barra mostra: rótulo · barra · valor em dias · n processos

    Renderizado via components.html() com estilos inline.
    """

    # ── Funil: cards em sequência com setas ──────────────────────
    cards_html = ""
    for i, (lbl, dias, n, cor) in enumerate(etapas):
        dias_str = f"{dias:.0f}d" if dias > 0 else "s/d"
        n_str    = f"{n} proc." if n > 0 else "—"
        seta     = "" if i == len(etapas) - 1 else """
            <div style="font-size:20px;color:#94a3b8;
                        display:flex;align-items:center;
                        padding:0 6px;margin-top:-8px;">→</div>
        """
        cards_html += f"""
        <div style="display:flex;align-items:center;">
            <div style="background:{cor};border-radius:10px;padding:12px 14px;
                        text-align:center;min-width:90px;">
                <div style="font-size:20px;font-weight:700;color:#fff;
                            line-height:1;margin-bottom:3px;">{dias_str}</div>
                <div style="font-size:14px;color:rgba(255,255,255,0.85);
                            line-height:1.3;">{lbl}</div>
                <div style="font-size:14px;color:rgba(255,255,255,0.65);
                            margin-top:3px;">{n_str}</div>
            </div>
            {seta}
        </div>
        """

    # ── Barras horizontais ───────────────────────────────────────
    barras_html = ""
    for lbl, dias, n, cor in etapas:
        pct     = max(3, round(dias / max_val * 100, 1)) if dias > 0 else 0
        dias_str = f"{dias:.0f} dias" if dias > 0 else "sem dados"
        n_str    = f"{n} processos" if n > 0 else "—"
        barras_html += f"""
        <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;
                        font-size:14px;margin-bottom:5px;">
                <span style="font-weight:500;color:#334155;">{lbl}</span>
                <span style="color:{cor};font-weight:700;">{dias_str}
                    <span style="font-size:14px;color:#94a3b8;font-weight:400;">
                        · {n_str}
                    </span>
                </span>
            </div>
            <div style="height:14px;background:#e2e8f0;border-radius:99px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{cor};
                            border-radius:99px;"></div>
            </div>
        </div>
        """

    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">

        <!-- Funil horizontal -->
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Fluxo do ciclo regulatório
        </div>
        <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;
                    margin-bottom:24px;">
            {cards_html}
        </div>

        <!-- Barras horizontais -->
        <div style="border-top:.5px solid #e2e8f0;padding-top:18px;">
            <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                        letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
                Tempo médio por etapa
            </div>
            {barras_html}
        </div>

    </div>
    """


# Altura total: funil (~130px) + barras (~50px × 4) + headers (~80px)
altura_grafico = 130 + len(_ETAPAS) * 50 + 80
components.html(
    _html_funil_e_barras(_ETAPAS, max_dias),
    height=altura_grafico,
)

alerta_informacao(
    "O ciclo total não é necessariamente a soma das etapas — "
    "processos distintos têm datas disponíveis em cada etapa. "
    "Cada média usa apenas os registros com ambas as datas preenchidas."
)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Tabela detalhada — largura total
# ─────────────────────────────────────────────────────────────
secao_titulo("📋 Tabela detalhada por processo")

colunas_tabela = {
    "municipio":                 "Município",
    "regional":                  "Regional",
    "ano":                       "Ano",
    "data_recebimento_tn":       "Data TN",
    "data_analise_agems":        "Data análise AGEMS",
    "data_publicacao_camara":    "Data câmara",
    "data_publicacao_diretoria": "Data diretoria",
    "dias_tn_auto":              "Dias TN→Auto",
    "dias_auto_camara":          "Dias Auto→Câmara",
    "dias_camara_dir":           "Dias Câmara→Dir.",
    "dias_total":                "Dias total",
}

cols_existentes = [c for c in colunas_tabela if c in base.columns]
df_tabela = (
    base[cols_existentes]
    .rename(columns=colunas_tabela)
    .sort_values("Dias total", ascending=False, na_position="last")
    .reset_index(drop=True)
)

st.caption(f"📊 {len(df_tabela):,} registros · use os filtros da sidebar para segmentar")

# Configuração de colunas para melhor legibilidade
col_cfg = {}
for nm in ["Dias TN→Auto", "Dias Auto→Câmara", "Dias Câmara→Dir.", "Dias total"]:
    if nm in df_tabela.columns:
        col_cfg[nm] = st.column_config.NumberColumn(width="small")
for nm in ["Data TN", "Data análise AGEMS", "Data câmara", "Data diretoria"]:
    if nm in df_tabela.columns:
        col_cfg[nm] = st.column_config.DatetimeColumn(width="medium", format="DD/MM/YYYY")
for nm in ["Município", "Regional"]:
    if nm in df_tabela.columns:
        col_cfg[nm] = st.column_config.TextColumn(width="medium")

st.dataframe(
    df_tabela,
    use_container_width=True,
    height=420,
    hide_index=True,
    column_config=col_cfg,
)

# Exportação para Excel
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as w:
    df_tabela.to_excel(w, index=False, sheet_name="Lead Time")
st.download_button(
    "📥 Exportar para Excel",
    data=buf.getvalue(),
    file_name="lead_time_fiscalizacao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
