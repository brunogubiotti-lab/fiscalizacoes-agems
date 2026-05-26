"""
pages/juridico_camara.py
==========================
Painel Jurídico · Decisões: câmara de julgamento

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.
    - Removida coluna 'resultado_norm': era calculada mas nunca usada.

REDESIGN v7.0 — Esboço 3 "Assimétrico 2 faixas":
    - KPIs: mantidos exatamente como estavam (kpi_card original).
    - Faixa 1: barras empilhadas por ano (coluna larga 2fr) + mini stats
      consolidados com barra de taxa de acatamento (coluna estreita 1fr).
    - Faixa 2: categorias não acatadas com barras CSS coloridas (coluna
      estreita 1fr) + tabela de pendentes com alerta (coluna larga 1.6fr).
    - Todos os gráficos renderizados via st.components.v1.html() com
      estilos inline para evitar o bug de escape do st.markdown.
    - Gráfico de barras empilhadas: mantido em Plotly (interatividade
      de hover é valiosa para análise ano a ano).
    - Tabela de pendentes: mantida como st.dataframe nativo com exportação Excel.
    - alerta_informacao() removido da seção de empilhadas — informação
      relevante já está integrada nos mini stats.

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline (components.html),
      blocos f-string e CSS embarcado em st.markdown.
    - Nenhuma lógica de dados ou layout foi alterada.
"""
import io
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import carregar_dados_tratados
from utils.filters import renderizar_filtros_sidebar, aplicar_todos_filtros
from utils.ui_components import (
    kpi_card, secao_titulo,
    alerta_atencao, alerta_informacao, sem_dados,
)
from utils.charts import LAYOUT_PADRAO

# ─────────────────────────────────────────────────────────────
# Carrega dados e aplica filtros
# ─────────────────────────────────────────────────────────────
filtros = renderizar_filtros_sidebar()
dados   = carregar_dados_tratados()

dados_filtrados         = aplicar_todos_filtros(dados, filtros)
fiscalizacoes_filtradas = dados_filtrados["fiscalizacoes"]
julgamentos_filtrados   = dados_filtrados["julgamentos"]
autos_filtrados         = dados_filtrados["autos_infracao"]

if fiscalizacoes_filtradas.empty:
    sem_dados()
    st.stop()

# ─────────────────────────────────────────────────────────────
# Cálculos de KPIs
# ─────────────────────────────────────────────────────────────
total_julgados = len(julgamentos_filtrados)

qtd_acatadas  = int(
    julgamentos_filtrados["resultado_camara_padronizado"]
    .isin(["ACATADA", "ACATADA PARCIALMENTE"]).sum()
)
qtd_nao_acat  = int(
    (julgamentos_filtrados["resultado_camara_padronizado"] == "NÃO ACATADA").sum()
)
qtd_pendentes = int(
    (julgamentos_filtrados["resultado_camara_padronizado"] == "PENDENTE").sum()
)
# Contagens individuais para os mini stats
qtd_so_acatada = int(
    (julgamentos_filtrados["resultado_camara_padronizado"] == "ACATADA").sum()
)
qtd_ac_parcial = int(
    (julgamentos_filtrados["resultado_camara_padronizado"] == "ACATADA PARCIALMENTE").sum()
)

denominador_taxa = qtd_acatadas + qtd_nao_acat
taxa_acatamento  = (qtd_acatadas / denominador_taxa * 100) if denominador_taxa > 0 else 0.0

# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo("📊 Indicadores da câmara de julgamento")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Processos julgados", str(total_julgados), "🏛️",
             cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A")
with col2:
    kpi_card("Pendentes de análise", str(qtd_pendentes), "⏳",
             cor_fundo="#FFFBEB", cor_borda="#F59E0B", cor_valor="#92400E",
             subtitulo="aguardando julgamento da câmara")
with col3:
    kpi_card("Taxa de acatamento", f"{taxa_acatamento:.1f}%", "✅",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D",
             subtitulo="acatadas ÷ (acatadas + não acatadas)")
with col4:
    kpi_card("Não acatadas", str(qtd_nao_acat), "❌",
             cor_fundo="#FEF2F2", cor_borda="#DC2626", cor_valor="#DC2626",
             subtitulo="defesas rejeitadas pela câmara")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Prepara dados para o gráfico de barras empilhadas por ano
