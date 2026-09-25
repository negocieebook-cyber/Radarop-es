from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.theme import apply_theme
from app.components import render_page_header
from app.ui.shared import render_global_risk_notice
from app.ui.terminal_page import render_terminal_page
from app.ui.pages.panel_page import decision_panel_page
from app.ui.pages.simulator_page import tools_page
from app.ui.pages.engines_page import demo_page
from app.ui.pages.graphical_page import radar_grafico_page
from app.ui.pages.market_page import real_eod_opportunities_page, show_real_market_radar
from app.ui.pages.tracking_page import opening_watchlist_page, positions_hub_page
from app.ui.pages.retrospective_page import retrospective_page
from app.ui.pages.config_page import configuration_page

PAGE_GROUPS: list[tuple[str, list[str]]] = [
    ("Painel", ["Visão geral", "Radar EOD", "Radar de Mercado"]),
    ("Análise", ["Terminal", "Radar Gráfico"]),
    ("Acompanhamento", ["Eventos", "Posições", "Retrospectiva"]),
    ("Ferramentas", ["Simulador", "Demonstração"]),
    ("Sistema", ["Configurações"]),
]

PAGE_TITLES = {
    "Visão geral": "Painel de decisão",
    "Radar EOD": "Radar EOD",
    "Radar de Mercado": "Radar de Mercado",
    "Terminal": "Terminal",
    "Radar Gráfico": "Radar Gráfico",
    "Eventos": "Watchlist de Abertura",
    "Posições": "Posições e Alertas",
    "Retrospectiva": "Retrospectiva",
    "Simulador": "Simulador e Histórico",
    "Demonstração": "Demonstração",
    "Configurações": "Configurações",
}

PAGE_DESCRIPTIONS = {
    "Visão geral": "Página inicial: o que merece atenção hoje, quantas oportunidades estão prontas ou esperando gatilho e se os dados estão atualizados. Comece por aqui.",
    "Radar EOD": "Lista de oportunidades calculadas com o fechamento de ontem (EOD). Cada card mostra estratégia, gatilho e invalidação. Confira no pregão antes de decidir; não é ordem.",
    "Radar de Mercado": "Foto do mercado por ativo: preço, variação do dia, tendência e nota de saúde (Healthbox). Serve para entender o cenário, não para recomendar.",
    "Terminal": "Digite um ativo (ex.: PETR4) e veja tudo sobre ele numa tela: preço, saúde, estratégia que combinaria, eventos próximos e alertas.",
    "Radar Gráfico": "Ideias baseadas em regiões do gráfico (suporte, resistência, rompimento), ranqueadas por objetivo. Na segunda aba ficam as que você marcou para acompanhar.",
    "Eventos": "Candidatas que você salvou do Radar EOD, prontas para conferir na abertura do pregão, com preço de referência e regras de invalidação.",
    "Posições": "Suas posições registradas (exemplo e entradas manuais), com lucro/prejuízo acompanhado. Na aba Alertas, avisos de saída e de revisão.",
    "Retrospectiva": "O que aconteceu com as candidatas da Abertura que venceram: resultado estimado com o fechamento do ativo no vencimento. Aprendizado, não relatório de execução.",
    "Simulador": "Calculadora de opções: digite strikes e prêmios e veja perda máxima, ganho máximo e break-even. Na aba Histórico ficam suas decisões. Não envia ordens.",
    "Demonstração": "Modo de exemplo com dados falsos (MOCK): veja como o motor de oportunidades, os motores técnicos e o checklist funcionam, sem misturar com dado real.",
    "Configurações": "Parte técnica: status das fontes (opcoes.net.br e brapi), testes de coleta, universo de opções, rotinas de atualização e notificações por Telegram. Só mexa aqui se quiser ajustar dados.",
}

