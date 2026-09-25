"""Páginas do simulador manual."""

from __future__ import annotations

import streamlit as st

from app.components import render_manual_simulation, strategy_label
from app.manual_trade_simulator import (
    SUPPORTED_STRATEGIES,
    build_manual_simulation_from_strategy,
    calculate_manual_strategy_risk,
    delete_manual_simulation,
    list_manual_simulations,
    save_manual_simulation,
)
from app.user_trading_profile import load_user_trading_profile
from app.ui.pages.tracking_page import history_page


def manual_simulator_form(seed: dict | None = None, key_prefix: str = "manual") -> None:
    seed = seed or {}
    thesis = seed.get("thesis") or {}
    candidate = seed.get("candidate") or seed
    initial_strategy = str(candidate.get("strategy_id") or "long_call")
    if initial_strategy not in SUPPORTED_STRATEGIES:
        initial_strategy = "long_call"
    with st.form(f"{key_prefix}_form"):
        header = st.columns(4)
        strategy_id = header[0].selectbox("Estratégia", list(SUPPORTED_STRATEGIES), index=list(SUPPORTED_STRATEGIES).index(initial_strategy), format_func=strategy_label, key=f"{key_prefix}_strategy")
        ticker = header[1].text_input("Ativo", value=str(thesis.get("ativo") or seed.get("ticker") or ""), key=f"{key_prefix}_ticker")
        expiration = header[2].text_input("Vencimento", value=str(candidate.get("expiration") or ""), key=f"{key_prefix}_expiration")
        quantity = header[3].number_input("Quantidade de contratos", min_value=1, value=1, step=1, key=f"{key_prefix}_quantity")
        settings = st.columns(2)
        default_multiplier = load_user_trading_profile().get("multiplicador_contrato_padrao")
        multiplier_text = settings[0].text_input("Multiplicador do contrato", value="100" if default_multiplier is None else str(default_multiplier), help="Padrão B3: 100 ações por contrato de opção.", key=f"{key_prefix}_multiplier")
        has_underlying = settings[1].checkbox("Tenho o ativo em carteira", value=False, key=f"{key_prefix}_underlying", disabled=strategy_id != "covered_call")
        template = build_manual_simulation_from_strategy({**candidate, "strategy_id": strategy_id, "strategy_name": strategy_id}, thesis)
        legs = []
        st.markdown("#### Pernas manuais")
        for index, leg in enumerate(template.get("legs", [])):
            columns = st.columns((1, 1, 1, 1, 1))
            leg_type_label = {"call": "Call", "put": "Put", "stock": "Ativo"}.get(leg["type"], leg["type"])
            leg_action_label = {"buy": "Compra", "sell": "Venda"}.get(leg["action"], leg["action"])
            columns[0].text_input("Tipo", value=leg_type_label, disabled=True, key=f"{key_prefix}_type_{strategy_id}_{index}")
            columns[1].text_input("Ação", value=leg_action_label, disabled=True, key=f"{key_prefix}_action_{strategy_id}_{index}")
            strike_text = columns[2].text_input("Strike", value="", disabled=leg["type"] == "stock", key=f"{key_prefix}_strike_{strategy_id}_{index}")
            premium_label = "Preço do ativo" if leg["type"] == "stock" else "Prêmio"
            premium_text = columns[3].text_input(premium_label, value="", key=f"{key_prefix}_premium_{strategy_id}_{index}")
            leg_quantity = columns[4].number_input("Qtd. perna", min_value=1, value=1, step=1, key=f"{key_prefix}_leg_quantity_{strategy_id}_{index}")
            def optional_number(value: str) -> float | None:
                try:
                    return float(value.replace(",", ".")) if value.strip() else None
                except ValueError:
                    return None
            legs.append({**leg, "strike": optional_number(strike_text), "premium": optional_number(premium_text), "quantity": leg_quantity, "expiration": expiration or None})
        calculate = st.form_submit_button("Calcular simulação")
    if calculate:
        try:
            multiplier = float(multiplier_text.replace(",", ".")) if multiplier_text.strip() else None
        except ValueError:
            multiplier = None
        simulation = {
            **template,
            "ticker": ticker or None,
            "strategy_id": strategy_id,
            "strategy_name": strategy_id,
            "expiration": expiration or None,
            "quantity": quantity,
            "contract_multiplier": multiplier,
            "has_underlying_position": has_underlying,
            "legs": legs,
            "source": "manual",
        }
        st.session_state[f"{key_prefix}_result"] = calculate_manual_strategy_risk(simulation, load_user_trading_profile())
    result = st.session_state.get(f"{key_prefix}_result")
    if result:
        render_manual_simulation(result)
        if st.button("Salvar simulação manual", key=f"{key_prefix}_save"):
            saved = save_manual_simulation(result)
            st.session_state[f"{key_prefix}_result"] = saved
            st.success("Simulação manual salva. Nenhuma ordem foi criada.")

def manual_simulations_page() -> None:
    st.warning("Valores desta tela são digitados manualmente e não são cotações validadas. Nenhuma ordem é enviada.")
    manual_simulator_form(st.session_state.get("manual_simulation_seed"), "manual_page")
    st.markdown("## Simulações salvas")
    simulations = list_manual_simulations()
    if not simulations:
        st.info("Nenhuma simulação manual salva.")
    for index, simulation in enumerate(simulations):
        render_manual_simulation(simulation)
        if st.button("Excluir simulação", key=f"delete_manual_{index}_{simulation.get('simulation_id')}"):
            delete_manual_simulation(str(simulation.get("simulation_id")))
            st.rerun()


def tools_page() -> None:
    tabs = st.tabs(["Simulador", "Histórico"])
    with tabs[0]:
        manual_simulations_page()
    with tabs[1]:
        history_page()