# ─────────────────────────────────────────────────────────────
julgamentos_com_ano = julgamentos_filtrados.merge(
    autos_filtrados[["auto_id", "fiscalizacao_id"]], on="auto_id", how="left",
).merge(
    fiscalizacoes_filtradas[["fiscalizacao_id", "ano"]], on="fiscalizacao_id", how="left",
)

MAPA_ROTULOS = {
    "ACATADA":              "Acatada",
    "ACATADA PARCIALMENTE": "Acatada Parcialmente",
    "NÃO ACATADA":          "Não Acatada",
    "PENDENTE":             "Pendente de Análise",
    "NÃO SE APLICA":        "Não se Aplica",
    "OUTROS":               "Outros",
}
julgamentos_com_ano["resultado_label"] = (
    julgamentos_com_ano["resultado_camara_padronizado"]
    .map(MAPA_ROTULOS).fillna("Outros")
)
pivot_ano = (
    julgamentos_com_ano
    .groupby(["ano", "resultado_label"])
    .size().reset_index(name="Quantidade")
)
totais_ano         = pivot_ano.groupby("ano")["Quantidade"].transform("sum")
pivot_ano["Pct"]   = (pivot_ano["Quantidade"] / totais_ano * 100).round(1)
pivot_ano["Texto"] = pivot_ano["Pct"].apply(lambda p: f"{p:.0f}%" if p >= 8 else "")

ORDEM = ["Acatada", "Acatada Parcialmente", "Não Acatada",
         "Pendente de Análise", "Não se Aplica", "Outros"]
CORES = {
    "Acatada":              "#1E3A8A",
    "Acatada Parcialmente": "#3B82F6",
    "Não Acatada":          "#DC2626",
    "Pendente de Análise":  "#F59E0B",
    "Não se Aplica":        "#94A3B8",
    "Outros":               "#CBD5E1",
}

fig_stacked    = go.Figure()
anos_ordenados = sorted(
    julgamentos_com_ano["ano"].dropna().unique().astype(str)
)
for resultado in ORDEM:
    df_cat = pivot_ano[pivot_ano["resultado_label"] == resultado]
    if df_cat.empty:
        continue
    fig_stacked.add_trace(go.Bar(
        name=resultado,
        y=df_cat["ano"].astype(str),          # anos no eixo Y (horizontal)
        x=df_cat["Quantidade"],               # quantidades no eixo X
        orientation="h",                      # barras horizontais
        marker_color=CORES[resultado],
        text=df_cat["Texto"],
        textposition="inside",
        textfont={"size": 12, "color": "white"},
        customdata=df_cat[["Pct"]].values,
        hovertemplate=(
            f"<b>{resultado}</b><br>Ano: %{{y}}<br>"
            "Quantidade: %{x}<br>Percentual: %{customdata[0]:.1f}%<extra></extra>"
        ),
    ))

layout_sem_legend = {k: v for k, v in LAYOUT_PADRAO.items() if k != "legend"}
fig_stacked.update_layout(
    **layout_sem_legend,
    barmode="stack", height=340,
    xaxis_title="Quantidade de processos",    # eixo X agora é quantidade
    yaxis_title="Ano",                        # eixo Y agora é ano
    # categoryorder "array" garante ordem cronológica dos anos no eixo Y
    yaxis={"categoryorder": "array", "categoryarray": anos_ordenados},
    legend={"orientation": "h", "y": -0.25, "x": 0.5, "xanchor": "center"},
)

