"""
pages/financeiro_boletos.py
=============================
Painel Financeiro · Boletos emitidos

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.

CORREÇÃO v6.1:
    - Eixo X dos gráficos de evolução anual corrigido para tipo categórico.

REDESIGN v7.0 — Esboço 2 "Gráficos + Tabela lado a lado":
    - KPIs: mantidos exatamente como estavam (kpi_card original, 3 colunas).
    - Layout principal em 2 colunas [1, 1.6]:
        · Coluna esquerda: barras horizontais CSS de evolução (quantidade e
          valor) + mini stats de crescimento anual (% qtd e % valor).
        · Coluna direita: tabela de boletos (st.dataframe nativo) com
          exportação Excel e alerta informativo.
    - Gráficos CSS renderizados via st.components.v1.html() com estilos
      inline para evitar bug de escape do st.markdown.
    - Tabela: st.dataframe nativo com NumberColumn formatado em R$.
    - Tudo visível sem scroll excessivo — página compacta.

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
    calcular_boletos_emitidos,
    formatar_moeda, formatar_percentual,
)
from utils.ui_components import (
    kpi_card, secao_titulo,
    alerta_informacao, alerta_atencao, sem_dados,
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
# Métricas base
# ─────────────────────────────────────────────────────────────
total_boletos       = calcular_boletos_emitidos(autos_filtrados)
boletos_com_valor   = boletos_filtrados[boletos_filtrados["valor_boleto"] > 0]
valor_total_boletos = float(boletos_com_valor["valor_boleto"].sum())
qtd_boletos_reais   = len(boletos_com_valor)
ticket_boleto       = (
    valor_total_boletos / qtd_boletos_reais
) if qtd_boletos_reais > 0 else 0.0

# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo("🧾 Indicadores de boletos")

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Boletos emitidos", str(total_boletos), "🧾",
             cor_fundo="#FDF4FF", cor_borda="#A855F7", cor_valor="#7E22CE",
             subtitulo="autos com boleto registrado")
with col2:
    kpi_card("Valor total de boletos", formatar_moeda(valor_total_boletos), "💳",
             cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A",
             subtitulo=f"em {qtd_boletos_reais} boletos com valor")
with col3:
    kpi_card("Valor médio por boleto", formatar_moeda(ticket_boleto), "🎫",
             cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Prepara dados anuais para o gráfico de evolução
# ─────────────────────────────────────────────────────────────
boletos_com_ano = boletos_com_valor.merge(
    autos_filtrados[["auto_id", "fiscalizacao_id"]], on="auto_id", how="left",
).merge(
    fiscalizacoes_filtradas[["fiscalizacao_id", "ano"]], on="fiscalizacao_id", how="left",
)

boletos_por_ano = pd.DataFrame()
if not boletos_com_ano.empty and "ano" in boletos_com_ano.columns:
    # dropna + astype(int) evita "2022.0" float no eixo
    boletos_limpo = boletos_com_ano.dropna(subset=["ano"]).copy()
    boletos_limpo["ano"] = boletos_limpo["ano"].astype(int)

    boletos_por_ano = (
        boletos_limpo
        .groupby("ano")
        .agg(
            quantidade =("boleto_id",    "count"),
            valor_total=("valor_boleto", "sum"),
        )
        .reset_index()
        .sort_values("ano")
    )
    boletos_por_ano["ano_str"] = boletos_por_ano["ano"].astype(str)


def _html_evolucao(df: pd.DataFrame) -> str:
    """
    Gera o painel de evolução anual com:
      - Barras horizontais de quantidade (navy)
      - Barras horizontais de valor (verde)
      - Mini stats de crescimento anual (% qtd e % valor)

    Cálculo de crescimento: compara primeiro e último ano do DataFrame.
    Se houver apenas 1 ano, exibe apenas as barras sem os mini stats.

    Largura das barras: proporcional ao máximo de cada série.
    Mínimo de 3% para barras pequenas ficarem visíveis.
    """
    if df.empty:
        return "<div style='font-size:14px;color:#94a3b8;'>Sem dados de evolução.</div>"

    max_qtd = int(df["quantidade"].max())
    max_val = float(df["valor_total"].max())

    # ── Barras de quantidade ─────────────────────────────
    barras_qtd = ""
    for _, row in df.iterrows():
        pct = max(3, round(row["quantidade"] / max_qtd * 100, 1))
        barras_qtd += f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;
                        font-size:14px;margin-bottom:4px;">
                <span style="font-weight:600;color:#334155;">{row['ano_str']}</span>
                <span style="font-weight:700;color:#1e3a8a;">{int(row['quantidade'])}</span>
            </div>
            <div style="height:14px;background:#e2e8f0;border-radius:99px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:#1e3a8a;border-radius:99px;">
                </div>
            </div>
        </div>
        """

    # ── Barras de valor ──────────────────────────────────
    barras_val = ""
    for _, row in df.iterrows():
        pct = max(3, round(row["valor_total"] / max_val * 100, 1))
        v   = float(row["valor_total"])
        v_fmt = f"R$ {v/1_000_000:.2f}M" if v >= 1_000_000 else f"R$ {v/1_000:.0f}k"
        barras_val += f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;
                        font-size:14px;margin-bottom:4px;">
                <span style="font-weight:600;color:#334155;">{row['ano_str']}</span>
                <span style="font-weight:700;color:#16a34a;">{v_fmt}</span>
            </div>
            <div style="height:14px;background:#e2e8f0;border-radius:99px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:#16a34a;border-radius:99px;">
                </div>
            </div>
        </div>
        """

    # ── Mini stats de crescimento (só se houver ≥2 anos) ─
    mini_stats = ""
    if len(df) >= 2:
        qtd_ini  = int(df["quantidade"].iloc[0])
        qtd_fim  = int(df["quantidade"].iloc[-1])
        val_ini  = float(df["valor_total"].iloc[0])
        val_fim  = float(df["valor_total"].iloc[-1])

        # Crescimento: evita divisão por zero
        cresc_qtd = round((qtd_fim - qtd_ini) / qtd_ini * 100, 1) if qtd_ini else 0
        cresc_val = round((val_fim - val_ini) / val_ini * 100, 1) if val_ini else 0

        def _cor_cresc(v: float) -> str:
            return "#15803d" if v >= 0 else "#dc2626"

        def _sinal(v: float) -> str:
            return f"+{v:.1f}%" if v >= 0 else f"{v:.1f}%"

        mini_stats = f"""
        <div style="border-top:.5px solid #e2e8f0;padding-top:14px;margin-top:4px;">
            <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                        letter-spacing:.06em;color:#94a3b8;margin-bottom:10px;">
                Crescimento
                {df['ano_str'].iloc[0]} → {df['ano_str'].iloc[-1]}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                            padding:10px;text-align:center;">
                    <div style="font-size:20px;font-weight:700;
                                color:{_cor_cresc(cresc_qtd)};line-height:1;margin-bottom:3px;">
                        {_sinal(cresc_qtd)}
                    </div>
                    <div style="font-size:14px;color:#94a3b8;">em quantidade</div>
                </div>
                <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                            padding:10px;text-align:center;">
                    <div style="font-size:20px;font-weight:700;
                                color:{_cor_cresc(cresc_val)};line-height:1;margin-bottom:3px;">
                        {_sinal(cresc_val)}
                    </div>
                    <div style="font-size:14px;color:#94a3b8;">em valor</div>
                </div>
            </div>
        </div>
        """

    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:12px;">
            Quantidade de boletos por ano
        </div>
        {barras_qtd}
        <div style="border-top:.5px solid #e2e8f0;padding-top:14px;margin:4px 0 12px;">
            <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                        letter-spacing:.06em;color:#94a3b8;margin-bottom:12px;">
                Valor total de boletos por ano (R$)
            </div>
            {barras_val}
        </div>
        {mini_stats}
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Prepara tabela de boletos
# ─────────────────────────────────────────────────────────────
df_bol = pd.DataFrame()
if not boletos_com_valor.empty:
    boletos_tabela = boletos_com_valor.merge(
        autos_filtrados[["auto_id", "termo", "auto_num", "fiscalizacao_id"]],
        on="auto_id", how="left",
    ).merge(
        fiscalizacoes_filtradas[["fiscalizacao_id", "municipio", "regional", "ano"]],
        on="fiscalizacao_id", how="left",
    )

    df_bol = boletos_tabela[[
        "termo", "auto_num", "numero_boleto",
        "municipio", "regional", "ano", "valor_boleto",
    ]].rename(columns={
        "termo":         "Termo",
        "auto_num":      "Nº Auto",
        "numero_boleto": "Nº Boleto",
        "municipio":     "Município",
        "regional":      "Regional",
        "ano":           "Ano",
        "valor_boleto":  "Valor (R$)",
    }).sort_values("Valor (R$)", ascending=False).reset_index(drop=True)

# ─────────────────────────────────────────────────────────────
# Renderização: 2 colunas [1, 1.6]
# Coluna esquerda: gráfico de evolução CSS
# Coluna direita : tabela de boletos + alerta + exportação
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📈 Evolução anual · Tabela de boletos",
    "Boletos por ano e detalhamento completo por auto",
)

col_graf, col_tbl = st.columns([1, 1.6])

with col_graf:
    if not boletos_por_ano.empty:
        # Altura: 2 seções de barras + mini stats + cabeçalhos ≈ 480px
        n_anos      = len(boletos_por_ano)
        altura_graf = n_anos * 38 * 2 + 200   # 2 séries × linhas × altura + overhead
        components.html(
            _html_evolucao(boletos_por_ano),
            height=max(480, altura_graf),
        )
    else:
        alerta_atencao("Não há dados de boletos com valor para os filtros selecionados.")

with col_tbl:
    if df_bol.empty:
        alerta_atencao("Nenhum boleto com valor encontrado para os filtros selecionados.")
    else:
        st.caption(f"📊 {len(df_bol):,} boletos com valor registrado")

        col_cfg = {
            "Termo":      st.column_config.TextColumn(width="medium"),
            "Nº Auto":    st.column_config.TextColumn(width="small"),
            "Nº Boleto":  st.column_config.TextColumn(width="small"),
            "Município":  st.column_config.TextColumn(width="medium"),
            "Regional":   st.column_config.TextColumn(width="medium"),
            "Ano":        st.column_config.NumberColumn(width="small"),
            "Valor (R$)": st.column_config.NumberColumn(
                format="R$ %.2f", width="medium"
            ),
        }

        st.dataframe(
            df_bol,
            use_container_width=True,
            height=420,
            hide_index=True,
            column_config=col_cfg,
        )

        # Exportação para Excel
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_bol.to_excel(w, index=False, sheet_name="Boletos")
        st.download_button(
            "📥 Exportar para Excel",
            data=buf.getvalue(),
            file_name="boletos_emitidos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        alerta_informacao(
            "Somente boletos com valor > 0 são exibidos nesta aba. "
            "Boletos com valor zero indicam autos em que o valor ainda não foi definido."
        )
