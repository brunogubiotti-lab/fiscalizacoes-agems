"""
pages/juridico_diretoria.py
=============================
Painel Jurídico · Decisões: diretoria

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.

CORREÇÃO v6.1:
    - Eixo X dos gráficos corrigido para tipo categórico.

REDESIGN v7.0 — Esboço 1 "Linear empilhado":
    - KPIs: mantidos exatamente como estavam (kpi_card original).
    - Gráfico de barras agrupadas por município: substituído por barras
      horizontais duplas CSS puras (prelim / def), com nome e valores
      exibidos diretamente em cada linha — mais legível que o Plotly
      com 15 municípios no eixo X.
    - Seção "Efetividade regulatória por ano" REMOVIDA conforme solicitado.
    - Tabela de autos com decisão definitiva: mantida como st.dataframe
      nativo com exportação Excel, na largura total da página.
    - alerta_informacao() mantido no rodapé.
    - Todos os gráficos CSS renderizados via st.components.v1.html()
      com estilos inline para evitar bug de escape do st.markdown.

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

from utils.data_loader import carregar_dados_tratados
from utils.filters import renderizar_filtros_sidebar, aplicar_todos_filtros
from utils.metrics import (
    calcular_valor_preliminar_total, calcular_valor_definitivo_total,
    calcular_reducao_valor, formatar_moeda, formatar_percentual,
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
julgamentos_filtrados   = dados_filtrados["julgamentos"]
autos_filtrados         = dados_filtrados["autos_infracao"]

if fiscalizacoes_filtradas.empty:
    sem_dados()
    st.stop()

autos_com_definitivo = autos_filtrados[autos_filtrados["tem_valor_definitivo"]].copy()

# ─────────────────────────────────────────────────────────────
# Cálculo de KPIs
# ─────────────────────────────────────────────────────────────
valor_prelim    = calcular_valor_preliminar_total(autos_filtrados)
valor_def       = calcular_valor_definitivo_total(autos_filtrados)
reducao_pct     = calcular_reducao_valor(autos_filtrados)
autos_def_count = len(autos_com_definitivo)
total_autos     = len(autos_filtrados)
taxa_def        = (autos_def_count / total_autos * 100) if total_autos > 0 else 0.0

# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo("📊 Indicadores de conversão · Preliminar → Definitivo")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Valor preliminar total", formatar_moeda(valor_prelim), "📄",
             cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A")
with col2:
    kpi_card("Valor definitivo total", formatar_moeda(valor_def), "✅",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D")
with col3:
    cor_red   = "#16A34A" if reducao_pct <= 0 else "#DC2626"
    label_red = "Redução após julgamento" if reducao_pct <= 0 else "Aumento após julgamento"
    kpi_card(
        label_red, formatar_percentual(abs(reducao_pct)),
        "📉" if reducao_pct <= 0 else "📈",
        cor_fundo="#FEF2F2" if reducao_pct > 0 else "#F0FDF4",
        cor_borda=cor_red, cor_valor=cor_red,
    )
with col4:
    kpi_card(
        "Autos c/ valor definitivo",
        f"{autos_def_count} ({formatar_percentual(taxa_def)})",
        "🎯",
        cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E",
        subtitulo=f"de {total_autos} autos totais",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Prepara dados para o gráfico de barras duplas por município
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "🏙️ Comparativo Preliminar vs. Definitivo por município",
    "Municípios com valor definitivo definido · Top 15",
)

if autos_com_definitivo.empty:
    alerta_atencao("Nenhum auto com valor definitivo encontrado para os filtros selecionados.")
else:
    autos_com_mun = autos_com_definitivo.merge(
        fiscalizacoes_filtradas[["fiscalizacao_id", "municipio"]],
        on="fiscalizacao_id", how="left",
    )
    comparativo = (
        autos_com_mun
        .groupby("municipio")
        .agg(
            preliminar=("valor_preliminar_num", "sum"),
            definitivo=("valor_definitivo_num",  "sum"),
        )
        .reset_index()
        .sort_values("preliminar", ascending=False)
        .head(15)
    )

    max_val = float(comparativo["preliminar"].max()) if not comparativo.empty else 1.0

    def _formatar_valor(v: float) -> str:
        """Formata valor financeiro de forma compacta: R$ 1,2M ou R$ 345k."""
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"R$ {v/1_000:.0f}k"
        return f"R$ {v:,.2f}"

    def _html_barras_comparativo(df: pd.DataFrame, max_v: float) -> str:
        """
        Gera barras horizontais duplas (preliminar / definitivo) por município.

        Estrutura de cada linha:
          - Nome do município + valores compactos no cabeçalho
          - Barra azul navy (preliminar) proporcional ao valor máximo
          - Barra verde (definitivo) proporcional ao mesmo valor máximo
          - Mínimo de 2% para barras pequenas ficarem visíveis

        A legenda fica no topo do componente.
        """
        linhas = ""
        for _, row in df.iterrows():
            mun   = str(row["municipio"])
            p_val = float(row["preliminar"])
            d_val = float(row["definitivo"])
            p_pct = max(2, round(p_val / max_v * 100, 1))
            d_pct = max(2, round(d_val / max_v * 100, 1))
            p_fmt = _formatar_valor(p_val)
            d_fmt = _formatar_valor(d_val)

            # Cor do valor definitivo: verde se reduziu, âmbar se igual, azul se aumentou
            if d_val < p_val * 0.99:
                cor_d_txt = "#15803d"
            elif d_val > p_val * 1.01:
                cor_d_txt = "#b45309"
            else:
                cor_d_txt = "#64748b"

            linhas += f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;
                            margin-bottom:4px;align-items:baseline;">
                    <span style="font-size:14px;font-weight:500;color:#334155;">{mun}</span>
                    <span style="font-size:14px;color:#94a3b8;">
                        <span style="color:#1e3a8a;font-weight:600;">{p_fmt}</span>
                        &nbsp;→&nbsp;
                        <span style="color:{cor_d_txt};font-weight:600;">{d_fmt}</span>
                    </span>
                </div>
                <div style="display:flex;flex-direction:column;gap:3px;">
                    <div style="height:9px;background:#e2e8f0;border-radius:2px;overflow:hidden;">
                        <div style="width:{p_pct}%;height:100%;background:#1e3a8a;border-radius:2px;">
                        </div>
                    </div>
                    <div style="height:9px;background:#e2e8f0;border-radius:2px;overflow:hidden;">
                        <div style="width:{d_pct}%;height:100%;background:#16a34a;border-radius:2px;">
                        </div>
                    </div>
                </div>
            </div>
            """

        return f"""
        <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
            <div style="display:flex;gap:16px;margin-bottom:16px;">
                <div style="display:flex;align-items:center;gap:5px;font-size:14px;color:#64748b;">
                    <div style="width:12px;height:9px;border-radius:2px;background:#1e3a8a;"></div>
                    Valor Preliminar
                </div>
                <div style="display:flex;align-items:center;gap:5px;font-size:14px;color:#64748b;">
                    <div style="width:12px;height:9px;border-radius:2px;background:#16a34a;"></div>
                    Valor Definitivo
                </div>
            </div>
            {linhas}
        </div>
        """

    # Altura fixa com scroll interno:
    # O componente tem altura fixa de 500px.
    # O conteúdo interno tem max-height:450px com overflow-y:auto,
    # permitindo rolar para ver todos os municípios sem crescer a página.
    def _com_scroll(html_inner: str) -> str:
        return f"""
        <div style="max-height:450px;overflow-y:auto;padding-right:4px;
                    font-family:-apple-system,'Segoe UI',sans-serif;">
            {html_inner}
        </div>
        """

    components.html(
        _com_scroll(_html_barras_comparativo(comparativo, max_val)),
        height=470,    # altura fixa do iframe — scroll ocorre dentro
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Tabela: autos com decisão definitiva — largura total
# ─────────────────────────────────────────────────────────────
secao_titulo("📋 Tabela: autos com decisão definitiva")

if autos_com_definitivo.empty:
    alerta_atencao("Nenhum auto com valor definitivo para exibir.")
else:
    # Remove duplicatas por auto_id antes de exibir
    autos_unicos = autos_com_definitivo.drop_duplicates(subset=["auto_id"]).copy()
    autos_tabela = autos_unicos.merge(
        fiscalizacoes_filtradas[["fiscalizacao_id", "municipio", "ano"]],
        on="fiscalizacao_id", how="left",
    )
    df_exibir = autos_tabela[[
        "termo", "auto_num", "municipio", "ano",
        "valor_preliminar_num", "valor_definitivo_num", "tem_boleto",
    ]].rename(columns={
        "termo":                "Termo",
        "auto_num":             "Nº Auto",
        "municipio":            "Município",
        "ano":                  "Ano",
        "valor_preliminar_num": "Valor Preliminar (R$)",
        "valor_definitivo_num": "Valor Definitivo (R$)",
        "tem_boleto":           "Possui Boleto",
    })

    # Configuração de colunas para o dataframe nativo
    col_cfg = {
        "Termo":                  st.column_config.TextColumn(width="medium"),
        "Nº Auto":                st.column_config.TextColumn(width="small"),
        "Município":              st.column_config.TextColumn(width="medium"),
        "Ano":                    st.column_config.NumberColumn(width="small"),
        "Valor Preliminar (R$)":  st.column_config.NumberColumn(
            format="R$ %.2f", width="medium"
        ),
        "Valor Definitivo (R$)":  st.column_config.NumberColumn(
            format="R$ %.2f", width="medium"
        ),
        "Possui Boleto":          st.column_config.CheckboxColumn(width="small"),
    }

    st.dataframe(
        df_exibir,
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config=col_cfg,
    )

    # Exportação para Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_exibir.to_excel(w, index=False, sheet_name="Autos Definitivos")
    st.download_button(
        "📥 Exportar para Excel",
        data=buf.getvalue(),
        file_name="autos_com_decisao_definitiva.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

alerta_informacao(
    "A efetividade regulatória é medida pela taxa de conversão "
    "(percentual de autos que chegam ao valor definitivo) e pela "
    "diferença entre valor preliminar e definitivo."
)
