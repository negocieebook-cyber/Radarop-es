"""Auditoria do motor de retrospectiva com dados sintéticos (sem rede)."""

from __future__ import annotations

from datetime import date

import app.retrospective_engine as engine
from app.retrospective_engine import _payoff_estimates, summarize_retrospective


def _strikes(bought: float | None = None, sold: float | None = None) -> dict:
    return {"comprado": bought, "vendido": sold}


def test_call_debit_spread_payoff() -> None:
    result = _payoff_estimates("call_debit_spread", _strikes(48, 50), 48.5, 1.5)
    assert result["calculated"] is True
    assert result["pnl_per_unit"] == -1.0
    assert _payoff_estimates("call_debit_spread", _strikes(48, 50), 50.0, 1.5)["pnl_per_unit"] == 0.5
    assert _payoff_estimates("call_debit_spread", _strikes(48, 50), 52.0, 1.5)["pnl_per_unit"] == 0.5
    assert _payoff_estimates("call_debit_spread", _strikes(48, 50), 47.0, 1.5)["pnl_per_unit"] == -1.5


def test_put_debit_spread_payoff() -> None:
    result = _payoff_estimates("put_debit_spread", _strikes(50, 48), 47.0, 1.2)
    assert result["calculated"] is True
    assert result["pnl_per_unit"] == 0.8
    assert _payoff_estimates("put_debit_spread", _strikes(50, 48), 51.0, 1.2)["pnl_per_unit"] == -1.2


def test_bull_put_spread_payoff() -> None:
    result = _payoff_estimates("bull_put_spread", _strikes(46, 48), 48.5, 0.8)
    assert result["calculated"] is True
    assert result["pnl_per_unit"] == 0.8
    assert _payoff_estimates("bull_put_spread", _strikes(46, 48), 47.0, 0.8)["pnl_per_unit"] == -0.2
    assert _payoff_estimates("bull_put_spread", _strikes(46, 48), 44.0, 0.8)["pnl_per_unit"] == -1.2


def test_bear_call_spread_payoff() -> None:
    result = _payoff_estimates("bear_call_spread", _strikes(50, 48), 47.0, 0.8)
    assert result["calculated"] is True
    assert result["pnl_per_unit"] == 0.8
    assert _payoff_estimates("bear_call_spread", _strikes(50, 48), 49.0, 0.8)["pnl_per_unit"] == -0.2
    assert _payoff_estimates("bear_call_spread", _strikes(50, 48), 52.0, 0.8)["pnl_per_unit"] == -1.2


def test_long_call_and_put_payoff() -> None:
    assert _payoff_estimates("long_call", _strikes(48), 50.0, 1.5)["pnl_per_unit"] == 0.5
    assert _payoff_estimates("long_call", _strikes(48), 47.0, 1.5)["pnl_per_unit"] == -1.5
    assert _payoff_estimates("long_put", _strikes(50), 47.0, 1.5)["pnl_per_unit"] == 1.5
    assert _payoff_estimates("long_put", _strikes(50), 51.0, 1.5)["pnl_per_unit"] == -1.5


def test_covered_call_payoff_only_option_leg() -> None:
    assert _payoff_estimates("covered_call", _strikes(None, 50), 49.0, 1.0)["pnl_per_unit"] == 1.0
    assert _payoff_estimates("covered_call", _strikes(None, 50), 52.0, 1.0)["pnl_per_unit"] == -1.0


def test_missing_fields_are_honest() -> None:
    result = _payoff_estimates("call_debit_spread", _strikes(48), 48.5, None)
    assert result["calculated"] is False
    assert "referência de entrada" in result["missing_fields"]
    unknown = _payoff_estimates("iron_condor", _strikes(48, 50), 48.5, 1.0)
    assert unknown["calculated"] is False


def test_summarize_retrospective() -> None:
    items = [
        {"tipo_estrutura": "call_debit_spread", "pnl_por_unidade_estimado": -1.0, "resultado": "perda estimada"},
        {"tipo_estrutura": "call_debit_spread", "pnl_por_unidade_estimado": 0.5, "resultado": "ganho estimado"},
        {"tipo_estrutura": "bull_put_spread", "pnl_por_unidade_estimado": 0.8, "resultado": "ganho estimado"},
        {"tipo_estrutura": "bull_put_spread", "pnl_por_unidade_estimado": None, "resultado": "inconclusivo"},
    ]
    summary = summarize_retrospective(items)
    assert summary["vencidas"] == 4
    assert summary["avaliadas"] == 3
    assert summary["inconclusivas"] == 1
    assert summary["ganhos"] == 2
    assert summary["perdas"] == 1
    bucket = summary["por_estrategia"]["call_debit_spread"]
    assert bucket["n"] == 2
    assert bucket["taxa_ganho"] == 0.5
    assert bucket["soma_pnl_estimado"] == -0.5


def test_evaluate_expired_item_with_patched_history(monkeypatch) -> None:
    monkeypatch.setattr(
        engine,
        "_cached_history",
        lambda symbol: {"success": True, "candles": [{"date": "2026-09-18", "close": 48.5}]},
    )
    item = {
        "id": "test", "ativo": "PETR4", "estrategia": "teste", "tipo_estrutura": "call_debit_spread",
        "vencimento": "2026-09-18", "strikes": {"comprado": 48.0, "vendido": 50.0},
        "preco_eod_referencia": 1.5, "status": "aguardando confirmação",
    }
    record = engine.evaluate_expired_item(item, {})
    assert record["resultado"] == "perda estimada"
    assert record["pnl_por_unidade_estimado"] == -1.0
    assert record["preco_vencimento"] == 48.5
    assert record["data_preco_vencimento"] == "2026-09-18"


def test_invalidated_item_is_inconclusive(monkeypatch) -> None:
    monkeypatch.setattr(
        engine,
        "_cached_history",
        lambda symbol: {"success": True, "candles": [{"date": "2026-09-18", "close": 48.5}]},
    )
    item = {
        "id": "test", "ativo": "PETR4", "tipo_estrutura": "call_debit_spread",
        "vencimento": "2026-09-18", "strikes": {"comprado": 48.0, "vendido": 50.0},
        "preco_eod_referencia": 1.5, "status": "invalidado",
    }
    record = engine.evaluate_expired_item(item, {})
    assert record["resultado"] == "inconclusivo"
    assert "invalidada" in record["observacao"]


def test_price_at_expiry_uses_last_available_session(monkeypatch) -> None:
    monkeypatch.setattr(
        engine,
        "_cached_history",
        lambda symbol: {"success": True, "candles": [{"date": "2026-09-16", "close": 48.2}, {"date": "2026-09-17", "close": 48.8}]},
    )
    price, price_date, error = engine.price_at_expiry("PETR4", date(2026, 9, 18))
    assert price == 48.8
    assert price_date == "2026-09-17"
    assert error is None
    price, price_date, error = engine.price_at_expiry("PETR4", date(2026, 9, 5))
    assert price is None
    assert error is not None
