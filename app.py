"""
app.py
======
Ponto de entrada — st.navigation() com grupos na sidebar.

Estrutura de páginas em pages/:
    sobre.py
    fiscalizacao_acervo.py          ← primeiro item de Fiscalização
    fiscalizacao_indicadores.py
    fiscalizacao_termos.py
    fiscalizacao_autos.py
    juridico_camara.py
    juridico_diretoria.py
    juridico_enquadramento.py
    financeiro_multas.py
    financeiro_boletos.py
    lead_time.py

Como rodar:
    streamlit run app.py

Ícones: sintaxe ":material/nome:" — suportada a partir do Streamlit 1.31.
Lista completa em: https://fonts.google.com/icons

REFATORAÇÃO v6.0:
    - injetar_css_global() movido para cá (era chamado em cada page — desperdício).
      O CSS global só precisa ser injetado uma vez por sessão; pages herdam
      o estado da sessão do app.py quando usam st.navigation().
    - st.set_page_config() permanece aqui (único lugar correto).
      Cada page tinha seu próprio st.set_page_config() → gerava aviso do Streamlit
      "set_page_config() can only be called once per app". Removido das pages.
"""

import streamlit as st
from utils.ui_components import injetar_css_global   # ← movido para cá

st.set_page_config(
    page_title="AGEMS · Fiscalização",
    page_icon=":material/balance:",   # ícone Material no título da aba
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":     None,
        "Report a bug": None,
        "About": "Sistema de Monitoramento de Fiscalização Regulatória · AGEMS",
    },
)

# CSS global injetado UMA VEZ aqui — pages não precisam mais chamar injetar_css_global()
# Isso evita reinjetar o mesmo bloco <style> a cada navegação de página.
injetar_css_global()

# ── Navegação com ícones Material Design ──────────────────────────────────────
# Cada st.Page recebe icon=":material/<nome>:" no lugar de emoji.
# Os grupos ("Sistema", "Fiscalização" etc.) viram cabeçalhos na sidebar
# automaticamente pelo st.navigation().

pg = st.navigation(
    {
        "Sistema": [
            st.Page(
                "pages/sobre.py",
                title="Sobre o sistema",
                icon=":material/info:",        # ícone de informação
                default=True,
            ),
        ],

        "Fiscalização": [
            st.Page(
                "pages/fiscalizacao_acervo.py",
                title="Acervo de documentos",
                icon=":material/folder_open:", # pasta aberta
            ),
            st.Page(
                "pages/fiscalizacao_indicadores.py",
                title="Indicadores gerais",
                icon=":material/bar_chart:",   # gráfico de barras
            ),
            st.Page(
                "pages/fiscalizacao_termos.py",
                title="Termos de Notificação",
                icon=":material/description:", # documento com linhas
            ),
            st.Page(
                "pages/fiscalizacao_autos.py",
                title="Autos de Infração",
                icon=":material/gavel:",       # martelo jurídico
            ),
        ],

        "Painel jurídico": [
            st.Page(
                "pages/juridico_camara.py",
                title="Decisões: câmara",
                icon=":material/account_balance:", # prédio/banco
            ),
            st.Page(
                "pages/juridico_diretoria.py",
                title="Decisões: diretoria",
                icon=":material/manage_accounts:",  # pessoa com engrenagem
            ),
            st.Page(
                "pages/juridico_enquadramento.py",
                title="Enquadramento legal",
                icon=":material/menu_book:",        # livro aberto
            ),
        ],

        "Painel financeiro": [
            st.Page(
                "pages/financeiro_multas.py",
                title="Valores de multas",
                icon=":material/receipt_long:",    # recibo longo
            ),
            st.Page(
                "pages/financeiro_boletos.py",
                title="Boletos emitidos",
                icon=":material/request_quote:",   # documento financeiro
            ),
        ],

        "Outros": [
            st.Page(
                "pages/lead_time.py",
                title="Lead time",
                icon=":material/timer:",           # cronômetro
            ),
        ],
    }
)

pg.run()
