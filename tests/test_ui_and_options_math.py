"""Auditoria de componentes de UI e matemática de opções com dados MOCK / TESTE."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from app.components import render_daily_priority_item, render_real_opportunity_card
from app.options_math import calculate_option_strategy


def _ui_page() -> None:
    import streamlit as st

    from app.components import render_daily_priority_item, render_real_opportunity_card

    st.set_page_config(layout="wide")
    opportunity = {"ativo": "TESTE3", "estrategia": "trava de baixa com put", "vencimento": "2099-01-01"}
    render_real_opportunity_card(opportunity, key_suffix="_evitar_0")
    render_real_opportunity_card(opportunity, key_suffix="_evitar_1")
    priority = {"ativo": "TESTE3", "strategy_name": "iron condor"}
    render_daily_priority_item(priority, key_suffix="_top_premio_0")
    render_daily_priority_item(priority, key_suffix="_top_premio_1")


def test_cards_aceitam_sufixo_sem_chave_duplicada() -> None:
    at = AppTest.from_function(_ui_page, default_timeout=30)
    at.run()
    assert not at.exception


def test_cards_sem_sufixo_duplicam_chave() -> None:
    """Reproduz o crash StreamlitDuplicateElementKey quando o sufixo é omitido."""

    def page() -> None:
        import streamlit as st

        from app.components import render_real_opportunity_card

        st.set_page_config(layout="wide")
        opportunity = {"ativo": "TESTE3", "estrategia": "trava de baixa com put", "vencimento": "2099-01-01"}
        render_real_opportunity_card(opportunity)
        render_real_opportunity_card(opportunity)

    at = AppTest.from_function(page, default_timeout=30)
    at.run()
    assert at.exception


@pytest.mark.parametrize(
    ("opportunity", "expected"),
    [
        (
            {
                "tipo_estrutura": "call_debit_spread",
                "strike_comprado": 100,
                "strike_vendido": 110,
                "premio_pago": 5,
                "premio_recebido": 2,
                "quantidade": 1,
            },
            {"net_cost": 3.0, "max_profit": 7.0, "max_loss": 3.0, "break_even": 103.0},
        ),
        (
            {
                "tipo_estrutura": "put_credit_spread",
                "strike_vendido": 100,
                "strike_comprado": 90,
                "premio_recebido": 3,
                "premio_pago": 1,
                "quantidade": 1,
            },
            None,
        ),
    ],
)
def test_calculate_option_strategy(opportunity: dict, expected: dict | None) -> None:
    result = calculate_option_strategy(opportunity)
    if expected is None:
        assert result is not None
        assert result.get("can_calculate") in {True, False}
        return
    for key, value in expected.items():
        assert result.get(key) == value, f"{key}: {result.get(key)} != {value}"
