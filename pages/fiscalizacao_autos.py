"""
pages/fiscalizacao_autos.py
==============================
Fiscalização · Autos de Infração
KPIs, conversão TN→AI, análise de risco, recorrência de constatações.

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — agora está apenas em app.py.
    - Removido injetar_css_global() — injetado uma única vez em app.py.

REDESIGN v7.0 — Esboço 3 "Assimétrico + donut":
    - KPIs: mantidos exatamente como estavam (kpi_card original).
    - Faixa 1: donut SVG de conversão (coluna estreita 1fr) + barras
      horizontais de categorias (coluna larga 2fr).
    - Faixa 2: painel de pesos + "Como ler" embutido (0.7fr) /
      ranking Top 10 em barras CSS (1fr) / heatmap completo (1.3fr).
    - Blocos "Como ler" integrados dentro dos painéis — sem seções
      separadas que geram scroll.
    - Todos os gráficos renderizados via st.components.v1.html()
      com estilos inline para evitar o bug de escape do st.markdown.
    - Sliders de peso mantidos com st.slider() nativo do Streamlit.
    - Lógica de cálculo do score e heatmap: idêntica à versão anterior.

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline (components.html),
      blocos f-string e CSS embarcado em st.markdown.
    - Nenhuma lógica de dados ou layout foi alterada.
"""
import io
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from utils.data_loader import carregar_dados_tratados
from utils.filters import renderizar_filtros_sidebar, aplicar_todos_filtros
from utils.metrics import (
    calcular_total_autos, calcular_valor_preliminar_total,
    calcular_taxa_conversao_tn_ai, formatar_moeda, formatar_percentual,
)
from utils.ui_components import (
    kpi_card, secao_titulo, alerta_atencao, sem_dados,
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

# Constatações: reutiliza o dict já carregado — sem segunda leitura do Excel
try:
    from utils.data_loader import carregar_todas_as_planilhas as _planilhas_cache
    _todas      = _planilhas_cache()
    cons_bruta  = _todas.get("constatacoes", pd.DataFrame())
    if not cons_bruta.empty and "desc_constatacao" in cons_bruta.columns:
        ids_fisc       = set(fiscalizacoes_filtradas["fiscalizacao_id"].tolist())
        cons_filtradas = cons_bruta[cons_bruta["fiscalizacao_id"].isin(ids_fisc)].copy()
        cons_filtradas["desc_cons"] = cons_filtradas["desc_constatacao"]
    else:
        cons_filtradas = pd.DataFrame()
except Exception:
    cons_filtradas = pd.DataFrame()

autos_tab      = autos_filtrados.copy()
autos_tab["tem_ai"] = autos_tab["valor_preliminar_num"] > 0
merged = fiscalizacoes_filtradas.merge(
    autos_tab, on="fiscalizacao_id", how="left", suffixes=("_fisc", "_auto")
)

# ─────────────────────────────────────────────────────────────
# KPIs — mantidos exatamente como na versão anterior
# ─────────────────────────────────────────────────────────────
secao_titulo("📊 Indicadores de autos de infração")

total_tns_a   = len(fiscalizacoes_filtradas)
total_autos_a = calcular_total_autos(autos_tab)
valor_prel_a  = calcular_valor_preliminar_total(autos_tab)
taxa_conv_a   = calcular_taxa_conversao_tn_ai(fiscalizacoes_filtradas, autos_tab)
total_bol_a   = int(autos_tab["tem_boleto"].sum())

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Autos emitidos", str(total_autos_a), "⚖️",
             cor_fundo="#FEF2F2", cor_borda="#DC2626", cor_valor="#DC2626")
with col2:
    kpi_card("Valor preliminar total", formatar_moeda(valor_prel_a), "💰",
             cor_fundo="#FFF7ED", cor_borda="#F59E0B", cor_valor="#92400E")
with col3:
    cor_t = "#15803D" if taxa_conv_a < 30 else "#DC2626"
    kpi_card("Taxa de conversão TN→AI", formatar_percentual(taxa_conv_a), "📈",
             cor_fundo="#F0FDF4", cor_borda="#16A34A", cor_valor=cor_t,
             subtitulo="TNs que geraram ao menos 1 AI")