PAGE_HOW_TO = {
    "Visão geral": [
        "Leia os 4 números do topo",
        "Veja a leitura operacional: o que validar, acompanhar ou evitar",
        "Clique em Detalhes ou Simular no que interessar",
    ],
    "Radar EOD": [
        "Leia os cards: gatilho é a condição para a ideia valer",
        "Salve as que fizerem sentido em Acompanhar",
        "Confira-as amanhã em Eventos antes da abertura",
    ],
    "Radar de Mercado": [
        "Escolha o ativo",
        "Veja preço, variação do dia e nota de saúde",
        "Use para entender o cenário; aqui não sai recomendação",
    ],
    "Terminal": [
        "Digite o ativo (ex.: PETR4)",
        "Leia saúde, eventos próximos e estratégia sugerida",
        "Decida se vale acompanhar ou não",
    ],
    "Radar Gráfico": [
        "Veja as prioridades por objetivo",
        "Abra Detalhes para ver gatilho e invalidação",
        "Acompanhe as teses que quiser seguir",
    ],
    "Eventos": [
        "Confira cada candidata na abertura do pregão",
        "Compare o preço do pregão com a referência EOD",
        "Se entrar, registre a entrada manual; senão, remova",
    ],
    "Posições": [
        "Veja o monitor: status e lucro/prejuízo de cada posição",
        "Na aba Alertas, veja quando revisar ou realizar",
        "P/L da opção usa marcação EOD da última sessão; não é intraday",
    ],
    "Retrospectiva": [
        "Veja o resumo por estratégia das candidatas vencidas",
        "Abra o detalhe: preço do vencimento e P/L estimado por contrato",
        "Use como aprendizado; não é registro de execução real",
    ],
    "Simulador": [
        "Escolha a estratégia e digite strikes e prêmios",
        "Clique em Calcular simulação para ver perda, ganho e break-even",
        "Salve se quiser guardar a conta",
    ],
    "Demonstração": [
        "Explore livremente: tudo aqui é MOCK / EXEMPLO",
        "Veja como o motor aprova e reprova operações",
        "Nada aqui se mistura com o radar real",
    ],
    "Configurações": [
        "Veja o status das fontes (opcoes.net.br e brapi) e rode testes",
        "Na aba Rotinas, veja a frequência e configure o Telegram",
        "Só mexa aqui se quiser ajustar dados e testes",
    ],
}

REAL_BADGE_PAGES = {
    "Visão geral", "Radar EOD", "Radar Gráfico", "Radar de Mercado",
    "Eventos", "Posições", "Retrospectiva", "Simulador", "Terminal",
}


def _render_sidebar_nav() -> str:
    current = st.session_state.get("page", "Visão geral")
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Radar de Opções Brasil</div>', unsafe_allow_html=True)
        st.caption("Rotina objetiva de estudo, decisão e saída. Nenhuma ordem é enviada.")
        for group_label, items in PAGE_GROUPS:
            st.markdown(f'<div class="sidebar-group">{group_label}</div>', unsafe_allow_html=True)
            for item in items:
                if st.button(
                    item,
                    key=f"nav::{item}",
                    type="primary" if item == current else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["page"] = item
                    st.rerun()
    return current


def main() -> None:
    apply_theme()
    page = _render_sidebar_nav()
    if page not in PAGE_TITLES:
        page = "Visão geral"
        st.session_state["page"] = page

    render_page_header(
        PAGE_TITLES.get(page, page),
        "DADOS REAIS EOD / EXPERIMENTAL" if page in REAL_BADGE_PAGES else "DADOS MOCK / EXEMPLO",
        PAGE_DESCRIPTIONS.get(page, ""),
        PAGE_HOW_TO.get(page),
    )
    render_global_risk_notice()

    routes = {
        "Visão geral": decision_panel_page,
        "Radar EOD": real_eod_opportunities_page,
        "Radar de Mercado": show_real_market_radar,
        "Terminal": render_terminal_page,
        "Radar Gráfico": radar_grafico_page,
        "Eventos": opening_watchlist_page,
        "Posições": positions_hub_page,
        "Retrospectiva": retrospective_page,
        "Simulador": tools_page,
        "Demonstração": demo_page,
        "Configurações": configuration_page,
    }
    routes.get(page, decision_panel_page)()

    st.caption(
        "Radar de Opções Brasil • apoio à decisão • nenhuma ordem é enviada • motor mock e análise real EOD experimental permanecem separados"
    )


if __name__ == "__main__":
    main()