# ─────────────────────────────────────────────────────────────
# HTML dos mini stats consolidados
# Renderizado via components.html() — sem bug de escape
# ─────────────────────────────────────────────────────────────
def _html_mini_stats(acatada: int, ac_parcial: int,
                     nao_acat: int, pendentes: int,
                     taxa: float) -> str:
    """
    Painel de visão consolidada com 4 contadores em grid 2x2
    e barra de progresso da taxa de acatamento.
    """
    pct_barra = min(taxa, 100)
    cor_taxa  = "#15803d" if taxa >= 70 else "#dc2626"
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Visão consolidada
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;">
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                        padding:12px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:#1e3a8a;line-height:1;margin-bottom:3px;">
                    {acatada}
                </div>
                <div style="font-size:14px;color:#94a3b8;">Acatadas</div>
            </div>
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                        padding:12px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:#3b82f6;line-height:1;margin-bottom:3px;">
                    {ac_parcial}
                </div>
                <div style="font-size:14px;color:#94a3b8;">Ac. Parcialmente</div>
            </div>
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                        padding:12px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:#dc2626;line-height:1;margin-bottom:3px;">
                    {nao_acat}
                </div>
                <div style="font-size:14px;color:#94a3b8;">Não Acatadas</div>
            </div>
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                        padding:12px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:#f59e0b;line-height:1;margin-bottom:3px;">
                    {pendentes}
                </div>
                <div style="font-size:14px;color:#94a3b8;">Pendentes</div>
            </div>
        </div>
        <div style="border-top:.5px solid #e2e8f0;padding-top:14px;">
            <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                        letter-spacing:.06em;color:#94a3b8;margin-bottom:8px;">
                Taxa de acatamento
            </div>
            <div style="height:12px;background:#e2e8f0;border-radius:99px;overflow:hidden;margin-bottom:5px;">
                <div style="width:{pct_barra:.1f}%;height:100%;background:{cor_taxa};border-radius:99px;">
                </div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:14px;">
                <span style="color:#94a3b8;">0%</span>
                <span style="color:{cor_taxa};font-weight:700;font-size:14px;">{taxa:.1f}%</span>
                <span style="color:#94a3b8;">100%</span>
            </div>
        </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Faixa 1: Barras empilhadas (Plotly) + Mini stats
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📊 Distribuição dos resultados por ano",
    "Composição das decisões da câmara ao longo dos anos",
)

col_stack, col_stats = st.columns([2, 1])

with col_stack:
    # Plotly mantido nesta seção — hover interativo é valioso para análise
    st.plotly_chart(fig_stacked, use_container_width=True)