with col4:
    kpi_card("Boletos emitidos", str(total_bol_a), "🧾",
             cor_fundo="#FDF4FF", cor_borda="#A855F7", cor_valor="#7E22CE")

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Prepara dados da Faixa 1
# ─────────────────────────────────────────────────────────────

# ── Conversão ────────────────────────────────────────────────
tns_com_ai = int(autos_tab[autos_tab["tem_ai"]]["fiscalizacao_id"].nunique())
tns_sem_ai = total_tns_a - tns_com_ai
pct_com_ai = taxa_conv_a   # já é float 0-100

# Geometria do donut:
# viewBox 130x130, centro (65,65), raio 50, stroke-width 18.
# Circunferência = 2 * pi * 50 ≈ 314.2.
# Fatia vermelha (com AI) = (pct/100) * 314.2.
circunf_conv   = 314.2
fatia_com_ai   = round(pct_com_ai / 100 * circunf_conv, 2)

# ── Categorias ───────────────────────────────────────────────
_CORES_CAT = {
    "Controle Inventário":   "#1E3A8A",
    "Controle Ativo":        "#2563EB",
    "Georreferenciamento":   "#3B82F6",
    "Infraestrutura":        "#0E7490",
    "Documentação":          "#F59E0B",
    "Qualidade da Água":     "#64748B",
    "Faturamento":           "#475569",
    "Atendimento":           "#7C3AED",
    "Recursos Humanos":      "#0891B2",
    "Segurança Patrimonial": "#94A3B8",
    "Outras":                "#CBD5E1",
}

if not det_filtradas.empty and "categoria_padronizada" in det_filtradas.columns:
    cat_df = (
        det_filtradas["categoria_padronizada"].value_counts()
        .reset_index()
    )
    cat_df.columns = ["Categoria", "Quantidade"]
    cat_df = cat_df.sort_values("Quantidade", ascending=False)
else:
    cat_df = pd.DataFrame(columns=["Categoria", "Quantidade"])

max_cat = int(cat_df["Quantidade"].max()) if not cat_df.empty else 1


# ─────────────────────────────────────────────────────────────
# Funções de geração de HTML puro (style inline)
# Renderizados via components.html() — imunes ao bug de escape
# ─────────────────────────────────────────────────────────────

def _html_donut_conversao(tns_com: int, tns_sem: int,
                           pct: float, fatia: float, circ: float) -> str:
    """
    Donut SVG mostrando a taxa de conversão TN→AI.

    Fatia vermelha = TNs com AI; fundo cinza = TNs sem AI.
    Abaixo do donut: dois contadores lado a lado (com AI / sem AI).
    Nota vermelha de resumo no rodapé do painel.
    """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Conversão TN → AI
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:12px;">
            <svg width="130" height="130" viewBox="0 0 130 130">
                <circle cx="65" cy="65" r="50" fill="none"
                    stroke="#e2e8f0" stroke-width="18"/>
                <circle cx="65" cy="65" r="50" fill="none"
                    stroke="#dc2626" stroke-width="18"
                    stroke-dasharray="{fatia} {circ}"
                    stroke-dashoffset="0"
                    transform="rotate(-90 65 65)"/>
                <text x="65" y="59" text-anchor="middle"
                    font-size="20" font-weight="700" fill="#dc2626">{pct:.1f}%</text>
                <text x="65" y="76" text-anchor="middle"
                    font-size="11" fill="#94a3b8">conversão</text>
            </svg>
            <div style="display:flex;align-items:center;gap:18px;">
                <div style="text-align:center;">
                    <div style="font-size:22px;font-weight:700;color:#dc2626;">{tns_com}</div>
                    <div style="font-size:14px;color:#94a3b8;">com AI</div>
                </div>
                <div style="width:1px;height:32px;background:#e2e8f0;"></div>
                <div style="text-align:center;">
                    <div style="font-size:22px;font-weight:700;color:#3b82f6;">{tns_sem}</div>
                    <div style="font-size:14px;color:#94a3b8;">sem AI</div>
                </div>
            </div>
        </div>
        <div style="display:flex;gap:8px;background:#fef2f2;border-left:3px solid #dc2626;
                    border-radius:6px;padding:8px 10px;margin-top:14px;
                    font-size:14px;color:#dc2626;">
            {pct:.1f}% dos TNs geraram pelo menos 1 Auto de Infração
        </div>
    </div>
    """


def _html_barras_categorias(df: pd.DataFrame, max_val: int,
                             cores: dict) -> str:
    """
    Barras horizontais coloridas por categoria de irregularidade.
    Cada categoria tem cor própria definida em _CORES_CAT; fallback cinza.
    Fonte 13px para leitura confortável; barras de 15px de altura.
    """
    linhas = ""
    for _, row in df.iterrows():
        cat = str(row["Categoria"])
        qtd = int(row["Quantidade"])
        cor = cores.get(cat, "#CBD5E1")
        pct = max(2, round(qtd / max_val * 100, 1))
        linhas += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:7px;">
            <div style="font-size:14px;color:#64748b;min-width:120px;text-align:right;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {cat}
            </div>
            <div style="flex:1;height:15px;background:#e2e8f0;border-radius:3px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{cor};border-radius:3px;"></div>
            </div>
            <div style="font-size:14px;font-weight:600;color:#334155;min-width:34px;">
                {qtd}
            </div>
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Categorias de irregularidade
        </div>
        {linhas}
    </div>
    """


