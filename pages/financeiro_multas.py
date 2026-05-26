"""
pages/financeiro_multas.py
============================
Painel Financeiro · Valores de multas

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.

REDESIGN v7.0 — Esboço 3 "Pareto + painel lateral":
    - KPIs: mantidos exatamente como estavam (kpi_card original).
    - Comparativo anual: mantido como Plotly em 2 colunas compactas.
    - Pareto Preliminar → coluna [2, 1]:
        · Pareto Plotly (grafico_pareto) na coluna larga
        · KPI de valor prelim + ticket médio por categoria (barras CSS)
          na coluna estreita
    - Pareto Definitivo → coluna [2, 1]:
        · Pareto Plotly (grafico_pareto) na coluna larga
        · KPI de valor def + resumo por regional (st.dataframe)
          na coluna estreita
    - Todas as funções utilitárias originais preservadas:
        grafico_pareto(), grafico_barras_agrupadas(),
        calcular_ticket_medio_por_categoria(), tabela_com_exportacao()
    - Barras de ticket médio: renderizadas via st.components.v1.html()
      com estilos inline — evita bug de escape do st.markdown.
    - alerta_informacao() da linha 80% movido para após os dois Paretos.

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
from utils.metrics import (
    calcular_valor_preliminar_total, calcular_valor_definitivo_total,
    calcular_boletos_emitidos, calcular_ticket_medio_por_categoria,
    formatar_moeda, formatar_percentual,
)
from utils.charts import (
    grafico_pareto, grafico_barras_agrupadas,
    LAYOUT_PADRAO, COR_AZUL_ESCURO, COR_VERDE, COR_LARANJA,
)
from utils.ui_components import (
    kpi_card, secao_titulo,
    tabela_com_exportacao, alerta_informacao, alerta_atencao, sem_dados,
)

# ─────────────────────────────────────────────────────────────
# Carrega dados e aplica filtros
# ─────────────────────────────────────────────────────────────
filtros = renderizar_filtros_sidebar()
dados   = carregar_dados_tratados()

dados_filtrados         = aplicar_todos_filtros(dados, filtros)
fiscalizacoes_filtradas = dados_filtrados["fiscalizacoes"]
autos_filtrados         = dados_filtrados["autos_infracao"]
det_filtradas           = dados_filtrados["determinacoes"]
boletos_filtrados       = dados_filtrados["boletos"]

if fiscalizacoes_filtradas.empty:
    sem_dados()
    st.stop()

# ─────────────────────────────────────────────────────────────
# Métricas base — usadas nos KPIs e nos painéis laterais
# ─────────────────────────────────────────────────────────────
valor_prelim    = calcular_valor_preliminar_total(autos_filtrados)
valor_def       = calcular_valor_definitivo_total(autos_filtrados)
total_boletos   = calcular_boletos_emitidos(autos_filtrados)
autos_com_valor = autos_filtrados[autos_filtrados["valor_preliminar_num"] > 0]
ticket_medio    = (valor_prelim / len(autos_com_valor)) if len(autos_com_valor) > 0 else 0.0
pct_arrecadado  = (valor_def / valor_prelim * 100) if valor_prelim > 0 else 0.0

# Merges reutilizados em múltiplas seções
autos_com_ano = autos_filtrados.merge(
    fiscalizacoes_filtradas[["fiscalizacao_id", "ano"]],
    on="fiscalizacao_id", how="left",
)
autos_com_mun = autos_filtrados.merge(
    fiscalizacoes_filtradas[["fiscalizacao_id", "municipio"]],
    on="fiscalizacao_id", how="left",
)

# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo("💳 Indicadores financeiros")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Valor preliminar total", formatar_moeda(valor_prelim), "📄",
             cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A")
with col2:
    kpi_card("Valor definitivo total", formatar_moeda(valor_def), "✅",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D")
with col3:
    kpi_card("Ticket médio por auto", formatar_moeda(ticket_medio), "🎫",
             cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E",
             subtitulo=f"em {len(autos_com_valor)} autos com valor")
with col4:
    kpi_card("% valor confirmado", formatar_percentual(pct_arrecadado), "📊",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D",
             subtitulo="definitivo / preliminar")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Comparativo anual — Plotly compacto em 2 colunas
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📈 Comparativo anual: Preliminar vs. Definitivo",
    "Evolução dos valores por ano de fiscalização",
)

comparativo_anual = (
    autos_com_ano
    .dropna(subset=["ano"])
    .assign(ano=lambda df: df["ano"].astype(int).astype(str))  # garante string limpa
    .groupby("ano")
    .agg(
        valor_preliminar=("valor_preliminar_num", "sum"),
        valor_definitivo=("valor_definitivo_num", "sum"),
    )
    .reset_index()
    .sort_values("ano")
)

if not comparativo_anual.empty:
    col_barras, col_taxa = st.columns(2)

    with col_barras:
        # Barras agrupadas prelim/def por ano
        fig_anual = grafico_barras_agrupadas(
            df=comparativo_anual,
            coluna_x="ano",
            colunas_y=["valor_preliminar", "valor_definitivo"],
            nomes_series=["Valor Preliminar (R$)", "Valor Definitivo (R$)"],
            cores=[COR_AZUL_ESCURO, COR_VERDE],
            titulo="Valores por ano · Preliminar vs. Definitivo",
        )
        # Força eixo categórico — evita interpolação de anos como float
        fig_anual.update_layout(xaxis=dict(type="category"), height=320)
        st.plotly_chart(fig_anual, use_container_width=True)

    with col_taxa:
        # Percentual confirmado (def/prelim) por ano
        comparativo_anual["pct_confirmado"] = (
            comparativo_anual["valor_definitivo"]
            / comparativo_anual["valor_preliminar"].replace(0, float("nan"))
            * 100
        ).round(1).fillna(0)

        fig_pct = go.Figure()
        fig_pct.add_trace(go.Bar(
            x=comparativo_anual["ano"],
            y=comparativo_anual["pct_confirmado"],
            marker_color=COR_LARANJA,
            text=comparativo_anual["pct_confirmado"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>% confirmado: %{y:.1f}%<extra></extra>",
        ))
        layout_pct = {k: v for k, v in LAYOUT_PADRAO.items() if k != "legend"}
        fig_pct.update_layout(
            **layout_pct,
            title="% Valor confirmado por ano (def / prelim)",
            xaxis=dict(type="category"),
            yaxis=dict(showgrid=True, gridcolor="#E5E7EB", range=[0, 110]),
            height=320,
        )
        st.plotly_chart(fig_pct, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Paretos — seção de destaque
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📊 Pareto por município · Concentração financeira",
    "Princípio 80/20 · quais municípios concentram o maior valor",
)

# Subsets usados pelos Paretos
autos_com_valor_mun = autos_com_mun[autos_com_mun["valor_preliminar_num"] > 0]
autos_com_def_mun   = autos_com_mun[autos_com_mun["valor_definitivo_num"]  > 0]

# ─────────────────────────────────────────────────────────────
# Painel lateral 1 — Ticket médio por categoria (barras CSS)
# Renderizado via components.html() para evitar bug de escape
# do st.markdown quando class= e style= aparecem na mesma tag.
# ─────────────────────────────────────────────────────────────
def _html_ticket_medio(df: pd.DataFrame, max_val: float) -> str:
    """
    Barras horizontais âmbar do ticket médio por categoria.

    df deve ter colunas: 'Categoria' e 'Ticket Médio (R$)'.
    Cada barra é proporcional ao máximo; mínimo 3% para barras
    pequenas ficarem visíveis.
    Valores formatados como R$ XXXk ou R$ X,XXM.
    """
    linhas = ""
    for _, row in df.iterrows():
        cat = str(row["Categoria"])[:24]
        val = float(row["Ticket Médio (R$)"])
        pct = max(3, round(val / max_val * 100, 1))

        if val >= 1_000_000:
            val_fmt = f"R$ {val/1_000_000:.1f}M"
        elif val >= 1_000:
            val_fmt = f"R$ {val/1_000:.0f}k"
        else:
            val_fmt = f"R$ {val:,.0f}"

        linhas += f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <div style="font-size:14px;color:#64748b;min-width:112px;text-align:right;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {cat}
            </div>
            <div style="flex:1;height:14px;background:#e2e8f0;border-radius:3px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:#f59e0b;border-radius:3px;">
                </div>
            </div>
            <div style="font-size:14px;font-weight:600;color:#334155;min-width:56px;
                        text-align:right;">
                {val_fmt}
            </div>
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            🎫 Ticket médio por categoria
        </div>
        {linhas}
    </div>
    """


