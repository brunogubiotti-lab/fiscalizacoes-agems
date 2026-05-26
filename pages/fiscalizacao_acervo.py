"""
pages/fiscalizacao_acervo.py
===============================
Fiscalização · Acervo de documentos
Tabela filtrável de processos por município — links de pastas no OneDrive.

REFATORAÇÃO v6.0:
    - Removido st.set_page_config() — centralizado em app.py.
    - Removido injetar_css_global() — centralizado em app.py.

ATUALIZAÇÃO v8.0 — Padronização tipográfica:
    - Escala de fontes unificada: 9→11, 10→12, 11→13, 12→13, 13→14, 15→16px.
    - Aplica-se a todos os componentes HTML inline (components.html),
      blocos f-string e CSS embarcado em st.markdown.
    - Nenhuma lógica de dados ou layout foi alterada.
"""
import streamlit as st
from utils.filters import renderizar_filtros_sidebar
from utils.ui_components import alerta_informacao, banner_wip


renderizar_filtros_sidebar()

banner_wip(
    "O acervo está sendo alimentado com os links das pastas do SharePoint/OneDrive. "
    "Processos sem link cadastrado exibem '—' na coluna Pasta. "
    "Para adicionar links, edite o dicionário ACERVO no topo deste arquivo."
)


# ── ACERVO ───────────────────────────────────────────────────────────────────
# Estrutura por município:
#   "processos" → lista de dicts com "nome" e "link" da pasta do processo
#
# Com link:    {"nome": "1. RFP 019-2023 – Condições Gerais", "link": "https://..."}
# Sem link:    {"nome": "1. RFP 019-2023 – Condições Gerais", "link": ""}
ACERVO = {
    "Água Clara": {"processos": [
        {"nome": "1. RFP 019-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBjhDUDEvpiRbaLeq0V37wlAYcKyxcfAT0Q2b28HOHvh4I?e=VZevg3"},
    ]},
    "Alcinópolis": {"processos": [
        {"nome": "1. RFP 023-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgA03fut8BQJQ6Oljh_A3Z9RASoHMtRHr9GVOzFD1fmdT4w?e=La0MPn"},
    ]},
    "Amambai": {"processos": [
        {"nome": "1. RFP 016-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgA650gpfyrJQKjMHaoJ0AlUASwgWIj9wmctr37avyVl1eQ?e=PGjUad"},
        {"nome": "2. RFP 021-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB3MPYgzh7xQ6dZcQ_SVe4nAUgcyX332g6XyBCmAAZWI70?e=DW6EYK"},
    ]},
    "Anastácio": {"processos": [
        {"nome": "1. RFP 008-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB_P6CgwPtFSKJCBKppRbd5Ab9GFRjjBivrpV7wwpyQzSg?e=0zeqP2"},
        {"nome": "2. RFP 015-2025 – Obras SES",        "link": ""},
    ]},
    "Anaurilândia": {"processos": [
        {"nome": "1. RFP 026-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBhnT22XID7Sq4B8KjRxU-lAUEOG8FNiPV7vN5XVGCkACA?e=HY84Et"},
        {"nome": "2. RFP 011-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCut8JKAz9cRb4GQ_zXt8ClAb-9bIFCUcGVo0YsjCI3EwQ?e=Dssbg2"},
    ]},
    "Angélica": {"processos": [
        {"nome": "1. RFP 030-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCg1SyCEAVWSbHVRoIHKTMdAYW_BCtbRcjyN1VAHyoR-T4?e=NjhrNh"},
    ]},
    "Antônio João": {"processos": [
        {"nome": "1. RFP 014-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDfGWYJuzVJSrMrWkYont64AVNjrCAnsg3vlc_flLBiJws?e=MSHhQ9"},
        {"nome": "2. RFP 016-2025 – Obras SES",        "link": ""},
    ]},
    "Aparecida do Taboado": {"processos": [
        {"nome": "1. RFP 030-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDPz0ABMv2NRJicwKiGm80lAa0HmOPx8zzjbMbgra3fM9s?e=vigV7j"},
    ]},
    "Aquidauana": {"processos": [
        {"nome": "1. RFP 009-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAPXyygle9lSrkeBFj9SRooAYp6iews_H99xuUj95rSpcI?e=OmdNVl"},
    ]},
    "Aral Moreira": {"processos": [
        {"nome": "1. RFP 012-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDbB_ZE4dN-To2HZt1_NK_VAc9wlWYUaFWZZZTJnkxae6Y?e=eXn1eb"},
        {"nome": "2. RFP 022-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAf0toH12QaTYHtqt0OTS0XAa_RAujlmfyNtlLEIpiC-kU?e=o9Dpht"},
    ]},
    "Bataguassu": {"processos": [
        {"nome": "1. RFP 008-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB0w9G9cKAPSYwynKVMwwqmAV2RwOQ7kS7Vx-YioLFF_hk?e=ilFjIb"},
        {"nome": "2. RFP 012-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBmHyNzimDORbPjJCOnC8XrAZp4_lIqfVl-7HLppuRCnAI?e=mo7pUH"},
    ]},
    "Batayporã": {"processos": [
        {"nome": "1. RFP 029-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDIecDGkEbuRaKFTNC8W3G4ATf4YhQplfQW4bqVyMYBLlM?e=rmlx8r"},
        {"nome": "2. RFE 001-2025 – Obras de SES-MSP", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBabmhVriDETpVYuKwmncRyASZsAZ1hyF46-3vFcMo1NkI?e=m4DL6M"},
    ]},
    "Bodoquena": {"processos": [
        {"nome": "1. RFP 023-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCCBFMa0XapTraZr6UcIFKvAa_pjDJN500VWETiB9AeRsQ?e=YYMyjy"},
    ]},
    "Bonito": {"processos": [
        {"nome": "1. RFP 021-2022 – Condições Gerais", "link": ""},
    ]},
    "Brasilândia": {"processos": []},
    "Caarapó":     {"processos": []},
    "Camapuã":     {"processos": []},
    "Caracol":     {"processos": []},
    "Chapadão do Sul":  {"processos": []},
    "Coronel Sapucaia": {"processos": []},
    "Corumbá": {"processos": [
        {"nome": "1. RFP 024-2022 – Condições Gerais", "link": ""},
    ]},
    "Coxim":      {"processos": []},
    "Deodápolis": {"processos": []},
    "Dois Irmãos do Buriti": {"processos": []},
    "Douradina":  {"processos": []},
    "Dourados": {"processos": [
        {"nome": "1. RFP 024-2022 – Condições Gerais",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBuVXCzZ3NWSbF1jeq-_aKSAeuGirX38dcVDQR-5g2qfwg?e=7XEhes"},
        {"nome": "2. RFE 002-2023 – Agrotóxico",               "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDFBRH46ECzSIu6qYbsw8u7AWJB7ylLGwSj3QTElsUGBIE?e=1CeiiN"},
        {"nome": "3. RFE 002-2024 – Extravasamento de esgoto", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB6q4men-6KQLMHYkFlet_NAa0wkNCzbWsiSzv497LONto?e=aC6Goy"},
        {"nome": "4. RFE 002-2025 – Rompimento de Adutora",    "link": ""},
        {"nome": "5. RFP 013-2025 – Obras SES",                "link": ""},
    ]},
    "Eldorado": {"processos": [
        {"nome": "1. RFP 035-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBhmB13aInkTbruKCQxYLrzAYDGRqQhZLAaM-B_kW6C8io?e=geI6Wv"},
    ]},
    "Fátima do Sul": {"processos": [
        {"nome": "1. RFP 014-2023 – Condições Gerais",         "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBKHyu9VxYOSZ6fwTdFHZSdAVhCk3rUSFyJF_8bnrtWPtc?e=zzILni"},
        {"nome": "2. RFE 003-2024 – Extravasamento de Esgoto", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgC5m3mUDCh5RI1fkzVXby5sAeIJfw5IPGplUkTYHDDJHHc?e=eltaTq"},
        {"nome": "3. RFP 004-2025 – Obras SES",                "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDQihLu5URtQ4cevp5i3B4LAWpS3ikKqJi4-gEu-I3aUqw?e=4VC2th"},
    ]},
    "Figueirão": {"processos": [
        {"nome": "1. RFP 025-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgA8l3O8WvZ_QK2rKrF_XAhbAQUbg-shY9iqUFwQKL830qw?e=lQBdML"},
    ]},
    "Guia Lopes da Laguna": {"processos": [
        {"nome": "1. RFP 002-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCQxeE1nYzqTo385PDrDneNAcwpkdc7shb3oFgXS4xvLV8?e=9TB2cK"},
    ]},
    "Iguatemi": {"processos": [
        {"nome": "1. RFP 036-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAbK9zzHOmVSZ88OSJBvGXiAZ_NKuDxtzmPoz2OU4Zg1_U?e=slg8nm"},
    ]},
    "Inocência": {"processos": [
        {"nome": "1. RFP 028-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAYxjrccMDLQowUocYLerQSAQMhv318Z2Y64cdsoEHwQVk?e=TIuoET"},
        {"nome": "2. RFP 001-2025 – Obras de SES-MSP", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBnN9CkjeSQS5FGMwUjkW4oAebNDT1XywSBsF3vgwLBpp4?e=M05a1j"},
    ]},
    "Itaporã": {"processos": [
        {"nome": "1. RFP 011-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDIZZy7p47SSYjXpdEaeVVTARPwsH21hL9Xs9rMpUoZSsc?e=XobArO"},
        {"nome": "2. RFE 005-2023 – Agrotóxico",       "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAD0myM3GoMRpH2IDwDg_WRAS4Q3HzdpCb-de_NcFJ2GTo?e=oKcSxs"},
        {"nome": "3. RFP 026-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgC1GTwEKD_RTqZ2OQrGMUJIAQTAnLQz5qgMa_LRSYOXXto?e=HidOF9"},
    ]},
    "Itaquiraí": {"processos": [
        {"nome": "1. RFP 006-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgClFK1QUTgnQ5v4SyaSZfdTAW75MH49zKzh1WKWmEVu90Y?e=ddjDgI"},
    ]},
    "Ivinhema": {"processos": [
        {"nome": "1. RFP 031-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCHCK7ET078Q7NXhVSsPbevAVsG2ae-B_3xr52GwdKRiz8?e=bLEeAB"},
        {"nome": "2. RFP 008-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAAt6xCPKJbQYnfG4FO4FmYAXT-8J4uAMK7IdWUD2GI3pU?e=Jidr2E"},
    ]},
    "Japorã": {"processos": [
        {"nome": "1. RFP 033-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCgZO09MZtJR49SeelhnY9yAUO-pUZUFYMImPQEeSj5mPQ?e=VpNcVF"},
    ]},
    "Jardim": {"processos": [
        {"nome": "1. RFP 003-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBSM6LR30qmTpUOMCnn9NqmAfxhFMIEgbVm80E3c6hH1XA?e=ubhvER"},
        {"nome": "2. RFP 023-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgD8GynK4YZUQ7dpuPVplVNjAQoLI4RjbsSwMW4zU_Wh-rw?e=k6FkYC"},
    ]},
    "Jateí": {"processos": [
        {"nome": "1. RFP 017-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDMJfHBWq2ZT4hAiQuhj-ywAWkqU0K5n8kmk9fUJ28LQIw?e=sBkdk0"},
    ]},
    "Juti": {"processos": [
        {"nome": "1. RFP 004-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDW3-D4tsOTRqsKw82qLjm2ARmdwTToAJjKeG4kUp6SiKk?e=a0uDxH"},
        {"nome": "2. RFP 003-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgD8MJtj9DK_Tp-6NjcUYNPPAad23TP0s6j3TqKVTTOJOnQ?e=m6YMDd"},
    ]},
    "Ladário": {"processos": [
        {"nome": "1. RFP 020-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBOaZgt-XllSa8aS9FQUJMPAWuafVHmmGCLcJYBTmrx6V4?e=qnWbYt"},
    ]},
    "Laguna Caarapã": {"processos": [
        {"nome": "1. RFP 015-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCbWzI27zgjQbscQRuyXK44AdPjBjeheSsEuhxQEM-8MSc?e=t7lRYA"},
    ]},
    "Maracaju": {"processos": [
        {"nome": "1. RFP 012-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAcEFyWKfXUSqhBrNwfkPBFAcGHnAMjRNwpuTdV0u45yew?e=nUe7EA"},
        {"nome": "2. RFP 003-2023 – Agrotóxico",       "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgA-RJZ9-2x5T5U4ggCKYnH5AdIv1WTyu8FECIctCaUkntU?e=ACFTvg"},
        {"nome": "3. RFP 019-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgA9P7HB-tACQIthf3thcU_YAbHYsHIStoRPqQJN9AXS20U?e=0PKW83"},
    ]},
    "Miranda": {"processos": [
        {"nome": "1. RFP 022-2022 – Condições Gerais",         "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBZQ9K-IgalKg-oqFPjFEsEAS0_X7g5ZNS5Cv7FJFRRng?e=Ycxuxa"},
        {"nome": "2. RFE 001-2024 – Extravasamento de Esgoto", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCPDY1E_nk3Rb_fNa8HHmYBATz-9GX-s7eBwGKVqLv6Og?e=BFnZFY"},
    ]},
    "Mundo Novo": {"processos": [
        {"nome": "1. RFP 034-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCT0pZv_GpAGz3x3i6ufrgBAf0gxl5f3Y81rAf0GS-p3g?e=nJVFVF"},
    ]},
    "Naviraí": {"processos": [
        {"nome": "1. RFP 005-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDY2iv6cJJTTaqrHQ4Xt6YBAK1y_SqQDpZDn8XlmC15MQ?e=Ib3P1T"},
    ]},
    "Nioaque": {"processos": [
        {"nome": "1. RFP 011-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCD0N5A5ap0Q_SXQkrjv0YBAI8iq_RtKHHjODtFhIvtKg?e=jiqGex"},
    ]},
    "Nova Alvorada do Sul": {"processos": [
        {"nome": "1. RFE 006-2023 – Agrotóxico", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAIOya2vXRFSqRQYFWJvgUBAWjxBSzTWHkfLJTjp1Wr5A?e=sHVP1c"},
    ]},
    "Nova Andradina": {"processos": [
        {"nome": "1. RFP 027-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCHXh9i_aJJQ9pS27K2D30BAVCb2BJHA6xQJMdSJPiDaQ?e=tWdkLM"},
        {"nome": "2. RFE 006-2023 – Agrotóxico",       "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgC1FC96HS1CS8JBDSNGi_gBAX6EBKBv8LH7ggvhM2JLkw?e=wIRzRN"},
    ]},
    "Novo Horizonte do Sul": {"processos": [
        {"nome": "1. RFP 018-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCWa1zUt_d6SNa2IA2fMMkBAVb1s3qERfJoSAZSDdFqxg?e=MqYbHW"},
    ]},
    "Paranaíba": {"processos": [
        {"nome": "1. RFP 011-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB9I93yWiT2REf2uo2KPQwBAb04_bm-DQZJ_Iax9F_gqQ?e=hOsHg1"},
        {"nome": "2. RFE 005-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgAdAhyzpQBgSjY9MShSAcYBASpMwOmGJjvCH0CZRH8RBw?e=b9DQDI"},
    ]},
    "Paranhos": {"processos": [
        {"nome": "1. RFP 039-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgD5sk79IbdRTs8-iX7oNXkBAfWKn8YvHdQRa5hHRcGxmQ?e=tYKvSM"},
    ]},
    "Pedro Gomes": {"processos": [
        {"nome": "1. RFP 027-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBPI3VeWtBCTp5EqB7M9oEBAc3JJp-7SzKjpPMI3GcxLw?e=bm0RNa"},
    ]},
    "Ponta Porã": {"processos": [
        {"nome": "1. RFP 013-2022 – Condições Gerais", "link": ""},
        {"nome": "2. RFP 017-2025 – Obras SES",        "link": ""},
    ]},
    "Porto Murtinho": {"processos": [
        {"nome": "1. RFP 006-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCE0ACZKzLYSoCiW1niBusMAXp_koey4yDMEPZDLwNMZRs?e=uGrWWV"},
    ]},
    "Ribas do Rio Pardo": {"processos": [
        {"nome": "1. RFP 020-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB3fDG6sI0bSKy42zv79uPlAX8OThlgLgxLLACDoqxGUKo?e=ZccIfL"},
    ]},
    "Rio Brilhante": {"processos": [
        {"nome": "1. RFP 010-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB6tPtOJtROS64mJMNjO4wJAS17MkyakR9-Z6LN-YuGaoE?e=IK4zvD"},
        {"nome": "2. RFE 007-2023 – Agrotóxico",       "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgC6sx1Byxp-SYWosAadEfU5AU9OUWy2j-1lrvVhh-3DRnc?e=n2v0R2"},
    ]},
    "Rio Negro": {"processos": [
        {"nome": "1. RFP 004-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCelT2NuuCsTq1dHHJxW7HqAX8Pw5btSAMkA81EAHz1k8w?e=NciSks"},
        {"nome": "2. RFE 004-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCH8m3t-xeHQbwomSNxBBtwAfbf8rZawH1nvRDu0RqNPFw?e=aehR5Q"},
    ]},
    "Rio Verde de Mato Grosso": {"processos": [
        {"nome": "1. RFP 029-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBz6kleYrjBSoA4vscEfFtgAS4yXdu_UHOqJqx9m7mOwQM?e=sjHRZs"},
    ]},
    "Santa Rita do Pardo": {"processos": [
        {"nome": "1. RFP 007-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCcWvJG2bQLSp7M7_6pgyAGAWwGpXVW5ln6wIsQNBOvCu4?e=GK6pPc"},
    ]},
    "Selvíria": {"processos": [
        {"nome": "1. RFP 010-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgD8A-AA5QWQTY5irJiKyKMkAZU1ZPH95u8SRvhWk3sR4Eo?e=tiBWgh"},
    ]},
    "Sete Quedas": {"processos": [
        {"nome": "1. RFP 038-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDQJvXn21KmRbPZ35QQnUT1AdLuAxBIDSAMzQsamXV5mIQ?e=EB1C0t"},
    ]},
    "Sidrolândia": {"processos": [
        {"nome": "1. RFP 001-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCpSncnPj17R7ULPrnoCwphASoUALfrZZIZslV8c6-TqPs?e=VPbSIh"},
        {"nome": "2. RFP 020-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCnUwyR9xdrRpvxnByVkl0xAc7ZLvVuZMXMuTwcQwC0taE?e=g0mryy"},
    ]},
    "Sonora": {"processos": [
        {"nome": "1. RFP 026-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBqilwJZQuFQZWz9qXR9Ly6AVtXLEwhnRde2H4YFsaAsu0?e=RF3UYi"},
    ]},
    "Tacuru": {"processos": [
        {"nome": "1. RFP 037-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDhtmGK6Dc3QKwCNsKjLaMNAV56y4Lc6fWEjheAeRvuMTo?e=cKVN3W"},
    ]},
    "Taquarussu": {"processos": [
        {"nome": "1. RFP 028-2023 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBlT4WUoIy3QIcOsKuYAX2xAWjm7xfp-G2UfT-8fu2MaTA?e=0sut8H"},
        {"nome": "2. RFP 010-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgDmrmcPfQEfQrV9uTt51XjvAcNe8P7e_20djW_lqdWpVGQ?e=cZPX4n"},
    ]},
    "Terenos": {"processos": [
        {"nome": "1. RFP 003-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgCpEbDM5WZ8T63efho7pzxQAWL5JjCOXsaw_GNuF1AJmvk?e=L4dIrR"},
        {"nome": "2. RFP 014-2025 – Obras SES",        "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgABvSA3D-DJSJoGL6-XhpfoAZogcwZfWlCEJIB65D9dqDQ?e=jgBCwI"},
    ]},
    "Três Lagoas": {"processos": [
        {"nome": "1. RFP 041-2024 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgBNTdgNBKtiR5XZrobbgi32AUmJcdDj32PGdtizVAYTs8M?e=QiQGQ2"},
    ]},
    "Vicentina": {"processos": [
        {"nome": "1. RFP 016-2022 – Condições Gerais", "link": "https://sanesul-my.sharepoint.com/:f:/g/personal/bruno_gubiotti_sanesul_ms_gov_br/IgB4EYAaRSKVSbA8CCKVxwgXAbKJvyYklANsrRO0YKVGR0o?e=Vapge5"},
        {"nome": "2. RFP 005-2025 – Obras SES",        "link": ""},
    ]},
}


# ── Filtro de busca ───────────────────────────────────────────────────────────
busca = st.text_input(
    "Buscar",
    placeholder="🔍  Buscar município...",
    label_visibility="collapsed",
    key="busca_acervo",
)

acv = {
    m: d for m, d in ACERVO.items()
    if d["processos"] and busca.strip().lower() in m.lower()
} if busca.strip() else {
    m: d for m, d in ACERVO.items()
    if d["processos"]
}

# ── Métricas ──────────────────────────────────────────────────────────────────
total_mun  = len(ACERVO)
mun_c_proc = sum(1 for d in ACERVO.values() if d["processos"])
total_proc = sum(len(d["processos"]) for d in ACERVO.values())
proc_c_lnk = sum(1 for d in ACERVO.values() for p in d["processos"] if p.get("link"))
sem_link   = total_proc - proc_c_lnk

st.caption(
    f"📂 {total_mun} municípios · "
    f"{mun_c_proc} com processos · "
    f"{total_proc} processos · "
    f"📎 {proc_c_lnk} com link · "
    f"⏳ {sem_link} aguardando link"
)
st.markdown("<br>", unsafe_allow_html=True)

# ── Constantes de estilo ──────────────────────────────────────────────────────
# Cores dos badges por tipo de processo (detectado pelo nome)
# Cada tipo tem: cor de fundo (bg) e cor do texto (txt)
TIPO_CORES = {
    "Condições Gerais": {"bg": "#EFF6FF", "txt": "#1D4ED8"},  # azul
    "Obras SES":        {"bg": "#F0FDF4", "txt": "#15803D"},  # verde
    "Obras de SES-MSP": {"bg": "#F0FDF4", "txt": "#15803D"},  # verde
    "Agrotóxico":       {"bg": "#FFF7ED", "txt": "#C2410C"},  # laranja
    "Extravasamento":   {"bg": "#FDF4FF", "txt": "#7E22CE"},  # roxo
    "Rompimento":       {"bg": "#FFF1F2", "txt": "#BE123C"},  # vermelho
}
# Cor padrão para tipos não mapeados
COR_PADRAO = {"bg": "#F1F5F9", "txt": "#475569"}


def _badge_tipo(nome_processo: str) -> str:
    """
    Detecta o tipo do processo pelo nome e retorna HTML de um badge colorido.

    Lógica:
    - Percorre TIPO_CORES buscando a chave dentro do nome do processo.
    - Se não encontrar, usa COR_PADRAO.
    - Extrai o tipo do nome após o '–' (ex: '1. RFP 019-2023 – Condições Gerais').
    """
    # Tenta extrair a descrição após o traço '–'
    tipo_texto = nome_processo.split("–")[-1].strip() if "–" in nome_processo else nome_processo

    # Procura a cor correspondente ao tipo
    cor = COR_PADRAO
    for chave, cores in TIPO_CORES.items():
        if chave.lower() in nome_processo.lower():
            cor = cores
            # Usa o nome da chave como label do badge (mais limpo)
            tipo_texto = chave
            break

    return (
        f'<span style="'
        f'background:{cor["bg"]};color:{cor["txt"]};'
        f'font-size:14px;font-weight:600;padding:2px 8px;'
        f'border-radius:999px;white-space:nowrap;">'
        f'{tipo_texto}</span>'
    )


def _card_municipio(municipio: str, processos: list) -> str:
    """
    Gera o HTML completo de um card de município para o layout em grade.

    Estrutura do card:
    ┌─────────────────────────────┐
    │ 📁 Nome do Município        │
    │ N processo(s)    [badge qtd]│
    ├─────────────────────────────┤
    │ 📋 Nome processo  [badge]   │  → com link: linha clicável
    │ 📋 Nome processo  [badge]   │  → sem link: ícone '—'
    └─────────────────────────────┘
    """
    qtd = len(processos)
    label_qtd = f'{qtd} processo{"s" if qtd != 1 else ""}'

    # ── Cabeçalho do card ────────────────────────────────────────────────────
    html = (
        f'<div style="'
        f'background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;'
        f'overflow:hidden;height:100%;display:flex;flex-direction:column;">'

        # Topo: ícone + nome + contagem
        f'<div style="padding:14px 16px 10px;border-bottom:1px solid #F1F5F9;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">'
        f'<div style="display:flex;align-items:center;gap:8px;min-width:0;">'
        f'<span style="font-size:18px;flex-shrink:0;">📁</span>'
        f'<span style="font-size:14px;font-weight:700;color:#1E293B;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{municipio}</span>'
        f'</div>'
        f'<span style="background:#EFF6FF;color:#1D4ED8;font-size:14px;font-weight:600;'
        f'padding:2px 8px;border-radius:999px;flex-shrink:0;">{qtd}</span>'
        f'</div>'
        f'<div style="font-size:14px;color:#94A3B8;margin-top:3px;">{label_qtd}</div>'
        f'</div>'
    )

    # ── Lista de processos ────────────────────────────────────────────────────
    html += '<div style="padding:8px 0;flex:1;">'

    for proc in processos:
        nome  = proc["nome"]
        link  = proc.get("link", "")
        badge = _badge_tipo(nome)

        # Extrai apenas o código do processo (ex: "RFP 019-2023") para exibir compacto
        partes = nome.split("–")
        # Parte antes do '–' tem "1. RFP 019-2023 ", removemos o número ordinal
        codigo = partes[0].strip()
        if ". " in codigo:
            codigo = codigo.split(". ", 1)[1].strip()  # remove "1. "

        if link:
            # Linha clicável → abre o link no SharePoint
            html += (
                f'<a href="{link}" target="_blank" style="'
                f'display:flex;align-items:center;justify-content:space-between;'
                f'gap:8px;padding:6px 16px;text-decoration:none;'
                f'border-bottom:1px solid #F8FAFC;'
                f'transition:background 0.15s;" '
                f'onmouseover="this.style.background=\'#F8FAFC\'" '
                f'onmouseout="this.style.background=\'transparent\'">'
                f'<span style="display:flex;align-items:center;gap:6px;min-width:0;">'
                f'<span style="font-size:14px;flex-shrink:0;">📋</span>'
                f'<span style="font-size:14px;color:#334155;white-space:nowrap;'
                f'overflow:hidden;text-overflow:ellipsis;">{codigo}</span>'
                f'</span>'
                f'<span style="flex-shrink:0;">{badge}</span>'
                f'</a>'
            )
        else:
            # Sem link → exibe em cinza com traço
            html += (
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'gap:8px;padding:6px 16px;border-bottom:1px solid #F8FAFC;">'
                f'<span style="display:flex;align-items:center;gap:6px;min-width:0;">'
                f'<span style="font-size:14px;flex-shrink:0;opacity:0.4;">📋</span>'
                f'<span style="font-size:14px;color:#94A3B8;white-space:nowrap;'
                f'overflow:hidden;text-overflow:ellipsis;">{codigo}</span>'
                f'</span>'
                f'<span style="font-size:14px;color:#CBD5E1;flex-shrink:0;">'
                f'<span title="Sem link cadastrado">—</span></span>'
                f'</div>'
            )

    html += '</div></div>'  # fecha lista + card
    return html


# ── Sem resultados ────────────────────────────────────────────────────────────
if not acv:
    st.markdown(
        '<div style="background:#F9FAFB;border:2px dashed #E5E7EB;border-radius:10px;'
        'padding:32px;text-align:center;color:#9CA3AF;">'
        '<p style="font-size:32px;margin:0;">🔍</p>'
        '<p style="font-size:17px;margin:8px 0 0;">Nenhum município encontrado.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    # ── Grade de cards: 3 colunas ─────────────────────────────────────────────
    # Converte o dicionário filtrado em lista para fatiar em linhas de 3
    municipios = list(acv.items())

    # Número de cards por linha (colunas da grade)
    COLS = 3

    # Itera de 3 em 3 para criar cada linha da grade
    for i in range(0, len(municipios), COLS):
        # Fatia os municípios desta linha (pode ser menos de 3 na última)
        linha = municipios[i : i + COLS]

        # st.columns cria as colunas lado a lado no Streamlit
        colunas = st.columns(COLS, gap="medium")

        for col, (municipio, dm) in zip(colunas, linha):
            with col:
                # Renderiza o HTML do card dentro da coluna
                st.markdown(
                    _card_municipio(municipio, dm["processos"]),
                    unsafe_allow_html=True,
                )

        # Espaço vertical entre as linhas da grade
        st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

alerta_informacao(
    "O botão 📂 abre a pasta do processo no SharePoint/OneDrive. "
    "Processos sem link cadastrado exibem '—'. "
    "A estrutura segue o padrão AGEMS/Sanesul."
)
