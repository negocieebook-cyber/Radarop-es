"""Auditoria com dados didáticos MOCK / TESTE; não contém cotações reais."""

from __future__ import annotations

from app.manual_trade_simulator import calculate_manual_strategy_risk


PROFILE = {
    "capital_disponivel": 50000,
    "perda_maxima_por_operacao": None,
    "percentual_maximo_por_operacao": None,
    "tolerancia_capital": "moderada",
}


def simulation(strategy: str, legs: list[tuple[str, str, float | None, float | None]], quantity: int = 1, multiplier: int = 100, has_stock: bool = False) -> dict:
    return {
        "simulation_id": f"mock-test-{strategy}",
        "source": "manual",
        "data_status": "MOCK / TESTE",
        "ticker": "TEST3",
        "strategy_id": strategy,
        "strategy_name": strategy,
        "quantity": quantity,
        "contract_multiplier": multiplier,
        "has_underlying_position": has_stock,
        "legs": [
            {"type": kind, "action": action, "strike": strike, "premium": premium, "quantity": 1, "expiration": "2099-12-31"}
            for kind, action, strike, premium in legs
        ],
    }


def calculate(strategy: str, legs: list[tuple[str, str, float | None, float | None]], **kwargs) -> dict:
    return calculate_manual_strategy_risk(simulation(strategy, legs, **kwargs), PROFILE)


def test_long_call() -> None:
    result = calculate("long_call", [("call", "buy", 100, 2)])
    assert result["max_loss"] == 200
    assert result["capital_required"] == 200
    assert result["break_even_points"] == [102]


def test_long_put() -> None:
    result = calculate("long_put", [("put", "buy", 100, 3)])
    assert result["max_loss"] == 300
    assert result["break_even_points"] == [97]


def test_call_debit_spread() -> None:
    result = calculate("call_debit_spread", [("call", "buy", 100, 5), ("call", "sell", 110, 2)])
    assert result["net_debit"] == 300
    assert result["max_loss"] == 300
    assert result["max_gain"] == 700
    assert result["break_even_points"] == [103]


def test_put_debit_spread() -> None:
    result = calculate("put_debit_spread", [("put", "buy", 100, 5), ("put", "sell", 90, 2)])
    assert result["net_debit"] == 300
    assert result["max_loss"] == 300
    assert result["max_gain"] == 700
    assert result["break_even_points"] == [97]


def test_bull_put_spread() -> None:
    result = calculate("bull_put_spread", [("put", "sell", 100, 4), ("put", "buy", 90, 1)])
    assert result["net_credit"] == 300
    assert result["max_gain"] == 300
    assert result["max_loss"] == 700
    assert result["break_even_points"] == [97]


def test_bear_call_spread() -> None:
    result = calculate("bear_call_spread", [("call", "sell", 100, 4), ("call", "buy", 110, 1)])
    assert result["net_credit"] == 300
    assert result["max_gain"] == 300
    assert result["max_loss"] == 700
    assert result["break_even_points"] == [103]


def test_iron_condor() -> None:
    result = calculate("iron_condor", [
        ("put", "buy", 90, 1), ("put", "sell", 95, 2),
        ("call", "sell", 105, 2), ("call", "buy", 110, 1),
    ])
    assert result["net_credit"] == 200
    assert result["max_gain"] == 200
    assert result["max_loss"] == 300
    assert result["capital_required"] == 300
    assert result["break_even_points"] == [93, 107]


def test_cash_secured_put() -> None:
    result = calculate("cash_secured_put", [("put", "sell", 100, 3)])
    assert result["capital_required"] == 10000
    assert result["max_gain"] == 300
    assert result["max_loss"] == 9700
    assert result["break_even_points"] == [97]


def test_covered_call_marks_stock_risk_and_requires_stock() -> None:
    legs = [("stock", "buy", None, 100), ("call", "sell", 110, 2)]
    without_stock = calculate("covered_call", legs)
    with_stock = calculate("covered_call", legs, has_stock=True)
    assert without_stock["net_credit"] == 200
    assert without_stock["max_gain"] == 1200
    assert without_stock["max_loss"] == 9800
    assert without_stock["capital_fit_status"] == "exige_ativo_em_carteira"
    assert "queda do ativo" in without_stock["risk_note"].lower()
    assert with_stock["capital_fit_status"] == "cabe_bem"


def test_missing_fields_are_pending() -> None:
    result = calculate("long_call", [("call", "buy", 100, None)])
    assert result["capital_fit_status"] == "pendente_dados"
    assert result["max_loss"] is None
    assert result["missing_fields"]


def test_quantity_scales_all_monetary_values() -> None:
    one = calculate("long_call", [("call", "buy", 100, 2)], quantity=1)
    three = calculate("long_call", [("call", "buy", 100, 2)], quantity=3)
    assert three["max_loss"] == one["max_loss"] * 3
    assert three["net_debit"] == one["net_debit"] * 3
    assert three["break_even_points"] == one["break_even_points"]


def test_multiplier_scales_all_monetary_values() -> None:
    hundred = calculate("long_put", [("put", "buy", 100, 3)], multiplier=100)
    ten = calculate("long_put", [("put", "buy", 100, 3)], multiplier=10)
    assert hundred["max_loss"] == ten["max_loss"] * 10
    assert hundred["break_even_points"] == ten["break_even_points"]


def test_manual_source_is_preserved() -> None:
    result = calculate("long_call", [("call", "buy", 100, 2)])
    assert result["source"] == "manual"
    assert result["data_status"] == "MOCK / TESTE"


def test_mock_examples_never_claim_real_data() -> None:
    result = calculate("iron_condor", [
        ("put", "buy", 90, 1), ("put", "sell", 95, 2),
        ("call", "sell", 105, 2), ("call", "buy", 110, 1),
    ])
    assert "REAL" not in result["data_status"]
    assert "manual" in result["warning"].lower()