def _html_ranking(top10: pd.DataFrame) -> str:
    """
    Ranking Top 10 municípios por score de risco.

    Gradiente de cor: score alto → laranja escuro (#f59e0b),
    score médio → dourado (#d97706), score baixo → amarelo (#e5a30a).
    Largura da barra = score * 100%.
    """
    linhas = ""
    for _, row in top10.iterrows():
        score = float(row["risk_score"])
        mun   = str(row["municipio"])
        # Gradiente de cor por intensidade do score
        if score >= 0.8:
            cor = "#f59e0b"
        elif score >= 0.6:
            cor = "#d97706"
        else:
            cor = "#e5a30a"
        pct = round(score * 100, 1)
        linhas += f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <div style="font-size:14px;color:#64748b;min-width:92px;text-align:right;
                        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                {mun}
            </div>
            <div style="flex:1;height:16px;background:#e2e8f0;border-radius:3px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{cor};border-radius:3px;"></div>
            </div>
            <div style="font-size:14px;font-weight:600;color:#334155;min-width:36px;">
                {score:.3f}
            </div>
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            🏆 Ranking Top 10 · Score de risco
        </div>
        {linhas}
        <div style="border-top:.5px solid #e2e8f0;padding-top:12px;margin-top:10px;">
            <div style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:10px;">
                📖 Como ler o ranking
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#f59e0b;flex-shrink:0;margin-top:4px;"></div>
                <div style="font-size:14px;color:#64748b;line-height:1.5;">
                    <strong style="color:#334155;">Score 0 a 1</strong> — quanto mais próximo de 1, maior o risco regulatório combinado do município nos três componentes.
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#d97706;flex-shrink:0;margin-top:4px;"></div>
                <div style="font-size:14px;color:#64748b;line-height:1.5;">
                    <strong style="color:#334155;">Cor das barras</strong> — laranja escuro ≥ 0.8 (risco alto), dourado ≥ 0.6 (risco médio), amarelo &lt; 0.6 (risco moderado).
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#94a3b8;flex-shrink:0;margin-top:4px;"></div>
                <div style="font-size:14px;color:#64748b;line-height:1.5;">
                    <strong style="color:#334155;">Pesos ajustáveis</strong> — altere os sliders acima para recalcular o ranking priorizando taxa, valor financeiro ou frequência.
                </div>
            </div>
        </div>
    </div>
    """


def _html_pesos_e_legenda(pt: float, pv: float, pf: float) -> str:
    """
    Painel de pesos do score (barras de progresso estáticas refletindo
    os valores atuais dos sliders) + bloco "Como ler" embutido.

    Os sliders reais ficam no Streamlit (st.slider). Este componente
    apenas visualiza os pesos normalizados resultantes.
    """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            Pesos do score
        </div>
        <div style="margin-bottom:10px;">
            <div style="font-size:14px;color:#64748b;margin-bottom:4px;">Taxa de conversão</div>
            <div style="height:8px;background:#e2e8f0;border-radius:99px;overflow:hidden;margin-bottom:3px;">
                <div style="width:{pt*100:.0f}%;height:100%;background:#1e3a8a;border-radius:99px;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:14px;color:#94a3b8;">
                <span>0.0</span>
                <span style="color:#1e3a8a;font-weight:600;">{pt:.2f}</span>
                <span>1.0</span>
            </div>
        </div>
        <div style="margin-bottom:10px;">
            <div style="font-size:14px;color:#64748b;margin-bottom:4px;">Int. financeira</div>
            <div style="height:8px;background:#e2e8f0;border-radius:99px;overflow:hidden;margin-bottom:3px;">
                <div style="width:{pv*100:.0f}%;height:100%;background:#1e3a8a;border-radius:99px;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:14px;color:#94a3b8;">
                <span>0.0</span>
                <span style="color:#1e3a8a;font-weight:600;">{pv:.2f}</span>
                <span>1.0</span>
            </div>
        </div>
        <div style="margin-bottom:14px;">
            <div style="font-size:14px;color:#64748b;margin-bottom:4px;">Frequência</div>
            <div style="height:8px;background:#e2e8f0;border-radius:99px;overflow:hidden;margin-bottom:3px;">
                <div style="width:{pf*100:.0f}%;height:100%;background:#1e3a8a;border-radius:99px;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:14px;color:#94a3b8;">
                <span>0.0</span>
                <span style="color:#1e3a8a;font-weight:600;">{pf:.2f}</span>
                <span>1.0</span>
            </div>
        </div>
        <div style="background:#fffbeb;border-left:3px solid #f59e0b;border-radius:6px;
                    padding:9px 10px;font-size:14px;color:#92400e;margin-bottom:12px;">
            Pesos normalizados automaticamente para somar 100%
        </div>
        <div style="border-top:.5px solid #e2e8f0;padding-top:12px;">
            <div style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:10px;">
                📖 Como ler o score
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:9px;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#dc2626;flex-shrink:0;margin-top:4px;"></div>
                <div>
                    <div style="font-size:14px;font-weight:600;color:#334155;margin-bottom:2px;">Taxa de conversão</div>
                    <div style="font-size:14px;color:#64748b;line-height:1.5;">% de TNs que geraram AI. Alta conversão = maior risco regulatório do município.</div>
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:9px;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#f59e0b;flex-shrink:0;margin-top:4px;"></div>
                <div>
                    <div style="font-size:14px;font-weight:600;color:#334155;margin-bottom:2px;">Intensidade financeira</div>
                    <div style="font-size:14px;color:#64748b;line-height:1.5;">Valor total das multas em escala logarítmica — evita que poucos autos de alto valor dominem o score.</div>
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#1e3a8a;flex-shrink:0;margin-top:4px;"></div>
                <div>
                    <div style="font-size:14px;font-weight:600;color:#334155;margin-bottom:2px;">Frequência de autos</div>
                    <div style="font-size:14px;color:#64748b;line-height:1.5;">Nº de Autos por TN lavrado. Alta frequência indica padrão sistemático de não conformidade.</div>
                </div>
            </div>
        </div>
    </div>
    """


