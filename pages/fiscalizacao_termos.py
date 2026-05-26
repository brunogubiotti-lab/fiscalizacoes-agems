"""
pages/fiscalizacao_termos.py
===============================
Fiscalização · Termos de Notificação
KPIs, determinações por município/categoria/setor, tabela detalhada.

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.
    - carregar_todas_as_planilhas() substituído por alias _planilhas_cache
      com @st.cache_data — sem segunda leitura do Excel por sessão.

REDESIGN v7.0:
    - KPIs: mantidos exatamente como estavam (kpi_card original).
    - Seções de análise (município / categoria / setor) unificadas em grid
      de 3 colunas, sem título separado por seção.
    - Gráficos convertidos de Plotly para barras horizontais CSS puras
      (município e setor) e donut SVG inline (categoria), usando
      st.components.v1.html() para evitar o bug de escape do st.markdown.
    - Detalhamento por TN: mantido integralmente.

AJUSTE v7.1:
    - Tabela completa (município) e Resumo por setor REMOVIDOS — não
      estavam no esboço aprovado.
    - Proporções das colunas: [1.4, 1, 1.4] — município e setor ganham
      mais espaço horizontal; categoria fica centralizada.
    - Fontes aumentadas em todos os gráficos:
        · rótulos de município/setor: 11px → 13px
        · valores numéricos:          11px → 13px bold
        · altura das barras:          13-14px → 16px
        · espaçamento entre barras:   7px → 9px
        · donut SVG: raio 44 → 54 (viewBox 120 → 140); texto central maior
        · legenda do donut: 10px → 12px; dot 9px → 11px
    - Altura dos componentes recalculada para acomodar fontes maiores.

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

from utils.data_loader import carregar_dados_tratados, carregar_todas_as_planilhas as _planilhas_cache
from utils.filters import renderizar_filtros_sidebar, aplicar_todos_filtros
from utils.metrics import (
    calcular_total_tns, calcular_total_determinacoes,
    calcular_municipio_com_mais_tns, calcular_media_determinacoes_por_tn,
)
from utils.ui_components import (
    kpi_card, secao_titulo,
    alerta_atencao, sem_dados,
)
from utils.charts import PALETA_CATEGORICA

# ─────────────────────────────────────────────────────────────
# Carrega dados e aplica filtros
# ─────────────────────────────────────────────────────────────
filtros = renderizar_filtros_sidebar()
dados   = carregar_dados_tratados()

dados_filtrados         = aplicar_todos_filtros(dados, filtros)
fiscalizacoes_filtradas = dados_filtrados["fiscalizacoes"]
autos_filtrados         = dados_filtrados["autos_infracao"]
julgamentos_filtrados   = dados_filtrados["julgamentos"]
det_filtradas           = dados_filtrados["determinacoes"]

if fiscalizacoes_filtradas.empty:
    sem_dados()
    st.stop()

# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo("📊 Indicadores gerais")

total_tns_t         = calcular_total_tns(fiscalizacoes_filtradas)
total_det_t         = calcular_total_determinacoes(det_filtradas)
municipio_top, qt_t = calcular_municipio_com_mais_tns(fiscalizacoes_filtradas)
media_det_t         = calcular_media_determinacoes_por_tn(fiscalizacoes_filtradas, det_filtradas)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Total de TNs", str(total_tns_t), "📋",
             cor_fundo="#EFF6FF", cor_borda="#3B82F6", cor_valor="#1E3A8A")
with col2:
    kpi_card("Total de determinações", f"{total_det_t:,}", "📌",
             cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E")
with col3:
    kpi_card("Município c/ maior volume", municipio_top, "🏙️",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor="#15803D",
             subtitulo=f"{qt_t} TNs")
with col4:
    kpi_card("Média det./TN", str(media_det_t), "📐",
             cor_fundo="#FDF4FF", cor_borda="#A855F7", cor_valor="#7E22CE",
             subtitulo="determinações por termo")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Prepara os dados dos 3 gráficos analíticos
# ─────────────────────────────────────────────────────────────

# ── Município ────────────────────────────────────────────────
# Faz left join para trazer o município de cada determinação,
# agrupa e ordena decrescente, limita ao Top 10.
det_com_mun = det_filtradas.merge(
    fiscalizacoes_filtradas[["fiscalizacao_id", "municipio"]],
    on="fiscalizacao_id", how="left",
)
det_por_mun = (
    det_com_mun.groupby("municipio").size()
    .reset_index(name="Determinações")
    .sort_values("Determinações", ascending=False)
)
top10_mun = det_por_mun.head(10)
max_mun   = int(top10_mun["Determinações"].max()) if not top10_mun.empty else 1

# ── Categoria ────────────────────────────────────────────────
# Agrupa por categoria padronizada; usa PALETA_CATEGORICA do sistema
# para manter consistência de cores com as outras abas.
det_por_cat   = (
    det_filtradas.groupby("categoria_padronizada").size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
)
total_det_cat = int(det_por_cat["Quantidade"].sum()) if not det_por_cat.empty else 0

# ── Setor ────────────────────────────────────────────────────
det_por_setor = (
    det_filtradas.groupby("setor").size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
)
max_setor = int(det_por_setor["Quantidade"].max()) if not det_por_setor.empty else 1


# ─────────────────────────────────────────────────────────────
# Funções de geração de HTML puro (style inline, sem classes CSS)
# Todos os blocos são renderizados via st.components.v1.html()
# para evitar o bug de escape do st.markdown com class+style.
# ─────────────────────────────────────────────────────────────

def _html_barras_municipio(df: pd.DataFrame, max_val: int) -> str:
    """
    Painel Top 10 municípios — barras horizontais navy.

    Largura de cada barra = (det / max_det) * 100%, mínimo 4%.
    Fontes: 13px para rótulos e valores (leitura confortável na tela cheia).
    Barras: 16px de altura.
    """
    linhas = ""
    for _, row in df.iterrows():
        pct = max(4, round(row["Determinações"] / max_val * 100, 1))
        linhas += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:9px;">
            <div style="font-size:14px;color:#64748b;min-width:110px;text-align:right;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {row['municipio']}
            </div>
            <div style="flex:1;height:16px;background:#e2e8f0;border-radius:4px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:#1e3a8a;border-radius:4px;"></div>
            </div>
            <div style="font-size:14px;font-weight:600;color:#334155;min-width:34px;">
                {int(row['Determinações'])}
            </div>
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:2px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Top 10 por município
        </div>
        {linhas}
    </div>
    """