# ── Pareto 1: Valor Preliminar ────────────────────────────
st.markdown("""
<div style="display:flex;gap:8px;background:#eff6ff;border-left:4px solid #3b82f6;
            border-radius:8px;padding:9px 14px;font-size:14px;color:#1d4ed8;margin-bottom:12px;">
    📄 <strong>Valor Preliminar</strong> — Identifica os municípios que concentram
    o maior montante financeiro no ato da autuação inicial, antes de qualquer
    julgamento ou recurso.
</div>
""", unsafe_allow_html=True)

col_p1, col_info1 = st.columns([2, 1])

with col_p1:
    if not autos_com_valor_mun.empty:
        st.plotly_chart(
            grafico_pareto(
                df=autos_com_valor_mun,
                coluna_categoria="municipio",
                coluna_valor="valor_preliminar_num",
                titulo="Pareto: Valor Preliminar por município",
                top_n=20,
            ),
            use_container_width=True,
        )
    else:
        alerta_atencao("Nenhum dado com valor preliminar > 0.")

with col_info1:
    # KPI de valor preliminar
    st.markdown(f"""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                padding:14px 16px;margin-bottom:12px;">
        <div style="font-size:14px;font-weight:600;letter-spacing:.1em;
                    text-transform:uppercase;color:#94a3b8;margin-bottom:5px;">
            Valor preliminar total
        </div>
        <div style="font-size:24px;font-weight:700;color:#1d4ed8;line-height:1;">
            {formatar_moeda(valor_prelim)}
        </div>
        <div style="font-size:14px;color:#94a3b8;margin-top:4px;">
            {len(autos_com_valor)} autos com valor
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ticket médio por categoria via barras CSS
    ticket_df = calcular_ticket_medio_por_categoria(autos_filtrados, det_filtradas)
    if not ticket_df.empty:
        max_ticket = float(ticket_df["Ticket Médio (R$)"].max())
        # Altura ≈ 26px por categoria + 55px cabeçalho
        altura_ticket = len(ticket_df) * 26 + 55
        components.html(
            _html_ticket_medio(ticket_df, max_ticket),
            height=altura_ticket,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Pareto 2: Valor Definitivo ────────────────────────────
st.markdown("""
<div style="display:flex;gap:8px;background:#f0fdf4;border-left:4px solid #16a34a;
            border-radius:8px;padding:9px 14px;font-size:14px;color:#15803d;margin-bottom:12px;">
    ✅ <strong>Valor Definitivo</strong> — Reflete a concentração financeira real
    após o julgamento e encerramento dos processos. Permite comparar quais
    municípios tiveram maior ou menor redução em relação ao valor inicial.
</div>
""", unsafe_allow_html=True)

col_p2, col_info2 = st.columns([2, 1])

with col_p2:
    if not autos_com_def_mun.empty:
        st.plotly_chart(
            grafico_pareto(
                df=autos_com_def_mun,
                coluna_categoria="municipio",
                coluna_valor="valor_definitivo_num",
                titulo="Pareto: Valor Definitivo por município",
                top_n=20,
            ),
            use_container_width=True,
        )
    else:
        alerta_atencao("Nenhum valor definitivo encontrado.")

with col_info2:
    # KPI de valor definitivo
    st.markdown(f"""
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                padding:14px 16px;margin-bottom:12px;">
        <div style="font-size:14px;font-weight:600;letter-spacing:.1em;
                    text-transform:uppercase;color:#94a3b8;margin-bottom:5px;">
            Valor definitivo total
        </div>
        <div style="font-size:24px;font-weight:700;color:#15803d;line-height:1;">
            {formatar_moeda(valor_def)}
        </div>
        <div style="font-size:14px;color:#94a3b8;margin-top:4px;">
            {formatar_percentual(pct_arrecadado)} do preliminar confirmado
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Resumo por regional — st.dataframe nativo
    autos_com_regional = autos_filtrados.merge(
        fiscalizacoes_filtradas[["fiscalizacao_id", "regional"]],
        on="fiscalizacao_id", how="left",
    )
    resumo_regional = (
        autos_com_regional
        .groupby("regional")
        .agg(
            valor_preliminar=("valor_preliminar_num", "sum"),
            valor_definitivo=("valor_definitivo_num", "sum"),
            autos           =("auto_id", "count"),
        )
        .reset_index()
        .rename(columns={
            "regional":         "Regional",
            "valor_preliminar": "Valor Prelim. (R$)",
            "valor_definitivo": "Valor Def. (R$)",
            "autos":            "Autos",
        })
        .sort_values("Valor Prelim. (R$)", ascending=False)
    )

    st.dataframe(
        resumo_regional,
        use_container_width=True,
        height=340,
        hide_index=True,
        column_config={
            "Regional":          st.column_config.TextColumn(width="medium"),
            "Valor Prelim. (R$)":st.column_config.NumberColumn(
                format="R$ %.2f", width="medium"),
            "Valor Def. (R$)":   st.column_config.NumberColumn(
                format="R$ %.2f", width="medium"),
            "Autos":             st.column_config.NumberColumn(width="small"),
        },
    )

# Nota final dos Paretos
alerta_informacao(
    "A linha vermelha tracejada marca os 80%. "
    "Municípios à esquerda concentram a maior parte do valor regulado."
)