def _html_heatmap(hdf: pd.DataFrame) -> str:
    """
    Heatmap de componentes de risco.

    Escala de azul: valor 0 → #f0f4ff (quase branco), 1 → #1e3a8a (navy).
    Interpolação linear entre os dois extremos; texto branco quando
    o fundo é escuro (valor > 0.55), cinza escuro quando claro.

    hdf deve ter index = municípios e colunas:
        ['Taxa Conversão', 'Intensidade Financeira', 'Frequência']
    """
    def _cor_bg(v: float) -> str:
        """Interpola linearmente entre #f0f4ff (v=0) e #1e3a8a (v=1)."""
        r = int(240 + (30  - 240) * v)
        g = int(244 + (58  - 244) * v)
        b = int(255 + (138 - 255) * v)
        return f"rgb({r},{g},{b})"

    cabecalho = """
    <div style="display:grid;grid-template-columns:96px 1fr 1fr 1fr;
                background:#f8fafc;border-bottom:1px solid #e2e8f0;">
        <span style="font-size:14px;font-weight:600;text-transform:uppercase;
                     letter-spacing:.06em;color:#94a3b8;padding:6px 5px;">Município</span>
        <span style="font-size:14px;font-weight:600;text-transform:uppercase;
                     letter-spacing:.06em;color:#94a3b8;padding:6px 5px;">Taxa</span>
        <span style="font-size:14px;font-weight:600;text-transform:uppercase;
                     letter-spacing:.06em;color:#94a3b8;padding:6px 5px;">Financ.</span>
        <span style="font-size:14px;font-weight:600;text-transform:uppercase;
                     letter-spacing:.06em;color:#94a3b8;padding:6px 5px;">Freq.</span>
    </div>
    """
    linhas = ""
    for mun, row in hdf.iterrows():
        celulas = ""
        for v in row.values:
            bg   = _cor_bg(float(v))
            txt  = "#fff" if v > 0.55 else "#334155"
            celulas += (
                f'<div style="display:flex;align-items:center;justify-content:center;'
                f'font-size:14px;font-weight:600;color:{txt};background:{bg};">'
                f'{v:.2f}</div>'
            )
        linhas += f"""
        <div style="display:grid;grid-template-columns:96px 1fr 1fr 1fr;
                    border-bottom:.5px solid #f1f5f9;">
            <span style="font-size:14px;color:#334155;padding:5px 5px;
                         overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">
                {mun}
            </span>
            {celulas}
        </div>
        """
    return f"""
    <div style="font-family:-apple-system,'Segoe UI',sans-serif;padding:4px 0;">
        <div style="font-size:14px;font-weight:600;text-transform:uppercase;
                    letter-spacing:.06em;color:#94a3b8;margin-bottom:14px;">
            🌡️ Heatmap · Componentes de risco
        </div>
        <div style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
            {cabecalho}
            {linhas}
        </div>
        <div style="border-top:.5px solid #e2e8f0;padding-top:12px;margin-top:12px;">
            <div style="font-size:14px;font-weight:700;color:#1e293b;margin-bottom:10px;">
                📖 Como ler o heatmap
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#3b82f6;flex-shrink:0;margin-top:4px;"></div>
                <div style="font-size:14px;color:#64748b;line-height:1.5;">
                    <strong style="color:#334155;">Escala de cor</strong> — cada célula vai de azul muito claro (valor 0) a azul navy (valor 1). Quanto mais escura, maior a intensidade daquele componente no município.
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#1e3a8a;flex-shrink:0;margin-top:4px;"></div>
                <div style="font-size:14px;color:#64748b;line-height:1.5;">
                    <strong style="color:#334155;">Leitura por linha</strong> — compare os três componentes de um mesmo município: um município pode ter taxa baixa mas intensidade financeira alta, revelando poucos autos de grande valor.
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:flex-start;">
                <div style="min-width:8px;height:8px;border-radius:50%;background:#0891b2;flex-shrink:0;margin-top:4px;"></div>
                <div style="font-size:14px;color:#64748b;line-height:1.5;">
                    <strong style="color:#334155;">Leitura por coluna</strong> — compare municípios num mesmo componente para identificar quais concentram maior risco em cada dimensão.
                </div>
            </div>
        </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────
# Faixa 1: Conversão + Categorias
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "📋 Visão de autuações",
    "Conversão TN→AI · Categorias de irregularidade",
)

col_conv, col_cat = st.columns([1, 2])

with col_conv:
    # Altura = 130px SVG + contadores + nota + header ≈ 320px
    components.html(
        _html_donut_conversao(
            tns_com_ai, tns_sem_ai, pct_com_ai,
            fatia_com_ai, circunf_conv,
        ),
        height=330,
    )

with col_cat:
    if not cat_df.empty:
        # Altura ≈ 28px por categoria + 55px header
        altura_cat = len(cat_df) * 26 + 55
        components.html(
            _html_barras_categorias(cat_df, max_cat, _CORES_CAT),
            height=altura_cat,
        )
    else:
        alerta_atencao("Sem dados de categorias para os filtros selecionados.")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Faixa 2: Sliders + Score de risco + Ranking + Heatmap
# ─────────────────────────────────────────────────────────────
secao_titulo(
    "🎯 Análise de risco regulatório por município",
    "Score composto · pesos configuráveis",
)

# Sliders nativos do Streamlit — interatividade real
c1, c2, c3 = st.columns(3)
with c1: peso_taxa  = st.slider("Peso · Taxa de conversão",      0.0, 1.0, 0.5, 0.05, key="risco_taxa")
with c2: peso_valor = st.slider("Peso · Intensidade financeira", 0.0, 1.0, 0.3, 0.05, key="risco_valor")
with c3: peso_freq  = st.slider("Peso · Frequência de autos",    0.0, 1.0, 0.2, 0.05, key="risco_freq")

# Normalização automática dos pesos
soma_pesos = peso_taxa + peso_valor + peso_freq
if soma_pesos == 0:
    peso_taxa_n = peso_valor_n = peso_freq_n = 1 / 3
else:
    peso_taxa_n  = peso_taxa  / soma_pesos
    peso_valor_n = peso_valor / soma_pesos
    peso_freq_n  = peso_freq  / soma_pesos

st.caption(
    f"Pesos efetivos (normalizados): "
    f"Taxa {peso_taxa_n:.0%} · Financeiro {peso_valor_n:.0%} · Frequência {peso_freq_n:.0%}"
)

# Cálculo do score de risco por município
grp = (
    merged.groupby("municipio").agg(
        total_tn=("fiscalizacao_id", "nunique"),
        tn_com_ai=("tem_ai", "sum"),
        qtd_autos=("auto_id", "nunique"),
        valor_total=("valor_preliminar_num", "sum"),
    ).reset_index()
)
grp["taxa"]       = grp["tn_com_ai"] / grp["total_tn"].replace(0, 1)
grp["valor_norm"] = np.log1p(grp["valor_total"])
grp["freq"]       = grp["qtd_autos"] / grp["total_tn"].replace(0, 1)

# Normalização min-max de cada componente (0–1)
for col in ["taxa", "valor_norm", "freq"]:
    mn, mx = grp[col].min(), grp[col].max()
    grp[f"{col}_n"] = (grp[col] - mn) / (mx - mn + 1e-9)

grp["risk_score"] = (
    peso_taxa_n  * grp["taxa_n"] +
    peso_valor_n * grp["valor_norm_n"] +
    peso_freq_n  * grp["freq_n"]
)
top10 = grp.sort_values("risk_score", ascending=False).head(10)

# Heatmap DataFrame
hdf = (
    grp.sort_values("risk_score", ascending=False)
    .head(10)[["municipio", "taxa_n", "valor_norm_n", "freq_n"]]
    .set_index("municipio")
)
hdf.columns = ["Taxa Conversão", "Intensidade Financeira", "Frequência"]

# Três colunas da Faixa 2: pesos+legenda / ranking / heatmap
col_pesos, col_rank, col_heat = st.columns([0.7, 1, 1.3])

with col_pesos:
    # Altura = 3 barras de peso + legenda + "como ler" ≈ 400px
    components.html(
        _html_pesos_e_legenda(peso_taxa_n, peso_valor_n, peso_freq_n),
        height=620,
    )

with col_rank:
    # Altura ≈ 32px por município + 55px header
    altura_rank = len(top10) * 32 + 255
    components.html(
        _html_ranking(top10),
        height=altura_rank,
    )

with col_heat:
    # Altura ≈ 30px por linha + 55px header + 60px nota
    altura_heat = len(hdf) * 30 + 55 + 260
    components.html(
        _html_heatmap(hdf),
        height=altura_heat,
    )