def _html_donut_categoria(df: pd.DataFrame, total: int) -> str:
    """
    Donut SVG + legenda para distribuição por categoria.

    Geometria (v7.1 — maior):
        viewBox  140x140, centro (70,70), raio 54, stroke-width 22.
        Circunferência = 2 * pi * 54 ≈ 339.3.
    Cada fatia: stroke-dasharray = (pct/100)*339.3  espaço  339.3.
    Offset acumulado rotacionado -90° para começar no topo.

    Legenda: 12px, dot 11px — mais legível que a versão anterior (10px/9px).
    Exibe no máximo 7 categorias para não poluir.
    """
    _CORES_FALLBACK = [
        "#1e3a8a", "#2563eb", "#16a34a", "#ca8a04",
        "#dc2626", "#9333ea", "#0891b2", "#94a3b8",
    ]
    paleta = list(PALETA_CATEGORICA) if PALETA_CATEGORICA else _CORES_FALLBACK
    while len(paleta) < len(df):
        paleta += _CORES_FALLBACK

    circunf = 339.3   # 2 * pi * 54
    offset  = 0.0
    fatias  = ""
    legenda = ""

    for i, (_, row) in enumerate(df.iterrows()):
        pct        = row["Quantidade"] / total * 100 if total else 0
        comprimento = round(pct / 100 * circunf, 2)
        cor         = paleta[i % len(paleta)]

        fatias += (
            f'<circle cx="70" cy="70" r="54" fill="none"'
            f' stroke="{cor}" stroke-width="22"'
            f' stroke-dasharray="{comprimento} {circunf}"'
            f' stroke-dashoffset="{-offset:.2f}"'
            f' transform="rotate(-90 70 70)"/>'
        )
        offset += comprimento

        # Legenda: máximo 7 categorias
        if i < 7:
            nome_curto = str(row["categoria_padronizada"])[:20]
            legenda += f"""
            <div style="display:flex;align-items:center;gap:7px;margin-bottom:7px;">
                <div style="width:11px;height:11px;border-radius:50%;
                            background:{cor};flex-shrink:0;"></div>
                <div style="font-size:14px;color:#64748b;flex:1;">{nome_curto}</div>
                <div style="font-size:14px;font-weight:600;color:#334155;">{pct:.1f}%</div>
            </div>
            """

    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:2px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Por categoria
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:14px;">
            <svg width="140" height="140" viewBox="0 0 140 140">
                <circle cx="70" cy="70" r="54" fill="none"
                    stroke="#e2e8f0" stroke-width="22"/>
                {fatias}
                <text x="70" y="65" text-anchor="middle"
                    font-size="16" font-weight="700" fill="#1e293b">{total:,}</text>
                <text x="70" y="82" text-anchor="middle"
                    font-size="11" fill="#94a3b8">det.</text>
            </svg>
            <div style="width:100%;">{legenda}</div>
        </div>
    </div>
    """


def _html_barras_setor(df: pd.DataFrame, max_val: int) -> str:
    """
    Painel de setores responsáveis — barras verdes.

    Largura = (qtd / max_qtd) * 100%, mínimo 3%.
    Valor numérico à direita da barra (fora dela) para sempre ser legível.
    Fontes: 13px (era 11px). Barras: 16px (era 14px).
    """
    linhas = ""
    for _, row in df.iterrows():
        pct = max(3, round(row["Quantidade"] / max_val * 100, 1))
        linhas += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:9px;">
            <div style="font-size:14px;color:#64748b;min-width:72px;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {row['setor']}
            </div>
            <div style="flex:1;height:16px;background:#e2e8f0;border-radius:4px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:#16a34a;border-radius:4px;"></div>
            </div>
            <div style="font-size:14px;font-weight:600;color:#334155;min-width:36px;">
                {int(row['Quantidade'])}
            </div>
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:2px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Por setor responsável
        </div>
        {linhas}
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Renderiza o bloco analítico em 3 colunas
#
# Proporções [1.4, 1, 1.4]:
#   - município e setor ganham mais espaço horizontal para as
#     barras ficarem mais longas e legíveis
#   - categoria fica centralizada com o donut bem enquadrado
#
# Sem tabelas neste bloco (removidas em v7.1).
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📊 Análise de determinações",
    "Município · Categoria · Setor responsável",
)

col_mun, col_cat, col_set = st.columns([1.4, 1, 1.4])

# ── Coluna 1: Top 10 municípios ──────────────────────────────
with col_mun:
    if not top10_mun.empty:
        # Altura: 28px por barra (16px barra + 9px gap + 3px margem) + 55px header
        altura_mun = len(top10_mun) * 28 + 55
        components.html(
            _html_barras_municipio(top10_mun, max_mun),
            height=altura_mun,
        )

# ── Coluna 2: Donut de categoria ─────────────────────────────
with col_cat:
    if not det_por_cat.empty:
        n_cats     = min(len(det_por_cat), 7)
        # 140px SVG + 14px gap + (n_cats * 26px legenda) + 55px header
        altura_cat = 140 + 14 + n_cats * 26 + 55
        components.html(
            _html_donut_categoria(det_por_cat, total_det_cat),
            height=altura_cat,
        )

# ── Coluna 3: Barras de setor ────────────────────────────────
with col_set:
    if not det_por_setor.empty:
        # Mesma lógica de altura do município
        altura_set = len(det_por_setor) * 28 + 55
        components.html(
            _html_barras_setor(det_por_setor, max_setor),
            height=altura_set,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Detalhamento por Termo de Notificação
# Mantido integralmente da versão anterior (lógica + exportação).
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📄 Detalhamento por Termo de Notificação",
    "Termos · Determinações · Constatações vinculadas",
)

det_tab = det_filtradas[["termo", "num_det", "desc_det", "categoria_padronizada"]].copy()

try:
    # _planilhas_cache usa @st.cache_data — retorno já está em memória,
    # não gera segunda leitura do Excel nesta sessão.
    _pl2    = _planilhas_cache()
    cons_r2 = _pl2.get("constatacoes", pd.DataFrame())
except Exception:
    cons_r2 = pd.DataFrame()

if not cons_r2.empty and "fiscalizacao_id" in cons_r2.columns:
    ids_ff  = set(fiscalizacoes_filtradas["fiscalizacao_id"].tolist())
    cols_c  = [c for c in ["num_constatacao", "desc_constatacao"] if c in cons_r2.columns]
    cons_f2 = cons_r2[cons_r2["fiscalizacao_id"].isin(ids_ff)][["fiscalizacao_id"] + cols_c].copy()
    if "num_constatacao"  in cons_f2.columns: cons_f2["num_cons"]  = cons_f2["num_constatacao"]
    if "desc_constatacao" in cons_f2.columns: cons_f2["desc_cons"] = cons_f2["desc_constatacao"]
    df_fin = det_filtradas[
        ["termo", "num_det", "desc_det", "categoria_padronizada", "fiscalizacao_id"]
    ].merge(
        cons_f2[["fiscalizacao_id", "num_cons", "desc_cons"]],
        on="fiscalizacao_id", how="left",
    ).drop(columns=["fiscalizacao_id"])
else:
    df_fin = det_tab.copy()

rename_map = {
    "termo":                "Termo de Notificação",
    "num_det":              "Nº Determinação",
    "desc_det":             "Descrição Determinação",
    "categoria_padronizada":"Categoria",
    "num_cons":             "Nº Constatação",
    "desc_cons":            "Descrição Constatação",
}
df_ex_tn = df_fin.rename(
    columns={k: v for k, v in rename_map.items() if k in df_fin.columns}
).reset_index(drop=True)

if df_ex_tn.empty:
    alerta_atencao("Não foi possível montar a tabela detalhada com os filtros atuais.")
else:
    st.caption(f"📊 {len(df_ex_tn):,} linhas")

    # CSS de scroll horizontal — injeta via st.markdown para sobrescrever
    # o overflow padrão do container Streamlit que envolve o dataframe.
    st.markdown(
        """
        <style>
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            overflow-y: auto !important;
        }
        [data-testid="stDataFrame"] > div::-webkit-scrollbar { height: 8px; }
        [data-testid="stDataFrame"] > div::-webkit-scrollbar-track {
            background: #f1f5f9; border-radius: 4px;
        }
        [data-testid="stDataFrame"] > div::-webkit-scrollbar-thumb {
            background: #94a3b8; border-radius: 4px;
        }
        [data-testid="stDataFrame"] > div::-webkit-scrollbar-thumb:hover {
            background: #3B82F6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Configuração de largura das colunas no dataframe nativo
    col_cfg = {}
    for nm, lg in [
        ("Termo de Notificação",   "medium"),
        ("Descrição Determinação", "large"),
        ("Categoria",              "medium"),
        ("Descrição Constatação",  "large"),
    ]:
        if nm in df_ex_tn.columns:
            col_cfg[nm] = st.column_config.TextColumn(width=lg)
    for nm in ["Nº Determinação", "Nº Constatação"]:
        if nm in df_ex_tn.columns:
            col_cfg[nm] = st.column_config.NumberColumn(width="small")

    st.dataframe(df_ex_tn, use_container_width=True, height=480, column_config=col_cfg)

    # Exportação para Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_ex_tn.to_excel(w, index=False, sheet_name="Detalhamento")
    st.download_button(
        "📥 Exportar para Excel",
        data=buf.getvalue(),
        file_name="detalhamento_tn_determinacoes_constatacoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