with col_stats:
    # Altura calculada: 4 cards (2x2) + barra de taxa + cabeçalho ≈ 370px
    components.html(
        _html_mini_stats(
            qtd_so_acatada, qtd_ac_parcial,
            qtd_nao_acat, qtd_pendentes,
            taxa_acatamento,
        ),
        height=370,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Prepara dados das categorias não acatadas
# ─────────────────────────────────────────────────────────────
ids_nao_acatados_auto = julgamentos_filtrados[
    julgamentos_filtrados["resultado_camara_padronizado"] == "NÃO ACATADA"
]["auto_id"].unique().tolist()

ids_nao_acatados_fisc = (
    autos_filtrados[autos_filtrados["auto_id"].isin(ids_nao_acatados_auto)]
    ["fiscalizacao_id"].unique().tolist()
)

cat_count = pd.DataFrame(columns=["Categoria", "Quantidade", "Percentual"])
total_cat = 0

if ids_nao_acatados_fisc:
    det_nao_acat = dados_filtrados["determinacoes"][
        dados_filtrados["determinacoes"]["fiscalizacao_id"].isin(ids_nao_acatados_fisc)
    ].copy()

    if not det_nao_acat.empty:
        cat_count = (
            det_nao_acat.groupby("categoria_padronizada").size()
            .reset_index(name="Quantidade")
            .sort_values("Quantidade", ascending=False)
            .reset_index(drop=True)
        )
        total_cat = int(cat_count["Quantidade"].sum())
        cat_count["Percentual"] = (
            cat_count["Quantidade"] / total_cat * 100
        ).round(1)

max_cat = int(cat_count["Quantidade"].max()) if not cat_count.empty else 1


def _html_barras_categorias(df: pd.DataFrame, max_val: int, total: int) -> str:
    """
    Barras horizontais das categorias não acatadas.

    Gradiente de cor por intensidade: vermelho escuro para as 3 primeiras
    (maior volume), laranja para as intermediárias, amarelo para as menores.
    Mostra percentual à direita de cada barra.
    Rodapé com total de determinações em processos rejeitados.
    """
    linhas = ""
    for i, (_, row) in enumerate(df.iterrows()):
        cat = str(row["categoria_padronizada"])
        qtd = int(row["Quantidade"])
        pct = float(row["Percentual"])
        pct_barra = max(2, round(qtd / max_val * 100, 1))

        # Cor por posição no ranking
        if i < 3:
            cor = "#dc2626"   # vermelho — top 3
        elif i < 6:
            cor = "#f97316"   # laranja — intermediárias
        else:
            cor = "#fbbf24"   # amarelo — menores

        linhas += f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <div style="font-size:14px;color:#64748b;min-width:108px;text-align:right;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {cat}
            </div>
            <div style="flex:1;height:15px;background:#e2e8f0;border-radius:3px;overflow:hidden;">
                <div style="width:{pct_barra}%;height:100%;background:{cor};border-radius:3px;"></div>
            </div>
            <div style="font-size:14px;font-weight:600;color:#334155;min-width:36px;">
                {pct:.1f}%
            </div>
        </div>
        """

    rodape = ""
    if total > 0:
        rodape = f"""
        <div style="display:flex;gap:8px;background:#fffbeb;border-left:3px solid #f59e0b;
                    border-radius:6px;padding:8px 10px;margin-top:12px;
                    font-size:14px;color:#92400e;">
            💡 {total:,} determinações em processos Não Acatados
        </div>
        """

    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            🔴 Não acatadas por categoria
        </div>
        {linhas}
        {rodape}
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Faixa 2: Categorias (estreita) + Tabela pendentes (larga)
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "🔴 Não acatadas · Processos pendentes",
    "Categorias com defesas rejeitadas · Casos aguardando julgamento",
)

col_cat, col_pend = st.columns([1, 1.6])

with col_cat:
    if not cat_count.empty:
        # Altura ≈ 26px por categoria + 80px cabeçalho e rodapé
        altura_cat = len(cat_count) * 26 + 80
        components.html(
            _html_barras_categorias(cat_count, max_cat, total_cat),
            height=altura_cat,
        )
    elif not ids_nao_acatados_fisc:
        alerta_informacao("Nenhum processo 'Não Acatado' para os filtros selecionados.")
    else:
        alerta_informacao("Não foi possível cruzar determinações com os processos não acatados.")

with col_pend:
    # Tabela de pendentes — st.dataframe nativo com exportação Excel
    pendentes_df = julgamentos_filtrados[
        julgamentos_filtrados["resultado_padronizado"] == "Pendente de Análise"
    ].copy()

    if pendentes_df.empty:
        alerta_informacao("✅ Não há processos pendentes para os filtros selecionados.")
    else:
        pendentes_enriquecidos = pendentes_df.merge(
            autos_filtrados[["auto_id", "fiscalizacao_id", "termo", "auto_num"]],
            on="auto_id", how="left",
        ).merge(
            fiscalizacoes_filtradas[["fiscalizacao_id", "municipio", "regional", "ano", "objeto"]],
            on="fiscalizacao_id", how="left",
        )

        colunas_exibir = {
            "termo":           "Termo",
            "auto_num":        "Auto",
            "municipio":       "Município",
            "regional":        "Regional",
            "ano":             "Ano",
            "objeto":          "Objeto da Fiscalização",
            "resultado_agems": "Resultado AGEMS",
        }
        df_pend = (
            pendentes_enriquecidos[list(colunas_exibir.keys())]
            .rename(columns=colunas_exibir)
        )

        alerta_atencao(f"{len(df_pend)} processos aguardando julgamento.")

        # Configuração de colunas para o dataframe nativo
        col_cfg = {
            "Termo":                st.column_config.TextColumn(width="medium"),
            "Objeto da Fiscalização": st.column_config.TextColumn(width="large"),
            "Resultado AGEMS":      st.column_config.TextColumn(width="medium"),
            "Ano":                  st.column_config.NumberColumn(width="small"),
        }
        st.dataframe(
            df_pend,
            use_container_width=True,
            height=350,
            hide_index=True,
            column_config=col_cfg,
        )

        # Exportação para Excel
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_pend.to_excel(w, index=False, sheet_name="Pendentes")
        st.download_button(
            "📥 Exportar para Excel",
            data=buf.getvalue(),
            file_name="processos_pendentes_camara.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
