"""Páginas dos motores de exemplo (MOCK / EXEMPLO)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.bulkowski_engine import analyze_pattern_for_asset, list_patterns
from app.components import alerts_section
from app.healthbox_engine import build_healthbox, healthbox_confirms_strategy, healthbox_score
from app.mock_data import MOCK_ALERTS, MOCK_ASSET_SNAPSHOTS, MOCK_OPPORTUNITIES, MOCK_POSITIONS
from app.ui.pages.mock_page import evaluate_opportunity, opportunities_page, show_data_control


def show_bulkowski_engine() -> None:
    st.markdown("## Bulkowski Pattern Engine — exemplo estrutural")
    st.warning(
        "Base mockada. Nenhuma estatística real foi coletada ainda. O sistema não copia texto integral do ThePatternSite. Estatísticas ausentes aparecem como indisponível."
    )
    patterns = list_patterns()
    catalog_rows = [
        {
            "ID": item["id"],
            "Padrão": item["nome"],
            "Categoria": item["categoria"],
            "Tipo": item["tipo"],
            "Direção teórica": item["direcao_teorica"],
            "Taxa de falha": item["taxa_falha"],
            "Status": item["status_dado"],
        }
        for item in patterns
    ]
    with st.expander(f"Padrões disponíveis na base mockada ({len(catalog_rows)})"):
        st.dataframe(pd.DataFrame(catalog_rows), width="stretch", hide_index=True)

    analyses = [analyze_pattern_for_asset(snapshot) for snapshot in MOCK_ASSET_SNAPSHOTS]
    analysis_rows = [
        {
            "Ativo": item["ativo"],
            "Padrão detectado": item["nome_padrao"],
            "Tipo": item["tipo"],
            "Direção teórica": item["direcao_teorica"],
            "Confirmação": item["confirmacao"],
            "Rompimento": item["rompimento"],
            "Pullback/throwback": item["pullback_throwback"],
            "Alvo técnico": item["alvo_tecnico_metodo"],
            "Taxa de falha": item["taxa_falha"],
            "Movimento médio pós-rompimento": item["movimento_medio_pos_rompimento"],
            "Confiabilidade": item["confiabilidade"],
            "Fonte": item["fonte_nome"],
            "Status": item["status"],
        }
        for item in analyses
    ]
    st.markdown("### Análise por ativo")
    st.dataframe(pd.DataFrame(analysis_rows), width="stretch", hide_index=True)
    if any(not item["pattern_detected"] for item in analyses):
        st.info("Ativos sem padrão: padrão não detectado — não usar leitura gráfica como confirmação.")

def show_healthbox_engine() -> None:
    st.markdown("## Stock Healthbox Engine — exemplo estrutural")
    st.warning(
        "Base mockada. Nenhum dado real de mercado foi coletado ainda. Campos ausentes não são preenchidos por chute. Healthbox é filtro, não recomendação isolada."
    )
    strategies = {
        "PETR4": "call_debit_spread",
        "VALE3": "bull_put_spread",
        "ITUB4": "covered_call",
        "BOVA11": "put_debit_spread",
        "ABEV3": "covered_call",
    }
    def display_value(value: object, suffix: str = "") -> str:
        return f"{value:.2f}{suffix}" if isinstance(value, (int, float)) else "indisponível"

    rows = []
    for snapshot in MOCK_ASSET_SNAPSHOTS:
        healthbox = build_healthbox(snapshot)
        score_result = healthbox_score(healthbox)
        confirmation = healthbox_confirms_strategy(healthbox, strategies.get(snapshot["ativo"], ""))
        rows.append(
            {
                "Ativo": healthbox["ativo"],
                "Tendência": healthbox["tendencia"],
                "Variação diária": display_value(healthbox["variacao_diaria_percent"], "%"),
                "Range diário": display_value(healthbox["range_diario_percent"], "%"),
                "ADR": display_value(healthbox["adr_percent"], "%"),
                "ATR": display_value(healthbox["atr_percent"], "%"),
                "rVol": display_value(healthbox["rvol"], "x"),
                "RSI": display_value(healthbox["rsi"]),
                "RSI 200": display_value(healthbox["rsi_200"]),
                "Suporte": display_value(healthbox["suporte"]),
                "Resistência": display_value(healthbox["resistencia"]),
                "Distância suporte": display_value(healthbox["distancia_suporte_percent"], "%"),
                "Distância resistência": display_value(healthbox["distancia_resistencia_percent"], "%"),
                "Score": str(score_result["score"]) if score_result["score"] is not None else "score não calculado",
                "Confirmação": confirmation,
                "Campos ausentes": ", ".join(healthbox["campos_ausentes"]) or "nenhum",
                "Tipo de dado": healthbox["tipo_dado"],
            }
        )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

def _render_operation_checklist() -> None:
    st.markdown("## Checklist da Operação")
    for opportunity in MOCK_OPPORTUNITIES:
        evaluated = evaluate_opportunity(opportunity)
        with st.expander(f"{opportunity['ativo']} • {opportunity['estrategia']}"):
            for item in evaluated["checklist"]:
                st.markdown(f"**{item['question']}** — {item['detail']} · `{item['tipo_dado']}`")
    st.markdown("## Posições em Acompanhamento — exemplo visual")
    st.caption("Esta tabela é MOCK / EXEMPLO. Entradas confirmadas aparecem em Minhas Posições.")
    st.dataframe(pd.DataFrame(MOCK_POSITIONS), width="stretch", hide_index=True)
    st.markdown("## Alertas de Saída — exemplo")
    alerts_section(MOCK_ALERTS)

def demo_page() -> None:
    st.info("Estas seções usam somente dados MOCK / EXEMPLO e não se misturam com o Radar real.")
    tabs = st.tabs(["Motor de oportunidades", "Motores técnicos", "Checklist e registros"])
    with tabs[0]:
        opportunities_page()
    with tabs[1]:
        show_healthbox_engine()
        show_bulkowski_engine()
    with tabs[2]:
        _render_operation_checklist()
        show_data_control()
